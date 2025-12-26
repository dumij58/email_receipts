# Database Implementation Guide

## Overview

The Email Receipts application now includes a comprehensive database system to:
- Track all sent emails with transaction IDs
- Support multiple admin users
- Maintain email delivery history with status and error information
- Export email logs to CSV

## Database Features

### Auto-Detection
The application automatically detects the database environment:
- **Development (Local)**: Uses SQLite at `data/email_receipts.db`
- **Production (Docker)**: Uses PostgreSQL with connection from `DATABASE_URL` environment variable

### Database Models

#### User Model
Stores admin users with secure password hashing:
```python
- id: Primary key
- username: Unique username (indexed)
- email: Email address (optional)
- password_hash: Securely hashed password
- created_at: Account creation timestamp
- last_login: Last successful login timestamp
- is_active: Account status flag
```

#### SentEmail Model
Tracks all email receipts sent through the system:
```python
- id: Primary key
- user_id: Foreign key to User (who sent it)
- recipient_email: Recipient's email address (indexed)
- recipient_name: Recipient's full name
- magazine_name: Magazine/product name
- purchase_amount: Purchase amount
- purchase_date: Date of purchase
- sent_at: Timestamp when email was sent (indexed)
- message_id: Brevo/email service transaction ID
- status: 'success' or 'failed' (indexed)
- error_message: Error details if failed
```

## Setup Instructions

### Local Development

1. **Install Dependencies**
   ```bash
   pip install Flask-SQLAlchemy==3.1.1 Flask-Migrate==4.0.5
   # Note: psycopg2-binary is only needed for PostgreSQL production
   ```

2. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```
   This will:
   - Create all database tables
   - Create a default admin user (if none exist)
   - Use credentials from environment variables or defaults

3. **Environment Variables** (`.env` file)
   ```bash
   # Admin User Configuration
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   ADMIN_EMAIL=admin@example.com  # Optional
   
   # No DATABASE_URL needed for local dev (uses SQLite)
   ```

### Production (Docker)

1. **Update Environment Variables**
   ```bash
   # Database (automatically configured in docker-compose.yml)
   DATABASE_URL=postgresql://emailapp:emailapp_password@db:5432/email_receipts
   
   # Admin User
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-very-secure-password
   ADMIN_EMAIL=admin@example.com
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```
   
   The PostgreSQL database will:
   - Run in a separate container
   - Persist data in a Docker volume (`postgres_data`)
   - Initialize automatically on first run
   - Create the default admin user if none exist

## Using the System

### Authentication

1. **Login** at `/login` with:
   - Default username from `ADMIN_USERNAME` env var (default: `admin`)
   - Default password from `ADMIN_PASSWORD` env var (default: `admin123`)
   - ⚠️ **Change the default password immediately in production!**

2. **Last Login Tracking**: The system updates `last_login` timestamp on each successful login

### Viewing Sent Emails

Navigate to **Sent Emails** in the navigation menu to:

1. **View Email History**
   - Paginated list (20/50/100 per page)
   - Shows recipient info, magazine details, timestamps, status
   - Displays Brevo message IDs for tracking
   - Shows error messages for failed sends

2. **Filter Emails**
   - **Status**: Filter by success/failed
   - **Date Range**: From/To date filters
   - **Search**: Search by recipient email or name
   - **Per Page**: Adjust results per page (20, 50, or 100)

3. **Export to CSV**
   - Click "Export to CSV" button
   - Exports filtered results with all fields
   - Filename includes timestamp: `sent_emails_YYYYMMDD_HHMMSS.csv`

### Email Tracking

Every email sent (single or bulk) is automatically logged with:
- Who sent it (current logged-in user)
- Recipient details
- Purchase information
- Send timestamp
- Brevo message ID (for delivery tracking)
- Success/failure status
- Error message (if failed)

## Database Management

### Migrations (Future)

When you need to modify the database schema:

```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Backup (Production)

**PostgreSQL Backup:**
```bash
# Backup database
docker-compose exec db pg_dump -U emailapp email_receipts > backup.sql

# Restore database
docker-compose exec -T db psql -U emailapp email_receipts < backup.sql
```

**SQLite Backup (Local):**
```bash
# Simply copy the database file
cp data/email_receipts.db data/email_receipts.db.backup
```

### Managing Users

#### Add New Admin User (via Python)

```python
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    new_admin = User(
        username='newadmin',
        email='newadmin@example.com',
        password_hash=generate_password_hash('secure-password'),
        created_at=datetime.utcnow(),
        is_active=True
    )
    db.session.add(new_admin)
    db.session.commit()
    print(f"Created user: {new_admin.username}")
```

#### Disable User

```python
from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(username='oldadmin').first()
    if user:
        user.is_active = False
        db.session.commit()
        print(f"Disabled user: {user.username}")
```

## Security Considerations

1. **Password Hashing**: All passwords are hashed using Werkzeug's `generate_password_hash()`
2. **Database Credentials**: PostgreSQL credentials should be changed in production
3. **Default Admin**: Always change the default admin password after first login
4. **Inactive Users**: Set `is_active=False` instead of deleting users (maintains audit trail)
5. **Connection Pooling**: Configured with `pool_pre_ping` and `pool_recycle` for reliability

## Troubleshooting

### "No such table: users" Error
Run the initialization script:
```bash
python scripts/init_db.py
```

### Login Not Working
1. Verify user exists in database
2. Check `is_active=True` for the user
3. Ensure correct password
4. Check environment variables are loaded

### PostgreSQL Connection Issues (Docker)
1. Verify database container is running: `docker-compose ps`
2. Check database health: `docker-compose logs db`
3. Verify `DATABASE_URL` environment variable
4. Ensure containers are on the same network

### Database Migration Issues
1. Delete `migrations/` folder if corrupted
2. Re-run `flask db init` and `flask db migrate`
3. Or use `scripts/init_db.py` for fresh start

## Performance Optimization

The database includes indexes on frequently queried fields:
- `User.username` - Fast login lookups
- `SentEmail.recipient_email` - Fast recipient searches
- `SentEmail.sent_at` - Fast date range queries
- `SentEmail.status` - Fast status filtering

## Data Retention

- **Current Policy**: All email records are retained permanently
- **Future Consideration**: Implement archival or cleanup if database grows large
- **Export Regularly**: Use CSV export feature for external archival

## API Changes

The email service now returns detailed transaction data:

```python
# Before (boolean only)
success = email_service.send_single_receipt(...)

# After (tuple with details)
success, message_id, error_message = email_service.send_single_receipt(...)
```

This allows the application to log detailed information about each email transaction.

## Summary of Files Created/Modified

### New Files
- `models.py` - Database models (User, SentEmail)
- `scripts/init_db.py` - Database initialization script
- `templates/sent_emails.html` - Sent emails viewing page
- `data/email_receipts.db` - SQLite database (local dev)
- `docs/DATABASE.md` - This documentation file

### Modified Files
- `requirements.txt` - Added database dependencies
- `app.py` - Database configuration, authentication refactor, email logging
- `email_service.py` - Return transaction details (message_id, errors)
- `docker-compose.yml` - Added PostgreSQL service
- `Dockerfile` - Run init script, create data directory
- `templates/base.html` - Added "Sent Emails" navigation link

## Next Steps

Future enhancements to consider:
1. User management interface (create/edit/delete users via web UI)
2. Email resend functionality from sent emails page
3. Advanced analytics and reporting dashboard
4. Automatic database backup scheduling
5. Email delivery status webhooks from Brevo
6. Multi-tenant support (separate databases per organization)
