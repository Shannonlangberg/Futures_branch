#!/usr/bin/env python3
"""
Check GivingSummary table for a person and verify it's being updated
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Person, GivingSummary, GivingTransaction
from datetime import datetime, timedelta

def check_giving_summary(email='Shannon.langberg@futures.church'):
    """Check giving summary for a person"""
    with app.app_context():
        print("="*80)
        print(f"GIVING SUMMARY CHECK FOR: {email}")
        print("="*80)
        
        # Find person
        person = Person.query.filter(
            db.func.lower(Person.email) == db.func.lower(email)
        ).first()
        
        if not person:
            print(f"❌ Person not found for {email}")
            return
        
        print(f"\n✅ Person found: {person.id} - {person.full_name}")
        print(f"   Campus: {person.campus}")
        
        # Check GivingTransactions
        print("\n" + "="*80)
        print("GIVING TRANSACTIONS")
        print("="*80)
        
        all_transactions = GivingTransaction.query.filter_by(
            person_id=person.id,
            status='completed'
        ).order_by(GivingTransaction.created_at.desc()).all()
        
        print(f"Found {len(all_transactions)} completed transactions")
        for t in all_transactions[:10]:  # Show last 10
            print(f"  - {t.created_at}: ${t.amount} ({t.giving_type})")
        
        # Check last 12 weeks
        period_end = datetime.now().date()
        period_start = period_end - timedelta(weeks=12)
        
        recent_transactions = [t for t in all_transactions 
                              if t.created_at.date() >= period_start]
        
        print(f"\n📊 Last 12 weeks ({period_start} to {period_end}):")
        print(f"   Transactions: {len(recent_transactions)}")
        if recent_transactions:
            total = sum(t.amount for t in recent_transactions)
            print(f"   Total amount: ${total:.2f}")
        
        # Check GivingSummary records
        print("\n" + "="*80)
        print("GIVING SUMMARY RECORDS")
        print("="*80)
        
        summaries = GivingSummary.query.filter_by(
            person_id=person.id
        ).order_by(GivingSummary.period_end.desc()).all()
        
        print(f"Found {len(summaries)} giving summary records")
        for summary in summaries:
            print(f"\n  📅 Period: {summary.period_start} to {summary.period_end}")
            print(f"     Frequency: {summary.frequency}")
            print(f"     Pattern Score: {summary.pattern_score:.2f}")
            print(f"     Last Gift: {summary.last_gift_at}")
            print(f"     Updated: {summary.updated_at}")
        
        # Calculate what frequency SHOULD be
        print("\n" + "="*80)
        print("EXPECTED FREQUENCY CALCULATION")
        print("="*80)
        
        count = len(recent_transactions)
        if count >= 10:
            expected = 'weekly'
        elif count >= 3:
            expected = 'monthly'
        elif count >= 1:
            expected = 'occasional'
        else:
            expected = 'none'
        
        print(f"Transaction count in last 12 weeks: {count}")
        print(f"Expected frequency: {expected}")
        
        if summaries:
            latest = summaries[0]
            if latest.frequency == expected:
                print(f"✅ Frequency matches! ({latest.frequency})")
            else:
                print(f"❌ Frequency mismatch! Expected: {expected}, Got: {latest.frequency}")
        else:
            print(f"⚠️  No GivingSummary records found - needs to be created!")

if __name__ == '__main__':
    email = sys.argv[1] if len(sys.argv) > 1 else 'Shannon.langberg@futures.church'
    check_giving_summary(email)

