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
    email = db.Column(db.String(200), nullable=True)
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
        try:
            dream_team_roles = json.loads(self.dream_team_roles) if self.dream_team_roles else []
        except (TypeError, ValueError, json.JSONDecodeError):
            dream_team_roles = []
        
        try:
            tags = json.loads(self.tags) if self.tags else []
        except (TypeError, ValueError, json.JSONDecodeError):
            tags = []
        
        return {
            'id': self.id,
            'full_name': self.full_name,
            'preferred_name': self.preferred_name,
            'email': self.email,
            'phone': self.phone,
            'campus': self.campus,
            'department': self.department,
            'connect_group': self.connect_group,
            'dream_team_roles': dream_team_roles,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'pastoral_notes': self.pastoral_notes,
            'tags': tags,
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
    
    # Note: Database uses person_id as PRIMARY KEY (no separate id column)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), primary_key=True, nullable=False)
    
    @property
    def id(self):
        """Alias for person_id to maintain compatibility with code that expects .id"""
        return self.person_id
    
    # Summary pulse
    pulse_status = db.Column(db.String(20), default='green')  # green, amber, red
    last_seen = db.Column(db.Date)  # Note: DB uses DATE not DATETIME
    pulse_last_calculated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Raw logs (JSON columns as per actual DB schema)
    attendance_log = db.Column(db.Text, nullable=False, default='[]')  # JSON array
    serving_log = db.Column(db.Text, nullable=False, default='[]')     # JSON array
    milestones_log = db.Column(db.Text, default='[]')                  # JSON array
    email_engagement = db.Column(db.Text, default='[]')                # JSON array
    social_engagement = db.Column(db.Text, default='[]')               # JSON array
    
    # Note: These columns don't exist in actual DB schema - handle gracefully via properties
    # The actual DB has: attendance_log, serving_log, milestones_log, email_engagement, social_engagement
    
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
        """Add Bible reading record to milestones_log"""
        if reading_date is None:
            reading_date = datetime.utcnow().date()
        elif isinstance(reading_date, str):
            reading_date = datetime.fromisoformat(reading_date).date()
        
        milestones_log = self._load_json(self.milestones_log or '[]')
        milestones_log.append({
            'type': 'bible_reading',
            'date': reading_date.isoformat()
        })
        self.milestones_log = self._dump_json(milestones_log)
        self.recalculate_heartbeat()
    
    def add_giving(self, amount, giving_date=None, campus=None):
        """Add giving record to milestones_log"""
        if giving_date is None:
            giving_date = datetime.utcnow().date()
        elif isinstance(giving_date, str):
            giving_date = datetime.fromisoformat(giving_date).date()
        
        milestones_log = self._load_json(self.milestones_log or '[]')
        milestones_log.append({
            'type': 'giving',
            'date': giving_date.isoformat(),
            'amount': float(amount),
            'campus': campus
        })
        self.milestones_log = self._dump_json(milestones_log)
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
        import logging
        logger = logging.getLogger(__name__)
        
        if attendance_date is None:
            attendance_date = datetime.utcnow().date()
        elif isinstance(attendance_date, str):
            attendance_date = datetime.fromisoformat(attendance_date).date()
        elif isinstance(attendance_date, datetime):
            attendance_date = attendance_date.date()
        
        logger.info(f"add_group_attendance called - person_id: {self.person_id}, group_id: {group_id}, date: {attendance_date}, present: {present}")
        
        # Update last_seen to the attendance date (as datetime for consistency)
        attendance_datetime = datetime.combine(attendance_date, datetime.min.time())
        if not self.last_seen or attendance_datetime > self.last_seen:
            old_last_seen = self.last_seen
            self.last_seen = attendance_datetime
            logger.info(f"Updated last_seen from {old_last_seen} to {self.last_seen}")
        
        # Get group attendance from milestones_log
        milestones_log = self._load_json(self.milestones_log or '[]')
        group_log = [log for log in milestones_log if log.get('type') == 'group_attendance']
        logger.info(f"Current group_attendance_log has {len(group_log)} entries")
        
        # Check for duplicate entries (same group_id and date)
        existing_entry = None
        date_iso = attendance_date.isoformat()
        for entry in group_log:
            entry_date = entry.get('date')
            entry_group_id = entry.get('group_id')
            if entry_group_id == group_id and entry_date == date_iso:
                existing_entry = entry
                logger.info(f"Found existing entry for group {group_id} on {date_iso}")
                break
        
        if existing_entry:
            # Update existing entry
            existing_entry['present'] = present
            logger.info(f"Updated existing entry: {existing_entry}")
        else:
            # Add new entry
            new_entry = {
                'group_id': group_id,
                'date': date_iso,
                'present': present
            }
            group_log.append(new_entry)
            logger.info(f"Added new entry: {new_entry}")
        
        # Save to milestones_log
        all_milestones = self._load_json(self.milestones_log or '[]')
        # Remove old group attendance entries
        all_milestones = [m for m in all_milestones if m.get('type') != 'group_attendance']
        # Add new group attendance entries
        all_milestones.extend(group_log)
        self.milestones_log = self._dump_json(all_milestones)
        logger.info(f"Group attendance log now has {len(group_log)} entries")
        
        # Recalculate heartbeat
        old_engagement = self.overall_engagement
        old_pulse = self.pulse_status
        self.recalculate_heartbeat()
        logger.info(f"Heartbeat recalculated - engagement: {old_engagement} -> {self.overall_engagement}, pulse: {old_pulse} -> {self.pulse_status}")
    
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
        milestones_log_all = self._load_json(self.milestones_log or '[]')
        group_log = [log for log in milestones_log_all if log.get('type') == 'group_attendance']
        if group_log:
            recent_group_dates = []
            for r in group_log:
                if r.get('present', True) and 'date' in r:
                    date_str = r['date']
                    try:
                        if isinstance(date_str, str):
                            # Parse ISO date string and convert to datetime
                            date_obj = datetime.fromisoformat(date_str).date()
                            group_datetime = datetime.combine(date_obj, datetime.min.time())
                        else:
                            # Already a date object
                            group_datetime = datetime.combine(date_str, datetime.min.time())
                        recent_group_dates.append(group_datetime)
                    except (ValueError, TypeError):
                        continue
            if recent_group_dates:
                latest_group = max(recent_group_dates)
                if not latest_activity or latest_group > latest_activity:
                    latest_activity = latest_group
        
        if latest_activity:
            # last_seen is a DATE column, so store only the date part
            if isinstance(latest_activity, datetime):
                self.last_seen = latest_activity.date()
            else:
                self.last_seen = latest_activity
        
        # Calculate days since last seen - convert to date if needed
        if self.last_seen:
            if isinstance(self.last_seen, datetime):
                last_seen_date = self.last_seen.date()
            else:
                last_seen_date = self.last_seen
            days_since_last_seen = (now.date() - last_seen_date).days
        else:
            days_since_last_seen = None
        
        # 2. BIBLE READING (25% weight)
        # Target: Daily reading = 56 days in 8 weeks
        milestones_log = self._load_json(self.milestones_log or '[]')
        bible_log = [m for m in milestones_log if m.get('type') == 'bible_reading']
        recent_bible = [
            r for r in bible_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        bible_freq = min(len(recent_bible) / 56, 1.0)  # Daily target
        bible_score = bible_freq * 100.0
        
        # 3. GIVING (15% weight)
        # Target: Weekly giving = 8 times in 8 weeks
        giving_log = [m for m in milestones_log if m.get('type') == 'giving']
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
        import logging
        logger = logging.getLogger(__name__)
        
        group_log = [m for m in milestones_log if m.get('type') == 'group_attendance']
        logger.info(f"Recalculating heartbeat for person {self.person_id} - group_log has {len(group_log)} entries")
        logger.info(f"Group log entries: {group_log}")
        logger.info(f"Eight weeks ago date: {eight_weeks_ago.date()}")
        
        recent_groups = []
        for r in group_log:
            if 'date' in r and r.get('present', True):
                try:
                    entry_date = datetime.fromisoformat(r['date']).date()
                    if entry_date >= eight_weeks_ago.date():
                        recent_groups.append(r)
                        logger.info(f"Found recent group attendance: {r}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing group attendance date {r.get('date')}: {e}")
                    continue
        
        logger.info(f"Recent groups count: {len(recent_groups)}")
        group_freq = min(len(recent_groups) / 8, 1.0)  # Weekly target
        group_score = group_freq * 100.0
        logger.info(f"Group frequency: {group_freq}, Group score: {group_score}")
        
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
            # Convert last_seen (DATE) to date for comparison with now.date()
            if isinstance(self.last_seen, datetime):
                last_seen_date = self.last_seen.date()
            else:
                last_seen_date = self.last_seen
            days_since_last_seen = (now.date() - last_seen_date).days
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
        
        milestones_log = self._load_json(self.milestones_log or '[]')
        bible_log = [m for m in milestones_log if m.get('type') == 'bible_reading']
        recent_bible = [
            r for r in bible_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Bible reading: {len(recent_bible)} days in last 8 weeks")
        
        giving_log = [m for m in milestones_log if m.get('type') == 'giving']
        recent_giving = [
            r for r in giving_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Giving: {len(recent_giving)} times in last 8 weeks")
        
        serving_log = self._load_json(self.serving_log or '[]')
        recent_serving = [
            r for r in serving_log
            if 'date' in r and datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Serving: {len(recent_serving)} times in last 8 weeks")
        
        group_log = [m for m in milestones_log if m.get('type') == 'group_attendance']
        recent_groups = [
            r for r in group_log
            if 'date' in r and r.get('present', True) and 
            datetime.fromisoformat(r['date']).date() >= eight_weeks_ago.date()
        ]
        reasons.append(f"Connect groups: {len(recent_groups)} meetings in last 8 weeks")
        
        reasons.append(f"Overall engagement score: {int(self.overall_engagement)}/100")
        
        return reasons
    
    def to_dict(self, recalculate=True):
        """Convert engagement profile to dictionary"""
        try:
            # Recalculate heartbeat before returning to ensure data is up to date
            if recalculate:
                self.recalculate_heartbeat()
        except Exception as e:
            # If recalculation fails, log but continue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error recalculating heartbeat for {self.person_id}: {e}")
        
        # Parse milestones_log to extract different types
        try:
            milestones_log = self._load_json(self.milestones_log or '[]')
            bible_log = [m for m in milestones_log if m.get('type') == 'bible_reading']
            giving_log = [m for m in milestones_log if m.get('type') == 'giving']
            group_attendance_log = [m for m in milestones_log if m.get('type') == 'group_attendance']
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error parsing milestones_log for {self.person_id}: {e}")
            bible_log = []
            giving_log = []
            group_attendance_log = []
        
        # Handle last_seen - it's a DATE in DB, not DATETIME
        last_seen_str = None
        try:
            if self.last_seen:
                if isinstance(self.last_seen, datetime):
                    last_seen_str = self.last_seen.isoformat()
                elif hasattr(self.last_seen, 'isoformat'):
                    last_seen_str = self.last_seen.isoformat()
                else:
                    # It's a date object, convert to datetime for isoformat
                    last_seen_str = datetime.combine(self.last_seen, datetime.min.time()).isoformat()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error formatting last_seen for {self.person_id}: {e}")
        
        # Get pulse reasons safely
        try:
            pulse_reasons = self.get_pulse_reasons()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting pulse reasons for {self.person_id}: {e}")
            pulse_reasons = ['Error loading engagement data']
        
        try:
            attendance_log = self._load_json(self.attendance_log or '[]')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error parsing attendance_log for {self.person_id}: {e}")
            attendance_log = []
        
        try:
            serving_log = self._load_json(self.serving_log or '[]')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error parsing serving_log for {self.person_id}: {e}")
            serving_log = []
        
        return {
            'id': self.person_id,  # Use person_id as id (it's the primary key)
            'person_id': self.person_id,
            'pulse_status': getattr(self, 'pulse_status', 'red'),
            'last_seen': last_seen_str,
            'attendance_log': attendance_log,
            'interaction_log': [],  # Not stored in DB
            'bible_log': bible_log,
            'giving_log': giving_log,
            'serving_log': serving_log,
            'group_attendance_log': group_attendance_log,
            'attendance_frequency': getattr(self, 'attendance_frequency', 0.0),
            'serving_frequency': getattr(self, 'serving_frequency', 0.0),
            'overall_engagement': getattr(self, 'overall_engagement', 0.0),
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None,
            'pulse_reasons': pulse_reasons
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
        """Get the next uncompleted step - intelligently skips steps that should be considered complete"""
        if not self.pathway:
            return None
        
        completed_step_ids = [c.pathway_step_id for c in self.step_completions.all()]
        all_steps = self.pathway.steps.order_by(PathwayStep.step_order).all()
        
        # If no steps completed, return first step
        if not completed_step_ids:
            return all_steps[0] if all_steps else None
        
        # Find the highest order number of completed steps
        completed_orders = [
            step.step_order 
            for step in all_steps 
            if step.id in completed_step_ids
        ]
        
        if completed_orders:
            highest_completed_order = max(completed_orders)
            # Find the next uncompleted step after the highest completed step
            for step in all_steps:
                if step.id not in completed_step_ids and step.step_order > highest_completed_order:
                    return step
        
        # If we got here, either all steps are complete, or we should still check for earlier uncompleted steps
        # But only if they haven't completed any steps (to avoid showing step 1 when they've done steps 2,3,4)
        if completed_orders:
            # They've completed steps but there are no steps after their highest completed
            # This means they've completed everything, or we're at the end
            return None
        
        # Fallback: return first uncompleted step
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
            # Create a mapping of step_id to completion date
            completion_map = {
                c.pathway_step_id: c.completed_at.isoformat() if c.completed_at else None
                for c in self.step_completions.all()
            }
            
            pathway_dict = {
                'id': self.pathway.id,
                'name': self.pathway.name,
                'description': self.pathway.description,
                'category': self.pathway.category,
                'steps': [
                    {
                        **step.to_dict(),
                        'is_completed': step.id in completed_step_ids,
                        'completed_at': completion_map.get(step.id)
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
    leader_emails = db.Column(db.Text)  # JSON array of additional leader emails
    
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
    
    def get_leader_emails(self):
        """Get list of all leader emails (leader, co-leader, and additional leaders)"""
        emails = []
        if self.leader and self.leader.email:
            emails.append(self.leader.email.lower())
        if self.co_leader and self.co_leader.email:
            emails.append(self.co_leader.email.lower())
        if self.leader_emails:
            try:
                additional_emails = json.loads(self.leader_emails)
                if isinstance(additional_emails, list):
                    emails.extend([e.lower() for e in additional_emails if e])
            except (json.JSONDecodeError, TypeError):
                pass
        return list(set(emails))  # Remove duplicates
    
    def to_dict(self):
        """Convert connect group to dictionary"""
        # Parse leader_emails JSON (handle gracefully if column doesn't exist)
        leader_emails_list = []
        try:
            if hasattr(self, 'leader_emails') and self.leader_emails:
                try:
                    leader_emails_list = json.loads(self.leader_emails)
                    if not isinstance(leader_emails_list, list):
                        leader_emails_list = []
                except (json.JSONDecodeError, TypeError):
                    leader_emails_list = []
        except AttributeError:
            # Column doesn't exist in database
            leader_emails_list = []
        
        result = {
            'id': self.id,
            'name': self.name,
            'campus': self.campus,
            'leader_id': self.leader_id,
            'leader_name': self.leader.full_name if self.leader else None,
            'leader_email': self.leader.email if self.leader else None,
            'co_leader_id': self.co_leader_id,
            'co_leader_name': self.co_leader.full_name if self.co_leader else None,
            'co_leader_email': self.co_leader.email if self.co_leader else None,
            'leader_emails': leader_emails_list,  # Additional leader emails
            'meeting_day': self.meeting_day,
            'meeting_time': self.meeting_time,
            'meeting_frequency': self.meeting_frequency,
            'location': self.location,
            'leader_access_code': self.leader_access_code if hasattr(self, 'leader_access_code') else None,
        }
        
        # Add member count safely
        try:
            result['member_count'] = self.get_member_count()
        except Exception as e:
            result['member_count'] = 0
        
        result['is_active'] = self.is_active
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        result['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        
        return result


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


class GivingTransaction(db.Model):
    """Detailed giving transaction tracking with source"""
    __tablename__ = 'giving_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    stripe_payment_intent_id = db.Column(db.String(200), unique=True, nullable=True)
    amount = db.Column(db.Float, nullable=False)  # Amount in dollars
    currency = db.Column(db.String(10), default='AUD')
    giving_type = db.Column(db.String(50), nullable=False)  # 'tithe', 'offering', 'missions', 'event'
    campus = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(50), nullable=False)  # 'app', 'qr_code', 'web', 'tap_to_give', 'manual'
    qr_code_id = db.Column(db.String(100), nullable=True)  # For tracking which QR code was used
    service_date = db.Column(db.Date, nullable=True)  # Date of service if from QR code
    status = db.Column(db.String(50), default='completed')  # 'completed', 'pending', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    person = db.relationship('Person', backref='giving_transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'amount': self.amount,
            'currency': self.currency,
            'giving_type': self.giving_type,
            'campus': self.campus,
            'source': self.source,
            'qr_code_id': self.qr_code_id,
            'service_date': self.service_date.isoformat() if self.service_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class GivingQRCode(db.Model):
    """QR codes for tap-to-give on chair backs"""
    __tablename__ = 'giving_qr_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    qr_code_id = db.Column(db.String(100), unique=True, nullable=False)  # Unique identifier for QR
    campus = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(100), nullable=True)  # e.g., "Main Auditorium", "Youth Room"
    seat_number = db.Column(db.String(50), nullable=True)  # e.g., "Row 5, Seat 12"
    is_active = db.Column(db.Boolean, default=True)
    scan_count = db.Column(db.Integer, default=0)  # Track how many times scanned
    last_scan_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'qr_code_id': self.qr_code_id,
            'campus': self.campus,
            'zone': self.zone,
            'seat_number': self.seat_number,
            'is_active': self.is_active,
            'scan_count': self.scan_count,
            'last_scan_at': self.last_scan_at.isoformat() if self.last_scan_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'qr_url': f"/give/qr/{self.qr_code_id}"  # URL for the QR code
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


class PastoralCareAppointment(db.Model):
    """Scheduled pastoral care appointments/catch-ups"""
    __tablename__ = 'pastoral_care_appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    pastor_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=True)
    care_case_id = db.Column(db.Integer, db.ForeignKey('heartbeat_care_cases.id'), nullable=True)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    appointment_type = db.Column(db.String(50), default='catch_up')
    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    location = db.Column(db.String(200))
    location_details = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='scheduled')
    requested_by_person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=True)
    created_by_person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=True)
    
    person_notified = db.Column(db.Boolean, default=False)
    pastor_notified = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    notes = db.Column(db.Text)
    follow_up_notes = db.Column(db.Text)
    
    person = db.relationship('Person', foreign_keys=[person_id], backref='pastoral_appointments')
    pastor = db.relationship('Person', foreign_keys=[pastor_id])
    requested_by = db.relationship('Person', foreign_keys=[requested_by_person_id])
    created_by = db.relationship('Person', foreign_keys=[created_by_person_id])
    care_case = db.relationship('CareCase', backref='appointments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'pastor_id': self.pastor_id,
            'pastor_name': self.pastor.full_name if self.pastor else None,
            'care_case_id': self.care_case_id,
            'title': self.title,
            'description': self.description,
            'appointment_type': self.appointment_type,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'duration_minutes': self.duration_minutes,
            'location': self.location,
            'location_details': self.location_details,
            'status': self.status,
            'requested_by_person_id': self.requested_by_person_id,
            'created_by_person_id': self.created_by_person_id,
            'person_notified': self.person_notified,
            'pastor_notified': self.pastor_notified,
            'reminder_sent': self.reminder_sent,
            'notes': self.notes,
            'follow_up_notes': self.follow_up_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
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


# ============================================================================
# PULSE TV MODULE MODELS
# ============================================================================

class TVSeries(db.Model):
    """TV Series model for Pulse TV"""
    __tablename__ = 'tv_series'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # 'foundations', 'leadership', 'parents', 'youth', etc.
    audience = db.Column(db.String(100))  # 'all', 'adults', 'youth', 'kids', 'parents'
    thumbnail_url = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, default=False)
    create_custom_step = db.Column(db.Boolean, default=False)  # Create custom discipleship step when series completed
    custom_step_name = db.Column(db.String(200))  # Custom name for step (defaults to series title)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    episodes = db.relationship('TVEpisode', backref='series', lazy='dynamic', order_by='TVEpisode.order_index', cascade='all, delete-orphan')
    tags = db.relationship('TVTag', secondary='tv_series_tags', lazy='dynamic', backref='series')
    # Note: discipleship_links are accessed through episodes, not directly from series
    
    def to_dict(self, include_episodes=False):
        """Convert series to dictionary"""
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'audience': self.audience,
            'thumbnail_url': self.thumbnail_url,
            'is_published': self.is_published,
            'create_custom_step': self.create_custom_step,
            'custom_step_name': self.custom_step_name,
            'episode_count': self.episodes.filter_by(is_published=True).count() if include_episodes else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_episodes:
            result['episodes'] = [e.to_dict() for e in self.episodes.filter_by(is_published=True).order_by(TVEpisode.order_index).all()]
        
        return result


class TVEpisode(db.Model):
    """TV Episode model"""
    __tablename__ = 'tv_episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('tv_series.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))  # YouTube/Vimeo embed URL or S3 link
    duration_seconds = db.Column(db.Integer, default=0)
    order_index = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False)
    downloadable_notes_url = db.Column(db.String(500))
    create_custom_step = db.Column(db.Boolean, default=False)  # Create custom discipleship step when episode completed
    custom_step_name = db.Column(db.String(200))  # Custom name for step (defaults to episode title)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('TVTag', secondary='tv_episode_tags', lazy='dynamic', backref='episodes')
    progress_records = db.relationship('TVUserEpisodeProgress', backref='episode', lazy='dynamic', cascade='all, delete-orphan')
    discipleship_links = db.relationship('TVEpisodeDiscipleshipLink', backref='episode', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_progress=False, person_id=None):
        """Convert episode to dictionary"""
        result = {
            'id': self.id,
            'series_id': self.series_id,
            'series_title': self.series.title if self.series else None,
            'title': self.title,
            'description': self.description,
            'video_url': self.video_url,
            'duration_seconds': self.duration_seconds,
            'duration_formatted': self._format_duration(self.duration_seconds),
            'order_index': self.order_index,
            'is_published': self.is_published,
            'downloadable_notes_url': self.downloadable_notes_url,
            'create_custom_step': self.create_custom_step,
            'custom_step_name': self.custom_step_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_progress and person_id:
            progress = self.progress_records.filter_by(person_id=person_id).first()
            if progress:
                result['progress'] = progress.to_dict()
            else:
                result['progress'] = None
        
        return result
    
    def _format_duration(self, seconds):
        """Format duration in seconds to HH:MM:SS or MM:SS"""
        if not seconds:
            return "0:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"


class TVTag(db.Model):
    """Tag model for TV content"""
    __tablename__ = 'tv_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Pivot tables for many-to-many relationships
tv_series_tags = db.Table('tv_series_tags',
    db.Column('series_id', db.Integer, db.ForeignKey('tv_series.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tv_tags.id'), primary_key=True)
)

tv_episode_tags = db.Table('tv_episode_tags',
    db.Column('episode_id', db.Integer, db.ForeignKey('tv_episodes.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tv_tags.id'), primary_key=True)
)


class TVUserEpisodeProgress(db.Model):
    """Tracks user watching progress for episodes"""
    __tablename__ = 'tv_user_episode_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    episode_id = db.Column(db.Integer, db.ForeignKey('tv_episodes.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_position_seconds = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    person = db.relationship('Person', backref='tv_progress')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'episode_id': self.episode_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_position_seconds': self.last_position_seconds,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TVEpisodeDiscipleshipLink(db.Model):
    """Links episodes to discipleship steps for auto-completion"""
    __tablename__ = 'tv_episode_discipleship_links'
    
    id = db.Column(db.Integer, primary_key=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('tv_episodes.id'), nullable=False)
    discipleship_step_type = db.Column(db.String(50), nullable=False)  # 'salvation', 'baptism', 'holy_spirit', 'next_steps', etc.
    auto_complete = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'episode_id': self.episode_id,
            'discipleship_step_type': self.discipleship_step_type,
            'auto_complete': self.auto_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    
    # Normalize email - convert empty string to None
    email_value = email.strip() if email else None
    email_value = email_value if email_value else None
    
    # Normalize department - standardize case format
    department_value = None
    if department:
        dept_lower = department.strip().lower()
        if dept_lower == 'kids':
            department_value = 'Kids'
        elif dept_lower == 'youth':
            department_value = 'Youth'
        elif dept_lower in ['young adults', 'youngadults', 'young_adults']:
            department_value = 'Young Adults'
        elif dept_lower == 'families':
            department_value = 'Families'
        elif dept_lower == 'adults':
            department_value = 'Adults'
        elif dept_lower == 'seniors':
            department_value = 'Seniors'
        else:
            # For other values, use Title Case
            department_value = department.strip().title()
    
    # Create person
    person = Person(
        id=person_id,
        full_name=full_name,
        email=email_value,
        campus=campus,
        preferred_name=preferred_name,
        phone=phone,
        department=department_value,
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

