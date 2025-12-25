# Login Feature - Quick Reference

## Overview
A secure login system has been added to protect the email receipts application using Flask-Login.

## Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

## Configuration

### Environment Variables (.env)
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SECRET_KEY=your-secret-key-here
```

### Quick Setup
Run the setup script to configure credentials:
```bash
./scripts/setup_credentials.sh
```

## Protected Routes
All routes now require authentication except `/login`:
- `/` - Dashboard (requires login)
- `/send-single` - Send single email (requires login)
- `/send-bulk` - Send bulk emails (requires login)
- `/api/send-email` - API endpoint (requires login)
- `/logout` - Logout (requires login)

## Features
- ✅ Session-based authentication using Flask-Login
- ✅ Password hashing with Werkzeug
- ✅ Automatic redirect to login page for unauthenticated users
- ✅ "Remember me" session management
- ✅ Flash messages for login errors
- ✅ Logout button in navigation bar
- ✅ Next page redirect after successful login

## User Interface
- **Login Page**: Clean, modern design with SYNEXIS'25 branding
- **Logout Button**: Red logout button appears in navigation when logged in
- **Flash Messages**: Success/error messages for login attempts

## Security Recommendations

### For Development
- Default credentials are fine for local testing
- Keep `.env` out of version control (already in `.gitignore`)

### For Production
1. **Change credentials immediately**:
   ```env
   ADMIN_USERNAME=your_secure_username
   ADMIN_PASSWORD=your_very_strong_password_here
   ```

2. **Use strong SECRET_KEY**:
   ```python
   # Generate a secure key:
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Use HTTPS**: Deploy behind a reverse proxy with SSL/TLS

4. **Consider additional security**:
   - Rate limiting on login attempts
   - Account lockout after failed attempts
   - Two-factor authentication
   - Database-backed user management

## Files Modified
- `app.py` - Added Flask-Login integration, User model, login/logout routes
- `templates/login.html` - New login page template
- `templates/base.html` - Added logout button to navigation
- `requirements.txt` - Added Flask-Login==0.6.3
- `.env.example` - Added ADMIN_USERNAME and ADMIN_PASSWORD
- `README.md` - Updated with login documentation

## Installation

### Install Dependencies
```bash
pip install -r requirements.txt
```

### With Docker
```bash
docker compose up -d --build
```

The new Flask-Login dependency will be automatically installed.

## Testing

1. Start the application
2. Navigate to http://localhost:5000
3. You'll be redirected to `/login`
4. Enter credentials (admin/admin123)
5. You'll be redirected to the dashboard
6. Click "Logout" in the navigation to log out

## Troubleshooting

### Issue: Import error for flask_login
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Can't log in
**Solution**: Check credentials in `.env` file match what you're entering

### Issue: Redirects to login after already logged in
**Solution**: Clear browser cookies or check SECRET_KEY is set correctly

## Future Enhancements
- [ ] Database-backed user management
- [ ] User registration system
- [ ] Password reset functionality
- [ ] Role-based access control (admin, user, etc.)
- [ ] Login attempt rate limiting
- [ ] Session timeout configuration
- [ ] Two-factor authentication
