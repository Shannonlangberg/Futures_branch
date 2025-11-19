"""
Events API

Endpoints for managing events, RSVPs, and event registration.
"""
from flask import Blueprint, request, jsonify
from models import db, Event, Person
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__, url_prefix='/api/events')


def get_person_by_email(email):
    """Get person by email"""
    return Person.query.filter_by(email=email, is_active=True).first()


@events_bp.route('', methods=['GET'])
def get_events():
    """Get all events (optionally filtered by campus)"""
    try:
        campus = request.args.get('campus')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Event.query.filter_by(is_active=True)
        
        if campus:
            query = query.filter_by(campus=campus)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
                query = query.filter(Event.start_time >= start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
                query = query.filter(Event.start_time <= end)
            except ValueError:
                pass
        
        # Sort by start time
        events = query.order_by(Event.start_time.asc()).all()
        
        return jsonify({
            'events': [e.to_dict() for e in events],
            'count': len(events)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get a specific event"""
    try:
        event = Event.query.filter_by(id=event_id, is_active=True).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        return jsonify({'event': event.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        return jsonify({'error': str(e)}), 500


@events_bp.route('/rsvp', methods=['POST'])
def rsvp_event():
    """RSVP to an event"""
    try:
        data = request.get_json()
        email = data.get('email')
        event_id = data.get('event_id')
        rsvp = data.get('rsvp')  # 'yes', 'no', 'maybe'
        
        if not email or not event_id or not rsvp:
            return jsonify({'error': 'Email, event_id, and rsvp required'}), 400
        
        if rsvp not in ['yes', 'no', 'maybe']:
            return jsonify({'error': 'RSVP must be yes, no, or maybe'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        event = Event.query.filter_by(id=event_id, is_active=True).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # TODO: In the future, store RSVP in a database table
        # For now, just log it
        logger.info(f"RSVP recorded: {email} - Event {event_id} - {rsvp}")
        
        return jsonify({
            'success': True,
            'message': f'RSVP recorded: {rsvp}',
            'rsvp': rsvp
        }), 200
        
    except Exception as e:
        logger.error(f"Error recording RSVP: {e}")
        return jsonify({'error': str(e)}), 500


