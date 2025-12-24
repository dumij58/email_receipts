# Email Receipts Flask Application

A professional Flask application for sending email receipts to magazine buyers. Features a clean web interface for sending individual and bulk emails, with full Docker support for easy deployment.

## Features

- 📧 **Single Email Sending**: Send individual receipts with custom details
- 📬 **Bulk Email Sending**: Upload CSV files to send receipts to multiple customers
- 🎨 **Clean Web Interface**: Modern, responsive UI built with HTML/CSS
- 🔒 **Secure Configuration**: Environment-based SMTP credentials
- 🐳 **Docker Support**: Fully containerized with Docker and docker-compose
- 📊 **API Endpoints**: RESTful API for programmatic access
- ✅ **Professional Templates**: HTML email templates with receipt details

## Project Structure

```
email-receipts/
├── app.py                  # Main Flask application
├── email_service.py        # Email sending logic
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Dashboard
│   ├── send_single.html   # Single email form
│   └── send_bulk.html     # Bulk email form
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Prerequisites

- Python 3.11+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- SMTP email account (Gmail, Outlook, etc.)

## Setup Instructions

### 1. Clone or Download the Project

### 2. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your SMTP credentials:

```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Magazine Store
```

**For Gmail users**: You need to create an App Password:
1. Go to https://myaccount.google.com/apppasswords
2. Generate a new app password
3. Use that password in the `.env` file

### 3. Local Development Setup

#### Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Run the Application

```bash
python app.py
```

Visit: http://localhost:5000

### 4. Docker Deployment

#### Build and Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at: http://localhost:5000

#### Stop the Application

```bash
docker-compose down
```

#### View Logs

```bash
docker-compose logs -f
```

#### Rebuild After Changes

```bash
docker-compose up -d --build
```

## Usage

### Web Interface

1. **Dashboard** (`/`): Overview and navigation
2. **Send Single Email** (`/send-single`): Form for individual receipts
3. **Send Bulk Emails** (`/send-bulk`): CSV upload for batch sending

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
docker-compose up -d
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
| `SMTP_SERVER` | SMTP server address | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port | 587 |
| `SMTP_USERNAME` | Email account username | Required |
| `SMTP_PASSWORD` | Email account password | Required |
| `SENDER_EMAIL` | Sender email address | Same as SMTP_USERNAME |
| `SENDER_NAME` | Sender display name | Magazine Store |

## Troubleshooting

### Email Not Sending

1. **Check SMTP credentials**: Verify username and password in `.env`
2. **Gmail users**: Make sure you're using an App Password, not your regular password
3. **Firewall**: Ensure port 587 is open for SMTP
4. **Check logs**: `docker-compose logs -f` to see error messages

### Docker Issues

1. **Port already in use**: Change port in `docker-compose.yml`
2. **Build fails**: Run `docker-compose build --no-cache`
3. **Container won't start**: Check logs with `docker-compose logs`

## Security Notes

- Never commit `.env` file to version control
- Use strong secret keys in production
- Consider using SSL/TLS for SMTP (port 465)
- Implement rate limiting for production use
- Add authentication for web interface if needed

## Development

### Running Tests

```bash
# Add your tests here
python -m pytest
```

### Making Changes

1. Edit the code
2. Test locally: `python app.py`
3. Rebuild Docker: `docker-compose up -d --build`

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue or pull request.

---

**Happy Emailing! 📧**
