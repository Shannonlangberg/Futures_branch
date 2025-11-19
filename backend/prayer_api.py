# prayer_api.py
from flask import Blueprint, jsonify, request
from models import db, Person, CareCase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

prayer_bp = Blueprint('prayer', __name__, url_prefix='/api/prayer')

@prayer_bp.route('/requests', methods=['POST'])
def create_prayer_request():
    """Create a new prayer request - logs to Heartbeat care signals"""
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
        
        # Create care case in Heartbeat
        try:
            care_case = CareCase(
                person_id=person.id,
                type='prayer_request',
                status='open',
                priority='medium',
                summary=request_text[:500],  # First 500 chars as summary
                details=request_text,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            db.session.commit()
            
            logger.info(f"Prayer request created for {email}: {care_case.id}")
            
            return jsonify({
                'success': True,
                'message': 'Prayer request received',
                'id': care_case.id
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
    """Create a new praise report - logs to Heartbeat care signals"""
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
        
        # Create care case in Heartbeat (praise reports are positive care signals)
        try:
            care_case = CareCase(
                person_id=person.id,
                type='praise_report',
                status='open',
                priority='low',
                summary=report[:500],  # First 500 chars as summary
                details=report,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            db.session.commit()
            
            logger.info(f"Praise report created for {email}: {care_case.id}")
            
            return jsonify({
                'success': True,
                'message': 'Praise report received',
                'id': care_case.id
            }), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating care case: {e}")
            return jsonify({'error': 'Failed to create praise report'}), 500
        
    except Exception as e:
        logger.error(f"Error creating praise report: {e}")
        return jsonify({'error': str(e)}), 500

