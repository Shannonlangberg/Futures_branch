#!/usr/bin/env python3
"""
Communication Platform Database Models
LINK Reach System - Email & SMS Campaign Management
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum

# Import existing db instance
from models import db

class CampaignType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class CampaignStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EngagementType(Enum):
    OPEN = "open"
    CLICK = "click"
    REPLY = "reply"
    BOUNCE = "bounce"
    UNSUBSCRIBE = "unsubscribe"
    SMS_DELIVERED = "sms_delivered"
    SMS_READ = "sms_read"
    SMS_REPLY = "sms_reply"

class Campaign(db.Model):
    """
    Campaign management for email and SMS communications
    """
    __tablename__ = 'campaigns'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Campaign type and status
    campaign_type = db.Column(db.Enum(CampaignType), nullable=False)
    status = db.Column(db.Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    
    # Content
    subject_line = db.Column(db.String(200), nullable=True)  # Email subject
    content = db.Column(db.Text, nullable=False)  # Email HTML or SMS text
    content_text = db.Column(db.Text, nullable=True)  # Plain text version for email
    
    # Targeting and scheduling
    target_criteria = db.Column(db.JSON, nullable=False, default=dict)
    # Format: {"campus": ["Paradise", "Sunshine Coast"], "department": ["Adults"], "tags": ["New", "Leader"]}
    
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Campaign metrics
    total_recipients = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    delivered_count = db.Column(db.Integer, default=0)
    open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    bounce_count = db.Column(db.Integer, default=0)
    unsubscribe_count = db.Column(db.Integer, default=0)
    
    # System fields
    created_by = db.Column(db.String(36), nullable=False)  # User ID
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recipients = db.relationship('CampaignRecipient', backref='campaign', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Campaign {self.name} ({self.campaign_type.value})>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'campaign_type': self.campaign_type.value,
            'status': self.status.value,
            'subject_line': self.subject_line,
            'content': self.content,
            'content_text': self.content_text,
            'target_criteria': self.target_criteria,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.scheduled_at.isoformat() if self.sent_at else None,
            'total_recipients': self.total_recipients,
            'sent_count': self.sent_count,
            'delivered_count': self.delivered_count,
            'open_count': self.open_count,
            'click_count': self.click_count,
            'reply_count': self.reply_count,
            'bounce_count': self.bounce_count,
            'unsubscribe_count': self.unsubscribe_count,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CampaignTemplate(db.Model):
    """
    Reusable email and SMS templates
    """
    __tablename__ = 'campaign_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Template type and content
    template_type = db.Column(db.Enum(CampaignType), nullable=False)
    subject_line = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    content_text = db.Column(db.Text, nullable=True)
    
    # Template variables
    variables = db.Column(db.JSON, nullable=False, default=list)
    # Format: ["{{name}}", "{{campus}}", "{{event_title}}"]
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # System fields
    created_by = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CampaignTemplate {self.name} ({self.template_type.value})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type.value,
            'subject_line': self.subject_line,
            'content': self.content,
            'content_text': self.content_text,
            'variables': self.variables,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CampaignRecipient(db.Model):
    """
    Individual recipients for campaigns with engagement tracking
    """
    __tablename__ = 'campaign_recipients'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False)
    
    # Contact information
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Delivery status
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)
    
    # Engagement tracking
    opened_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    
    # External service IDs
    sendgrid_message_id = db.Column(db.String(100), nullable=True)
    twilio_message_sid = db.Column(db.String(100), nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='campaign_recipients')
    
    def __repr__(self):
        return f'<CampaignRecipient {self.email or self.phone} for Campaign {self.campaign_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'person_id': self.person_id,
            'email': self.email,
            'phone': self.phone,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'failure_reason': self.failure_reason,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'unsubscribed_at': self.unsubscribed_at.isoformat() if self.unsubscribed_at else None,
            'sendgrid_message_id': self.sendgrid_message_id,
            'twilio_message_sid': self.twilio_message_sid,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class EngagementEvent(db.Model):
    """
    Detailed tracking of all engagement events for scoring
    """
    __tablename__ = 'engagement_events'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    recipient_id = db.Column(db.String(36), db.ForeignKey('campaign_recipients.id'), nullable=False)
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False)
    
    # Event details
    event_type = db.Column(db.Enum(EngagementType), nullable=False)
    event_data = db.Column(db.JSON, nullable=True)  # Additional event data
    
    # Scoring
    points_earned = db.Column(db.Integer, nullable=False, default=0)
    
    # External service data
    external_id = db.Column(db.String(100), nullable=True)  # SendGrid/Twilio event ID
    external_timestamp = db.Column(db.DateTime, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('Campaign', backref='engagement_events')
    recipient = db.relationship('CampaignRecipient', backref='engagement_events')
    person = db.relationship('Person', backref='engagement_events')
    
    def __repr__(self):
        return f'<EngagementEvent {self.event_type.value} for {self.person_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'recipient_id': self.recipient_id,
            'person_id': self.person_id,
            'event_type': self.event_type.value,
            'event_data': self.event_data,
            'points_earned': self.points_earned,
            'external_id': self.external_id,
            'external_timestamp': self.external_timestamp.isoformat() if self.external_timestamp else None,
            'created_at': self.created_at.isoformat()
        }

class CommunicationPreferences(db.Model):
    """
    User preferences for communication channels and frequency
    """
    __tablename__ = 'communication_preferences'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False, unique=True)
    
    # Channel preferences
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=False)
    
    # Frequency preferences
    max_emails_per_week = db.Column(db.Integer, default=3)
    max_sms_per_week = db.Column(db.Integer, default=2)
    
    # Category preferences
    preferred_categories = db.Column(db.JSON, default=list)
    # Format: ["Events", "Devotionals", "Giving", "General"]
    
    # Opt-out tracking
    unsubscribed_categories = db.Column(db.JSON, default=list)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='communication_preferences', uselist=False)
    
    def __repr__(self):
        return f'<CommunicationPreferences for {self.person_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'max_emails_per_week': self.max_emails_per_week,
            'max_sms_per_week': self.max_sms_per_week,
            'preferred_categories': self.preferred_categories,
            'unsubscribed_categories': self.unsubscribed_categories,
            'unsubscribed_at': self.unsubscribed_at.isoformat() if self.unsubscribed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class EmailList(db.Model):
    """
    Custom email lists for targeted campaigns (e.g., "Business People", "New People")
    """
    __tablename__ = 'email_lists'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # List type: 'custom' (manually created), 'csv' (imported from CSV), 'filtered' (based on criteria)
    list_type = db.Column(db.String(50), nullable=False, default='custom')
    
    # For filtered lists, store the criteria
    filter_criteria = db.Column(db.JSON, nullable=True)
    # Format: {"campus": ["Paradise"], "department": ["Adults"], "tags": ["Business"]}
    
    # List members (stored as JSON array of person IDs or email addresses)
    members = db.Column(db.JSON, nullable=False, default=list)
    # Format: [{"email": "user@example.com", "name": "John Doe", "person_id": "123"}, ...]
    
    # Metadata
    member_count = db.Column(db.Integer, default=0)
    created_by = db.Column(db.String(36), nullable=False)  # User ID
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailList {self.name} ({self.member_count} members)>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'list_type': self.list_type,
            'filter_criteria': self.filter_criteria,
            'members': self.members,
            'member_count': self.member_count,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_member_count(self):
        """Update member count from members array"""
        self.member_count = len(self.members) if self.members else 0
