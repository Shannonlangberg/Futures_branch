"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlmodel import SQLModel

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables
    from models import (
        Person, Track, TrackStop, Leader, Assignment,
        Stamp, Transfer, Activity, Note, RBACRole, EventLog
    )
    from core.db import engine
    
    SQLModel.metadata.create_all(engine)


def downgrade() -> None:
    # Drop all tables
    from models import (
        Person, Track, TrackStop, Leader, Assignment,
        Stamp, Transfer, Activity, Note, RBACRole, EventLog
    )
    from core.db import engine
    
    SQLModel.metadata.drop_all(engine)






