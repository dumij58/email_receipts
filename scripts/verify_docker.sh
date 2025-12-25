#!/bin/bash
# Docker Deployment Verification Script
# Run this on your server to verify Docker setup

echo "========================================"
echo "Email Receipts - Docker Deployment Check"
echo "========================================"
echo ""

# Check if .env file exists
echo "1. Checking .env file..."
if [ -f .env ]; then
    echo "   ✓ .env file exists"
    if grep -q "ADMIN_USERNAME" .env && grep -q "ADMIN_PASSWORD" .env; then
        echo "   ✓ ADMIN credentials found in .env"
        ADMIN_USER=$(grep "ADMIN_USERNAME" .env | cut -d '=' -f2)
        echo "   → Admin username: $ADMIN_USER"
    else
        echo "   ✗ ADMIN credentials missing in .env"
    fi
else
    echo "   ✗ .env file not found!"
    echo "   → Create .env file with ADMIN_USERNAME and ADMIN_PASSWORD"
fi
echo ""

# Check Docker
echo "2. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✓ Docker installed"
    docker --version
else
    echo "   ✗ Docker not installed"
fi
echo ""

# Check Docker Compose
echo "3. Checking Docker Compose..."
if command -v docker compose &> /dev/null; then
    echo "   ✓ Docker Compose installed"
    docker compose --version
else
    echo "   ✗ Docker Compose not installed"
fi
echo ""

# Check if container is running
echo "4. Checking container status..."
if docker ps | grep -q email-receipts-app; then
    echo "   ✓ Container is running"
    docker compose ps
else
    echo "   ✗ Container is not running"
    echo "   → Run: docker compose up -d"
fi
echo ""

# Check port
echo "5. Checking port 5858..."
if netstat -tuln 2>/dev/null | grep -q ":5858" || ss -tuln 2>/dev/null | grep -q ":5858"; then
    echo "   ✓ Port 5858 is listening"
else
    echo "   ✗ Port 5858 is not listening"
    echo "   → Container might not be running or port mapping is wrong"
fi
echo ""

# Test health endpoint
echo "6. Testing health endpoint..."
if curl -s -f http://localhost:5858/api/health &> /dev/null; then
    echo "   ✓ Health check passed"
    curl -s http://localhost:5858/api/health
else
    echo "   ✗ Health check failed"
    echo "   → Application might not be running properly"
fi
echo ""

# Check environment variables in container
echo "7. Checking environment variables in container..."
if docker ps | grep -q email-receipts-app; then
    ENV_CHECK=$(docker compose exec -T web env | grep "ADMIN_USERNAME" 2>/dev/null)
    if [ -n "$ENV_CHECK" ]; then
        echo "   ✓ Environment variables loaded"
        docker compose exec -T web env | grep "ADMIN_USERNAME"
    else
        echo "   ✗ Environment variables not loaded"
        echo "   → Rebuild container: docker compose down && docker compose up -d"
    fi
else
    echo "   ⊘ Container not running, skipping check"
fi
echo ""

# Check logs
echo "8. Recent logs (last 20 lines)..."
if docker ps | grep -q email-receipts-app; then
    docker compose logs --tail=20 web
else
    echo "   ⊘ Container not running, no logs available"
fi
echo ""

# Summary
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "To deploy/redeploy:"
echo "  1. Ensure .env file exists with ADMIN_USERNAME and ADMIN_PASSWORD"
echo "  2. Run: docker compose down"
echo "  3. Run: docker compose build --no-cache"
echo "  4. Run: docker compose up -d"
echo "  5. Check logs: docker compose logs -f web"
echo ""
echo "To test login:"
echo "  curl -i -X POST http://localhost:5858/login \\"
echo "    -d \"username=$ADMIN_USER&password=YOUR_PASSWORD\" \\"
echo "    -H \"Content-Type: application/x-www-form-urlencoded\""
echo ""
echo "Access application at: http://YOUR_SERVER_IP:5858"
echo ""
