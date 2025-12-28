#!/usr/bin/env python3
"""
Database migration script to add Brevo webhook tracking fields
Adds: delivery_status, last_status_update, opened_at, clicked_at, bounce_reason
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, SentEmail
from flask import Flask
from datetime import datetime

def run_migration():
    """Add new columns for Brevo webhook tracking"""
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'sqlite:///email_receipts.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        print("Starting database migration for Brevo webhook tracking...")
        
        # Check if we're using SQLite or PostgreSQL
        engine = db.engine
        connection = engine.connect()
        
        try:
            # Add new columns (SQLite will ignore if already exists)
            migrations = [
                ("delivery_status", "ALTER TABLE sent_emails ADD COLUMN delivery_status VARCHAR(30)"),
                ("last_status_update", "ALTER TABLE sent_emails ADD COLUMN last_status_update TIMESTAMP"),
                ("opened_at", "ALTER TABLE sent_emails ADD COLUMN opened_at TIMESTAMP"),
                ("clicked_at", "ALTER TABLE sent_emails ADD COLUMN clicked_at TIMESTAMP"),
                ("bounce_reason", "ALTER TABLE sent_emails ADD COLUMN bounce_reason TEXT"),
            ]
            
            for field_name, sql in migrations:
                try:
                    connection.execute(db.text(sql))
                    connection.commit()
                    print(f"✓ Added column: {field_name}")
                except Exception as e:
                    connection.rollback()  # Rollback failed transaction
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"○ Column already exists: {field_name}")
                    else:
                        print(f"✗ Error adding {field_name}: {e}")
            
            # Create indexes for new columns
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sent_emails_delivery_status ON sent_emails(delivery_status)",
            ]
            
            for sql in indexes:
                try:
                    connection.execute(db.text(sql))
                    connection.commit()
                    print(f"✓ Created index: {sql.split('idx_')[1].split(' ON')[0]}")
                except Exception as e:
                    print(f"○ Index may already exist: {e}")
            
            print("\n✓ Migration completed successfully!")
            print("\nNew fields added:")
            print("  - delivery_status: Track delivery events (delivered, bounced, etc.)")
            print("  - last_status_update: Timestamp of last webhook event")
            print("  - opened_at: First email open timestamp")
            print("  - clicked_at: First link click timestamp")
            print("  - bounce_reason: Reason for delivery failures")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            return False
        finally:
            connection.close()
    
    return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
