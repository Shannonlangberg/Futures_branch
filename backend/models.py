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
    department = db.Column(db.String(50))  # Kids, Youth, Young Adults, Families, Adults, Seniors
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
            'department': self.department,
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
    
    # Summary pulse
    pulse_status = db.Column(db.String(20), default='green')  # green, amber, red
    last_seen = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Raw logs (JSON text – we can normalize later)
    attendance_log = db.Column(db.Text)          # [{timestamp, campus, zones}]
    interaction_log = db.Column(db.Text)         # reserved for notes etc.
    bible_log = db.Column(db.Text)               # [{date}]
    giving_log = db.Column(db.Text)              # [{date, amount, campus}]
    serving_log = db.Column(db.Text)             # [{date, role, campus, location}]
    group_attendance_log = db.Column(db.Text)    # [{group_id, date, present}]
    
    # Derived metrics (simple v1)
    attendance_frequency = db.Column(db.Float, default=0.0)
    serving_frequency = db.Column(db.Float, default=0.0)
    overall_engagement = db.Column(db.Float, default=0.0)
    
    def _load_json(self, value):
        """Helper to load JSON from text field"""
        return json.loads(value) if value else []
    
    def _dump_json(self, value):
        """Helper to dump JSON to text field"""
        return json.dumps(value or [])
    
    def add_attendance(self, zones, campus, attendance_time=None):
        """Add attendance record and recalculate heartbeat"""
        if attendance_time is None:
            attendance_time = datetime.utcnow()
        
        attendance_log = self._load_json(self.attendance_log)
        attendance_log.append({
            'timestamp': attendance_time.isoformat(),
            'zones': zones,
            'campus': campus
        })
        self.attendance_log = self._dump_json(attendance_log)
        self.last_seen = attendance_time
        self.recalculate_heartbeat()
    
    def add_bible_reading(self, reading_date=None):
        """Add Bible reading record"""
        if reading_date is None:
            reading_date = datetime.utcnow().date()
        elif isinstance(reading_date, str):
            reading_date = datetime.fromisoformat(reading_date).date()
        
        bible_log = self._load_json(self.bible_log)
        bible_log.append({
            'date': reading_date.isoformat()
        })
        self.bible_log = self._dump_json(bible_log)
        self.recalculate_heartbeat()
    
    def add_giving(self, amount, giving_date=None, campus=None):
        """Add giving record"""
        if giving_date is None:
            giving_date = datetime.utcnow().date()
        elif isinstance(giving_date, str):
            giving_date = datetime.fromisoformat(giving_date).date()
        
        giving_log = self._load_json(self.giving_log)
        giving_log.append({
            'date': giving_date.isoformat(),
            'amount': float(amount),
            'campus': campus
        })
        self.giving_log = self._dump_json(giving_log)
        self.recalculate_heartbeat()
    
    def add_serving_record(self, role, campus, serving_date=None, location=None):
        """Add serving activity record"""
        if serving_date is None:
            serving_date = datetime.utcnow().date()
        elif isinstance(serving_date, str):
            serving_date = datetime.fromisoformat(serving_date).date()
        
        serving_log = self._load_json(self.serving_log)
        serving_log.append({
            'date': serving_date.isoformat(),
            'role': role,
            'campus': campus,
            'location': location
        })
        self.serving_log = self._dump_json(serving_log)
        self.recalculate_heartbeat()
    
    def add_group_attendance(self, group_id, attendance_date=None, present=True):
        """Add connect group attendance record"""
        if attendance_date is None:
            attendance_date = datetime.utcnow().date()
        elif isinstance(attendance_date, str):
            attendance_date = datetime.fromisoformat(attendance_date).date()
        
        group_log = self._load_json(self.group_attendance_log)
        group_log.append({
            'group_id': group_id,
            'date': attendance_date.isoformat(),
            'present': present
        })
        self.group_attendance_log = self._dump_json(group_log)
        self.recalculate_heartbeat()
    
    def recalculate_heartbeat(self):
        """
        Recalculate heartbeat metrics and pulse_status.
        Enhanced version with all 5 engagement factors and weighted scoring.
        """
        now = datetime.utcnow()
        eight_weeks_ago = now - timedelta(days=56)
        
        # 1. ATTENDANCE (30% weight)
        attendance_log = self._load_json(self.attendance_log)
        recent_attendance = [
            r for r in attendance_log
            if 'timestamp' in r and (now - datetime.fromisoformat(r['timestamp'])).days <= 56
        ]
        services_last_8_weeks = len(recent_attendance)
        max_services = 8
        attendance_freq = min(services_last_8_weeks / max_services, 1.0) if max_services > 0 else 0.0
        attendance_score = attendance_freq * 100.0
        self.attendance_frequency = attendance_freq
        
        # Update last_seen if we have recent attendance
        if recent_attendance:
            latest_attendance = max(
                [datetime.fromisoformat(r['timestamp']) for r in recent_attendance if 'timestamp' in r],
                default=None
            )
            if latest_attendance:
                self.last_seen = latest_attendance
        
        days_since_last_seen = (now - self.last_seen).days if self.last_seen else None
        
        # 2. BIBLE READING (25% weight)
        # Target: Daily reading = 56 days in 8 weeks
        bible_log = self._load_json(self.bible_log)
        recent_bible = [
            r for r in bible_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        bible_freq = min(len(recent_bible) / 56, 1.0)  # Daily target
        bible_score = bible_freq * 100.0
        
        # 3. GIVING (15% weight)
        # Target: Weekly giving = 8 times in 8 weeks
        giving_log = self._load_json(self.giving_log)
        recent_giving = [
            r for r in giving_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        giving_freq = min(len(recent_giving) / 8, 1.0)  # Weekly target
        giving_score = giving_freq * 100.0
        
        # 4. SERVING (15% weight)
        # Target: Weekly serving = 8 times in 8 weeks
        serving_log = self._load_json(self.serving_log)
        recent_serving = [
            r for r in serving_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        serving_freq = min(len(recent_serving) / 8, 1.0)  # Weekly target
        serving_score = serving_freq * 100.0
        self.serving_frequency = serving_freq
        
        # 5. CONNECT GROUPS (15% weight)
        # Target: Weekly attendance = 8 meetings in 8 weeks
        group_log = self._load_json(self.group_attendance_log)
        recent_groups = [
            r for r in group_log
            if 'date' in r and r.get('present', True) and 
            datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        group_freq = min(len(recent_groups) / 8, 1.0)  # Weekly target
        group_score = group_freq * 100.0
        
        # Weighted overall engagement score
        weights = {
            'attendance': 0.30,  # 30%
            'bible': 0.25,      # 25%
            'giving': 0.15,     # 15%
            'serving': 0.15,    # 15%
            'groups': 0.15       # 15%
        }
        
        self.overall_engagement = (
            attendance_score * weights['attendance'] +
            bible_score * weights['bible'] +
            giving_score * weights['giving'] +
            serving_score * weights['serving'] +
            group_score * weights['groups']
        )
        
        # Pulse status determination
        # Consider both overall engagement and recency
        if not self.last_seen:
            self.pulse_status = 'red'
        elif days_since_last_seen <= 14:
            # Recent activity - check engagement level
            if self.overall_engagement >= 70:
                self.pulse_status = 'green'
            elif self.overall_engagement >= 40:
                self.pulse_status = 'amber'
            else:
                self.pulse_status = 'red'
        elif days_since_last_seen <= 28:
            # 2-4 weeks - amber unless very high engagement
            if self.overall_engagement >= 80:
                self.pulse_status = 'green'
            else:
                self.pulse_status = 'amber'
        else:
            # >4 weeks - red unless exceptional engagement
            if self.overall_engagement >= 90:
                self.pulse_status = 'amber'
            else:
                self.pulse_status = 'red'
    
    def get_pulse_reasons(self):
        """Explain current pulse status in human language"""
        reasons = []
        
        now = datetime.utcnow()
        eight_weeks_ago = now - timedelta(days=56)
        
        if not self.last_seen:
            reasons.append("No attendance recorded")
        else:
            days_since_last_seen = (now - self.last_seen).days
            if days_since_last_seen <= 14:
                reasons.append(f"Attended {days_since_last_seen} days ago")
            elif days_since_last_seen <= 28:
                reasons.append(f"Last seen {days_since_last_seen} days ago (2–4 weeks)")
            else:
                reasons.append(f"Last seen {days_since_last_seen} days ago (>4 weeks)")
        
        # Engagement breakdown
        attendance_log = self._load_json(self.attendance_log)
        recent_attendance = [
            r for r in attendance_log
            if 'timestamp' in r and (now - datetime.fromisoformat(r['timestamp'])).days <= 56
        ]
        services_last_8_weeks = len(recent_attendance)
        reasons.append(f"Services: {services_last_8_weeks}/8 in last 8 weeks")
        
        bible_log = self._load_json(self.bible_log)
        recent_bible = [
            r for r in bible_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Bible reading: {len(recent_bible)} days in last 8 weeks")
        
        giving_log = self._load_json(self.giving_log)
        recent_giving = [
            r for r in giving_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Giving: {len(recent_giving)} times in last 8 weeks")
        
        serving_log = self._load_json(self.serving_log)
        recent_serving = [
            r for r in serving_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Serving: {len(recent_serving)} times in last 8 weeks")
        
        group_log = self._load_json(self.group_attendance_log)
        recent_groups = [
            r for r in group_log
            if 'date' in r and r.get('present', True) and 
            datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Connect groups: {len(recent_groups)} meetings in last 8 weeks")
        
        reasons.append(f"Overall engagement score: {int(self.overall_engagement)}/100")
        
        return reasons
    
    def to_dict(self):
        """Convert engagement profile to dictionary"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'pulse_status': self.pulse_status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'attendance_log': self._load_json(self.attendance_log),
            'interaction_log': self._load_json(self.interaction_log),
            'bible_log': self._load_json(self.bible_log),
            'giving_log': self._load_json(self.giving_log),
            'serving_log': self._load_json(self.serving_log),
            'group_attendance_log': self._load_json(self.group_attendance_log),
            'attendance_frequency': self.attendance_frequency,
            'serving_frequency': self.serving_frequency,
            'overall_engagement': self.overall_engagement,
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


class ConnectGroup(db.Model):
    """Connect Group model"""
    __tablename__ = 'connect_groups'
    
    id = db.Column(db.String(50), primary_key=True)  # e.g., "cg_copper_coast_1"
    name = db.Column(db.String(200), nullable=False)  # e.g., "Copper Coast Young Adults"
    campus = db.Column(db.String(100), nullable=False)
    leader_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    co_leader_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=True)
    
    # Meeting schedule
    meeting_day = db.Column(db.String(20))  # "Monday", "Tuesday", etc.
    meeting_time = db.Column(db.String(20))  # "7:00 PM"
    meeting_frequency = db.Column(db.String(20), default='weekly')  # weekly, bi-weekly, monthly
    location = db.Column(db.String(200))  # Address or location name
    
    # Leader access (simple password for leader portal)
    leader_access_code = db.Column(db.String(50))  # Simple password for leader login
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leader = db.relationship('Person', foreign_keys=[leader_id], backref='led_groups')
    co_leader = db.relationship('Person', foreign_keys=[co_leader_id], backref='co_led_groups')
    
    def get_members(self):
        """Get all active members of this group"""
        return Person.query.filter_by(connect_group=self.id, is_active=True).all()
    
    def get_member_count(self):
        """Get count of active members"""
        return Person.query.filter_by(connect_group=self.id, is_active=True).count()
    
    def to_dict(self):
        """Convert connect group to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'campus': self.campus,
            'leader_id': self.leader_id,
            'leader_name': self.leader.full_name if self.leader else None,
            'leader_email': self.leader.email if self.leader else None,
            'co_leader_id': self.co_leader_id,
            'co_leader_name': self.co_leader.full_name if self.co_leader else None,
            'meeting_day': self.meeting_day,
            'meeting_time': self.meeting_time,
            'meeting_frequency': self.meeting_frequency,
            'location': self.location,
            'member_count': self.get_member_count(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ConnectGroupMeeting(db.Model):
    """Individual connect group meeting attendance records"""
    __tablename__ = 'connect_group_meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(50), db.ForeignKey('connect_groups.id'), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    group = db.relationship('ConnectGroup', backref='meetings')
    attendance = db.relationship('ConnectGroupAttendance', backref='meeting', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert meeting to dictionary"""
        present_count = len([a for a in self.attendance if a.present])
        return {
            'id': self.id,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'meeting_date': self.meeting_date.isoformat(),
            'notes': self.notes,
            'attendance_count': present_count,
            'total_members': len(self.attendance),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ConnectGroupAttendance(db.Model):
    """Individual attendance record for a meeting"""
    __tablename__ = 'connect_group_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('connect_group_meetings.id'), nullable=False)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    present = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    # Relationships
    person = db.relationship('Person', backref='cg_attendance_records')
    
    def to_dict(self):
        """Convert attendance record to dictionary"""
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'present': self.present,
            'notes': self.notes
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
    """Resource category model for organizing resources"""
    __tablename__ = 'resource_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    folder_id = db.Column(db.String(200))  # Google Drive folder ID
    sort_order = db.Column(db.Integer, default=0)
    links = db.Column(db.Text)  # JSON array of links
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'id': self.slug or str(self.id),
            'displayName': self.display_name,
            'slug': self.slug,
            'description': self.description or '',
            'folderId': self.folder_id or '',
            'sortOrder': self.sort_order or 0,
            'links': json.loads(self.links) if self.links else [],
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            print("[DEBUG] Database tables created successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization error: {e}")
        # Don't raise - allow app to start even if table creation fails
        import traceback
        traceback.print_exc()


def create_person_with_engagement(
    full_name,
    email,
    campus,
    preferred_name=None,
    phone=None,
    department=None,
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
        department=department,
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

