# Docker Quick Start Guide

## Port Configuration
- **Host Port**: 5858 (access the app from your browser)
- **Container Port**: 8080 (internal Flask app port)
- **Access URL**: http://localhost:5858

## Quick Commands

### 1. Stop any running containers
```bash
docker-compose down
```

### 2. Build the Docker image
```bash
docker-compose build --no-cache
```

### 3. Start the application
```bash
docker-compose up -d
```

### 4. Check logs
```bash
docker-compose logs -f web
```

### 5. Check container status
```bash
docker-compose ps
```

### 6. Test the application
```bash
# From your browser
open http://localhost:5858

# From terminal
curl http://localhost:5858/api/health
```

## Troubleshooting

### Container won't start
```bash
# Check detailed logs
docker-compose logs web

# Check if container is running
docker ps -a

# Restart from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Can't access the web interface
```bash
# Check if port 5858 is in use
lsof -i :5858

# Check container networking
docker-compose exec web python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/api/health').read())"

# Check if Flask is listening
docker-compose exec web netstat -tuln | grep 8080
```

### Port already in use
```bash
# Find what's using port 5858
lsof -i :5858

# Kill the process (replace PID with actual process ID)
kill -9 PID

# Or use a different port by editing docker-compose.yml
# Change "5858:8080" to "5859:8080" for example
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Security
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password

# Brevo Email Configuration
BREVO_API_KEY=your-brevo-api-key
SENDER_EMAIL=your-verified-email@example.com
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Magazine Store

# Application Settings
MAGAZINE_NAME=SYNEXIS'25
PURCHASE_AMOUNT=1000.00
```

Generate a strong SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Docker Commands Reference

```bash
# Build
docker-compose build

# Start (detached mode)
docker-compose up -d

# Start (with logs)
docker-compose up

# Stop
docker-compose stop

# Restart
docker-compose restart

# Stop and remove
docker-compose down

# View logs (follow)
docker-compose logs -f web

# View logs (last 100 lines)
docker-compose logs --tail=100 web

# Execute command in container
docker-compose exec web python check_security.py

# Shell access
docker-compose exec web /bin/bash
```

## Health Check

The container includes a health check that runs every 30 seconds:

```bash
# View health status
docker inspect email-receipts-app | grep -A 10 Health

# Or using docker-compose
docker-compose ps
```

## Logs Location

Logs are persisted in the `./logs` directory on your host machine, mapped to `/app/logs` in the container.

## Default Login Credentials

- **Username**: admin (or set via ADMIN_USERNAME)
- **Password**: admin123 (or set via ADMIN_PASSWORD)

⚠️ **Change these in production!**
