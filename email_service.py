import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from flask import render_template

# Load environment variables from .env file (only if not in Docker)
if not os.path.exists('/.dockerenv'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.sender_email = os.environ.get('SENDER_EMAIL', self.smtp_username)
        self.sender_name = os.environ.get('SENDER_NAME', 'Magazine Store')
        self.magazine_name = os.environ.get('MAGAZINE_NAME', '[MAGAZINE_NAME]')
        self.purchase_amount = os.environ.get('PURCHASE_AMOUNT', '[PURCHASE_AMOUNT]')
        
        # Debug logging (only if not in production)
        if os.environ.get('FLASK_ENV') != 'production':
            logger.info(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
            logger.info(f"SMTP Username: {self.smtp_username[:3]}...{self.smtp_username[-3:] if len(self.smtp_username) > 6 else ''}")
            logger.info(f"SMTP Password configured: {bool(self.smtp_password)}")
            logger.info(f"Sender Email: {self.sender_email}")
    
    def is_configured(self):
        """Check if SMTP is properly configured"""
        return bool(self.smtp_username and self.smtp_password)
    
    def create_receipt_email(self, recipient_name, magazine_name, purchase_amount, purchase_date):
        """Create HTML email content for receipt"""
        html_content = render_template(
            'email_receipt.html',
            recipient_name=recipient_name,
            magazine_name=magazine_name,
            purchase_amount=purchase_amount,
            purchase_date=purchase_date,
            receipt_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            sender_name=self.sender_name
        )
        return html_content
    
    def send_email(self, recipient_email, subject, html_content):
        """Send an email using SMTP"""
        try:
            # Log configuration for debugging
            logger.info(f"Attempting to send email to {recipient_email}")
            logger.info(f"SMTP: {self.smtp_server}:{self.smtp_port}")
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.sender_name} <{self.sender_email}>"
            message['To'] = recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                logger.info(f"Starting TLS...")
                server.starttls()
                logger.info(f"Logging in with username: {self.smtp_username[:3]}...")
                server.login(self.smtp_username, self.smtp_password)
                logger.info(f"Sending message...")
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {str(e)}")
            logger.error(f"Username: {self.smtp_username}, Password configured: {bool(self.smtp_password)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error sending to {recipient_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return False
    
    def send_single_receipt(self, recipient_email, recipient_name, magazine_name, 
                          purchase_amount, purchase_date):
        """Send a single receipt email"""
        subject = f"Receipt for {magazine_name} - {self.sender_name}"
        html_content = self.create_receipt_email(
            recipient_name, magazine_name, purchase_amount, purchase_date
        )
        return self.send_email(recipient_email, subject, html_content)
    
    def send_bulk_receipts(self, csv_reader):
        """Send bulk receipt emails from CSV data"""
        success_count = 0
        failed_count = 0
        
        for row in csv_reader:
            try:
                # Expected CSV columns: email, name, magazine_name, purchase_amount, purchase_date
                recipient_email = row.get('email', '').strip()
                recipient_name = row.get('name', '').strip()
                purchase_date = row.get('purchase_date', '').strip()
                
                if not all([recipient_email, recipient_name, purchase_date]):
                    logger.warning(f"Skipping row with missing data: {row}")
                    failed_count += 1
                    continue
                
                success = self.send_single_receipt(
                    recipient_email, recipient_name, self.magazine_name,
                    self.purchase_amount, purchase_date
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                failed_count += 1
        
        logger.info(f"Bulk send completed: {success_count} success, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count}
