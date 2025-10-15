from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Week(db.Model):
    __tablename__ = 'weeks'
    
    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "2025-W42"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    presentations = db.relationship('Presentation', backref='week', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'week_id': self.week_id,
            'created_at': self.created_at.isoformat(),
            'presentations': [p.to_dict() for p in self.presentations]
        }


class Presentation(db.Model):
    __tablename__ = 'presentations'
    
    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.String(20), db.ForeignKey('weeks.week_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    presenter = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    vote_records = db.relationship('Vote', backref='presentation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'week_id': self.week_id,
            'title': self.title,
            'presenter': self.presenter,
            'votes': self.votes,
            'created_at': self.created_at.isoformat()
        }


class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id'), nullable=False)
    user_identifier = db.Column(db.String(100), nullable=False)  # Browser fingerprint or session ID
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one vote per user per presentation
    __table_args__ = (db.UniqueConstraint('presentation_id', 'user_identifier', name='_user_presentation_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'user_identifier': self.user_identifier,
            'voted_at': self.voted_at.isoformat()
        }

