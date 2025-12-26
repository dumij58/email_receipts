"""
Enhanced Security Version of Email Receipts Application
This file demonstrates additional security features for production use.
To use this version, rename it to app.py (backup the original first).
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from email_service import EmailService
from models import db, User, SentEmail
import os
import csv
import logging
from io import StringIO
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
from functools import wraps
import secrets

# Load environment variables from .env file (only if not in Docker)
# Check multiple indicators for Docker environment
is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
if not is_docker:
    from dotenv import load_dotenv
    load_dotenv()

app = Flask(__name__)

# Debug mode configuration
DEBUG_MODE = os.environ.get('DEBUG', 'false').lower() == 'true'

# Configure logging to stdout for Docker
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[logging.StreamHandler()]
)
app.logger.setLevel(log_level)

if DEBUG_MODE:
    app.logger.debug(f"Loaded .env file for local development" if not is_docker else "Running in Docker - using environment variables from docker-compose")

# ============================================
# DATABASE CONFIGURATION
# ============================================

# Auto-detect database: SQLite for development, PostgreSQL for production
if os.environ.get('DATABASE_URL'):
    # PostgreSQL (production)
    database_url = os.environ.get('DATABASE_URL')
    # Handle postgres:// vs postgresql:// (required for SQLAlchemy 1.4+)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.logger.info("Using PostgreSQL database")
else:
    # SQLite (development)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'email_receipts.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.logger.info(f"Using SQLite database at {db_path}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 300,    # Recycle connections after 5 minutes
}

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

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
    # Content Security Policy - relaxed to allow browser extensions and devtools
    # Note: blob: added to script-src to prevent browser extension conflicts
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
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
# HELPER FUNCTIONS
# ============================================

def extract_transaction_id(message_id):
    """Extract transaction ID from Brevo message_id format: <[transaction_id]@smtp-relay.mailin.fr>"""
    if not message_id:
        return None
    try:
        # Format: <[transaction_id]@smtp-relay.mailin.fr>
        if message_id.startswith('<') and '@' in message_id:
            # Remove < and split by @
            transaction_part = message_id[1:].split('@')[0]
            return transaction_part
        return message_id
    except Exception:
        return message_id

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

# Note: User model is now defined in models.py and uses the database

@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID"""
    return db.session.get(User, int(user_id))

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
            if DEBUG_MODE:
                app.logger.debug(f"CSRF Check: Token received: {bool(token)}")
            if not token or not validate_csrf_token(token):
                app.logger.warning(f"CSRF validation failed for {request.path}")
                flash('Invalid security token. Please try again.', 'error')
                return redirect(request.url)
            if DEBUG_MODE:
                app.logger.debug("CSRF validation passed")
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
        
        # Query user from database
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Update last login timestamp
            from datetime import timezone
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            login_user(user, remember=True)
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
        if DEBUG_MODE:
            app.logger.debug("Processing email send request")
        try:
            recipient_email = sanitize_input(request.form.get('email', ''))
            recipient_name = sanitize_input(request.form.get('name', ''))
            purchase_date = sanitize_input(request.form.get('purchase_date', ''))
            edition = sanitize_input(request.form.get('edition', ''))
            
            # Digital edition fields (only if edition is digital)
            digital_link = sanitize_input(request.form.get('digital_link', '')) if edition == 'digital' else None
            digital_username = sanitize_input(request.form.get('digital_username', '')) if edition == 'digital' else None
            digital_password = sanitize_input(request.form.get('digital_password', '')) if edition == 'digital' else None
            
            if DEBUG_MODE:
                app.logger.debug(f"Form data received - Email: {recipient_email}, Name: {recipient_name}, Date: {purchase_date}, Edition: {edition}")
            
            # Validate inputs
            if not all([recipient_email, recipient_name, purchase_date, edition]):
                if DEBUG_MODE:
                    app.logger.debug("Missing required fields")
                flash('All required fields must be filled', 'error')
                return redirect(url_for('send_single'))
            
            # Validate edition
            if edition not in ['digital', 'print']:
                flash('Invalid edition type', 'error')
                return redirect(url_for('send_single'))
            
            # Validate digital fields if digital edition
            if edition == 'digital' and not all([digital_link, digital_username, digital_password]):
                flash('Digital edition requires link, username, and password', 'error')
                return redirect(url_for('send_single'))
            
            # Validate email format
            if not validate_email(recipient_email):
                if DEBUG_MODE:
                    app.logger.debug(f"Invalid email format: {recipient_email}")
                flash('Invalid email address format', 'error')
                return redirect(url_for('send_single'))
            
            # Send email
            if DEBUG_MODE:
                app.logger.debug(f"Calling email_service.send_single_receipt for {recipient_email}")
            success, message_id, error_message = email_service.send_single_receipt(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                magazine_name=magazine_name,
                purchase_amount=purchase_amount,
                purchase_date=purchase_date
            )
            
            # Extract transaction ID from message_id
            transaction_id = extract_transaction_id(message_id)
            
            # Log email to database
            try:
                from datetime import timezone
                sent_email = SentEmail(
                    user_id=current_user.id,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    purchase_date=purchase_date,
                    edition=edition,
                    digital_link=digital_link,
                    digital_username=digital_username,
                    digital_password=digital_password,
                    sent_at=datetime.now(timezone.utc),
                    transaction_id=transaction_id,
                    message_id=message_id,
                    status='success' if success else 'failed',
                    error_message=error_message
                )
                db.session.add(sent_email)
                db.session.commit()
                if DEBUG_MODE:
                    app.logger.debug(f"Email transaction logged to database (ID: {sent_email.id})")
            except Exception as e:
                app.logger.error(f"Failed to log email to database: {str(e)}")
                db.session.rollback()
            
            if DEBUG_MODE:
                app.logger.debug(f"Email send result: {success}")
            if success:
                flash(f'Email successfully sent to {recipient_email}', 'success')
            else:
                flash('Failed to send email. Please check your configuration.', 'error')
                
        except Exception as e:
            # Log error but don't expose details to user
            app.logger.error(f'Error sending email: {str(e)}', exc_info=True)
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
            
            # Parse CSV rows and store data for database logging
            recipients = []
            for row in csv_reader:
                edition = row.get('edition', 'print').lower()
                # Validate edition
                if edition not in ['digital', 'print']:
                    edition = 'print'
                
                recipient_data = {
                    'email': row.get('email'),
                    'name': row.get('name'),
                    'purchase_date': row.get('purchase_date'),
                    'edition': edition,
                    'digital_link': row.get('link', '') if edition == 'digital' else None,
                    'digital_username': row.get('username', '') if edition == 'digital' else None,
                    'digital_password': row.get('password', '') if edition == 'digital' else None
                }
                recipients.append(recipient_data)
            
            # Process bulk emails (use original email_service logic)
            csv_reader = csv.DictReader(StringIO(csv_content))
            results = email_service.send_bulk_receipts(csv_reader)
            
            # Log all emails to database
            try:
                from datetime import timezone
                for i, (recipient_email, recipient_name, success, message_id, error_message) in enumerate(results['results']):
                    # Get corresponding recipient data
                    recipient_data = recipients[i] if i < len(recipients) else {}
                    
                    # Extract transaction ID from message_id
                    transaction_id = extract_transaction_id(message_id)
                    
                    sent_email = SentEmail(
                        user_id=current_user.id,
                        recipient_email=recipient_email,
                        recipient_name=recipient_name,
                        purchase_date=recipient_data.get('purchase_date', datetime.now(timezone.utc).strftime('%Y-%m-%d')),
                        edition=recipient_data.get('edition', 'print'),
                        digital_link=recipient_data.get('digital_link'),
                        digital_username=recipient_data.get('digital_username'),
                        digital_password=recipient_data.get('digital_password'),
                        sent_at=datetime.now(timezone.utc),
                        transaction_id=transaction_id,
                        message_id=message_id,
                        status='success' if success else 'failed',
                        error_message=error_message
                    )
                    db.session.add(sent_email)
                db.session.commit()
                if DEBUG_MODE:
                    app.logger.debug(f"Logged {len(results['results'])} email transactions to database")
            except Exception as e:
                app.logger.error(f"Failed to log bulk emails to database: {str(e)}")
                db.session.rollback()
            
            flash(f'Bulk email completed: {results["success"]} sent, {results["failed"]} failed', 
                  'success' if results["failed"] == 0 else 'warning')
            
        except Exception as e:
            app.logger.error(f'Error processing bulk email: {str(e)}')
            flash('Error processing file. Please check the format.', 'error')
            
        return redirect(url_for('send_bulk'))
    
    return render_template('send_bulk.html')

@app.route('/sent-emails')
@login_required
def sent_emails():
    """View sent emails with pagination and filtering"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    # Validate per_page options
    if per_page not in [20, 50, 100]:
        per_page = 20
    
    # Build query
    query = SentEmail.query
    
    # Apply filters
    if status_filter:
        query = query.filter(SentEmail.status == status_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SentEmail.sent_at >= date_from_obj)
        except ValueError:
            flash('Invalid date format for date_from', 'error')
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire end date
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(SentEmail.sent_at <= date_to_obj)
        except ValueError:
            flash('Invalid date format for date_to', 'error')
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                SentEmail.recipient_email.ilike(search_pattern),
                SentEmail.recipient_name.ilike(search_pattern)
            )
        )
    
    # Order by sent_at descending (most recent first)
    query = query.order_by(SentEmail.sent_at.desc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('sent_emails.html',
                         emails=pagination.items,
                         pagination=pagination,
                         status_filter=status_filter,
                         date_from=date_from,
                         date_to=date_to,
                         search=search,
                         per_page=per_page)

@app.route('/sent-emails/export')
@login_required
def export_sent_emails():
    """Export sent emails to CSV with applied filters"""
    # Get same filters as sent_emails view
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    # Build query with same filters
    query = SentEmail.query
    
    if status_filter:
        query = query.filter(SentEmail.status == status_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SentEmail.sent_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(SentEmail.sent_at <= date_to_obj)
        except ValueError:
            pass
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                SentEmail.recipient_email.ilike(search_pattern),
                SentEmail.recipient_name.ilike(search_pattern)
            )
        )
    
    # Order by sent_at descending
    query = query.order_by(SentEmail.sent_at.desc())
    
    # Get all results (be careful with large datasets)
    emails = query.all()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Recipient Email', 'Recipient Name', 'Purchase Date', 'Edition',
        'Transaction ID', 'Sent At', 'Status', 'Error Message', 'Sent By',
        'Digital Link', 'Digital Username', 'Digital Password'
    ])
    
    # Write data rows
    for email in emails:
        email_dict = email.to_dict()
        writer.writerow([
            email_dict['id'],
            email_dict['recipient_email'],
            email_dict['recipient_name'],
            email_dict['purchase_date'],
            email_dict['edition'],
            email_dict['transaction_id'],
            email_dict['sent_at'],
            email_dict['status'],
            email_dict['error_message'],
            email_dict['sent_by'],
            email_dict.get('digital_link', ''),
            email_dict.get('digital_username', ''),
            email_dict.get('digital_password', '')
        ])
    
    # Prepare response
    output.seek(0)
    
    from io import BytesIO
    from datetime import timezone
    
    # Create BytesIO from string
    byte_output = BytesIO()
    byte_output.write(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    
    return send_file(
        byte_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'sent_emails_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'email-receipts',
        'brevo_configured': email_service.is_configured()
    })

@app.route('/api/email-config')
@login_required
def email_config():
    """Check Brevo/email configuration (debug endpoint)"""
    return jsonify({
        'email_service': 'Brevo (Sendinblue)',
        'api_key_set': bool(email_service.brevo_api_key),
        'sender_email': email_service.sender_email,
        'sender_name': email_service.sender_name,
        'magazine_name': email_service.magazine_name,
        'is_configured': email_service.is_configured()
    })

@app.route('/api/send-email', methods=['POST'])
@login_required
def api_send_email():
    """API endpoint for sending single email with enhanced validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        required_fields = ['email', 'name', 'purchase_date', 'edition']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate edition
        edition = data.get('edition', 'print').lower()
        if edition not in ['digital', 'print']:
            return jsonify({'error': 'Invalid edition type'}), 400
        
        # Validate digital fields if digital edition
        if edition == 'digital':
            if not all(field in data for field in ['digital_link', 'digital_username', 'digital_password']):
                return jsonify({'error': 'Digital edition requires link, username, and password'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Sanitize inputs
        recipient_email = sanitize_input(data['email'])
        recipient_name = sanitize_input(data['name'])
        purchase_date = sanitize_input(data['purchase_date'])
        digital_link = sanitize_input(data.get('digital_link', '')) if edition == 'digital' else None
        digital_username = sanitize_input(data.get('digital_username', '')) if edition == 'digital' else None
        digital_password = sanitize_input(data.get('digital_password', '')) if edition == 'digital' else None
        
        success, message_id, error_message = email_service.send_single_receipt(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            magazine_name=magazine_name,
            purchase_amount=purchase_amount,
            purchase_date=purchase_date
        )
        
        # Extract transaction ID from message_id
        transaction_id = extract_transaction_id(message_id)
        
        # Log email to database
        try:
            from datetime import timezone
            sent_email = SentEmail(
                user_id=current_user.id,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                purchase_date=purchase_date,
                edition=edition,
                digital_link=digital_link,
                digital_username=digital_username,
                digital_password=digital_password,
                sent_at=datetime.now(timezone.utc),
                transaction_id=transaction_id,
                message_id=message_id,
                status='success' if success else 'failed',
                error_message=error_message
            )
            db.session.add(sent_email)
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Failed to log email to database: {str(e)}")
            db.session.rollback()
        
        if success:
            return jsonify({'message': 'Email sent successfully', 'message_id': message_id}), 200
        else:
            return jsonify({'error': 'Failed to send email', 'details': error_message}), 500
            
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
    # Get port from environment variable, default to 5002 for local dev
    port = int(os.environ.get('FLASK_RUN_PORT', 5002))
    
    # Production mode check
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
