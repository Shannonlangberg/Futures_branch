#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/shannonlangberg/Documents/Futures_PulseV1.1/backend')

from app import app, db, Person

with app.app_context():
    # Find persons with shannon in name
    persons = Person.query.filter(
        db.or_(
            Person.full_name.ilike('%shannon%'),
            Person.email.ilike('%shannon%')
        ),
        Person.is_active == True
    ).all()
    
    print("Found persons matching 'shannon':")
    for p in persons:
        print(f"  ID: {p.id}")
        print(f"  Name: {p.full_name}")
        print(f"  Email: {p.email}")
        print(f"  ---")
