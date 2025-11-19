"""
Connect Groups API

Endpoints for managing connect groups, joining groups, and attendance.
"""
from flask import Blueprint, request, jsonify
from models import db, ConnectGroup, Person, ConnectGroupMeeting, ConnectGroupAttendance, EngagementProfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

connect_groups_bp = Blueprint('connect_groups', __name__, url_prefix='/api/connect-groups')


def get_person_by_email(email):
    """Get person by email"""
    return Person.query.filter_by(email=email, is_active=True).first()


@connect_groups_bp.route('', methods=['GET'])
def get_connect_groups():
    """Get all connect groups (optionally filtered by campus)"""
    try:
        campus = request.args.get('campus')
        is_active = request.args.get('is_active', 'true')
        
        query = ConnectGroup.query
        
        if campus:
            query = query.filter_by(campus=campus)
        
        if is_active.lower() == 'true':
            query = query.filter_by(is_active=True)
        
        groups = query.all()
        
        return jsonify({
            'groups': [g.to_dict() for g in groups],
            'count': len(groups)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connect groups: {e}")
        return jsonify({'error': str(e)}), 500


@connect_groups_bp.route('/my-groups', methods=['GET'])
def get_my_groups():
    """Get groups that a person belongs to"""
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Get person's connect group
        if not person.connect_group:
            return jsonify({'groups': [], 'count': 0}), 200
        
        # Find the group
        group = ConnectGroup.query.filter_by(id=person.connect_group, is_active=True).first()
        
        if not group:
            return jsonify({'groups': [], 'count': 0}), 200
        
        return jsonify({
            'groups': [group.to_dict()],
            'count': 1
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting my groups: {e}")
        return jsonify({'error': str(e)}), 500


@connect_groups_bp.route('/join', methods=['POST'])
def join_group():
    """Request to join a connect group"""
    try:
        data = request.get_json()
        email = data.get('email')
        group_id = data.get('group_id')
        
        if not email or not group_id:
            return jsonify({'error': 'Email and group_id required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        group = ConnectGroup.query.filter_by(id=group_id, is_active=True).first()
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        # Store old connect group to check if it's a new assignment
        old_connect_group = person.connect_group
        
        # Update person's connect group
        person.connect_group = group_id
        db.session.flush()  # Flush to ensure person is updated before pathway logic
        
        # If person was just assigned to a connect group (was None/empty, now has value),
        # auto-complete the "Joined Connect Group" pathway step
        if not old_connect_group and group_id:
            try:
                from models import PersonPathwayProgress, PathwayStep, PersonPathwayStepCompletion
                
                # Find active pathway progress for this person
                active_progress = PersonPathwayProgress.query.filter_by(
                    person_id=person.id,
                    is_active=True
                ).first()
                
                if active_progress:
                    # Find the "Joined Connect Group" step (milestone_type = "group_join")
                    connect_step = PathwayStep.query.filter_by(
                        pathway_id=active_progress.pathway_id,
                        milestone_type='group_join'
                    ).first()
                    
                    if connect_step:
                        # Check if already completed
                        existing_completion = PersonPathwayStepCompletion.query.filter_by(
                            person_pathway_progress_id=active_progress.id,
                            pathway_step_id=connect_step.id
                        ).first()
                        
                        if not existing_completion:
                            # Auto-complete the step
                            completion = PersonPathwayStepCompletion(
                                person_pathway_progress_id=active_progress.id,
                                pathway_step_id=connect_step.id,
                                completed_by_person_id=person.id,  # Person completes their own step
                                completed_at=datetime.utcnow(),
                                notes=f'Auto-completed when joined connect group: {group.name}'
                            )
                            db.session.add(completion)
                            
                            # Update current step to next uncompleted step
                            next_step = active_progress.get_next_step()
                            active_progress.current_step_id = next_step.id if next_step else None
                            
                            # Mark as started if not already
                            if not active_progress.started_at:
                                active_progress.started_at = datetime.utcnow()
                            
                            # Check if pathway is complete
                            if not next_step:
                                active_progress.completed_at = datetime.utcnow()
                            
                            active_progress.updated_at = datetime.utcnow()
                            
                            # Trigger Heartbeat recalculation since spiritual score may have changed
                            try:
                                from heartbeat_engine import HeartbeatEngine
                                engine = HeartbeatEngine()
                                engine.calculate_heartbeat(person.id)
                                logger.info(f"Auto-completed 'Joined Connect Group' step and recalculated Heartbeat for person {person.id}")
                            except Exception as hb_error:
                                logger.warning(f"Failed to recalculate Heartbeat after auto-completing pathway step: {hb_error}")
                                # Don't fail the request if recalculation fails
            except Exception as pathway_error:
                logger.warning(f"Error auto-completing pathway step when joining connect group: {pathway_error}", exc_info=True)
                # Don't fail the join request if pathway step completion fails
        
        db.session.commit()
        
        logger.info(f"Person {email} joined group {group_id}")
        
        return jsonify({
            'success': True,
            'message': 'Successfully joined group',
            'group': group.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error joining group: {e}")
        return jsonify({'error': str(e)}), 500


@connect_groups_bp.route('/attendance', methods=['POST'])
def submit_group_attendance():
    """Submit connect group attendance"""
    try:
        data = request.get_json()
        email = data.get('email')
        group_id = data.get('group_id')
        meeting_date = data.get('meeting_date')
        status = data.get('status', 'present')  # 'present', 'absent', 'apology'
        
        if not email or not group_id or not meeting_date:
            return jsonify({'error': 'Email, group_id, and meeting_date required'}), 400
        
        person = get_person_by_email(email)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        group = ConnectGroup.query.filter_by(id=group_id, is_active=True).first()
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        # Parse meeting date
        try:
            if isinstance(meeting_date, str):
                meeting_date_obj = datetime.fromisoformat(meeting_date.split('T')[0]).date()
            else:
                meeting_date_obj = meeting_date
        except Exception:
            return jsonify({'error': 'Invalid meeting_date format'}), 400
        
        # Find or create meeting
        meeting = ConnectGroupMeeting.query.filter_by(
            group_id=group_id,
            meeting_date=meeting_date_obj
        ).first()
        
        if not meeting:
            meeting = ConnectGroupMeeting(
                group_id=group_id,
                meeting_date=meeting_date_obj,
                notes=''
            )
            db.session.add(meeting)
            db.session.flush()
        
        # Check if attendance already exists
        existing = ConnectGroupAttendance.query.filter_by(
            meeting_id=meeting.id,
            person_id=person.id
        ).first()
        
        if existing:
            existing.present = (status == 'present')
        else:
            attendance = ConnectGroupAttendance(
                meeting_id=meeting.id,
                person_id=person.id,
                present=(status == 'present'),
                notes=''
            )
            db.session.add(attendance)
        
        # Update engagement profile
        engagement = person.engagement_profile
        if not engagement:
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        engagement.add_group_attendance(
            group_id=group_id,
            attendance_date=meeting_date_obj,
            present=(status == 'present')
        )
        engagement.recalculate_heartbeat()
        
        # ALSO create ConnectAttendance record for Heartbeat system
        if status == 'present':  # Only create for present attendance
            try:
                from models import ConnectAttendance, HeartbeatConnectGroup, Campus as HeartbeatCampus
                from heartbeat_engine import HeartbeatEngine
                
                # Get or create Heartbeat campus
                campus_normalized = group.campus.lower().replace(' ', '_') if group.campus else 'unknown'
                heartbeat_campus = HeartbeatCampus.query.filter_by(id=campus_normalized).first()
                if not heartbeat_campus:
                    heartbeat_campus = HeartbeatCampus(
                        id=campus_normalized,
                        name=group.campus or 'Unknown',
                        timezone='Australia/Adelaide',
                        is_active=True
                    )
                    db.session.add(heartbeat_campus)
                    db.session.flush()
                    logger.info(f"Created Heartbeat campus: {campus_normalized}")
                
                # Find or create HeartbeatConnectGroup
                heartbeat_group = HeartbeatConnectGroup.query.filter_by(
                    name=group.name,
                    campus_id=heartbeat_campus.id,
                    is_active=True
                ).first()
                
                if not heartbeat_group:
                    # Try matching by name and campus only
                    heartbeat_group = HeartbeatConnectGroup.query.filter_by(
                        name=group.name,
                        campus_id=heartbeat_campus.id
                    ).first()
                
                if not heartbeat_group:
                    heartbeat_group = HeartbeatConnectGroup(
                        campus_id=heartbeat_campus.id,
                        name=group.name,
                        leader_person_id=group.leader_id if hasattr(group, 'leader_id') else None,
                        type='home',
                        day_of_week=group.meeting_day if hasattr(group, 'meeting_day') else None,
                        is_active=group.is_active if hasattr(group, 'is_active') else True
                    )
                    db.session.add(heartbeat_group)
                    db.session.flush()
                    logger.info(f"Created HeartbeatConnectGroup: {heartbeat_group.id} for {group.name}")
                
                # Create or update ConnectAttendance record
                existing_attendance = ConnectAttendance.query.filter_by(
                    person_id=person.id,
                    connect_group_id=heartbeat_group.id,
                    date=meeting_date_obj
                ).first()
                
                if existing_attendance:
                    existing_attendance.status = 'present'
                    logger.info(f"Updated ConnectAttendance for {person.full_name} on {meeting_date_obj}")
                else:
                    connect_attendance = ConnectAttendance(
                        person_id=person.id,
                        connect_group_id=heartbeat_group.id,
                        date=meeting_date_obj,
                        status='present'
                    )
                    db.session.add(connect_attendance)
                    logger.info(f"Created ConnectAttendance for {person.full_name} on {meeting_date_obj}")
                
                # Recalculate heartbeat using HeartbeatEngine
                engine = HeartbeatEngine()
                snapshot = engine.calculate_heartbeat(person.id)
                logger.info(f"Recalculated heartbeat for {person.full_name}: engagement={snapshot.engagement_score}, total={snapshot.total_score}")
                
            except Exception as hb_error:
                logger.error(f"Error creating Heartbeat ConnectAttendance record: {hb_error}", exc_info=True)
                # Don't fail the whole operation if Heartbeat sync fails
        
        db.session.commit()
        
        logger.info(f"Group attendance recorded: {email} - {group_id} - {status}")
        
        return jsonify({
            'success': True,
            'message': 'Attendance recorded',
            'status': status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting group attendance: {e}")
        return jsonify({'error': str(e)}), 500


