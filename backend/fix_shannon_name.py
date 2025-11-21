#!/usr/bin/env python3
"""Fix Shannon's name in the database"""

from app import app
from models import db, Person

def fix_shannon_name():
    with app.app_context():
        person = Person.query.filter(
            db.func.lower(Person.email) == 'shannon.langberg@futures.church',
            Person.is_active == True
        ).first()
        
        if not person:
            print("❌ Person not found")
            return
        
        print(f"Found person: {person.id}")
        print(f"Current name: {person.full_name}")
        print(f"Email: {person.email}")
        
        # Update name
        person.full_name = "Shannon Langberg"
        person.preferred_name = "Shannon"
        
        db.session.commit()
        
        print(f"\n✅ Updated name to: {person.full_name}")
        print(f"✅ Preferred name: {person.preferred_name}")

if __name__ == '__main__':
    fix_shannon_name()

