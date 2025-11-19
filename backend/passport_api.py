# passport_api.py - Passport API routes integrated into Futures Pulse
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
import os
import sys

# Add passport backend to path
passport_backend = os.path.join(os.path.dirname(__file__), '..', 'passport', 'backend')
if os.path.exists(passport_backend):
    sys.path.insert(0, passport_backend)

passport_bp = Blueprint('passport', __name__, url_prefix='/api/passport')

@passport_bp.route('/health', methods=['GET'])
def passport_health():
    """Health check for Passport API"""
    return jsonify({
        "status": "ok",
        "service": "Futures Pulse Passport",
        "integrated": True
    })

@passport_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    """Get current user's passport info (uses Futures Pulse session)"""
    try:
        # Map Futures Pulse user to Passport leader
        # For now, return basic info
        return jsonify({
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "campus": current_user.campus,
            "email": getattr(current_user, 'email', ''),
            "passport_ready": False,  # Will be True when Passport is fully integrated
            "message": "Passport system is being integrated. Use your existing Futures Pulse login."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@passport_bp.route('/info', methods=['GET'])
@login_required
def passport_info():
    """Get Passport system info"""
    return jsonify({
        "status": "integrated",
        "message": "Passport is integrated into Futures Pulse. Use your existing login.",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "campus": current_user.campus
        },
        "backend_status": "ready",
        "frontend_status": "in_progress"
    })









