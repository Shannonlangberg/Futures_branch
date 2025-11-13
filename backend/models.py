# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

class Person(db.Model):
    """Person model for church members"""
    __tablename__ = 'persons'
    
    id = db.Column(db.String(50), primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    preferred_name = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    campus = db.Column(db.String(100), nullable=False)
    connect_group = db.Column(db.String(200))
    dream_team_roles = db.Column(db.Text)  # JSON array stored as text
    birthday = db.Column(db.Date)
    pastoral_notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON array stored as text
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Discipleship milestones
    dna_completed = db.Column(db.Date)
    baptised_on = db.Column(db.Date)
    filled_holy_spirit = db.Column(db.Date)
    rise_attended = db.Column(db.Date)
    first_served_on = db.Column(db.Date)
    
    # Relationship to engagement profile
    engagement_profile = db.relationship('EngagementProfile', backref='person', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert person to dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'preferred_name': self.preferred_name,
            'email': self.email,
            'phone': self.phone,
            'campus': self.campus,
            'connect_group': self.connect_group,
            'dream_team_roles': json.loads(self.dream_team_roles) if self.dream_team_roles else [],
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'pastoral_notes': self.pastoral_notes,
            'tags': json.loads(self.tags) if self.tags else [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'dna_completed': self.dna_completed.isoformat() if self.dna_completed else None,
            'baptised_on': self.baptised_on.isoformat() if self.baptised_on else None,
            'filled_holy_spirit': self.filled_holy_spirit.isoformat() if self.filled_holy_spirit else None,
            'rise_attended': self.rise_attended.isoformat() if self.rise_attended else None,
            'first_served_on': self.first_served_on.isoformat() if self.first_served_on else None,
        }


class EngagementProfile(db.Model):
    """Engagement profile tracking for persons"""
    __tablename__ = 'engagement_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False, unique=True)
    pulse_status = db.Column(db.String(20), default='green')  # green, amber, red
    last_seen = db.Column(db.DateTime)
    attendance_log = db.Column(db.Text)  # JSON array stored as text
    interaction_log = db.Column(db.Text)  # JSON array stored as text
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def add_attendance(self, zones, campus, attendance_time=None):
        """Add attendance record"""
        if attendance_time is None:
            attendance_time = datetime.utcnow()
        
        attendance_log = json.loads(self.attendance_log) if self.attendance_log else []
        
        attendance_record = {
            'timestamp': attendance_time.isoformat(),
            'zones': zones,
            'campus': campus
        }
        
        attendance_log.append(attendance_record)
        self.attendance_log = json.dumps(attendance_log)
        self.last_seen = attendance_time
        self.update_pulse_status()
    
    def update_pulse_status(self):
        """Update pulse status based on attendance"""
        if not self.last_seen:
            self.pulse_status = 'red'
            return
        
        days_since_last_seen = (datetime.utcnow() - self.last_seen).days
        
        if days_since_last_seen <= 14:
            self.pulse_status = 'green'
        elif days_since_last_seen <= 28:
            self.pulse_status = 'amber'
        else:
            self.pulse_status = 'red'
    
    def get_pulse_reasons(self):
        """Get reasons for current pulse status"""
        reasons = []
        
        if not self.last_seen:
            reasons.append("No attendance recorded")
            return reasons
        
        days_since_last_seen = (datetime.utcnow() - self.last_seen).days
        
        if self.pulse_status == 'green':
            reasons.append(f"Attended {days_since_last_seen} days ago")
        elif self.pulse_status == 'amber':
            reasons.append(f"Last seen {days_since_last_seen} days ago (2-4 weeks)")
        else:
            reasons.append(f"Last seen {days_since_last_seen} days ago (>4 weeks)")
        
        return reasons
    
    def to_dict(self):
        """Convert engagement profile to dictionary"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'pulse_status': self.pulse_status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'attendance_log': json.loads(self.attendance_log) if self.attendance_log else [],
            'interaction_log': json.loads(self.interaction_log) if self.interaction_log else [],
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'pulse_reasons': self.get_pulse_reasons()
        }


class BeaconZone(db.Model):
    """Beacon zone model for attendance tracking"""
    __tablename__ = 'beacon_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(200), nullable=False)
    campus = db.Column(db.String(100), nullable=False)
    beacon_uuid = db.Column(db.String(100), nullable=False)
    beacon_major = db.Column(db.Integer, nullable=False)
    beacon_minor = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def find_zone(cls, uuid, major, minor):
        """Find beacon zone by UUID, major, and minor"""
        return cls.query.filter_by(
            beacon_uuid=uuid,
            beacon_major=major,
            beacon_minor=minor,
            is_active=True
        ).first()
    
    def to_dict(self):
        """Convert beacon zone to dictionary"""
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'campus': self.campus,
            'beacon_uuid': self.beacon_uuid,
            'beacon_major': self.beacon_major,
            'beacon_minor': self.beacon_minor,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EventCategory(db.Model):
    """Event category model"""
    __tablename__ = 'event_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert event category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Event(db.Model):
    """Event model"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    campus = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('event_categories.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to category
    category = db.relationship('EventCategory', backref='events')
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'campus': self.campus,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ResourceCategory(db.Model):
    """Configurable resource category surfaced in the Resources hub"""
    __tablename__ = 'resource_categories'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    folder_id = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    links = db.relationship(
        'ResourceLink',
        backref='category',
        cascade='all, delete-orphan',
        order_by='ResourceLink.sort_order'
    )

    def to_dict(self, include_links: bool = False):
        data = {
            'id': self.id,
            'slug': self.slug,
            'display_name': self.display_name,
            'description': self.description or '',
            'folder_id': self.folder_id or '',
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_links:
            data['links'] = [link.to_dict() for link in self.links]
        return data


class ResourceLink(db.Model):
    """Manual quick links surfaced within a resource category"""
    __tablename__ = 'resource_links'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('resource_categories.id', ondelete='CASCADE'), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'label': self.label,
            'url': self.url,
            'description': self.description or '',
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class GoogleOAuthToken(db.Model):
    """Store Google OAuth tokens per user"""
    __tablename__ = 'google_oauth_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default='google_drive')
    token_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'provider', name='uq_google_tokens_user_provider'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("[DEBUG] Database tables created successfully")


def create_person_with_engagement(
    full_name,
    email,
    campus,
    preferred_name=None,
    phone=None,
    connect_group=None,
    dream_team_roles=None,
    birthday=None,
    pastoral_notes=None,
    tags=None
):
    """Create a person with an engagement profile"""
    import uuid
    
    # Generate unique ID
    person_id = str(uuid.uuid4())
    
    # Create person
    person = Person(
        id=person_id,
        full_name=full_name,
        email=email,
        campus=campus,
        preferred_name=preferred_name,
        phone=phone,
        connect_group=connect_group,
        dream_team_roles=json.dumps(dream_team_roles) if dream_team_roles else None,
        birthday=birthday,
        pastoral_notes=pastoral_notes,
        tags=json.dumps(tags) if tags else None
    )
    
    # Create engagement profile
    engagement = EngagementProfile(person_id=person_id)
    
    # Add to session
    db.session.add(person)
    db.session.add(engagement)
    
    return person, engagement

