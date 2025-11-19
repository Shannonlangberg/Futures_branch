"""
Beacon Management API

Endpoints for managing Bluetooth beacons and zones.
Used by Settings page and mobile app.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, BeaconZone, Person
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

beacon_bp = Blueprint('beacon', __name__, url_prefix='/api/beacons')


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
        
        # Validate UUID format (should be like: 00000000-0000-0000-0000-000000000000)
        uuid = data['beacon_uuid'].strip()
        if len(uuid) != 36 or uuid.count('-') != 4:
            return jsonify({'error': 'Invalid UUID format. Expected format: 00000000-0000-0000-0000-000000000000'}), 400
        
        # Validate major and minor are integers
        try:
            major = int(data['beacon_major'])
            minor = int(data['beacon_minor'])
        except (ValueError, TypeError):
            return jsonify({'error': 'beacon_major and beacon_minor must be integers'}), 400
        
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
            uuid = data['beacon_uuid'].strip()
            if len(uuid) != 36 or uuid.count('-') != 4:
                return jsonify({'error': 'Invalid UUID format'}), 400
            beacon.beacon_uuid = uuid
        if 'beacon_major' in data:
            try:
                beacon.beacon_major = int(data['beacon_major'])
            except (ValueError, TypeError):
                return jsonify({'error': 'beacon_major must be an integer'}), 400
        if 'beacon_minor' in data:
            try:
                beacon.beacon_minor = int(data['beacon_minor'])
            except (ValueError, TypeError):
                return jsonify({'error': 'beacon_minor must be an integer'}), 400
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
        
        # Find beacon zone
        zone = BeaconZone.find_zone(
            uuid=data['beacon_uuid'],
            major=data['beacon_major'],
            minor=data['beacon_minor']
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
                Service.type == 'sunday',
                Service.starts_at >= service_start,
                Service.starts_at <= service_end
            ).order_by(Service.starts_at.desc()).first()
        
        # If no service found, create one for today
        if not service and Service:
            # Create service for this Sunday
            service_date = detection_time.replace(hour=10, minute=0, second=0, microsecond=0)
            service = Service(
                campus_id=campus_id,
                type='sunday',
                starts_at=service_date,
                ends_at=service_date + timedelta(hours=2)
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
            'timestamp': detection_time.isoformat()
        }
        
        if service:
            response_data['service_id'] = service.id
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error detecting beacon: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

