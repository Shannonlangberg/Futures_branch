"""
Connect Groups API

Endpoints for managing connect groups, joining groups, and attendance.
"""
from flask import Blueprint, request, jsonify
from models import db, ConnectGroup, Person, ConnectGroupMeeting, ConnectGroupAttendance, EngagementProfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

connect_groups_bp = Blueprint('connect_groups', __name__, url_prefix='/api/connect-groups')


def get_person_by_email(email):
    """Get person by email"""
    return Person.query.filter_by(email=email, is_active=True).first()


@connect_groups_bp.route('', methods=['GET'])
def get_connect_groups():
    """Get all connect groups (optionally filtered by campus)"""
    try:
        campus = request.args.get('campus')
        is_active = request.args.get('is_active', 'true')
        
        query = ConnectGroup.query
        
        if campus:
            query = query.filter_by(campus=campus)
        
        if is_active.lower() == 'true':
            query = query.filter_by(is_active=True)
        
        groups = query.all()
        
        return jsonify({
            'groups': [g.to_dict() for g in groups],
            'count': len(groups)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connect groups: {e}")
        return jsonify({'error': str(e)}), 500


@connect_groups_bp.route('/my-groups', methods=['GET'])
def get_my_groups():
    """Get groups that a person belongs to"""
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get person's connect group
        if not person.connect_group:
            return jsonify({'groups': [], 'count': 0}), 200
        
        # Find the group
        group = ConnectGroup.query.filter_by(id=person.connect_group, is_active=True).first()
        
        if not group:
            return jsonify({'groups': [], 'count': 0}), 200
        
        return jsonify({
            'groups': [group.to_dict()],
            'count': 1
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting my groups: {e}")
        return jsonify({'error': str(e)}), 500


@connect_groups_bp.route('/join', methods=['POST'])
def join_group():
    """Request to join a connect group"""
    try:
        data = request.get_json()
        email = data.get('email')
        group_id = data.get('group_id')
        
        if not email or not group_id:
            return jsonify({'error': 'Email and group_id required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        group = ConnectGroup.query.filter_by(id=group_id, is_active=True).first()
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        # Update person's connect group
        person.connect_group = group_id
        db.session.commit()
        
        logger.info(f"Person {email} joined group {group_id}")
        
        return jsonify({
            'success': True,
            'message': 'Successfully joined group',
            'group': group.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error joining group: {e}")
        return jsonify({'error': str(e)}), 500


@connect_groups_bp.route('/attendance', methods=['POST'])
def submit_group_attendance():
    """Submit connect group attendance"""
    try:
        data = request.get_json()
        email = data.get('email')
        group_id = data.get('group_id')
        meeting_date = data.get('meeting_date')
        status = data.get('status', 'present')  # 'present', 'absent', 'apology'
        
        if not email or not group_id or not meeting_date:
            return jsonify({'error': 'Email, group_id, and meeting_date required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        group = ConnectGroup.query.filter_by(id=group_id, is_active=True).first()
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        # Parse meeting date
        try:
            if isinstance(meeting_date, str):
                meeting_date_obj = datetime.fromisoformat(meeting_date.split('T')[0]).date()
            else:
                meeting_date_obj = meeting_date
        except Exception:
            return jsonify({'error': 'Invalid meeting_date format'}), 400
        
        # Find or create meeting
        meeting = ConnectGroupMeeting.query.filter_by(
            group_id=group_id,
            meeting_date=meeting_date_obj
        ).first()
        
        if not meeting:
            meeting = ConnectGroupMeeting(
                group_id=group_id,
                meeting_date=meeting_date_obj,
                notes=''
            )
            db.session.add(meeting)
            db.session.flush()
        
        # Check if attendance already exists
        existing = ConnectGroupAttendance.query.filter_by(
            meeting_id=meeting.id,
            person_id=person.id
        ).first()
        
        if existing:
            existing.present = (status == 'present')
        else:
            attendance = ConnectGroupAttendance(
                meeting_id=meeting.id,
                person_id=person.id,
                present=(status == 'present'),
                notes=''
            )
            db.session.add(attendance)
        
        # Update engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        engagement.add_group_attendance(
            group_id=group_id,
            attendance_date=meeting_date_obj,
            present=(status == 'present')
        )
        engagement.recalculate_heartbeat()
        
        db.session.commit()
        
        logger.info(f"Group attendance recorded: {email} - {group_id} - {status}")
        
        return jsonify({
            'success': True,
            'message': 'Attendance recorded',
            'status': status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting group attendance: {e}")
        return jsonify({'error': str(e)}), 500


