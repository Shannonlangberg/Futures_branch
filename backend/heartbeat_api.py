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
    
    Special case: If campus_id is 'all_campuses', returns all people from all campuses.
    """
    try:
        # Get status filter
        status_filter = request.args.get('status')
        
        # Handle "all_campuses" special case
        if campus_id == 'all_campuses' or campus_id == 'all':
            # Get all active people from all campuses
            people = Person.query.filter_by(is_active=True).all()
            campus_name = 'All Campuses'
            campus_id_display = 'all_campuses'
        else:
            # Try to find campus by ID first
            campus = Campus.query.get(campus_id)
            
            # If not found by ID, try to find by name (for flexibility)
            if not campus:
                campus = Campus.query.filter_by(name=campus_id).first()
            
            # If still not found, create it from the campus name
            if not campus:
                # Normalize campus_id to create new campus
                campus_id_normalized = campus_id.lower().replace(' ', '_')
                campus = Campus(
                    id=campus_id_normalized,
                    name=campus_id,  # Use original as display name
                    timezone='Australia/Adelaide',
                    is_active=True
                )
                db.session.add(campus)
                db.session.commit()
                logger.info(f"Created Heartbeat campus: {campus_id_normalized} ({campus_id})")
            
            campus_name = campus.name
            campus_id_display = campus_id
            
            # Get people for this campus
            # Try multiple matching strategies
            # 1. Exact match with campus.name
            people = Person.query.filter_by(
                campus=campus.name,
                is_active=True
            ).all()
            
            # 2. If no results, try normalized name variations
            if not people:
                # Try common variations
                variations = [
                    campus.name,
                    campus.id.replace('_', ' ').title(),  # copper_coast -> Copper Coast
                    campus.id.replace('_', ' '),  # copper_coast -> copper coast
                    campus.name.lower(),
                    campus.name.upper()
                ]
                for variation in variations:
                    people = Person.query.filter_by(
                        campus=variation,
                        is_active=True
                    ).all()
                    if people:
                        logger.info(f"Found {len(people)} people using campus variation: {variation}")
                        break
        
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
            'campus_id': campus_id_display,
            'campus_name': campus_name,
            'people': results,
            'count': len(results),
            'message': f'Found {len(results)} people for {campus_name}' if results else f'No people found for {campus_name}. Run recalculation after adding data.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting campus people: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        return jsonify({
            'error': str(e),
            'details': 'Check server logs for more information'
        }), 500


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
        
        # Get pathway progress
        from models import PersonPathwayProgress
        pathway_progress = PersonPathwayProgress.query.filter_by(
            person_id=person_id,
            is_active=True
        ).first()
        
        return jsonify({
            'person_id': person_id,
            'person': person.to_dict(),
            'heartbeat': snapshot.to_dict(),
            'pathway': pathway_progress.to_dict() if pathway_progress else None,
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
    
    Special case: If campus_id is 'all_campuses', recalculates for all people.
    
    Returns:
        Summary of processed people and any errors
    """
    try:
        # Handle "all_campuses" special case
        if campus_id == 'all_campuses' or campus_id == 'all':
            # Get all active people from all campuses
            all_people = Person.query.filter_by(is_active=True).all()
            processed = 0
            errors = 0
            
            for person in all_people:
                try:
                    engine.calculate_heartbeat(person.id)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error calculating heartbeat for person {person.id}: {e}")
                    errors += 1
            
            result = {
                'processed': processed,
                'errors': errors,
                'total': len(all_people)
            }
            campus_name = 'All Campuses'
        else:
            result = engine.recalculate_campus(campus_id)
            # Get campus name for response
            campus = Campus.query.get(campus_id)
            campus_name = campus.name if campus else campus_id
        
        return jsonify({
            'message': 'Recalculation completed',
            'campus_id': campus_id,
            'campus_name': campus_name,
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

