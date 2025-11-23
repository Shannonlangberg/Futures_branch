# serving_models.py - Database Models for Serving Module

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum

# Import the existing db instance
from models import db

class ServingTeam(db.Model):
    """
    Serving teams (e.g., Kids, Worship, Hospitality, Media)
    """
    __tablename__ = 'serving_teams'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    campus = db.Column(db.String(50), nullable=False, index=True)
    department = db.Column(db.String(50), nullable=True)  # e.g., "Ministry", "Operations"
    team_type = db.Column(db.String(30), nullable=False, default='ministry')  # ministry, operations, admin
    
    # Team configuration
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    requires_background_check = db.Column(db.Boolean, nullable=False, default=False)
    min_age = db.Column(db.Integer, nullable=True)
    max_age = db.Column(db.Integer, nullable=True)
    
    # Leadership
    leader_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=True)
    co_leader_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('ServingRole', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('TeamMember', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ServingTeam {self.name} ({self.campus})>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'campus': self.campus,
            'department': self.department,
            'team_type': self.team_type,
            'is_active': self.is_active,
            'requires_background_check': self.requires_background_check,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'leader_id': self.leader_id,
            'co_leader_id': self.co_leader_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'member_count': self.members.filter_by(is_active=True).count(),
            'active_roles_count': self.roles.filter_by(is_active=True).count()
        }


class ServingRole(db.Model):
    """
    Specific roles within serving teams (e.g., "Kids Check-In", "Worship Leader")
    """
    __tablename__ = 'serving_roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    team_id = db.Column(db.String(36), db.ForeignKey('serving_teams.id'), nullable=False)
    
    # Role requirements
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    requires_training = db.Column(db.Boolean, nullable=False, default=False)
    training_hours = db.Column(db.Integer, nullable=True)
    requires_background_check = db.Column(db.Boolean, nullable=False, default=False)
    min_serving_age = db.Column(db.Integer, nullable=True)
    
    # Scheduling
    typical_duration_hours = db.Column(db.Float, nullable=True)  # e.g., 2.5 hours
    typical_frequency = db.Column(db.String(30), nullable=True)  # "weekly", "bi-weekly", "monthly"
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedules = db.relationship('ServingSchedule', backref='role', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ServingRole {self.name} ({self.team.name})>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'is_active': self.is_active,
            'requires_training': self.requires_training,
            'training_hours': self.training_hours,
            'requires_background_check': self.requires_background_check,
            'min_serving_age': self.min_serving_age,
            'typical_duration_hours': self.typical_duration_hours,
            'typical_frequency': self.typical_frequency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TeamMember(db.Model):
    """
    People who are members of serving teams
    """
    __tablename__ = 'team_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False)
    team_id = db.Column(db.String(36), db.ForeignKey('serving_teams.id'), nullable=False)
    
    # Membership status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    joined_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    left_date = db.Column(db.Date, nullable=True)
    
    # Role assignments
    primary_role_id = db.Column(db.String(36), db.ForeignKey('serving_roles.id'), nullable=True)
    secondary_roles = db.Column(db.JSON, nullable=True)  # Array of role IDs
    
    # Permissions
    is_leader = db.Column(db.Boolean, nullable=False, default=False)
    can_schedule = db.Column(db.Boolean, nullable=False, default=False)
    can_approve_requests = db.Column(db.Boolean, nullable=False, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='team_memberships')
    primary_role = db.relationship('ServingRole')
    
    def __repr__(self):
        return f'<TeamMember {self.person.full_name if self.person else "Unknown"} ({self.team.name if self.team else "Unknown"})>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'person_email': self.person.email if self.person else None,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'is_active': self.is_active,
            'joined_date': self.joined_date.isoformat() if self.joined_date else None,
            'left_date': self.left_date.isoformat() if self.left_date else None,
            'primary_role_id': self.primary_role_id,
            'primary_role_name': self.primary_role.name if self.primary_role else None,
            'secondary_roles': self.secondary_roles or [],
            'is_leader': self.is_leader,
            'can_schedule': self.can_schedule,
            'can_approve_requests': self.can_approve_requests,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ServingSchedule(db.Model):
    """
    Scheduled serving opportunities (shifts)
    """
    __tablename__ = 'serving_schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = db.Column(db.String(36), db.ForeignKey('serving_roles.id'), nullable=False)
    team_id = db.Column(db.String(36), db.ForeignKey('serving_teams.id'), nullable=False)
    
    # Scheduling details
    scheduled_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(50), nullable=False, default='Australia/Adelaide')
    
    # Assignment
    assigned_person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=True)
    backup_person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=True)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='open')  # open, assigned, confirmed, completed, cancelled
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_person = db.relationship('Person', foreign_keys=[assigned_person_id])
    backup_person = db.relationship('Person', foreign_keys=[backup_person_id])
    
    def __repr__(self):
        return f'<ServingSchedule {self.role.name if self.role else "Unknown"} on {self.scheduled_date} at {self.start_time}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'timezone': self.timezone,
            'assigned_person_id': self.assigned_person_id,
            'assigned_person_name': self.assigned_person.full_name if self.assigned_person else None,
            'backup_person_id': self.backup_person_id,
            'backup_person_name': self.backup_person.full_name if self.backup_person else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ServingRequest(db.Model):
    """
    Requests to serve (sign-ups, time-off requests, swap requests)
    """
    __tablename__ = 'serving_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False)
    schedule_id = db.Column(db.String(36), db.ForeignKey('serving_schedules.id'), nullable=True)
    team_id = db.Column(db.String(36), db.ForeignKey('serving_teams.id'), nullable=False)
    
    # Request details
    request_type = db.Column(db.String(30), nullable=False)  # sign_up, time_off, swap, availability
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, denied, cancelled
    
    # Scheduling
    requested_date = db.Column(db.Date, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    
    # Request details
    reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Approval
    approved_by = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', foreign_keys=[person_id])
    schedule = db.relationship('ServingSchedule')
    team = db.relationship('ServingTeam')
    approver = db.relationship('Person', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<ServingRequest {self.request_type} by {self.person.full_name if self.person else "Unknown"} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'person_email': self.person.email if self.person else None,
            'schedule_id': self.schedule_id,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'request_type': self.request_type,
            'status': self.status,
            'requested_date': self.requested_date.isoformat() if self.requested_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'reason': self.reason,
            'notes': self.notes,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_notes': self.approval_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ServingRecord(db.Model):
    """
    Actual serving activity records (completed shifts)
    """
    __tablename__ = 'serving_records'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False)
    schedule_id = db.Column(db.String(36), db.ForeignKey('serving_schedules.id'), nullable=True)
    team_id = db.Column(db.String(36), db.ForeignKey('serving_teams.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('serving_roles.id'), nullable=False)
    
    # Serving details
    served_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    actual_duration_hours = db.Column(db.Float, nullable=True)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='completed')  # completed, no_show, partial
    notes = db.Column(db.Text, nullable=True)
    
    # Check-in/out
    checked_in_at = db.Column(db.DateTime, nullable=True)
    checked_out_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', foreign_keys=[person_id])
    schedule = db.relationship('ServingSchedule')
    team = db.relationship('ServingTeam')
    role = db.relationship('ServingRole')
    
    def __repr__(self):
        return f'<ServingRecord {self.person.full_name if self.person else "Unknown"} served {self.role.name if self.role else "Unknown"} on {self.served_date}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'person_email': self.person.email if self.person else None,
            'schedule_id': self.schedule_id,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'served_date': self.served_date.isoformat() if self.served_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'actual_duration_hours': self.actual_duration_hours,
            'status': self.status,
            'notes': self.notes,
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
            'checked_out_at': self.checked_out_at.isoformat() if self.checked_out_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class PersonAvailability(db.Model):
    """
    Person's availability for serving
    """
    __tablename__ = 'person_availability'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = db.Column(db.String(36), db.ForeignKey('persons.id'), nullable=False)
    
    # Availability period
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # None means ongoing
    
    # Time preferences
    preferred_days = db.Column(db.JSON, nullable=True)  # ["monday", "friday", "sunday"]
    preferred_times = db.Column(db.JSON, nullable=True)  # ["morning", "afternoon", "evening"]
    preferred_teams = db.Column(db.JSON, nullable=True)  # Array of team IDs
    
    # Constraints
    unavailable_dates = db.Column(db.JSON, nullable=True)  # Array of specific dates
    max_hours_per_week = db.Column(db.Float, nullable=True)
    max_servings_per_month = db.Column(db.Integer, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='availability_preferences')
    
    def __repr__(self):
        return f'<PersonAvailability {self.person.full_name if self.person else "Unknown"} {self.start_date} to {self.end_date}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person.full_name if self.person else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'preferred_days': self.preferred_days or [],
            'preferred_times': self.preferred_times or [],
            'preferred_teams': self.preferred_teams or [],
            'unavailable_dates': self.unavailable_dates or [],
            'max_hours_per_week': self.max_hours_per_week,
            'max_servings_per_month': self.max_servings_per_month,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Utility functions for serving operations

def create_serving_team(name, campus, **kwargs):
    """Helper function to create a serving team"""
    team = ServingTeam(
        name=name,
        campus=campus,
        **kwargs
    )
    db.session.add(team)
    db.session.commit()
    return team


def add_person_to_team(person_id, team_id, **kwargs):
    """Helper function to add a person to a serving team"""
    member = TeamMember(
        person_id=person_id,
        team_id=team_id,
        **kwargs
    )
    db.session.add(member)
    db.session.commit()
    return member


def create_serving_schedule(role_id, team_id, scheduled_date, start_time, end_time, **kwargs):
    """Helper function to create a serving schedule"""
    schedule = ServingSchedule(
        role_id=role_id,
        team_id=team_id,
        scheduled_date=scheduled_date,
        start_time=start_time,
        end_time=end_time,
        **kwargs
    )
    db.session.add(schedule)
    db.session.commit()
    return schedule


def log_serving_activity(person_id, team_id, role_id, served_date, **kwargs):
    """Helper function to log actual serving activity"""
    record = ServingRecord(
        person_id=person_id,
        team_id=team_id,
        role_id=role_id,
        served_date=served_date,
        **kwargs
    )
    db.session.add(record)
    db.session.commit()
    return record
