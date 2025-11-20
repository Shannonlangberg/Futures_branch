# webhooks.py
from flask import Blueprint, jsonify, request
from models import db, Person, EngagementProfile, GivingTransaction, GivingSubscription
from datetime import datetime, timezone
import logging
import os
import stripe

logger = logging.getLogger(__name__)

# Get webhook secret from environment
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

@webhooks_bp.route('/stripe', methods=['GET', 'POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks for payments and subscriptions
    This ensures all payments go through our system for security
    """
    # Log ALL requests to this endpoint (even GET for testing)
    logger.info(f"[WEBHOOK] ⚡ Request received: {request.method} {request.url}")
    print(f"[WEBHOOK] ⚡ Request received: {request.method} {request.url}")
    print(f"[WEBHOOK] Headers: {dict(request.headers)}")
    
    # Allow GET for testing endpoint accessibility
    if request.method == 'GET':
        return jsonify({
            'status': 'ok',
            'endpoint': '/api/webhooks/stripe',
            'method': 'POST required for webhooks',
            'webhook_secret_configured': bool(STRIPE_WEBHOOK_SECRET)
        }), 200
    
    # Get raw payload as bytes (required for Stripe signature verification)
    payload = request.get_data()
    # Also get text version for logging
    payload_text = payload.decode('utf-8') if payload else ''
    
    # Try multiple header name variations (case sensitivity, proxy modifications)
    sig_header = (
        request.headers.get('Stripe-Signature') or
        request.headers.get('stripe-signature') or
        request.headers.get('STRIPE-SIGNATURE') or
        request.headers.get('HTTP_STRIPE_SIGNATURE') or
        request.headers.get('X-Stripe-Signature')
    )
    
    logger.info(f"[WEBHOOK] ✅ POST request received - processing webhook")
    print(f"[WEBHOOK] ✅ POST request received - processing webhook")
    print(f"[WEBHOOK] Payload length: {len(payload)} bytes")
    print(f"[WEBHOOK] Has signature header: {bool(sig_header)}")
    if sig_header:
        # Log first part of signature for debugging (not the full secret)
        sig_preview = sig_header.split(',')[0][:50] if ',' in sig_header else sig_header[:50]
        print(f"[WEBHOOK] Signature header preview: {sig_preview}...")
        logger.info(f"[WEBHOOK] Signature header format: {sig_header[:100] if len(sig_header) > 100 else sig_header}")
    
    # Log all headers for debugging
    logger.debug(f"[WEBHOOK] All headers: {dict(request.headers)}")
    
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("[WEBHOOK] Stripe webhook secret not configured")
        return jsonify({'error': 'Webhook not configured'}), 500
    
    if not sig_header:
        logger.error("[WEBHOOK] Missing Stripe-Signature header")
        logger.error(f"[WEBHOOK] Available headers: {list(request.headers.keys())}")
        return jsonify({'error': 'Missing signature header'}), 400
    
    try:
        # Verify webhook signature for security
        # Stripe requires raw bytes, not text
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        logger.info(f"[WEBHOOK] ✅ Webhook signature verified. Event type: {event['type']}")
    except ValueError as e:
        logger.error(f"[WEBHOOK] Invalid payload: {e}")
        logger.error(f"[WEBHOOK] Payload preview: {payload_text[:200] if payload_text else 'Empty'}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        error_msg = str(e)
        logger.error(f"[WEBHOOK] Invalid signature: {error_msg}")
        # Log more details for debugging
        logger.error(f"[WEBHOOK] Signature header: {sig_header[:200]}")
        logger.error(f"[WEBHOOK] Payload length: {len(payload)}")
        logger.error(f"[WEBHOOK] Webhook secret configured: {bool(STRIPE_WEBHOOK_SECRET)}")
        logger.error(f"[WEBHOOK] Webhook secret prefix: {STRIPE_WEBHOOK_SECRET[:10]}..." if STRIPE_WEBHOOK_SECRET else "Not set")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        logger.error(f"[WEBHOOK] Unexpected error during signature verification: {e}", exc_info=True)
        return jsonify({'error': 'Signature verification failed'}), 400
    
    # Handle different event types
    event_type = event['type']
    data = event['data']['object']
    
    logger.info(f"[WEBHOOK] Processing event: {event_type}")
    
    try:
        if event_type == 'payment_intent.succeeded':
            # One-time payment succeeded
            handle_payment_success(data)
        elif event_type == 'invoice.payment_succeeded':
            # Subscription payment succeeded
            handle_subscription_payment(data)
        elif event_type == 'customer.subscription.created':
            # Subscription created
            handle_subscription_created(data)
        elif event_type == 'customer.subscription.updated':
            # Subscription updated (status change, etc.)
            handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            # Subscription canceled
            handle_subscription_deleted(data)
        elif event_type == 'invoice.payment_failed':
            # Payment failed
            handle_payment_failed(data)
        else:
            logger.info(f"[WEBHOOK] Unhandled event type: {event_type}")
        
        logger.info(f"[WEBHOOK] ✅ Successfully processed {event_type}")
        return jsonify({'received': True}), 200
        
    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Error handling webhook {event_type}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def handle_payment_success(payment_intent):
    """Handle successful one-time payment"""
    try:
        payment_intent_id = payment_intent['id']
        logger.info(f"[WEBHOOK] Processing payment_intent.succeeded: {payment_intent_id}")
        
        # Check if transaction already exists
        existing = GivingTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if existing:
            logger.info(f"[WEBHOOK] Transaction already exists for {payment_intent_id}")
            return  # Already processed
        
        metadata = payment_intent.get('metadata', {})
        email = metadata.get('person_email')
        if not email:
            logger.warning(f"[WEBHOOK] No email in payment intent {payment_intent_id}")
            return
        
        logger.info(f"[WEBHOOK] Looking up person with email: {email}")
        
        # Case-insensitive person lookup (same as giving_api.py)
        from models import Person
        person = Person.query.filter(
            db.func.lower(Person.email) == db.func.lower(email),
            Person.is_active == True
        ).first()
        
        if not person:
            logger.warning(f"[WEBHOOK] Person not found for email {email}")
            return
        
        logger.info(f"[WEBHOOK] Found person: {person.id} - {person.full_name}")
        
        # Create transaction record
        transaction = GivingTransaction(
            person_id=person.id,
            stripe_payment_intent_id=payment_intent['id'],
            amount=payment_intent['amount'] / 100,  # Convert from cents
            currency=payment_intent.get('currency', 'AUD').upper(),
            giving_type=metadata.get('giving_type', 'tithe'),
            campus=metadata.get('campus', person.campus),
            source=metadata.get('source', 'web'),
            qr_code_id=metadata.get('qr_code_id') or None,
            status='completed',
            created_at=datetime.fromtimestamp(payment_intent['created'], tz=timezone.utc)
        )
        db.session.add(transaction)
        
        # Update engagement profile
        engagement = person.engagement_profile
        if not engagement:
            from models import EngagementProfile
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        engagement.add_giving(
            amount=transaction.amount,
            giving_date=datetime.now(timezone.utc).date(),
            campus=transaction.campus
        )
        engagement.recalculate_heartbeat()
        
        db.session.commit()
        logger.info(f"[WEBHOOK] ✅ Payment processed: ${transaction.amount} from {email} (Transaction ID: {transaction.id})")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"[WEBHOOK] ❌ Error handling payment success: {e}", exc_info=True)
        raise


def handle_subscription_payment(invoice):
    """Handle successful subscription payment"""
    try:
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return
        
        # Get subscription from Stripe
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        metadata = stripe_sub.get('metadata', {})
        
        # Find our subscription record
        subscription = GivingSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            logger.warning(f"Subscription not found: {subscription_id}")
            return
        
        # Create transaction for this payment
        existing = GivingTransaction.query.filter_by(
            stripe_payment_intent_id=invoice.get('payment_intent')
        ).first()
        
        if not existing and invoice.get('payment_intent'):
            transaction = GivingTransaction(
                person_id=subscription.person_id,
                stripe_payment_intent_id=invoice['payment_intent'],
                amount=invoice['amount_paid'] / 100,
                currency=invoice.get('currency', 'AUD').upper(),
                giving_type=subscription.giving_type,
                campus=subscription.campus,
                source=subscription.source,
                qr_code_id=subscription.qr_code_id,
                status='completed',
                created_at=datetime.fromtimestamp(invoice['created'], tz=timezone.utc)
            )
            db.session.add(transaction)
            
            # Update engagement profile
            person = subscription.person
            engagement = person.engagement_profile
            if not engagement:
                from models import EngagementProfile
                engagement = EngagementProfile(person_id=person.id)
                db.session.add(engagement)
            
            engagement.add_giving(
                amount=transaction.amount,
                giving_date=datetime.now(timezone.utc).date(),
                campus=transaction.campus
            )
            engagement.recalculate_heartbeat()
        
        db.session.commit()
        logger.info(f"Subscription payment processed: ${invoice['amount_paid']/100} for subscription {subscription_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling subscription payment: {e}")
        raise


def handle_subscription_created(subscription_data):
    """Handle subscription creation"""
    try:
        subscription_id = subscription_data['id']
        metadata = subscription_data.get('metadata', {})
        
        # Update our subscription record if it exists
        subscription = GivingSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=timezone.utc
            )
            db.session.commit()
            logger.info(f"Subscription created: {subscription_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling subscription created: {e}")


def handle_subscription_updated(subscription_data):
    """Handle subscription updates"""
    try:
        subscription_id = subscription_data['id']
        subscription = GivingSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=timezone.utc
            )
            subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
            
            if subscription_data['status'] == 'canceled':
                subscription.canceled_at = datetime.now(timezone.utc)
            
            db.session.commit()
            logger.info(f"Subscription updated: {subscription_id} - {subscription.status}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling subscription updated: {e}")


def handle_subscription_deleted(subscription_data):
    """Handle subscription cancellation"""
    try:
        subscription_id = subscription_data['id']
        subscription = GivingSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Subscription canceled: {subscription_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling subscription deleted: {e}")


def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        subscription_id = invoice.get('subscription')
        if subscription_id:
            subscription = GivingSubscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                subscription.status = 'past_due'
                db.session.commit()
                logger.warning(f"Subscription payment failed: {subscription_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling payment failed: {e}")

@webhooks_bp.route('/mailchimp', methods=['POST'])
def mailchimp_webhook():
    """Handle Mailchimp webhooks"""
    return jsonify({'received': True}), 200

@webhooks_bp.route('/planning-center', methods=['POST'])
def planning_center_webhook():
    """Handle Planning Center webhooks"""
    return jsonify({'received': True}), 200

@webhooks_bp.route('/test', methods=['GET', 'POST'])
def test_webhook():
    """Test webhook endpoint"""
    return jsonify({
        'message': 'Webhook test successful',
        'method': request.method,
        'data': request.get_json() if request.method == 'POST' else None
    }), 200

@webhooks_bp.route('/check-transactions', methods=['GET'])
def check_transactions():
    """Check if transactions exist in database (for debugging)"""
    try:
        from models import GivingTransaction
        count = GivingTransaction.query.count()
        recent = GivingTransaction.query.order_by(
            GivingTransaction.created_at.desc()
        ).limit(5).all()
        
        return jsonify({
            'total_transactions': count,
            'recent_transactions': [t.to_dict() for t in recent]
        }), 200
    except Exception as e:
        logger.error(f"Error checking transactions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/test-endpoint', methods=['GET'])
def test_endpoint():
    """Test if webhook endpoint is reachable"""
    return jsonify({
        'status': 'ok',
        'message': 'Webhook endpoint is reachable',
        'webhook_secret_configured': bool(STRIPE_WEBHOOK_SECRET),
        'endpoint': '/api/webhooks/stripe'
    }), 200

@webhooks_bp.route('/diagnostics', methods=['GET'])
def webhook_diagnostics():
    """Diagnostic information about webhook configuration"""
    import stripe as stripe_lib
    
    diagnostics = {
        'endpoint_url': 'https://futuresbranch-production.up.railway.app/api/webhooks/stripe',
        'webhook_secret_configured': bool(STRIPE_WEBHOOK_SECRET),
        'webhook_secret_prefix': STRIPE_WEBHOOK_SECRET[:10] + '...' if STRIPE_WEBHOOK_SECRET else 'Not set',
        'stripe_api_key_configured': bool(stripe_lib.api_key if hasattr(stripe_lib, 'api_key') else False),
        'stripe_api_key_mode': 'test' if (stripe_lib.api_key and stripe_lib.api_key.startswith('sk_test_')) else ('live' if (stripe_lib.api_key and stripe_lib.api_key.startswith('sk_live_')) else 'unknown'),
        'recent_transactions_count': GivingTransaction.query.count(),
        'recent_transactions': [t.to_dict() for t in GivingTransaction.query.order_by(GivingTransaction.created_at.desc()).limit(3).all()]
    }
    
    return jsonify(diagnostics), 200

