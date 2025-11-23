"""
Devotions Module Database Models
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json
from models import db

class DevotionPlan(db.Model):
    """Devotional plan model"""
    __tablename__ = 'devotion_plans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)
    source = db.Column(db.String(50), default='canvas')  # 'canvas', 'uploaded', 'public'
    
    # Audience targeting
    campus = db.Column(db.String(100), nullable=True)  # Null = all campuses
    audience = db.Column(db.Text, nullable=True)  # JSON: {campus:["Paradise"], departments:["Youth"]}
    
    # Status
    status = db.Column(db.String(20), default='draft')  # 'draft', 'published', 'archived'
    is_assigned = db.Column(db.Boolean, default=False)
    
    # Dates
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    
    # Metadata
    created_by = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    content = db.relationship('DevotionContent', backref='plan', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cover_url': self.cover_url,
            'source': self.source,
            'campus': self.campus,
            'audience': json.loads(self.audience) if self.audience else {},
            'status': self.status,
            'is_assigned': self.is_assigned,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'content_count': self.content.count() if self.content else 0
        }

class DevotionContent(db.Model):
    """Individual day content for a devotion plan"""
    __tablename__ = 'devotion_content'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = db.Column(db.String(36), db.ForeignKey('devotion_plans.id'), nullable=False)
    
    day_index = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    scripture_ref = db.Column(db.String(200), nullable=False)  # e.g. "Luke 11:1-13 (NIV)"
    scripture_text = db.Column(db.Text, nullable=False)  # Full scripture text
    devo_body = db.Column(db.Text, nullable=True)  # Devotional content (HTML/MD)
    
    media = db.Column(db.Text, nullable=True)  # JSON array: [{type:"audio", url:"..."}]
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint on plan_id + day_index
    __table_args__ = (db.UniqueConstraint('plan_id', 'day_index', name='uq_plan_day'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'day_index': self.day_index,
            'scripture_ref': self.scripture_ref,
            'scripture_text': self.scripture_text,
            'devo_body': self.devo_body,
            'media': json.loads(self.media) if self.media else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

