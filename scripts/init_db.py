#!/usr/bin/env python3
"""
Database initialization script for Email Receipts application.
Creates database tables and default admin user if none exist.
"""
import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path is set
from app import app, db
from models import User, SentEmail

def init_database():
    """Initialize database with tables and default admin user"""
    with app.app_context():
        print("Initializing database...")
        
        # Create all tables
        db.create_all()
        print("[OK] Database tables created")
        
        # Check if any users exist
        user_count = User.query.count()
        
        if user_count == 0:
            # Create default admin user from environment variables
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_email = os.environ.get('ADMIN_EMAIL', '')
            
            print(f"No users found. Creating default admin user: {admin_username}")
            
            admin_user = User(
                username=admin_username,
                email=admin_email if admin_email else None,
                password_hash=generate_password_hash(admin_password),
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"[OK] Default admin user created: {admin_username}")
            if os.environ.get('FLASK_ENV') != 'production':
                print(f"  Username: {admin_username}")
                print(f"  Password: {admin_password}")
                print("  WARNING: Change the default password after first login!")
        else:
            print(f"[OK] Database already has {user_count} user(s). Skipping default admin creation.")
        
        print("[OK] Database initialization complete!")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"[ERROR] Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
