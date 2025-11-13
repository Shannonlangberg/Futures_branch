"""Verification service for assignment completion"""
from sqlmodel import Session
from models.assignment import Assignment, AssignmentStatus
from models.track import TrackStop
from datetime import datetime, timezone
from typing import Dict, Any

def verify_completion(
    session: Session,
    assignment: Assignment,
    evidence: Dict[str, Any]
) -> bool:
    """Verify if assignment completion evidence meets requirements"""
    track_stop = session.get(TrackStop, assignment.track_stop_id)
    if not track_stop:
        return False
    
    requirements = track_stop.get_requirements()
    
    # If no requirements, auto-verify
    if not requirements:
        return True
    
    # Check required fields
    required_fields = requirements.get("required_fields", [])
    for field in required_fields:
        if field not in evidence:
            return False
    
    # Check minimum values
    min_values = requirements.get("min_values", {})
    for key, min_val in min_values.items():
        if key in evidence:
            try:
                if float(evidence[key]) < min_val:
                    return False
            except (ValueError, TypeError):
                return False
    
    return True

def auto_stamp_on_completion(
    session: Session,
    assignment: Assignment
) -> bool:
    """Auto-create stamp when assignment is completed"""
    from models.stamp import Stamp
    
    # Check if stamp already exists
    from sqlmodel import select
    existing_stmt = select(Stamp).where(
        Stamp.person_id == assignment.person_id,
        Stamp.track_stop_id == assignment.track_stop_id
    )
    existing = session.exec(existing_stmt).first()
    if existing:
        return False
    
    # Create stamp
    stamp = Stamp(
        person_id=assignment.person_id,
        track_stop_id=assignment.track_stop_id,
        stamped_by=assignment.mentor_leader_id,
        stamped_at=datetime.now(timezone.utc)
    )
    session.add(stamp)
    session.commit()
    return True

