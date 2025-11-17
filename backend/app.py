@app.route('/api/session')
def session_info():
    if current_user.is_authenticated:
        # Check if user needs Google Drive auth (admin users only)
        needs_drive_auth = False
        if current_user.role in ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']:
            # Check if Google Drive is authenticated
            drive_authenticated = session.get('google_drive_authenticated', False)
            # Check if token is still valid
            token_expiry = session.get('google_drive_token_expiry', 0)
            token_valid = token_expiry > datetime.now(timezone.utc).timestamp()
            
            # Admin users need Drive auth if not authenticated or token expired
            needs_drive_auth = not (drive_authenticated and token_valid)
        
        return jsonify({
            "authenticated": True,
            "user": current_user.username,
            "role": current_user.role,
            "campus": current_user.campus,
            "full_name": current_user.full_name,
            "needs_drive_auth": needs_drive_auth,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        return jsonify({
            "authenticated": False,
            "user": None,
            "role": None,
            "campus": None,
            "full_name": None,
            "needs_drive_auth": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
