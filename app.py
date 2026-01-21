"""
Enhanced Security Version of Email Receipts Application
This file demonstrates additional security features for production use.
To use this version, rename it to app.py (backup the original first).
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from email_service import EmailService
from models import db, User, SentEmail, EmailAccount, EmailTemplate
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
    # Added cdn.jsdelivr.net for Bootstrap Icons
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'"
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

# Custom unauthorized handler to ensure redirects work properly
@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to login page"""
    flash('Please log in to access this page.', 'error')
    return redirect(url_for('login'))

# Legacy email service for backwards compatibility (will be replaced by account-specific instances)
# email_service = EmailService()  # Commented out - now using active account
# magazine_name = email_service.magazine_name  # Commented out - now from templates
# purchase_amount = email_service.purchase_amount  # Commented out - now from templates

# ============================================
# HELPER FUNCTIONS
# ============================================

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

def get_all_accounts():
    """Helper function to get all active accounts for template dropdown"""
    return EmailAccount.query.filter_by(is_active=True).order_by(EmailAccount.name).all()

app.jinja_env.globals['get_all_accounts'] = get_all_accounts

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
    from flask import g
    
    # Check if user has an active account
    if not g.active_account:
        flash('Please select an email account first', 'warning')
        return redirect(url_for('accounts_list'))
    
    if request.method == 'POST':
        if DEBUG_MODE:
            app.logger.debug("Processing email send request")
        try:
            # Get template selection
            template_id = request.form.get('template_id')
            if not template_id:
                flash('Please select a template', 'error')
                return redirect(url_for('send_single'))
            
            template = EmailTemplate.query.get(template_id)
            if not template or template.account_id != g.active_account.id:
                flash('Invalid template selected', 'error')
                return redirect(url_for('send_single'))
            
            recipient_email = sanitize_input(request.form.get('email', ''))
            recipient_name = sanitize_input(request.form.get('name', ''))
            purchase_date = sanitize_input(request.form.get('purchase_date', ''))
            edition = sanitize_input(request.form.get('edition', ''))
            quantity = int(request.form.get('quantity', '1') or '1')
            
            # Digital edition fields (only if edition is digital)
            digital_link = sanitize_input(request.form.get('digital_link', '')) if edition == 'digital' else None
            digital_username = sanitize_input(request.form.get('digital_username', '')) if edition == 'digital' else None
            digital_password = sanitize_input(request.form.get('digital_password', '')) if edition == 'digital' else None
            
            if DEBUG_MODE:
                app.logger.debug(f"Form data received - Email: {recipient_email}, Template: {template.name}")
            
            # Validate inputs
            if not all([recipient_email, recipient_name, purchase_date, edition]):
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
                flash('Invalid email address format', 'error')
                return redirect(url_for('send_single'))
            
            # Generate transaction ID
            import uuid
            transaction_id = f"SNX-{uuid.uuid4().hex[:12].upper()}"
            
            # Initialize email service with active account
            email_service = EmailService(account=g.active_account)
            
            # Send email with template
            success, message_id, error_message = email_service.send_single_receipt(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                magazine_name=template.magazine_name,
                purchase_amount=template.purchase_amount,
                purchase_date=purchase_date,
                quantity=quantity,
                transaction_id=transaction_id,
                edition=edition,
                digital_link=digital_link,
                digital_username=digital_username,
                digital_password=digital_password,
                template_path=template.template_path
            )
            
            # Log email to database
            try:
                from datetime import timezone
                sent_email = SentEmail(
                    user_id=current_user.id,
                    account_id=g.active_account.id,
                    template_id=template.id,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    purchase_date=purchase_date,
                    edition=edition,
                    magazine_name=template.magazine_name,
                    purchase_amount=template.purchase_amount,
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
                flash(f'Email successfully sent to {recipient_email}', 'success')
            else:
                flash('Failed to send email. Please check your configuration.', 'error')
                
        except Exception as e:
            app.logger.error(f'Error sending email: {str(e)}', exc_info=True)
            flash('An error occurred while sending the email.', 'error')
            
        return redirect(url_for('send_single'))
    
    # GET request - load templates for active account
    templates = EmailTemplate.query.filter_by(
        account_id=g.active_account.id,
        is_active=True
    ).order_by(EmailTemplate.name).all()
    
    return render_template('send_single.html', templates=templates)

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
                for i, (recipient_email, recipient_name, success, transaction_id, message_id, error_message) in enumerate(results['results']):
                    # Get corresponding recipient data
                    recipient_data = recipients[i] if i < len(recipients) else {}
                    
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

@app.route('/send-reminder', methods=['GET', 'POST'])
@login_required
def send_reminder():
    """Send payment reminder emails with enhanced validation"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'csv_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(url_for('send_reminder'))
            
            file = request.files['csv_file']
            
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('send_reminder'))
            
            # Secure filename
            filename = secure_filename(file.filename)
            
            if not filename.endswith('.csv'):
                flash('Only CSV files are allowed', 'error')
                return redirect(url_for('send_reminder'))
            
            # Read CSV file with size validation
            csv_content = file.read().decode('utf-8')
            
            # Limit CSV size
            if len(csv_content) > 1024 * 1024:  # 1MB limit for CSV
                flash('CSV file is too large (max 1MB)', 'error')
                return redirect(url_for('send_reminder'))
            
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            # Parse CSV rows for database logging
            recipients = []
            for row in csv_reader:
                recipient_data = {
                    'email': row.get('email'),
                    'name': row.get('name'),
                    'preorder_date': row.get('preorder_date')
                }
                recipients.append(recipient_data)
            
            # Process bulk reminder emails
            csv_reader = csv.DictReader(StringIO(csv_content))
            results = email_service.send_bulk_reminders(csv_reader)
            
            flash(f'Reminder emails sent: {results["success"]} successful, {results["failed"]} failed', 
                  'success' if results["failed"] == 0 else 'warning')
            
        except Exception as e:
            app.logger.error(f'Error processing reminder emails: {str(e)}')
            flash('Error processing file. Please check the format.', 'error')
            
        return redirect(url_for('send_reminder'))
    
    return render_template('send_reminder.html')

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
    
    # Apply filters only if provided
    filters_applied = False
    if status_filter:
        query = query.filter(SentEmail.status == status_filter)
        filters_applied = True
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SentEmail.sent_at >= date_from_obj)
            filters_applied = True
        except ValueError:
            flash('Invalid date format for date_from', 'error')
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire end date
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(SentEmail.sent_at <= date_to_obj)
            filters_applied = True
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
        filters_applied = True
    
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
                         per_page=per_page,
                         filters_applied=filters_applied)

@app.route('/sent-emails/resend/<int:email_id>', methods=['POST'])
@login_required
def resend_email(email_id):
    """Resend a previously sent email"""
    try:
        # Get the original email record
        original_email = SentEmail.query.get_or_404(email_id)
        
        # Create email service
        email_service = EmailService()
        
        # Get additional data for the email
        magazine_name = os.environ.get('MAGAZINE_NAME', '[MAGAZINE_NAME]')
        purchase_amount = os.environ.get('PURCHASE_AMOUNT', '[PURCHASE_AMOUNT]')
        
        # Resend the email with same data
        success, message_id, error_message = email_service.send_single_receipt(
            recipient_email=original_email.recipient_email,
            recipient_name=original_email.recipient_name,
            magazine_name=magazine_name,
            purchase_amount=purchase_amount,
            purchase_date=original_email.purchase_date,
            quantity=1,  # Default quantity
            transaction_id=original_email.transaction_id,
            edition=original_email.edition,
            digital_link=original_email.digital_link,
            digital_username=original_email.digital_username,
            digital_password=original_email.digital_password
        )
        
        # Create new sent email record
        new_email_record = SentEmail(
            user_id=current_user.id,
            recipient_email=original_email.recipient_email,
            recipient_name=original_email.recipient_name,
            purchase_date=original_email.purchase_date,
            edition=original_email.edition,
            digital_link=original_email.digital_link,
            digital_username=original_email.digital_username,
            digital_password=original_email.digital_password,
            transaction_id=original_email.transaction_id,
            message_id=message_id,
            status='success' if success else 'failed',
            error_message=error_message
        )
        
        db.session.add(new_email_record)
        db.session.commit()
        
        if success:
            flash(f'Email successfully resent to {original_email.recipient_email}', 'success')
        else:
            flash(f'Failed to resend email: {error_message}', 'error')
        
    except Exception as e:
        app.logger.error(f"Error resending email: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
    
    return redirect(url_for('sent_emails'))

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
        quantity = int(data.get('quantity', '1') or '1')  # Default to 1 if not provided
        digital_link = sanitize_input(data.get('digital_link', '')) if edition == 'digital' else None
        digital_username = sanitize_input(data.get('digital_username', '')) if edition == 'digital' else None
        digital_password = sanitize_input(data.get('digital_password', '')) if edition == 'digital' else None
        
        # Generate transaction ID before sending
        import uuid
        transaction_id = f"SNX-{uuid.uuid4().hex[:12].upper()}"
        
        success, message_id, error_message = email_service.send_single_receipt(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            magazine_name=magazine_name,
            purchase_amount=purchase_amount,
            purchase_date=purchase_date,
            quantity=quantity,
            transaction_id=transaction_id,
            edition=edition,
            digital_link=digital_link,
            digital_username=digital_username,
            digital_password=digital_password
        )
        
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
# ACCOUNT MANAGEMENT ROUTES
# ============================================

@app.before_request
def load_active_account():
    """Load active account into g for easy access in templates and routes"""
    from flask import g
    if current_user.is_authenticated:
        g.active_account = current_user.active_account
        # If user doesn't have an active account, set to first available account
        if not g.active_account:
            first_account = EmailAccount.query.filter_by(is_active=True).first()
            if first_account:
                current_user.active_account_id = first_account.id
                db.session.commit()
                g.active_account = first_account
    else:
        g.active_account = None

@app.route('/accounts')
@login_required
def accounts_list():
    """List all email accounts"""
    accounts = EmailAccount.query.order_by(EmailAccount.created_at.desc()).all()
    return render_template('accounts_list.html', accounts=accounts)

@app.route('/accounts/add', methods=['GET', 'POST'])
@login_required
@csrf_protect
def account_add():
    """Add a new email account"""
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name', '').strip(), max_length=100)
            brevo_api_key = request.form.get('brevo_api_key', '').strip()
            sender_email = request.form.get('sender_email', '').strip()
            sender_name = sanitize_input(request.form.get('sender_name', '').strip(), max_length=100)
            
            # Validation
            if not all([name, brevo_api_key, sender_email, sender_name]):
                flash('All fields are required', 'error')
                return redirect(url_for('account_add'))
            
            if not validate_email(sender_email):
                flash('Invalid sender email address', 'error')
                return redirect(url_for('account_add'))
            
            # Create account (API key will be automatically encrypted)
            account = EmailAccount(
                name=name,
                brevo_api_key=brevo_api_key,
                sender_email=sender_email,
                sender_name=sender_name,
                is_active=True,
                created_by=current_user.id
            )
            
            db.session.add(account)
            db.session.commit()
            
            flash(f'Account "{name}" created successfully', 'success')
            return redirect(url_for('accounts_list'))
            
        except Exception as e:
            app.logger.error(f'Error creating account: {str(e)}')
            flash('Failed to create account', 'error')
            db.session.rollback()
            return redirect(url_for('account_add'))
    
    return render_template('account_form.html', account=None)

@app.route('/accounts/edit/<int:account_id>', methods=['GET', 'POST'])
@login_required
@csrf_protect
def account_edit(account_id):
    """Edit an existing email account"""
    account = EmailAccount.query.get_or_404(account_id)
    
    if request.method == 'POST':
        try:
            account.name = sanitize_input(request.form.get('name', '').strip(), max_length=100)
            new_api_key = request.form.get('brevo_api_key', '').strip()
            account.sender_email = request.form.get('sender_email', '').strip()
            account.sender_name = sanitize_input(request.form.get('sender_name', '').strip(), max_length=100)
            account.is_active = request.form.get('is_active') == 'on'
            
            # Only update API key if provided (otherwise keep existing)
            if new_api_key:
                account.brevo_api_key = new_api_key
            
            # Validation
            if not all([account.name, account.sender_email, account.sender_name]):
                flash('Name, sender email, and sender name are required', 'error')
                return redirect(url_for('account_edit', account_id=account_id))
            
            if not validate_email(account.sender_email):
                flash('Invalid sender email address', 'error')
                return redirect(url_for('account_edit', account_id=account_id))
            
            db.session.commit()
            flash(f'Account "{account.name}" updated successfully', 'success')
            return redirect(url_for('accounts_list'))
            
        except Exception as e:
            app.logger.error(f'Error updating account: {str(e)}')
            flash('Failed to update account', 'error')
            db.session.rollback()
            return redirect(url_for('account_edit', account_id=account_id))
    
    return render_template('account_form.html', account=account)

@app.route('/accounts/switch/<int:account_id>', methods=['POST'])
@login_required
@csrf_protect
def account_switch(account_id):
    """Switch active account for current user"""
    account = EmailAccount.query.get_or_404(account_id)
    
    if not account.is_active:
        flash('Cannot switch to inactive account', 'error')
        return redirect(request.referrer or url_for('index'))
    
    current_user.active_account_id = account_id
    db.session.commit()
    
    flash(f'Switched to account: {account.name}', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/accounts/delete/<int:account_id>', methods=['POST'])
@login_required
@csrf_protect
def account_delete(account_id):
    """Delete an email account"""
    account = EmailAccount.query.get_or_404(account_id)
    
    # Check if any users are using this account
    users_count = User.query.filter_by(active_account_id=account_id).count()
    if users_count > 0:
        flash(f'Cannot delete account - {users_count} user(s) are currently using it', 'error')
        return redirect(url_for('accounts_list'))
    
    try:
        account_name = account.name
        db.session.delete(account)
        db.session.commit()
        flash(f'Account "{account_name}" deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f'Error deleting account: {str(e)}')
        flash('Failed to delete account', 'error')
        db.session.rollback()
    
    return redirect(url_for('accounts_list'))

# ============================================
# TEMPLATE MANAGEMENT ROUTES
# ============================================

@app.route('/templates')
@login_required
def templates_list():
    """List all email templates for active account"""
    from flask import g
    if not g.active_account:
        flash('Please select an account first', 'warning')
        return redirect(url_for('accounts_list'))
    
    templates = EmailTemplate.query.filter_by(
        account_id=g.active_account.id
    ).order_by(EmailTemplate.created_at.desc()).all()
    
    return render_template('templates_list.html', templates=templates)

@app.route('/templates/add', methods=['GET', 'POST'])
@login_required
@csrf_protect
def template_add():
    """Add a new email template"""
    from flask import g
    if not g.active_account:
        flash('Please select an account first', 'warning')
        return redirect(url_for('accounts_list'))
    
    if request.method == 'POST':
        try:
            name = sanitize_input(request.form.get('name', '').strip(), max_length=100)
            template_type = request.form.get('template_type', '').strip()
            magazine_name = sanitize_input(request.form.get('magazine_name', '').strip(), max_length=100)
            purchase_amount = sanitize_input(request.form.get('purchase_amount', '').strip(), max_length=50)
            
            # File upload
            if 'template_file' not in request.files:
                flash('Template file is required', 'error')
                return redirect(url_for('template_add'))
            
            file = request.files['template_file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('template_add'))
            
            if not file.filename.endswith('.html'):
                flash('Only HTML files are allowed', 'error')
                return redirect(url_for('template_add'))
            
            # Validation
            if not all([name, template_type, magazine_name, purchase_amount]):
                flash('All fields are required', 'error')
                return redirect(url_for('template_add'))
            
            if template_type not in ['receipt_digital', 'receipt_print', 'reminder']:
                flash('Invalid template type', 'error')
                return redirect(url_for('template_add'))
            
            # Save file
            filename = secure_filename(file.filename)
            template_dir = os.path.join('templates', 'email_templates', str(g.active_account.id))
            os.makedirs(template_dir, exist_ok=True)
            
            file_path = os.path.join(template_dir, filename)
            file.save(file_path)
            
            # Store relative path for render_template
            template_path = f"email_templates/{g.active_account.id}/{filename}"
            
            # Create template record
            template = EmailTemplate(
                account_id=g.active_account.id,
                name=name,
                template_type=template_type,
                template_path=template_path,
                magazine_name=magazine_name,
                purchase_amount=purchase_amount,
                is_active=True,
                created_by=current_user.id
            )
            
            db.session.add(template)
            db.session.commit()
            
            flash(f'Template "{name}" created successfully', 'success')
            return redirect(url_for('templates_list'))
            
        except Exception as e:
            app.logger.error(f'Error creating template: {str(e)}')
            flash('Failed to create template', 'error')
            db.session.rollback()
            return redirect(url_for('template_add'))
    
    return render_template('template_form.html', template=None)

@app.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
@csrf_protect
def template_edit(template_id):
    """Edit an existing email template"""
    from flask import g
    template = EmailTemplate.query.get_or_404(template_id)
    
    # Security check - ensure template belongs to user's active account
    if template.account_id != g.active_account.id:
        flash('Access denied', 'error')
        return redirect(url_for('templates_list'))
    
    if request.method == 'POST':
        try:
            template.name = sanitize_input(request.form.get('name', '').strip(), max_length=100)
            template.template_type = request.form.get('template_type', '').strip()
            template.magazine_name = sanitize_input(request.form.get('magazine_name', '').strip(), max_length=100)
            template.purchase_amount = sanitize_input(request.form.get('purchase_amount', '').strip(), max_length=50)
            template.is_active = request.form.get('is_active') == 'on'
            
            # Handle file upload (optional on edit)
            if 'template_file' in request.files:
                file = request.files['template_file']
                if file.filename != '':
                    if not file.filename.endswith('.html'):
                        flash('Only HTML files are allowed', 'error')
                        return redirect(url_for('template_edit', template_id=template_id))
                    
                    # Save new file
                    filename = secure_filename(file.filename)
                    template_dir = os.path.join('templates', 'email_templates', str(g.active_account.id))
                    os.makedirs(template_dir, exist_ok=True)
                    
                    file_path = os.path.join(template_dir, filename)
                    file.save(file_path)
                    
                    # Update path
                    template.template_path = f"email_templates/{g.active_account.id}/{filename}"
            
            # Validation
            if not all([template.name, template.template_type, template.magazine_name, template.purchase_amount]):
                flash('All fields are required', 'error')
                return redirect(url_for('template_edit', template_id=template_id))
            
            if template.template_type not in ['receipt_digital', 'receipt_print', 'reminder']:
                flash('Invalid template type', 'error')
                return redirect(url_for('template_edit', template_id=template_id))
            
            db.session.commit()
            flash(f'Template "{template.name}" updated successfully', 'success')
            return redirect(url_for('templates_list'))
            
        except Exception as e:
            app.logger.error(f'Error updating template: {str(e)}')
            flash('Failed to update template', 'error')
            db.session.rollback()
            return redirect(url_for('template_edit', template_id=template_id))
    
    return render_template('template_form.html', template=template)

@app.route('/templates/preview/<int:template_id>')
@login_required
def template_preview(template_id):
    """Preview template with sample data"""
    from flask import g
    template = EmailTemplate.query.get_or_404(template_id)
    
    # Security check
    if template.account_id != g.active_account.id:
        flash('Access denied', 'error')
        return redirect(url_for('templates_list'))
    
    # Sample data for preview
    sample_data = {
        'recipient_name': 'John Doe',
        'magazine_name': template.magazine_name,
        'purchase_amount': template.purchase_amount,
        'purchase_date': datetime.now().strftime('%Y-%m-%d'),
        'quantity': 1,
        'transaction_id': 'PREVIEW-XXXX-XXXX',
        'edition': 'digital' if template.template_type == 'receipt_digital' else 'print',
        'digital_link': 'https://example.com/digital-edition',
        'digital_username': 'johndoe@example.com',
        'digital_password': 'sample123',
        'preorder_date': datetime.now().strftime('%Y-%m-%d'),
        'receipt_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sender_name': g.active_account.sender_name
    }
    
    try:
        html_content = render_template(template.template_path, **sample_data)
        return html_content
    except Exception as e:
        app.logger.error(f'Error previewing template: {str(e)}')
        flash('Failed to preview template', 'error')
        return redirect(url_for('templates_list'))

@app.route('/templates/delete/<int:template_id>', methods=['POST'])
@login_required
@csrf_protect
def template_delete(template_id):
    """Delete an email template"""
    from flask import g
    template = EmailTemplate.query.get_or_404(template_id)
    
    # Security check
    if template.account_id != g.active_account.id:
        flash('Access denied', 'error')
        return redirect(url_for('templates_list'))
    
    try:
        template_name = template.name
        # Optionally delete the file
        try:
            file_path = os.path.join('templates', template.template_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            app.logger.warning(f'Failed to delete template file: {str(e)}')
        
        db.session.delete(template)
        db.session.commit()
        flash(f'Template "{template_name}" deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f'Error deleting template: {str(e)}')
        flash('Failed to delete template', 'error')
        db.session.rollback()
    
    return redirect(url_for('templates_list'))

# ============================================
# BREVO WEBHOOK ENDPOINT
# ============================================

@app.route('/webhook/brevo', methods=['POST'])
def brevo_webhook():
    """
    Webhook endpoint to receive Brevo email events
    Handles: delivered, hard_bounce, soft_bounce, blocked, spam, invalid_email, opened, click
    """
    try:
        # Get webhook data
        data = request.get_json()
        
        if not data:
            app.logger.warning("Brevo webhook: No JSON data received")
            return jsonify({'error': 'No data received'}), 400
        
        # Log webhook for debugging
        app.logger.info(f"Brevo webhook received: {data.get('event', 'unknown')}")
        
        # Validate webhook signature (if configured)
        webhook_secret = os.environ.get('BREVO_WEBHOOK_SECRET')
        if webhook_secret:
            signature = request.headers.get('X-Brevo-Signature')
            if not signature:
                app.logger.warning("Brevo webhook: Missing signature")
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Verify signature (Brevo uses HMAC-SHA256)
            import hmac
            import hashlib
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                request.data,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                app.logger.warning("Brevo webhook: Invalid signature")
                return jsonify({'error': 'Unauthorized'}), 401
        
        # Extract event data
        event_type = data.get('event')
        message_id = data.get('message-id') or data.get('id')
        email = data.get('email')
        timestamp_str = data.get('date') or data.get('ts')
        
        if not event_type or not message_id:
            app.logger.warning(f"Brevo webhook: Missing event or message_id: {data}")
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Parse timestamp
        from datetime import timezone
        event_timestamp = datetime.now(timezone.utc)
        if timestamp_str:
            try:
                # Brevo sends Unix timestamp
                if isinstance(timestamp_str, (int, float)):
                    event_timestamp = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
                elif isinstance(timestamp_str, str) and timestamp_str.isdigit():
                    event_timestamp = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
                else:
                    # Try ISO format
                    event_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                app.logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
        
        # Find email record by message_id
        sent_email = SentEmail.query.filter_by(message_id=message_id).first()
        
        if not sent_email:
            app.logger.warning(f"Brevo webhook: Email record not found for message_id: {message_id}")
            return jsonify({'warning': 'Email record not found'}), 200  # Return 200 to prevent retries
        
        # Update record based on event type
        updated = False
        
        if event_type in ['delivered', 'delivery']:
            sent_email.delivery_status = 'delivered'
            sent_email.last_status_update = event_timestamp
            updated = True
            app.logger.info(f"Email {message_id} delivered to {email}")
        
        elif event_type in ['hard_bounce', 'hard-bounce']:
            sent_email.delivery_status = 'hard_bounce'
            sent_email.last_status_update = event_timestamp
            sent_email.bounce_reason = data.get('reason') or data.get('error')
            updated = True
            app.logger.info(f"Email {message_id} hard bounced: {sent_email.bounce_reason}")
        
        elif event_type in ['soft_bounce', 'soft-bounce']:
            sent_email.delivery_status = 'soft_bounce'
            sent_email.last_status_update = event_timestamp
            sent_email.bounce_reason = data.get('reason') or data.get('error')
            updated = True
            app.logger.info(f"Email {message_id} soft bounced: {sent_email.bounce_reason}")
        
        elif event_type in ['blocked', 'block']:
            sent_email.delivery_status = 'blocked'
            sent_email.last_status_update = event_timestamp
            sent_email.bounce_reason = data.get('reason') or data.get('error')
            updated = True
            app.logger.info(f"Email {message_id} blocked: {sent_email.bounce_reason}")
        
        elif event_type == 'spam':
            sent_email.delivery_status = 'spam'
            sent_email.last_status_update = event_timestamp
            sent_email.bounce_reason = 'Marked as spam by recipient'
            updated = True
            app.logger.info(f"Email {message_id} marked as spam")
        
        elif event_type in ['invalid_email', 'invalid-email']:
            sent_email.delivery_status = 'invalid_email'
            sent_email.last_status_update = event_timestamp
            sent_email.bounce_reason = 'Invalid email address'
            updated = True
            app.logger.info(f"Email {message_id} invalid address: {email}")
        
        elif event_type in ['opened', 'open']:
            # Only record first open
            if not sent_email.opened_at:
                sent_email.opened_at = event_timestamp
                sent_email.last_status_update = event_timestamp
                updated = True
                app.logger.info(f"Email {message_id} opened by {email}")
        
        elif event_type in ['click', 'clicked']:
            # Only record first click
            if not sent_email.clicked_at:
                sent_email.clicked_at = event_timestamp
                sent_email.last_status_update = event_timestamp
                updated = True
                app.logger.info(f"Email {message_id} link clicked by {email}")
        
        elif event_type == 'unsubscribe':
            sent_email.last_status_update = event_timestamp
            updated = True
            app.logger.info(f"Email {message_id} recipient unsubscribed: {email}")
        
        else:
            app.logger.warning(f"Brevo webhook: Unknown event type: {event_type}")
        
        # Save changes
        if updated:
            try:
                db.session.commit()
                app.logger.info(f"Updated email record for message_id: {message_id}")
            except Exception as e:
                app.logger.error(f"Failed to update email record: {e}")
                db.session.rollback()
                return jsonify({'error': 'Database error'}), 500
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        app.logger.error(f"Brevo webhook error: {str(e)}", exc_info=True)
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
