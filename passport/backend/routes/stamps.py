"""Stamp routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session, select
from models.stamp import Stamp
from models.person import Person
from models.track import TrackStop

bp = Blueprint('stamps', __name__, url_prefix='/api/stamps')

@bp.route('/pending', methods=['GET'])
@require_auth
def get_pending_stamps():
    """Get pending stamps (for approval workflow if needed)"""
    session = next(get_session())
    
    # Get all stamps (you can add approval logic here)
    statement = select(Stamp).order_by(Stamp.stamped_at.desc())
    stamps = session.exec(statement).all()
    
    result = []
    for stamp in stamps:
        person = session.get(Person, stamp.person_id)
        track_stop = session.get(TrackStop, stamp.track_stop_id)
        
        result.append({
            "id": stamp.id,
            "person_id": stamp.person_id,
            "person_name": person.full_name if person else "Unknown",
            "track_stop_id": stamp.track_stop_id,
            "track_stop_name": track_stop.name if track_stop else "Unknown",
            "stamped_by": stamp.stamped_by,
            "stamped_at": stamp.stamped_at.isoformat()
        })
    
    return jsonify(result)

@bp.route('/<stamp_id>/approve', methods=['POST'])
@require_auth
def approve_stamp(stamp_id: str):
    """Approve a stamp (if approval workflow is enabled)"""
    # For now, stamps are auto-approved on creation
    # This endpoint can be extended for approval workflows
    session = next(get_session())
    stamp = session.get(Stamp, stamp_id)
    
    if not stamp:
        return jsonify({"error": "Stamp not found"}), 404
    
    return jsonify({
        "id": stamp.id,
        "status": "approved"
    })

