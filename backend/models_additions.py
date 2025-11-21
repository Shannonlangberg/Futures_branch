"""
Additional models to add to models.py for new heartbeat features
"""

# Add to models.py after existing models:

class AppSession(db.Model):
    """Track app opens for engagement scoring"""
    __tablename__ = 'app_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=False)
    session_start = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    platform = db.Column(db.String(20))  # 'ios', 'android', 'web'
    app_version = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    person = db.relationship('Person', backref='app_sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'platform': self.platform,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PrayerSubmission(db.Model):
    """Prayer and praise submissions from congregation"""
    __tablename__ = 'prayer_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'), nullable=True)  # Nullable for anonymous
    email = db.Column(db.String(200), nullable=True)  # For non-person submissions
    name = db.Column(db.String(200), nullable=True)  # Display name
    
    submission_type = db.Column(db.String(20), nullable=False)  # 'prayer', 'praise'
    category = db.Column(db.String(50))  # 'health', 'family', 'work', 'spiritual', 'other'
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_urgent = db.Column(db.Boolean, default=False)
    
    # Source tracking
    campus = db.Column(db.String(100))
    source = db.Column(db.String(50))  # 'app', 'web', 'qr', 'nfc'
    prayer_link_id = db.Column(db.Integer, db.ForeignKey('prayer_links.id'), nullable=True)
    
    # Moderation
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'declined'
    is_public = db.Column(db.Boolean, default=False)  # Can be shared with prayer team
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='prayer_submissions')
    prayer_link = db.relationship('PrayerLink', backref='submissions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id if not self.is_anonymous else None,
            'name': self.name if not self.is_anonymous else 'Anonymous',
            'submission_type': self.submission_type,
            'category': self.category,
            'content': self.content,
            'is_anonymous': self.is_anonymous,
            'is_urgent': self.is_urgent,
            'campus': self.campus,
            'source': self.source,
            'status': self.status,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

