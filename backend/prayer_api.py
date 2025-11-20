# prayer_api.py
from flask import Blueprint, jsonify, request
from models import db, Person, CareCase
from datetime import datetime
import logging
import sqlite3

logger = logging.getLogger(__name__)

prayer_bp = Blueprint('prayer', __name__, url_prefix='/api/prayer')

def get_db_path():
    """Get the database path from Flask app config"""
    from flask import current_app
    import os
    try:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_path = db_uri.replace('sqlite:///', '').replace('sqlite:////', '')
        if not os.path.isabs(db_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            instance_path = os.path.join(backend_dir, 'instance', 'futures_link.db')
            db_path = instance_path if os.path.exists(instance_path) else os.path.join(backend_dir, 'futures_link.db')
        return db_path
    except Exception as e:
        logger.warning(f"Error getting db path: {e}, using fallback")
        return 'instance/futures_link.db'

def get_campus_pastor(campus):
    """Find the campus pastor for a given campus"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, full_name, email
            FROM users
            WHERE role = 'campus_pastor' 
            AND campus = ?
            AND active = 1
            LIMIT 1
        ''', (campus,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'email': row[3]
            }
        return None
    except Exception as e:
        logger.error(f"Error finding campus pastor for {campus}: {e}")
        return None

@prayer_bp.route('/requests', methods=['POST'])
def create_prayer_request():
    """Create a new prayer request - logs to Heartbeat care signals and routes to campus pastor"""
    try:
        data = request.get_json()
        email = data.get('email')
        request_text = data.get('request')
        
        if not email or not request_text:
            return jsonify({'error': 'Email and request text required'}), 400
        
        # Find person by email
        person = Person.query.filter_by(email=email, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Find campus pastor for routing
        campus_pastor = None
        pastor_info = None
        if person.campus and person.campus != 'all_campuses':
            campus_pastor = get_campus_pastor(person.campus)
            if campus_pastor:
                pastor_info = f"Routed to {campus_pastor['full_name']} ({campus_pastor['email']}) - {person.campus} campus pastor"
                logger.info(f"Prayer request from {email} ({person.campus}) - {pastor_info}")
            else:
                logger.warning(f"No campus pastor found for {person.campus} campus")
        
        # Create care case in Heartbeat
        try:
            # Include routing info in details
            details_with_routing = request_text
            if pastor_info:
                details_with_routing += f"\n\n---\n{pastor_info}"
            
            care_case = CareCase(
                person_id=person.id,
                type='prayer_request',
                status='open',
                priority='medium',
                summary=request_text[:500],  # First 500 chars as summary
                details=details_with_routing,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            db.session.commit()
            
            logger.info(f"Prayer request created for {email}: {care_case.id} - Campus: {person.campus}")
            
            response_message = 'Prayer request received'
            if pastor_info:
                response_message += f'. Your campus pastor has been notified.'
            
            return jsonify({
                'success': True,
                'message': response_message,
                'id': care_case.id,
                'routed_to': campus_pastor['email'] if campus_pastor else None
            }), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating care case: {e}")
            return jsonify({'error': 'Failed to create prayer request'}), 500
        
    except Exception as e:
        logger.error(f"Error creating prayer request: {e}")
        return jsonify({'error': str(e)}), 500

@prayer_bp.route('/praise', methods=['POST'])
def create_praise_report():
    """Create a new praise report - logs to Heartbeat care signals and routes to campus pastor"""
    try:
        data = request.get_json()
        email = data.get('email')
        report = data.get('report')
        
        if not email or not report:
            return jsonify({'error': 'Email and report text required'}), 400
        
        # Find person by email
        person = Person.query.filter_by(email=email, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Find campus pastor for routing
        campus_pastor = None
        pastor_info = None
        if person.campus and person.campus != 'all_campuses':
            campus_pastor = get_campus_pastor(person.campus)
            if campus_pastor:
                pastor_info = f"Routed to {campus_pastor['full_name']} ({campus_pastor['email']}) - {person.campus} campus pastor"
                logger.info(f"Praise report from {email} ({person.campus}) - {pastor_info}")
        
        # Create care case in Heartbeat (praise reports are positive care signals)
        try:
            # Include routing info in details
            details_with_routing = report
            if pastor_info:
                details_with_routing += f"\n\n---\n{pastor_info}"
            
            care_case = CareCase(
                person_id=person.id,
                type='praise_report',
                status='open',
                priority='low',
                summary=report[:500],  # First 500 chars as summary
                details=details_with_routing,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            db.session.commit()
            
            logger.info(f"Praise report created for {email}: {care_case.id} - Campus: {person.campus}")
            
            response_message = 'Praise report received'
            if pastor_info:
                response_message += '! Your campus pastor has been notified.'
            
            return jsonify({
                'success': True,
                'message': response_message,
                'id': care_case.id,
                'routed_to': campus_pastor['email'] if campus_pastor else None
            }), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating care case: {e}")
            return jsonify({'error': 'Failed to create praise report'}), 500
        
    except Exception as e:
        logger.error(f"Error creating praise report: {e}")
        return jsonify({'error': str(e)}), 500

