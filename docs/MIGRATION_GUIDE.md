# Migration Guide: Adding Database Support

This guide helps you upgrade from the in-memory user system to the new database-backed system.

## What Changed?

### Before (v1.0)
- Single admin user stored in memory
- No email tracking/history
- User data lost on restart
- Manual credential management via environment variables

### After (v2.0 - Database Support)
- Multiple admin users stored in database
- Complete email tracking with transaction IDs
- Persistent user and email data
- Web-based sent emails viewing with filters and export
- PostgreSQL for production, SQLite for development

## Migration Steps

### For Local Development

1. **Pull Latest Code**
   ```bash
   git pull origin main
   ```

2. **Install New Dependencies**
   ```bash
   source venv/bin/activate  # Activate your virtual environment
   pip install -r requirements.txt
   ```

3. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```
   
   This will:
   - Create `data/email_receipts.db` SQLite database
   - Create tables for users and sent emails
   - Migrate your existing admin user (from env vars) to the database

4. **Update `.env` File** (if needed)
   ```bash
   # Your existing credentials will be used to create the first admin user
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   ADMIN_EMAIL=admin@example.com  # Optional, new field
   ```

5. **Start Application**
   ```bash
   python app.py
   ```

6. **Verify Login**
   - Go to http://localhost:5002
   - Login with your admin credentials
   - Navigate to "Sent Emails" to see the new feature

### For Docker Deployment

1. **Pull Latest Code**
   ```bash
   git pull origin main
   ```

2. **Update Environment Variables** (`.env` file)
   ```bash
   # Add new database password (or keep default for testing)
   # The DATABASE_URL is auto-configured in docker-compose.yml
   
   # Ensure admin credentials are set
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-production-password
   ADMIN_EMAIL=admin@example.com
   
   # Optional: Custom PostgreSQL password
   POSTGRES_PASSWORD=my-secure-db-password
   ```

3. **Stop Existing Containers**
   ```bash
   docker-compose down
   ```

4. **Rebuild and Start**
   ```bash
   docker-compose up -d --build
   ```
   
   This will:
   - Build new Docker image with database support
   - Start PostgreSQL container
   - Initialize database automatically
   - Create default admin user
   - Start the web application

5. **Verify Deployment**
   ```bash
   # Check all containers are running
   docker-compose ps
   
   # View logs
   docker-compose logs -f web
   docker-compose logs -f db
   ```

6. **Access Application**
   - Go to http://your-server:5858
   - Login with admin credentials
   - Check "Sent Emails" page works

## Data Considerations

### No Data Loss
- Your existing admin credentials from environment variables will be used to create the first database user
- No previous email history exists (tracking starts from v2.0)
- All future emails will be logged automatically

### Credentials
Your existing `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables will be used to create the first admin user in the database. After that:
- You can add more users programmatically (see DATABASE.md)
- Users are persistent across restarts
- Login uses database instead of environment variables

## Rollback (If Needed)

If you need to rollback to the previous version:

### Local Development
```bash
git checkout v1.0  # Or your previous commit
pip install -r requirements.txt  # Reinstall old dependencies
python app.py
```

### Docker
```bash
git checkout v1.0
docker-compose down
docker-compose up -d --build
```

The old version will continue to work with your existing environment variables.

## Common Issues

### "ModuleNotFoundError: No module named 'flask_sqlalchemy'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### "No such table: users"
**Solution**: Initialize database
```bash
python scripts/init_db.py
```

### Docker: Database connection refused
**Solution**: 
1. Check if database container is running: `docker-compose ps`
2. Wait for database to be healthy: `docker-compose logs db`
3. Restart if needed: `docker-compose restart web`

### Can't login after migration
**Solution**:
1. Check your `.env` file has correct credentials
2. Delete database and reinitialize:
   ```bash
   # Local
   rm -f data/email_receipts.db
   python scripts/init_db.py
   
   # Docker
   docker-compose down -v  # Removes volumes
   docker-compose up -d
   ```

## New Features Available

After migration, you now have access to:

1. **Sent Emails Page** (`/sent-emails`)
   - View all sent email receipts
   - Filter by status (success/failed)
   - Filter by date range
   - Search by recipient email or name
   - Pagination (20/50/100 per page)
   - Export to CSV

2. **Email Tracking**
   - Every email automatically logged
   - Brevo message IDs captured
   - Success/failure status tracked
   - Error messages recorded
   - Sender identification (which admin sent it)

3. **Multi-User Support**
   - Can add multiple admin users
   - Each user has their own credentials
   - Last login timestamps tracked
   - Users can be activated/deactivated

## Testing the Migration

1. **Test Login**
   - Use your existing admin credentials
   - Should work exactly as before

2. **Send Test Email**
   - Go to "Send Single"
   - Send a test email
   - Go to "Sent Emails" page
   - Verify email appears in the list

3. **Test Filters**
   - Try different filter combinations
   - Test date range filtering
   - Test search functionality
   - Test different pagination sizes

4. **Test CSV Export**
   - Apply some filters
   - Click "Export to CSV"
   - Verify file downloads correctly
   - Open CSV to verify data

## Support

If you encounter issues:

1. Check `docs/DATABASE.md` for detailed documentation
2. Check application logs:
   - Local: Console output
   - Docker: `docker-compose logs web`
3. Verify environment variables are set correctly
4. Ensure database is initialized properly

## Verification Checklist

- [ ] Dependencies installed successfully
- [ ] Database initialized (no errors)
- [ ] Can login with admin credentials
- [ ] Dashboard loads correctly
- [ ] Can send single email
- [ ] Can send bulk emails
- [ ] "Sent Emails" page works
- [ ] Email tracking is working
- [ ] Filters work correctly
- [ ] CSV export works
- [ ] Docker deployment successful (if applicable)
- [ ] PostgreSQL container running (if Docker)

Congratulations! You've successfully migrated to the database-backed system. 🎉
