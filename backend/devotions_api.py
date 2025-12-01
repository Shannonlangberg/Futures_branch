"""
Devotions & Notes API endpoints
This module provides positive-only, forward-looking guidance for church members
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import logging
import uuid
import json

logger = logging.getLogger(__name__)

# Create blueprint
devotions_bp = Blueprint('devotions', __name__, url_prefix='/api/devotions')

def enforce_positive_response(f):
    """Decorator to ensure all Devotions responses are positive-only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            response = f(*args, **kwargs)
            
            # Check for forbidden keys/words in response
            response_str = str(response)
            forbidden_keys = ['score', 'attendance', 'streak', 'missed', 'pulse', 'beacon', 'raw']
            forbidden_words = ['missed', 'absent', 'overdue', 'failed', 'declined']
            
            # Check for forbidden keys
            for key in forbidden_keys:
                if f'"{key}"' in response_str.lower():
                    logger.error(f"Forbidden key '{key}' detected in Devotions response")
                    return jsonify({'error': 'Invalid response content'}), 500
            
            # Check for forbidden words
            for word in forbidden_words:
                if word in response_str.lower():
                    logger.error(f"Forbidden word '{word}' detected in Devotions response")
                    return jsonify({'error': 'Invalid response content'}), 500
            
            return response
        except Exception as e:
            logger.error(f"Error in Devotions API: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function

@devotions_bp.route('/library', methods=['GET'])
@login_required
@enforce_positive_response
def get_devotion_library():
    """Get user's devotion library with assigned, in-progress, completed, and personal plans"""
    try:
        # Try to import devotions models
        try:
            from devotions_models import DevotionPlan
            from models import db
        except ImportError:
            DevotionPlan = None
        
        # Get user's campus
        user_campus = getattr(current_user, 'campus', None) or 'all_campuses'
        
        # Query published plans that are visible to this user's campus
        if DevotionPlan:
            try:
                # Get plans where:
                # 1. Status is 'published'
                # 2. Campus is None (all campuses) OR matches user's campus
                query = DevotionPlan.query.filter(
                    DevotionPlan.status == 'published'
                )
                
                # Filter by campus: show if campus is None/empty (all) or matches user's campus
                if user_campus and user_campus != 'all_campuses':
                    # Show plans for all campuses (None or empty) OR user's specific campus
                    from sqlalchemy import or_
                    query = query.filter(
                        or_(
                            DevotionPlan.campus.is_(None),
                            DevotionPlan.campus == '',
                            DevotionPlan.campus == user_campus
                        )
                    )
                # If user has all_campuses access, show all published plans (no filter)
                
                plans = query.order_by(DevotionPlan.created_at.desc()).all()
                
                # Format plans for library
                assigned = []
                for plan in plans:
                    assigned.append({
                        'id': plan.id,
                        'title': plan.title,
                        'description': plan.description or '',
                        'cover_url': plan.cover_url,
                        'campus': plan.campus or 'All Campuses',
                        'total_days': plan.total_days or 30,
                        'content_count': plan.content.count() if hasattr(plan, 'content') else 0
                    })
                
                library_data = {
                    'assigned': assigned,
                    'in_progress': [],  # TODO: Get from plan_assignments table
                    'completed': [],   # TODO: Get from plan_assignments with completed status
                    'personal': []     # TODO: Get personal plans
                }
                
                return jsonify(library_data)
            except Exception as db_error:
                logger.warning(f"Error querying devotions: {db_error}")
                # Fall through to sample data
        
        # Fallback to sample data if models not available
        library_data = {
            'assigned': [
                {
                    'id': '1',
                    'title': 'Daily Devotional',
                    'description': 'Start your day with God',
                    'cover_url': None,
                    'assigned_at': '2024-08-15T00:00:00Z'
                }
            ],
            'in_progress': [],
            'completed': [],
            'personal': []
        }
        
        return jsonify(library_data)
    except Exception as e:
        logger.error(f"Error fetching devotion library: {e}")
        return jsonify({'error': 'Failed to fetch library'}), 500

@devotions_bp.route('/plan/<plan_id>', methods=['GET'])
@login_required
@enforce_positive_response
def get_devotion_plan(plan_id):
    """Get plan details and days for a specific devotion plan"""
    try:
        # This would query the database for plan and days
        # For now, return sample data
        plan_data = {
            'plan': {
                'id': plan_id,
                'title': 'Daily Devotional',
                'description': 'Start your day with God',
                'cover_url': None,
                'source': 'canvas',
                'audience': {'campus': ['all_campuses']}
            },
            'days': [
                {
                    'day_index': 1,
                    'scripture_ref': 'Psalm 1:1-3 (NIV)',
                    'scripture_text': 'Blessed is the one who does not walk in step with the wicked or stand in the way that sinners take or sit in the company of mockers, but whose delight is in the law of the Lord, and who meditates on his law day and night. That person is like a tree planted by streams of water, which yields its fruit in season and whose leaf does not wither—whatever they do prospers.',
                    'devo_body': 'Today we begin our journey through the Psalms. This opening passage sets the foundation for what it means to be blessed by God. Notice how the psalmist contrasts two ways of living: following the world or following God\'s Word. The imagery of a tree planted by streams of water is powerful - when we root ourselves in God\'s truth, we find stability and fruitfulness.',
                    'media': []
                }
            ],
            'assignment': {
                'id': 'assignment_1',
                'assigned_at': '2024-08-15T00:00:00Z',
                'start_on': None,
                'notify_time': None,
                'progress': {'currentDay': 1, 'completedDays': []}
            },
            'progress': {'currentDay': 1, 'completedDays': []}
        }
        
        return jsonify(plan_data)
    except Exception as e:
        logger.error(f"Error fetching devotion plan: {e}")
        return jsonify({'error': 'Failed to fetch plan'}), 500

@devotions_bp.route('/assign', methods=['POST'])
@login_required
@enforce_positive_response
def assign_devotion_plan():
    """Assign a devotion plan to the current user"""
    try:
        data = request.get_json()
        plan_id = data.get('planId')
        start_on = data.get('startOn')
        notify_time = data.get('notifyTime')
        
        if not plan_id:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        # This would create/update the plan assignment in the database
        # For now, return success
        assignment_data = {
            'id': str(uuid.uuid4()),
            'plan_id': plan_id,
            'user_id': current_user.id,
            'assigned_at': datetime.utcnow().isoformat(),
            'start_on': start_on,
            'notify_time': notify_time,
            'progress': {'currentDay': 1, 'completedDays': []}
        }
        
        logger.info(f"Plan {plan_id} assigned to user {current_user.id}")
        return jsonify(assignment_data), 201
        
    except Exception as e:
        logger.error(f"Error assigning devotion plan: {e}")
        return jsonify({'error': 'Failed to assign plan'}), 500

@devotions_bp.route('/progress', methods=['POST'])
@login_required
@enforce_positive_response
def update_devotion_progress():
    """Update devotion progress for a specific day - tracks to heartbeat"""
    try:
        data = request.get_json()
        plan_id = data.get('planId')
        day_index = data.get('dayIndex')
        event = data.get('event')
        
        if not all([plan_id, day_index, event]):
            return jsonify({'error': 'Plan ID, day index, and event are required'}), 400
        
        if event not in ['start', 'complete', 'note_saved', 'media_play']:
            return jsonify({'error': 'Invalid event type'}), 400
        
        # Update heartbeat tracking when devotion is completed
        if event == 'complete':
            try:
                from models import Person, EngagementProfile, db
                
                person = Person.query.get(current_user.id)
                if person and person.engagement_profile:
                    # Track bible reading for heartbeat
                    person.engagement_profile.add_bible_reading(reading_date=datetime.utcnow().date())
                    db.session.commit()
                    logger.info(f"Tracked bible reading for person {current_user.id} via devotions")
            except Exception as e:
                logger.error(f"Error tracking devotion to heartbeat: {e}")
                # Don't fail the progress update if heartbeat tracking fails
        
        # This would update progress in the database
        # For now, return success
        progress_data = {
            'plan_id': plan_id,
            'day_index': day_index,
            'event': event,
            'occurred_at': datetime.utcnow().isoformat(),
            'meta': {}
        }
        
        logger.info(f"Progress updated: {event} for plan {plan_id}, day {day_index}")
        return jsonify(progress_data), 200
        
    except Exception as e:
        logger.error(f"Error updating devotion progress: {e}")
        return jsonify({'error': 'Failed to update progress'}), 500

@devotions_bp.route('/notes', methods=['POST'])
@login_required
@enforce_positive_response
def create_note():
    """Create a new note"""
    try:
        data = request.get_json()
        title = data.get('title')
        body = data.get('body')
        tags = data.get('tags', [])
        plan_id = data.get('planId')
        day_index = data.get('dayIndex')
        
        if not title or not body:
            return jsonify({'error': 'Title and body are required'}), 400
        
        # This would create the note in the database
        # For now, return success
        note_data = {
            'id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'plan_id': plan_id,
            'day_index': day_index,
            'title': title,
            'body': body,
            'tags': tags,
            'is_shared': False,
            'share_token': None,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Note created for user {current_user.id}")
        return jsonify(note_data), 201
        
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return jsonify({'error': 'Failed to create note'}), 500

@devotions_bp.route('/notes/<note_id>', methods=['PUT'])
@login_required
@enforce_positive_response
def update_note(note_id):
    """Update an existing note"""
    try:
        data = request.get_json()
        title = data.get('title')
        body = data.get('body')
        tags = data.get('tags', [])
        
        if not title or not body:
            return jsonify({'error': 'Title and body are required'}), 400
        
        # This would update the note in the database
        # For now, return success
        note_data = {
            'id': note_id,
            'title': title,
            'body': body,
            'tags': tags,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Note {note_id} updated for user {current_user.id}")
        return jsonify(note_data), 200
        
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        return jsonify({'error': 'Failed to update note'}), 500

@devotions_bp.route('/notes', methods=['GET'])
@login_required
@enforce_positive_response
def get_notes():
    """Get user's notes with optional filtering"""
    try:
        plan_id = request.args.get('planId')
        tag = request.args.get('tag')
        q = request.args.get('q')
        
        # This would query the database for notes
        # For now, return sample data
        notes_data = [
            {
                'id': '1',
                'title': 'Reflection on Psalm 1',
                'body': 'This passage really speaks to me about the importance of staying rooted in God\'s Word.',
                'tags': ['reflection', 'psalms', 'growth'],
                'plan_id': '1',
                'plan_title': 'Daily Devotional',
                'day_index': 1,
                'created_at': '2024-08-15T10:30:00Z',
                'is_shared': False,
                'share_token': None
            }
        ]
        
        # Apply filters
        if plan_id:
            notes_data = [n for n in notes_data if n['plan_id'] == plan_id]
        if tag:
            notes_data = [n for n in notes_data if tag in n['tags']]
        if q:
            notes_data = [n for n in notes_data if q.lower() in n['title'].lower() or q.lower() in n['body'].lower()]
        
        return jsonify(notes_data)
        
    except Exception as e:
        logger.error(f"Error fetching notes: {e}")
        return jsonify({'error': 'Failed to fetch notes'}), 500

@devotions_bp.route('/notes/<note_id>/share', methods=['POST'])
@login_required
@enforce_positive_response
def share_note(note_id):
    """Toggle note sharing and generate share token"""
    try:
        # This would update the note's sharing status in the database
        # For now, return success
        share_data = {
            'note_id': note_id,
            'is_shared': True,
            'share_token': str(uuid.uuid4()),
            'share_url': f"/notes/{note_id}?token={str(uuid.uuid4())}"
        }
        
        logger.info(f"Note {note_id} shared by user {current_user.id}")
        return jsonify(share_data), 200
        
    except Exception as e:
        logger.error(f"Error sharing note: {e}")
        return jsonify({'error': 'Failed to share note'}), 500
