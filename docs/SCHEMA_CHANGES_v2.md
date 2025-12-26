# Database Implementation & Schema Changes

## Overview
This document covers two major updates:
1. **Initial Database Implementation** - Added database tracking for sent emails and admin users
2. **Schema Updates** - Added edition tracking (digital/print) with conditional digital credentials and transaction ID extraction

---

## Part 1: Initial Database Implementation

### New Database Models

**User Model:**
- `id` (Integer, primary key)
- `username` (String(80), unique, indexed)
- `password_hash` (String(255))
- `created_at` (DateTime)
- `is_active` (Boolean, default True)

**SentEmail Model (Initial):**
- `id` (Integer, primary key)
- `user_id` (Integer, foreign key to User)
- `recipient_email` (String(255), indexed)
- `recipient_name` (String(255))
- `magazine_name` (String(255))
- `purchase_amount` (String(50))
- `purchase_date` (String(50))
- `sent_at` (DateTime, indexed)
- `message_id` (String(255))
- `status` (String(50), indexed)
- `error_message` (Text, nullable)

### Features Added

**Database Auto-Detection:**
- SQLite for development (no DATABASE_URL)
- PostgreSQL for production (DATABASE_URL set)

**Authentication System:**
- User login with Flask-Login
- Password hashing with Werkzeug
- CSRF protection
- Rate limiting (5 attempts per 5 minutes)
- Session management
- Default admin user creation (dumij58/dumijfosmedia)

**Email Tracking:**
- All sent emails logged to database
- Records success/failure status
- Stores Brevo message_id
- Links to sending user
- Tracks error messages

**Sent Emails Viewer:**
- Paginated view (20/50/100 per page)
- Filtering by status (success/failed)
- Date range filtering
- Search by email or name
- CSV export functionality
- Maintains filters in export

**Database Management:**
- Flask-Migrate for migrations
- Initialization script (scripts/init_db.py)
- Proper indexing for performance
- Database directory creation

### Docker Integration

**docker-compose.yml:**
- Added PostgreSQL 15 service
- postgres_data volume for persistence
- Environment variables for connection

**Dockerfile:**
- Creates data directory
- Runs init_db.py on startup
- Handles both SQLite and PostgreSQL

### Bug Fixes (Deprecation Warnings)

**Fixed Deprecations:**
- Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Replaced `User.query.get(id)` with `db.session.get(User, id)`

---

## Part 2: Schema Updates - Edition & Transaction Tracking

## Database Schema Changes

### SentEmail Model Updates

**Removed Columns:**
- `magazine_name` - Now retrieved from environment variable only
- `purchase_amount` - Now retrieved from environment variable only

**Added Columns:**
- `edition` (String, required) - Type of purchase: 'digital' or 'print'
- `transaction_id` (String(100), indexed) - Extracted from Brevo message_id format
- `digital_link` (String(500), nullable) - Digital access URL
- `digital_username` (String(100), nullable) - Digital login username  
- `digital_password` (String(100), nullable) - Digital login password

## Backend Changes

### app.py

**New Helper Function:**
- `extract_transaction_id(message_id)` - Parses Brevo format `<[transaction_id]@smtp-relay.mailin.fr>` to extract transaction ID

**Updated Routes:**
- `send_single` - Added edition field validation, conditional digital field validation, transaction ID extraction
- `send_bulk` - Updated CSV parsing to handle edition and digital columns, conditional field handling
- `api_send_email` - Added edition validation, digital fields support
- `export_sent_emails` - Updated export columns to include transaction_id, edition, digital fields

**Validation Logic:**
- Edition must be 'digital' or 'print'
- Digital fields (link, username, password) required only when edition='digital'
- Digital fields cleared/ignored for print editions

## Frontend Changes

### templates/send_single.html

**New Form Fields:**
- Edition dropdown (digital/print selection)
- Digital Access Link (URL input, conditional)
- Username (text input, conditional)
- Password (text input, conditional)

**JavaScript Functionality:**
- Automatically shows/hides digital fields based on edition selection
- Dynamically sets required attribute on digital fields
- Clears digital field values when switching to print edition

### templates/sent_emails.html

**Table Column Changes:**
- **Removed:** Magazine, Amount, Message ID columns
- **Added:** Edition, Transaction ID columns
- **Updated:** Status now displays as ✓ (green) / ✗ (red) symbols instead of badge

**New Features:**
- Edition badge display (📱 Digital / 📰 Print)
- "Digital Access" column with "Show Details" button for digital editions
- Expandable row showing digital credentials (link, username, password)
- JavaScript toggle for digital details visibility

### templates/send_bulk.html

**Updated CSV Documentation:**
- New format: `email,name,purchase_date,edition,link,username,password`
- Clear explanation of required vs conditional columns
- Examples showing both print and digital entries
- Note about leaving digital columns empty for print editions

## Sample Data Updates

### sample_data.csv
- Updated header to include edition and digital columns
- Mixed examples of print and digital purchases
- Print editions have empty digital columns
- Digital editions include link, username, password

## Migration Notes

**Breaking Changes:**
- Old database must be dropped and recreated (incompatible schema)
- CSV import format changed - old CSV files won't work
- API endpoints now require edition field

**Backward Compatibility:**
- Magazine name and amount still available via environment variables
- Email sending functionality unchanged
- Authentication system unaffected

## Testing Checklist

- [x] Database reinitialized with new schema
- [x] Flask app starts without errors
- [x] Sample CSV files updated
- [ ] Test single email with print edition
- [ ] Test single email with digital edition
- [ ] Test bulk upload with mixed editions
- [ ] Verify transaction ID extraction
- [ ] Check sent emails display
- [ ] Test CSV export with new columns
- [ ] Verify digital details expansion

## Files Modified

**Backend:**
- `models.py` - SentEmail model schema changes
- `app.py` - Route updates, validation logic, transaction ID extraction

**Frontend:**
- `templates/send_single.html` - Edition selection, conditional digital fields
- `templates/sent_emails.html` - Updated table columns, digital details display
- `templates/send_bulk.html` - CSV format documentation

**Data:**
- `sample_data.csv` - Updated format with digital examples
- `sample_data_new.csv` - New sample file with complete examples
