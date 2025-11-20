"""Authentication and JWT utilities"""
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ISSUER = os.getenv("JWT_ISSUER", "futures-pulse")
DEV_AUTH_ENABLED = os.getenv("DEV_AUTH_ENABLED", "true").lower() == "true"

def create_jwt_token(leader_id: str, email: str, role: str) -> str:
    """Create a JWT token for a leader"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": leader_id,
        "email": email,
        "role": role,
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], issuer=JWT_ISSUER)
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_leader() -> Optional[Dict]:
    """Get current leader from JWT token or dev header"""
    if DEV_AUTH_ENABLED:
        dev_user = request.headers.get("X-Dev-User")
        if dev_user:
            # Parse dev user format: "leader_id|email|role"
            parts = dev_user.split("|")
            if len(parts) >= 2:
                return {
                    "leader_id": parts[0],
                    "email": parts[1],
                    "role": parts[2] if len(parts) > 2 else "mentor"
                }
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt_token(token)
    return payload

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        leader = get_current_leader()
        if not leader:
            return jsonify({"error": "Unauthorized"}), 401
        request.current_leader = leader
        return f(*args, **kwargs)
    return decorated_function











