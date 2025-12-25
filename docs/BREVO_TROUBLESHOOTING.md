# Brevo Email Troubleshooting Guide for Docker

## Problem: Emails work locally but not in Docker

### Quick Diagnosis

1. **Check if Brevo credentials are loaded in container:**
```bash
docker-compose exec web env | grep BREVO
```

Should output:
```
BREVO_API_KEY=your-brevo-api-key
SENDER_EMAIL=your-verified-email@example.com
```

If any are missing, the .env file is not being read properly.

2. **Check email configuration via API:**

After logging in to the web interface, visit:
```
http://YOUR_SERVER_IP:5858/api/email-config
```

This will show:
- Email service (Brevo)
- Whether API key is set
- Sender email and name
- Configuration status

3. **Check Docker logs for errors:**
```bash
docker-compose logs web | grep -i "brevo\|email\|failed to send"
```

## Common Issues & Solutions

### Issue 1: Environment variables not loading

**Symptoms:**
- BREVO_API_KEY is empty
- API shows "is_configured": false

**Solution:**
```bash
# 1. Verify .env file exists
cat .env | grep BREVO

# 2. Ensure .env is in same directory as docker-compose.yml
pwd
ls -la .env docker-compose.yml

# 3. Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 4. Verify again
docker-compose exec web env | grep BREVO
```

### Issue 2: Brevo Authentication Error

**Symptoms:**
- Error: "Unauthorized" or API authentication failed
- Log shows: "Brevo API Exception"

**Solution:**

1. **Verify your API key:**
   - Go to: https://app.brevo.com → Account → SMTP & API → API Keys
   - Make sure the key has the correct permissions
   - Copy the key exactly (starts with `xkeysib-`)
   
2. **Update .env file:**
```bash
BREVO_API_KEY=xkeysib-your-actual-api-key-here
SENDER_EMAIL=your-verified-email@example.com
```

3. **Rebuild:**
```bash
docker-compose down
docker-compose up -d
```

### Issue 3: Sender Email Not Verified

**Symptoms:**
- Error: "Sender email not verified"
- Emails not sending

**Solution:**

1. **Verify your sender email in Brevo:**
   - Go to: https://app.brevo.com → Senders
   - Click "Add a Sender"
   - Enter your email and verify it
   
2. **Use the verified email in .env:**
```bash
SENDER_EMAIL=your-verified-email@example.com
```

3. **Rebuild:**
```bash
docker-compose down
docker-compose up -d
```

### Issue 4: Network connectivity from Docker

**Symptoms:**
- Timeout errors
- Cannot connect to Brevo API

**Solution:**

1. **Test network from container:**
```bash
# Test internet connectivity
docker-compose exec web curl -I https://api.brevo.com

# Check if container can access external APIs
docker-compose exec web curl -I https://www.google.com
```

2. **If connection fails, check Docker network:**
```bash
# Restart Docker daemon if needed
sudo systemctl restart docker
```

3. **Check firewall rules:**
```bash
# Allow outbound on port 587
sudo iptables -A OUTPUT -p tcp --dport 587 -j ACCEPT
```

### Issue 4: Wrong API key format

**Common mistakes:**

❌ Wrong:
```
BREVO_API_KEY=your-api-key-here    # Placeholder text
BREVO_API_KEY=SG.abc123...         # SendGrid key (wrong service)
```

✅ Correct:
```
BREVO_API_KEY=xkeysib-caf0e2e8...  # Actual Brevo key (starts with xkeysib-)
```

### Issue 5: .env file format errors

**Common mistakes:**

❌ Wrong:
```
BREVO_API_KEY = your-key-here     # Spaces around =
BREVO_API_KEY='your-key-here'     # Quotes around value
```

✅ Correct:
```
BREVO_API_KEY=xkeysib-your-actual-key-here
SENDER_EMAIL=your-verified-email@example.com
```

## Testing Email Sending

### Test 1: Check configuration
```bash
docker-compose exec web python3 -c "
from email_service import EmailService
es = EmailService()
print(f'Configured: {es.is_configured()}')
print(f'API Key set: {bool(es.brevo_api_key)}')
print(f'Sender Email: {es.sender_email}')
"
```

### Test 2: Test Brevo API connection
```bash
docker-compose exec web python3 -c "
import sib_api_v3_sdk
import os

api_key = os.environ.get('BREVO_API_KEY')
print(f'API Key configured: {bool(api_key)}')

if api_key:
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        account_info = api_instance.get_account()
        print(f'✓ Connected to Brevo API')
        print(f'✓ Account email: {account_info.email}')
        print(f'✓ All tests passed!')
    except Exception as e:
        print(f'✗ Error: {e}')
else:
    print('✗ API key not set')
"
```

### Test 3: Send test email
```bash
# Replace with your email
docker-compose exec web python3 -c "
from email_service import EmailService
from datetime import datetime

es = EmailService()
result = es.send_single_receipt(
    'your-test-email@example.com',
    'Test Recipient',
    'SYNEXIS25',
    '1000.00',
    datetime.now().strftime('%Y-%m-%d')
)
print(f'Email sent: {result}')
"
```

## Debug Checklist

Run through this checklist:

- [ ] .env file exists in project root
- [ ] .env contains BREVO_API_KEY (starts with xkeysib-)
- [ ] .env contains SENDER_EMAIL (verified in Brevo)
- [ ] No spaces around = in .env
- [ ] Container rebuilt after .env changes
- [ ] Environment variables visible in container (`docker-compose exec web env | grep BREVO`)
- [ ] Network connectivity from container to api.brevo.com
- [ ] Sender email verified in Brevo dashboard
- [ ] API key has correct permissions
- [ ] Logs show Brevo configuration loaded (`docker-compose logs web | grep -i brevo`)
- [ ] API endpoint shows is_configured: true

## View Detailed Logs

```bash
# Watch logs in real-time
docker-compose logs -f web

# Filter for email-related logs
docker-compose logs web | grep -i "email\|smtp"

# Last 50 lines
docker-compose logs --tail=50 web
```

## Complete Reset (Nuclear Option)

If nothing works, start completely fresh:

```bash
# 1. Stop everything
docker-compose down -v

# 2. Remove all containers and images
docker system prune -a -f

# 3. Verify .env file
cat .env

# 4. Rebuild from scratch
docker-compose build --no-cache

# 5. Start with logs visible
docker-compose up

# Watch the logs as it starts to see any errors
```

## Still Not Working?

1. **Check container logs during email send:**
```bash
# In one terminal, watch logs:
docker-compose logs -f web

# In another, try sending an email from the web interface
```

2. **Enable debug logging:**
Add to docker-compose.yml under environment:
```yaml
- FLASK_ENV=development  # Enables verbose logging
```

Then rebuild: `docker-compose down && docker-compose up -d`

3. **Verify sender email in Brevo:**
- Go to https://app.brevo.com → Senders
- Make sure your SENDER_EMAIL is verified
- Check that the email matches exactly

## Brevo-Specific Troubleshooting

### "Unauthorized" or 401 Error
- Your API key is invalid or expired
- Generate a new API key from Brevo dashboard
- Make sure you copied the entire key (starts with xkeysib-)

### "Sender email not verified"
- You must verify your sender email in Brevo dashboard
- Go to: Senders → Add a Sender → Verify
- Check your email for verification link

### Rate limiting
- Free tier: 300 emails per day
- Check your Brevo dashboard for usage
- Upgrade if you need more capacity

### API Key Permissions
- Make sure your API key has "Send emails" permission
- Check in: Account → SMTP & API → API Keys

## Quick Reference

```bash
# Check config
docker-compose exec web env | grep BREVO

# Test API connection
docker-compose exec web curl -I https://api.brevo.com

# View logs
docker-compose logs -f web

# Restart container
docker-compose restart web

# Full rebuild
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Check API endpoint
curl http://localhost:5858/api/email-config  # After login
```
