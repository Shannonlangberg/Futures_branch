"""Activity model"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

class ActivityType(str, Enum):
    ATTEND = "ATTEND"
    SERVE = "SERVE"
    GIVE = "GIVE"
    NOTE = "NOTE"
    QUIZ = "QUIZ"

class Activity(SQLModel, table=True):
    __tablename__ = "activities"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    person_id: str = Field(foreign_key="people.id")
    type: ActivityType
    payload: str = Field(default="{}")  # JSON string
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    person: "Person" = Relationship(back_populates="activities")
    
    def get_payload(self) -> Dict[str, Any]:
        """Parse payload JSON"""
        try:
            return json.loads(self.payload)
        except:
            return {}


