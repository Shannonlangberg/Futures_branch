"""
Beacon Management API

Endpoints for managing Bluetooth beacons and zones.
Used by Settings page and mobile app.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, BeaconZone, BeaconSchedule, Person
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

beacon_bp = Blueprint('beacon', __name__, url_prefix='/api/beacons')


def normalize_uuid(uuid_str):
    """Normalize UUID string to uppercase and validate format"""
    if not uuid_str:
        return None
    uuid = str(uuid_str).strip().upper()
    # Validate UUID format: 8-4-4-4-12 hexadecimal digits
    uuid_pattern = re.compile(r'^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$')
    if not uuid_pattern.match(uuid):
        return None
    return uuid


def validate_beacon_data(data):
    """Validate and normalize beacon data from request"""
    errors = []
    
    if 'beacon_uuid' not in data:
        errors.append('Missing required field: beacon_uuid')
    else:
        uuid = normalize_uuid(data['beacon_uuid'])
        if not uuid:
            errors.append('Invalid UUID format. Expected format: 00000000-0000-0000-0000-000000000000')
        else:
            data['beacon_uuid'] = uuid
    
    if 'beacon_major' in data:
        try:
            data['beacon_major'] = int(data['beacon_major'])
            if data['beacon_major'] < 0 or data['beacon_major'] > 65535:
                errors.append('beacon_major must be between 0 and 65535')
        except (ValueError, TypeError):
            errors.append('beacon_major must be an integer')
    
    if 'beacon_minor' in data:
        try:
            data['beacon_minor'] = int(data['beacon_minor'])
            if data['beacon_minor'] < 0 or data['beacon_minor'] > 65535:
                errors.append('beacon_minor must be between 0 and 65535')
        except (ValueError, TypeError):
            errors.append('beacon_minor must be an integer')
    
    return errors


@beacon_bp.route('', methods=['GET'])
@login_required
def get_beacons():
    """Get all beacon zones (admin only)"""
    try:
        if not current_user.has_permission('beacons', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get optional filters
        campus_filter = request.args.get('campus')
        is_active = request.args.get('is_active')
        
        query = BeaconZone.query
        
        if campus_filter and campus_filter != 'all_campuses':
            query = query.filter_by(campus=campus_filter)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter_by(is_active=is_active_bool)
        
        beacons = query.order_by(BeaconZone.campus, BeaconZone.zone_name).all()
        
        return jsonify({
            'beacons': [b.to_dict() for b in beacons],
            'count': len(beacons)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting beacons: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('', methods=['POST'])
@login_required
def create_beacon():
    """Create a new beacon zone (admin only)"""
    try:
        if not current_user.has_permission('beacons', 'create'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['zone_name', 'campus', 'beacon_uuid', 'beacon_major', 'beacon_minor']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate and normalize beacon data
        validation_errors = validate_beacon_data(data)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        uuid = data['beacon_uuid']
        major = data['beacon_major']
        minor = data['beacon_minor']
        
        # Check for duplicate UUID/major/minor combination
        existing = BeaconZone.query.filter_by(
            beacon_uuid=uuid,
            beacon_major=major,
            beacon_minor=minor
        ).first()
        
        if existing:
            return jsonify({'error': 'A beacon with this UUID, major, and minor already exists'}), 400
        
        # Create new beacon zone
        beacon = BeaconZone(
            zone_name=data['zone_name'],
            campus=data['campus'],
            beacon_uuid=uuid,
            beacon_major=major,
            beacon_minor=minor,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(beacon)
        db.session.commit()
        
        return jsonify({
            'message': 'Beacon zone created successfully',
            'beacon': beacon.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating beacon: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/<int:beacon_id>', methods=['GET'])
@login_required
def get_beacon(beacon_id):
    """Get a single beacon zone (admin only)"""
    try:
        if not current_user.has_permission('beacons', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        beacon = BeaconZone.query.get(beacon_id)
        if not beacon:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        return jsonify({'beacon': beacon.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Error getting beacon: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/<int:beacon_id>', methods=['PUT'])
@login_required
def update_beacon(beacon_id):
    """Update a beacon zone (admin only)"""
    try:
        if not current_user.has_permission('beacons', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        beacon = BeaconZone.query.get(beacon_id)
        if not beacon:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'zone_name' in data:
            beacon.zone_name = data['zone_name']
        if 'campus' in data:
            beacon.campus = data['campus']
        if 'beacon_uuid' in data:
            validation_errors = validate_beacon_data({'beacon_uuid': data['beacon_uuid']})
            if validation_errors:
                return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
            beacon.beacon_uuid = data['beacon_uuid']
        if 'beacon_major' in data or 'beacon_minor' in data:
            validation_data = {}
            if 'beacon_major' in data:
                validation_data['beacon_major'] = data['beacon_major']
            if 'beacon_minor' in data:
                validation_data['beacon_minor'] = data['beacon_minor']
            validation_errors = validate_beacon_data(validation_data)
            if validation_errors:
                return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
            if 'beacon_major' in data:
                beacon.beacon_major = data['beacon_major']
            if 'beacon_minor' in data:
                beacon.beacon_minor = data['beacon_minor']
        if 'is_active' in data:
            beacon.is_active = bool(data['is_active'])
        
        # Check for duplicate UUID/major/minor if changed
        if 'beacon_uuid' in data or 'beacon_major' in data or 'beacon_minor' in data:
            existing = BeaconZone.query.filter_by(
                beacon_uuid=beacon.beacon_uuid,
                beacon_major=beacon.beacon_major,
                beacon_minor=beacon.beacon_minor
            ).filter(BeaconZone.id != beacon_id).first()
            
            if existing:
                return jsonify({'error': 'A beacon with this UUID, major, and minor already exists'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Beacon zone updated successfully',
            'beacon': beacon.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating beacon: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/<int:beacon_id>', methods=['DELETE'])
@login_required
def delete_beacon(beacon_id):
    """Delete a beacon zone (admin only)"""
    try:
        if not current_user.has_permission('beacons', 'delete'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        beacon = BeaconZone.query.get(beacon_id)
        if not beacon:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        db.session.delete(beacon)
        db.session.commit()
        
        return jsonify({'message': 'Beacon zone deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting beacon: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/detect', methods=['POST'])
def detect_beacon():
    """
    Public endpoint for mobile app to report beacon detection.
    Creates Heartbeat attendance event automatically.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['person_email', 'beacon_uuid', 'beacon_major', 'beacon_minor']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Find person by email
        person = Person.query.filter_by(email=data['person_email'], is_active=True).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Validate and normalize UUID
        beacon_uuid = normalize_uuid(data['beacon_uuid'])
        if not beacon_uuid:
            return jsonify({'error': 'Invalid UUID format. Expected format: 00000000-0000-0000-0000-000000000000'}), 400
        
        # Validate major and minor
        try:
            beacon_major = int(data['beacon_major'])
            beacon_minor = int(data['beacon_minor'])
            if beacon_major < 0 or beacon_major > 65535:
                return jsonify({'error': 'beacon_major must be between 0 and 65535'}), 400
            if beacon_minor < 0 or beacon_minor > 65535:
                return jsonify({'error': 'beacon_minor must be between 0 and 65535'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'beacon_major and beacon_minor must be integers'}), 400
        
        # Find beacon zone
        zone = BeaconZone.find_zone(
            uuid=beacon_uuid,
            major=beacon_major,
            minor=beacon_minor
        )
        if not zone:
            return jsonify({'error': 'Beacon zone not found or inactive'}), 404
        
        # Get detection time
        detection_time = datetime.utcnow()
        if data.get('timestamp'):
            try:
                detection_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Get active schedule for this beacon at detection time
        schedule = zone.get_active_schedule(detection_time)
        if not schedule:
            return jsonify({
                'error': 'No active schedule found for this beacon at this time',
                'message': 'Beacon is not configured for this day/time. Please check beacon schedules.'
            }), 400
        
        event_type = schedule.event_type
        
        # Create Heartbeat attendance event
        from models import AttendanceEvent
        from heartbeat_engine import HeartbeatEngine
        from datetime import timedelta
        
        # Import Service from models (Heartbeat module)
        try:
            from models import Service
        except ImportError:
            # Fallback if Service not in models
            Service = None
        
        # Find or create the service for this campus and time
        engine = HeartbeatEngine()
        campus_id = engine._get_campus_id(zone.campus)
        
        # Find the service for this campus and time (within 2 hours of detection)
        service = None
        if Service:
            service_start = detection_time - timedelta(hours=2)
            service_end = detection_time + timedelta(hours=1)
            
            service = Service.query.filter(
                Service.campus_id == campus_id,
                Service.type == event_type,  # Use event_type from schedule
                Service.starts_at >= service_start,
                Service.starts_at <= service_end
            ).order_by(Service.starts_at.desc()).first()
        
        # If no service found, create one based on schedule
        if not service and Service:
            # Use schedule's start_time if available, otherwise default
            if schedule.start_time:
                service_date = detection_time.replace(
                    hour=schedule.start_time.hour,
                    minute=schedule.start_time.minute,
                    second=0,
                    microsecond=0
                )
            else:
                # Default based on event type
                if event_type == 'sunday':
                    service_date = detection_time.replace(hour=10, minute=0, second=0, microsecond=0)
                elif event_type == 'youth':
                    service_date = detection_time.replace(hour=19, minute=0, second=0, microsecond=0)
                else:
                    service_date = detection_time.replace(hour=19, minute=0, second=0, microsecond=0)
            
            # Calculate end time
            if schedule.end_time:
                end_time = detection_time.replace(
                    hour=schedule.end_time.hour,
                    minute=schedule.end_time.minute,
                    second=0,
                    microsecond=0
                )
            else:
                end_time = service_date + timedelta(hours=2)
            
            service = Service(
                campus_id=campus_id,
                type=event_type,
                starts_at=service_date,
                ends_at=end_time
            )
            db.session.add(service)
            db.session.flush()
        
        # If Service model doesn't exist, we'll skip creating attendance event
        # but still update engagement profile
        if not Service:
            logger.warning("Service model not available - skipping Heartbeat attendance event creation")
        
        # Create Heartbeat attendance event if Service model exists
        if Service and service:
            # Check for duplicate attendance (within 10 minutes)
            recent_attendance = AttendanceEvent.query.filter(
                AttendanceEvent.person_id == person.id,
                AttendanceEvent.service_id == service.id,
                AttendanceEvent.created_at >= detection_time - timedelta(minutes=10)
            ).first()
            
            if recent_attendance:
                return jsonify({
                    'message': 'Attendance already logged recently',
                    'duplicate': True,
                    'person_id': person.id,
                    'zone': zone.zone_name,
                    'campus': zone.campus
                }), 200
            
            # Create attendance event
            attendance = AttendanceEvent(
                person_id=person.id,
                service_id=service.id,
                source='beacon',
                created_at=detection_time
            )
            db.session.add(attendance)
        
        # Check if this beacon zone is linked to an event and mark event attendance
        try:
            from models import Event, EventRegistration
            from sqlalchemy import text
            
            # Check if beacon_zone_id column exists in events table
            # Use raw SQL to check for events linked to this beacon zone
            try:
                # Try to find events linked to this beacon zone
                # First check if beacon_zone_id column exists
                result = db.session.execute(text("""
                    SELECT name FROM pragma_table_info('events') WHERE name = 'beacon_zone_id'
                """))
                has_beacon_column = result.fetchone() is not None
                
                if has_beacon_column:
                    # Find events linked to this beacon zone that are happening around this time
                    event_window_start = detection_time - timedelta(hours=2)
                    event_window_end = detection_time + timedelta(hours=2)
                    
                    events = db.session.execute(text("""
                        SELECT id, title, start_time, end_time 
                        FROM events 
                        WHERE beacon_zone_id = :zone_id
                        AND start_time <= :window_end
                        AND (end_time IS NULL OR end_time >= :window_start)
                        AND is_active = 1
                    """), {
                        'zone_id': zone.id,
                        'window_start': event_window_start,
                        'window_end': event_window_end
                    }).fetchall()
                    
                    for event_row in events:
                        event_id = event_row[0]
                        event_title = event_row[1]
                        
                        # Check if registration already exists
                        existing_reg = db.session.execute(text("""
                            SELECT id, status FROM event_registrations 
                            WHERE event_id = :event_id AND person_id = :person_id
                        """), {
                            'event_id': event_id,
                            'person_id': person.id
                        }).fetchone()
                        
                        if existing_reg:
                            # Update existing registration to 'attended'
                            reg_id = existing_reg[0]
                            db.session.execute(text("""
                                UPDATE event_registrations 
                                SET status = 'attended', updated_at = :now
                                WHERE id = :reg_id
                            """), {
                                'reg_id': reg_id,
                                'now': detection_time
                            })
                            logger.info(f"Updated event registration {reg_id} to 'attended' for event {event_id} ({event_title})")
                        else:
                            # Create new registration with 'attended' status
                            db.session.execute(text("""
                                INSERT INTO event_registrations 
                                (event_id, person_id, email, name, phone, status, created_at, updated_at)
                                VALUES (:event_id, :person_id, :email, :name, :phone, 'attended', :now, :now)
                            """), {
                                'event_id': event_id,
                                'person_id': person.id,
                                'email': person.email or '',
                                'name': person.full_name or '',
                                'phone': person.phone or '',
                                'now': detection_time
                            })
                            logger.info(f"Created event registration with 'attended' status for event {event_id} ({event_title})")
            except Exception as event_error:
                # If beacon_zone_id column doesn't exist or query fails, just log and continue
                logger.debug(f"Could not check for event registrations (beacon_zone_id may not exist): {event_error}")
        except Exception as e:
            # Don't fail beacon detection if event registration fails
            logger.warning(f"Error checking/creating event registration: {e}")
        
        # Also update engagement profile (legacy system)
        engagement = person.engagement_profile
        if not engagement:
            from models import EngagementProfile
            engagement = EngagementProfile(person_id=person.id)
            db.session.add(engagement)
        
        engagement.add_attendance(
            zones=[zone.zone_name],
            campus=zone.campus,
            attendance_time=detection_time
        )
        
        db.session.commit()
        
        response_data = {
            'message': 'Attendance logged successfully',
            'person_id': person.id,
            'zone': zone.zone_name,
            'campus': zone.campus,
            'event_type': event_type,
            'timestamp': detection_time.isoformat()
        }
        
        if service:
            response_data['service_id'] = service.id
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error detecting beacon: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# SCHEDULE MANAGEMENT ENDPOINTS

@beacon_bp.route('/<int:beacon_id>/schedules', methods=['GET'])
@login_required
def get_beacon_schedules(beacon_id):
    """Get all schedules for a beacon zone"""
    try:
        if not current_user.has_permission('beacons', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        beacon = BeaconZone.query.get(beacon_id)
        if not beacon:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        schedules = beacon.schedules.filter_by(is_active=True).all()
        
        return jsonify({
            'schedules': [s.to_dict() for s in schedules],
            'count': len(schedules)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting schedules: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/<int:beacon_id>/schedules', methods=['POST'])
@login_required
def create_beacon_schedule(beacon_id):
    """Create a new schedule for a beacon zone"""
    try:
        if not current_user.has_permission('beacons', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        beacon = BeaconZone.query.get(beacon_id)
        if not beacon:
            return jsonify({'error': 'Beacon zone not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if 'event_type' not in data:
            return jsonify({'error': 'Missing required field: event_type'}), 400
        
        # Parse times if provided
        start_time = None
        end_time = None
        
        if data.get('start_time'):
            try:
                from datetime import time as dt_time
                time_parts = data['start_time'].split(':')
                start_time = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid start_time format. Use HH:MM:SS'}), 400
        
        if data.get('end_time'):
            try:
                from datetime import time as dt_time
                time_parts = data['end_time'].split(':')
                end_time = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid end_time format. Use HH:MM:SS'}), 400
        
        # Create schedule
        schedule = BeaconSchedule(
            beacon_zone_id=beacon_id,
            event_type=data['event_type'],
            day_of_week=data.get('day_of_week'),
            start_time=start_time,
            end_time=end_time,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule created successfully',
            'schedule': schedule.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating schedule: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
def update_beacon_schedule(schedule_id):
    """Update a beacon schedule"""
    try:
        if not current_user.has_permission('beacons', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        schedule = BeaconSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'event_type' in data:
            schedule.event_type = data['event_type']
        if 'day_of_week' in data:
            schedule.day_of_week = data['day_of_week'] if data['day_of_week'] else None
        if 'start_time' in data:
            if data['start_time']:
                try:
                    from datetime import time as dt_time
                    time_parts = data['start_time'].split(':')
                    schedule.start_time = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
                except (ValueError, IndexError):
                    return jsonify({'error': 'Invalid start_time format'}), 400
            else:
                schedule.start_time = None
        if 'end_time' in data:
            if data['end_time']:
                try:
                    from datetime import time as dt_time
                    time_parts = data['end_time'].split(':')
                    schedule.end_time = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
                except (ValueError, IndexError):
                    return jsonify({'error': 'Invalid end_time format'}), 400
            else:
                schedule.end_time = None
        if 'is_active' in data:
            schedule.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule updated successfully',
            'schedule': schedule.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating schedule: {e}")
        return jsonify({'error': str(e)}), 500


@beacon_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
def delete_beacon_schedule(schedule_id):
    """Delete a beacon schedule"""
    try:
        if not current_user.has_permission('beacons', 'delete'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        schedule = BeaconSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404
        
        db.session.delete(schedule)
        db.session.commit()
        
        return jsonify({'message': 'Schedule deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting schedule: {e}")
        return jsonify({'error': str(e)}), 500

