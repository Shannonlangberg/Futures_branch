#!/usr/bin/env python3
"""
Quick script to manually sync a Stripe payment to the database
Usage: python sync_payment.py <payment_intent_id>
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Person, GivingTransaction, EngagementProfile
from giving_api import get_person_by_email
from datetime import datetime, timezone
import stripe

# Set Stripe API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
if not stripe.api_key:
    print("ERROR: STRIPE_SECRET_KEY not set in environment")
    sys.exit(1)

def sync_payment(payment_intent_id):
    """Sync a payment from Stripe to the database"""
    with app.app_context():
        try:
            # Retrieve payment intent from Stripe
            print(f"Fetching payment intent: {payment_intent_id}")
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status != 'succeeded':
                print(f"ERROR: Payment not successful (status: {payment_intent.status})")
                return False
            
            # Check if already exists
            existing = GivingTransaction.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if existing:
                print(f"✅ Transaction already exists: ${existing.amount} on {existing.created_at}")
                return True
            
            # Get person from metadata
            metadata = payment_intent.get('metadata', {})
            email = metadata.get('person_email')
            if not email:
                print("ERROR: No email in payment metadata")
                return False
            
            print(f"Looking up person: {email}")
            person = get_person_by_email(email)
            if not person:
                print(f"ERROR: Person not found for email: {email}")
                return False
            
            # Get giving details
            giving_type = metadata.get('giving_type', 'tithe')
            campus = metadata.get('campus', person.campus) or 'paradise'
            source = metadata.get('source', 'app')
            amount = payment_intent.amount / 100
            
            # Create transaction
            transaction = GivingTransaction(
                person_id=person.id,
                stripe_payment_intent_id=payment_intent_id,
                amount=amount,
                currency=payment_intent.get('currency', 'AUD').upper(),
                giving_type=giving_type,
                campus=campus,
                source=source,
                status='completed',
                created_at=datetime.fromtimestamp(payment_intent['created'], tz=timezone.utc)
            )
            db.session.add(transaction)
            
            # Update engagement profile
            engagement = person.engagement_profile
            if not engagement:
                engagement = EngagementProfile(person_id=person.id)
                db.session.add(engagement)
            
            engagement.add_giving(
                amount=transaction.amount,
                giving_date=datetime.now(timezone.utc).date(),
                campus=transaction.campus
            )
            engagement.recalculate_heartbeat()
            
            db.session.commit()
            print(f"✅ Successfully synced payment: ${amount} from {email}")
            print(f"   Transaction ID: {transaction.id}")
            print(f"   Type: {giving_type}, Campus: {campus}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python sync_payment.py <payment_intent_id>")
        print("Example: python sync_payment.py pi_3SVQhL0vXFTJ3Cth0vqfgWmC")
        sys.exit(1)
    
    payment_intent_id = sys.argv[1]
    success = sync_payment(payment_intent_id)
    sys.exit(0 if success else 1)

