# Email Receipts Flask Application

A professional Flask application for sending email receipts to magazine buyers. Features a clean web interface for sending individual and bulk emails, with full Docker support for easy deployment.

## 🚀 Quick Start

### Local Development
```bash
# 1. Clone the repository
git clone https://github.com/dumij58/email_receipts.git
cd email_receipts

# 2. Set up environment
cp .env.example .env
nano .env  # Update with your credentials

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python3 app.py
```

**Access at:** http://localhost:5002

### Docker Deployment (Production/Server)
```bash
# Quick start
docker compose up -d

# Access at: http://your-server:5858
```

**📖 For server deployment, see [SERVER_DEPLOYMENT.md](SERVER_DEPLOYMENT.md)**

**Default login:** admin / admin123 (⚠️ Change in .env file!)

> 📖 **New to this project?** Start with the [Security Summary](docs/SECURITY_SUMMARY.md) to understand security features.

## Features

- 🔐 **User Authentication**: Secure login system with database-backed user management
- 📊 **Email Tracking**: Track all sent emails with transaction IDs and status
- � **Real-time Status Updates**: Brevo webhook integration for delivery tracking, opens, clicks, bounces
- 📧 **Single Email Sending**: Send individual receipts with custom details
- 📬 **Bulk Email Sending**: Upload CSV files to send receipts to multiple customers
- 📈 **Sent Emails Dashboard**: View, filter, and export email history with delivery status badges
- 🔍 **Advanced Filtering**: Filter by status, date range, and search recipients
- 📥 **CSV Export**: Export filtered email logs with delivery metrics
- 🎨 **Clean Web Interface**: Modern, responsive UI built with HTML/CSS
- 🔒 **Secure Configuration**: Environment-based API credentials
- 🗄️ **Database Support**: SQLite for development, PostgreSQL for production
- 🐳 **Docker Support**: Fully containerized with Docker and docker compose
- 📊 **API Endpoints**: RESTful API for programmatic access
- ✅ **Professional Templates**: HTML email templates with receipt details

## Project Structure

```
email-receipts/
├── app.py                  # Main Flask application with authentication
├── app_basic.py           # Basic version (backup)
├── email_service.py        # Email sending logic
├── models.py              # Database models (User, SentEmail)
├── templates/              # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Dashboard
│   ├── login.html         # Login page
│   ├── send_single.html   # Single email form
│   ├── send_bulk.html     # Bulk email form
│   └── sent_emails.html   # Email history viewer
├── data/                   # Database files (SQLite, local dev)
├── docs/                   # Documentation
│   ├── DATABASE.md        # Database implementation guide
│   ├── MIGRATION_GUIDE.md # Migration instructions
│   ├── LOGIN_FEATURE.md
│   ├── SECURITY_SUMMARY.md
│   ├── SECURITY_RECOMMENDATIONS.md
│   ├── DOCKER_DEPLOYMENT.md
│   └── DOCKER_UPDATE_SUMMARY.md
├── scripts/                # Utility scripts
│   ├── init_db.py         # Database initialization
│   ├── check_security.py
│   ├── setup_credentials.sh
│   └── docker_deploy.sh
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration (with PostgreSQL)
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Prerequisites

- Python 3.11+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- Brevo account (free tier: 300 emails/day)

## Setup Instructions

### 1. Clone or Download the Project

### 2. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Brevo credentials:

```env
BREVO_API_KEY=your-brevo-api-key
SENDER_EMAIL=your-verified-email@example.com
SENDER_NAME=Magazine Store
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

**Setting up Brevo (Sendinblue)**:
1. Sign up at https://brevo.com (free tier: 300 emails/day)
2. Verify your sender email: Senders → Add a Sender → Verify email
3. Create an API Key: Account → SMTP & API → API Keys → Create a new API key
4. Copy the API key and add it to your `.env` file as `BREVO_API_KEY`
5. Use your verified email as `SENDER_EMAIL`

**⚠️ Important**: Change the default admin credentials (`ADMIN_USERNAME` and `ADMIN_PASSWORD`) before deploying to production!

### 3. Local Development Setup

#### Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Initialize Database

```bash
python scripts/init_db.py
```

This will create the SQLite database and set up the default admin user from your `.env` credentials.

#### Run the Application

```bash
python app.py
```

Visit: http://localhost:5002

### 4. Docker Deployment

#### Build and Run with Docker Compose

```bash
docker compose up -d
```

The application will be available at: http://localhost:5858

Docker deployment includes:
- **Web Application**: Flask app with Gunicorn
- **PostgreSQL Database**: Persistent storage for users and email logs
- **Automatic Initialization**: Database tables and admin user created on first run

#### Stop the Application

```bash
docker compose down
```

#### View Logs

```bash
docker compose logs -f
```

#### Rebuild After Changes

```bash
docker compose up -d --build
```

## Usage

### Login

When you first access the application, you'll be redirected to the login page.

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**⚠️ Security Note**: These are default credentials for development. **Always change them** in production by setting the `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables in your `.env` file.

### Web Interface

1. **Login Page** (`/login`): Secure authentication with database-backed users
2. **Dashboard** (`/`): Overview and navigation (requires login)
3. **Send Single Email** (`/send-single`): Form for individual receipts (requires login)
4. **Send Bulk Emails** (`/send-bulk`): CSV upload for batch sending (requires login)
5. **Sent Emails** (`/sent-emails`): View email history with filtering and export (requires login)
6. **Logout**: Click the red "Logout" button in the navigation bar

### Sent Emails Dashboard

The **Sent Emails** page provides comprehensive email tracking with real-time delivery status:

**Features:**
- View all sent email receipts with full details
- **Real-time delivery tracking** via Brevo webhooks:
  - ✓ Delivered - Successfully delivered to recipient
  - ✗ Hard Bounce - Permanent delivery failure
  - ⚠ Soft Bounce - Temporary delivery issue
  - 🚫 Blocked - Blocked by recipient's server
  - 🚩 Spam - Marked as spam
- **Engagement metrics**:
  - 👁 Email opened by recipient
  - 🖱 Links clicked by recipient
- Filter by status (success/failed)
- Filter by date range (from/to)
- Search by recipient email or name
- Adjustable pagination (20/50/100 per page)
- Export filtered results to CSV with delivery metrics
- View bounce reasons and error details

**Access:** Navigate to "Sent Emails" in the top menu after logging in.

### Setting Up Webhooks for Real-Time Tracking

To enable real-time email delivery and engagement tracking:

1. **Configure webhook secret** (optional but recommended):
   ```bash
   # Add to .env or docker-compose.yml
   BREVO_WEBHOOK_SECRET=your-secure-random-secret
   ```

2. **Configure webhook in Brevo dashboard**:
   - Login to [Brevo](https://app.brevo.com/)
   - Go to: Profile → SMTP & API → Webhooks
   - Add webhook URL: `https://your-domain.com/webhook/brevo`
   - Select events: delivered, hard_bounce, soft_bounce, blocked, spam, opened, click

3. **For local testing with ngrok**:
   ```bash
   ngrok http 5000
   # Use the HTTPS URL: https://abc123.ngrok.io/webhook/brevo
   ```

**📖 Detailed setup instructions:** See [docs/WEBHOOK_SETUP.md](docs/WEBHOOK_SETUP.md)

### CSV File Format for Bulk Sending

Your CSV file should have these columns:

```csv
email,name,magazine_name,purchase_amount,purchase_date
john@example.com,John Doe,Tech Monthly,29.99,2025-01-15
jane@example.com,Jane Smith,Fashion Weekly,19.99,2025-01-14
```

**Required columns:**
- `email`: Customer's email address
- `name`: Customer's full name
- `magazine_name`: Name of the magazine
- `purchase_amount`: Amount paid (without currency symbol)
- `purchase_date`: Date of purchase (YYYY-MM-DD format)

### API Endpoints

#### Health Check
```bash
GET /api/health
```

#### Send Single Email (API)
```bash
POST /api/send-email
Content-Type: application/json

{
  "email": "customer@example.com",
  "name": "John Doe",
  "magazine_name": "Tech Monthly",
  "purchase_amount": "29.99",
  "purchase_date": "2025-01-15"
}
```

## Docker Deployment to Local Server

### 1. Transfer Files to Server

```bash
scp -r email-receipts/ user@your-server:/path/to/deployment/
```

### 2. SSH into Server

```bash
ssh user@your-server
cd /path/to/deployment/email-receipts
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

### 4. Deploy with Docker Compose

```bash
docker compose up -d
```

### 5. Access the Application

Open your browser and navigate to:
```
http://your-server-ip:5000
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | PostgreSQL connection (Docker only) | Auto-configured |
| `BREVO_API_KEY` | Brevo API key for email service | Required |
| `SENDER_EMAIL` | Sender email address (must be verified in Brevo) | Required |
| `SENDER_NAME` | Sender display name | Magazine Store |
| `MAGAZINE_NAME` | Default magazine name | SYNEXIS'25 |
| `PURCHASE_AMOUNT` | Default purchase amount | 1000.00 |
| `ADMIN_USERNAME` | Admin login username | admin |
| `ADMIN_PASSWORD` | Admin login password | admin123 |
| `ADMIN_EMAIL` | Admin email address (optional) | - |

## Troubleshooting

### Database Issues

1. **"No such table: users"**: Run `python scripts/init_db.py` to initialize the database
2. **Can't login after setup**: Verify admin credentials in `.env` and reinitialize database
3. **Database locked (SQLite)**: Only one process can write at a time; restart the application
4. **PostgreSQL connection failed (Docker)**: Check database container with `docker compose logs db`

### Email Not Sending

1. **Check Brevo API key**: Verify the API key is correct in `.env`
2. **Verify sender email**: Make sure your sender email is verified in Brevo dashboard
3. **Check API limits**: Free tier allows 300 emails/day
4. **Check logs**: `docker compose logs -f` to see error messages
5. **Check Sent Emails page**: View status and error messages for failed sends

### Docker Issues

1. **Port already in use**: Change port in `docker-compose.yml`
2. **Build fails**: Run `docker compose build --no-cache`
3. **Container won't start**: Check logs with `docker compose logs`
4. **Database not initializing**: Check `docker compose logs web` for initialization errors

## Security Notes

- ✅ **Login Required**: All routes except `/login` require authentication
- 🗄️ **Database-Backed Users**: User credentials stored securely in database with hashed passwords
- 🔐 **Change Default Credentials**: Update `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`
- 🔑 Never commit `.env` file to version control (already in `.gitignore`)
- 🔒 Use strong secret keys and passwords in production
- 🔐 Keep your Brevo API key secure and never expose it publicly
- ⚡ Rate limiting implemented for login attempts (5 attempts per 5 minutes)
- 🛡️ Use HTTPS in production to protect login credentials in transit
- 📊 **Audit Trail**: All sent emails tracked with sender identification

### Managing Users

The application uses a database-backed authentication system. Users are stored in the database with secure password hashing.

**Adding New Admin Users**: See [DATABASE.md](docs/DATABASE.md) for instructions on adding additional admin users programmatically.

**For Existing Installations**: If upgrading from a previous version, see [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for migration instructions.

## 📚 Documentation

### Quick Reference
- **[Database Implementation Guide](docs/DATABASE.md)** - Complete database documentation
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Upgrade instructions for existing installations
- **[Scripts Guide](scripts/README.md)** - Utility scripts documentation
- **[Login Feature Guide](docs/LOGIN_FEATURE.md)** - Authentication system documentation
- **[Security Summary](docs/SECURITY_SUMMARY.md)** - Security overview and quick reference
- **[Security Recommendations](docs/SECURITY_RECOMMENDATIONS.md)** - Detailed security best practices
- **[Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)** - Complete Docker deployment instructions
- **[Docker Update Summary](docs/DOCKER_UPDATE_SUMMARY.md)** - Docker configuration changes

### Security Tools
```bash
# Check your security configuration
python3 scripts/check_security.py

# Set up credentials interactively
./scripts/setup_credentials.sh

# Generate strong SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Docker Quick Commands
```bash
# Using the deployment script
./scripts/docker_deploy.sh start    # Start application
./scripts/docker_deploy.sh status   # Check status
./scripts/docker_deploy.sh logs     # View logs
./scripts/docker_deploy.sh security # Run security check

# Or use docker compose directly
docker compose up -d         # Start
docker compose logs -f web   # View logs
docker compose down          # Stop
```

## Development

### Running Tests

```bash
# Add your tests here
python -m pytest
```

### Making Changes

1. Edit the code
2. Test locally: `python app.py`
3. Run security check: `python3 scripts/check_security.py`
4. Rebuild Docker: `docker compose up -d --build`

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue or pull request.

---

**Happy Emailing! 📧**
