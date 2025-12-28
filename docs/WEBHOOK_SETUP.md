# Brevo Webhook Setup Guide

This guide explains how to configure Brevo webhooks to enable real-time email delivery and engagement tracking.

## Overview

The application now supports real-time email status tracking via Brevo webhooks. This enables:

- **Delivery Tracking**: Know when emails are delivered, bounced, blocked, or marked as spam
- **Engagement Metrics**: Track when recipients open emails and click links
- **Failure Reasons**: Capture detailed bounce and block reasons
- **Updated Status Display**: View delivery status badges and engagement icons in the email history

## Webhook Events Tracked

The application processes the following Brevo webhook events:

| Event | Description | Status Update |
|-------|-------------|---------------|
| `delivered` | Email successfully delivered to recipient's server | ✓ Delivered |
| `hard_bounce` | Permanent delivery failure (invalid email, domain doesn't exist) | ✗ Hard Bounce |
| `soft_bounce` | Temporary delivery failure (mailbox full, server temporarily unavailable) | ⚠ Soft Bounce |
| `blocked` | Email blocked by recipient's server or ISP | 🚫 Blocked |
| `spam` | Recipient marked email as spam | 🚩 Spam |
| `invalid_email` | Email address format is invalid | ✗ Invalid |
| `opened` | Recipient opened the email (first open only) | 👁 Opened |
| `click` | Recipient clicked a link in the email (first click only) | 🖱 Clicked |

## Setup Instructions

### Step 1: Get Your Webhook URL

Your webhook endpoint URL is:

```
https://your-domain.com/webhook/brevo
```

**For local testing with ngrok:**

```bash
# Install ngrok if not already installed
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start your Flask app (in Docker or locally)
docker compose up -d
# or
python3 app.py

# In another terminal, start ngrok
ngrok http 5000

# Use the HTTPS URL provided by ngrok
https://abc123.ngrok.io/webhook/brevo
```

### Step 2: Configure Webhook Secret (Recommended)

For security, configure a webhook secret to validate incoming webhook requests:

1. **Generate a secure random secret:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Add to your environment:**

**For Docker (docker-compose.yml):**
```yaml
services:
  web:
    environment:
      - BREVO_WEBHOOK_SECRET=your-generated-secret-here
```

**For local development (.env file):**
```
BREVO_WEBHOOK_SECRET=your-generated-secret-here
```

3. **Restart your application:**

```bash
docker compose down && docker compose up -d
```

### Step 3: Configure Webhook in Brevo Dashboard

1. **Login to Brevo:**
   - Go to [https://app.brevo.com/](https://app.brevo.com/)
   - Sign in with your account

2. **Navigate to Webhooks:**
   - Click on your profile icon (top right)
   - Select **"SMTP & API"**
   - Click on **"Webhooks"** tab

3. **Create New Webhook:**
   - Click **"Add a new webhook"**
   - Enter your webhook URL: `https://your-domain.com/webhook/brevo`
   - **Important:** Use HTTPS (required by Brevo)

4. **Select Events to Track:**

   Check the following events:
   - ✅ **Transactional**
     - ✅ `delivered`
     - ✅ `hard_bounce`
     - ✅ `soft_bounce`
     - ✅ `blocked`
     - ✅ `spam`
     - ✅ `invalid_email`
     - ✅ `opened` (requires tracking enabled in email)
     - ✅ `click` (requires tracking enabled in email)

5. **Configure Webhook Authentication (if using secret):**
   - In the webhook settings, add custom header:
     - Header name: `X-Brevo-Signature`
     - Value: Your webhook secret from Step 2

6. **Save Webhook:**
   - Click **"Save"** to activate the webhook

### Step 4: Test the Webhook

1. **Send a test email:**
   - Use the "Send Single Email" feature in the application
   - Send an email to yourself

2. **Check webhook delivery:**
   - Brevo Dashboard → Webhooks → Click on your webhook
   - View recent webhook calls and responses
   - Should see `200 OK` responses

3. **Verify database update:**
   - Go to "Sent Emails" page in the application
   - Wait a few seconds for delivery
   - Refresh the page
   - You should see "✓ Delivered" status

4. **Test engagement tracking:**
   - Open the email you received
   - Click any links in the email
   - Refresh "Sent Emails" page
   - Should see "👁 Opened" and "🖱 Clicked" badges

### Step 5: Monitor Webhook Activity

**Check application logs:**

```bash
# Docker logs
docker compose logs -f web | grep "Brevo webhook"

# Local logs
# Look for log entries like:
# INFO: Brevo webhook received: delivered
# INFO: Email <message-id> delivered to user@example.com
# INFO: Updated email record for message_id: <message-id>
```

**Check Brevo webhook logs:**
- Brevo Dashboard → Webhooks → Click on your webhook
- View **"Recent calls"** tab
- Check status codes (should be 200)
- View request/response payloads

## Troubleshooting

### Webhook Returns 400 Error

**Cause:** Missing or invalid JSON payload

**Solution:**
- Check Brevo webhook logs for the exact payload sent
- Ensure webhook is configured for transactional emails
- Verify events are being triggered

### Webhook Returns 401 Unauthorized

**Cause:** Webhook signature validation failed

**Solution:**
- Verify `BREVO_WEBHOOK_SECRET` is set correctly in environment
- Ensure the secret in Brevo dashboard matches your environment variable
- Check application logs for signature validation errors

### Webhook Returns 500 Error

**Cause:** Database or internal error

**Solution:**
- Check application logs: `docker compose logs -f web`
- Verify database is accessible
- Ensure all required fields are in the webhook payload

### Status Not Updating in Database

**Cause:** `message_id` mismatch or email record not found

**Solution:**
- Check logs for: "Email record not found for message_id"
- Verify the email was sent through the application (not manually)
- Ensure `message_id` is being saved during email send

### Emails Show "⏳ Pending..." Status

**Cause:** Webhook not yet received or not configured

**Solution:**
- Wait a few seconds and refresh (delivery takes 1-5 seconds typically)
- Verify webhook is configured and active in Brevo dashboard
- Check webhook URL is correct and accessible
- Test webhook using Brevo's test feature

### ngrok Session Expired (Local Testing)

**Cause:** Free ngrok URLs expire after 2 hours

**Solution:**
- Restart ngrok to get a new URL
- Update webhook URL in Brevo dashboard
- For persistent URLs, upgrade to ngrok paid plan or use a production domain

## Database Migration

After deploying the webhook feature, run the database migration to add new columns:

```bash
# Run migration script
docker compose exec web python3 scripts/migrate_email_status.py

# Or locally
python3 scripts/migrate_email_status.py
```

This adds the following fields to the `sent_emails` table:
- `delivery_status` - Current delivery status
- `last_status_update` - Timestamp of last webhook event
- `opened_at` - First email open timestamp
- `clicked_at` - First link click timestamp
- `bounce_reason` - Reason for bounces/blocks/spam

## Security Considerations

1. **Always use HTTPS** for webhook URLs in production
2. **Set a webhook secret** (`BREVO_WEBHOOK_SECRET`) to validate webhook authenticity
3. **Monitor webhook logs** for suspicious activity
4. **Rate limiting**: Brevo may send duplicate events; the application handles this gracefully
5. **Webhook retries**: Brevo retries failed webhooks; return 200 even if record not found to prevent infinite retries

## API Reference

### Webhook Endpoint

**URL:** `/webhook/brevo`  
**Method:** `POST`  
**Content-Type:** `application/json`

**Headers:**
- `X-Brevo-Signature` (optional): HMAC-SHA256 signature for validation

**Example Payload (Delivered Event):**
```json
{
  "event": "delivered",
  "message-id": "<202312280800.123456@smtp-relay.mailin.fr>",
  "email": "recipient@example.com",
  "date": 1703750400,
  "ts": 1703750400
}
```

**Example Payload (Hard Bounce):**
```json
{
  "event": "hard_bounce",
  "message-id": "<202312280800.123456@smtp-relay.mailin.fr>",
  "email": "invalid@nonexistent.com",
  "date": 1703750400,
  "reason": "Invalid domain",
  "error": "550 5.1.1 User unknown"
}
```

**Response:**
- `200 OK`: Event processed successfully
- `400 Bad Request`: Invalid payload
- `401 Unauthorized`: Invalid signature
- `500 Internal Server Error`: Server error

## Additional Resources

- [Brevo Webhooks Documentation](https://developers.brevo.com/docs/webhooks)
- [Brevo Transactional Email API](https://developers.brevo.com/docs/send-a-transactional-email)
- [SMTP & API Settings](https://app.brevo.com/settings/keys/api)

## Support

For issues with:
- **Brevo service**: Contact Brevo support at https://help.brevo.com/
- **Application webhook code**: Check application logs and see [BREVO_TROUBLESHOOTING.md](BREVO_TROUBLESHOOTING.md)
- **Database migration**: See migration script logs or contact your administrator
