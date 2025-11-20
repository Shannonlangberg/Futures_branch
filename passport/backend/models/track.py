"""Track and TrackStop models"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

class Track(SQLModel, table=True):
    __tablename__ = "tracks"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    owner_leader_id: Optional[str] = Field(default=None, foreign_key="leaders.id")
    campus_id: Optional[str] = None
    is_active: bool = Field(default=True)
    
    # Relationships
    stops: List["TrackStop"] = Relationship(back_populates="track")

class TrackStop(SQLModel, table=True):
    __tablename__ = "track_stops"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    track_id: str = Field(foreign_key="tracks.id")
    name: str
    order_index: int
    requirements_json: str = Field(default="{}")  # JSON string for requirements
    
    # Relationships
    track: Track = Relationship(back_populates="stops")
    assignments: List["Assignment"] = Relationship(back_populates="track_stop")
    stamps: List["Stamp"] = Relationship(back_populates="track_stop")
    
    def get_requirements(self) -> Dict[str, Any]:
        """Parse requirements JSON"""
        try:
            return json.loads(self.requirements_json)
        except:
            return {}











