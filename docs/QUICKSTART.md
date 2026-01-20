# Quick Start Guide

## Overview

Email Receipts is a Flask application for sending email receipts to magazine buyers with email tracking and webhook integration for real-time delivery status.

## Prerequisites

- Docker & Docker Compose (recommended) **OR** Python 3.11+
- Brevo account (free tier: 300 emails/day)

## Setup Steps

### 1. Get Brevo Credentials

1. Sign up at [https://brevo.com](https://brevo.com) (free, no credit card)
2. **Verify sender email:**
   - Go to Senders → Add a Sender
   - Enter your email and verify it
3. **Create API key:**
   - Go to Account → SMTP & API → API Keys
   - Create a new API key
   - Copy it (starts with `xkeysib-`)

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Brevo Email Service
BREVO_API_KEY=xkeysib-your-actual-api-key-here
SENDER_EMAIL=your-verified-email@example.com
SENDER_NAME=Magazine Store

# Login Credentials (CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password-here
SECRET_KEY=your-secret-key-here

# Application Settings
MAGAZINE_NAME=SYNEXIS'25
PURCHASE_AMOUNT=1000.00
```

Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Run the Application

#### Option A: Docker (Recommended)

```bash
# Start application
docker compose up -d

# View logs
docker compose logs -f web

# Access at: http://localhost:5858
```

#### Option B: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Run application
python app.py

# Access at: http://localhost:5002
```

### 4. Login

- Navigate to the application URL
- Login with your admin credentials
- **⚠️ Change default password immediately if using admin/admin123**

## Features

- **Send Individual Emails**: Custom receipt for single customer
- **Bulk Email Upload**: CSV upload for multiple customers
- **Email Tracking**: View all sent emails with delivery status
- **Real-time Updates**: Webhook integration for delivery, opens, clicks
- **Search & Filter**: Find emails by recipient, status, or date
- **CSV Export**: Download email logs

## Next Steps

- **Enable Webhooks**: See [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) for real-time tracking
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues
- **Production Deployment**: Use Docker with nginx reverse proxy and SSL certificate

## Quick Commands

### Docker
```bash
# Start
docker compose up -d

# Stop
docker compose down

# Rebuild
docker compose build --no-cache && docker compose up -d

# View logs
docker compose logs -f web

# Check status
docker compose ps
```

### Database
```bash
# Initialize database
python scripts/init_db.py

# View sent emails (in Python shell)
python -c "from app import db; from models import SentEmail; print(SentEmail.query.count())"
```
