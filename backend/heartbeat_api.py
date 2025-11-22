# heartbeat_api.py
"""
Heartbeat API Blueprint

REST endpoints for the Heartbeat health tracking module.
"""

from flask import Blueprint, jsonify, request
from models import (
    db, Person, Campus, HeartbeatSnapshot, AttendanceEvent, Service,
    HeartbeatConnectGroup, ConnectAttendance, ServingAssignment,
    GivingSummary, GivingTransaction, DiscipleshipStep, CareCase, CareTouchpoint,
    AppSession, TVUserEpisodeProgress, PrayerSubmission
)
from heartbeat_engine import HeartbeatEngine
from datetime import datetime, date, timedelta
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

heartbeat_bp = Blueprint('heartbeat', __name__, url_prefix='/api/heartbeat')

engine = HeartbeatEngine()


@heartbeat_bp.route('/campus/<campus_id>/people', methods=['GET'])
def get_campus_people(campus_id):
    """
    Get all people for a campus with their latest HeartbeatSnapshot.
    
    Query params:
        - status: Filter by status ('healthy', 'watch', 'at_risk', 'critical')
        - department: Filter by department ('Kids', 'Youth', 'Young Adults', 'Families', 'Adults', 'Seniors')
    
    Special case: If campus_id is 'all_campuses', returns all people from all campuses.
    """
    try:
        # Get filters
        status_filter = request.args.get('status')
        department_filter = request.args.get('department')
        
        # Handle "all_campuses" special case
        if campus_id == 'all_campuses' or campus_id == 'all':
            # Get all active people from all campuses
            query = Person.query.filter_by(is_active=True)
            if department_filter:
                query = query.filter_by(department=department_filter)
            people = query.all()
            campus_name = 'All Campuses'
            campus_id_display = 'all_campuses'
        else:
            # Try to find campus by ID first
            campus = Campus.query.get(campus_id)
            
            # If not found by ID, try to find by name (for flexibility)
            if not campus:
                campus = Campus.query.filter_by(name=campus_id).first()
            
            # If still not found, create it from the campus name
            if not campus:
                # Normalize campus_id to create new campus
                campus_id_normalized = campus_id.lower().replace(' ', '_')
                campus = Campus(
                    id=campus_id_normalized,
                    name=campus_id,  # Use original as display name
                    timezone='Australia/Adelaide',
                    is_active=True
                )
                db.session.add(campus)
                db.session.commit()
                logger.info(f"Created Heartbeat campus: {campus_id_normalized} ({campus_id})")
            
            campus_name = campus.name
            campus_id_display = campus_id
            
            # Get people for this campus
            # Try multiple matching strategies
            # 1. Exact match with campus.name
            query = Person.query.filter_by(
                campus=campus.name,
                is_active=True
            )
            
            # Apply department filter if provided
            if department_filter:
                query = query.filter_by(department=department_filter)
            
            people = query.all()
            
            # 2. If no results, try normalized name variations
            if not people:
                # Try common variations
                variations = [
                    campus.name,
                    campus.id.replace('_', ' ').title(),  # copper_coast -> Copper Coast
                    campus.id.replace('_', ' '),  # copper_coast -> copper coast
                    campus.name.lower(),
                    campus.name.upper()
                ]
                for variation in variations:
                    query = Person.query.filter_by(
                        campus=variation,
                        is_active=True
                    )
                    if department_filter:
                        query = query.filter_by(department=department_filter)
                    people = query.all()
                    if people:
                        logger.info(f"Found {len(people)} people using campus variation: {variation}")
                        break
        
        results = []
        for person in people:
            # Get latest snapshot
            snapshot = HeartbeatSnapshot.query.filter_by(
                person_id=person.id
            ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
            
            # Apply status filter
            if status_filter:
                if not snapshot or snapshot.status != status_filter:
                    continue
            
            person_data = {
                'person_id': person.id,
                'full_name': person.full_name,
                'preferred_name': person.preferred_name,
                'email': person.email,
                'phone': person.phone,
                'campus': person.campus,
                'department': person.department
            }
            
            if snapshot:
                person_data['heartbeat'] = snapshot.to_dict()
            else:
                person_data['heartbeat'] = None
            
            results.append(person_data)
        
        return jsonify({
            'campus_id': campus_id_display,
            'campus_name': campus_name,
            'people': results,
            'count': len(results),
            'message': f'Found {len(results)} people for {campus_name}' if results else f'No people found for {campus_name}. Run recalculation after adding data.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting campus people: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        return jsonify({
            'error': str(e),
            'details': 'Check server logs for more information'
        }), 500


@heartbeat_bp.route('/person/<person_id>', methods=['GET'])
def get_person_heartbeat(person_id):
    """
    Get full heartbeat detail for one person, including scores and recent events.
    """
    try:
        person = Person.query.get(person_id)
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Refresh person from database to ensure we have latest milestone data and connect_group
        db.session.refresh(person)
        # Expire all to force fresh queries for relationships
        db.session.expire_all()
        # Re-query person to ensure we have the absolute latest data
        person = Person.query.get(person_id)
        
        # Get latest snapshot
        snapshot = HeartbeatSnapshot.query.filter_by(
            person_id=person_id
        ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
        
        # Check if we need to recalculate (if snapshot is old or doesn't exist)
        should_recalculate = False
        if not snapshot:
            should_recalculate = True
            logger.info(f"No heartbeat snapshot found for {person_id}, will recalculate")
        else:
            # Recalculate if snapshot is older than 1 day OR if there's new connect attendance
            snapshot_age = datetime.utcnow() - snapshot.calculated_at
            if snapshot_age.days > 1:
                should_recalculate = True
                logger.info(f"Heartbeat snapshot for {person_id} is {snapshot_age.days} days old, will recalculate")
            else:
                # Check if there's new connect attendance since last calculation
                recent_connect_count = ConnectAttendance.query.filter(
                    ConnectAttendance.person_id == person_id,
                    ConnectAttendance.date >= snapshot.calculated_at.date()
                ).count()
                if recent_connect_count > 0:
                    should_recalculate = True
                    logger.info(f"Found {recent_connect_count} new connect attendance records for {person_id} since last calculation, will recalculate")
        
        # Auto-recalculate if needed
        if should_recalculate:
            try:
                snapshot = engine.calculate_heartbeat(person_id)
                db.session.commit()  # Ensure snapshot is saved
                logger.info(f"✅ Auto-recalculated heartbeat for {person_id}: gather={snapshot.gather_score}, engagement={snapshot.engagement_score}, spiritual={snapshot.spiritual_score}, care={snapshot.care_score}, total={snapshot.total_score}, status={snapshot.status}")
            except Exception as e:
                logger.error(f"❌ Error auto-recalculating heartbeat for {person_id}: {e}", exc_info=True)
                db.session.rollback()
                # Continue with existing snapshot or None
                if not snapshot:
                    return jsonify({
                        'person_id': person_id,
                        'person': person.to_dict(),
                        'heartbeat': None,
                        'message': 'No heartbeat snapshot found. Run recalculation to generate one.'
                    }), 200
        
        # Get recent events for context
        twelve_weeks_ago = date.today() - timedelta(weeks=12)
        
        # Recent attendance from AttendanceEvent table
        recent_attendance_events = AttendanceEvent.query.filter(
            AttendanceEvent.person_id == person_id,
            AttendanceEvent.created_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
        ).order_by(AttendanceEvent.created_at.desc()).limit(10).all()
        
        # Also get attendance from engagement_profiles.attendance_log (mobile app logs here)
        attendance_from_log = []
        try:
            if person.engagement_profile:
                import json as json_lib
                attendance_log_str = person.engagement_profile.attendance_log or '[]'
                attendance_log = json_lib.loads(attendance_log_str) if attendance_log_str else []
                
                # Convert attendance_log entries to same format as AttendanceEvent
                for entry in attendance_log:
                    if isinstance(entry, dict) and 'timestamp' in entry:
                        try:
                            entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                            # Only include entries from last 12 weeks
                            if entry_time.date() >= twelve_weeks_ago:
                                attendance_from_log.append({
                                    'id': f"log_{entry_time.isoformat()}",
                                    'person_id': person_id,
                                    'created_at': entry_time.isoformat(),
                                    'source': entry.get('zones', ['sunday_service'])[0] if entry.get('zones') else 'sunday_service',
                                    'campus': entry.get('campus', person.campus),
                                    'zones': entry.get('zones', ['sunday_service'])
                                })
                        except Exception as e:
                            logger.warning(f"Error parsing attendance log entry: {e}")
        except Exception as e:
            logger.warning(f"Error reading attendance_log from engagement profile: {e}")
        
        # Combine both sources and sort by date (newest first)
        all_attendance = [a.to_dict() for a in recent_attendance_events] + attendance_from_log
        all_attendance.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        recent_attendance = all_attendance[:10]  # Limit to 10 most recent
        
        # Recent connect attendance (include more to show missed meetings)
        recent_connect = ConnectAttendance.query.filter(
            ConnectAttendance.person_id == person_id,
            ConnectAttendance.date >= twelve_weeks_ago
        ).order_by(ConnectAttendance.date.desc()).limit(20).all()
        
        # Enrich with group names
        for att in recent_connect:
            if att.connect_group:
                att_dict = att.to_dict()
                att_dict['connect_group'] = {
                    'id': att.connect_group.id,
                    'name': att.connect_group.name
                }
                # Replace the to_dict result with enriched version
                att._enriched_dict = att_dict
        
        # Recent serving
        recent_serving = ServingAssignment.query.filter(
            ServingAssignment.person_id == person_id
        ).order_by(ServingAssignment.created_at.desc()).limit(10).all()
        
        # Recent discipleship steps from DiscipleshipStep table
        # Get ALL discipleship steps (not just recent ones) to ensure we capture all milestones
        recent_steps = DiscipleshipStep.query.filter(
            DiscipleshipStep.person_id == person_id
        ).order_by(DiscipleshipStep.date.desc()).all()  # Removed limit to get all steps
        
        logger.info(f"DEBUG: Found {len(recent_steps)} DiscipleshipStep records for person {person_id}")
        for step in recent_steps:
            logger.info(f"  DiscipleshipStep: type={step.type}, date={step.date}, description={step.description}")
        
        # Also include Person-level milestones (baptism, DNA, etc.) as spiritual events
        # Include ALL milestones regardless of date (not just last 12 weeks) since these are significant life events
        person_milestones = []
        
        # Debug: Log person milestone fields
        logger.info(f"DEBUG: Person {person_id} milestone fields - baptised_on: {person.baptised_on}, dna_completed: {person.dna_completed}, filled_holy_spirit: {person.filled_holy_spirit}")
        
        if person.baptised_on:
            person_milestones.append({
                'id': f'person_milestone_baptism_{person.id}',
                'person_id': person_id,
                'type': 'baptism',
                'description': 'Baptism',
                'date': person.baptised_on.isoformat() if person.baptised_on else None,
                'created_at': person.baptised_on.isoformat() if person.baptised_on else None,
                'is_person_milestone': True
            })
        
        if person.dna_completed:
            person_milestones.append({
                'id': f'person_milestone_dna_{person.id}',
                'person_id': person_id,
                'type': 'dna_completed',
                'description': 'DNA Completed',
                'date': person.dna_completed.isoformat() if person.dna_completed else None,
                'created_at': person.dna_completed.isoformat() if person.dna_completed else None,
                'is_person_milestone': True
            })
        
        if person.filled_holy_spirit:
            person_milestones.append({
                'id': f'person_milestone_holy_spirit_{person.id}',
                'person_id': person_id,
                'type': 'filled_holy_spirit',
                'description': 'Filled with Holy Spirit',
                'date': person.filled_holy_spirit.isoformat() if person.filled_holy_spirit else None,
                'created_at': person.filled_holy_spirit.isoformat() if person.filled_holy_spirit else None,
                'is_person_milestone': True
            })
        
        if person.rise_attended:
            person_milestones.append({
                'id': f'person_milestone_rise_{person.id}',
                'person_id': person_id,
                'type': 'rise_attended',
                'description': 'RISE Attended',
                'date': person.rise_attended.isoformat() if person.rise_attended else None,
                'created_at': person.rise_attended.isoformat() if person.rise_attended else None,
                'is_person_milestone': True
            })
        
        if person.first_served_on:
            person_milestones.append({
                'id': f'person_milestone_first_served_{person.id}',
                'person_id': person_id,
                'type': 'first_served',
                'description': 'First Time Serving',
                'date': person.first_served_on.isoformat() if person.first_served_on else None,
                'created_at': person.first_served_on.isoformat() if person.first_served_on else None,
                'is_person_milestone': True
            })
        
        # Get pathway progress to include completed pathway steps as spiritual events
        from models import PersonPathwayProgress, PersonPathwayStepCompletion, PathwayStep
        pathway_progress = PersonPathwayProgress.query.filter_by(
            person_id=person_id,
            is_active=True
        ).first()
        
        # Include completed pathway steps as spiritual events
        pathway_step_events = []
        if pathway_progress:
            db.session.refresh(pathway_progress)
            # Get all completed pathway steps
            completed_steps = PersonPathwayStepCompletion.query.filter_by(
                person_pathway_progress_id=pathway_progress.id
            ).all()
            
            # Get person's connect group name if they have one
            connect_group_name = None
            if person.connect_group:
                try:
                    from models import ConnectGroup
                    connect_group = ConnectGroup.query.filter_by(id=person.connect_group).first()
                    if connect_group:
                        connect_group_name = connect_group.name
                except Exception as e:
                    logger.warning(f"Error fetching connect group name: {e}")
            
            for completion in completed_steps:
                # Handle case where step_actions column doesn't exist yet
                step = None
                try:
                    step = PathwayStep.query.get(completion.pathway_step_id)
                except Exception as e:
                    error_str = str(e).lower()
                    if 'no such column' in error_str and 'step_actions' in error_str:
                        # Column doesn't exist - load step manually without step_actions
                        try:
                            from sqlalchemy import text
                            raw_step = db.session.execute(
                                text('''
                                    SELECT id, pathway_id, step_order, step_name, step_description, 
                                           milestone_type, is_required, created_at
                                    FROM discipleship_pathway_steps 
                                    WHERE id = :step_id
                                '''),
                                {'step_id': completion.pathway_step_id}
                            ).fetchone()
                            
                            if raw_step:
                                # Create a minimal PathwayStep-like object
                                class MinimalStep:
                                    def __init__(self, row):
                                        self.id = row[0]
                                        self.pathway_id = row[1]
                                        self.step_order = row[2]
                                        self.step_name = row[3]
                                        self.step_description = row[4]
                                        self.milestone_type = row[5]
                                        self.is_required = row[6]
                                        self.created_at = row[7]
                                    def get_actions(self):
                                        return []
                                
                                step = MinimalStep(raw_step)
                                logger.debug(f"Loaded pathway step {completion.pathway_step_id} without step_actions column")
                        except Exception as e2:
                            logger.warning(f"Error loading pathway step {completion.pathway_step_id} manually: {e2}")
                            step = None
                    else:
                        # Different error - log and continue
                        logger.warning(f"Error loading pathway step {completion.pathway_step_id}: {e}")
                        step = None
                
                if step and completion.completed_at:
                    # Map milestone types to spiritual event types
                    milestone_type = step.milestone_type or ''
                    step_type = milestone_type if milestone_type else step.step_name.lower().replace(' ', '_')
                    
                    # Build description with connect group name if applicable
                    description = step.step_name
                    if milestone_type == 'group_join' and connect_group_name:
                        description = f"{step.step_name}: {connect_group_name}"
                    
                    pathway_step_events.append({
                        'id': f'pathway_step_{completion.id}',
                        'person_id': person_id,
                        'type': step_type,
                        'description': description,
                        'date': completion.completed_at.isoformat() if completion.completed_at else None,
                        'created_at': completion.completed_at.isoformat() if completion.completed_at else None,
                        'is_person_milestone': False,
                        'is_pathway_step': True,
                        'step_order': step.step_order,
                        'milestone_type': milestone_type,
                        'connect_group_name': connect_group_name if milestone_type == 'group_join' else None
                    })
                    
            # Refresh relationships to get latest step completions
            try:
                # Force reload of step_completions relationship
                _ = pathway_progress.step_completions.all()
            except Exception as e:
                logger.warning(f"Error refreshing pathway step completions: {e}")
        
        # Combine DiscipleshipStep records with Person milestones and pathway steps
        all_discipleship_steps = [d.to_dict() for d in recent_steps] + person_milestones + pathway_step_events
        
        # Debug: Log what we're returning
        logger.info(f"DEBUG: Returning {len(all_discipleship_steps)} total discipleship steps:")
        logger.info(f"  - DiscipleshipStep records: {len(recent_steps)}")
        logger.info(f"  - Person milestones: {len(person_milestones)}")
        logger.info(f"  - Pathway step completions: {len(pathway_step_events)}")
        for milestone in person_milestones:
            logger.info(f"    Person milestone: {milestone.get('type')} - {milestone.get('description')} on {milestone.get('date')}")
        for step_event in pathway_step_events:
            logger.info(f"    Pathway step: {step_event.get('type')} - {step_event.get('description')} on {step_event.get('date')}")
        
        # Sort by date (newest first)
        all_discipleship_steps.sort(key=lambda x: x.get('date') or x.get('created_at') or '', reverse=True)
        
        # Open care cases
        open_cases = CareCase.query.filter(
            CareCase.person_id == person_id,
            CareCase.status.in_(['open', 'in_progress'])
        ).all()
        
        # Recent giving transactions
        recent_giving = GivingTransaction.query.filter(
            GivingTransaction.person_id == person_id,
            GivingTransaction.status == 'completed',
            GivingTransaction.created_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
        ).order_by(GivingTransaction.created_at.desc()).limit(20).all()
        
        logger.info(f"DEBUG: Found {len(recent_giving)} giving transactions for person {person_id} in last 12 weeks")
        
        # NEW: App opens (engagement tracking)
        recent_app_opens = []
        try:
            recent_app_opens = AppSession.query.filter(
                AppSession.person_id == person_id,
                AppSession.session_start >= datetime.combine(twelve_weeks_ago, datetime.min.time())
            ).order_by(AppSession.session_start.desc()).limit(20).all()
        except Exception as e:
            logger.warning(f"Error fetching app sessions for person {person_id}: {e}")
            recent_app_opens = []
        
        # NEW: TV episode completions (spiritual growth)
        recent_tv = []
        try:
            recent_tv = TVUserEpisodeProgress.query.filter(
                TVUserEpisodeProgress.person_id == person_id,
                TVUserEpisodeProgress.completed == True,
                TVUserEpisodeProgress.completed_at.isnot(None),
                TVUserEpisodeProgress.completed_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
            ).order_by(TVUserEpisodeProgress.completed_at.desc()).limit(20).all()
        except Exception as e:
            logger.warning(f"Error fetching TV episode progress for person {person_id}: {e}")
            recent_tv = []
        
        # NEW: Prayer submissions (care/spiritual)
        recent_prayers = []
        try:
            recent_prayers = PrayerSubmission.query.filter(
                PrayerSubmission.person_id == person_id,
                PrayerSubmission.created_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
            ).order_by(PrayerSubmission.created_at.desc()).limit(20).all()
        except Exception as e:
            logger.warning(f"Error fetching prayer submissions for person {person_id}: {e}")
            recent_prayers = []
        
        logger.info(f"📊 NEW DATA: app_opens={len(recent_app_opens)}, tv_completions={len(recent_tv)}, prayers={len(recent_prayers)}")
        
        # Log what we're returning
        heartbeat_dict = snapshot.to_dict() if snapshot else None
        logger.info(f"📤 Returning heartbeat data for {person_id}: gather_score={heartbeat_dict.get('gather_score') if heartbeat_dict else 'None'}, total_score={heartbeat_dict.get('total_score') if heartbeat_dict else 'None'}, attendance_count={len(recent_attendance)}, giving_count={len(recent_giving)}")
        
        return jsonify({
            'person_id': person_id,
            'person': person.to_dict(),
            'heartbeat': heartbeat_dict,
            'journey': pathway_progress.to_dict() if pathway_progress else None,
            'pathway': pathway_progress.to_dict() if pathway_progress else None,  # Keep for backward compatibility
            'recent_activity': {
                'attendance': recent_attendance if recent_attendance and isinstance(recent_attendance[0], dict) else ([a.to_dict() for a in recent_attendance] if recent_attendance else []),
                'connect_groups': [
                    (c._enriched_dict if hasattr(c, '_enriched_dict') else c.to_dict()) 
                    for c in recent_connect
                ],
                'serving': [s.to_dict() for s in recent_serving],
                'giving': [g.to_dict() for g in recent_giving],
                'discipleship_steps': all_discipleship_steps,
                'open_care_cases': [c.to_dict() for c in open_cases],
                'app_opens': [a.to_dict() for a in recent_app_opens],
                'tv_completions': [t.to_dict() for t in recent_tv],
                'prayer_submissions': [p.to_dict() for p in recent_prayers]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting person heartbeat: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        return jsonify({'error': str(e), 'details': 'Check server logs for more information'}), 500


@heartbeat_bp.route('/recalculate/<campus_id>', methods=['POST'])
def recalculate_campus(campus_id):
    """
    Trigger recalculation for all active people in a campus.
    
    Special case: If campus_id is 'all_campuses', recalculates for all people.
    
    Returns:
        Summary of processed people and any errors
    """
    try:
        # Handle "all_campuses" special case
        if campus_id == 'all_campuses' or campus_id == 'all':
            # Get all active people from all campuses
            all_people = Person.query.filter_by(is_active=True).all()
            processed = 0
            errors = 0
            
            for person in all_people:
                try:
                    engine.calculate_heartbeat(person.id)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error calculating heartbeat for person {person.id}: {e}")
                    errors += 1
            
            result = {
                'processed': processed,
                'errors': errors,
                'total': len(all_people)
            }
            campus_name = 'All Campuses'
        else:
            result = engine.recalculate_campus(campus_id)
            # Get campus name for response
            campus = Campus.query.get(campus_id)
            campus_name = campus.name if campus else campus_id
        
        return jsonify({
            'message': 'Recalculation completed',
            'campus_id': campus_id,
            'campus_name': campus_name,
            'results': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error recalculating campus: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/recalculate/person/<person_id>', methods=['POST'])
def recalculate_person(person_id):
    """
    Trigger recalculation for a specific person.
    
    Query params:
        - start_date: Optional start date (YYYY-MM-DD)
        - end_date: Optional end date (YYYY-MM-DD)
    """
    try:
        # Parse optional date range
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        if request.args.get('end_date'):
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        snapshot = engine.calculate_heartbeat(person_id, start_date, end_date)
        
        return jsonify({
            'message': 'Recalculation completed',
            'person_id': person_id,
            'snapshot': snapshot.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error recalculating person: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/snapshots/<person_id>', methods=['GET'])
def get_person_snapshots(person_id):
    """
    Get all historical snapshots for a person.
    
    Query params:
        - limit: Maximum number of snapshots to return (default: 10)
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        snapshots = HeartbeatSnapshot.query.filter_by(
            person_id=person_id
        ).order_by(HeartbeatSnapshot.calculated_at.desc()).limit(limit).all()
        
        return jsonify({
            'person_id': person_id,
            'snapshots': [s.to_dict() for s in snapshots],
            'count': len(snapshots)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting snapshots: {e}")
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/next-steps', methods=['GET'])
def get_next_steps():
    """
    Get people who are ready for their next discipleship step.
    
    Query params:
        - campus_id: Optional campus filter
        - department: Optional department filter
    
    Returns people who:
        - Have completed their current pathway step and are ready for the next
        - Don't have a pathway assigned but should have one
    """
    try:
        from models import PersonPathwayProgress, PersonPathwayStepCompletion, PathwayStep
        
        campus_filter = request.args.get('campus_id')
        department_filter = request.args.get('department')
        
        # Build base query
        query = Person.query.filter_by(is_active=True)
        if campus_filter and campus_filter != 'all_campuses':
            query = query.filter_by(campus=campus_filter)
        if department_filter:
            query = query.filter_by(department=department_filter)
        
        people = query.all()
        
        results = []
        for person in people:
            # Get latest heartbeat snapshot
            snapshot = HeartbeatSnapshot.query.filter_by(
                person_id=person.id
            ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
            
            # Check pathway progress
            progress = PersonPathwayProgress.query.filter_by(
                person_id=person.id,
                is_active=True
            ).first()
            
            next_step_info = None
            reason = None
            
            if progress and progress.current_step:
                # Check if current step is completed
                current_step_completion = PersonPathwayStepCompletion.query.filter_by(
                    person_pathway_progress_id=progress.id,
                    pathway_step_id=progress.current_step_id,
                    is_completed=True
                ).first()
                
                if current_step_completion:
                    # Find next step in pathway
                    next_step = PathwayStep.query.filter_by(
                        pathway_id=progress.pathway_id,
                        step_order=progress.current_step.step_order + 1
                    ).first()
                    
                    if next_step:
                        # Get pathway name
                        from models import DiscipleshipPathway
                        pathway = DiscipleshipPathway.query.get(progress.pathway_id)
                        next_step_info = {
                            'pathway_id': progress.pathway_id,
                            'pathway_name': pathway.name if pathway else None,
                            'current_step': progress.current_step.step_name,
                            'next_step': next_step.step_name,
                            'next_step_id': next_step.id
                        }
                        reason = 'ready_for_next_step'
            elif not progress:
                # Person doesn't have a pathway assigned
                reason = 'no_pathway_assigned'
            
            # Only include people who need a next step
            if next_step_info or reason == 'no_pathway_assigned':
                person_data = {
                    'person_id': person.id,
                    'full_name': person.full_name,
                    'preferred_name': person.preferred_name,
                    'email': person.email,
                    'phone': person.phone,
                    'campus': person.campus,
                    'department': person.department,
                    'next_step': next_step_info,
                    'reason': reason
                }
                
                if snapshot:
                    person_data['heartbeat'] = snapshot.to_dict()
                else:
                    person_data['heartbeat'] = None
                
                results.append(person_data)
        
        return jsonify({
            'people': results,
            'count': len(results),
            'message': f'Found {len(results)} people ready for next steps'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting next steps: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/campus-overview', methods=['GET'])
def get_campus_overview():
    """
    Get overview of all campuses with heartbeat statistics.
    
    Returns summary stats for each campus: healthy, watch, at_risk, critical counts.
    """
    try:
        campuses = Campus.query.filter_by(is_active=True).all()
        
        results = []
        for campus in campuses:
            # Get people for this campus
            people = Person.query.filter_by(
                campus=campus.name,
                is_active=True
            ).all()
            
            stats = {
                'total': len(people),
                'healthy': 0,
                'watch': 0,
                'at_risk': 0,
                'critical': 0,
                'no_data': 0
            }
            
            for person in people:
                snapshot = HeartbeatSnapshot.query.filter_by(
                    person_id=person.id
                ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
                
                if snapshot:
                    status = snapshot.status
                    if status == 'healthy':
                        stats['healthy'] += 1
                    elif status == 'watch':
                        stats['watch'] += 1
                    elif status == 'at_risk':
                        stats['at_risk'] += 1
                    elif status == 'critical':
                        stats['critical'] += 1
                else:
                    stats['no_data'] += 1
            
            results.append({
                'campus_id': campus.id,
                'campus_name': campus.name,
                'stats': stats
            })
        
        return jsonify({
            'campuses': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting campus overview: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@heartbeat_bp.route('/department-overview', methods=['GET'])
def get_department_overview():
    """
    Get overview by department with heartbeat statistics.
    
    Query params:
        - campus_id: Optional campus filter
    
    Returns summary stats for each department: healthy, watch, at_risk, critical counts.
    """
    try:
        campus_filter = request.args.get('campus_id')
        
        departments = ['Kids', 'Youth', 'Young Adults', 'Families', 'Adults', 'Seniors']
        
        results = []
        for dept in departments:
            query = Person.query.filter_by(
                department=dept,
                is_active=True
            )
            
            if campus_filter and campus_filter != 'all_campuses':
                query = query.filter_by(campus=campus_filter)
            
            people = query.all()
            
            stats = {
                'total': len(people),
                'healthy': 0,
                'watch': 0,
                'at_risk': 0,
                'critical': 0,
                'no_data': 0
            }
            
            for person in people:
                snapshot = HeartbeatSnapshot.query.filter_by(
                    person_id=person.id
                ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
                
                if snapshot:
                    status = snapshot.status
                    if status == 'healthy':
                        stats['healthy'] += 1
                    elif status == 'watch':
                        stats['watch'] += 1
                    elif status == 'at_risk':
                        stats['at_risk'] += 1
                    elif status == 'critical':
                        stats['critical'] += 1
                else:
                    stats['no_data'] += 1
            
            if stats['total'] > 0:  # Only include departments with people
                results.append({
                    'department': dept,
                    'stats': stats
                })
        
        return jsonify({
            'departments': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting department overview: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

