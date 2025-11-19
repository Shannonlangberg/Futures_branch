"""Track routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth
from core.db import get_session
from sqlmodel import Session, select
from models.track import Track, TrackStop

bp = Blueprint('tracks', __name__, url_prefix='/api/tracks')

@bp.route('', methods=['GET'])
@require_auth
def get_tracks():
    """Get all tracks"""
    session = next(get_session())
    campus_id = request.args.get('campus_id')
    
    statement = select(Track).where(Track.is_active == True)
    if campus_id:
        statement = statement.where(Track.campus_id == campus_id)
    
    tracks = session.exec(statement).all()
    
    return jsonify([{
        "id": t.id,
        "name": t.name,
        "owner_leader_id": t.owner_leader_id,
        "campus_id": t.campus_id,
        "is_active": t.is_active
    } for t in tracks])

@bp.route('/<track_id>/stops', methods=['GET'])
@require_auth
def get_track_stops(track_id: str):
    """Get stops for a track"""
    session = next(get_session())
    
    statement = select(TrackStop).where(
        TrackStop.track_id == track_id
    ).order_by(TrackStop.order_index)
    
    stops = session.exec(statement).all()
    
    return jsonify([{
        "id": s.id,
        "track_id": s.track_id,
        "name": s.name,
        "order_index": s.order_index,
        "requirements": s.get_requirements()
    } for s in stops])









