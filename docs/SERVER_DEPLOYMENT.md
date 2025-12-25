# Server Deployment Guide

## Pre-Deployment Checklist

### 1. Ensure .env file exists on server
Create `.env` file in the project root with:

```bash
# Security
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=dumij58
ADMIN_PASSWORD=dumijfosmedia

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

Generate SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Set proper permissions
```bash
chmod 600 .env
```

## Docker Deployment Steps

### Step 1: Stop existing containers
```bash
docker-compose down
```

### Step 2: Remove old images (optional, for clean build)
```bash
docker rmi email-receipts-app:latest 2>/dev/null || true
```

### Step 3: Build the image
```bash
docker-compose build --no-cache
```

### Step 4: Start the application
```bash
docker-compose up -d
```

### Step 5: Check logs
```bash
docker-compose logs -f web
```

Look for:
- "DEBUG: Loaded admin username: dumij58"
- "Running on http://0.0.0.0:8080"

### Step 6: Verify environment variables loaded
```bash
docker-compose exec web env | grep ADMIN
```

Should show:
```
ADMIN_USERNAME=dumij58
ADMIN_PASSWORD=dumijfosmedia
```

### Step 7: Test the application
```bash
# From server
curl http://localhost:5858/api/health

# From browser
# Access: http://your-server-ip:5858
```

## Troubleshooting

### Issue: Can't access the web interface

**Check if container is running:**
```bash
docker-compose ps
```

**Check if port is accessible:**
```bash
netstat -tuln | grep 5858
```

**Test from inside container:**
```bash
docker-compose exec web curl http://localhost:8080/api/health
```

**Check firewall:**
```bash
# Allow port 5858
sudo ufw allow 5858/tcp
# Or for iptables
sudo iptables -A INPUT -p tcp --dport 5858 -j ACCEPT
```

### Issue: Login not redirecting

**Check environment variables:**
```bash
docker-compose exec web python3 -c "import os; print('Username:', os.environ.get('ADMIN_USERNAME')); print('Has password:', bool(os.environ.get('ADMIN_PASSWORD')))"
```

**Check logs for DEBUG output:**
```bash
docker-compose logs web | grep DEBUG
```

**Test login from server:**
```bash
curl -i -X POST http://localhost:5858/login \
  -d "username=dumij58&password=dumijfosmedia" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c /tmp/cookies.txt
```

Look for `Location:` header with redirect to `/`.

### Issue: .env file not being read

Docker Compose should automatically load .env file. Verify:

1. **.env file exists in same directory as docker-compose.yml:**
```bash
ls -la .env
```

2. **.env file has correct format (no spaces around =):**
```bash
cat .env
```

3. **Rebuild container after .env changes:**
```bash
docker-compose down
docker-compose up -d
```

### Issue: Port 5858 already in use

**Find what's using the port:**
```bash
sudo lsof -i :5858
```

**Kill the process or change port:**
```bash
# Option 1: Kill the process
sudo kill -9 <PID>

# Option 2: Change port in docker-compose.yml
# Change "5858:8080" to "5859:8080"
```

### Issue: Health check failing

**Check health status:**
```bash
docker inspect email-receipts-app | grep -A 10 Health
```

**Test health endpoint manually:**
```bash
docker-compose exec web python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/api/health').read())"
```

## Complete Redeployment (Clean Slate)

If everything is broken, start fresh:

```bash
# 1. Stop and remove everything
docker-compose down -v

# 2. Remove images
docker rmi $(docker images | grep email-receipts | awk '{print $3}')

# 3. Clean Docker cache
docker system prune -a

# 4. Verify .env file
cat .env

# 5. Build fresh
docker-compose build --no-cache

# 6. Start
docker-compose up -d

# 7. Watch logs
docker-compose logs -f web
```

## Testing Login

### From command line:
```bash
# Should return 302 redirect
curl -i -X POST http://localhost:5858/login \
  -d "username=dumij58&password=dumijfosmedia" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### From browser:
1. Go to `http://your-server-ip:5858`
2. Login with:
   - Username: `dumij58`
   - Password: `dumijfosmedia`
3. Should redirect to dashboard

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Can't connect to port 5858 | Check firewall, verify container is running |
| Login shows "Invalid credentials" | Verify .env file, check ADMIN_USERNAME and ADMIN_PASSWORD |
| No redirect after login | Check browser console for errors, verify cookie settings |
| Container exits immediately | Check logs with `docker-compose logs web` |
| Health check fails | Increase start_period in docker-compose.yml |

## Production Recommendations

1. **Use HTTPS with reverse proxy (nginx/traefik)**
2. **Set strong SECRET_KEY**
3. **Change default admin credentials**
4. **Set up log rotation**
5. **Enable firewall**
6. **Regular backups of .env file**
7. **Monitor container health**
8. **Set resource limits in docker-compose.yml**

## Quick Reference

```bash
# View logs
docker-compose logs -f web

# Restart container
docker-compose restart web

# Shell access
docker-compose exec web /bin/bash

# Check environment
docker-compose exec web env

# Stop
docker-compose down

# Start
docker-compose up -d

# Rebuild
docker-compose build --no-cache && docker-compose up -d
```

## Getting Help

1. Check logs: `docker-compose logs web`
2. Check container status: `docker-compose ps`
3. Verify environment: `docker-compose exec web env | grep ADMIN`
4. Test health: `curl http://localhost:5858/api/health`
