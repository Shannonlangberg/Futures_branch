"""Inbox routes - assignments for current leader"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session, select
from models.assignment import Assignment, AssignmentStatus
from models.person import Person
from models.track import TrackStop

bp = Blueprint('inbox', __name__, url_prefix='/api/inbox')

@bp.route('', methods=['GET'])
@require_auth
def get_inbox():
    """Get assignments where current leader is mentor"""
    leader_info = get_current_leader()
    if not leader_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    session = next(get_session())
    leader_id = leader_info["leader_id"]
    
    status_filter = request.args.get('status')
    statement = select(Assignment).where(Assignment.mentor_leader_id == leader_id)
    
    if status_filter:
        try:
            status_enum = AssignmentStatus(status_filter)
            statement = statement.where(Assignment.status == status_enum)
        except ValueError:
            pass
    
    assignments = session.exec(statement.order_by(Assignment.created_at.desc())).all()
    
    result = []
    for assignment in assignments:
        person = session.get(Person, assignment.person_id)
        track_stop = session.get(TrackStop, assignment.track_stop_id)
        
        result.append({
            "id": assignment.id,
            "person_id": assignment.person_id,
            "person_name": person.full_name if person else "Unknown",
            "track_stop_id": assignment.track_stop_id,
            "track_stop_name": track_stop.name if track_stop else "Unknown",
            "status": assignment.status.value,
            "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
            "completed_at": assignment.completed_at.isoformat() if assignment.completed_at else None,
            "evidence": assignment.get_evidence(),
            "created_at": assignment.created_at.isoformat()
        })
    
    return jsonify(result)

