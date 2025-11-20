"""Complete assignment routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session
from datetime import datetime, timezone
from models.assignment import Assignment, AssignmentStatus
from services.verifier import verify_completion, auto_stamp_on_completion
from services.events import log_event
import json

bp = Blueprint('complete', __name__, url_prefix='/api/complete')

@bp.route('', methods=['POST'])
@require_auth
def complete_assignment():
    """Mark assignment as complete"""
    leader_info = get_current_leader()
    if not leader_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    assignment_id = data.get('assignment_id')
    outcome = data.get('outcome', 'COMPLETE')
    evidence = data.get('evidence_json', {})
    
    if not assignment_id:
        return jsonify({"error": "assignment_id required"}), 400
    
    session = next(get_session())
    assignment = session.get(Assignment, assignment_id)
    
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    
    if assignment.mentor_leader_id != leader_info["leader_id"]:
        return jsonify({"error": "Not authorized to complete this assignment"}), 403
    
    # Verify completion
    if not verify_completion(session, assignment, evidence):
        return jsonify({"error": "Completion evidence does not meet requirements"}), 400
    
    # Update assignment
    if outcome == 'COMPLETE':
        assignment.status = AssignmentStatus.COMPLETE
        assignment.completed_at = datetime.now(timezone.utc)
    elif outcome == 'NO_SHOW':
        assignment.status = AssignmentStatus.NO_SHOW
    else:
        assignment.status = AssignmentStatus.COMPLETE
        assignment.completed_at = datetime.now(timezone.utc)
    
    assignment.evidence_json = json.dumps(evidence)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    
    # Auto-stamp if complete
    stamp_created = False
    if assignment.status == AssignmentStatus.COMPLETE:
        stamp_created = auto_stamp_on_completion(session, assignment)
    
    # Log event
    log_event(
        session,
        "assignment_completed",
        {
            "assignment_id": assignment.id,
            "outcome": outcome,
            "stamp_created": stamp_created
        },
        leader_info["leader_id"]
    )
    
    return jsonify({
        "id": assignment.id,
        "status": assignment.status.value,
        "completed_at": assignment.completed_at.isoformat() if assignment.completed_at else None,
        "stamp_created": stamp_created
    })










