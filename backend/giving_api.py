"""
Giving API - Stripe Integration

Endpoints for handling giving/tithe/donations with Stripe payments.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Person, EngagementProfile, GivingTransaction, GivingQRCode, GivingSubscription
from datetime import datetime, timedelta, date, timezone
import logging
import os
import stripe
import uuid

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

giving_bp = Blueprint('giving', __name__, url_prefix='/api/giving')


def get_person_by_email(email):
    """Get person by email - try multiple methods like other endpoints"""
    if not email:
        return None
    
    email = email.strip()
    
    # Method 1: Direct match (like beacon API uses)
    person = Person.query.filter_by(email=email, is_active=True).first()
    if person:
        return person
    
    # Method 2: Case-insensitive with func.lower
    try:
        person = Person.query.filter(
            db.func.lower(Person.email) == db.func.lower(email),
            Person.is_active == True
        ).first()
        if person:
            return person
    except:
        pass
    
    # Method 3: Try with trimmed/cleaned email
    email_clean = email.strip().lower()
    try:
        # Query all active persons and check manually
        persons = Person.query.filter_by(is_active=True).all()
        for p in persons:
            if p.email and p.email.strip().lower() == email_clean:
                return p
    except:
        pass
    
    return None


@giving_bp.route('/create-intent', methods=['POST'])
def create_payment_intent():
    """
    Create a Stripe Payment Intent for giving
    Public endpoint - uses email to identify person
    """
    # Log immediately to verify endpoint is being hit
    print(f"[GIVING API] ===== CREATE PAYMENT INTENT CALLED =====")
    print(f"[GIVING API] Method: {request.method}")
    print(f"[GIVING API] URL: {request.url}")
    print(f"[GIVING API] Headers: {dict(request.headers)}")
    logger.error(f"[GIVING API] ===== CREATE PAYMENT INTENT CALLED =====")  # Use error level so it shows in logs
    logger.error(f"[GIVING API] Request received at /api/giving/create-intent")
    
    try:
        data = request.get_json()
        print(f"[GIVING API] Request data: {data}")
        logger.error(f"[GIVING API] Creating payment intent with data: {data}")
        
        if not stripe.api_key:
            logger.error("Stripe API key not configured")
            return jsonify({'error': 'Stripe not configured'}), 500
        
        amount = data.get('amount')  # Amount in cents
        giving_type = data.get('type', 'tithe')  # 'tithe', 'offering', 'missions', 'event'
        campus = data.get('campus', '')
        email = data.get('email', '').strip()  # Get and trim email
        source = data.get('source', 'app')  # 'app', 'qr_code', 'web', 'tap_to_give'
        
        # Normalize email for lookup (lowercase, but keep original for storage)
        email_lower = email.lower() if email else ''
        qr_code_id = data.get('qr_code_id', None)  # QR code identifier if from QR
        service_date = data.get('service_date', None)  # Service date if from QR
        
        if not amount or amount <= 0:
            logger.warning(f"Invalid amount: {amount}")
            return jsonify({'error': 'Invalid amount'}), 400
        
        if not email:
            logger.warning("Email not provided in request")
            return jsonify({'error': 'Email required'}), 400
        
        print(f"[GIVING API] Looking up person with email: '{email}'")
        logger.error(f"[GIVING API] Looking up person with email: '{email}'")
        
        # Try multiple lookup methods to match how other endpoints work
        person = None
        
        # Method 1: Direct query like beacon API
        try:
            person = Person.query.filter_by(email=email, is_active=True).first()
            if person:
                print(f"[GIVING API] Found via direct query: {person.id}")
                logger.error(f"[GIVING API] Found via direct query: {person.id}")
        except Exception as e:
            print(f"[GIVING API] Direct query failed: {e}")
            logger.error(f"[GIVING API] Direct query failed: {e}")
        
        # Method 2: Use helper function
        if not person:
            try:
                person = get_person_by_email(email)
                if person:
                    print(f"[GIVING API] Found via helper function: {person.id}")
                    logger.error(f"[GIVING API] Found via helper function: {person.id}")
            except Exception as e:
                print(f"[GIVING API] Helper function failed: {e}")
                logger.error(f"[GIVING API] Helper function failed: {e}")
        
        # Method 3: Try case-insensitive manual search
        if not person:
            try:
                email_lower = email.strip().lower()
                all_persons = Person.query.filter_by(is_active=True).all()
                for p in all_persons:
                    if p.email and p.email.strip().lower() == email_lower:
                        person = p
                        print(f"[GIVING API] Found via manual search: {person.id} (email in DB: '{p.email}')")
                        logger.error(f"[GIVING API] Found via manual search: {person.id} (email in DB: '{p.email}')")
                        break
            except Exception as e:
                print(f"[GIVING API] Manual search failed: {e}")
                logger.error(f"[GIVING API] Manual search failed: {e}")
        
        # Verify person exists, create if missing
        try:
            
            if not person:
                # Person doesn't exist - create it immediately
                print("=" * 80)
                print(f"[GIVING API] PERSON NOT FOUND - CREATING NOW")
                print(f"[GIVING API] Email: {email}")
                print("=" * 80)
                logger.error("=" * 80)
                logger.error(f"[GIVING API] PERSON NOT FOUND - CREATING NOW")
                logger.error(f"[GIVING API] Email: {email}")
                logger.error("=" * 80)
                
                try:
                    # Generate unique ID
                    person_id = f"user_{uuid.uuid4().hex[:12]}"
                    name_from_email = email.split('@')[0].replace('.', ' ').title()
                    person_campus = campus or 'paradise'
                    
                    print(f"[GIVING API] Creating Person: id={person_id}, name={name_from_email}, campus={person_campus}")
                    logger.error(f"[GIVING API] Creating Person: id={person_id}, name={name_from_email}, campus={person_campus}")
                    
                    # Create Person - minimal fields only
                    person = Person(
                        id=person_id,
                        full_name=name_from_email,
                        email=email,
                        campus=person_campus,
                        is_active=True
                    )
                    
                    print(f"[GIVING API] Person object created, adding to session")
                    logger.error(f"[GIVING API] Person object created, adding to session")
                    db.session.add(person)
                    
                    print(f"[GIVING API] Flushing to get ID...")
                    logger.error(f"[GIVING API] Flushing to get ID...")
                    db.session.flush()
                    
                    print(f"[GIVING API] Person ID after flush: {person.id}")
                    logger.error(f"[GIVING API] Person ID after flush: {person.id}")
                    
                    # Skip engagement profile - schema issues
                    print(f"[GIVING API] Skipping engagement profile (schema issues)")
                    logger.error(f"[GIVING API] Skipping engagement profile (schema issues)")
                    
                    print(f"[GIVING API] Committing transaction...")
                    logger.error(f"[GIVING API] Committing transaction...")
                    db.session.commit()
                    
                    print(f"[GIVING API] ✅ COMMIT SUCCESS!")
                    logger.error(f"[GIVING API] ✅ COMMIT SUCCESS!")
                    
                    # Re-query to verify
                    verify = Person.query.filter_by(id=person.id).first()
                    if verify:
                        print(f"[GIVING API] ✅ VERIFIED: Person {person.id} exists!")
                        logger.error(f"[GIVING API] ✅ VERIFIED: Person {person.id} exists!")
                        person = verify  # Use the verified person
                    else:
                        print(f"[GIVING API] ❌ VERIFICATION FAILED!")
                        logger.error(f"[GIVING API] ❌ VERIFICATION FAILED!")
                        raise Exception("Person not found after commit")
                        
                except Exception as create_error:
                    print(f"[GIVING API] ❌❌❌ CREATION FAILED: {create_error}")
                    logger.error(f"❌❌❌ CREATION FAILED: {create_error}", exc_info=True)
                    import traceback
                    tb = traceback.format_exc()
                    print(f"[GIVING API] Traceback:\n{tb}")
                    logger.error(f"Traceback:\n{tb}")
                    db.session.rollback()
                    return jsonify({'error': f'Failed to create person: {str(create_error)}'}), 500
            
            # Final check
            if not person:
                print(f"[GIVING API] ❌ FINAL CHECK FAILED - Person is None!")
                logger.error(f"❌ FINAL CHECK FAILED - Person is None!")
                return jsonify({'error': f'Person not found for email: {email}'}), 404
            
            print(f"[GIVING API] ✅ Person ready: {person.id} - {person.full_name}")
            logger.error(f"[GIVING API] ✅ Person ready: {person.id} - {person.full_name}")
                
        except Exception as e:
            print(f"[GIVING API] ❌ Exception in person lookup: {e}")
            logger.error(f"Error looking up person: {e}", exc_info=True)
            import traceback
            traceback_str = traceback.format_exc()
            print(f"[GIVING API] Traceback: {traceback_str}")
            logger.error(f"Traceback: {traceback_str}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        
        # Use person's campus if not provided or if "all_campuses" was sent
        if not campus or campus == 'all_campuses':
            campus = person.campus or ''
        
        # If person still doesn't have a campus, default to a valid one
        if not campus:
            campus = 'paradise'  # Default campus
            logger.warning(f"Person {person.id} has no campus, defaulting to 'paradise'")
        
        # If from QR code, update scan count
        if qr_code_id and source in ['qr_code', 'tap_to_give']:
            try:
                qr_code = GivingQRCode.query.filter_by(qr_code_id=qr_code_id, is_active=True).first()
                if qr_code:
                    qr_code.scan_count += 1
                    qr_code.last_scan_at = datetime.utcnow()
                    db.session.commit()
            except Exception as e:
                logger.warning(f"Error updating QR code scan count: {e}")
        
        # Create Payment Intent
        try:
            logger.info(f"Creating Stripe payment intent for ${amount/100} {giving_type}")
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency='aud',  # Australian Dollars
                metadata={
                    'person_id': person.id,
                    'person_email': email,
                    'giving_type': giving_type,
                    'campus': campus,
                    'source': source,
                    'qr_code_id': qr_code_id or '',
                    'service_date': service_date or '',
                },
                receipt_email=email,
            )
            
            logger.info(f"Payment intent created: {payment_intent.id}")
            return jsonify({
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
            }), 200
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}", exc_info=True)
            return jsonify({'error': f'Stripe error: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@giving_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    """
    Confirm a payment after successful Stripe payment
    This updates the Heartbeat giving log
    """
    try:
        data = request.get_json()
        
        payment_intent_id = data.get('payment_intent_id')
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID required'}), 400
        
        # Retrieve payment intent from Stripe
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment intent: {e}")
            return jsonify({'error': 'Payment intent not found'}), 404
        
        # Check if payment was successful
        if payment_intent.status != 'succeeded':
            return jsonify({'error': 'Payment not successful'}), 400
        
        # Get person from metadata
        email = payment_intent.metadata.get('person_email')
        if not email:
            return jsonify({'error': 'Person email not found in payment'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get giving details from metadata
        giving_type = payment_intent.metadata.get('giving_type', 'tithe')
        campus = payment_intent.metadata.get('campus', person.campus)
        source = payment_intent.metadata.get('source', 'app')
        qr_code_id = payment_intent.metadata.get('qr_code_id') or None
        service_date_str = payment_intent.metadata.get('service_date')
        amount = payment_intent.amount / 100  # Convert from cents to dollars
        
        # Parse service date if provided
        service_date_obj = None
        if service_date_str:
            try:
                service_date_obj = datetime.fromisoformat(service_date_str).date()
            except:
                pass
        
        # Check if transaction already exists (prevent duplicates)
        existing = GivingTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if not existing:
            # Create transaction record
            transaction = GivingTransaction(
                person_id=person.id,
                stripe_payment_intent_id=payment_intent_id,
                amount=amount,
                currency='AUD',
                giving_type=giving_type,
                campus=campus,
                source=source,
                qr_code_id=qr_code_id,
                service_date=service_date_obj or datetime.utcnow().date(),
                status='completed',
                created_at=datetime.utcnow()
            )
            db.session.add(transaction)
        
        # Update engagement profile with giving record
        engagement = person.engagement_profile
        if not engagement:
            from models import EngagementProfile
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        engagement.add_giving(
            amount=amount,
            giving_date=datetime.utcnow().date(),
            campus=campus
        )
        
        # Recalculate heartbeat
        engagement.recalculate_heartbeat()
        
        db.session.commit()
        
        logger.info(f"Payment confirmed: ${amount} from {email} ({giving_type})")
        
        return jsonify({
            'success': True,
            'message': 'Payment confirmed and recorded',
            'amount': amount,
            'type': giving_type,
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming payment: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/create-setup-intent', methods=['POST'])
def create_setup_intent():
    """
    Create a Stripe Setup Intent for collecting payment method for subscriptions
    Public endpoint - uses email to identify person
    """
    try:
        data = request.get_json()
        
        if not stripe.api_key:
            return jsonify({'error': 'Stripe not configured'}), 500
        
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Verify person exists
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Create or retrieve Stripe Customer
        stripe_customer = None
        existing_subscription = GivingSubscription.query.filter_by(
            person_id=person.id,
            status='active'
        ).first()
        
        if existing_subscription:
            try:
                stripe_customer = stripe.Customer.retrieve(existing_subscription.stripe_customer_id)
            except:
                pass
        
        if not stripe_customer:
            stripe_customer = stripe.Customer.create(
                email=email,
                name=person.full_name,
                metadata={
                    'person_id': person.id,
                    'campus': person.campus or '',
                }
            )
        
        # Create Setup Intent
        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer.id,
            payment_method_types=['card'],
        )
        
        return jsonify({
            'client_secret': setup_intent.client_secret,
            'setup_intent_id': setup_intent.id,
            'customer_id': stripe_customer.id,
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating setup intent: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/get-setup-intent-payment-method', methods=['POST'])
def get_setup_intent_payment_method():
    """
    Retrieve payment method ID from a confirmed setup intent
    Public endpoint
    """
    try:
        data = request.get_json()
        setup_intent_id = data.get('setup_intent_id')
        
        if not setup_intent_id:
            return jsonify({'error': 'Setup intent ID required'}), 400
        
        if not stripe.api_key:
            return jsonify({'error': 'Stripe not configured'}), 500
        
        # Retrieve setup intent from Stripe
        setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)
        
        if setup_intent.status != 'succeeded':
            return jsonify({'error': 'Setup intent not succeeded'}), 400
        
        payment_method_id = setup_intent.payment_method
        
        if not payment_method_id:
            return jsonify({'error': 'Payment method not found'}), 404
        
        return jsonify({
            'payment_method_id': payment_method_id,
        }), 200
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error retrieving setup intent: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error retrieving setup intent payment method: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/create-subscription', methods=['POST'])
def create_subscription():
    """
    Create a Stripe Subscription for recurring giving
    Public endpoint - uses email to identify person
    """
    try:
        data = request.get_json()
        
        if not stripe.api_key:
            return jsonify({'error': 'Stripe not configured'}), 500
        
        amount = data.get('amount')  # Amount in cents
        giving_type = data.get('type', 'tithe')
        campus = data.get('campus', '')
        email = data.get('email')
        source = data.get('source', 'app')
        qr_code_id = data.get('qr_code_id', None)
        interval = data.get('interval', 'month')  # 'week', 'month', 'year'
        payment_method_id = data.get('payment_method_id')  # From Stripe Elements
        setup_intent_id = data.get('setup_intent_id')  # Alternative: get payment method from setup intent
        
        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Get payment method from setup intent if provided
        if setup_intent_id and not payment_method_id:
            try:
                setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)
                if setup_intent.status == 'succeeded':
                    payment_method_id = setup_intent.payment_method
            except:
                pass
        
        if not payment_method_id:
            return jsonify({'error': 'Payment method required'}), 400
        
        if interval not in ['week', 'month', 'year']:
            return jsonify({'error': 'Invalid interval. Must be week, month, or year'}), 400
        
        # Verify person exists
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Use person's campus if not provided
        if not campus:
            campus = person.campus
        
        # If from QR code, update scan count
        if qr_code_id and source in ['qr_code', 'tap_to_give']:
            qr_code = GivingQRCode.query.filter_by(qr_code_id=qr_code_id, is_active=True).first()
            if qr_code:
                qr_code.scan_count += 1
                qr_code.last_scan_at = datetime.utcnow()
                db.session.commit()
        
        try:
            # Create or retrieve Stripe Customer
            stripe_customer = None
            existing_subscription = GivingSubscription.query.filter_by(
                person_id=person.id,
                status='active'
            ).first()
            
            if existing_subscription:
                # Use existing customer
                try:
                    stripe_customer = stripe.Customer.retrieve(existing_subscription.stripe_customer_id)
                except:
                    pass
            
            if not stripe_customer:
                # Create new customer
                stripe_customer = stripe.Customer.create(
                    email=email,
                    name=person.full_name,
                    metadata={
                        'person_id': person.id,
                        'campus': campus,
                    }
                )
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer.id,
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                stripe_customer.id,
                invoice_settings={
                    'default_payment_method': payment_method_id,
                },
            )
            
            # Create Stripe Price
            price = stripe.Price.create(
                unit_amount=int(amount),
                currency='aud',
                recurring={
                    'interval': interval,
                },
                metadata={
                    'person_id': person.id,
                    'giving_type': giving_type,
                    'campus': campus,
                }
            )
            
            # Create Subscription
            subscription = stripe.Subscription.create(
                customer=stripe_customer.id,
                items=[{'price': price.id}],
                metadata={
                    'person_id': person.id,
                    'person_email': email,
                    'giving_type': giving_type,
                    'campus': campus,
                    'source': source,
                    'qr_code_id': qr_code_id or '',
                },
            )
            
            # Save subscription to database
            db_subscription = GivingSubscription(
                person_id=person.id,
                stripe_subscription_id=subscription.id,
                stripe_customer_id=stripe_customer.id,
                amount=amount / 100,  # Convert from cents to dollars
                giving_type=giving_type,
                campus=campus,
                source=source,
                qr_code_id=qr_code_id,
                interval=interval,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
            )
            db.session.add(db_subscription)
            db.session.commit()
            
            logger.info(f"Subscription created: ${amount/100} {interval}ly from {email} ({giving_type})")
            
            return jsonify({
                'success': True,
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
                'status': subscription.status,
            }), 200
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating subscription: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/subscriptions', methods=['GET'])
def get_subscriptions():
    """
    Get subscriptions for a person
    Public endpoint - uses email to identify person
    """
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'subscriptions': []}), 200
        
        subscriptions = GivingSubscription.query.filter_by(
            person_id=person.id
        ).order_by(GivingSubscription.created_at.desc()).all()
        
        return jsonify({
            'subscriptions': [sub.to_dict() for sub in subscriptions]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/subscriptions/<subscription_id>/cancel', methods=['POST'])
def cancel_subscription(subscription_id):
    """
    Cancel a subscription
    Public endpoint - uses email to verify ownership
    """
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        subscription = GivingSubscription.query.filter_by(
            id=subscription_id,
            person_id=person.id
        ).first()
        
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Cancel in Stripe
        try:
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            subscription.cancel_at_period_end = True
            subscription.status = stripe_sub.status
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Subscription will cancel at end of current period'
            }), 200
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error canceling subscription: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/history', methods=['GET'])
def get_giving_history():
    """
    Get giving history for a person (pattern view, not amounts)
    """
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            # Return empty history instead of error
            return jsonify({'transactions': []}), 200
        
        engagement = person.engagement_profile
        if not engagement:
            return jsonify({'transactions': []}), 200
        
        # Get giving log
        try:
            giving_log = engagement._load_json(engagement.giving_log)
        except:
            giving_log = []
        
        # Return pattern view (dates only, not amounts)
        transactions = []
        for record in giving_log:
            if isinstance(record, dict) and record.get('date'):
                transactions.append({
                    'date': record.get('date'),
                    'type': record.get('type', 'giving'),  # Generic type for privacy
                    # Don't include amount - only pattern
                })
        
        # Sort by date descending
        transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return jsonify({
            'transactions': transactions[:50],  # Last 50 transactions
            'total_count': len(giving_log),
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting giving history: {e}", exc_info=True)
        # Return empty history instead of error to prevent app crashes
        return jsonify({'transactions': [], 'total_count': 0}), 200


@giving_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events
    This is called by Stripe when payment status changes
    """
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        if not STRIPE_WEBHOOK_SECRET:
            logger.warning("Stripe webhook secret not configured")
            return jsonify({'error': 'Webhook secret not configured'}), 500
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid payload in Stripe webhook")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in Stripe webhook")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            # Get person from metadata
            email = payment_intent.metadata.get('person_email')
            if email:
                person = get_person_by_email(email)
                if person:
                    # Same logic as confirm_payment - create transaction record
                    giving_type = payment_intent.metadata.get('giving_type', 'tithe')
                    campus = payment_intent.metadata.get('campus', person.campus)
                    source = payment_intent.metadata.get('source', 'app')
                    qr_code_id = payment_intent.metadata.get('qr_code_id') or None
                    service_date_str = payment_intent.metadata.get('service_date')
                    amount = payment_intent.amount / 100
                    
                    service_date_obj = None
                    if service_date_str:
                        try:
                            service_date_obj = datetime.fromisoformat(service_date_str).date()
                        except:
                            pass
                    
                    # Check if transaction already exists
                    existing = GivingTransaction.query.filter_by(
                        stripe_payment_intent_id=payment_intent.id
                    ).first()
                    
                    if not existing:
                        transaction = GivingTransaction(
                            person_id=person.id,
                            stripe_payment_intent_id=payment_intent.id,
                            amount=amount,
                            currency='AUD',
                            giving_type=giving_type,
                            campus=campus,
                            source=source,
                            qr_code_id=qr_code_id,
                            service_date=service_date_obj or datetime.utcnow().date(),
                            status='completed',
                            created_at=datetime.utcnow()
                        )
                        db.session.add(transaction)
                    
                    engagement = person.engagement_profile
                    if not engagement:
                        from models import EngagementProfile
                        engagement = EngagementProfile(person_id=person.id)
                        db.session.add(engagement)
                    
                    engagement.add_giving(
                        amount=amount,
                        giving_date=datetime.utcnow().date(),
                        campus=campus
                    )
                    
                    engagement.recalculate_heartbeat()
                    db.session.commit()
                    
                    logger.info(f"Webhook: Payment succeeded - ${amount} from {email} via {source}")
        
        return jsonify({'received': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {e}")
        return jsonify({'error': str(e)}), 500


# ANALYTICS ENDPOINTS

@giving_bp.route('/analytics', methods=['GET'])
@login_required
def get_giving_analytics():
    """
    Get giving analytics for admin/finance team
    Filters: campus, date range, giving_type, source
    """
    try:
        if not current_user.has_permission('finance', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        campus = request.args.get('campus')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        giving_type = request.args.get('giving_type')
        source = request.args.get('source')
        
        query = GivingTransaction.query.filter_by(status='completed')
        
        if campus and campus != 'all_campuses':
            query = query.filter_by(campus=campus)
        
        if giving_type:
            query = query.filter_by(giving_type=giving_type)
        
        if source:
            query = query.filter_by(source=source)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date).date()
                query = query.filter(GivingTransaction.created_at >= datetime.combine(start, datetime.min.time()))
            except:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date).date()
                query = query.filter(GivingTransaction.created_at <= datetime.combine(end, datetime.max.time()))
            except:
                pass
        
        transactions = query.order_by(GivingTransaction.created_at.desc()).all()
        
        # Calculate totals
        total_amount = sum(t.amount for t in transactions)
        transaction_count = len(transactions)
        
        # Breakdowns
        by_campus = {}
        by_type = {}
        by_source = {}
        by_date = {}
        
        for t in transactions:
            # By campus
            by_campus[t.campus] = by_campus.get(t.campus, 0) + t.amount
            
            # By type
            by_type[t.giving_type] = by_type.get(t.giving_type, 0) + t.amount
            
            # By source
            by_source[t.source] = by_source.get(t.source, {'count': 0, 'amount': 0})
            by_source[t.source]['count'] += 1
            by_source[t.source]['amount'] += t.amount
            
            # By date
            date_key = t.created_at.date().isoformat()
            by_date[date_key] = by_date.get(date_key, {'count': 0, 'amount': 0})
            by_date[date_key]['count'] += 1
            by_date[date_key]['amount'] += t.amount
        
        return jsonify({
            'summary': {
                'total_amount': total_amount,
                'transaction_count': transaction_count,
                'average_transaction': total_amount / transaction_count if transaction_count > 0 else 0
            },
            'breakdowns': {
                'by_campus': by_campus,
                'by_type': by_type,
                'by_source': by_source,
                'by_date': by_date
            },
            'transactions': [t.to_dict() for t in transactions[:100]],  # Last 100
            'total_transactions': len(transactions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting giving analytics: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/analytics/qr-scans', methods=['GET'])
@login_required
def get_qr_scan_analytics():
    """Get QR code scan analytics - taps per Sunday/service"""
    try:
        if not current_user.has_permission('finance', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        campus = request.args.get('campus')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get transactions from QR codes
        from sqlalchemy import or_
        query = GivingTransaction.query.filter(
            GivingTransaction.status == 'completed'
        ).filter(
            or_(
                GivingTransaction.source == 'qr_code',
                GivingTransaction.source == 'tap_to_give'
            )
        )
        
        if campus and campus != 'all_campuses':
            query = query.filter_by(campus=campus)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date).date()
                query = query.filter(GivingTransaction.service_date >= start)
            except:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date).date()
                query = query.filter(GivingTransaction.service_date <= end)
            except:
                pass
        
        transactions = query.all()
        
        # Group by service date
        by_service_date = {}
        qr_codes_used = {}
        
        for t in transactions:
            service_date_key = t.service_date.isoformat() if t.service_date else t.created_at.date().isoformat()
            
            if service_date_key not in by_service_date:
                by_service_date[service_date_key] = {
                    'date': service_date_key,
                    'scans': 0,
                    'gifts': 0,
                    'amount': 0,
                    'campus': t.campus
                }
            
            by_service_date[service_date_key]['scans'] += 1
            by_service_date[service_date_key]['amount'] += t.amount
            if t.amount > 0:
                by_service_date[service_date_key]['gifts'] += 1
            
            # Track QR codes used
            if t.qr_code_id:
                if t.qr_code_id not in qr_codes_used:
                    qr_codes_used[t.qr_code_id] = 0
                qr_codes_used[t.qr_code_id] += 1
        
        # Get QR code details
        qr_details = {}
        for qr_id in qr_codes_used.keys():
            qr = GivingQRCode.query.filter_by(qr_code_id=qr_id).first()
            if qr:
                qr_details[qr_id] = {
                    'campus': qr.campus,
                    'zone': qr.zone,
                    'seat_number': qr.seat_number,
                    'total_scans': qr.scan_count
                }
        
        return jsonify({
            'by_service_date': list(by_service_date.values()),
            'qr_codes_used': qr_codes_used,
            'qr_details': qr_details,
            'total_scans': len(transactions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting QR scan analytics: {e}")
        return jsonify({'error': str(e)}), 500


# QR CODE MANAGEMENT

@giving_bp.route('/qr-codes', methods=['GET'])
@login_required
def get_qr_codes():
    """Get all QR codes (admin only)"""
    try:
        if not current_user.has_permission('finance', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        campus = request.args.get('campus')
        is_active = request.args.get('is_active', 'true')
        
        query = GivingQRCode.query
        
        if campus and campus != 'all_campuses':
            query = query.filter_by(campus=campus)
        
        if is_active.lower() == 'true':
            query = query.filter_by(is_active=True)
        
        qr_codes = query.order_by(GivingQRCode.campus, GivingQRCode.zone).all()
        
        return jsonify({
            'qr_codes': [qr.to_dict() for qr in qr_codes],
            'count': len(qr_codes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting QR codes: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/qr-codes', methods=['POST'])
@login_required
def create_qr_code():
    """Create a new QR code for tap-to-give"""
    try:
        if not current_user.has_permission('finance', 'create'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        campus = data.get('campus')
        zone = data.get('zone')
        seat_number = data.get('seat_number')
        count = data.get('count', 1)  # Generate multiple at once
        
        if not campus:
            return jsonify({'error': 'Campus required'}), 400
        
        created_qr_codes = []
        
        code_type = data.get('type', 'qr')  # 'qr' or 'nfc'
        
        for i in range(count):
            if code_type == 'nfc':
                qr_code_id = f"nfc_{campus}_{uuid.uuid4().hex[:12]}"
            else:
                qr_code_id = f"qr_{campus}_{uuid.uuid4().hex[:12]}"
            
            qr_code = GivingQRCode(
                qr_code_id=qr_code_id,
                campus=campus,
                zone=zone,
                seat_number=seat_number if count == 1 else f"{seat_number}-{i+1}" if seat_number else None,
                is_active=True
            )
            
            db.session.add(qr_code)
            created_qr_codes.append(qr_code)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {count} QR code(s)',
            'qr_codes': [qr.to_dict() for qr in created_qr_codes]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating QR code: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/qr-codes/<int:qr_id>', methods=['DELETE'])
@login_required
def delete_qr_code(qr_id):
    """Delete (deactivate) a QR code"""
    try:
        if not current_user.has_permission('finance', 'delete'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        qr_code = GivingQRCode.query.get(qr_id)
        if not qr_code:
            return jsonify({'error': 'QR code not found'}), 404
        
        qr_code.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'QR code deactivated'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting QR code: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/qr/<qr_code_id>', methods=['GET'])
def qr_code_redirect(qr_code_id):
    """
    QR code redirect endpoint - opens giving page with QR context
    Public endpoint - no auth required
    """
    try:
        qr_code = GivingQRCode.query.filter_by(qr_code_id=qr_code_id, is_active=True).first()
        
        if not qr_code:
            return jsonify({'error': 'Invalid QR code'}), 404
        
        # Update scan count
        qr_code.scan_count += 1
        qr_code.last_scan_at = datetime.utcnow()
        db.session.commit()
        
        # Return redirect info - frontend will handle showing giving page
        return jsonify({
            'success': True,
            'qr_code': qr_code.to_dict(),
            'redirect_to': '/give',
            'campus': qr_code.campus,
            'service_date': date.today().isoformat()  # Assume today's service
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling QR redirect: {e}")
        return jsonify({'error': str(e)}), 500


@giving_bp.route('/nfc/<nfc_code_id>', methods=['GET'])
def nfc_code_redirect(nfc_code_id):
    """
    NFC code redirect endpoint - opens giving page with NFC context
    Public endpoint - no auth required
    Supports both nfc_ prefixed IDs and direct QR code IDs (for compatibility)
    """
    try:
        # Try to find by NFC ID first, then fall back to QR code ID
        nfc_code = GivingQRCode.query.filter_by(qr_code_id=nfc_code_id, is_active=True).first()
        
        # If not found, try with nfc_ prefix
        if not nfc_code and not nfc_code_id.startswith('nfc_'):
            nfc_code = GivingQRCode.query.filter_by(qr_code_id=f'nfc_{nfc_code_id}', is_active=True).first()
        
        if not nfc_code:
            return jsonify({'error': 'Invalid NFC code'}), 404
        
        # Update scan count
        nfc_code.scan_count += 1
        nfc_code.last_scan_at = datetime.utcnow()
        db.session.commit()
        
        # Return redirect info - frontend will handle showing giving page
        return jsonify({
            'success': True,
            'qr_code': nfc_code.to_dict(),  # Reuse same structure
            'redirect_to': '/give',
            'campus': nfc_code.campus,
            'service_date': date.today().isoformat()  # Assume today's service
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling NFC redirect: {e}")
        return jsonify({'error': str(e)}), 500

