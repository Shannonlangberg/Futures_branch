"""Seed script for initial data"""
from core.db import get_session
from models.person import Person, Zone
from models.track import Track, TrackStop
from models.leader import Leader, LeaderRole
from models.assignment import Assignment, AssignmentStatus
from datetime import datetime, timezone, timedelta
import json

def seed_database():
    """Seed the database with initial data"""
    session = next(get_session())
    
    # Campus
    campus_id = "copper-coast"
    
    # Create people
    people_data = [
        {"name": "Jeff", "email": "jeff@example.com", "zone": Zone.FOUND},
        {"name": "Sarah", "email": "sarah@example.com", "zone": Zone.FAITHFUL},
        {"name": "Mike", "email": "mike@example.com", "zone": Zone.FOUND},
        {"name": "Emma", "email": "emma@example.com", "zone": Zone.FAITHFUL},
        {"name": "Tom", "email": "tom@example.com", "zone": Zone.FOUND},
        {"name": "Lisa", "email": "lisa@example.com", "zone": Zone.FOUND},
        {"name": "David", "email": "david@example.com", "zone": Zone.FAITHFUL},
        {"name": "Rachel", "email": "rachel@example.com", "zone": Zone.FOUND},
        {"name": "John", "email": "john@example.com", "zone": Zone.FOUND},
        {"name": "Amy", "email": "amy@example.com", "zone": Zone.FOUND},
        {"name": "Chris", "email": "chris@example.com", "zone": Zone.FOUND},
        {"name": "Jessica", "email": "jessica@example.com", "zone": Zone.FOUND},
    ]
    
    people = []
    for p_data in people_data:
        person = Person(
            full_name=p_data["name"],
            email=p_data["email"],
            campus_id=campus_id,
            current_zone=p_data["zone"],
            pulse_score=50 if p_data["zone"] == Zone.FAITHFUL else 30
        )
        session.add(person)
        people.append(person)
    
    session.commit()
    
    # Create leaders (first 6 people become leaders)
    # Note: We need to create leader people first, then assign them as leaders
    leader_people_data = [
        {"name": "Sheena", "email": "sheena@example.com", "zone": Zone.FAITHFUL},
        {"name": "Tom", "email": "tom@example.com", "zone": Zone.FAITHFUL},
        {"name": "Emma", "email": "emma@example.com", "zone": Zone.FAITHFUL},
        {"name": "Shannon", "email": "shannon@example.com", "zone": Zone.FOCUSED},
        {"name": "Mike", "email": "mike@example.com", "zone": Zone.FAITHFUL},
        {"name": "Lisa", "email": "lisa@example.com", "zone": Zone.FAITHFUL},
    ]
    
    leader_people = []
    for lp_data in leader_people_data:
        person = Person(
            full_name=lp_data["name"],
            email=lp_data["email"],
            campus_id=campus_id,
            current_zone=lp_data["zone"],
            pulse_score=70
        )
        session.add(person)
        leader_people.append(person)
    
    session.commit()
    
    leaders_data = [
        {"person": leader_people[0], "role": LeaderRole.TRACK_OWNER, "capacity": 8},
        {"person": leader_people[1], "role": LeaderRole.MENTOR, "capacity": 5},
        {"person": leader_people[2], "role": LeaderRole.MENTOR, "capacity": 6},
        {"person": leader_people[3], "role": LeaderRole.CAMPUS_PASTOR, "capacity": 10},
        {"person": leader_people[4], "role": LeaderRole.MENTOR, "capacity": 4},
        {"person": leader_people[5], "role": LeaderRole.MENTOR, "capacity": 5},
    ]
    
    leaders = []
    for l_data in leaders_data:
        leader = Leader(
            person_id=l_data["person"].id,
            role=l_data["role"],
            campus_id=campus_id,
            capacity_slots=l_data["capacity"],
            is_active=True
        )
        session.add(leader)
        leaders.append(leader)
    
    session.commit()
    
    # Create Worship track
    track_owner = leaders[0]  # Sheena
    track = Track(
        name="Worship",
        owner_leader_id=track_owner.id,
        campus_id=campus_id,
        is_active=True
    )
    session.add(track)
    session.commit()
    
    # Create track stops
    stops_data = [
        {"name": "Join Team", "order": 1},
        {"name": "Rehearsals", "order": 2},
        {"name": "Workshop", "order": 3},
        {"name": "Platform Shadowing", "order": 4},
    ]
    
    stops = []
    for s_data in stops_data:
        stop = TrackStop(
            track_id=track.id,
            name=s_data["name"],
            order_index=s_data["order"],
            requirements_json='{"required_fields": ["attendance_tag"]}'
        )
        session.add(stop)
        stops.append(stop)
    
    session.commit()
    
    # Assign 8 people to track (use the regular people, not leader people)
    assigned_people = people[:8]
    for person in assigned_people:
        person.active_track_id = track.id
    
    session.commit()
    
    # Create assignments for first 5 people (first stop)
    first_stop = stops[0]
    mentor = leaders[1]  # Tom
    
    assignments = []
    for i, person in enumerate(assigned_people[:5]):
        status = AssignmentStatus.IN_PROGRESS if i == 0 else AssignmentStatus.NEW
        assignment = Assignment(
            person_id=person.id,
            track_stop_id=first_stop.id,
            mentor_leader_id=mentor.id,
            status=status,
            due_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_by=track_owner.id,
            created_at=datetime.now(timezone.utc)
        )
        session.add(assignment)
        assignments.append(assignment)
    
    session.commit()
    
    print(f"✅ Seeded database:")
    print(f"   - {len(people)} people created")
    print(f"   - {len(leaders)} leaders created")
    print(f"   - 1 track created (Worship)")
    print(f"   - {len(stops)} track stops created")
    print(f"   - {len(assignments)} assignments created")
    print(f"   - 8 people assigned to track")
    print(f"   - 3 people in push queue (ready to move)")

if __name__ == "__main__":
    seed_database()

