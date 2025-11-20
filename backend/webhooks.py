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

@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks for payments and subscriptions
    This ensures all payments go through our system for security
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook secret not configured")
        return jsonify({'error': 'Webhook not configured'}), 500
    
    try:
        # Verify webhook signature for security
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle different event types
    event_type = event['type']
    data = event['data']['object']
    
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
        
        return jsonify({'received': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling webhook {event_type}: {e}")
        return jsonify({'error': str(e)}), 500


def handle_payment_success(payment_intent):
    """Handle successful one-time payment"""
    try:
        # Check if transaction already exists
        existing = GivingTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent['id']
        ).first()
        
        if existing:
            return  # Already processed
        
        metadata = payment_intent.get('metadata', {})
        email = metadata.get('person_email')
        if not email:
            logger.warning(f"No email in payment intent {payment_intent['id']}")
            return
        
        from models import Person
        person = Person.query.filter_by(email=email, is_active=True).first()
        if not person:
            logger.warning(f"Person not found for email {email}")
            return
        
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
        logger.info(f"Payment processed: ${transaction.amount} from {email}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling payment success: {e}")
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

