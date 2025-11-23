#!/usr/bin/env python3
"""Quick script to get all leader IDs from the database"""
from core.db import get_session
from sqlmodel import Session, select
from models.leader import Leader
from models.person import Person

def get_leaders():
    session = next(get_session())
    leaders = session.exec(select(Leader)).all()
    
    print("\n" + "="*60)
    print("PASSPORT LEADER IDs FOR LOGIN")
    print("="*60 + "\n")
    
    for leader in leaders:
        person = session.get(Person, leader.person_id)
        name = person.full_name if person else "Unknown"
        email = person.email if person else "unknown@example.com"
        
        print(f"Name: {name}")
        print(f"  Leader ID: {leader.id}")
        print(f"  Role: {leader.role.value}")
        print(f"  Email: {email}")
        print(f"  Campus: {leader.campus_id or 'N/A'}")
        print()
    
    print("="*60)
    print("\nTo login, use any Leader ID above with:")
    print("  POST http://localhost:8000/api/auth/dev-login")
    print("  Body: {\"leader_id\": \"<ID>\", \"email\": \"<email>\", \"role\": \"<role>\"}")
    print()

if __name__ == "__main__":
    get_leaders()












