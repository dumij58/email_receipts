#!/usr/bin/env python3
"""
Migration script to convert from single-account to multi-account system.

This script:
1. Creates a default EmailAccount from environment variables
2. Copies existing email templates to new directory structure
3. Creates EmailTemplate records for each template type
4. Updates existing SentEmail records with account_id and template_id
5. Sets the default account as active for all existing users

Run this AFTER running `flask db upgrade` to create the new tables.
"""
import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import EmailAccount, EmailTemplate, SentEmail, User
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_default_account():
    """Create default email account from environment variables"""
    print("Creating default email account...")
    
    # Get credentials from environment
    brevo_api_key = os.getenv('BREVO_API_KEY')
    sender_email = os.getenv('SENDER_EMAIL')
    sender_name = os.getenv('SENDER_NAME', 'Magazine Store')
    
    if not brevo_api_key or not sender_email:
        print("ERROR: BREVO_API_KEY and SENDER_EMAIL must be set in environment variables")
        sys.exit(1)
    
    # Check if default account already exists
    existing_account = EmailAccount.query.filter_by(sender_email=sender_email).first()
    if existing_account:
        print(f"Default account already exists: {existing_account.name} (ID: {existing_account.id})")
        return existing_account
    
    # Create new account
    account = EmailAccount(
        name="Default Account",
        brevo_api_key=brevo_api_key,
        sender_email=sender_email,
        sender_name=sender_name,
        is_active=True
    )
    
    db.session.add(account)
    db.session.commit()
    
    print(f"✓ Created default account: {account.name} (ID: {account.id})")
    return account


def copy_templates(account_id):
    """Copy existing email templates to new directory structure"""
    print("\nCopying email templates...")
    
    # Create directory structure
    template_dir = Path('templates/email_templates')
    account_dir = template_dir / str(account_id)
    account_dir.mkdir(parents=True, exist_ok=True)
    
    # Template files to copy
    template_files = [
        'email_receipt_digital.html',
        'email_receipt_print.html',
        'email_reminder.html'
    ]
    
    copied_files = []
    for template_file in template_files:
        source = Path('templates') / template_file
        destination = account_dir / template_file
        
        if source.exists():
            if not destination.exists():
                shutil.copy2(source, destination)
                print(f"✓ Copied {template_file} to {destination}")
            else:
                print(f"  {template_file} already exists in destination")
            copied_files.append(template_file)
        else:
            print(f"⚠ Warning: {template_file} not found in templates/")
    
    return copied_files


def create_template_records(account_id, copied_files):
    """Create EmailTemplate records for copied templates"""
    print("\nCreating template records...")
    
    # Get magazine name and purchase amount from environment
    magazine_name = os.getenv('MAGAZINE_NAME', 'Magazine')
    purchase_amount = os.getenv('PURCHASE_AMOUNT', '$0.00')
    
    # Template mapping
    templates_config = [
        {
            'name': f'{magazine_name} - Digital Receipt',
            'template_type': 'receipt_digital',
            'filename': 'email_receipt_digital.html'
        },
        {
            'name': f'{magazine_name} - Print Receipt',
            'template_type': 'receipt_print',
            'filename': 'email_receipt_print.html'
        },
        {
            'name': f'{magazine_name} - Payment Reminder',
            'template_type': 'reminder',
            'filename': 'email_reminder.html'
        }
    ]
    
    created_templates = []
    for config in templates_config:
        if config['filename'] not in copied_files:
            continue
        
        # Check if template already exists
        existing = EmailTemplate.query.filter_by(
            account_id=account_id,
            template_type=config['template_type']
        ).first()
        
        if existing:
            print(f"  Template already exists: {existing.name} (ID: {existing.id})")
            created_templates.append(existing)
            continue
        
        # Create template record
        template = EmailTemplate(
            account_id=account_id,
            name=config['name'],
            template_type=config['template_type'],
            template_path=f"email_templates/{account_id}/{config['filename']}",
            magazine_name=magazine_name,
            purchase_amount=purchase_amount,
            is_active=True
        )
        
        db.session.add(template)
        created_templates.append(template)
    
    db.session.commit()
    
    for template in created_templates:
        print(f"✓ Created template: {template.name} (ID: {template.id})")
    
    return created_templates


def update_sent_emails(account_id, templates):
    """Update existing SentEmail records with account_id and template_id"""
    print("\nUpdating existing sent email records...")
    
    # Create template lookup by type
    template_map = {
        'receipt_digital': next((t for t in templates if t.template_type == 'receipt_digital'), None),
        'receipt_print': next((t for t in templates if t.template_type == 'receipt_print'), None),
        'reminder': next((t for t in templates if t.template_type == 'reminder'), None)
    }
    
    # Get all sent emails without account_id
    sent_emails = SentEmail.query.filter_by(account_id=None).all()
    
    if not sent_emails:
        print("  No sent emails to update")
        return
    
    updated_count = 0
    for email in sent_emails:
        email.account_id = account_id
        
        # Determine template based on edition
        if email.edition and email.edition.lower() == 'digital':
            email.template_id = template_map['receipt_digital'].id if template_map['receipt_digital'] else None
        elif email.edition and email.edition.lower() == 'print':
            email.template_id = template_map['receipt_print'].id if template_map['receipt_print'] else None
        # Note: Old emails won't have template for reminders, that's OK
        
        updated_count += 1
    
    db.session.commit()
    print(f"✓ Updated {updated_count} sent email records")


def set_default_active_account(account_id):
    """Set the default account as active for all users"""
    print("\nSetting default active account for users...")
    
    users = User.query.filter_by(active_account_id=None).all()
    
    if not users:
        print("  All users already have an active account set")
        return
    
    for user in users:
        user.active_account_id = account_id
    
    db.session.commit()
    print(f"✓ Set default account for {len(users)} user(s)")


def main():
    """Run the migration"""
    print("=" * 60)
    print("Multi-Account Migration Script")
    print("=" * 60)
    
    with app.app_context():
        # Step 1: Create default account
        account = create_default_account()
        
        # Step 2: Copy templates
        copied_files = copy_templates(account.id)
        
        # Step 3: Create template records
        templates = create_template_records(account.id, copied_files)
        
        # Step 4: Update existing sent emails
        update_sent_emails(account.id, templates)
        
        # Step 5: Set default active account for users
        set_default_active_account(account.id)
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Verify the migration by checking /accounts page")
        print("2. Update your .env file to include SECRET_KEY if not already set")
        print("3. Test sending emails with the new system")
        print("4. Create additional accounts and templates as needed")


if __name__ == '__main__':
    main()
