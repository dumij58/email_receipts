# Multi-Account Implementation - Remaining Tasks

## Overview
Most of the multi-account and multi-template system has been implemented. This guide covers the remaining manual updates needed.

## Completed Features
✅ Database models with encrypted API keys  
✅ Migration script  
✅ Email service refactor  
✅ Account management UI  
✅ Template management UI  
✅ Account switcher in navigation  
✅ Updated `/send-single` route  

## Remaining Tasks

### 1. Update `/send-bulk` Route in app.py

**Location:** Line ~419 in app.py

**Current Issue:** Still uses global `email_service` and doesn't support templates

**Required Changes:**
```python
@app.route('/send-bulk', methods=['GET', 'POST'])
@login_required
@csrf_protect
def send_bulk():
    """Send bulk email receipts with template support"""
    from flask import g
    
    # Check if user has an active account
    if not g.active_account:
        flash('Please select an email account first', 'warning')
        return redirect(url_for('accounts_list'))
    
    if request.method == 'POST':
        try:
            # Get template selection
            template_id = request.form.get('template_id')
            if not template_id:
                flash('Please select a template', 'error')
                return redirect(url_for('send_bulk'))
            
            template = EmailTemplate.query.get(template_id)
            if not template or template.account_id != g.active_account.id:
                flash('Invalid template selected', 'error')
                return redirect(url_for('send_bulk'))
            
            # ... existing file upload code ...
            
            # Replace email_service initialization:
            email_service = EmailService(account=g.active_account)
            
            # Update send_bulk_receipts to use template values
            # You'll need to modify email_service.py to accept template parameter
            # OR manually iterate CSV and use template.magazine_name, template.purchase_amount
            
    # GET request - load templates
    templates = EmailTemplate.query.filter_by(
        account_id=g.active_account.id,
        is_active=True,
        template_type__in=['receipt_digital', 'receipt_print']
    ).order_by(EmailTemplate.name).all()
    
    return render_template('send_bulk.html', templates=templates)
```

### 2. Update `/send-reminder` Route in app.py

**Location:** Line ~530 in app.py

**Required Changes:**
- Add active account check
- Add template selection (filter by template_type='reminder')
- Initialize EmailService with active account
- Pass template to email service

### 3. Update send_single.html Template

**Location:** templates/send_single.html

**Add Template Selector:**
```html
<div class="form-group">
    <label for="template_id">Email Template *</label>
    <select name="template_id" id="template_id" required>
        <option value="">-- Select Template --</option>
        {% for template in templates %}
        <option value="{{ template.id }}">
            {{ template.name }} ({{ template.magazine_name }} - {{ template.purchase_amount }})
        </option>
        {% endfor %}
    </select>
</div>
```

**Add JavaScript to auto-fill edition based on template type:**
```javascript
<script>
document.getElementById('template_id').addEventListener('change', function() {
    // Auto-select edition based on template type
    // You can add data-type attribute to options if needed
});
</script>
```

### 4. Update send_bulk.html Template

**Location:** templates/send_bulk.html

**Add:** Template selector dropdown (similar to send_single.html)

### 5. Update send_reminder.html Template

**Location:** templates/send_reminder.html

**Add:** Template selector dropdown filtered to only show reminder templates

### 6. Install Dependencies

```bash
cd /Users/dumij58/Dumindu/Projects/email-receipts
pip install sqlalchemy-utils==0.41.1
```

### 7. Run Database Migrations

```bash
# Create new migration for the schema changes
flask db migrate -m "Add multi-account and template support"

# Apply migration
flask db upgrade

# Run data migration script
python scripts/migrate_to_multi_account.py
```

### 8. Update Environment Variables

Ensure your `.env` file has:
```env
SECRET_KEY=your-secure-secret-key-here-min-32-chars
BREVO_API_KEY=your-existing-key  # Will be migrated to database
SENDER_EMAIL=your@email.com      # Will be migrated to database
SENDER_NAME=Your Name            # Will be migrated to database
MAGAZINE_NAME=Your Magazine      # Will be migrated to database
PURCHASE_AMOUNT=Rs. 1500         # Will be migrated to database
```

### 9. Test the System

1. Start the application
2. Login
3. Navigate to Settings → Email Accounts
4. Verify default account was created
5. Navigate to Settings → Email Templates
6. Verify templates were created
7. Try switching accounts using the dropdown in navigation
8. Test sending a single email with template selection
9. Test bulk sending
10. Test reminders

### 10. Optional Enhancements

**CSV Format Update for Bulk Sending:**

You can optionally add a `template_id` column to your CSV files to allow different templates per row:
```csv
email,name,purchase_date,edition,template_id
john@example.com,John Doe,2026-01-20,digital,1
```

**Template Variables Enhancement:**

Add custom variables to templates by extending the render_template calls in email_service.py.

## Troubleshooting

### Error: "No module named 'sqlalchemy_utils'"
Run: `pip install sqlalchemy-utils`

### Error: "SECRET_KEY not set"
Add `SECRET_KEY=` to your `.env` file with a random 32+ character string

### Account switcher not showing
Make sure you're logged in and have run the migration script

### Templates not appearing
Check that templates are marked as `is_active=True` and belong to your active account

## Support

If you encounter issues:
1. Check application logs in `logs/` directory
2. Verify database migrations: `flask db current`
3. Check that email account has valid Brevo API key
4. Ensure template files exist in `templates/email_templates/<account_id>/`
