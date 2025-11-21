"""
Engagement API - App opens, Prayer submissions, Event attendance tracking
New heartbeat data sources
"""
from flask import Blueprint, request, jsonify
from models import db, Person, AppSession, PrayerSubmission, EventRegistration
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

engagement_api_bp = Blueprint('engagement_api', __name__, url_prefix='/api/engagement')


@engagement_api_bp.route('/log-app-open', methods=['POST'])
def log_app_open():
    """
    Log app open for engagement tracking (+1 ENGAGEMENT point)
    Public endpoint for mobile app
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find person
        person = Person.query.filter(
            db.func.lower(Person.email) == email.lower(),
            Person.is_active == True
        ).first()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Create session record
        session = AppSession(
            person_id=person.id,
            platform=data.get('platform', 'unknown'),
            app_version=data.get('app_version')
        )
        db.session.add(session)
        
        # Update engagement profile last_seen
        if person.engagement_profile:
            person.engagement_profile.last_seen = datetime.now(timezone.utc).date()
            person.engagement_profile.recalculate_heartbeat()
        
        db.session.commit()
        
        logger.info(f"App open logged for {email} on {session.platform}")
        
        return jsonify({
            'message': 'App open logged successfully',
            'session_id': session.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging app open: {e}", exc_info=True)
        return jsonify({'error': 'Failed to log app open'}), 500


@engagement_api_bp.route('/submit-prayer', methods=['POST'])
def submit_prayer():
    """
    Submit a prayer request or praise (+5 CARE/SPIRITUAL points)
    Public endpoint for mobile/web app
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        submission_type = data.get('type', 'prayer')  # 'prayer' or 'praise'
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if submission_type not in ['prayer', 'praise']:
            return jsonify({'error': 'Type must be "prayer" or "praise"'}), 400
        
        # Find person (optional for anonymous submissions)
        person = None
        if email:
            person = Person.query.filter(
                db.func.lower(Person.email) == email.lower(),
                Person.is_active == True
            ).first()
        
        # Create submission
        submission = PrayerSubmission(
            person_id=person.id if person else None,
            email=email if not data.get('is_anonymous') else None,
            name=data.get('name') if not data.get('is_anonymous') else 'Anonymous',
            submission_type=submission_type,
            category=data.get('category'),
            content=content,
            is_anonymous=data.get('is_anonymous', False),
            is_urgent=data.get('is_urgent', False),
            campus=data.get('campus'),
            source=data.get('source', 'app'),
            prayer_link_id=data.get('prayer_link_id'),
            is_public=data.get('is_public', True)
        )
        db.session.add(submission)
        
        # Update engagement/spiritual score if person identified
        if person and person.engagement_profile:
            # Add to milestones log
            person.engagement_profile.add_serving_record(
                role=f"Prayer Submission - {submission_type.title()}",
                campus=submission.campus or person.campus,
                serving_date=datetime.now(timezone.utc).date()
            )
            person.engagement_profile.recalculate_heartbeat()
        
        db.session.commit()
        
        logger.info(f"{submission_type.title()} submitted by {email or 'Anonymous'}")
        
        return jsonify({
            'message': f'{submission_type.title()} submitted successfully!',
            'submission_id': submission.id,
            'type': submission_type
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting prayer/praise: {e}", exc_info=True)
        return jsonify({'error': 'Failed to submit'}), 500


@engagement_api_bp.route('/mark-event-attended', methods=['POST'])
def mark_event_attended():
    """
    Mark an event as attended (+10 ENGAGEMENT points)
    For staff/leader use or self-check-in
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        event_id = data.get('event_id')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not event_id:
            return jsonify({'error': 'Event ID is required'}), 400
        
        # Find person
        person = Person.query.filter(
            db.func.lower(Person.email) == email.lower(),
            Person.is_active == True
        ).first()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Find registration
        registration = EventRegistration.query.filter_by(
            event_id=event_id,
            person_id=person.id
        ).first()
        
        if not registration:
            # Create registration if doesn't exist
            registration = EventRegistration(
                event_id=event_id,
                person_id=person.id,
                email=person.email,
                name=person.full_name,
                status='attended'
            )
            db.session.add(registration)
        else:
            # Update status
            registration.status = 'attended'
        
        # Update engagement profile
        if person.engagement_profile:
            person.engagement_profile.recalculate_heartbeat()
        
        db.session.commit()
        
        logger.info(f"Event {event_id} marked as attended by {email}")
        
        return jsonify({
            'message': 'Event attendance recorded!',
            'registration_id': registration.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking event attendance: {e}", exc_info=True)
        return jsonify({'error': 'Failed to record attendance'}), 500

