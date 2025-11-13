"""Note model"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

class NoteSource(str, Enum):
    VOICE = "voice"
    MANUAL = "manual"
    SYSTEM = "system"

class Note(SQLModel, table=True):
    __tablename__ = "notes"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    person_id: str = Field(foreign_key="people.id")
    leader_id: str = Field(foreign_key="leaders.id")
    text: str
    source: NoteSource = Field(default=NoteSource.MANUAL)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    person: "Person" = Relationship(back_populates="notes")
    leader: "Leader" = Relationship(back_populates="notes")


