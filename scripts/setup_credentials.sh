#!/bin/bash

# Email Receipts - Setup Script
# This script helps you set up the application credentials

echo "🔐 Email Receipts - Security Setup"
echo "===================================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Do you want to update it? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
else
    # Copy from example if .env doesn't exist
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

echo ""
echo "📝 Let's set up your admin credentials..."
echo ""

# Get admin username
read -p "Enter admin username (press Enter for 'admin'): " admin_user
admin_user=${admin_user:-admin}

# Get admin password
read -s -p "Enter admin password (press Enter for 'admin123'): " admin_pass
echo ""
admin_pass=${admin_pass:-admin123}

# Update .env file with credentials
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^ADMIN_USERNAME=.*/ADMIN_USERNAME=$admin_user/" .env
    sed -i '' "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$admin_pass/" .env
else
    # Linux
    sed -i "s/^ADMIN_USERNAME=.*/ADMIN_USERNAME=$admin_user/" .env
    sed -i "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$admin_pass/" .env
fi

echo ""
echo "✅ Credentials saved to .env file"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "   - Never commit your .env file to version control"
echo "   - Use strong passwords in production"
echo "   - The .env file should be readable only by the application"
echo ""
echo "🚀 You can now run the application with:"
echo "   Local: python app.py"
echo "   Docker: docker compose up -d"
echo ""
