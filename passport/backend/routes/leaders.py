"""Leader routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session, select
from models.leader import Leader
from models.person import Person
from models.assignment import Assignment, AssignmentStatus

bp = Blueprint('leaders', __name__, url_prefix='/api/leaders')

@bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    """Get current leader profile and capacity"""
    leader_info = get_current_leader()
    if not leader_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    session = next(get_session())
    leader_id = leader_info["leader_id"]
    
    leader = session.get(Leader, leader_id)
    if not leader:
        return jsonify({"error": "Leader not found"}), 404
    
    person = session.get(Person, leader.person_id)
    
    # Count active assignments
    active_stmt = select(Assignment).where(
        Assignment.mentor_leader_id == leader_id,
        Assignment.status.in_([AssignmentStatus.NEW, AssignmentStatus.IN_PROGRESS])
    )
    active_assignments = session.exec(active_stmt).all()
    active_count = len(active_assignments)
    
    return jsonify({
        "id": leader.id,
        "person_id": leader.person_id,
        "full_name": person.full_name if person else "Unknown",
        "email": person.email if person else None,
        "role": leader.role.value,
        "campus_id": leader.campus_id,
        "capacity_slots": leader.capacity_slots,
        "active_assignments": active_count,
        "available_slots": max(0, leader.capacity_slots - active_count),
        "is_active": leader.is_active
    })











