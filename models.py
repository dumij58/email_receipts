"""
Database models for Email Receipts application
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and audit trail"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationship to sent emails
    sent_emails = db.relationship('SentEmail', backref='sender', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'


class SentEmail(db.Model):
    """Model to track all sent email receipts"""
    __tablename__ = 'sent_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Recipient information
    recipient_email = db.Column(db.String(120), nullable=False, index=True)
    recipient_name = db.Column(db.String(120), nullable=False)
    
    # Purchase information
    purchase_date = db.Column(db.String(50), nullable=False)
    edition = db.Column(db.String(20), nullable=False)  # 'digital' or 'print'
    
    # Digital edition details (only for digital purchases)
    digital_link = db.Column(db.String(500), nullable=True)
    digital_username = db.Column(db.String(100), nullable=True)
    digital_password = db.Column(db.String(100), nullable=True)
    
    # Email tracking
    sent_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    transaction_id = db.Column(db.String(100), nullable=True, index=True)  # Extracted from message_id
    message_id = db.Column(db.String(255), nullable=True)  # Full Brevo message ID
    status = db.Column(db.String(20), nullable=False, index=True)  # 'success' or 'failed'
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SentEmail {self.recipient_email} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON/CSV export"""
        return {
            'id': self.id,
            'recipient_email': self.recipient_email,
            'recipient_name': self.recipient_name,
            'purchase_date': self.purchase_date,
            'edition': self.edition,
            'digital_link': self.digital_link or '',
            'digital_username': self.digital_username or '',
            'digital_password': self.digital_password or '',
            'sent_at': self.sent_at.strftime('%Y-%m-%d %H:%M:%S') if self.sent_at else '',
            'transaction_id': self.transaction_id or '',
            'status': self.status,
            'error_message': self.error_message or '',
            'sent_by': self.sender.username if self.sender else ''
        }
