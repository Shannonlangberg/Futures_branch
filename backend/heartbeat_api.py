# heartbeat_api.py
"""
Heartbeat API Blueprint

REST endpoints for the Heartbeat health tracking module.
"""

from flask import Blueprint, jsonify, request
from models import (
    db, Person, Campus, HeartbeatSnapshot, AttendanceEvent, Service,
    HeartbeatConnectGroup, ConnectAttendance, ServingAssignment,
    GivingSummary, DiscipleshipStep, CareCase, CareTouchpoint
)
from heartbeat_engine import HeartbeatEngine
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

heartbeat_bp = Blueprint('heartbeat', __name__, url_prefix='/api/heartbeat')

engine = HeartbeatEngine()


@heartbeat_bp.route('/campus/<campus_id>/people', methods=['GET'])
def get_campus_people(campus_id):
    """
    Get all people for a campus with their latest HeartbeatSnapshot.
    
    Query params:
        - status: Filter by status ('healthy', 'watch', 'at_risk', 'critical')
    """
    try:
        # Verify campus exists
        campus = Campus.query.get(campus_id)
        if not campus:
            return jsonify({'error': 'Campus not found'}), 404
        
        # Get status filter
        status_filter = request.args.get('status')
        
        # Get people for this campus
        # Map campus_id to campus name
        people = Person.query.filter_by(
            campus=campus.name,
            is_active=True
        ).all()
        
        results = []
        for person in people:
            # Get latest snapshot
            snapshot = HeartbeatSnapshot.query.filter_by(
                person_id=person.id
            ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
            
            # Apply status filter
            if status_filter and snapshot:
                if snapshot.status != status_filter:
                    continue
            elif status_filter and not snapshot:
                continue
            
            person_data = {
                'person_id': person.id,
                'full_name': person.full_name,
                'preferred_name': person.preferred_name,
                'email': person.email,
                'phone': person.phone,
                'campus': person.campus
            }
            
            if snapshot:
                person_data['heartbeat'] = snapshot.to_dict()
            else:
                person_data['heartbeat'] = None
            
            results.append(person_data)
        
        return jsonify({
            'campus_id': campus_id,
            'campus_name': campus.name,
            'people': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting campus people: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/person/<person_id>', methods=['GET'])
def get_person_heartbeat(person_id):
    """
    Get full heartbeat detail for one person, including scores and recent events.
    """
    try:
        person = Person.query.get(person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get latest snapshot
        snapshot = HeartbeatSnapshot.query.filter_by(
            person_id=person_id
        ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
        
        if not snapshot:
            return jsonify({
                'person_id': person_id,
                'person': person.to_dict(),
                'heartbeat': None,
                'message': 'No heartbeat snapshot found. Run recalculation to generate one.'
            }), 200
        
        # Get recent events for context
        twelve_weeks_ago = date.today() - timedelta(weeks=12)
        
        # Recent attendance
        recent_attendance = AttendanceEvent.query.filter(
            AttendanceEvent.person_id == person_id,
            AttendanceEvent.created_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
        ).order_by(AttendanceEvent.created_at.desc()).limit(10).all()
        
        # Recent connect attendance
        recent_connect = ConnectAttendance.query.filter(
            ConnectAttendance.person_id == person_id,
            ConnectAttendance.date >= twelve_weeks_ago
        ).order_by(ConnectAttendance.date.desc()).limit(10).all()
        
        # Recent serving
        recent_serving = ServingAssignment.query.filter(
            ServingAssignment.person_id == person_id
        ).order_by(ServingAssignment.created_at.desc()).limit(10).all()
        
        # Recent discipleship steps
        recent_steps = DiscipleshipStep.query.filter(
            DiscipleshipStep.person_id == person_id
        ).order_by(DiscipleshipStep.date.desc()).limit(10).all()
        
        # Open care cases
        open_cases = CareCase.query.filter(
            CareCase.person_id == person_id,
            CareCase.status.in_(['open', 'in_progress'])
        ).all()
        
        return jsonify({
            'person_id': person_id,
            'person': person.to_dict(),
            'heartbeat': snapshot.to_dict(),
            'recent_activity': {
                'attendance': [a.to_dict() for a in recent_attendance],
                'connect_groups': [c.to_dict() for c in recent_connect],
                'serving': [s.to_dict() for s in recent_serving],
                'discipleship_steps': [d.to_dict() for d in recent_steps],
                'open_care_cases': [c.to_dict() for c in open_cases]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting person heartbeat: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/recalculate/<campus_id>', methods=['POST'])
def recalculate_campus(campus_id):
    """
    Trigger recalculation for all active people in a campus.
    
    Returns:
        Summary of processed people and any errors
    """
    try:
        result = engine.recalculate_campus(campus_id)
        
        return jsonify({
            'message': 'Recalculation completed',
            'campus_id': campus_id,
            'results': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error recalculating campus: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/recalculate/person/<person_id>', methods=['POST'])
def recalculate_person(person_id):
    """
    Trigger recalculation for a specific person.
    
    Query params:
        - start_date: Optional start date (YYYY-MM-DD)
        - end_date: Optional end date (YYYY-MM-DD)
    """
    try:
        # Parse optional date range
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        if request.args.get('end_date'):
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        snapshot = engine.calculate_heartbeat(person_id, start_date, end_date)
        
        return jsonify({
            'message': 'Recalculation completed',
            'person_id': person_id,
            'snapshot': snapshot.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error recalculating person: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/snapshots/<person_id>', methods=['GET'])
def get_person_snapshots(person_id):
    """
    Get all historical snapshots for a person.
    
    Query params:
        - limit: Maximum number of snapshots to return (default: 10)
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        snapshots = HeartbeatSnapshot.query.filter_by(
            person_id=person_id
        ).order_by(HeartbeatSnapshot.calculated_at.desc()).limit(limit).all()
        
        return jsonify({
            'person_id': person_id,
            'snapshots': [s.to_dict() for s in snapshots],
            'count': len(snapshots)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting snapshots: {e}")
        return jsonify({'error': str(e)}), 500

