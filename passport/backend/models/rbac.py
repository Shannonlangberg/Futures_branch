"""RBAC Role model"""
from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum
import uuid

class RBACScope(str, Enum):
    CAMPUS = "campus"
    TRACK = "track"
    GLOBAL = "global"

class RBACRole(SQLModel, table=True):
    __tablename__ = "rbac_roles"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    leader_id: str = Field(foreign_key="leaders.id")
    scope: RBACScope
    scope_id: Optional[str] = None  # campus_id or track_id if scope is campus/track








