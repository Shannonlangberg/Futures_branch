"""Passport routes - user-facing passport view"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth
from core.db import get_session
from sqlmodel import Session, select
from models.person import Person
from models.stamp import Stamp
from models.track import Track, TrackStop
from models.assignment import Assignment, AssignmentStatus

bp = Blueprint('passport', __name__, url_prefix='/api/passport')

@bp.route('/<person_id>', methods=['GET'])
@require_auth
def get_passport(person_id: str):
    """Get passport for a person - zones, stamps, next step"""
    session = next(get_session())
    person = session.get(Person, person_id)
    
    if not person:
        return jsonify({"error": "Person not found"}), 404
    
    # Get all stamps
    stamps_stmt = select(Stamp).where(Stamp.person_id == person_id)
    stamps = session.exec(stamps_stmt).all()
    
    # Get stamps with track stop info
    stamp_details = []
    for stamp in stamps:
        track_stop = session.get(TrackStop, stamp.track_stop_id)
        if track_stop:
            track = session.get(Track, track_stop.track_id)
            stamp_details.append({
                "id": stamp.id,
                "track_stop_id": stamp.track_stop_id,
                "track_stop_name": track_stop.name,
                "track_id": track_stop.track_id,
                "track_name": track.name if track else "Unknown",
                "stamped_at": stamp.stamped_at.isoformat()
            })
    
    # Get next step (next incomplete assignment)
    next_step = None
    if person.active_track_id:
        # Get track stops
        stops_stmt = select(TrackStop).where(
            TrackStop.track_id == person.active_track_id
        ).order_by(TrackStop.order_index)
        stops = session.exec(stops_stmt).all()
        
        # Find first stop without a stamp
        for stop in stops:
            has_stamp = any(s.track_stop_id == stop.id for s in stamps)
            if not has_stamp:
                # Check for active assignment
                assignment_stmt = select(Assignment).where(
                    Assignment.person_id == person_id,
                    Assignment.track_stop_id == stop.id,
                    Assignment.status.in_([AssignmentStatus.NEW, AssignmentStatus.IN_PROGRESS])
                )
                assignment = session.exec(assignment_stmt).first()
                
                next_step = {
                    "track_stop_id": stop.id,
                    "track_stop_name": stop.name,
                    "order_index": stop.order_index,
                    "has_assignment": assignment is not None,
                    "assignment_id": assignment.id if assignment else None
                }
                break
    
    return jsonify({
        "person_id": person.id,
        "full_name": person.full_name,
        "current_zone": person.current_zone.value,
        "pulse_score": person.pulse_score,
        "active_track_id": person.active_track_id,
        "stamps": stamp_details,
        "next_step": next_step
    })

