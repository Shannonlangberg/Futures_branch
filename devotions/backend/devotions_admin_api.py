"""
Devotions Admin API
Provides endpoints for managing devotional plans and content
"""

from flask import Blueprint, request, jsonify, g
from models import db, DevotionPlan, DevotionContent
from utils.rbac import require_perm, require_feature_flag, get_user_context
from utils.campus_scope import scope_devotions_query, validate_campus_access
from datetime import datetime
import uuid

devotions_admin_bp = Blueprint('devotions_admin', __name__, url_prefix='/api/devotions/admin')

@devotions_admin_bp.route('/plans', methods=['GET'])
@require_feature_flag('DEVOTIONS_ADMIN_ENABLED')
@require_perm('devotions_admin', 'view')
def get_devotion_plans():
    """Get all devotion plans (campus-scoped)"""
    try:
        user_context = get_user_context()
        
        # Build query with campus scoping
        query = DevotionPlan.query
        
        # Apply campus filter if needed
        if user_context.get('campus') and user_context.get('campus') != 'all_campuses':
            query = query.filter(DevotionPlan.campus == user_context['campus'])
        
        plans = query.order_by(DevotionPlan.created_at.desc()).all()
        
        plans_data = []
        for plan in plans:
            plan_data = {
                'id': plan.id,
                'title': plan.title,
                'description': plan.description,
                'campus': plan.campus,
                'status': plan.status,
                'start_date': plan.start_date.isoformat() if plan.start_date else None,
                'end_date': plan.end_date.isoformat() if plan.end_date else None,
                'created_at': plan.created_at.isoformat(),
                'updated_at': plan.updated_at.isoformat(),
                'content_count': len(plan.content) if plan.content else 0
            }
            plans_data.append(plan_data)
        
        return jsonify({
            'plans': plans_data,
            'count': len(plans_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch devotion plans: {str(e)}'}), 500

@devotions_admin_bp.route('/plans', methods=['POST'])
@require_feature_flag('DEVOTIONS_ADMIN_ENABLED')
@require_perm('devotions_admin', 'edit')
def create_devotion_plan():
    """Create a new devotion plan"""
    try:
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
@require_feature_flag('DEVOTIONS_ADMIN_ENABLED')
@require_perm('devotions_admin', 'edit')
def update_devotion_plan(plan_id):
    """Update an existing devotion plan"""
    try:
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
@require_feature_flag('DEVOTIONS_ADMIN_ENABLED')
@require_perm('devotions_admin', 'publish')
def publish_devotion_plan(plan_id):
    """Publish a devotion plan"""
    try:
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
@require_feature_flag('DEVOTIONS_ADMIN_ENABLED')
@require_perm('devotions_admin', 'view')
def get_plan_content(plan_id):
    """Get content for a specific devotion plan"""
    try:
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
