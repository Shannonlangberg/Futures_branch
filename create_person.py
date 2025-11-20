#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/shannonlangberg/Documents/Futures_PulseV1.1/backend')

from app import app, db, Person, EngagementProfile
import uuid

with app.app_context():
    # Check if person already exists
    existing = Person.query.filter_by(email='shannon.langberg@futures.church').first()
    if existing:
        print(f"Person already exists: {existing.id} - {existing.full_name}")
    else:
        # Create person record
        person = Person(
            id=f'pco_{uuid.uuid4().hex[:8]}',
            full_name='Shannon Langberg',
            preferred_name='Shannon',
            email='shannon.langberg@futures.church',
            phone='0424 156 023',
            campus='copper_coast',
            department='Adults',
            is_active=True
        )
        db.session.add(person)
        db.session.flush()
        
        # Create engagement profile
        engagement = EngagementProfile(person_id=person.id)
        db.session.add(engagement)
        
        db.session.commit()
        print(f"✅ Created Person: {person.id} - {person.full_name}")
