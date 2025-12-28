# Brevo Webhook Quick Start

## 🚀 What's New

Your email receipts application now tracks email delivery and engagement in real-time using Brevo webhooks!

## ✨ New Features

### Dashboard Updates
Visit the **Sent Emails** page to see:

| Badge | Meaning |
|-------|---------|
| ✓ Delivered | Email successfully delivered |
| ✗ Hard Bounce | Invalid email or domain |
| ⚠ Soft Bounce | Temporary issue (full mailbox, etc.) |
| 🚫 Blocked | Blocked by recipient's server |
| 🚩 Spam | Marked as spam |
| 👁 Opened | Recipient opened the email |
| 🖱 Clicked | Recipient clicked a link |
| ⏳ Pending... | Waiting for delivery confirmation |

### What Gets Tracked

1. **Delivery Status**: Know exactly what happened to each email
2. **Engagement**: See when emails are opened and links clicked
3. **Failure Reasons**: Detailed bounce/block reasons for troubleshooting
4. **Timestamps**: Precise timing for all events
5. **CSV Export**: All tracking data included in exports

## 🔧 Setup (5 minutes)

### Step 1: Optional Security (Recommended)

Add to your `.env` or `docker-compose.yml`:

```bash
BREVO_WEBHOOK_SECRET=your-random-secret-here
```

Generate a secret:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Restart if using Docker:
```bash
docker compose down && docker compose up -d
```

### Step 2: Configure Brevo Webhook

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Your profile → SMTP & API → Webhooks
3. **Add webhook**:
   - URL: `https://your-domain.com/webhook/brevo`
   - Events: Check all (delivered, bounces, opened, clicked, spam)
4. **Save**

### Step 3: Test It

1. Send a test email using your app
2. Wait 2-5 seconds
3. Refresh "Sent Emails" page
4. You should see "✓ Delivered" status!
5. Open the email → See "👁 Opened"
6. Click a link → See "🖱 Clicked"

## 🧪 Local Testing with ngrok

For testing on localhost:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start your app
docker compose up -d
# or
python3 app.py

# In another terminal, start ngrok
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Use this in Brevo: https://abc123.ngrok.io/webhook/brevo
```

## 📊 Check It's Working

### View Logs
```bash
# Docker
docker compose logs -f web | grep "Brevo webhook"

# Look for:
# INFO: Brevo webhook received: delivered
# INFO: Email <message-id> delivered to user@example.com
```

### Check Brevo Dashboard
- Go to: Webhooks → Your webhook → Recent calls
- Should see `200 OK` responses
- View request/response payloads

## 🐛 Troubleshooting

### Status stays "⏳ Pending..."

**Check:**
- Is webhook configured in Brevo? ✅
- Is webhook URL correct? ✅
- Is URL accessible (HTTPS)? ✅
- Wait 5 seconds and refresh

**Debug:**
```bash
docker compose logs -f web | grep webhook
```

### Webhook returns 401

**Fix:** Verify `BREVO_WEBHOOK_SECRET` matches in both:
- Your environment (.env or docker-compose.yml)
- Brevo webhook configuration

### Nothing happens

**Checklist:**
1. Webhook URL correct in Brevo? ✅
2. Application running? `curl http://localhost:5858/api/health` ✅
3. Database migrated? `docker compose exec web python3 scripts/migrate_email_status.py` ✅
4. Correct events selected in Brevo? ✅

## 📖 Full Documentation

- **Setup Guide**: [docs/WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)
- **Implementation Details**: [docs/WEBHOOK_IMPLEMENTATION_SUMMARY.md](WEBHOOK_IMPLEMENTATION_SUMMARY.md)
- **README**: [README.md](../README.md)

## 🎯 Key Points

✅ **No code changes needed after setup** - webhooks work automatically  
✅ **Real-time updates** - see delivery status within seconds  
✅ **Historical data** - existing emails won't have delivery status (only new emails)  
✅ **Secure** - uses HMAC signature validation  
✅ **Reliable** - handles Brevo retries gracefully  

## 🔐 Security Reminder

- ✅ Always use HTTPS webhook URLs in production
- ✅ Set `BREVO_WEBHOOK_SECRET` environment variable
- ✅ Keep webhook URL private
- ✅ Monitor webhook logs for suspicious activity

## 📞 Need Help?

- Check logs: `docker compose logs -f web`
- Test endpoint: `curl -X POST http://localhost:5858/webhook/brevo -H "Content-Type: application/json" -d '{"event":"delivered","message-id":"test","email":"test@example.com","date":1703750400}'`
- Review [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) for detailed instructions

---

**That's it!** Your email tracking is now live. 🎉
