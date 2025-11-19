#!/usr/bin/env python3
"""
Seed script for Heartbeat module

Creates initial Heartbeat data for testing:
- Heartbeat campuses from existing campuses
- Sample services
- Optionally: test attendance events, connect groups, etc.
"""
import os
import sys
from datetime import datetime, timedelta, date
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Campus, Service, Person
from config.database import build_sqlalchemy_settings

def seed_heartbeat_campuses():
    """Create Heartbeat campus records from existing Person.campus values"""
    print("[HEARTBEAT SEED] Creating Heartbeat campuses...")
    
    # Get unique campus names from Person table
    persons = Person.query.all()
    campus_names = set()
    for person in persons:
        if person.campus:
            campus_names.add(person.campus)
    
    print(f"[HEARTBEAT SEED] Found {len(campus_names)} unique campuses from Person records")
    
    created = 0
    for campus_name in campus_names:
        # Normalize to campus_id
        campus_id = campus_name.lower().replace(' ', '_')
        
        # Check if already exists
        existing = Campus.query.filter_by(id=campus_id).first()
        if existing:
            print(f"[HEARTBEAT SEED] Campus {campus_name} already exists")
            continue
        
        # Create new campus
        campus = Campus(
            id=campus_id,
            name=campus_name,
            timezone='Australia/Adelaide',
            is_active=True
        )
        db.session.add(campus)
        created += 1
        print(f"[HEARTBEAT SEED] Created campus: {campus_name} ({campus_id})")
    
    db.session.commit()
    print(f"[HEARTBEAT SEED] Created {created} new Heartbeat campuses")
    return created


def seed_sample_services(days_back=84):
    """Create sample Sunday services for the last 12 weeks"""
    print(f"[HEARTBEAT SEED] Creating sample services for last {days_back} days...")
    
    # Get all active campuses
    campuses = Campus.query.filter_by(is_active=True).all()
    if not campuses:
        print("[HEARTBEAT SEED] No campuses found. Run seed_heartbeat_campuses first.")
        return 0
    
    created = 0
    today = datetime.now()
    
    for campus in campuses:
        # Create Sunday services for the last 12 weeks
        for week in range(12):
            # Calculate Sunday date (12 weeks ago + week offset)
            sunday_date = today - timedelta(weeks=12-week)
            # Get the most recent Sunday
            days_since_sunday = sunday_date.weekday() + 1  # Monday=0, Sunday=6
            if days_since_sunday == 7:
                days_since_sunday = 0
            sunday_date = sunday_date - timedelta(days=days_since_sunday)
            
            # Create 9:00 AM service
            service_time = datetime.combine(sunday_date.date(), datetime.min.time().replace(hour=9))
            
            # Check if service already exists
            existing = Service.query.filter_by(
                campus_id=campus.id,
                type='sunday',
                starts_at=service_time
            ).first()
            
            if existing:
                continue
            
            service = Service(
                campus_id=campus.id,
                type='sunday',
                starts_at=service_time,
                ends_at=service_time + timedelta(hours=2)
            )
            db.session.add(service)
            created += 1
    
    db.session.commit()
    print(f"[HEARTBEAT SEED] Created {created} sample services")
    return created


def seed_test_data():
    """Create minimal test data for demonstration"""
    print("[HEARTBEAT SEED] Creating test data...")
    
    # This is optional - you can add test attendance, connect groups, etc. here
    # For now, we'll just create the structure
    
    print("[HEARTBEAT SEED] Test data creation complete")
    print("[HEARTBEAT SEED] Next steps:")
    print("  1. Create attendance events via API or database")
    print("  2. Create connect groups and attendance")
    print("  3. Create serving assignments")
    print("  4. Run recalculation: POST /api/heartbeat/recalculate/{campus_id}")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("HEARTBEAT MODULE SEED SCRIPT")
    print("=" * 60)
    
    # Create Flask app for context
    from flask import Flask
    from config.database import build_sqlalchemy_settings
    
    app = Flask(__name__)
    app.config.update(build_sqlalchemy_settings())
    db.init_app(app)
    
    with app.app_context():
        try:
            # Step 1: Create Heartbeat campuses
            seed_heartbeat_campuses()
            
            # Step 2: Create sample services
            seed_sample_services()
            
            # Step 3: Optional test data
            # seed_test_data()
            
            print("=" * 60)
            print("SEEDING COMPLETE!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Add attendance events (via API or database)")
            print("2. Create connect groups and record attendance")
            print("3. Add serving assignments")
            print("4. Run recalculation from dashboard or API")
            print("\nTo recalculate a campus:")
            print("  POST /api/heartbeat/recalculate/{campus_id}")
            print("  Or use the 'Recalculate Campus' button in the dashboard")
            
        except Exception as e:
            print(f"[HEARTBEAT SEED] ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

