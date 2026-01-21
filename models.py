"""
Database models for Email Receipts application
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import os

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
    
    # Active account for session persistence
    active_account_id = db.Column(db.Integer, db.ForeignKey('email_accounts.id'), nullable=True)
    
    # Relationship to sent emails
    sent_emails = db.relationship('SentEmail', backref='sender', lazy='dynamic')
    
    # Relationship to active account
    active_account = db.relationship('EmailAccount', foreign_keys=[active_account_id], backref='active_users')
    
    def __repr__(self):
        return f'<User {self.username}>'


class EmailAccount(db.Model):
    """Model to store multiple email sending accounts"""
    __tablename__ = 'email_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "FOSMedia Main", "SYNEXIS Account"
    
    # Encrypted Brevo API credentials
    brevo_api_key = db.Column(
        EncryptedType(db.String, os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'), AesEngine, 'pkcs5'),
        nullable=False
    )
    
    # Sender information
    sender_email = db.Column(db.String(120), nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    
    # Status and metadata
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    templates = db.relationship('EmailTemplate', backref='account', lazy='dynamic', cascade='all, delete-orphan')
    sent_emails = db.relationship('SentEmail', backref='account', lazy='dynamic')
    
    def __repr__(self):
        return f'<EmailAccount {self.name}>'


class EmailTemplate(db.Model):
    """Model to store customizable email templates"""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('email_accounts.id'), nullable=False)
    
    # Template information
    name = db.Column(db.String(100), nullable=False)  # e.g., "SYNEXIS Digital Receipt"
    template_type = db.Column(db.String(50), nullable=False)  # receipt_digital, receipt_print, reminder
    template_path = db.Column(db.String(255), nullable=False)  # Path to HTML file
    
    # Magazine/Product information
    magazine_name = db.Column(db.String(100), nullable=True)
    purchase_amount = db.Column(db.String(50), nullable=True)
    
    # Status and metadata
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    sent_emails = db.relationship('SentEmail', backref='template', lazy='dynamic')
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'


class SentEmail(db.Model):
    """Model to track all sent email receipts"""
    __tablename__ = 'sent_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Account and template used for sending
    account_id = db.Column(db.Integer, db.ForeignKey('email_accounts.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    
    # Recipient information
    recipient_email = db.Column(db.String(120), nullable=False, index=True)
    recipient_name = db.Column(db.String(120), nullable=False)
    
    # Purchase information
    purchase_date = db.Column(db.String(50), nullable=False)
    edition = db.Column(db.String(20), nullable=False)  # 'digital' or 'print'
    
    # Store actual values used (for historical accuracy)
    magazine_name = db.Column(db.String(100), nullable=True)
    purchase_amount = db.Column(db.String(50), nullable=True)
    
    # Digital edition details (only for digital purchases)
    digital_link = db.Column(db.String(500), nullable=True)
    digital_username = db.Column(db.String(100), nullable=True)
    digital_password = db.Column(db.String(100), nullable=True)
    
    # Email tracking
    sent_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    transaction_id = db.Column(db.String(100), nullable=True, index=True)  # Extracted from message_id
    message_id = db.Column(db.String(255), nullable=True)  # Full Brevo message ID
    status = db.Column(db.String(20), nullable=False, index=True)  # 'success' or 'failed' (initial send status)
    error_message = db.Column(db.Text, nullable=True)
    
    # Brevo webhook tracking - delivery and engagement events
    delivery_status = db.Column(db.String(30), nullable=True, index=True)  # delivered, hard_bounce, soft_bounce, blocked, spam, invalid_email
    last_status_update = db.Column(db.DateTime, nullable=True)  # Last webhook event timestamp
    opened_at = db.Column(db.DateTime, nullable=True)  # First email open timestamp
    clicked_at = db.Column(db.DateTime, nullable=True)  # First link click timestamp
    bounce_reason = db.Column(db.Text, nullable=True)  # Reason for bounce/block/spam
    
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
            'magazine_name': self.magazine_name or '',
            'purchase_amount': self.purchase_amount or '',
            'digital_link': self.digital_link or '',
            'digital_username': self.digital_username or '',
            'digital_password': self.digital_password or '',
            'sent_at': self.sent_at.strftime('%Y-%m-%d %H:%M:%S') if self.sent_at else '',
            'transaction_id': self.transaction_id or '',
            'status': self.status,
            'delivery_status': self.delivery_status or '',
            'last_status_update': self.last_status_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_status_update else '',
            'opened_at': self.opened_at.strftime('%Y-%m-%d %H:%M:%S') if self.opened_at else '',
            'clicked_at': self.clicked_at.strftime('%Y-%m-%d %H:%M:%S') if self.clicked_at else '',
            'bounce_reason': self.bounce_reason or '',
            'error_message': self.error_message or '',
            'sent_by': self.sender.username if self.sender else '',
            'account_name': self.account.name if self.account else '',
            'template_name': self.template.name if self.template else ''
        }
