# Quick Fix for Server Docker Login Issue

## The Problem
Login works locally but not redirecting after login in Docker on server.

## The Root Cause
The app wasn't loading the `.env` file properly in different environments.

## The Fix Applied

1. **Updated `app.py`** to conditionally load `.env`:
   - Loads `.env` file only when NOT in Docker (local development)
   - Docker gets environment variables from `docker-compose.yml`

2. **Fixed Docker Configuration**:
   - Container port: 8080 (internal)
   - Host port: 5858 (external)
   - Properly passes environment variables from `.env` file

3. **Added debugging output** to verify credentials are loaded correctly

## Deploy to Server

### Step 1: Ensure .env file exists on server
```bash
cd /path/to/email-receipts

# Create or edit .env file
nano .env
```

Add this content:
```
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=dumij58
ADMIN_PASSWORD=dumijfosmedia
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Magazine Store
MAGAZINE_NAME=SYNEXIS'25
PURCHASE_AMOUNT=1000.00
```

Generate SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Deploy with Docker
```bash
# Stop existing container
docker-compose down

# Pull latest code from git
git pull origin main

# Build fresh image
docker-compose build --no-cache

# Start container
docker-compose up -d

# Check logs
docker-compose logs -f web
```

### Step 3: Verify deployment
```bash
# Run verification script
./scripts/verify_docker.sh

# Or manually check:
# 1. Check container is running
docker-compose ps

# 2. Verify environment variables
docker-compose exec web env | grep ADMIN

# 3. Test health endpoint
curl http://localhost:5858/api/health

# 4. Test login
curl -i -X POST http://localhost:5858/login \
  -d "username=dumij58&password=dumijfosmedia" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Should see `Location: /` in the response headers (302 redirect).

### Step 4: Access from browser
```
http://YOUR_SERVER_IP:5858
```

Login with:
- Username: `dumij58`
- Password: `dumijfosmedia`

## Troubleshooting

### If login still not working:

1. **Check logs for DEBUG output:**
```bash
docker-compose logs web | grep DEBUG
```

Should see:
```
DEBUG: Loaded admin username: dumij58
```

2. **Verify environment in container:**
```bash
docker-compose exec web python3 -c "import os; print('User:', os.environ.get('ADMIN_USERNAME')); print('Pass:', os.environ.get('ADMIN_PASSWORD'))"
```

3. **Test from inside container:**
```bash
docker-compose exec web curl http://localhost:8080/login
```

4. **Check if .env is being read:**
```bash
# .env should be in same directory as docker-compose.yml
ls -la .env

# Check content
cat .env
```

5. **Complete rebuild:**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f web
```

### If can't access from external IP:

1. **Check firewall:**
```bash
# UFW
sudo ufw allow 5858/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 5858 -j ACCEPT
```

2. **Check port is listening:**
```bash
netstat -tuln | grep 5858
# or
ss -tuln | grep 5858
```

3. **Test from server itself first:**
```bash
curl http://localhost:5858
```

## Port Reference

- **Local development**: Port 5002 (python app.py)
- **Docker on server**: 
  - Internal: 8080
  - External: 5858
  - Access: `http://server-ip:5858`

## Files Changed

1. `app.py` - Added conditional .env loading and debug output
2. `docker-compose.yml` - Updated port mapping to 5858:8080
3. `Dockerfile` - Updated to use port 8080
4. Created `SERVER_DEPLOYMENT.md` - Full deployment guide
5. Created `scripts/verify_docker.sh` - Verification script

## Commit and Push

```bash
git add .
git commit -m "Fix Docker login redirect and environment loading"
git push origin main
```

Then on server:
```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
