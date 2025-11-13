"""Notes routes"""
from flask import Blueprint, request, jsonify
from core.auth import require_auth, get_current_leader
from core.db import get_session
from sqlmodel import Session, select
from models.note import Note, NoteSource
from datetime import datetime, timezone

bp = Blueprint('notes', __name__, url_prefix='/api/notes')

@bp.route('', methods=['POST'])
@require_auth
def create_note():
    """Create a note (voice or manual)"""
    leader_info = get_current_leader()
    if not leader_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    person_id = data.get('person_id')
    text = data.get('text')
    source = data.get('source', 'manual')
    
    if not all([person_id, text]):
        return jsonify({"error": "person_id and text required"}), 400
    
    try:
        source_enum = NoteSource(source)
    except ValueError:
        source_enum = NoteSource.MANUAL
    
    session = next(get_session())
    
    note = Note(
        person_id=person_id,
        leader_id=leader_info["leader_id"],
        text=text,
        source=source_enum,
        created_at=datetime.now(timezone.utc)
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    
    return jsonify({
        "id": note.id,
        "person_id": note.person_id,
        "text": note.text,
        "source": note.source.value,
        "created_at": note.created_at.isoformat()
    })

@bp.route('/person/<person_id>', methods=['GET'])
@require_auth
def get_person_notes(person_id: str):
    """Get all notes for a person"""
    session = next(get_session())
    
    statement = select(Note).where(
        Note.person_id == person_id
    ).order_by(Note.created_at.desc())
    
    notes = session.exec(statement).all()
    
    return jsonify([{
        "id": n.id,
        "leader_id": n.leader_id,
        "text": n.text,
        "source": n.source.value,
        "created_at": n.created_at.isoformat()
    } for n in notes])





