#!/usr/bin/env python3
"""
Example script for importing attendance data into Heartbeat

This shows how to:
1. Create attendance events for people
2. Link them to services
3. Recalculate heartbeat scores

Usage:
    python import_attendance_example.py
"""
import os
import sys
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Person, Service, AttendanceEvent, Campus
from config.database import build_sqlalchemy_settings
from heartbeat_engine import HeartbeatEngine

app = Flask(__name__)
app.config.update(build_sqlalchemy_settings())
db.init_app(app)

def import_attendance_for_person(person_id, service_id, source='manual'):
    """Record that a person attended a service"""
    attendance = AttendanceEvent(
        id=str(uuid.uuid4()),
        person_id=person_id,
        service_id=service_id,
        source=source,
        created_at=datetime.utcnow()
    )
    db.session.add(attendance)
    return attendance

def import_attendance_batch(campus_id, person_ids, service_id, source='manual'):
    """Record multiple people attending the same service"""
    attendances = []
    for person_id in person_ids:
        attendance = import_attendance_for_person(person_id, service_id, source)
        attendances.append(attendance)
    db.session.commit()
    return attendances

def example_usage():
    """Example of how to import attendance"""
    with app.app_context():
        # 1. Get a campus
        campus = Campus.query.filter_by(id='copper_coast').first()
        if not campus:
            print("Campus 'copper_coast' not found. Run seed_heartbeat.py first.")
            return
        
        # 2. Get a recent service
        services = Service.query.filter_by(
            campus_id=campus.id,
            type='sunday'
        ).order_by(Service.starts_at.desc()).limit(1).all()
        
        if not services:
            print("No services found. Run seed_heartbeat.py to create services.")
            return
        
        service = services[0]
        print(f"Using service: {service.starts_at} ({service.id})")
        
        # 3. Get some people from this campus
        people = Person.query.filter_by(
            campus=campus.name,
            is_active=True
        ).limit(10).all()
        
        if not people:
            print(f"No active people found for campus {campus.name}")
            return
        
        print(f"Found {len(people)} people")
        
        # 4. Record attendance for these people
        person_ids = [p.id for p in people]
        attendances = import_attendance_batch(
            campus.id,
            person_ids,
            service.id,
            source='manual'
        )
        
        print(f"✅ Recorded attendance for {len(attendances)} people")
        
        # 5. Recalculate heartbeat for these people
        engine = HeartbeatEngine()
        print("\nRecalculating heartbeat scores...")
        
        for person_id in person_ids:
            try:
                snapshot = engine.calculate_heartbeat(
                    person_id=person_id,
                    start_date=datetime.utcnow().date() - timedelta(weeks=12),
                    end_date=datetime.utcnow().date()
                )
                print(f"  ✅ {person_id}: Total score = {snapshot.total_score}")
            except Exception as e:
                print(f"  ❌ {person_id}: Error - {e}")
        
        print("\n✅ Done! Check the dashboard to see updated scores.")

if __name__ == '__main__':
    print("=" * 60)
    print("HEARTBEAT ATTENDANCE IMPORT EXAMPLE")
    print("=" * 60)
    print("\nThis script demonstrates how to import attendance data.")
    print("Modify it to match your data source.\n")
    
    example_usage()




