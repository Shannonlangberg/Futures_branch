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
        elif isinstance(attendance_date, datetime):
            attendance_date = attendance_date.date()
        
        # Update last_seen to the attendance date (as datetime for consistency)
        attendance_datetime = datetime.combine(attendance_date, datetime.min.time())
        if not self.last_seen or attendance_datetime > self.last_seen:
            self.last_seen = attendance_datetime
        
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
        
        # Update last_seen if we have recent attendance (from service attendance or group attendance)
        latest_activity = None
        
        if recent_attendance:
            latest_attendance = max(
                [datetime.fromisoformat(r['timestamp']) for r in recent_attendance if 'timestamp' in r],
                default=None
            )
            if latest_attendance:
                latest_activity = latest_attendance
        
        # Also check group attendance for last_seen
        group_log = self._load_json(self.group_attendance_log)
        if group_log:
            recent_group_dates = [
                datetime.fromisoformat(r['date']) if isinstance(r.get('date'), str) else datetime.combine(r['date'], datetime.min.time())
                for r in group_log
                if r.get('present', True) and 'date' in r
            ]
            if recent_group_dates:
                latest_group = max(recent_group_dates)
                if not latest_activity or latest_group > latest_activity:
                    latest_activity = latest_group
        
        if latest_activity:
            self.last_seen = latest_activity
        
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
    
    # Relationship to schedules
    schedules = db.relationship('BeaconSchedule', backref='beacon_zone', lazy='dynamic', cascade='all, delete-orphan')
    
    @classmethod
    def find_zone(cls, uuid, major, minor):
        """Find beacon zone by UUID, major, and minor"""
        return cls.query.filter_by(
            beacon_uuid=uuid,
            beacon_major=major,
            beacon_minor=minor,
            is_active=True
        ).first()
    
    def get_active_schedule(self, detection_time=None):
        """
        Get the active schedule for this beacon at the given time.
        Returns the schedule that matches the current day/time, or None.
        """
        if detection_time is None:
            detection_time = datetime.utcnow()
        
        day_name = detection_time.strftime('%A')  # 'Monday', 'Tuesday', etc.
        current_time = detection_time.time()
        
        # Find schedules that match
        matching_schedules = self.schedules.filter_by(is_active=True).all()
        
        for schedule in matching_schedules:
            # Check day of week
            if schedule.day_of_week and schedule.day_of_week != day_name:
                continue
            
            # Check time window
            if schedule.start_time and schedule.end_time:
                if not (schedule.start_time <= current_time <= schedule.end_time):
                    continue
            elif schedule.start_time:
                # Only start time specified - check if we're after it
                if current_time < schedule.start_time:
                    continue
            
            return schedule
        
        return None
    
    def to_dict(self):
        """Convert beacon zone to dictionary"""
        schedules_list = [s.to_dict() for s in self.schedules.filter_by(is_active=True).all()]
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'campus': self.campus,
            'beacon_uuid': self.beacon_uuid,
            'beacon_major': self.beacon_major,
            'beacon_minor': self.beacon_minor,
            'is_active': self.is_active,
            'schedules': schedules_list,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BeaconSchedule(db.Model):
    """Schedule for beacon zones - defines when a beacon logs which event type"""
    __tablename__ = 'beacon_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    beacon_zone_id = db.Column(db.Integer, db.ForeignKey('beacon_zones.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'sunday', 'youth', 'prayer_night', 'kids', etc.
    day_of_week = db.Column(db.String(20))  # 'Sunday', 'Monday', 'Friday', etc. (NULL = any day)
    start_time = db.Column(db.Time)  # e.g., '19:00:00' for 7 PM
    end_time = db.Column(db.Time)  # e.g., '22:00:00' for 10 PM
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert schedule to dictionary"""
        return {
            'id': self.id,
            'beacon_zone_id': self.beacon_zone_id,
            'event_type': self.event_type,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DiscipleshipPathway(db.Model):
    """Discipleship pathway template (e.g., Leadership, Worship Leader, etc.)"""
    __tablename__ = 'discipleship_pathways'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'leadership', 'worship', 'ministry', 'connect_leader', 'general'
    is_active = db.Column(db.Boolean, default=True)
    is_template = db.Column(db.Boolean, default=False)  # Pre-built templates
    created_by_person_id = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    steps = db.relationship('PathwayStep', backref='pathway', lazy='dynamic', order_by='PathwayStep.step_order', cascade='all, delete-orphan')
    person_progress = db.relationship('PersonPathwayProgress', backref='pathway', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert pathway to dictionary"""
        steps_list = [s.to_dict() for s in self.steps.order_by(PathwayStep.step_order).all()]
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active,
            'is_template': self.is_template,
            'created_by_person_id': self.created_by_person_id,
            'steps': steps_list,
            'step_count': len(steps_list),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PathwayStep(db.Model):
    """Individual step/milestone in a pathway"""
    __tablename__ = 'discipleship_pathway_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    pathway_id = db.Column(db.Integer, db.ForeignKey('discipleship_pathways.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)  # Order in pathway (1, 2, 3...)
    step_name = db.Column(db.String(200), nullable=False)
    step_description = db.Column(db.Text)
    milestone_type = db.Column(db.String(50))  # Maps to DiscipleshipStep.type or custom
    is_required = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    completions = db.relationship('PersonPathwayStepCompletion', backref='pathway_step', lazy='dynamic')
    
    def to_dict(self):
        """Convert step to dictionary"""
        return {
            'id': self.id,
            'pathway_id': self.pathway_id,
            'step_order': self.step_order,
            'step_name': self.step_name,
            'step_description': self.step_description,
            'milestone_type': self.milestone_type,
            'is_required': self.is_required,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PersonPathwayProgress(db.Model):
    """Tracks a person's progress through a pathway"""
    __tablename__ = 'person_pathway_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    pathway_id = db.Column(db.Integer, db.ForeignKey('discipleship_pathways.id'), nullable=False)
    assigned_by_person_id = db.Column(db.String(50))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    current_step_id = db.Column(db.Integer, db.ForeignKey('discipleship_pathway_steps.id'))
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='pathway_progress')
    current_step = db.relationship('PathwayStep', foreign_keys=[current_step_id])
    step_completions = db.relationship('PersonPathwayStepCompletion', backref='person_pathway_progress', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_progress_percentage(self):
        """Calculate progress percentage"""
        if not self.pathway:
            return 0
        
        total_steps = self.pathway.steps.count()
        if total_steps == 0:
            return 0
        
        completed_steps = self.step_completions.count()
        return round((completed_steps / total_steps) * 100, 1)
    
    def get_next_step(self):
        """Get the next uncompleted step"""
        if not self.pathway:
            return None
        
        completed_step_ids = [c.pathway_step_id for c in self.step_completions.all()]
        all_steps = self.pathway.steps.order_by(PathwayStep.step_order).all()
        
        for step in all_steps:
            if step.id not in completed_step_ids:
                return step
        
        return None  # All steps completed
    
    def to_dict(self):
        """Convert progress to dictionary"""
        next_step = self.get_next_step()
        completed_step_ids = [c.pathway_step_id for c in self.step_completions.all()]
        
        # Include full pathway with steps
        pathway_dict = None
        if self.pathway:
            pathway_dict = {
                'id': self.pathway.id,
                'name': self.pathway.name,
                'description': self.pathway.description,
                'category': self.pathway.category,
                'steps': [
                    {
                        **step.to_dict(),
                        'is_completed': step.id in completed_step_ids
                    }
                    for step in self.pathway.steps.order_by(PathwayStep.step_order).all()
                ]
            }
        
        return {
            'id': self.id,
            'person_id': self.person_id,
            'pathway_id': self.pathway_id,
            'pathway_name': self.pathway.name if self.pathway else None,
            'pathway': pathway_dict,  # Full pathway with steps
            'assigned_by_person_id': self.assigned_by_person_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_step_id': self.current_step_id,
            'current_step': self.current_step.to_dict() if self.current_step else None,
            'next_step': next_step.to_dict() if next_step else None,
            'is_active': self.is_active,
            'notes': self.notes,
            'progress_percentage': self.get_progress_percentage(),
            'completed_steps': self.step_completions.count(),
            'total_steps': self.pathway.steps.count() if self.pathway else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PersonPathwayStepCompletion(db.Model):
    """Tracks when a person completed a specific pathway step"""
    __tablename__ = 'person_pathway_step_completion'
    
    id = db.Column(db.Integer, primary_key=True)
    person_pathway_progress_id = db.Column(db.Integer, db.ForeignKey('person_pathway_progress.id'), nullable=False)
    pathway_step_id = db.Column(db.Integer, db.ForeignKey('discipleship_pathway_steps.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_by_person_id = db.Column(db.String(50))  # Who marked it complete
    notes = db.Column(db.Text)
    
    def to_dict(self):
        """Convert completion to dictionary"""
        return {
            'id': self.id,
            'person_pathway_progress_id': self.person_pathway_progress_id,
            'pathway_step_id': self.pathway_step_id,
            'step_name': self.pathway_step.step_name if self.pathway_step else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by_person_id': self.completed_by_person_id,
            'notes': self.notes
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
        # Parse links from JSON string, handle errors gracefully
        links = []
        if self.links:
            try:
                parsed_links = json.loads(self.links)
                if isinstance(parsed_links, list):
                    links = parsed_links
            except (json.JSONDecodeError, TypeError) as e:
                # If links can't be parsed, return empty list
                links = []
        
        return {
            'id': self.slug or str(self.id),
            'displayName': self.display_name,
            'slug': self.slug,
            'description': self.description or '',
            'folderId': self.folder_id or '',
            'sortOrder': self.sort_order or 0,
            'links': links,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# HEARTBEAT MODULE MODELS
# ============================================================================

class Campus(db.Model):
    """Campus model for Heartbeat module"""
    __tablename__ = 'heartbeat_campuses'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    timezone = db.Column(db.String(50), default='UTC')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Service(db.Model):
    """Service model for tracking church services"""
    __tablename__ = 'heartbeat_services'
    
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.String(50), db.ForeignKey('heartbeat_campuses.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'sunday', 'youth', 'kids', 'prayer_night', etc.
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    campus = db.relationship('Campus', backref='services')
    
    def to_dict(self):
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'type': self.type,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'ends_at': self.ends_at.isoformat() if self.ends_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AttendanceEvent(db.Model):
    """Attendance event tracking"""
    __tablename__ = 'heartbeat_attendance_events'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('heartbeat_services.id'), nullable=False)
    source = db.Column(db.String(50), nullable=False)  # 'beacon', 'manual', 'checkin', 'import'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    person = db.relationship('Person', backref='attendance_events')
    service = db.relationship('Service', backref='attendance_events')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'service_id': self.service_id,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class HeartbeatConnectGroup(db.Model):
    """Connect Group model for Heartbeat (extends existing ConnectGroup concept)"""
    __tablename__ = 'heartbeat_connect_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.String(50), db.ForeignKey('heartbeat_campuses.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    leader_person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'home', 'youth', 'interest'
    day_of_week = db.Column(db.String(20))  # 'Monday', 'Tuesday', etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    campus = db.relationship('Campus', backref='connect_groups')
    leader = db.relationship('Person', foreign_keys=[leader_person_id], backref='led_heartbeat_groups')
    
    def to_dict(self):
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'name': self.name,
            'leader_person_id': self.leader_person_id,
            'type': self.type,
            'day_of_week': self.day_of_week,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ConnectAttendance(db.Model):
    """Connect group attendance records"""
    __tablename__ = 'heartbeat_connect_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    connect_group_id = db.Column(db.Integer, db.ForeignKey('heartbeat_connect_groups.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'apology'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    person = db.relationship('Person', backref='connect_attendance')
    connect_group = db.relationship('HeartbeatConnectGroup', backref='attendance_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'connect_group_id': self.connect_group_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Team(db.Model):
    """Serving team model"""
    __tablename__ = 'heartbeat_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.String(50), db.ForeignKey('heartbeat_campuses.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    campus = db.relationship('Campus', backref='teams')
    
    def to_dict(self):
        return {
            'id': self.id,
            'campus_id': self.campus_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ServingAssignment(db.Model):
    """Serving assignment tracking"""
    __tablename__ = 'heartbeat_serving_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('heartbeat_teams.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('heartbeat_services.id'), nullable=False)
    role = db.Column(db.String(200))
    status = db.Column(db.String(20), nullable=False)  # 'scheduled', 'served', 'no_show'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    person = db.relationship('Person', backref='serving_assignments')
    team = db.relationship('Team', backref='assignments')
    service = db.relationship('Service', backref='serving_assignments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'team_id': self.team_id,
            'service_id': self.service_id,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class GivingSummary(db.Model):
    """Giving summary for a person over a period"""
    __tablename__ = 'heartbeat_giving_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # 'none', 'occasional', 'monthly', 'weekly'
    pattern_score = db.Column(db.Float, default=0.0)  # 0-1.0
    last_gift_at = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    person = db.relationship('Person', backref='giving_summaries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'frequency': self.frequency,
            'pattern_score': self.pattern_score,
            'last_gift_at': self.last_gift_at.isoformat() if self.last_gift_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DiscipleshipStep(db.Model):
    """Discipleship milestone tracking"""
    __tablename__ = 'heartbeat_discipleship_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'salvation', 'baptism', 'holy_spirit', 'next_steps', etc.
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_by_person_id = db.Column(db.String(50), db.ForeignKey('persons.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    person = db.relationship('Person', foreign_keys=[person_id], backref='discipleship_steps')
    created_by = db.relationship('Person', foreign_keys=[created_by_person_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'type': self.type,
            'description': self.description,
            'date': self.date.isoformat() if self.date else None,
            'created_by_person_id': self.created_by_person_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CareCase(db.Model):
    """Pastoral care case tracking"""
    __tablename__ = 'heartbeat_care_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'bereavement', 'marriage', 'mental_health', etc.
    status = db.Column(db.String(20), nullable=False)  # 'open', 'in_progress', 'closed'
    priority = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high'
    summary = db.Column(db.String(500))
    details = db.Column(db.Text)
    created_by_person_id = db.Column(db.String(50), db.ForeignKey('persons.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    person = db.relationship('Person', foreign_keys=[person_id], backref='care_cases')
    created_by = db.relationship('Person', foreign_keys=[created_by_person_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'summary': self.summary,
            'details': self.details,
            'created_by_person_id': self.created_by_person_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CareTouchpoint(db.Model):
    """Care touchpoint tracking"""
    __tablename__ = 'heartbeat_care_touchpoints'
    
    id = db.Column(db.Integer, primary_key=True)
    care_case_id = db.Column(db.Integer, db.ForeignKey('heartbeat_care_cases.id'), nullable=False)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    contacted_by_person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    method = db.Column(db.String(50), nullable=False)  # 'phone', 'in_person', 'message', 'email', 'visit', 'prayer'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    care_case = db.relationship('CareCase', backref='touchpoints')
    person = db.relationship('Person', foreign_keys=[person_id], backref='care_touchpoints')
    contacted_by = db.relationship('Person', foreign_keys=[contacted_by_person_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'care_case_id': self.care_case_id,
            'person_id': self.person_id,
            'contacted_by_person_id': self.contacted_by_person_id,
            'method': self.method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class HeartbeatSnapshot(db.Model):
    """Heartbeat health snapshot for a person"""
    __tablename__ = 'heartbeat_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    campus_id = db.Column(db.String(50), db.ForeignKey('heartbeat_campuses.id'), nullable=False)
    calculated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    gather_score = db.Column(db.Float, nullable=False)  # 0-100
    engagement_score = db.Column(db.Float, nullable=False)  # 0-100
    spiritual_score = db.Column(db.Float, nullable=False)  # 0-100
    care_score = db.Column(db.Float, nullable=False)  # 0-100
    total_score = db.Column(db.Float, nullable=False)  # 0-100
    status = db.Column(db.String(20), nullable=False)  # 'healthy', 'watch', 'at_risk', 'critical'
    risk_reasons = db.Column(db.Text)  # JSON array of strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    person = db.relationship('Person', backref='heartbeat_snapshots')
    campus = db.relationship('Campus', backref='snapshots')
    
    def to_dict(self):
        risk_reasons_list = []
        if self.risk_reasons:
            try:
                risk_reasons_list = json.loads(self.risk_reasons)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            'id': self.id,
            'person_id': self.person_id,
            'campus_id': self.campus_id,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
            'gather_score': self.gather_score,
            'engagement_score': self.engagement_score,
            'spiritual_score': self.spiritual_score,
            'care_score': self.care_score,
            'total_score': self.total_score,
            'status': self.status,
            'risk_reasons': risk_reasons_list,
            'created_at': self.created_at.isoformat() if self.created_at else None
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

