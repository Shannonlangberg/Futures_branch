"""Transfer model"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

class TransferStatus(str, Enum):
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"

class Transfer(SQLModel, table=True):
    __tablename__ = "transfers"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    person_id: str = Field(foreign_key="people.id")
    from_leader_id: str = Field(foreign_key="leaders.id")
    to_leader_id: str = Field(foreign_key="leaders.id")
    track_stop_id: str = Field(foreign_key="track_stops.id")
    status: TransferStatus = Field(default=TransferStatus.SENT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None


