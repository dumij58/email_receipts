import os
import base64
from datetime import datetime
import logging
from flask import render_template
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Load environment variables from .env file (only if not in Docker)
# Check multiple indicators for Docker environment
is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
if not is_docker:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

# Debug mode configuration
DEBUG_MODE = os.environ.get('DEBUG', 'false').lower() == 'true'

log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations using Brevo (Sendinblue)"""
    
    def __init__(self, account=None):
        """
        Initialize EmailService with an EmailAccount model instance.
        
        Args:
            account: EmailAccount model instance (optional - falls back to env vars for backwards compatibility)
        """
        # Load from account model if provided, otherwise fall back to environment variables
        if account:
            self.brevo_api_key = account.brevo_api_key  # Will be decrypted automatically by SQLAlchemy-Utils
            self.sender_email = account.sender_email
            self.sender_name = account.sender_name
            self.account_id = account.id
            self.account_name = account.name
        else:
            # Fallback to environment variables (for backwards compatibility during migration)
            self.brevo_api_key = os.environ.get('BREVO_API_KEY', '') or os.environ.get('SENDGRID_API_KEY', '')
            self.sender_email = os.environ.get('SENDER_EMAIL', '')
            self.sender_name = os.environ.get('SENDER_NAME', 'Magazine Store')
            self.account_id = None
            self.account_name = 'Legacy Account'
        
        # These will be overridden by template data when provided
        self.magazine_name = os.environ.get('MAGAZINE_NAME', '[MAGAZINE_NAME]')
        self.purchase_amount = os.environ.get('PURCHASE_AMOUNT', '[PURCHASE_AMOUNT]')
        
        # Debug logging to verify configuration
        if DEBUG_MODE:
            logger.debug(f"Initializing EmailService in {'Docker' if is_docker else 'Local'} environment")
            logger.debug(f"Account: {self.account_name} (ID: {self.account_id})")
            logger.debug(f"Brevo API Key configured: {bool(self.brevo_api_key)} (length: {len(str(self.brevo_api_key)) if self.brevo_api_key else 0})")
            logger.debug(f"Sender Email: {self.sender_email}")
            logger.debug(f"Sender Name: {self.sender_name}")
        
        # Initialize Brevo client
        if self.brevo_api_key:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = str(self.brevo_api_key)  # Ensure it's a string
            self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
            if DEBUG_MODE:
                logger.debug("Brevo API client initialized successfully")
        else:
            self.api_instance = None
            logger.error("CRITICAL: Brevo API key not configured - emails will not be sent!")
    
    def is_configured(self):
        """Check if Brevo is properly configured"""
        return bool(self.brevo_api_key and self.sender_email)
    
    def create_receipt_email(self, recipient_name, magazine_name, purchase_amount, purchase_date, quantity=1, transaction_id=None, edition=None, digital_link=None, digital_username=None, digital_password=None, template_path=None):
        """Create HTML email content for receipt using template (from EmailTemplate model or fallback)"""
        # If template_path is provided, use it; otherwise use legacy template selection
        if template_path:
            template = template_path
        elif edition and edition.lower() == 'digital':
            template = 'email_receipt_digital.html'
        else:
            template = 'email_receipt_print.html'
        
        html_content = render_template(
            template,
            recipient_name=recipient_name,
            magazine_name=magazine_name,
            purchase_amount=purchase_amount,
            purchase_date=purchase_date,
            quantity=quantity,
            transaction_id=transaction_id or 'N/A',
            edition=edition or 'print',
            digital_link=digital_link or '',
            digital_username=digital_username or '',
            digital_password=digital_password or '',
            receipt_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            sender_name=self.sender_name
        )
        return html_content
    
    def send_email(self, recipient_email, subject, html_content):
        """Send an email using Brevo API
        
        Returns:
            tuple: (success: bool, message_id: str, error_message: str)
        """
        try:
            if not self.api_instance:
                error_msg = "Brevo client not initialized. Check API key."
                logger.error(error_msg)
                return (False, None, error_msg)
            
            # Log for debugging
            if DEBUG_MODE:
                logger.debug(f"Attempting to send email to {recipient_email}")
            
            # Create Brevo email object
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": recipient_email}],
                sender={"name": self.sender_name, "email": self.sender_email},
                subject=subject,
                html_content=html_content
            )
            
            # Send email via Brevo API
            if DEBUG_MODE:
                logger.debug(f"Sending message via Brevo API...")
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            
            message_id = api_response.message_id if hasattr(api_response, 'message_id') else None
            
            if DEBUG_MODE:
                logger.debug(f"Email sent successfully to {recipient_email} (Message ID: {message_id})")
            return (True, message_id, None)
            
        except ApiException as e:
            error_msg = f"Brevo API Exception: {str(e)}"
            logger.error(error_msg)
            return (False, None, error_msg)
        except Exception as e:
            error_msg = f"Failed to send email to {recipient_email}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Error type: {type(e).__name__}")
            return (False, None, error_msg)
    
    def send_single_receipt(self, recipient_email, recipient_name, magazine_name, 
                          purchase_amount, purchase_date, quantity=1, transaction_id=None, edition=None, digital_link=None, digital_username=None, digital_password=None, template_path=None):
        """Send a single receipt email
        
        Returns:
            tuple: (success: bool, message_id: str, error_message: str)
        """
        subject = f"Receipt for {magazine_name} - {self.sender_name}"
        html_content = self.create_receipt_email(
            recipient_name, magazine_name, purchase_amount, purchase_date, quantity,
            transaction_id, edition, digital_link, digital_username, digital_password, template_path
        )
        return self.send_email(recipient_email, subject, html_content)
    
    def send_bulk_receipts(self, csv_reader):
        """Send bulk receipt emails from CSV data
        
        Returns:
            dict: {'success': int, 'failed': int, 'results': list of tuples}
        """
        success_count = 0
        failed_count = 0
        results = []  # List of (recipient_email, recipient_name, success, transaction_id, message_id, error_message)
        
        for row in csv_reader:
            try:
                # Expected CSV columns: email, name, purchase_date, quantity, edition, link, username, password
                recipient_email = row.get('email', '').strip()
                recipient_name = row.get('name', '').strip()
                purchase_date = row.get('purchase_date', '').strip()
                quantity = int(row.get('quantity', '1').strip() or '1')  # Default to 1 if not provided
                edition = row.get('edition', 'print').lower().strip()
                
                # Validate edition
                if edition not in ['digital', 'print']:
                    edition = 'print'
                
                # Digital edition fields
                digital_link = row.get('link', '').strip() if edition == 'digital' else None
                digital_username = row.get('username', '').strip() if edition == 'digital' else None
                digital_password = row.get('password', '').strip() if edition == 'digital' else None
                
                if not all([recipient_email, recipient_name, purchase_date]):
                    if DEBUG_MODE:
                        logger.debug(f"Skipping row with missing data: {row}")
                    failed_count += 1
                    results.append((recipient_email, recipient_name, False, None, None, "Missing required fields"))
                    continue
                
                # Validate digital fields if digital edition
                if edition == 'digital' and not all([digital_link, digital_username, digital_password]):
                    if DEBUG_MODE:
                        logger.debug(f"Skipping digital edition with missing credentials: {row}")
                    failed_count += 1
                    results.append((recipient_email, recipient_name, False, None, None, "Missing digital access credentials"))
                    continue
                
                # Generate transaction ID before sending
                import uuid
                transaction_id = f"SNX-{uuid.uuid4().hex[:12].upper()}"
                
                success, message_id, error_message = self.send_single_receipt(
                    recipient_email, recipient_name, self.magazine_name,
                    self.purchase_amount, purchase_date, quantity, transaction_id,
                    edition, digital_link, digital_username, digital_password
                )
                
                results.append((recipient_email, recipient_name, success, transaction_id, message_id, error_message))
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                error_msg = f"Error processing row: {str(e)}"
                logger.error(error_msg)
                failed_count += 1
                results.append((recipient_email, recipient_name, False, None, None, error_msg))
        
        if DEBUG_MODE:
            logger.debug(f"Bulk send completed: {success_count} success, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count, 'results': results}
    
    def create_reminder_email(self, recipient_name, preorder_date, quantity=1, magazine_name=None, purchase_amount=None, template_path=None):
        """Create HTML content for payment reminder email"""
        from flask import render_template
        
        # Use provided values or fall back to instance defaults
        mag_name = magazine_name or self.magazine_name
        purch_amount = purchase_amount or self.purchase_amount
        template = template_path or 'email_reminder.html'
        
        return render_template(template,
                             recipient_name=recipient_name,
                             magazine_name=mag_name,
                             preorder_date=preorder_date,
                             purchase_amount=purch_amount,
                             quantity=quantity,
                             sender_name=self.sender_name)
    
    def send_payment_reminder(self, recipient_email, recipient_name, preorder_date, quantity=1, magazine_name=None, purchase_amount=None, template_path=None):
        """Send a payment reminder email for pending preorders
        
        Returns:
            tuple: (success: bool, message_id: str, error_message: str)
        """
        mag_name = magazine_name or self.magazine_name
        subject = f"Payment Reminder: Complete Your {mag_name} Order"
        html_content = self.create_reminder_email(recipient_name, preorder_date, quantity, magazine_name, purchase_amount, template_path)
        return self.send_email(recipient_email, subject, html_content)
    
    def send_bulk_reminders(self, csv_reader):
        """Send bulk payment reminder emails from CSV data
        
        Returns:
            dict: {'success': int, 'failed': int, 'results': list of tuples}
        """
        success_count = 0
        failed_count = 0
        results = []  # List of (recipient_email, recipient_name, success, message_id, error_message)
        
        for row in csv_reader:
            try:
                # Expected CSV columns: email, name, preorder_date, quantity (optional)
                recipient_email = row.get('email', '').strip()
                recipient_name = row.get('name', '').strip()
                preorder_date = row.get('preorder_date', '').strip()
                quantity = int(row.get('quantity', '1').strip() or '1')  # Default to 1 if not provided
                
                if not all([recipient_email, recipient_name, preorder_date]):
                    if DEBUG_MODE:
                        logger.debug(f"Skipping row with missing data: {row}")
                    failed_count += 1
                    results.append((recipient_email, recipient_name, False, None, "Missing required fields"))
                    continue
                
                success, message_id, error_message = self.send_payment_reminder(
                    recipient_email, recipient_name, preorder_date, quantity
                )
                
                results.append((recipient_email, recipient_name, success, message_id, error_message))
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                error_msg = f"Error processing row: {str(e)}"
                logger.error(error_msg)
                failed_count += 1
                results.append((recipient_email, recipient_name, False, None, error_msg))
        
        if DEBUG_MODE:
            logger.debug(f"Bulk reminder send completed: {success_count} success, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count, 'results': results}
