"""
Discipleship Journey Management API

Endpoints for managing journeys and tracking person progress.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, DiscipleshipPathway, PathwayStep, PersonPathwayProgress, 
    PersonPathwayStepCompletion, Person
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

pathway_bp = Blueprint('pathway', __name__, url_prefix='/api/journeys')


# JOURNEY MANAGEMENT

@pathway_bp.route('', methods=['GET'])
@login_required
def get_pathways():
    """Get all journeys"""
    try:
        # Allow any logged-in user to view journeys (they can see their own progress)
        # Only restrict creation/editing, not viewing
        
        category_filter = request.args.get('category')
        is_template = request.args.get('is_template')
        
        query = DiscipleshipPathway.query
        
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        if is_template is not None:
            is_template_bool = is_template.lower() == 'true'
            query = query.filter_by(is_template=is_template_bool)
        
        pathways = query.order_by(DiscipleshipPathway.name).all()
        
        return jsonify({
            'pathways': [p.to_dict() for p in pathways],
            'count': len(pathways)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pathways: {e}", exc_info=True)
        # Check if it's a table doesn't exist error
        error_str = str(e).lower()
        if 'no such table' in error_str or 'does not exist' in error_str:
            return jsonify({
                'error': 'Journeys table not found. Please run migrations first.',
                'details': str(e),
                'pathways': [],
                'count': 0
            }), 500
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('', methods=['POST'])
@login_required
def create_pathway():
    """Create a new pathway (admin only)"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'edit') or 
                current_user.has_permission('heartbeat', 'create') or
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        # Create pathway
        pathway = DiscipleshipPathway(
            name=data['name'],
            description=data.get('description'),
            category=data.get('category', 'general'),
            is_template=data.get('is_template', False),
            created_by_person_id=getattr(current_user, 'id', None)
        )
        
        db.session.add(pathway)
        db.session.flush()  # Get pathway.id
        
        # Add steps if provided
        if 'steps' in data and isinstance(data['steps'], list):
            for step_data in data['steps']:
                step = PathwayStep(
                    pathway_id=pathway.id,
                    step_order=step_data.get('step_order', len(pathway.steps.all()) + 1),
                    step_name=step_data['step_name'],
                    step_description=step_data.get('step_description'),
                    milestone_type=step_data.get('milestone_type'),
                    is_required=step_data.get('is_required', True)
                )
                db.session.add(step)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pathway created successfully',
            'pathway': pathway.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating pathway: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/<int:pathway_id>', methods=['GET'])
@login_required
def get_pathway(pathway_id):
    """Get a single pathway"""
    try:
        if not current_user.has_permission('heartbeat', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        pathway = DiscipleshipPathway.query.get(pathway_id)
        if not pathway:
            return jsonify({'error': 'Pathway not found'}), 404
        
        return jsonify({'pathway': pathway.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Error getting pathway: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/<int:pathway_id>', methods=['PUT'])
@login_required
def update_pathway(pathway_id):
    """Update a pathway"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'edit') or 
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        pathway = DiscipleshipPathway.query.get(pathway_id)
        if not pathway:
            return jsonify({'error': 'Pathway not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            pathway.name = data['name']
        if 'description' in data:
            pathway.description = data['description']
        if 'category' in data:
            pathway.category = data['category']
        if 'is_active' in data:
            pathway.is_active = bool(data['is_active'])
        if 'is_template' in data:
            pathway.is_template = bool(data['is_template'])
        
        # Handle step updates if provided
        if 'steps' in data and isinstance(data['steps'], list):
            # Get existing step IDs
            existing_step_ids = {step.id for step in pathway.steps.all()}
            new_step_ids = {step.get('id') for step in data['steps'] if step.get('id') and not str(step.get('id')).startswith('temp_')}
            
            # Delete steps that are no longer in the list
            steps_to_delete = existing_step_ids - new_step_ids
            for step_id in steps_to_delete:
                step = PathwayStep.query.get(step_id)
                if step and step.pathway_id == pathway_id:
                    # Don't delete if there are completions - just mark as inactive or skip
                    # Actually, let's keep the step but mark it as not required
                    # Or we could soft-delete, but for now let's just not delete steps with completions
                    completion_count = PersonPathwayStepCompletion.query.filter_by(pathway_step_id=step_id).count()
                    if completion_count == 0:
                        db.session.delete(step)
                    else:
                        logger.info(f"Keeping step {step_id} because it has {completion_count} completions")
            
            # Update or create steps
            for idx, step_data in enumerate(data['steps']):
                step_order = idx + 1
                
                # Check if this is an existing step (has ID and not a temp ID)
                if step_data.get('id') and not str(step_data.get('id')).startswith('temp_'):
                    step_id = step_data['id']
                    step = PathwayStep.query.get(step_id)
                    if step and step.pathway_id == pathway_id:
                        # Update existing step
                        step.step_order = step_order
                        step.step_name = step_data.get('step_name', step.step_name)
                        step.step_description = step_data.get('step_description', step.step_description)
                        step.milestone_type = step_data.get('milestone_type', step.milestone_type)
                        step.is_required = step_data.get('is_required', True)
                else:
                    # Create new step
                    new_step = PathwayStep(
                        pathway_id=pathway_id,
                        step_order=step_order,
                        step_name=step_data.get('step_name', ''),
                        step_description=step_data.get('step_description'),
                        milestone_type=step_data.get('milestone_type'),
                        is_required=step_data.get('is_required', True)
                    )
                    db.session.add(new_step)
            
            # Reorder all steps to ensure proper ordering
            db.session.flush()
            all_steps = pathway.steps.order_by(PathwayStep.step_order).all()
            for idx, step in enumerate(all_steps, 1):
                step.step_order = idx
        
        pathway.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pathway updated successfully',
            'pathway': pathway.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating pathway: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/<int:pathway_id>', methods=['DELETE'])
@login_required
def delete_pathway(pathway_id):
    """Delete a pathway"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'delete') or 
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        pathway = DiscipleshipPathway.query.get(pathway_id)
        if not pathway:
            return jsonify({'error': 'Pathway not found'}), 404
        
        db.session.delete(pathway)
        db.session.commit()
        
        return jsonify({'message': 'Pathway deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting pathway: {e}")
        return jsonify({'error': str(e)}), 500


# STEP MANAGEMENT

@pathway_bp.route('/<int:pathway_id>/steps', methods=['POST'])
@login_required
def create_pathway_step(pathway_id):
    """Add a step to a pathway"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'edit') or 
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        pathway = DiscipleshipPathway.query.get(pathway_id)
        if not pathway:
            return jsonify({'error': 'Pathway not found'}), 404
        
        data = request.get_json()
        
        if 'step_name' not in data:
            return jsonify({'error': 'Missing required field: step_name'}), 400
        
        # Get next step order
        max_order = db.session.query(db.func.max(PathwayStep.step_order)).filter_by(pathway_id=pathway_id).scalar() or 0
        
        step = PathwayStep(
            pathway_id=pathway_id,
            step_order=data.get('step_order', max_order + 1),
            step_name=data['step_name'],
            step_description=data.get('step_description'),
            milestone_type=data.get('milestone_type'),
            is_required=data.get('is_required', True)
        )
        
        db.session.add(step)
        db.session.commit()
        
        return jsonify({
            'message': 'Step created successfully',
            'step': step.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating step: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/steps/<int:step_id>', methods=['PUT'])
@login_required
def update_pathway_step(step_id):
    """Update a pathway step"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'edit') or 
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        step = PathwayStep.query.get(step_id)
        if not step:
            return jsonify({'error': 'Step not found'}), 404
        
        data = request.get_json()
        
        if 'step_name' in data:
            step.step_name = data['step_name']
        if 'step_description' in data:
            step.step_description = data['step_description']
        if 'step_order' in data:
            step.step_order = int(data['step_order'])
        if 'milestone_type' in data:
            step.milestone_type = data['milestone_type']
        if 'is_required' in data:
            step.is_required = bool(data['is_required'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Step updated successfully',
            'step': step.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating step: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/steps/<int:step_id>', methods=['DELETE'])
@login_required
def delete_pathway_step(step_id):
    """Delete a pathway step"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'delete') or 
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        step = PathwayStep.query.get(step_id)
        if not step:
            return jsonify({'error': 'Step not found'}), 404
        
        db.session.delete(step)
        db.session.commit()
        
        return jsonify({'message': 'Step deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting step: {e}")
        return jsonify({'error': str(e)}), 500


# PERSON PATHWAY ASSIGNMENT

@pathway_bp.route('/person/<person_id>', methods=['GET'])
@login_required
def get_person_pathways(person_id):
    """Get all pathways for a person"""
    try:
        # Allow person to see their own pathways, or admin to see anyone's
        if person_id != getattr(current_user, 'id', None) and not current_user.has_permission('heartbeat', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.get(person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        progress_records = PersonPathwayProgress.query.filter_by(
            person_id=person_id,
            is_active=True
        ).all()
        
        return jsonify({
            'person_id': person_id,
            'pathways': [p.to_dict() for p in progress_records],
            'count': len(progress_records)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting person pathways: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/person/<person_id>/assign', methods=['POST'])
@login_required
def assign_pathway_to_person(person_id):
    """Assign a pathway to a person"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'edit') or 
                current_user.has_permission('heartbeat', 'create') or
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        person = Person.query.get(person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        data = request.get_json()
        
        if 'pathway_id' not in data:
            return jsonify({'error': 'Missing required field: pathway_id'}), 400
        
        pathway = DiscipleshipPathway.query.get(data['pathway_id'])
        if not pathway:
            return jsonify({'error': 'Pathway not found'}), 404
        
        # Check if this exact pathway is already assigned (prevent duplicates)
        existing_same = PersonPathwayProgress.query.filter_by(
            person_id=person_id,
            pathway_id=data['pathway_id'],
            is_active=True
        ).first()
        
        if existing_same:
            return jsonify({'error': 'This pathway is already assigned to this person'}), 400
        
        # Allow assigning new pathways even if others exist
        # Optionally, if replace_existing is true, mark old pathways as inactive
        if data.get('replace_existing', False):
            existing_all = PersonPathwayProgress.query.filter_by(
                person_id=person_id,
                is_active=True
            ).all()
            for old_progress in existing_all:
                old_progress.is_active = False
                old_progress.updated_at = datetime.utcnow()
            db.session.flush()  # Flush before creating new progress
        
        # Get first step
        first_step = pathway.steps.order_by(PathwayStep.step_order).first()
        
        # Create progress record
        progress = PersonPathwayProgress(
            person_id=person_id,
            pathway_id=data['pathway_id'],
            assigned_by_person_id=getattr(current_user, 'id', None),
            started_at=datetime.utcnow() if data.get('start_immediately', False) else None,
            current_step_id=first_step.id if first_step else None,
            notes=data.get('notes')
        )
        
        db.session.add(progress)
        db.session.commit()
        
        return jsonify({
            'message': 'Pathway assigned successfully',
            'progress': progress.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning pathway: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/progress/<int:progress_id>/complete-step', methods=['POST'])
@login_required
def complete_pathway_step(progress_id):
    """Mark a pathway step as completed"""
    try:
        progress = PersonPathwayProgress.query.get(progress_id)
        if not progress:
            return jsonify({'error': 'Pathway progress not found'}), 404
        
        # Check permissions - person can complete their own, or admin can complete any
        user_role = getattr(current_user, 'role', None)
        is_admin = user_role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']
        if progress.person_id != getattr(current_user, 'id', None) and not (current_user.has_permission('heartbeat', 'edit') or is_admin):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if 'step_id' not in data:
            return jsonify({'error': 'Missing required field: step_id'}), 400
        
        step = PathwayStep.query.get(data['step_id'])
        if not step or step.pathway_id != progress.pathway_id:
            return jsonify({'error': 'Invalid step for this pathway'}), 400
        
        # Check if already completed
        existing = PersonPathwayStepCompletion.query.filter_by(
            person_pathway_progress_id=progress_id,
            pathway_step_id=data['step_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Step already completed'}), 400
        
        # Parse completion date if provided, otherwise use current time
        completed_at = datetime.utcnow()
        if 'completed_at' in data and data['completed_at']:
            try:
                # Accept ISO format date string or datetime string
                if isinstance(data['completed_at'], str):
                    # Try parsing as ISO format
                    if 'T' in data['completed_at']:
                        completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
                    else:
                        # Just a date string (YYYY-MM-DD), use start of day UTC
                        from datetime import date as date_class
                        date_obj = date_class.fromisoformat(data['completed_at'])
                        completed_at = datetime.combine(date_obj, datetime.min.time())
                        # Keep as UTC
                        completed_at = datetime.utcfromtimestamp(completed_at.timestamp())
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid completed_at format: {data['completed_at']}, using current time: {e}")
                completed_at = datetime.utcnow()
        
        # Create completion record
        completion = PersonPathwayStepCompletion(
            person_pathway_progress_id=progress_id,
            pathway_step_id=data['step_id'],
            completed_by_person_id=getattr(current_user, 'id', None),
            completed_at=completed_at,
            notes=data.get('notes')
        )
        
        db.session.add(completion)
        
        # Update current step to next uncompleted step
        next_step = progress.get_next_step()
        progress.current_step_id = next_step.id if next_step else None
        
        # Mark as started if not already
        if not progress.started_at:
            progress.started_at = datetime.utcnow()
        
        # Check if pathway is complete
        if not next_step:
            progress.completed_at = datetime.utcnow()
        
        progress.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Trigger Heartbeat recalculation since spiritual score may have changed
        try:
            from heartbeat_engine import HeartbeatEngine
            engine = HeartbeatEngine()
            engine.calculate_heartbeat(progress.person_id)
            logger.info(f"Recalculated Heartbeat for person {progress.person_id} after pathway step completion")
        except Exception as e:
            logger.warning(f"Failed to recalculate Heartbeat after pathway step completion: {e}")
            # Don't fail the request if recalculation fails
        
        return jsonify({
            'message': 'Step completed successfully',
            'progress': progress.to_dict(),
            'completion': completion.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing step: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/progress/<int:progress_id>/update-completion', methods=['PUT'])
@login_required
def update_pathway_step_completion(progress_id):
    """Update completion date for an existing pathway step completion"""
    try:
        progress = PersonPathwayProgress.query.get(progress_id)
        if not progress:
            return jsonify({'error': 'Pathway progress not found'}), 404
        
        # Check permissions - person can update their own, or admin can update any
        user_role = getattr(current_user, 'role', None)
        is_admin = user_role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']
        if progress.person_id != getattr(current_user, 'id', None) and not (current_user.has_permission('heartbeat', 'edit') or is_admin):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if 'step_id' not in data:
            return jsonify({'error': 'Missing required field: step_id'}), 400
        
        if 'completed_at' not in data:
            return jsonify({'error': 'Missing required field: completed_at'}), 400
        
        step = PathwayStep.query.get(data['step_id'])
        if not step or step.pathway_id != progress.pathway_id:
            return jsonify({'error': 'Invalid step for this pathway'}), 400
        
        # Find existing completion
        completion = PersonPathwayStepCompletion.query.filter_by(
            person_pathway_progress_id=progress_id,
            pathway_step_id=data['step_id']
        ).first()
        
        if not completion:
            return jsonify({'error': 'Step completion not found'}), 404
        
        # Parse completion date
        completed_at = datetime.utcnow()
        if 'completed_at' in data and data['completed_at']:
            try:
                if isinstance(data['completed_at'], str):
                    if 'T' in data['completed_at']:
                        completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
                    else:
                        from datetime import date as date_class
                        date_obj = date_class.fromisoformat(data['completed_at'])
                        completed_at = datetime.combine(date_obj, datetime.min.time())
                        completed_at = datetime.utcfromtimestamp(completed_at.timestamp())
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid completed_at format: {data['completed_at']}, using current time: {e}")
                completed_at = datetime.utcnow()
        
        # Update completion date
        completion.completed_at = completed_at
        progress.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Completion date updated successfully',
            'completion': completion.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating completion date: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/progress/<int:progress_id>', methods=['DELETE'])
@login_required
def unassign_pathway(progress_id):
    """Unassign a pathway from a person"""
    try:
        # Allow heartbeat admins or any admin role
        if not (current_user.has_permission('heartbeat', 'edit') or 
                getattr(current_user, 'role', None) in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        progress = PersonPathwayProgress.query.get(progress_id)
        if not progress:
            return jsonify({'error': 'Pathway progress not found'}), 404
        
        # Soft delete - mark as inactive
        progress.is_active = False
        progress.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Pathway unassigned successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unassigning pathway: {e}")
        return jsonify({'error': str(e)}), 500


@pathway_bp.route('/progress/<int:progress_id>/ai-suggestion', methods=['GET'])
@login_required
def get_pathway_ai_suggestion(progress_id):
    """Get AI-powered suggestion for next steps in pathway"""
    try:
        progress = PersonPathwayProgress.query.get(progress_id)
        if not progress:
            return jsonify({'error': 'Pathway progress not found'}), 404
        
        # Check permissions - person can see their own, or admin can see any
        user_role = getattr(current_user, 'role', None)
        is_admin = user_role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']
        if progress.person_id != getattr(current_user, 'id', None) and not (current_user.has_permission('heartbeat', 'view') or is_admin):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Import Claude if available
        try:
            from app import claude
        except ImportError:
            claude = None
        
        if not claude:
            return jsonify({
                'suggestion': None,
                'message': 'AI assistant not available. Complete the next uncompleted step in your pathway.',
                'next_step': progress.get_next_step().to_dict() if progress.get_next_step() else None
            }), 200
        
        # Get person and pathway data
        person = Person.query.get(progress.person_id)
        completed_steps = progress.step_completions.all()
        all_steps = progress.pathway.steps.order_by(PathwayStep.step_order).all()
        next_step = progress.get_next_step()
        
        # Build context for Claude
        completed_step_names = [c.pathway_step.step_name for c in completed_steps if c.pathway_step]
        remaining_steps = [s for s in all_steps if s.id not in [c.pathway_step_id for c in completed_steps]]
        
        pathway_info = f"""
Pathway: {progress.pathway.name}
Person: {person.full_name if person else 'Unknown'}
Progress: {progress.get_progress_percentage()}% complete ({len(completed_steps)} of {len(all_steps)} steps)

Completed Steps:
{chr(10).join([f"- {name}" for name in completed_step_names]) if completed_step_names else "None yet"}

Remaining Steps:
{chr(10).join([f"- {s.step_order}. {s.step_name}: {s.step_description or 'No description'}" for s in remaining_steps]) if remaining_steps else "All steps completed!"}

Current Next Step (by order): {next_step.step_name if next_step else 'All complete'}
"""
        
        prompt = f"""You are a discipleship coach helping guide someone through their spiritual journey pathway.

{pathway_info}

Based on this person's progress, provide a thoughtful, encouraging suggestion for what they should focus on next. Consider:
1. Their spiritual journey so far
2. Natural progression in discipleship
3. What would be most beneficial at this stage
4. Any steps that might have been completed out of order

Give a brief (2-3 sentences), encouraging, pastoral response suggesting what step they should tackle next and why. Be warm and supportive.

If all steps are complete, celebrate their completion and suggest next steps in their spiritual growth."""
        
        try:
            response = claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            suggestion = response.content[0].text.strip()
            
            return jsonify({
                'suggestion': suggestion,
                'next_step': next_step.to_dict() if next_step else None,
                'progress_percentage': progress.get_progress_percentage(),
                'has_suggestion': True
            }), 200
            
        except Exception as e:
            logger.error(f"Claude API error in pathway suggestion: {e}")
            return jsonify({
                'suggestion': None,
                'message': 'AI suggestion unavailable. Complete the next uncompleted step in your pathway.',
                'next_step': next_step.to_dict() if next_step else None
            }), 200
        
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {e}")
        return jsonify({'error': str(e)}), 500


# MOBILE APP ENDPOINT (Public - person can see their own pathway)
@pathway_bp.route('/my-pathway', methods=['GET'])
def get_my_pathway():
    """Get current user's pathway (for mobile app - uses email)"""
    try:
        person_email = request.args.get('email')
        if not person_email:
            return jsonify({'error': 'Missing email parameter'}), 400
        
        person = Person.query.filter_by(email=person_email, is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        progress_records = PersonPathwayProgress.query.filter_by(
            person_id=person.id,
            is_active=True
        ).all()
        
        # Get the primary/active pathway (first one, or you could add a priority field)
        primary_pathway = progress_records[0] if progress_records else None
        
        if not primary_pathway:
            return jsonify({
                'person_id': person.id,
                'pathway': None,
                'message': 'No pathway assigned'
            }), 200
        
        # Check if person has connect group assigned but "Joined Connect Group" step isn't completed
        # Auto-complete it if needed
        if person.connect_group:
            try:
                from models import PathwayStep, PersonPathwayStepCompletion
                
                # Find the "Joined Connect Group" step
                connect_step = PathwayStep.query.filter_by(
                    pathway_id=primary_pathway.pathway_id,
                    milestone_type='group_join'
                ).first()
                
                if connect_step:
                    # Check if already completed
                    existing_completion = PersonPathwayStepCompletion.query.filter_by(
                        person_pathway_progress_id=primary_pathway.id,
                        pathway_step_id=connect_step.id
                    ).first()
                    
                    if not existing_completion:
                        # Auto-complete the step
                        completion = PersonPathwayStepCompletion(
                            person_pathway_progress_id=primary_pathway.id,
                            pathway_step_id=connect_step.id,
                            completed_by_person_id=person.id,
                            completed_at=datetime.utcnow(),
                            notes=f'Auto-completed: Person already assigned to connect group: {person.connect_group}'
                        )
                        db.session.add(completion)
                        
                        # Update current step to next uncompleted step
                        next_step = primary_pathway.get_next_step()
                        primary_pathway.current_step_id = next_step.id if next_step else None
                        
                        # Mark as started if not already
                        if not primary_pathway.started_at:
                            primary_pathway.started_at = datetime.utcnow()
                        
                        # Check if pathway is complete
                        if not next_step:
                            primary_pathway.completed_at = datetime.utcnow()
                        
                        primary_pathway.updated_at = datetime.utcnow()
                        
                        db.session.commit()
                        logger.info(f"Auto-completed 'Joined Connect Group' step for person {person.id} who already had connect group assigned")
                        
                        # Refresh the pathway data
                        primary_pathway = PersonPathwayProgress.query.get(primary_pathway.id)
            except Exception as pathway_error:
                logger.warning(f"Error auto-completing pathway step for existing connect group: {pathway_error}", exc_info=True)
                db.session.rollback()
                # Continue even if auto-completion fails
        
        return jsonify({
            'person_id': person.id,
            'person_name': person.full_name,
            'pathway': primary_pathway.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting my pathway: {e}")
        return jsonify({'error': str(e)}), 500

