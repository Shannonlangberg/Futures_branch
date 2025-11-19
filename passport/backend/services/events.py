"""Event logging service"""
from datetime import datetime, timezone
from sqlmodel import Session, select
from models.event import EventLog
import json

def log_event(
    session: Session,
    event_type: str,
    payload: dict,
    actor_id: str = None
) -> EventLog:
    """Log an event to the events_log table"""
    event = EventLog(
        event_type=event_type,
        payload_json=json.dumps(payload),
        actor_id=actor_id,
        occurred_at=datetime.now(timezone.utc)
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event









