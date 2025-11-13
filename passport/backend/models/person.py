"""Person model"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid

class Zone(str, Enum):
    FOUND = "FOUND"
    FAITHFUL = "FAITHFUL"
    FRUITFUL = "FRUITFUL"
    FOCUSED = "FOCUSED"

class Person(SQLModel, table=True):
    __tablename__ = "people"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    campus_id: Optional[str] = None
    current_zone: Zone = Field(default=Zone.FOUND)
    active_track_id: Optional[str] = Field(default=None, foreign_key="tracks.id")
    pulse_score: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    assignments: List["Assignment"] = Relationship(back_populates="person")
    stamps: List["Stamp"] = Relationship(back_populates="person")
    activities: List["Activity"] = Relationship(back_populates="person")
    notes: List["Note"] = Relationship(back_populates="person")

