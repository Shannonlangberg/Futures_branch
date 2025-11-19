"""Transfer routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session
from datetime import datetime, timezone
from models.transfer import Transfer, TransferStatus
from services.events import log_event

bp = Blueprint('transfer', __name__, url_prefix='/api/transfer')

@bp.route('/<transfer_id>/accept', methods=['POST'])
@require_auth
def accept_transfer(transfer_id: str):
    """Accept a transfer"""
    leader_info = get_current_leader()
    if not leader_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    session = next(get_session())
    transfer = session.get(Transfer, transfer_id)
    
    if not transfer:
        return jsonify({"error": "Transfer not found"}), 404
    
    if transfer.to_leader_id != leader_info["leader_id"]:
        return jsonify({"error": "Not authorized to accept this transfer"}), 403
    
    if transfer.status != TransferStatus.SENT:
        return jsonify({"error": "Transfer not in SENT status"}), 400
    
    transfer.status = TransferStatus.ACCEPTED
    transfer.accepted_at = datetime.now(timezone.utc)
    session.add(transfer)
    session.commit()
    
    # Log event
    log_event(
        session,
        "transfer_accepted",
        {
            "transfer_id": transfer.id,
            "person_id": transfer.person_id
        },
        leader_info["leader_id"]
    )
    
    return jsonify({
        "id": transfer.id,
        "status": transfer.status.value,
        "accepted_at": transfer.accepted_at.isoformat()
    })








