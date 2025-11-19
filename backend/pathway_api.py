"""
Discipleship Pathway Management API

Endpoints for managing pathways and tracking person progress.
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

pathway_bp = Blueprint('pathway', __name__, url_prefix='/api/pathways')


# PATHWAY MANAGEMENT

@pathway_bp.route('', methods=['GET'])
@login_required
def get_pathways():
    """Get all pathways"""
    try:
        # Allow any logged-in user to view pathways (they can see their own progress)
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
                'error': 'Pathways table not found. Please run migrations first.',
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
        
        # Check if already assigned
        existing = PersonPathwayProgress.query.filter_by(
            person_id=person_id,
            pathway_id=data['pathway_id'],
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'error': 'Pathway already assigned to this person'}), 400
        
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


@pathway_bp.route('/progress/<int:progress_id>/ai-suggestion', methods=['GET'])
@login_required
def get_pathway_ai_suggestion(progress_id):
    """Get AI-powered suggestion for the next pathway step"""
    try:
        progress = PersonPathwayProgress.query.get(progress_id)
        if not progress:
            return jsonify({'error': 'Pathway progress not found'}), 404
        
        # Check permissions - person can see their own, or admin can see any
        user_role = getattr(current_user, 'role', None)
        is_admin = user_role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']
        if progress.person_id != getattr(current_user, 'id', None) and not (current_user.has_permission('heartbeat', 'view') or is_admin):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get next step
        next_step = progress.get_next_step()
        if not next_step:
            return jsonify({
                'suggestion': "Congratulations! You've completed all steps in this pathway. This is a significant milestone in your spiritual journey!"
            }), 200
        
        # Get person info
        person = Person.query.get(progress.person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get completed steps info
        completed_steps = progress.step_completions.all()
        completed_step_names = [completion.pathway_step.step_name for completion in completed_steps if completion.pathway_step]
        
        # Get pathway info
        pathway_name = progress.pathway.name if progress.pathway else "Discipleship Pathway"
        pathway_steps = progress.pathway.steps.order_by(PathwayStep.step_order).all() if progress.pathway else []
        total_steps = len(pathway_steps)
        completed_count = len(completed_steps)
        
        # Try to import claude from app
        try:
            from app import claude
        except ImportError:
            # Fallback: try to initialize Claude here if not available from app
            try:
                from anthropic import Anthropic
                import os
                api_key = os.getenv("ANTHROPIC_API_KEY")
                claude = Anthropic(api_key=api_key) if api_key else None
            except:
                claude = None
        
        if not claude:
            return jsonify({
                'suggestion': f"The next step is '{next_step.step_name}'. {next_step.step_description or 'Continue moving forward in your spiritual journey!'}"
            }), 200
        
        # Build prompt for Claude
        completed_summary = ", ".join(completed_step_names) if completed_step_names else "None yet"
        
        prompt = f"""You're a friendly, encouraging discipleship mentor helping guide someone through their spiritual journey.

Context:
- Person: {person.full_name} ({person.campus} campus)
- Pathway: {pathway_name}
- Progress: {completed_count} of {total_steps} steps completed ({round((completed_count/total_steps)*100)}%)

Completed steps: {completed_summary}

Their next step is: "{next_step.step_name}"
Step description: {next_step.step_description or 'No description provided'}

Give them an encouraging, personalized suggestion about taking this next step. Be:
- Warm and supportive
- Specific to their journey and progress so far
- Practical and actionable
- Focused on the spiritual significance of this step
- Brief (2-3 sentences, under 80 words)

Write as if you're personally encouraging them, using their name if appropriate."""

        try:
            response = claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            suggestion = response.content[0].text.strip() if hasattr(response.content[0], 'text') else str(response.content[0])
            
            return jsonify({
                'suggestion': suggestion
            }), 200
            
        except Exception as e:
            logger.error(f"Claude API error in pathway suggestion: {e}")
            return jsonify({
                'suggestion': f"{person.full_name}, your next step is '{next_step.step_name}'. {next_step.step_description or 'This is an important milestone in your spiritual growth journey!'}"
            }), 200
        
    except Exception as e:
        logger.error(f"Error getting pathway AI suggestion: {e}")
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
        
        return jsonify({
            'person_id': person.id,
            'person_name': person.full_name,
            'pathway': primary_pathway.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting my pathway: {e}")
        return jsonify({'error': str(e)}), 500

