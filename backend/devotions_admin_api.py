"""
Devotions Admin API
Provides endpoints for managing devotional plans and content
"""

from flask import Blueprint, request, jsonify, g, send_from_directory
from flask_login import login_required, current_user
from models import db
from datetime import datetime
import uuid
import logging
import os
import json

logger = logging.getLogger(__name__)

# Try to import devotions models, fallback to None if they don't exist
try:
    from devotions_models import DevotionPlan, DevotionContent
except ImportError:
    DevotionPlan = None
    DevotionContent = None
    logger.warning("DevotionPlan and DevotionContent models not found - devotions admin will use mock data")

# Try to import RBAC utilities, provide fallbacks if they don't exist
try:
    from utils.rbac import require_perm, require_feature_flag, get_user_context
except ImportError:
    logger.warning("RBAC utilities not found - using fallback decorators")
    def require_perm(perm, action):
        def decorator(f):
            return f
        return decorator
    def require_feature_flag(flag):
        def decorator(f):
            return f
        return decorator
    def get_user_context():
        return {
            'user_id': current_user.id if current_user.is_authenticated else None,
            'role': getattr(current_user, 'role', 'user') if current_user.is_authenticated else 'user',
            'campus': getattr(current_user, 'campus', 'all_campuses') if current_user.is_authenticated else 'all_campuses'
        }

try:
    from utils.campus_scope import scope_devotions_query, validate_campus_access
except ImportError:
    logger.warning("Campus scope utilities not found - using fallback functions")
    def scope_devotions_query(query, user_role=None, user_campus=None):
        return query
    def validate_campus_access(perm, campus, user_role, user_campus):
        # More permissive validation - allow if user is admin/leadership or campuses match
        admin_roles = ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']
        if user_role in admin_roles:
            return True
        if not campus or campus.lower() in ['', 'all', 'all_campuses', 'all campuses']:
            return True
        if user_campus == 'all_campuses':
            return True
        # Allow if campuses match (case insensitive)
        return str(campus).lower() == str(user_campus).lower()

devotions_admin_bp = Blueprint('devotions_admin', __name__, url_prefix='/api/devotions/admin')

@devotions_admin_bp.route('/plans', methods=['GET'])
@login_required
def get_devotion_plans():
    """Get all devotion plans (campus-scoped)"""
    try:
        # If models don't exist, return empty list
        if DevotionPlan is None:
            logger.warning("DevotionPlan model not available - returning empty plans list")
            return jsonify({
                'plans': [],
                'count': 0
            })
        
        # Try to get user context, but don't fail if it doesn't work
        try:
            user_context = get_user_context()
        except Exception as e:
            logger.warning(f"Could not get user context: {e}")
            user_context = {
                'campus': 'all_campuses',
                'role': 'user'
            }
        
        # Try to query the database, but catch table doesn't exist errors
        try:
            # Build query with campus scoping
            query = DevotionPlan.query
            
            # Apply campus filter if needed
            if user_context.get('campus') and user_context.get('campus') != 'all_campuses':
                query = query.filter(DevotionPlan.campus == user_context['campus'])
            
            plans = query.order_by(DevotionPlan.created_at.desc()).all()
            
            # Helper function to check if cover image file exists
            def check_cover_image_exists(cover_url):
                """Check if cover image file actually exists on disk"""
                if not cover_url:
                    return None
                
                # Extract filename from URL
                if cover_url.startswith('/api/devotions/admin/media/'):
                    filename = cover_url.replace('/api/devotions/admin/media/', '')
                elif '/' in cover_url:
                    filename = os.path.basename(cover_url)
                else:
                    filename = cover_url
                
                # Check all possible locations
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                instance_dir = os.path.join(backend_dir, 'instance')
                data_dir = os.path.join(instance_dir, 'uploads', 'devotions')
                
                # Check Railway volume path
                if os.path.exists('/data'):
                    upload_dir = os.path.join('/data', 'uploads', 'devotions')
                    file_path = os.path.join(upload_dir, filename)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        return cover_url
                
                # Check instance directory
                file_path = os.path.join(data_dir, filename)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    return cover_url
                
                # Check old location
                old_dir = os.path.join(backend_dir, 'uploads', 'devotions')
                file_path = os.path.join(old_dir, filename)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    return cover_url
                
                # File doesn't exist - return None
                logger.debug(f"Cover image not found: {filename}")
                return None
            
            plans_data = []
            for plan in plans:
                plan_data = plan.to_dict() if hasattr(plan, 'to_dict') else {
                    'id': plan.id,
                    'title': plan.title,
                    'description': plan.description,
                    'campus': plan.campus,
                    'status': plan.status,
                    'start_date': plan.start_date.isoformat() if plan.start_date else None,
                    'end_date': plan.end_date.isoformat() if plan.end_date else None,
                    'total_days': getattr(plan, 'total_days', 30),
                    'created_at': plan.created_at.isoformat() if plan.created_at else None,
                    'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
                    'content_count': plan.content.count() if hasattr(plan, 'content') else 0
                }
                
                # Verify cover_url file exists, set to None if it doesn't
                if 'cover_url' in plan_data and plan_data['cover_url']:
                    verified_url = check_cover_image_exists(plan_data['cover_url'])
                    plan_data['cover_url'] = verified_url
                
                plans_data.append(plan_data)
            
            return jsonify({
                'plans': plans_data,
                'count': len(plans_data)
            })
        
        except Exception as db_error:
            # Check if it's a table doesn't exist error
            error_str = str(db_error).lower()
            if 'no such table' in error_str or 'does not exist' in error_str or 'operationalerror' in error_str:
                logger.warning(f"Devotion plans table does not exist yet: {db_error}")
                return jsonify({
                    'plans': [],
                    'count': 0,
                    'message': 'Database tables not initialized yet'
                })
            # Re-raise if it's a different error
            raise
        
    except Exception as e:
        logger.error(f"Error fetching devotion plans: {e}", exc_info=True)
        # Return empty list instead of error to allow frontend to load
        return jsonify({
            'plans': [],
            'count': 0,
            'error': f'Failed to fetch devotion plans: {str(e)}'
        }), 200  # Return 200 with empty list instead of 500

@devotions_admin_bp.route('/plans', methods=['POST'])
@login_required
def create_devotion_plan():
    """Create a new devotion plan"""
    try:
        # If models don't exist, return error
        if DevotionPlan is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        data = request.get_json()
        user_context = get_user_context()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Check campus access - allow if user has admin/leadership role or campus matches
        campus = data.get('campus', user_context.get('campus')) or ''
        
        # Allow creation if:
        # 1. User is admin/senior leadership
        # 2. Campus is empty/None (all campuses)
        # 3. Campus matches user's campus
        # 4. Campus access validation passes
        user_role = user_context.get('role', 'user')
        user_campus = user_context.get('campus', 'all_campuses')
        
        if campus.lower() in ['', 'all', 'all_campuses', 'all campuses']:
            campus = None  # Set to None for all campuses
        
        # Allow admin and senior leadership to create plans for any campus
        admin_roles = ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor']
        if user_role in admin_roles:
            pass  # Allow
        elif campus and user_campus != 'all_campuses' and campus.lower() != user_campus.lower():
            # Only block if trying to create for a different campus and not admin
            if not validate_campus_access('devotions_admin', campus, user_role, user_campus):
                return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Create new plan
        plan = DevotionPlan(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data.get('description', ''),
            campus=campus,
            status=data.get('status', 'draft'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            total_days=data.get('total_days', 30),  # Support custom plan length
            cover_url=data.get('cover_url', ''),
            created_by=user_context['user_id'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'message': 'Devotion plan created successfully',
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'campus': plan.campus,
                'status': plan.status,
                'total_days': plan.total_days
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating devotion plan: {e}", exc_info=True)
        return jsonify({'error': f'Failed to create devotion plan: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>', methods=['PUT'])
@login_required
def update_devotion_plan(plan_id):
    """Update an existing devotion plan"""
    try:
        # If models don't exist, return error
        if DevotionPlan is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        data = request.get_json()
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Update fields
        if 'title' in data:
            plan.title = data['title']
        if 'description' in data:
            plan.description = data['description']
        if 'status' in data:
            plan.status = data['status']
        if 'total_days' in data:
            plan.total_days = data['total_days']
        if 'campus' in data:
            # Handle campus update - empty string means all campuses
            campus = data['campus'] or ''
            if campus.lower() in ['', 'all', 'all_campuses', 'all campuses']:
                plan.campus = None
            else:
                plan.campus = campus
        if 'start_date' in data:
            plan.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None
        if 'end_date' in data:
            plan.end_date = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
        if 'cover_url' in data:
            plan.cover_url = data['cover_url']
        
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Devotion plan updated successfully',
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'campus': plan.campus,
                'status': plan.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating devotion plan: {e}", exc_info=True)
        return jsonify({'error': f'Failed to update devotion plan: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>/publish', methods=['POST'])
@login_required
def publish_devotion_plan(plan_id):
    """Publish a devotion plan"""
    try:
        # If models don't exist, return error
        if DevotionPlan is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Publish the plan
        plan.status = 'published'
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Devotion plan published successfully',
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'status': plan.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error publishing devotion plan: {e}", exc_info=True)
        return jsonify({'error': f'Failed to publish devotion plan: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>/content', methods=['GET'])
@login_required
def get_plan_content(plan_id):
    """Get content for a specific devotion plan"""
    try:
        # If models don't exist, return error
        if DevotionPlan is None or DevotionContent is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Get content
        content_data = []
        if plan.content:
            for item in plan.content.order_by(DevotionContent.day_index):
                content_data.append(item.to_dict() if hasattr(item, 'to_dict') else {
                    'id': item.id,
                    'day_index': item.day_index,
                    'title': item.title,
                    'scripture_ref': item.scripture_ref,
                    'scripture_text': item.scripture_text,
                    'devo_body': item.devo_body,
                    'prayer_focus': item.prayer_focus,
                    'media': json.loads(item.media) if item.media else [],
                    'cover_image': item.cover_image,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None
                })
        
        return jsonify({
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'campus': plan.campus,
                'total_days': getattr(plan, 'total_days', 30)
            },
            'content': content_data,
            'count': len(content_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching plan content: {e}", exc_info=True)
        return jsonify({'error': f'Failed to fetch plan content: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>/content', methods=['POST'])
@login_required
def create_plan_content(plan_id):
    """Create or update day content for a devotion plan"""
    try:
        if DevotionPlan is None or DevotionContent is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        data = request.get_json()
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        day_index = data.get('day_index')
        if not day_index:
            return jsonify({'error': 'day_index is required'}), 400
        
        # Check if content already exists for this day
        existing = DevotionContent.query.filter_by(plan_id=plan_id, day_index=day_index).first()
        
        if existing:
            # Update existing content
            if 'title' in data:
                existing.title = data['title']
            if 'scripture_ref' in data:
                existing.scripture_ref = data['scripture_ref']
            if 'scripture_text' in data:
                existing.scripture_text = data['scripture_text']
            if 'devo_body' in data:
                existing.devo_body = data['devo_body']
            if 'prayer_focus' in data:
                existing.prayer_focus = data['prayer_focus']
            if 'media' in data:
                existing.media = json.dumps(data['media']) if isinstance(data['media'], list) else data['media']
            if 'cover_image' in data:
                existing.cover_image = data['cover_image']
            
            existing.updated_at = datetime.utcnow()
        else:
            # Create new content
            content = DevotionContent(
                id=str(uuid.uuid4()),
                plan_id=plan_id,
                day_index=day_index,
                title=data.get('title'),
                scripture_ref=data.get('scripture_ref'),
                scripture_text=data.get('scripture_text'),
                devo_body=data.get('devo_body'),
                prayer_focus=data.get('prayer_focus'),
                media=json.dumps(data.get('media', [])) if data.get('media') else None,
                cover_image=data.get('cover_image'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(content)
        
        db.session.commit()
        
        content_obj = existing if existing else DevotionContent.query.filter_by(plan_id=plan_id, day_index=day_index).first()
        
        return jsonify({
            'message': 'Content saved successfully',
            'content': content_obj.to_dict() if hasattr(content_obj, 'to_dict') else {
                'id': content_obj.id,
                'day_index': content_obj.day_index,
                'title': content_obj.title
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving plan content: {e}", exc_info=True)
        return jsonify({'error': f'Failed to save content: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>/content/<day_index>', methods=['DELETE'])
@login_required
def delete_plan_content(plan_id, day_index):
    """Delete day content from a devotion plan"""
    try:
        if DevotionContent is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Find and delete content
        content = DevotionContent.query.filter_by(plan_id=plan_id, day_index=int(day_index)).first()
        if content:
            db.session.delete(content)
            db.session.commit()
            return jsonify({'message': 'Content deleted successfully'})
        else:
            return jsonify({'error': 'Content not found'}), 404
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting plan content: {e}", exc_info=True)
        return jsonify({'error': f'Failed to delete content: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>', methods=['DELETE'])
@login_required
def delete_devotion_plan(plan_id):
    """Delete a devotion plan"""
    try:
        if DevotionPlan is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Delete the plan (cascade will delete content)
        db.session.delete(plan)
        db.session.commit()
        
        return jsonify({
            'message': 'Devotion plan deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting devotion plan: {e}", exc_info=True)
        return jsonify({'error': f'Failed to delete devotion plan: {str(e)}'}), 500

@devotions_admin_bp.route('/plans/<plan_id>/archive', methods=['POST'])
@login_required
def archive_devotion_plan(plan_id):
    """Archive a devotion plan"""
    try:
        if DevotionPlan is None:
            return jsonify({'error': 'Devotions module not fully configured. Database models missing.'}), 503
        
        user_context = get_user_context()
        
        # Get the plan
        plan = DevotionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Devotion plan not found'}), 404
        
        # Check campus access
        if not validate_campus_access('devotions_admin', plan.campus, user_context['role'], user_context['campus']):
            return jsonify({'error': 'Insufficient campus access'}), 403
        
        # Archive the plan
        plan.status = 'archived'
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Devotion plan archived successfully',
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'status': plan.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error archiving devotion plan: {e}", exc_info=True)
        return jsonify({'error': f'Failed to archive devotion plan: {str(e)}'}), 500

# Media upload endpoints
@devotions_admin_bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """Upload image or video for devotion plans"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        # Create uploads/devotions directory - use persistent volume if available
        # Check for Railway volume mount or use instance directory for persistence
        instance_dir = os.path.join(os.path.dirname(__file__), '..', 'instance')
        data_dir = os.path.join(instance_dir, 'uploads', 'devotions')
        
        # Try Railway volume path first (/data is typically mounted)
        if os.path.exists('/data'):
            upload_dir = os.path.join('/data', 'uploads', 'devotions')
        else:
            # Fall back to instance directory (persists with database)
            upload_dir = data_dir
        
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(filepath)
        
        # Verify file was saved
        if not os.path.exists(filepath):
            logger.error(f"File upload failed - file not found at: {filepath}")
            return jsonify({'error': 'Failed to save file'}), 500
        
        logger.info(f"File uploaded successfully to: {filepath}")
        
        # Determine file type
        file_type = 'image' if file_ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'} else 'video'
        
        # Return URL path
        media_url = f"/api/devotions/admin/media/{filename}"
        
        return jsonify({
            'success': True,
            'url': media_url,
            'filename': filename,
            'type': file_type
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading media: {e}", exc_info=True)
        return jsonify({'error': f'Failed to upload media: {str(e)}'}), 500

@devotions_admin_bp.route('/media/<filename>')
def serve_media(filename):
    """Serve uploaded devotion media files (public endpoint)"""
    try:
        # Sanitize filename to prevent directory traversal
        filename = os.path.basename(filename)
        
        # Check both possible locations
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        instance_dir = os.path.join(backend_dir, 'instance')
        data_dir = os.path.join(instance_dir, 'uploads', 'devotions')
        
        # Try Railway volume path first
        if os.path.exists('/data'):
            upload_dir = os.path.join('/data', 'uploads', 'devotions')
            file_path = os.path.join(upload_dir, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                logger.info(f"Serving media from volume: {file_path}")
                return send_from_directory(upload_dir, filename)
        
        # Fall back to instance directory
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            logger.info(f"Serving media from instance: {file_path}")
            return send_from_directory(data_dir, filename)
        
        # Try old location for backwards compatibility
        old_dir = os.path.join(backend_dir, 'uploads', 'devotions')
        file_path = os.path.join(old_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            logger.info(f"Serving media from old location: {file_path}")
            return send_from_directory(old_dir, filename)
        
        upload_dir_check = os.path.join('/data', 'uploads', 'devotions') if os.path.exists('/data') else 'N/A'
        logger.warning(f"Media file not found: {filename}. Checked: {upload_dir_check}, {data_dir}, {old_dir}")
        return jsonify({'error': 'Media file not found'}), 404
    except Exception as e:
        logger.error(f"Error serving media: {e}", exc_info=True)
        return jsonify({'error': 'Failed to serve media'}), 500
