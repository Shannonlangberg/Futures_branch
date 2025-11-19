"""Authentication routes"""
from flask import Blueprint, request, jsonify
from core.auth import create_jwt_token, get_current_leader, DEV_AUTH_ENABLED
from core.db import get_session
from sqlmodel import Session, select
from models.leader import Leader

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/dev-login', methods=['POST'])
def dev_login():
    """Dev mode login - returns JWT token"""
    if not DEV_AUTH_ENABLED:
        return jsonify({"error": "Dev auth disabled"}), 403
    
    data = request.get_json() or {}
    leader_id = data.get('leader_id')
    email = data.get('email', 'dev@test.com')
    role = data.get('role', 'mentor')
    
    if not leader_id:
        return jsonify({"error": "leader_id required"}), 400
    
    # Create JWT token
    token = create_jwt_token(leader_id, email, role)
    
    return jsonify({
        "token": token,
        "leader_id": leader_id,
        "email": email,
        "role": role
    })









