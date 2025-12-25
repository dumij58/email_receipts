# Utility Scripts

This folder contains utility scripts for managing and deploying the Email Receipts application.

## 📜 Available Scripts

### `check_security.py` 🔐
**Purpose:** Automated security configuration checker

**Usage:**
```bash
python3 scripts/check_security.py
```

**What it checks:**
- ✅ Environment file (.env) exists
- ✅ SECRET_KEY is secure (32+ characters)
- ✅ Admin credentials changed from defaults
- ✅ Brevo API configuration
- ✅ File permissions (.env should be 600)
- ✅ Required dependencies installed
- ✅ Debug mode settings
- ✅ .gitignore configuration

**Output:**
- Security score (0-100%)
- Detailed check results with ✓/✗
- Specific recommendations for failures
- Color-coded status (GREEN=good, RED=critical, YELLOW=warning)

**Example output:**
```
Email Receipts - Security Configuration Check
============================================================

1. Environment Configuration
✓ Environment file (.env) exists

2. Secret Key Security
✗ SECRET_KEY is set and secure
⚠  Generate a strong SECRET_KEY:
   python -c "import secrets; print(secrets.token_hex(32))"

Security Score: 7/10 (70%)
Status: NEEDS IMPROVEMENT
```

---

### `setup_credentials.sh` 🔑
**Purpose:** Interactive credential setup wizard

**Usage:**
```bash
./scripts/setup_credentials.sh
```

**What it does:**
1. Creates `.env` file from `.env.example` if needed
2. Prompts for admin username (default: admin)
3. Prompts for admin password (default: admin123)
4. Updates `.env` file with new credentials
5. Provides security reminders

**Features:**
- Safe: Won't overwrite existing `.env` without confirmation
- Secure: Password input is hidden (silent mode)
- Compatible: Works on both macOS and Linux
- Helpful: Provides next steps after setup

**Example session:**
```
🔐 Email Receipts - Security Setup
====================================

✓ Created .env file from .env.example

📝 Let's set up your admin credentials...

Enter admin username (press Enter for 'admin'): myuser
Enter admin password (press Enter for 'admin123'): 

✓ Credentials saved to .env file

⚠️  IMPORTANT SECURITY NOTES:
   - Never commit your .env file to version control
   - Use strong passwords in production
```

---

### `docker_deploy.sh` 🐳
**Purpose:** Automated Docker deployment and management

**Usage:**
```bash
./scripts/docker_deploy.sh [command]
```

**Commands:**

| Command | Description |
|---------|-------------|
| `start` | Build and start the application |
| `stop` | Stop the application |
| `restart` | Restart the application |
| `rebuild` | Rebuild from scratch and start |
| `logs` | Show application logs (follow mode) |
| `status` | Show application status and health |
| `security` | Run security check inside container |
| `backup-logs` | Backup application logs |
| `help` | Show help message |

**Features:**
- 🎨 Color-coded output for better readability
- ✅ Automatic environment file checking
- 🏥 Health check verification after start
- 📊 Detailed status information
- 🔒 Docker and docker compose validation
- 🚀 Zero-downtime restart support

**Examples:**
```bash
# Start application
./scripts/docker_deploy.sh start

# Check status with health info
./scripts/docker_deploy.sh status

# View logs in real-time
./scripts/docker_deploy.sh logs

# Rebuild everything
./scripts/docker_deploy.sh rebuild

# Run security check
./scripts/docker_deploy.sh security
```

**Output example:**
```
🚀 Starting Email Receipts Application...
✓ Application started successfully!
ℹ Access the application at: http://localhost:5001
ℹ View logs with: docker compose logs -f web
ℹ Checking application health...
✓ Application is healthy!
```

---

## 🚀 Quick Start Workflow

### First Time Setup
```bash
# 1. Set up credentials
./scripts/setup_credentials.sh

# 2. Check security
python3 scripts/check_security.py

# 3. Start application
./scripts/docker_deploy.sh start
```

### Daily Development
```bash
# Check status
./scripts/docker_deploy.sh status

# View logs
./scripts/docker_deploy.sh logs

# Restart after changes
./scripts/docker_deploy.sh restart
```

### Before Deployment
```bash
# Run security check
python3 scripts/check_security.py

# Ensure everything passes
# Fix any issues identified

# Deploy
./scripts/docker_deploy.sh rebuild
```

---

## 🔧 Script Requirements

### `check_security.py`
**Dependencies:**
- Python 3.6+
- Standard library only (os, sys, datetime)

**Permissions:** Read access to project files

### `setup_credentials.sh`
**Dependencies:**
- Bash shell (zsh compatible)
- sed command (macOS/Linux)

**Permissions:** 
- Read/write access to `.env` file
- Executable (`chmod +x`)

### `docker_deploy.sh`
**Dependencies:**
- Docker
- Docker Compose
- curl (for health checks)
- Bash shell

**Permissions:** 
- Docker daemon access
- Executable (`chmod +x`)

---

## 📝 Making Scripts Executable

If scripts aren't executable:

```bash
chmod +x scripts/setup_credentials.sh
chmod +x scripts/docker_deploy.sh
```

Python scripts can be run directly:
```bash
python3 scripts/check_security.py
```

---

## 🎯 Use Cases

### Security Audit
```bash
# Before deployment
python3 scripts/check_security.py

# Fix issues, then re-check
python3 scripts/check_security.py
```

### Fresh Installation
```bash
# Complete setup
./scripts/setup_credentials.sh
python3 scripts/check_security.py
./scripts/docker_deploy.sh start
```

### Production Deployment
```bash
# Security check first
python3 scripts/check_security.py

# Ensure score is 80%+ 
# Then deploy
./scripts/docker_deploy.sh rebuild
```

### Troubleshooting
```bash
# Check status
./scripts/docker_deploy.sh status

# View logs
./scripts/docker_deploy.sh logs

# Run security check
./scripts/docker_deploy.sh security
```

---

## 🔒 Security Notes

### check_security.py
- Safe to run anytime
- Read-only operations
- No modifications to files
- Outputs sensitive info (use with caution in logs)

### setup_credentials.sh
- Modifies `.env` file
- Asks for confirmation before overwriting
- Password input is hidden
- Creates `.env` from `.env.example` if needed

### docker_deploy.sh
- Requires Docker daemon access
- Can start/stop/rebuild containers
- Validates prerequisites before running
- Safe to use in production

---

## 💡 Tips

1. **Always run security check before deployment:**
   ```bash
   python3 scripts/check_security.py
   ```

2. **Use setup script for initial configuration:**
   ```bash
   ./scripts/setup_credentials.sh
   ```

3. **Automate deployments with docker_deploy.sh:**
   ```bash
   ./scripts/docker_deploy.sh rebuild
   ```

4. **Monitor logs regularly:**
   ```bash
   ./scripts/docker_deploy.sh logs
   ```

5. **Check application health:**
   ```bash
   ./scripts/docker_deploy.sh status
   ```

---

## 🐛 Troubleshooting

### Script won't execute
```bash
# Make executable
chmod +x scripts/*.sh

# Or run with shell
bash scripts/docker_deploy.sh start
```

### check_security.py errors
```bash
# Ensure Python 3 is installed
python3 --version

# Run from project root
cd /path/to/email-receipts
python3 scripts/check_security.py
```

### docker_deploy.sh can't find docker
```bash
# Check Docker installation
docker --version
docker compose --version

# Start Docker daemon
# On macOS: Open Docker Desktop
# On Linux: sudo systemctl start docker
```

### Permission denied errors
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix .env permissions
chmod 600 .env

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
# Then logout and login
```

---

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [Security Summary](../docs/SECURITY_SUMMARY.md) - Security overview
- [Docker Deployment Guide](../docs/DOCKER_DEPLOYMENT.md) - Docker details
- [Login Feature Guide](../docs/LOGIN_FEATURE.md) - Authentication

---

## 🔄 Script Maintenance

### Adding New Scripts

1. Create script in `scripts/` folder
2. Make executable: `chmod +x scripts/new_script.sh`
3. Add documentation here
4. Update main README if needed
5. Test thoroughly before committing

### Modifying Existing Scripts

1. Test changes locally first
2. Update this README if behavior changes
3. Update examples if needed
4. Maintain backward compatibility when possible

---

**All scripts are maintained and tested for:**
- macOS (tested on macOS 14+)
- Linux (tested on Ubuntu 22.04+)
- Docker Desktop
- Docker Engine

For issues or improvements, open an issue or pull request.
