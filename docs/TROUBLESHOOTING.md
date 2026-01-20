# Troubleshooting Guide

## Common Issues

### Can't Send Emails

#### Issue: "Unauthorized" or Brevo API authentication failed

**Check API key:**
```bash
# Docker
docker compose exec web env | grep BREVO_API_KEY

# Local
echo $BREVO_API_KEY  # or check .env file
```

**Solution:**
1. Verify API key at [Brevo Dashboard](https://app.brevo.com) → Account → SMTP & API → API Keys
2. Ensure it starts with `xkeysib-`
3. Update `.env` file:
   ```
   BREVO_API_KEY=xkeysib-your-actual-key-here
   ```
4. Restart application

#### Issue: "Sender email not verified"

**Solution:**
1. Go to [Brevo Senders](https://app.brevo.com) → Senders
2. Add and verify your sender email
3. Update `.env` with verified email:
   ```
   SENDER_EMAIL=your-verified-email@example.com
   ```
4. Restart application

#### Issue: Emails work locally but not in Docker

**Check environment variables in container:**
```bash
docker compose exec web env | grep -E "BREVO|SENDER"
```

**Solution:**
1. Ensure `.env` file exists in same directory as `docker-compose.yml`
2. Rebuild container:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

### Login Issues

#### Issue: Can't login with credentials

**Check credentials:**
```bash
# Docker
docker compose exec web env | grep ADMIN

# Local
cat .env | grep ADMIN
```

**Solution:**
1. Verify credentials in `.env` file match what you're entering
2. Reset database and recreate admin user:
   ```bash
   # Docker
   docker compose down -v
   docker compose up -d
   
   # Local
   rm -f data/email_receipts.db
   python scripts/init_db.py
   ```

#### Issue: Redirects to login after already logged in

**Solution:**
1. Clear browser cookies
2. Check SECRET_KEY is set in `.env`
3. Generate new SECRET_KEY:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

### Docker Issues

#### Issue: Container won't start

**Check logs:**
```bash
docker compose logs web
```

**Common causes:**
- Port 5858 already in use: Change port in `docker-compose.yml`
- Database connection failed: Check PostgreSQL container is healthy
- Missing `.env` file: Create `.env` from `.env.example`

**Solution:**
```bash
# Full restart
docker compose down -v
docker compose build --no-cache
docker compose up -d

# Check status
docker compose ps
```

#### Issue: Can't access web interface at port 5858

**Check if container is running:**
```bash
docker compose ps
```

**Check if port is accessible:**
```bash
# From server
curl http://localhost:5858/api/health

# From browser
http://your-server-ip:5858
```

**Check port is not blocked:**
```bash
# Check firewall (Linux)
sudo ufw status
sudo ufw allow 5858
```

### Database Issues

#### Issue: "No such table: users" or database errors

**Solution:**
```bash
# Docker
docker compose exec web python scripts/init_db.py

# Local
python scripts/init_db.py
```

#### Issue: PostgreSQL connection refused (Docker)

**Check database container:**
```bash
docker compose ps
docker compose logs db
```

**Solution:**
1. Wait for database to be healthy (can take 10-30 seconds)
2. Restart web container:
   ```bash
   docker compose restart web
   ```

### Webhook Issues

#### Issue: Webhook not receiving events

**Check webhook is configured in Brevo:**
1. Go to [Brevo Dashboard](https://app.brevo.com) → SMTP & API → Webhooks
2. Verify URL is correct: `https://your-domain.com/webhook/brevo`
3. Ensure events are checked: delivered, hard_bounce, soft_bounce, opened, click

**Check webhook logs:**
```bash
# Docker
docker compose logs -f web | grep "webhook"

# Local
# Check console output for webhook-related messages
```

**Test webhook endpoint:**
```bash
curl -X POST http://localhost:5858/webhook/brevo \
  -H "Content-Type: application/json" \
  -d '{"event":"test"}'
```

#### Issue: Delivery status not updating

**Verify:**
1. Email has a `message_id` (check in Sent Emails page)
2. Webhook is configured in Brevo
3. Webhook secret matches (if using `BREVO_WEBHOOK_SECRET`)

**Solution:**
1. Send a test email
2. Check Brevo Dashboard → Logs → Webhook logs for delivery
3. Check application logs for webhook processing

## Getting Help

### Check Configuration

**Docker:**
```bash
# View all environment variables
docker compose exec web env

# Check Brevo configuration
curl http://localhost:5858/api/email-config  # After login
```

**Local:**
```bash
# Test Brevo connection
python -c "
from email_service import EmailService
es = EmailService()
print(f'Configured: {es.is_configured()}')
print(f'Sender: {es.sender_email}')
"
```

### Enable Debug Mode

**Local development only:**
```bash
# In app.py, change:
app.run(host='0.0.0.0', port=5002, debug=True)
```

**⚠️ Never enable debug mode in production!**

### View Application Logs

**Docker:**
```bash
# Live logs
docker compose logs -f web

# Last 100 lines
docker compose logs --tail=100 web

# Filter for errors
docker compose logs web | grep -i error
```

**Local:**
```bash
# Check logs/ directory
cat logs/app.log
```

## Still Having Issues?

1. **Check `.env` file** - Ensure all required variables are set
2. **Run security check** - `python scripts/check_security.py`
3. **Verify Brevo account** - Check email sending quota and limits
4. **Review logs** - Look for specific error messages
5. **Test incrementally** - Start with health check endpoint, then login, then email sending
