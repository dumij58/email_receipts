#!/bin/bash

# Debug script to diagnose email sending issues in Docker

echo "=========================================="
echo "Email Receipts Docker Debugging"
echo "=========================================="

cd "$(dirname "$0")/.." || exit 1

echo ""
echo "1. Container Status:"
echo "-------------------"
docker compose ps

echo ""
echo "2. Environment Variables in Container:"
echo "--------------------------------------"
docker compose exec web env | grep -E "BREVO|SENDER|FLASK|DOCKER" | sort

echo ""
echo "3. Recent Application Logs (last 100 lines):"
echo "--------------------------------------------"
docker compose logs --tail=100 | grep -v "health"

echo ""
echo "4. Email/CSRF Related Logs:"
echo "---------------------------"
docker compose logs | grep -iE "email|brevo|csrf|send" | tail -20

echo ""
echo "5. Error Logs:"
echo "-------------"
docker compose logs | grep -iE "error|exception|failed|warning" | tail -20

echo ""
echo "=========================================="
echo "Debugging complete!"
echo "=========================================="
echo ""
echo "To follow logs in real-time:"
echo "  docker compose logs -f | grep -iE 'email|csrf|error'"
echo ""
