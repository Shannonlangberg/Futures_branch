# serving_api.py - API endpoints for Serving Module

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional
import logging
import uuid

from models import db, Person, EngagementProfile
from serving_models import (
    ServingTeam, ServingRole, TeamMember, ServingSchedule, 
    ServingRequest, ServingRecord, PersonAvailability
)

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
serving_bp = Blueprint('serving', __name__, url_prefix='/api/serving')

# Helper functions
def has_serving_permission(permission_type: str, team_id: str = None) -> bool:
    """Check if current user has serving permissions"""
    if not current_user.is_authenticated:
        return False
    
    # Admin users have all permissions - check role instead of has_permission method
    if hasattr(current_user, 'role') and current_user.role in ['admin', 'senior_leadership', 'senior_leader']:
        return True
    
    # Check team-specific permissions
    if team_id:
        membership = TeamMember.query.filter_by(
            person_id=current_user.id,
            team_id=team_id,
            is_active=True
        ).first()
        
        if membership:
            if permission_type == 'read':
                return True
            elif permission_type == 'write' and (membership.is_leader or membership.can_schedule):
                return True
            elif permission_type == 'approve' and membership.can_approve_requests:
                return True
    
    return False


def get_user_teams(person_id: str) -> List[Dict[str, Any]]:
    """Get all teams a person belongs to"""
    memberships = TeamMember.query.filter_by(
        person_id=person_id,
        is_active=True
    ).all()
    
    teams = []
    for membership in memberships:
        team_data = membership.team.to_dict()
        team_data['membership'] = membership.to_dict()
        teams.append(team_data)
    
    return teams


# Team Management Endpoints

@serving_bp.route('/teams', methods=['GET'])
@login_required
def get_teams():
    """Get serving teams (filtered by campus and permissions)"""
    try:
        campus = request.args.get('campus')
        team_type = request.args.get('team_type')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        
        query = ServingTeam.query
        
        if campus:
            query = query.filter_by(campus=campus)
        if team_type:
            query = query.filter_by(team_type=team_type)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        teams = query.all()
        
        # Filter by permissions
        accessible_teams = []
        for team in teams:
            if has_serving_permission('read', team.id):
                team_data = team.to_dict()
                accessible_teams.append(team_data)
        
        return jsonify({
            'teams': accessible_teams,
            'count': len(accessible_teams)
        })
        
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        return jsonify({'error': 'Failed to fetch teams'}), 500


@serving_bp.route('/teams', methods=['POST'])
@login_required
def create_team():
    """Create a new serving team (admin/leader only)"""
    try:
        if not has_serving_permission('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'campus']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create team
        team = ServingTeam(
            name=data['name'],
            campus=data['campus'],
            description=data.get('description'),
            department=data.get('department'),
            team_type=data.get('team_type', 'ministry'),
            requires_background_check=data.get('requires_background_check', False),
            min_age=data.get('min_age'),
            max_age=data.get('max_age'),
            leader_id=data.get('leader_id'),
            co_leader_id=data.get('co_leader_id')
        )
        
        db.session.add(team)
        db.session.commit()
        
        return jsonify({
            'message': 'Team created successfully',
            'team': team.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating team: {e}")
        return jsonify({'error': 'Failed to create team'}), 500


@serving_bp.route('/teams/<team_id>', methods=['GET'])
@login_required
def get_team(team_id):
    """Get detailed information about a specific team"""
    try:
        team = ServingTeam.query.get_or_404(team_id)
        
        if not has_serving_permission('read', team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        team_data = team.to_dict()
        
        # Add members
        members = []
        for member in team.members.filter_by(is_active=True).all():
            member_data = member.to_dict()
            members.append(member_data)
        
        team_data['members'] = members
        
        # Add roles
        roles = []
        for role in team.roles.filter_by(is_active=True).all():
            role_data = role.to_dict()
            roles.append(role_data)
        
        team_data['roles'] = roles
        
        return jsonify(team_data)
        
    except Exception as e:
        logger.error(f"Error fetching team: {e}")
        return jsonify({'error': 'Failed to fetch team'}), 500


@serving_bp.route('/teams/<team_id>', methods=['PUT'])
@login_required
def update_team(team_id):
    """Update team information (admin/leader only)"""
    try:
        if not has_serving_permission('write', team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        team = ServingTeam.query.get_or_404(team_id)
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'description', 'department', 'team_type', 'is_active']:
            if field in data:
                setattr(team, field, data[field])
        
        # Update special fields
        if 'requires_background_check' in data:
            team.requires_background_check = data['requires_background_check']
        if 'min_age' in data:
            team.min_age = data['min_age']
        if 'max_age' in data:
            team.max_age = data['max_age']
        if 'leader_id' in data:
            team.leader_id = data['leader_id']
        if 'co_leader_id' in data:
            team.co_leader_id = data['co_leader_id']
        
        team.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Team updated successfully',
            'team': team.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating team: {e}")
        return jsonify({'error': 'Failed to update team'}), 500


# Role Management Endpoints

@serving_bp.route('/teams/<team_id>/roles', methods=['GET'])
@login_required
def get_team_roles(team_id):
    """Get all roles for a specific team"""
    try:
        if not has_serving_permission('read', team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        roles = ServingRole.query.filter_by(team_id=team_id, is_active=True).all()
        roles_data = [role.to_dict() for role in roles]
        
        return jsonify({
            'roles': roles_data,
            'count': len(roles_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching team roles: {e}")
        return jsonify({'error': 'Failed to fetch team roles'}), 500


@serving_bp.route('/teams/<team_id>/roles', methods=['POST'])
@login_required
def create_role(team_id):
    """Create a new role for a team (admin/leader only)"""
    try:
        if not has_serving_permission('write', team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Missing required field: name'}), 400
        
        # Create role
        role = ServingRole(
            name=data['name'],
            team_id=team_id,
            description=data.get('description'),
            requires_training=data.get('requires_training', False),
            training_hours=data.get('training_hours'),
            requires_background_check=data.get('requires_background_check', False),
            min_serving_age=data.get('min_serving_age'),
            typical_duration_hours=data.get('typical_duration_hours'),
            typical_frequency=data.get('typical_frequency')
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'message': 'Role created successfully',
            'role': role.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        return jsonify({'error': 'Failed to create role'}), 500


# Team Membership Endpoints

@serving_bp.route('/teams/<team_id>/members', methods=['GET'])
@login_required
def get_team_members(team_id):
    """Get all members of a specific team"""
    try:
        if not has_serving_permission('read', team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        members = TeamMember.query.filter_by(team_id=team_id, is_active=True).all()
        members_data = [member.to_dict() for member in members]
        
        return jsonify({
            'members': members_data,
            'count': len(members_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching team members: {e}")
        return jsonify({'error': 'Failed to fetch team members'}), 500


@serving_bp.route('/teams/<team_id>/members', methods=['POST'])
@login_required
def add_team_member(team_id):
    """Add a person to a team (admin/leader only)"""
    try:
        if not has_serving_permission('write', team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('person_id'):
            return jsonify({'error': 'Missing required field: person_id'}), 400
        
        # Check if person already exists in team
        existing_member = TeamMember.query.filter_by(
            person_id=data['person_id'],
            team_id=team_id,
            is_active=True
        ).first()
        
        if existing_member:
            return jsonify({'error': 'Person is already a member of this team'}), 400
        
        # Add member
        member = TeamMember(
            person_id=data['person_id'],
            team_id=team_id,
            primary_role_id=data.get('primary_role_id'),
            secondary_roles=data.get('secondary_roles', []),
            is_leader=data.get('is_leader', False),
            can_schedule=data.get('can_schedule', False),
            can_approve_requests=data.get('can_approve_requests', False)
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'message': 'Member added successfully',
            'member': member.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding team member: {e}")
        return jsonify({'error': 'Failed to add team member'}), 500


# Schedule Management Endpoints

@serving_bp.route('/schedule', methods=['GET'])
@login_required
def get_schedule():
    """Get serving schedule (filtered by user permissions)"""
    try:
        team_id = request.args.get('team_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        query = ServingSchedule.query
        
        if team_id:
            if not has_serving_permission('read', team_id):
                return jsonify({'error': 'Insufficient permissions'}), 403
            query = query.filter_by(team_id=team_id)
        else:
            # Get user's teams
            user_teams = get_user_teams(current_user.id)
            team_ids = [team['id'] for team in user_teams]
            if not team_ids:
                return jsonify({'schedules': [], 'count': 0})
            query = query.filter(ServingSchedule.team_id.in_(team_ids))
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(ServingSchedule.scheduled_date >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(ServingSchedule.scheduled_date <= end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        if status:
            query = query.filter_by(status=status)
        
        schedules = query.order_by(ServingSchedule.scheduled_date, ServingSchedule.start_time).all()
        schedules_data = [schedule.to_dict() for schedule in schedules]
        
        return jsonify({
            'schedules': schedules_data,
            'count': len(schedules_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        return jsonify({'error': 'Failed to fetch schedule'}), 500


@serving_bp.route('/schedule', methods=['POST'])
@login_required
def create_schedule():
    """Create a new serving schedule (admin/leader only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['role_id', 'team_id', 'scheduled_date', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check permissions
        if not has_serving_permission('write', data['team_id']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Parse dates and times
        try:
            scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Invalid date/time format: {e}'}), 400
        
        # Create schedule
        schedule = ServingSchedule(
            role_id=data['role_id'],
            team_id=data['team_id'],
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            assigned_person_id=data.get('assigned_person_id'),
            backup_person_id=data.get('backup_person_id'),
            notes=data.get('notes'),
            timezone=data.get('timezone', 'Australia/Adelaide')
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule created successfully',
            'schedule': schedule.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        return jsonify({'error': 'Failed to create schedule'}), 500


@serving_bp.route('/schedule/<schedule_id>', methods=['PUT'])
@login_required
def update_schedule(schedule_id):
    """Update a serving schedule (admin/leader only)"""
    try:
        schedule = ServingSchedule.query.get_or_404(schedule_id)
        
        if not has_serving_permission('write', schedule.team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'assigned_person_id' in data:
            schedule.assigned_person_id = data['assigned_person_id']
        if 'backup_person_id' in data:
            schedule.backup_person_id = data['backup_person_id']
        if 'status' in data:
            schedule.status = data['status']
        if 'notes' in data:
            schedule.notes = data['notes']
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule updated successfully',
            'schedule': schedule.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        return jsonify({'error': 'Failed to update schedule'}), 500


# Serving Requests Endpoints

@serving_bp.route('/requests', methods=['GET'])
@login_required
def get_requests():
    """Get serving requests (filtered by user permissions)"""
    try:
        team_id = request.args.get('team_id')
        request_type = request.args.get('request_type')
        status = request.args.get('status')
        
        query = ServingRequest.query
        
        if team_id:
            if not has_serving_permission('read', team_id):
                return jsonify({'error': 'Insufficient permissions'}), 403
            query = query.filter_by(team_id=team_id)
        else:
            # Get user's teams
            user_teams = get_user_teams(current_user.id)
            team_ids = [team['id'] for team in user_teams]
            if not team_ids:
                return jsonify({'requests': [], 'count': 0})
            query = query.filter(ServingRequest.team_id.in_(team_ids))
        
        if request_type:
            query = query.filter_by(request_type=request_type)
        if status:
            query = query.filter_by(status=status)
        
        requests = query.order_by(ServingRequest.created_at.desc()).all()
        requests_data = [req.to_dict() for req in requests]
        
        return jsonify({
            'requests': requests_data,
            'count': len(requests_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching requests: {e}")
        return jsonify({'error': 'Failed to fetch requests'}), 500


@serving_bp.route('/requests', methods=['POST'])
@login_required
def create_request():
    """Create a new serving request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['request_type', 'team_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create request
        request_obj = ServingRequest(
            person_id=current_user.id,
            team_id=data['team_id'],
            request_type=data['request_type'],
            schedule_id=data.get('schedule_id'),
            requested_date=data.get('requested_date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            reason=data.get('reason'),
            notes=data.get('notes')
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        return jsonify({
            'message': 'Request created successfully',
            'request': request_obj.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating request: {e}")
        return jsonify({'error': 'Failed to create request'}), 500


@serving_bp.route('/requests/<request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    """Approve or deny a serving request (admin/leader only)"""
    try:
        request_obj = ServingRequest.query.get_or_404(request_id)
        
        if not has_serving_permission('approve', request_obj.team_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        action = data.get('action')  # 'approve' or 'deny'
        notes = data.get('notes')
        
        if action not in ['approve', 'deny']:
            return jsonify({'error': 'Invalid action. Use "approve" or "deny"'}), 400
        
        # Update request status
        request_obj.status = 'approved' if action == 'approve' else 'denied'
        request_obj.approved_by = current_user.id
        request_obj.approved_at = datetime.utcnow()
        request_obj.approval_notes = notes
        
        # If approved and it's a sign-up request, assign to schedule
        if action == 'approve' and request_obj.request_type == 'sign_up' and request_obj.schedule_id:
            schedule = ServingSchedule.query.get(request_obj.schedule_id)
            if schedule:
                schedule.assigned_person_id = request_obj.person_id
                schedule.status = 'assigned'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Request {action}d successfully',
            'request': request_obj.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error approving request: {e}")
        return jsonify({'error': 'Failed to approve request'}), 500


# Serving Records Endpoints

@serving_bp.route('/records', methods=['GET'])
@login_required
def get_serving_records():
    """Get serving records (filtered by user permissions)"""
    try:
        person_id = request.args.get('person_id')
        team_id = request.args.get('team_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = ServingRecord.query
        
        if person_id:
            # Check if user can view this person's records
            if person_id != current_user.id and not has_serving_permission('admin'):
                return jsonify({'error': 'Insufficient permissions'}), 403
            query = query.filter_by(person_id=person_id)
        elif not has_serving_permission('admin'):
            # Regular users can only see their own records
            query = query.filter_by(person_id=current_user.id)
        
        if team_id:
            if not has_serving_permission('read', team_id):
                return jsonify({'error': 'Insufficient permissions'}), 403
            query = query.filter_by(team_id=team_id)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(ServingRecord.served_date >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(ServingRecord.served_date <= end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        records = query.order_by(ServingRecord.served_date.desc()).all()
        records_data = [record.to_dict() for record in records]
        
        return jsonify({
            'records': records_data,
            'count': len(records_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching serving records: {e}")
        return jsonify({'error': 'Failed to fetch serving records'}), 500


@serving_bp.route('/records', methods=['POST'])
@login_required
def log_serving():
    """Log actual serving activity"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['team_id', 'role_id', 'served_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check permissions
        if not has_serving_permission('write', data['team_id']):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Parse date
        try:
            served_date = datetime.strptime(data['served_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid served_date format. Use YYYY-MM-DD'}), 400
        
        # Parse times if provided
        start_time = None
        end_time = None
        if data.get('start_time'):
            try:
                start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Invalid start_time format. Use HH:MM'}), 400
        
        if data.get('end_time'):
            try:
                end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Invalid end_time format. Use HH:MM'}), 400
        
        # Calculate duration if both times provided
        actual_duration_hours = None
        if start_time and end_time:
            start_dt = datetime.combine(served_date, start_time)
            end_dt = datetime.combine(served_date, end_time)
            if end_dt > start_dt:
                duration = end_dt - start_dt
                actual_duration_hours = duration.total_seconds() / 3600
        
        # Create record
        record = ServingRecord(
            person_id=data.get('person_id', current_user.id),
            team_id=data['team_id'],
            role_id=data['role_id'],
            served_date=served_date,
            start_time=start_time,
            end_time=end_time,
            actual_duration_hours=actual_duration_hours,
            status=data.get('status', 'completed'),
            notes=data.get('notes')
        )
        
        db.session.add(record)
        db.session.commit()
        
        # Update engagement profile for heartbeat tracking
        person = Person.query.get(record.person_id)
        if person and person.engagement_profile:
            try:
                # Get role and team names for logging
                role_name = record.role.name if record.role else 'Unknown'
                team_name = record.team.name if record.team else 'Unknown'
                campus_name = record.team.campus if record.team else person.campus or 'Unknown'
                
                # Update engagement profile with serving record
                person.engagement_profile.add_serving_record(
                    role=role_name,
                    campus=campus_name,
                    serving_date=served_date,
                    location=team_name
                )
                db.session.commit()
                logger.info(f"Updated engagement profile for person {person.id} with serving record")
            except Exception as e:
                logger.error(f"Error updating engagement profile for serving record: {e}")
                db.session.rollback()
        
        return jsonify({
            'message': 'Serving activity logged successfully',
            'record': record.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error logging serving: {e}")
        return jsonify({'error': 'Failed to log serving activity'}), 500


# Availability Management Endpoints

@serving_bp.route('/availability', methods=['GET'])
@login_required
def get_availability():
    """Get person's availability preferences"""
    try:
        person_id = request.args.get('person_id', current_user.id)
        
        # Check permissions
        if person_id != current_user.id and not has_serving_permission('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        availability = PersonAvailability.query.filter_by(
            person_id=person_id,
            is_active=True
        ).all()
        
        availability_data = [avail.to_dict() for avail in availability]
        
        return jsonify({
            'availability': availability_data,
            'count': len(availability_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching availability: {e}")
        return jsonify({'error': 'Failed to fetch availability'}), 500


@serving_bp.route('/availability', methods=['POST'])
@login_required
def set_availability():
    """Set person's availability preferences"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('start_date'):
            return jsonify({'error': 'Missing required field: start_date'}), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = None
            if data.get('end_date'):
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create or update availability
        availability = PersonAvailability.query.filter_by(
            person_id=current_user.id,
            is_active=True
        ).first()
        
        if availability:
            # Update existing
            availability.start_date = start_date
            availability.end_date = end_date
            availability.preferred_days = data.get('preferred_days', [])
            availability.preferred_times = data.get('preferred_times', [])
            availability.preferred_teams = data.get('preferred_teams', [])
            availability.unavailable_dates = data.get('unavailable_dates', [])
            availability.max_hours_per_week = data.get('max_hours_per_week')
            availability.max_servings_per_month = data.get('max_servings_per_month')
            availability.notes = data.get('notes')
            availability.updated_at = datetime.utcnow()
        else:
            # Create new
            availability = PersonAvailability(
                person_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
                preferred_days=data.get('preferred_days', []),
                preferred_times=data.get('preferred_times', []),
                preferred_teams=data.get('preferred_teams', []),
                unavailable_dates=data.get('unavailable_dates', []),
                max_hours_per_week=data.get('max_hours_per_week'),
                max_servings_per_month=data.get('max_servings_per_month'),
                notes=data.get('notes')
            )
            db.session.add(availability)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Availability updated successfully',
            'availability': availability.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error setting availability: {e}")
        return jsonify({'error': 'Failed to set availability'}), 500


# Dashboard Endpoints

@serving_bp.route('/dashboard', methods=['GET'])
@login_required
def get_serving_dashboard():
    """Get personalized serving dashboard for current user"""
    try:
        user_id = current_user.id
        
        # Get user's teams
        teams = []
        try:
            teams = get_user_teams(user_id)
        except Exception as e:
            logger.warning(f"Error getting user teams for {user_id}: {e}")
        
        # Get upcoming schedules
        schedules_data = []
        try:
            upcoming_schedules = ServingSchedule.query.filter(
                ServingSchedule.assigned_person_id == user_id,
                ServingSchedule.scheduled_date >= datetime.now().date(),
                ServingSchedule.status.in_(['assigned', 'confirmed'])
            ).order_by(ServingSchedule.scheduled_date, ServingSchedule.start_time).limit(10).all()
            schedules_data = [schedule.to_dict() for schedule in upcoming_schedules]
        except Exception as e:
            logger.warning(f"Error getting serving schedules for {user_id}: {e}")
        
        # Get recent serving records
        records_data = []
        try:
            recent_records = ServingRecord.query.filter_by(
                person_id=user_id
            ).order_by(ServingRecord.served_date.desc()).limit(5).all()
            records_data = [record.to_dict() for record in recent_records]
        except Exception as e:
            logger.warning(f"Error getting serving records for {user_id}: {e}")
        
        # Get pending requests
        requests_data = []
        try:
            pending_requests = ServingRequest.query.filter_by(
                person_id=user_id,
                status='pending'
            ).order_by(ServingRequest.created_at.desc()).all()
            requests_data = [req.to_dict() for req in pending_requests]
        except Exception as e:
            logger.warning(f"Error getting serving requests for {user_id}: {e}")
        
        # Calculate serving stats
        total_servings = 0
        monthly_servings = 0
        try:
            total_servings = ServingRecord.query.filter_by(
                person_id=user_id,
                status='completed'
            ).count()
            
            this_month = datetime.now().replace(day=1).date()
            monthly_servings = ServingRecord.query.filter(
                ServingRecord.person_id == user_id,
                ServingRecord.status == 'completed',
                ServingRecord.served_date >= this_month
            ).count()
        except Exception as e:
            logger.warning(f"Error calculating serving stats for {user_id}: {e}")
        
        return jsonify({
            'teams': teams,
            'upcoming_schedules': schedules_data,
            'recent_records': records_data,
            'pending_requests': requests_data,
            'stats': {
                'total_serving': total_servings,
                'monthly_servings': monthly_servings,
                'active_teams': len(teams)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching serving dashboard: {e}")
        return jsonify({'error': 'Failed to fetch serving dashboard'}), 500


# Admin/Leader Dashboard Endpoints

@serving_bp.route('/admin/dashboard', methods=['GET'])
@login_required
def get_admin_dashboard():
    """Get admin/leader serving dashboard"""
    try:
        if not has_serving_permission('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get all teams user has access to
        user_teams = get_user_teams(current_user.id)
        team_ids = [team['id'] for team in user_teams]
        
        if not team_ids:
            return jsonify({'error': 'No teams accessible'}), 403
        
        # Get upcoming schedules with gaps
        upcoming_schedules = ServingSchedule.query.filter(
            ServingSchedule.team_id.in_(team_ids),
            ServingSchedule.scheduled_date >= datetime.now().date(),
            ServingSchedule.status.in_(['open', 'assigned'])
        ).order_by(ServingSchedule.scheduled_date, ServingSchedule.start_time).all()
        
        schedules_data = [schedule.to_dict() for schedule in upcoming_schedules]
        
        # Count gaps
        open_schedules = [s for s in schedules_data if s['status'] == 'open']
        
        # Get pending requests
        pending_requests = ServingRequest.query.filter(
            ServingRequest.team_id.in_(team_ids),
            ServingRequest.status == 'pending'
        ).order_by(ServingRequest.created_at.desc()).all()
        
        requests_data = [req.to_dict() for req in pending_requests]
        
        # Get team member counts
        team_stats = []
        for team in user_teams:
            member_count = TeamMember.query.filter_by(
                team_id=team['id'],
                is_active=True
            ).count()
            
            active_roles = ServingRole.query.filter_by(
                team_id=team['id'],
                is_active=True
            ).count()
            
            team_stats.append({
                'team_id': team['id'],
                'team_name': team['name'],
                'member_count': member_count,
                'active_roles': active_roles
            })
        
        return jsonify({
            'team_stats': team_stats,
            'upcoming_schedules': schedules_data,
            'pending_requests': requests_data,
            'gaps': {
                'open_schedules': len(open_schedules),
                'total_upcoming': len(schedules_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching admin dashboard: {e}")
        return jsonify({'error': 'Failed to fetch admin dashboard'}), 500


# Service Planning Endpoints

@serving_bp.route('/templates', methods=['GET'])
@login_required
def get_service_templates():
    """Get all service templates"""
    try:
        if not has_serving_permission('read'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # For now, return mock data - replace with database integration
        mock_templates = [
            {
                'id': '1',
                'name': 'Standard Sunday Service',
                'description': 'Regular Sunday morning service template',
                'campus': 'Paradise',
                'service_type': 'SUNDAY',
                'estimated_duration_minutes': 90,
                'structure': {
                    'items': [
                        { 'type': 'worship', 'duration': 20, 'description': 'Opening Worship' },
                        { 'type': 'announcements', 'duration': 5, 'description': 'Announcements' },
                        { 'type': 'message', 'duration': 35, 'description': 'Sermon' },
                        { 'type': 'worship', 'duration': 15, 'description': 'Closing Worship' },
                        { 'type': 'dismissal', 'duration': 5, 'description': 'Dismissal' }
                    ]
                }
            }
        ]
        
        return jsonify({
            'templates': mock_templates
        })
        
    except Exception as e:
        logger.error(f"Error fetching service templates: {e}")
        return jsonify({'error': 'Failed to fetch templates'}), 500


# Health Check Endpoint

@serving_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for serving module"""
    try:
        # Check database connectivity
        team_count = ServingTeam.query.count()
        role_count = ServingRole.query.count()
        member_count = TeamMember.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'stats': {
                'teams': team_count,
                'roles': role_count,
                'members': member_count
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Serving module health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
