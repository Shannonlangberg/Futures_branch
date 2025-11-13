"""People routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth
from core.db import get_session
from sqlmodel import Session, select
from models.person import Person

bp = Blueprint('people', __name__, url_prefix='/api/people')

@bp.route('', methods=['GET'])
@require_auth
def get_people():
    """Get all people (with optional campus filter)"""
    session = next(get_session())
    campus_id = request.args.get('campus_id')
    
    statement = select(Person)
    if campus_id:
        statement = statement.where(Person.campus_id == campus_id)
    
    people = session.exec(statement).all()
    
    return jsonify([{
        "id": p.id,
        "full_name": p.full_name,
        "email": p.email,
        "phone": p.phone,
        "campus_id": p.campus_id,
        "current_zone": p.current_zone.value,
        "active_track_id": p.active_track_id,
        "pulse_score": p.pulse_score,
        "created_at": p.created_at.isoformat()
    } for p in people])

@bp.route('/<person_id>', methods=['GET'])
@require_auth
def get_person(person_id: str):
    """Get person by ID"""
    session = next(get_session())
    person = session.get(Person, person_id)
    
    if not person:
        return jsonify({"error": "Person not found"}), 404
    
    return jsonify({
        "id": person.id,
        "full_name": person.full_name,
        "email": person.email,
        "phone": person.phone,
        "campus_id": person.campus_id,
        "current_zone": person.current_zone.value,
        "active_track_id": person.active_track_id,
        "pulse_score": person.pulse_score,
        "created_at": person.created_at.isoformat()
    })





