#!/usr/bin/env python3
"""
Verify that giving data flows through to heartbeat correctly
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Person, GivingSummary, GivingTransaction, EngagementProfile
from heartbeat_engine import HeartbeatEngine
from datetime import datetime, timedelta

def verify_heartbeat_giving(email='Shannon.langberg@futures.church'):
    """Verify giving data in heartbeat calculation"""
    with app.app_context():
        print("="*80)
        print(f"HEARTBEAT GIVING VERIFICATION FOR: {email}")
        print("="*80)
        
        # Find person
        person = Person.query.filter(
            db.func.lower(Person.email) == db.func.lower(email)
        ).first()
        
        if not person:
            print(f"❌ Person not found for {email}")
            return
        
        print(f"\n✅ Person: {person.full_name} ({person.id})")
        print(f"   Campus: {person.campus}")
        
        # Check GivingTransaction
        transactions = GivingTransaction.query.filter_by(
            person_id=person.id,
            status='completed'
        ).count()
        print(f"\n📊 Giving Transactions: {transactions}")
        
        # Check GivingSummary
        summaries = GivingSummary.query.filter_by(
            person_id=person.id
        ).all()
        print(f"📊 Giving Summaries: {len(summaries)}")
        if summaries:
            latest = max(summaries, key=lambda s: s.period_end)
            print(f"   Latest: {latest.frequency} (pattern: {latest.pattern_score:.2f})")
        
        # Check EngagementProfile
        engagement = person.engagement_profile
        if engagement:
            print(f"\n💓 Engagement Profile:")
            print(f"   Pulse Status: {engagement.pulse_status}")
            print(f"   Overall Engagement: {engagement.overall_engagement:.1f}")
            print(f"   Last Seen: {engagement.last_seen}")
        else:
            print(f"\n⚠️  No engagement profile found")
        
        # Run heartbeat calculation
        print("\n" + "="*80)
        print("RUNNING HEARTBEAT CALCULATION")
        print("="*80)
        
        try:
            engine = HeartbeatEngine()
            snapshot = engine.calculate_heartbeat(person.id)
            
            print(f"\n🎯 HEARTBEAT SCORES:")
            print(f"   Gather: {snapshot.gather_score:.1f}")
            print(f"   Engagement: {snapshot.engagement_score:.1f}")
            print(f"   Spiritual: {snapshot.spiritual_score:.1f}")
            print(f"   Care: {snapshot.care_score:.1f}")
            print(f"   TOTAL: {snapshot.total_score:.1f}")
            print(f"   Status: {snapshot.status}")
            
            # Check risk factors
            risk_factors = snapshot.risk_factors.split(',') if snapshot.risk_factors else []
            print(f"\n⚠️  Risk Factors: {len(risk_factors)}")
            for factor in risk_factors:
                if factor.strip():
                    print(f"   - {factor.strip()}")
            
            # Specifically check for giving
            if 'no_giving' in snapshot.risk_factors:
                print(f"\n❌ PROBLEM: 'no_giving' is in risk factors!")
                print(f"   This means heartbeat engine isn't seeing giving data")
            else:
                print(f"\n✅ Good! No 'no_giving' risk factor")
            
            # Check what data the engine loaded
            print("\n" + "="*80)
            print("DATA LOADED BY HEARTBEAT ENGINE")
            print("="*80)
            
            period_end = datetime.now().date()
            period_start = period_end - timedelta(weeks=12)
            
            data = engine._load_person_data(person.id, period_start, period_end)
            
            print(f"Attendance Events: {len(data.get('attendance_events', []))}")
            print(f"Connect Attendance: {len(data.get('connect_attendance', []))}")
            print(f"Active Groups: {len(data.get('active_groups', []))}")
            print(f"Serving Assignments: {len(data.get('serving_assignments', []))}")
            print(f"Giving Summaries: {len(data.get('giving_summaries', []))} ← THIS IS KEY!")
            
            if data.get('giving_summaries'):
                print(f"\n✅ Giving summaries found:")
                for gs in data['giving_summaries']:
                    print(f"   - {gs.period_start} to {gs.period_end}: {gs.frequency}")
            else:
                print(f"\n❌ No giving summaries found - this is the problem!")
            
        except Exception as e:
            print(f"\n❌ Error calculating heartbeat: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    email = sys.argv[1] if len(sys.argv) > 1 else 'Shannon.langberg@futures.church'
    verify_heartbeat_giving(email)

