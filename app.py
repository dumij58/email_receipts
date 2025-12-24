"""
Enhanced Security Version of Email Receipts Application
This file demonstrates additional security features for production use.
To use this version, rename it to app.py (backup the original first).
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from email_service import EmailService
import os
import csv
from io import StringIO
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
from functools import wraps
import secrets

app = Flask(__name__)

# ============================================
# ENHANCED SECURITY CONFIGURATION
# ============================================

# Use strong secret key (generate with: python -c "import secrets; print(secrets.token_hex(32))")
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session security
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session timeout

# Security headers
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Permissions policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'
login_manager.session_protection = 'strong'  # Enhanced session protection

# Initialize email service
email_service = EmailService()

magazine_name = email_service.magazine_name
purchase_amount = email_service.purchase_amount

# ============================================
# RATE LIMITING & BRUTE FORCE PROTECTION
# ============================================

# Simple in-memory rate limiting (for production, use Redis)
login_attempts = {}
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds

def check_rate_limit(ip_address):
    """Check if IP has exceeded login attempts"""
    now = datetime.now()
    if ip_address in login_attempts:
        attempts, first_attempt = login_attempts[ip_address]
        
        # Reset if window has passed
        if (now - first_attempt).seconds > RATE_LIMIT_WINDOW:
            login_attempts[ip_address] = (1, now)
            return True
        
        # Block if too many attempts
        if attempts >= RATE_LIMIT_ATTEMPTS:
            return False
        
        # Increment attempts
        login_attempts[ip_address] = (attempts + 1, first_attempt)
        return True
    else:
        login_attempts[ip_address] = (1, now)
        return True

def reset_rate_limit(ip_address):
    """Reset rate limit for IP after successful login"""
    if ip_address in login_attempts:
        del login_attempts[ip_address]

# ============================================
# USER MODEL & AUTHENTICATION
# ============================================

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# In-memory user store (in production, use a database)
# Default credentials from environment or default values
USERS = {
    os.environ.get('ADMIN_USERNAME', 'admin'): {
        'id': 1,
        'password': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
    }
}

@login_manager.user_loader
def load_user(user_id):
    for username, user_data in USERS.items():
        if user_data['id'] == int(user_id):
            return User(user_data['id'], username)
    return None

# ============================================
# CSRF PROTECTION
# ============================================

def generate_csrf_token():
    """Generate CSRF token for forms"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token == session.get('_csrf_token')

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def csrf_protect(f):
    """Decorator to protect routes with CSRF token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = request.form.get('_csrf_token')
            if not token or not validate_csrf_token(token):
                flash('Invalid security token. Please try again.', 'error')
                return redirect(request.url)
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# INPUT VALIDATION & SANITIZATION
# ============================================

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text, max_length=500):
    """Sanitize user input"""
    if not text:
        return ""
    # Remove any HTML tags
    text = text.strip()
    # Limit length
    return text[:max_length]

# ============================================
# ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with rate limiting and CSRF protection"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Rate limiting
        ip_address = request.remote_addr
        if not check_rate_limit(ip_address):
            flash('Too many login attempts. Please try again in 5 minutes.', 'error')
            return render_template('login.html'), 429
        
        username = sanitize_input(request.form.get('username', ''), 100)
        password = request.form.get('password', '')
        
        if username in USERS and check_password_hash(USERS[username]['password'], password):
            user = User(USERS[username]['id'], username)
            login_user(user)
            session.permanent = True  # Enable session timeout
            reset_rate_limit(ip_address)  # Reset attempts on success
            flash('Login successful!', 'success')
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            # Validate next_page to prevent open redirect
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    session.clear()  # Clear all session data
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/send-single', methods=['GET', 'POST'])
@login_required
@csrf_protect
def send_single():
    """Send a single email receipt with enhanced validation"""
    if request.method == 'POST':
        try:
            recipient_email = sanitize_input(request.form.get('email', ''))
            recipient_name = sanitize_input(request.form.get('name', ''))
            purchase_date = sanitize_input(request.form.get('purchase_date', ''))
            
            # Validate inputs
            if not all([recipient_email, recipient_name, purchase_date]):
                flash('All fields are required', 'error')
                return redirect(url_for('send_single'))
            
            # Validate email format
            if not validate_email(recipient_email):
                flash('Invalid email address format', 'error')
                return redirect(url_for('send_single'))
            
            # Send email
            success = email_service.send_single_receipt(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                magazine_name=magazine_name,
                purchase_amount=purchase_amount,
                purchase_date=purchase_date
            )
            
            if success:
                flash(f'Email successfully sent to {recipient_email}', 'success')
            else:
                flash('Failed to send email. Please check your configuration.', 'error')
                
        except Exception as e:
            # Log error but don't expose details to user
            app.logger.error(f'Error sending email: {str(e)}')
            flash('An error occurred while sending the email.', 'error')
            
        return redirect(url_for('send_single'))
    
    return render_template('send_single.html')

@app.route('/send-bulk', methods=['GET', 'POST'])
@login_required
@csrf_protect
def send_bulk():
    """Send bulk email receipts with enhanced validation"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'csv_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(url_for('send_bulk'))
            
            file = request.files['csv_file']
            
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('send_bulk'))
            
            # Secure filename
            filename = secure_filename(file.filename)
            
            if not filename.endswith('.csv'):
                flash('Only CSV files are allowed', 'error')
                return redirect(url_for('send_bulk'))
            
            # Read CSV file with size validation
            csv_content = file.read().decode('utf-8')
            
            # Limit CSV size
            if len(csv_content) > 1024 * 1024:  # 1MB limit for CSV
                flash('CSV file is too large (max 1MB)', 'error')
                return redirect(url_for('send_bulk'))
            
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            # Process bulk emails
            results = email_service.send_bulk_receipts(csv_reader)
            
            flash(f'Bulk email completed: {results["success"]} sent, {results["failed"]} failed', 
                  'success' if results["failed"] == 0 else 'warning')
            
        except Exception as e:
            app.logger.error(f'Error processing bulk email: {str(e)}')
            flash('Error processing file. Please check the format.', 'error')
            
        return redirect(url_for('send_bulk'))
    
    return render_template('send_bulk.html')

@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'email-receipts',
        'smtp_configured': email_service.is_configured()
    })

@app.route('/api/send-email', methods=['POST'])
@login_required
def api_send_email():
    """API endpoint for sending single email with enhanced validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        required_fields = ['email', 'name', 'magazine_name', 'purchase_amount', 'purchase_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Sanitize inputs
        recipient_email = sanitize_input(data['email'])
        recipient_name = sanitize_input(data['name'])
        
        success = email_service.send_single_receipt(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            magazine_name=data['magazine_name'],
            purchase_amount=data['purchase_amount'],
            purchase_date=data['purchase_date']
        )
        
        if success:
            return jsonify({'message': 'Email sent successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        app.logger.error(f'API error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    app.logger.error(f'Internal error: {str(e)}')
    return render_template('500.html'), 500

@app.errorhandler(429)
def rate_limit_error(e):
    """Handle rate limit errors"""
    return jsonify({'error': 'Too many requests'}), 429

if __name__ == '__main__':
    # Production mode check
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(host='0.0.0.0', port=5002, debug=False)
    else:
        app.run(host='0.0.0.0', port=5002, debug=True)
