# pastoral_care_api.py
"""
Pastoral Care Scheduling API

Endpoints for scheduling catch-ups, appointments, and pastoral care sessions.
Supports role-based access and notifications.
"""

from flask import Blueprint, jsonify, request
from models import db, Person, CareCase, PastoralCareAppointment
from datetime import datetime, date, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)

pastoral_care_bp = Blueprint('pastoral_care', __name__, url_prefix='/api/pastoral-care')


def require_pastor_or_admin(f):
    """Decorator to require pastor/leader/admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has pastor/leader/admin role
        allowed_roles = ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 
                        'campus_pastor', 'pastor', 'staff']
        if current_user.role not in allowed_roles:
            return jsonify({'error': 'Insufficient permissions. Pastor/leader role required.'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def get_user_person_id():
    """Get the Person ID for the current user"""
    from flask_login import current_user
    if not current_user.is_authenticated:
        return None
    
    # Try to find person by email
    person = Person.query.filter_by(email=current_user.email).first()
    if person:
        return person.id
    
    # Try to find by username/full_name
    person = Person.query.filter_by(full_name=current_user.full_name).first()
    if person:
        return person.id
    
    return None


@pastoral_care_bp.route('/appointments', methods=['GET'])
def get_appointments():
    """Get appointments with role-based filtering"""
    try:
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Query parameters
        person_id = request.args.get('person_id')
        pastor_id = request.args.get('pastor_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        upcoming_only = request.args.get('upcoming_only', 'false').lower() == 'true'
        
        # Build query
        query = PastoralCareAppointment.query
        
        # Role-based filtering
        user_person_id = get_user_person_id()
        if current_user.role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'staff']:
            # Pastors/leaders can see all appointments or filter by pastor_id
            if pastor_id:
                query = query.filter_by(pastor_id=pastor_id)
            elif user_person_id:
                # Show appointments where user is the pastor
                query = query.filter(PastoralCareAppointment.pastor_id == user_person_id)
        else:
            # Regular members can only see their own appointments
            if person_id and person_id != user_person_id:
                return jsonify({'error': 'You can only view your own appointments'}), 403
            query = query.filter_by(person_id=user_person_id or person_id)
        
        # Apply filters
        if person_id and current_user.role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'staff']:
            query = query.filter_by(person_id=person_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(PastoralCareAppointment.scheduled_date >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(PastoralCareAppointment.scheduled_date <= end_dt)
            except ValueError:
                pass
        
        if upcoming_only:
            query = query.filter(
                PastoralCareAppointment.scheduled_date >= datetime.utcnow(),
                PastoralCareAppointment.status.in_(['scheduled', 'confirmed'])
            )
        
        # Order by scheduled date
        appointments = query.order_by(PastoralCareAppointment.scheduled_date.asc()).all()
        
        return jsonify({
            'appointments': [a.to_dict() for a in appointments],
            'count': len(appointments)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pastoral_care_bp.route('/appointments', methods=['POST'])
@require_pastor_or_admin
def create_appointment():
    """Create a new pastoral care appointment"""
    try:
        data = request.get_json()
        
        # Required fields
        person_id = data.get('person_id')
        scheduled_date = data.get('scheduled_date')
        title = data.get('title', 'Pastoral Care Catch-Up')
        
        if not person_id or not scheduled_date:
            return jsonify({'error': 'person_id and scheduled_date are required'}), 400
        
        # Parse scheduled date
        try:
            if isinstance(scheduled_date, str):
                scheduled_dt = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
            else:
                scheduled_dt = scheduled_date
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid scheduled_date format: {e}'}), 400
        
        # Verify person exists
        person = Person.query.get(person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get current user's person ID
        user_person_id = get_user_person_id()
        
        # Create appointment
        appointment = PastoralCareAppointment(
            person_id=person_id,
            pastor_id=data.get('pastor_id') or user_person_id,  # Default to current user if pastor
            care_case_id=data.get('care_case_id'),
            title=title,
            description=data.get('description'),
            appointment_type=data.get('appointment_type', 'catch_up'),
            scheduled_date=scheduled_dt,
            duration_minutes=data.get('duration_minutes', 30),
            location=data.get('location', 'office'),
            location_details=data.get('location_details'),
            status='scheduled',
            requested_by_person_id=data.get('requested_by_person_id') or user_person_id,
            created_by_person_id=user_person_id
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # TODO: Send notifications
        # send_appointment_notifications(appointment)
        
        logger.info(f"Created appointment {appointment.id} for person {person_id} with pastor {appointment.pastor_id}")
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating appointment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pastoral_care_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    """Get a specific appointment"""
    try:
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        appointment = PastoralCareAppointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check permissions
        user_person_id = get_user_person_id()
        is_pastor = current_user.role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 
                                          'campus_pastor', 'pastor', 'staff']
        
        if not is_pastor and appointment.person_id != user_person_id:
            return jsonify({'error': 'You can only view your own appointments'}), 403
        
        return jsonify(appointment.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error fetching appointment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pastoral_care_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    """Update an appointment"""
    try:
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        appointment = PastoralCareAppointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check permissions
        user_person_id = get_user_person_id()
        is_pastor = current_user.role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 
                                          'campus_pastor', 'pastor', 'staff']
        
        if not is_pastor and appointment.person_id != user_person_id:
            return jsonify({'error': 'You can only update your own appointments'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            appointment.title = data['title']
        if 'description' in data:
            appointment.description = data['description']
        if 'scheduled_date' in data:
            try:
                scheduled_dt = datetime.fromisoformat(data['scheduled_date'].replace('Z', '+00:00'))
                appointment.scheduled_date = scheduled_dt
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid scheduled_date format'}), 400
        if 'duration_minutes' in data:
            appointment.duration_minutes = data['duration_minutes']
        if 'location' in data:
            appointment.location = data['location']
        if 'location_details' in data:
            appointment.location_details = data['location_details']
        if 'status' in data:
            appointment.status = data['status']
            if data['status'] == 'completed':
                appointment.completed_at = datetime.utcnow()
            elif data['status'] == 'cancelled':
                appointment.cancelled_at = datetime.utcnow()
        if 'notes' in data and is_pastor:
            appointment.notes = data['notes']
        if 'follow_up_notes' in data and is_pastor:
            appointment.follow_up_notes = data['follow_up_notes']
        if 'pastor_id' in data and is_pastor:
            appointment.pastor_id = data['pastor_id']
        
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Updated appointment {appointment_id}")
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating appointment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pastoral_care_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@require_pastor_or_admin
def delete_appointment(appointment_id):
    """Cancel/delete an appointment"""
    try:
        appointment = PastoralCareAppointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Soft delete by marking as cancelled
        appointment.status = 'cancelled'
        appointment.cancelled_at = datetime.utcnow()
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Cancelled appointment {appointment_id}")
        
        return jsonify({
            'success': True,
            'message': 'Appointment cancelled'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling appointment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pastoral_care_bp.route('/appointments/<int:appointment_id>/confirm', methods=['POST'])
def confirm_appointment(appointment_id):
    """Confirm an appointment (can be called by person or pastor)"""
    try:
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        appointment = PastoralCareAppointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check permissions
        user_person_id = get_user_person_id()
        is_pastor = current_user.role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 
                                          'campus_pastor', 'pastor', 'staff']
        
        if not is_pastor and appointment.person_id != user_person_id:
            return jsonify({'error': 'You can only confirm your own appointments'}), 403
        
        appointment.status = 'confirmed'
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # TODO: Send confirmation notifications
        # send_confirmation_notification(appointment)
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming appointment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pastoral_care_bp.route('/available-pastors', methods=['GET'])
def get_available_pastors():
    """Get list of available pastors/leaders for scheduling"""
    try:
        from flask_login import current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get all users with pastor/leader roles
        # This would need to query the users table or Person table with role info
        # For now, return a placeholder
        # TODO: Implement proper query based on your user/role system
        
        return jsonify({
            'pastors': [],
            'message': 'Pastor list functionality to be implemented'
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching pastors: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

