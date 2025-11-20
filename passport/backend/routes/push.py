"""Push routes - create assignments and transfers"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session
from datetime import datetime, timezone
from models.assignment import Assignment, AssignmentStatus
from models.transfer import Transfer, TransferStatus
from services.events import log_event

bp = Blueprint('push', __name__, url_prefix='/api/push')

@bp.route('', methods=['POST'])
@require_auth
def create_push():
    """Create assignment and transfer"""
    leader_info = get_current_leader()
    if not leader_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    person_id = data.get('person_id')
    track_stop_id = data.get('track_stop_id')
    mentor_leader_id = data.get('mentor_leader_id')
    due_at_str = data.get('due_at')
    
    if not all([person_id, track_stop_id, mentor_leader_id]):
        return jsonify({"error": "Missing required fields"}), 400
    
    session = next(get_session())
    
    # Parse due_at
    due_at = None
    if due_at_str:
        try:
            due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
        except:
            return jsonify({"error": "Invalid due_at format"}), 400
    
    # Create assignment
    assignment = Assignment(
        person_id=person_id,
        track_stop_id=track_stop_id,
        mentor_leader_id=mentor_leader_id,
        status=AssignmentStatus.NEW,
        due_at=due_at,
        created_by=leader_info["leader_id"],
        created_at=datetime.now(timezone.utc)
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    
    # Create transfer if from_leader_id is provided
    from_leader_id = data.get('from_leader_id')
    if from_leader_id:
        transfer = Transfer(
            person_id=person_id,
            from_leader_id=from_leader_id,
            to_leader_id=mentor_leader_id,
            track_stop_id=track_stop_id,
            status=TransferStatus.SENT,
            created_at=datetime.now(timezone.utc)
        )
        session.add(transfer)
        session.commit()
        session.refresh(transfer)
        
        # Log event
        log_event(
            session,
            "assignment_pushed",
            {
                "assignment_id": assignment.id,
                "transfer_id": transfer.id,
                "person_id": person_id,
                "from_leader": from_leader_id,
                "to_leader": mentor_leader_id
            },
            leader_info["leader_id"]
        )
        
        return jsonify({
            "assignment": {
                "id": assignment.id,
                "status": assignment.status.value
            },
            "transfer": {
                "id": transfer.id,
                "status": transfer.status.value
            }
        })
    
    # Log event
    log_event(
        session,
        "assignment_created",
        {
            "assignment_id": assignment.id,
            "person_id": person_id,
            "mentor_leader": mentor_leader_id
        },
        leader_info["leader_id"]
    )
    
    return jsonify({
        "assignment": {
            "id": assignment.id,
            "status": assignment.status.value
        }
    })











