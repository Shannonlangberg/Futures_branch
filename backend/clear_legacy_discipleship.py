#!/usr/bin/env python3
"""Clear legacy discipleship data from Person table columns"""

from app import app
from models import db, Person

def clear_legacy_data():
    with app.app_context():
        person = Person.query.filter(
            db.func.lower(Person.email) == 'shannon.langberg@futures.church',
            Person.is_active == True
        ).first()
        
        if not person:
            print("❌ Person not found")
            return
        
        print("="*80)
        print(f"CLEARING LEGACY DATA FOR: {person.full_name}")
        print("="*80)
        
        print("\n🗑️  Old data being cleared:")
        print(f"   - dna_completed: {person.dna_completed}")
        print(f"   - baptised_on: {person.baptised_on}")
        print(f"   - filled_holy_spirit: {person.filled_holy_spirit}")
        print(f"   - rise_attended: {person.rise_attended}")
        print(f"   - first_served_on: {person.first_served_on}")
        
        # Clear all legacy discipleship columns
        person.dna_completed = None
        person.baptised_on = None
        person.filled_holy_spirit = None
        person.rise_attended = None
        person.first_served_on = None
        
        db.session.commit()
        
        print("\n✅ Legacy discipleship data cleared!")
        print("\n📋 Person record now:")
        print(f"   - Full Name: {person.full_name}")
        print(f"   - Email: {person.email}")
        print(f"   - Campus: {person.campus}")
        print(f"   - Connect Group: {person.connect_group}")
        print(f"   - All legacy discipleship columns: None")
        
        print("\n🎯 Ready for new system!")
        print("   Use the Pathway system to track discipleship progress")
        print("="*80)

if __name__ == '__main__':
    clear_legacy_data()

