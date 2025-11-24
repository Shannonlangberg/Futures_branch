"""AI heuristic service for push queue suggestions"""
from sqlmodel import Session, select, func
from models.person import Person
from models.assignment import Assignment, AssignmentStatus
from models.activity import Activity, ActivityType
from datetime import datetime, timezone, timedelta
from typing import List, Dict

def get_push_queue(session: Session, campus_id: str = None) -> List[Dict]:
    """
    AI heuristic to identify people ready to move to next track stop.
    Returns candidates with readiness score.
    """
    # Base query for people
    statement = select(Person)
    if campus_id:
        statement = statement.where(Person.campus_id == campus_id)
    
    people = session.exec(statement).all()
    candidates = []
    
    for person in people:
        # Get current assignments
        assignments_stmt = select(Assignment).where(
            Assignment.person_id == person.id,
            Assignment.status == AssignmentStatus.COMPLETE
        )
        completed = session.exec(assignments_stmt).all()
        
        # Get recent activities (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        activities_stmt = select(Activity).where(
            Activity.person_id == person.id,
            Activity.occurred_at >= thirty_days_ago
        )
        activities = session.exec(activities_stmt).all()
        
        # Calculate readiness score
        score = 0
        
        # Points for completed assignments
        score += len(completed) * 10
        
        # Points for attendance (ATTEND activities)
        attend_count = len([a for a in activities if a.type == ActivityType.ATTEND])
        score += min(attend_count * 5, 25)  # Max 25 points
        
        # Points for serving (SERVE activities)
        serve_count = len([a for a in activities if a.type == ActivityType.SERVE])
        score += min(serve_count * 8, 24)  # Max 24 points
        
        # Points for pulse score
        score += person.pulse_score
        
        # Only include if score > threshold
        if score >= 30:
            candidates.append({
                "person_id": person.id,
                "full_name": person.full_name,
                "campus_id": person.campus_id,
                "current_zone": person.current_zone.value,
                "pulse_score": person.pulse_score,
                "readiness_score": score,
                "completed_assignments": len(completed),
                "recent_activities": len(activities)
            })
    
    # Sort by readiness score descending
    candidates.sort(key=lambda x: x["readiness_score"], reverse=True)
    return candidates













