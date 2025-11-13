"""Reports routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth
from core.db import get_session
from sqlmodel import Session, select, func
from models.leader import Leader
from models.assignment import Assignment, AssignmentStatus
from models.track import Track, TrackStop

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/track-health', methods=['GET'])
@require_auth
def get_track_health():
    """Get track health metrics"""
    session = next(get_session())
    track_id = request.args.get('track_id')
    
    if not track_id:
        return jsonify({"error": "track_id required"}), 400
    
    # Get track stops
    stops_stmt = select(TrackStop).where(
        TrackStop.track_id == track_id
    ).order_by(TrackStop.order_index)
    stops = session.exec(stops_stmt).all()
    
    # Get assignments per stop
    result = []
    for stop in stops:
        # Count assignments by status
        assignments_stmt = select(Assignment).where(
            Assignment.track_stop_id == stop.id
        )
        assignments = session.exec(assignments_stmt).all()
        
        status_counts = {
            "NEW": 0,
            "IN_PROGRESS": 0,
            "COMPLETE": 0,
            "NO_SHOW": 0
        }
        
        for assignment in assignments:
            status_counts[assignment.status.value] += 1
        
        result.append({
            "stop_id": stop.id,
            "stop_name": stop.name,
            "order_index": stop.order_index,
            "status_counts": status_counts,
            "total": len(assignments)
        })
    
    return jsonify({
        "track_id": track_id,
        "stops": result
    })

@bp.route('/mentor-load', methods=['GET'])
@require_auth
def get_mentor_load():
    """Get mentor load heatmap"""
    session = next(get_session())
    campus_id = request.args.get('campus_id')
    
    statement = select(Leader).where(Leader.is_active == True)
    if campus_id:
        statement = statement.where(Leader.campus_id == campus_id)
    
    leaders = session.exec(statement).all()
    
    result = []
    for leader in leaders:
        # Count active assignments
        active_stmt = select(Assignment).where(
            Assignment.mentor_leader_id == leader.id,
            Assignment.status.in_([AssignmentStatus.NEW, AssignmentStatus.IN_PROGRESS])
        )
        active_count = len(session.exec(active_stmt).all())
        
        # Calculate load percentage
        load_percentage = (active_count / leader.capacity_slots * 100) if leader.capacity_slots > 0 else 0
        
        result.append({
            "leader_id": leader.id,
            "capacity_slots": leader.capacity_slots,
            "active_assignments": active_count,
            "load_percentage": min(load_percentage, 100),
            "status": "overloaded" if active_count >= leader.capacity_slots else "available"
        })
    
    return jsonify(result)

