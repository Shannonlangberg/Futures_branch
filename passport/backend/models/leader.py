"""Leader model"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
import uuid

class LeaderRole(str, Enum):
    MENTOR = "mentor"
    TRACK_OWNER = "track_owner"
    CAMPUS_PASTOR = "campus_pastor"
    ADMIN = "admin"

class Leader(SQLModel, table=True):
    __tablename__ = "leaders"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    person_id: str = Field(foreign_key="people.id")
    role: LeaderRole = Field(default=LeaderRole.MENTOR)
    campus_id: Optional[str] = None
    capacity_slots: int = Field(default=5)
    is_active: bool = Field(default=True)
    
    # Relationships
    assignments_mentoring: List["Assignment"] = Relationship(back_populates="mentor")
    stamps_created: List["Stamp"] = Relationship(back_populates="stamped_by_leader")
    notes: List["Note"] = Relationship(back_populates="leader")












