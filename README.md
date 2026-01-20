# Email Receipts Flask Application

Flask application for sending email receipts to magazine buyers with real-time delivery tracking via Brevo webhooks.

## 🚀 Quick Start

**New users:** See [Quick Start Guide](docs/QUICKSTART.md) for complete setup instructions.

### Docker (Recommended)

```bash
# 1. Create .env file with your credentials
cp .env.example .env
nano .env  # Add BREVO_API_KEY, SENDER_EMAIL, admin credentials

# 2. Start application
docker compose up -d

# Access at: http://localhost:5858
```

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt
python scripts/init_db.py

# 2. Configure .env file (see Quick Start Guide)

# 3. Run
python app.py

# Access at: http://localhost:5002
```

**Default login:** admin / admin123  
⚠️ **Change password in `.env` immediately!**

## Features

- 🔐 **User Authentication** - Secure login with password hashing
- 📧 **Email Sending** - Individual and bulk email receipts via Brevo API
- 📊 **Email Tracking** - Database-backed history with transaction IDs
- 📈 **Real-time Status** - Webhook integration for delivery, opens, clicks
- 🔍 **Search & Filter** - Filter by status, date, recipient
- 📥 **CSV Export** - Download complete email logs
- 🐳 **Docker Support** - Containerized deployment with PostgreSQL
- 🎨 **Clean UI** - Modern, responsive web interface

## Prerequisites

- **Docker & Docker Compose** (recommended) OR **Python 3.11+**
- **Brevo account** - Free tier: 300 emails/day ([Sign up](https://brevo.com))

## Documentation

- 📚 **[Quick Start Guide](docs/QUICKSTART.md)** - Complete setup instructions
- 🔌 **[Webhook Setup](docs/WEBHOOK_SETUP.md)** - Enable real-time delivery tracking  
- 🔧 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## Project Structure

```
email-receipts/
├── app.py                  # Main Flask application
├── email_service.py        # Email sending logic (Brevo API)
├── models.py              # Database models (User, SentEmail)
├── templates/              # HTML templates
│   ├── send_single.html   # Single email form
│   ├── send_bulk.html     # Bulk upload form
│   ├── send_reminder.html # Reminder emails
│   └── sent_emails.html   # Email history viewer
├── data/                   # SQLite database (local dev)
├── docs/                   # Documentation
│   ├── QUICKSTART.md      # Getting started guide
│   ├── WEBHOOK_SETUP.md   # Webhook configuration
│   └── TROUBLESHOOTING.md # Common issues
├── scripts/                # Utility scripts
│   ├── init_db.py         # Database initialization
│   └── check_security.py  # Security checker
├── requirements.txt        # Python dependencies
├── docker-compose.yml     # Docker configuration
└── .env.example           # Environment template
```

## Configuration

### Required Environment Variables

Create a `.env` file with:

```bash
# Brevo Email Service
BREVO_API_KEY=xkeysib-your-api-key-here
SENDER_EMAIL=your-verified-email@example.com
SENDER_NAME=Magazine Store

# Admin Login (CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password
SECRET_KEY=your-secret-key-here

# Optional: Webhook Security
BREVO_WEBHOOK_SECRET=your-webhook-secret

# Application Settings
MAGAZINE_NAME=SYNEXIS'25
PURCHASE_AMOUNT=1000.00
```

**Generate secure keys:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

### Send Individual Email

1. Login to the application
2. Click "Send Single Email"
3. Fill in recipient details
4. Click "Send Receipt"

### Send Bulk Emails

1. Prepare CSV file with columns: `email`, `name`, `purchase_date`
2. Click "Send Bulk Emails"
3. Upload CSV file
4. Review and confirm

### View Email History

- Navigate to "Sent Emails"
- Filter by status, date, or search recipient
- View delivery status badges:
  - ✓ Delivered (green)
  - ⚠ Soft Bounce (yellow)
  - ✗ Hard Bounce (red)
  - 👁 Opened (blue)
  - 🖱 Clicked (cyan)

## Docker Commands

```bash
# Start application
docker compose up -d

# Stop application
docker compose down

# View logs
docker compose logs -f web

# Rebuild
docker compose build --no-cache && docker compose up -d

# Check status
docker compose ps
```

## Local Development Commands

```bash
# Initialize database
python scripts/init_db.py

# Check security configuration
python scripts/check_security.py

# Run application
python app.py
```

## Common Issues

**Emails not sending?**
- Verify BREVO_API_KEY in `.env`
- Ensure sender email is verified in Brevo dashboard
- Check logs: `docker compose logs -f web`

**Can't login?**
- Verify credentials in `.env` match what you're entering
- Reset database: `rm -f data/email_receipts.db && python scripts/init_db.py`

**Webhook not working?**
- Configure webhook URL in Brevo dashboard
- Use ngrok for local testing
- See [Webhook Setup Guide](docs/WEBHOOK_SETUP.md)

**More help:** See [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## Security Notes

- ⚠️ **Always change default credentials** before deployment
- 🔒 Use strong passwords and SECRET_KEY
- 🌐 Deploy with HTTPS in production (use nginx reverse proxy)
- 🔐 Keep `.env` file secure (already in `.gitignore`)
- 📝 Run `python scripts/check_security.py` to verify configuration

## License

MIT License - see LICENSE file for details
