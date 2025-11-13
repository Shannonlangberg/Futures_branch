"""Assignment model"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

class AssignmentStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    NO_SHOW = "NO_SHOW"

class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    person_id: str = Field(foreign_key="people.id")
    track_stop_id: str = Field(foreign_key="track_stops.id")
    mentor_leader_id: str = Field(foreign_key="leaders.id")
    status: AssignmentStatus = Field(default=AssignmentStatus.NEW)
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evidence_json: str = Field(default="{}")
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    person: "Person" = Relationship(back_populates="assignments")
    track_stop: "TrackStop" = Relationship(back_populates="assignments")
    mentor: "Leader" = Relationship(back_populates="assignments_mentoring")
    
    def get_evidence(self) -> Dict[str, Any]:
        """Parse evidence JSON"""
        try:
            return json.loads(self.evidence_json)
        except:
            return {}


