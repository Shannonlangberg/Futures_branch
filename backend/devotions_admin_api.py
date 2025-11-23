"""
Devotions Admin API
Provides endpoints for managing devotional plans and content
"""

from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from models import db
from datetime import datetime
import uuid
import logging

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
        return True

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
                    'created_at': plan.created_at.isoformat() if plan.created_at else None,
                    'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
                    'content_count': plan.content.count() if hasattr(plan, 'content') else 0
                }
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
        
        # Check campus access
        campus = data.get('campus', user_context.get('campus'))
        if not validate_campus_access('devotions_admin', campus, user_context['role'], user_context['campus']):
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
                'status': plan.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
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
        if 'start_date' in data:
            plan.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None
        if 'end_date' in data:
            plan.end_date = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
        
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
        plan.published_at = datetime.utcnow()
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Devotion plan published successfully',
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'status': plan.status,
                'published_at': plan.published_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
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
            for item in plan.content:
                content_data.append({
                    'id': item.id,
                    'day': item.day,
                    'title': item.title,
                    'content': item.content,
                    'scripture_reference': item.scripture_reference,
                    'prayer_focus': item.prayer_focus,
                    'created_at': item.created_at.isoformat()
                })
        
        return jsonify({
            'plan': {
                'id': plan.id,
                'title': plan.title,
                'campus': plan.campus
            },
            'content': content_data,
            'count': len(content_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch plan content: {str(e)}'}), 500
