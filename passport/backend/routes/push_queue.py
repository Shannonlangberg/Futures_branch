"""Push queue routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth
from core.db import get_session
from services.ai_suggester import get_push_queue

bp = Blueprint('push_queue', __name__, url_prefix='/api/push-queue')

@bp.route('', methods=['GET'])
@require_auth
def get_push_queue_route():
    """Get push queue - people ready to move to next stop"""
    session = next(get_session())
    campus_id = request.args.get('campus_id')
    
    candidates = get_push_queue(session, campus_id)
    
    return jsonify(candidates)












