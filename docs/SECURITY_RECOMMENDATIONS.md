# Security Recommendations for Email Receipts Application

## Current Security Status

### ✅ Implemented (Basic Security)
- [x] Password hashing with Werkzeug
- [x] Session-based authentication with Flask-Login
- [x] Route protection with `@login_required`
- [x] Environment-based configuration
- [x] File size limits (16MB)
- [x] Secure filename handling

### ⚠️ Missing (Critical for Production)

## 1. **HTTPS/SSL (CRITICAL)**
**Priority: HIGHEST**

**Current Risk:** Credentials sent in plain text over the network

**Solution:**
```bash
# Use reverse proxy (nginx/Apache) with SSL certificate
# Get free SSL from Let's Encrypt:
sudo certbot --nginx -d yourdomain.com
```

**Configuration example (nginx):**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

## 2. **Rate Limiting & Brute Force Protection**
**Priority: HIGH**

**Current Risk:** Unlimited login attempts allow brute force attacks

**Solutions:**

### Option A: Simple (In-Memory) - Already in `app_enhanced_security.py`
- Tracks failed login attempts by IP
- Blocks after 5 failed attempts for 5 minutes
- ⚠️ Resets when server restarts

### Option B: Production (Flask-Limiter with Redis)
```bash
pip install Flask-Limiter redis
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per 5 minutes")
def login():
    # ... login logic
```

## 3. **CSRF Protection**
**Priority: HIGH**

**Current Risk:** Cross-Site Request Forgery attacks possible

**Solution:** Use Flask-WTF
```bash
pip install Flask-WTF
```

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

Add to forms:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

## 4. **Security Headers**
**Priority: MEDIUM-HIGH**

**Current Risk:** Missing protection against XSS, clickjacking, etc.

**Solution:** Already implemented in `app_enhanced_security.py`

Headers added:
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Content-Security-Policy` - Restricts resource loading
- `Referrer-Policy` - Controls referrer information
- `Permissions-Policy` - Restricts browser features

## 5. **Input Validation & Sanitization**
**Priority: HIGH**

**Current Risk:** Potential injection attacks, malformed data

**Improvements:**
- Email format validation ✅ (in enhanced version)
- Input length limits ✅ (in enhanced version)
- HTML escaping (Jinja2 does this automatically)
- SQL injection prevention (use parameterized queries if adding database)

## 6. **Session Security**
**Priority: MEDIUM-HIGH**

**Current Risk:** Session hijacking, fixation attacks

**Enhancements in `app_enhanced_security.py`:**
```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Auto logout
login_manager.session_protection = 'strong'  # Enhanced protection
```

## 7. **Logging & Monitoring**
**Priority: MEDIUM**

**Current Risk:** Security incidents undetected

**Solution:**
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

# Log security events
@app.route('/login', methods=['POST'])
def login():
    # ... existing code ...
    if failed_login:
        app.logger.warning(f'Failed login attempt from {request.remote_addr} for user {username}')
```

## 8. **Database-Backed User Management**
**Priority: MEDIUM (for scaling)**

**Current Risk:** In-memory users reset on restart, limited to one user

**Solution:** Use SQLAlchemy with PostgreSQL/MySQL
```bash
pip install Flask-SQLAlchemy psycopg2-binary
```

```python
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/dbname'
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
```

## 9. **Environment Variable Security**
**Priority: MEDIUM**

**Current Risk:** Secrets in `.env` file could be exposed

**Solutions:**
- Never commit `.env` to git ✅ (already in `.gitignore`)
- Use environment variable managers (Docker secrets, Kubernetes secrets)
- Use secret management services (AWS Secrets Manager, HashiCorp Vault)

## 10. **Additional Hardening**

### A. Strong Secret Key
```python
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=a1b2c3d4e5f6... # 64 character hex string
```

### B. File Upload Validation
```python
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

### C. API Authentication
```python
# Add API key authentication
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/send-email', methods=['POST'])
@require_api_key
def api_send_email():
    # ... existing code
```

### D. Account Lockout
```python
# Lock account after too many failed attempts
MAX_FAILED_ATTEMPTS = 5
account_locks = {}

def is_account_locked(username):
    if username in account_locks:
        lock_time, attempts = account_locks[username]
        if attempts >= MAX_FAILED_ATTEMPTS:
            if (datetime.now() - lock_time).seconds < 900:  # 15 min
                return True
            else:
                del account_locks[username]
    return False
```

## Quick Implementation Checklist

### Immediate (Before Going Live)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Change default admin credentials
- [ ] Generate strong SECRET_KEY
- [ ] Implement rate limiting
- [ ] Add CSRF protection
- [ ] Add security headers
- [ ] Set up logging

### Short Term (Within 1 Week)
- [ ] Implement session timeout
- [ ] Add input validation
- [ ] Set up monitoring/alerts
- [ ] Add error handling
- [ ] Test with security scanner (OWASP ZAP)

### Long Term (Within 1 Month)
- [ ] Migrate to database-backed users
- [ ] Add two-factor authentication
- [ ] Implement audit logging
- [ ] Set up automated backups
- [ ] Regular security audits

## Testing Your Security

### Manual Testing
```bash
# Test rate limiting
for i in {1..10}; do curl -X POST http://localhost:5001/login; done

# Test HTTPS redirect
curl -I http://yourdomain.com

# Test security headers
curl -I https://yourdomain.com
```

### Automated Security Scanning
```bash
# Install OWASP ZAP
# Run automated scan
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:5001
```

## Production Deployment Checklist

- [ ] HTTPS enabled with valid certificate
- [ ] Debug mode disabled (`FLASK_ENV=production`)
- [ ] Strong, unique SECRET_KEY set
- [ ] Default credentials changed
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Logging configured
- [ ] Error pages configured (don't expose stack traces)
- [ ] File upload validation enabled
- [ ] Session timeout configured
- [ ] Backups configured
- [ ] Monitoring/alerting set up
- [ ] Security scan completed

## Recommended Security Stack

```
┌─────────────────────────────────┐
│   Cloudflare / CDN (DDoS)       │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Nginx (SSL/TLS, Rate Limit)   │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Flask App (Enhanced Security) │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Database (Encrypted at rest)  │
└─────────────────────────────────┘
```

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Mozilla Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [Let's Encrypt SSL](https://letsencrypt.org/)

## Support

For security vulnerabilities, please report privately to the development team rather than creating public issues.
