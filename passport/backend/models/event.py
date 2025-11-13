"""Event Log model"""
from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import json

class EventLog(SQLModel, table=True):
    __tablename__ = "events_log"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event_type: str
    payload_json: str = Field(default="{}")
    actor_id: Optional[str] = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_payload(self) -> Dict[str, Any]:
        """Parse payload JSON"""
        try:
            return json.loads(self.payload_json)
        except:
            return {}


