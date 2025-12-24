from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from email_service import EmailService
import os
import csv
from io import StringIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize email service
email_service = EmailService()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/send-single', methods=['GET', 'POST'])
def send_single():
    """Send a single email receipt"""
    if request.method == 'POST':
        try:
            recipient_email = request.form.get('email')
            recipient_name = request.form.get('name')
            magazine_name = request.form.get('magazine_name')
            purchase_amount = request.form.get('purchase_amount')
            purchase_date = request.form.get('purchase_date')
            
            # Validate inputs
            if not all([recipient_email, recipient_name, magazine_name, purchase_amount, purchase_date]):
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
def send_bulk():
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
        'smtp_configured': email_service.is_configured()
    })

@app.route('/api/send-email', methods=['POST'])
def api_send_email():
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
    app.run(host='0.0.0.0', port=5000, debug=True)
