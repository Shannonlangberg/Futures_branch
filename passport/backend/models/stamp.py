"""Stamp model"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
import uuid

class Stamp(SQLModel, table=True):
    __tablename__ = "stamps"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    person_id: str = Field(foreign_key="people.id")
    track_stop_id: str = Field(foreign_key="track_stops.id")
    stamped_by: str = Field(foreign_key="leaders.id")
    stamped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    person: "Person" = Relationship(back_populates="stamps")
    track_stop: "TrackStop" = Relationship(back_populates="stamps")
    stamped_by_leader: "Leader" = Relationship(back_populates="stamps_created")


