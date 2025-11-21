#!/usr/bin/env python3
"""
Backfill GivingSummary for all existing transactions
This ensures past transactions are counted in heartbeat
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Person, GivingSummary, GivingTransaction
from datetime import datetime, timedelta, timezone

def update_giving_summary(person_id):
    """
    Update or create GivingSummary for a person based on recent transactions.
    Same logic as webhook handler.
    """
    # Define a rolling 12-week period ending today
    period_end = datetime.now(timezone.utc).date()
    period_start = period_end - timedelta(weeks=12)
    
    # Get all completed transactions in this period
    recent_transactions = GivingTransaction.query.filter(
        GivingTransaction.person_id == person_id,
        GivingTransaction.created_at >= datetime.combine(period_start, datetime.min.time()),
        GivingTransaction.status == 'completed'
    ).all()
    
    transaction_count = len(recent_transactions)
    
    # Calculate frequency based on transaction count
    if transaction_count >= 10:
        frequency = 'weekly'
    elif transaction_count >= 3:
        frequency = 'monthly'
    elif transaction_count >= 1:
        frequency = 'occasional'
    else:
        frequency = 'none'
    
    # Calculate pattern_score (consistency)
    if transaction_count > 1:
        dates = sorted([t.created_at.date() for t in recent_transactions])
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        if avg_interval > 0:
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            std_dev = variance ** 0.5
            pattern_score = max(0.0, min(1.0, 1.0 - (std_dev / (avg_interval + 1))))
        else:
            pattern_score = 1.0
    else:
        pattern_score = 0.0 if transaction_count == 0 else 0.5
    
    # Get last gift date
    last_gift_at = max([t.created_at.date() for t in recent_transactions]) if recent_transactions else None
    
    # Check if summary exists for this period
    existing_summary = GivingSummary.query.filter(
        GivingSummary.person_id == person_id,
        GivingSummary.period_start == period_start,
        GivingSummary.period_end == period_end
    ).first()
    
    if existing_summary:
        # Update existing
        existing_summary.frequency = frequency
        existing_summary.pattern_score = pattern_score
        existing_summary.last_gift_at = last_gift_at
        existing_summary.updated_at = datetime.now(timezone.utc)
        print(f"  ✅ Updated GivingSummary: {frequency}, pattern={pattern_score:.2f}, {transaction_count} transactions")
    else:
        # Create new
        new_summary = GivingSummary(
            person_id=person_id,
            period_start=period_start,
            period_end=period_end,
            frequency=frequency,
            pattern_score=pattern_score,
            last_gift_at=last_gift_at
        )
        db.session.add(new_summary)
        print(f"  ✅ Created GivingSummary: {frequency}, pattern={pattern_score:.2f}, {transaction_count} transactions")
    
    return frequency, pattern_score

def backfill_all():
    """Backfill GivingSummary for all people with transactions"""
    with app.app_context():
        print("="*80)
        print("BACKFILLING GIVING SUMMARY FOR ALL PEOPLE")
        print("="*80)
        
        # Get all people with transactions
        people_with_transactions = db.session.query(GivingTransaction.person_id).distinct().all()
        person_ids = [p[0] for p in people_with_transactions]
        
        print(f"\nFound {len(person_ids)} people with giving transactions")
        print()
        
        updated = 0
        for person_id in person_ids:
            person = Person.query.get(person_id)
            if person:
                print(f"Processing: {person.full_name} ({person.id})")
                try:
                    frequency, pattern = update_giving_summary(person_id)
                    updated += 1
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            else:
                print(f"⚠️  Person {person_id} not found (orphaned transactions)")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "="*80)
            print(f"✅ SUCCESS! Updated {updated} people")
            print("="*80)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing changes: {e}")

if __name__ == '__main__':
    backfill_all()

