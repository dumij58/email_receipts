from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from email_service import EmailService
import os
import csv
from io import StringIO
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# Initialize email service
email_service = EmailService()

magazine_name = email_service.magazine_name
purchase_amount = email_service.purchase_amount

# User Model
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and check_password_hash(USERS[username]['password'], password):
            user = User(USERS[username]['id'], username)
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect to next page or index
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/send-single', methods=['GET', 'POST'])
@login_required
def send_single():
    """Send a single email receipt"""
    if request.method == 'POST':
        try:
            recipient_email = request.form.get('email')
            recipient_name = request.form.get('name')
            purchase_date = request.form.get('purchase_date')
            
            # Validate inputs
            if not all([recipient_email, recipient_name, purchase_date]):
                flash('All fields are required', 'error')
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
            flash(f'Error: {str(e)}', 'error')
            
        return redirect(url_for('send_single'))
    
    return render_template('send_single.html')
@app.route('/send-bulk', methods=['GET', 'POST'])
@login_required
def send_bulk():
    """Send bulk email receipts"""
    """Send bulk email receipts"""
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
            
            if not file.filename.endswith('.csv'):
                flash('Only CSV files are allowed', 'error')
                return redirect(url_for('send_bulk'))
            
            # Read CSV file
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            # Process bulk emails
            results = email_service.send_bulk_receipts(csv_reader)
            
            flash(f'Bulk email completed: {results["success"]} sent, {results["failed"]} failed', 
                  'success' if results["failed"] == 0 else 'warning')
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            
        return redirect(url_for('send_bulk'))
    
    return render_template('send_bulk.html')

@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'email-receipts',
        'brevo_configured': email_service.is_configured()
    })
@app.route('/api/send-email', methods=['POST'])
@login_required
def api_send_email():
    """API endpoint for sending single email"""
    """API endpoint for sending single email"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'name', 'magazine_name', 'purchase_amount', 'purchase_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        success = email_service.send_single_receipt(
            recipient_email=data['email'],
            recipient_name=data['name'],
            magazine_name=data['magazine_name'],
            purchase_amount=data['purchase_amount'],
            purchase_date=data['purchase_date']
        )
        
        if success:
            return jsonify({'message': 'Email sent successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
