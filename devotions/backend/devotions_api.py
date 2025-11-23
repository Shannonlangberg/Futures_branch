"""
Devotions & Notes API endpoints
This module provides positive-only, forward-looking guidance for church members
"""

from flask import jsonify, request, current_app
from functools import wraps
from datetime import datetime, timedelta
import logging
import uuid
import json

logger = logging.getLogger(__name__)

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

@enforce_positive_response
def get_devotion_library(current_user):
    """Get user's devotion library with assigned, in-progress, completed, and personal plans"""
    try:
        # This would query the database using the get_devotion_library function
        # For now, return sample data
        library_data = {
            'assigned': [
                {
                    'id': '1',
                    'title': 'Daily Devotional',
                    'description': 'Start your day with God',
                    'cover_url': None,
                    'assigned_at': '2024-08-15T00:00:00Z'
                },
                {
                    'id': '2',
                    'title': 'Bible Reading Plan',
                    'description': 'Read through the New Testament',
                    'cover_url': None,
                    'assigned_at': '2024-08-10T00:00:00Z'
                }
            ],
            'in_progress': [
                {
                    'id': '1',
                    'title': 'Daily Devotional',
                    'description': 'Start your day with God',
                    'cover_url': None,
                    'current_day': 1,
                    'completed_days': []
                }
            ],
            'completed': [],
            'personal': [
                {
                    'id': '3',
                    'title': 'Personal Study',
                    'description': 'Your personal devotional plan',
                    'cover_url': None,
                    'created_at': '2024-08-01T00:00:00Z'
                }
            ]
        }
        
        return jsonify(library_data)
    except Exception as e:
        logger.error(f"Error fetching devotion library: {e}")
        return jsonify({'error': 'Failed to fetch library'}), 500

@enforce_positive_response
def get_devotion_plan(plan_id, current_user):
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
                },
                {
                    'day_index': 2,
                    'scripture_ref': 'Psalm 1:4-6 (NIV)',
                    'scripture_text': 'Not so the wicked! They are like chaff that the wind blows away. Therefore the wicked will not stand in the judgment, nor sinners in the assembly of the righteous. For the Lord watches over the way of the righteous, but the way of the wicked leads to destruction.',
                    'devo_body': 'The contrast continues as we see the fate of those who choose not to follow God. The image of chaff being blown away by the wind shows how temporary and unstable a life without God can be. But take heart - the Lord watches over the way of the righteous. This doesn\'t mean life will be easy, but it does mean we have God\'s guidance and protection.',
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

@enforce_positive_response
def assign_devotion_plan(current_user):
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

@enforce_positive_response
def update_devotion_progress(current_user):
    """Update devotion progress for a specific day"""
    try:
        data = request.get_json()
        plan_id = data.get('planId')
        day_index = data.get('dayIndex')
        event = data.get('event')
        
        if not all([plan_id, day_index, event]):
            return jsonify({'error': 'Plan ID, day index, and event are required'}), 400
        
        if event not in ['start', 'complete', 'note_saved', 'media_play']:
            return jsonify({'error': 'Invalid event type'}), 400
        
        # This would update progress in the database using the update_plan_progress function
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

@enforce_positive_response
def create_note(current_user):
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

@enforce_positive_response
def update_note(note_id, current_user):
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

@enforce_positive_response
def get_notes(current_user):
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
                'body': 'This passage really speaks to me about the importance of staying rooted in God\'s Word. I love the tree imagery - it reminds me that spiritual growth takes time and consistent nourishment.',
                'tags': ['reflection', 'psalms', 'growth'],
                'plan_id': '1',
                'plan_title': 'Daily Devotional',
                'day_index': 1,
                'created_at': '2024-08-15T10:30:00Z',
                'is_shared': False,
                'share_token': None
            },
            {
                'id': '2',
                'title': 'John 1 Insights',
                'body': 'The concept of Jesus as the Word is so profound. It connects to Genesis 1 where God spoke creation into being. Jesus is that same creative, life-giving Word.',
                'tags': ['john', 'creation', 'jesus'],
                'plan_id': '2',
                'plan_title': 'Bible Reading Plan',
                'day_index': 1,
                'created_at': '2024-08-14T15:45:00Z',
                'is_shared': True,
                'share_token': 'abc123'
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

@enforce_positive_response
def share_note(note_id, current_user):
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

@enforce_positive_response
def get_shared_note(note_id):
    """Get a shared note by token"""
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({'error': 'Share token is required'}), 400
        
        # This would verify the token and fetch the note
        # For now, return sample data
        note_data = {
            'id': note_id,
            'title': 'Shared Note',
            'body': 'This is a shared note content.',
            'tags': ['shared'],
            'created_at': '2024-08-15T10:30:00Z'
        }
        
        return jsonify(note_data)
        
    except Exception as e:
        logger.error(f"Error fetching shared note: {e}")
        return jsonify({'error': 'Failed to fetch shared note'}), 500

# Telemetry events (privacy-safe)
def log_telemetry_event(event_type, user_id, meta=None):
    """Log telemetry events for analytics (no PII)"""
    try:
        event_data = {
            'event_type': event_type,
            'user_id': user_id,
            'meta': meta or {},
            'occurred_at': datetime.utcnow().isoformat()
        }
        
        # This would insert into the engagement_events table
        logger.info(f"Telemetry event: {event_type} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error logging telemetry: {e}")

# Allowed telemetry events
ALLOWED_TELEMETRY_EVENTS = [
    'devotion_open_plan',
    'devotion_open_day', 
    'devotion_media_play',
    'devotion_complete',
    'note_saved',
    'note_shared'
]

def validate_telemetry_event(event_type, meta):
    """Validate telemetry event data"""
    if event_type not in ALLOWED_TELEMETRY_EVENTS:
        raise ValueError(f"Invalid telemetry event type: {event_type}")
    
    # Ensure no PII in meta
    forbidden_keys = ['email', 'phone', 'address', 'name', 'content']
    for key in forbidden_keys:
        if key in str(meta).lower():
            raise ValueError(f"Forbidden key in telemetry: {key}")
    
    return True
