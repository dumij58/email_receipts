# Docker Deployment Guide - Enhanced Security

## Quick Start

### 1. Build and Run
```bash
# Build the image
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f web

# Check status
docker-compose ps
```

The application will be available at: **http://localhost:5001**

### 2. Configure Environment Variables

Before deploying, update your `.env` file:

```bash
# Security
SECRET_KEY=your-64-character-secret-key-here
ADMIN_USERNAME=your_secure_username
ADMIN_PASSWORD=your_strong_password

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Magazine Store

# Application Settings
MAGAZINE_NAME=SYNEXIS'25
PURCHASE_AMOUNT=1000.00
```

**Generate a strong SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Enhanced Security Features in Docker

### 1. Container Security
- ✅ Runs as non-root user (appuser)
- ✅ Minimal base image (python:3.11-slim)
- ✅ No unnecessary packages
- ✅ Health checks enabled

### 2. Network Security
- ✅ Isolated Docker network
- ✅ Only necessary ports exposed
- ✅ Environment variable isolation

### 3. Application Security
- ✅ Rate limiting (5 failed attempts = 5 min lockout)
- ✅ Security headers (XSS, clickjacking protection)
- ✅ CSRF protection
- ✅ Input validation
- ✅ Session security
- ✅ Password hashing

### 4. Logging
- ✅ Persistent logs in `./logs` directory
- ✅ Error tracking
- ✅ Security event logging

## Production Deployment

### Option 1: Behind Nginx Reverse Proxy (Recommended)

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://localhost:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Update `docker-compose.yml` to add nginx:
```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: email-receipts-app
    expose:
      - "5001"  # Only expose to nginx, not publicly
    environment:
      - FLASK_ENV=production
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - email-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: email-receipts-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - email-network

networks:
  email-network:
    driver: bridge
```

### Option 2: Direct Docker with Host Network

Update `docker-compose.yml`:
```yaml
services:
  web:
    network_mode: host
    # ... rest of configuration
```

⚠️ **Warning:** This is less secure. Use only for testing.

## Docker Commands

### Building
```bash
# Build the image
docker-compose build

# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build web
```

### Running
```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Monitoring
```bash
# View logs
docker-compose logs -f web

# View last 100 lines
docker-compose logs --tail=100 web

# Check status
docker-compose ps

# View resource usage
docker stats email-receipts-app

# Execute command in container
docker-compose exec web python check_security.py
```

### Maintenance
```bash
# Update application (zero-downtime)
docker-compose pull
docker-compose up -d --build

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Clean up old images
docker image prune -a

# View container details
docker inspect email-receipts-app
```

## Security Checklist for Docker Deployment

- [ ] Strong SECRET_KEY generated and set
- [ ] Default admin credentials changed
- [ ] SMTP credentials configured
- [ ] `.env` file secured (chmod 600)
- [ ] HTTPS/SSL configured (if internet-facing)
- [ ] Reverse proxy set up (nginx/Apache)
- [ ] Firewall configured
- [ ] Regular backups scheduled
- [ ] Log rotation configured
- [ ] Monitoring/alerting set up
- [ ] Container resource limits set

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs web

# Check if port is already in use
lsof -i :5001

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Can't connect to application
```bash
# Check if container is running
docker-compose ps

# Check health status
docker inspect email-receipts-app | grep -A 10 Health

# Test from inside container
docker-compose exec web curl http://localhost:5001/api/health
```

### Environment variables not loaded
```bash
# Verify .env file exists
ls -la .env

# Check environment in container
docker-compose exec web env | grep ADMIN

# Restart with fresh environment
docker-compose down
docker-compose up -d
```

### Logs not persisting
```bash
# Check volume mount
docker-compose exec web ls -la /app/logs

# Create logs directory if missing
mkdir -p logs
chmod 755 logs

# Restart container
docker-compose restart web
```

## Performance Optimization

### 1. Use Multi-Stage Build (Optional)
Create `Dockerfile.optimized`:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app
USER appuser
ENV PATH=/root/.local/bin:$PATH
EXPOSE 5001
CMD ["python", "app.py"]
```

### 2. Resource Limits
Add to `docker-compose.yml`:
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 3. Use Gunicorn for Production
Update CMD in Dockerfile:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", "app:app"]
```

## Monitoring & Logging

### 1. Log Aggregation
Use Docker logging drivers:
```yaml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 2. Health Monitoring
The health check runs every 30 seconds. View status:
```bash
docker inspect --format='{{json .State.Health}}' email-receipts-app | jq
```

### 3. Metrics Collection (Optional)
Add Prometheus monitoring:
```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

## Backup Strategy

### 1. Application Backup
```bash
# Backup script
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup environment file
cp .env "$BACKUP_DIR/"

# Backup logs
tar -czf "$BACKUP_DIR/logs.tar.gz" logs/

# Backup Docker images
docker save email-receipts-app:latest | gzip > "$BACKUP_DIR/image.tar.gz"

echo "Backup completed: $BACKUP_DIR"
```

### 2. Restore from Backup
```bash
#!/bin/bash
BACKUP_DIR=$1

# Restore environment
cp "$BACKUP_DIR/.env" .env

# Restore logs
tar -xzf "$BACKUP_DIR/logs.tar.gz"

# Restore image
docker load < "$BACKUP_DIR/image.tar.gz"

# Restart services
docker-compose up -d
```

## Security Best Practices

1. **Never commit `.env` to version control**
2. **Use secrets management** (Docker secrets, Vault, etc.)
3. **Keep images updated** regularly
4. **Scan for vulnerabilities** with `docker scan`
5. **Use specific image tags** instead of `latest`
6. **Implement log rotation** to prevent disk fill
7. **Set up alerts** for container failures
8. **Regular security audits** of dependencies
9. **Network segmentation** for multi-container apps
10. **Backup strategy** with automated testing

## Getting SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificate files will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f web`
2. Run security check: `docker-compose exec web python check_security.py`
3. Review documentation: `SECURITY_RECOMMENDATIONS.md`
4. Check Docker health: `docker-compose ps`
