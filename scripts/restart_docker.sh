#!/bin/bash

# Script to rebuild and restart Docker container with proper environment variables
# This ensures all changes are applied and environment variables are loaded correctly

echo "=========================================="
echo "Restarting Email Receipts Docker App"
echo "=========================================="

# Navigate to project directory
cd "$(dirname "$0")/.." || exit 1

# Stop and remove existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down

# Rebuild the image (ensures all code changes are included)
echo ""
echo "Rebuilding Docker image..."
docker-compose build --no-cache

# Start the containers
echo ""
echo "Starting containers..."
docker-compose up -d

# Wait for container to be ready
echo ""
echo "Waiting for container to start..."
sleep 5

# Show container status
echo ""
echo "Container status:"
docker-compose ps

# Show recent logs
echo ""
echo "=========================================="
echo "Recent logs (checking environment):"
echo "=========================================="
docker-compose logs --tail=30

echo ""
echo "=========================================="
echo "Docker restart complete!"
echo "=========================================="
echo ""
echo "To view live logs, run:"
echo "  docker-compose logs -f"
echo ""
echo "To check if emails are being sent:"
echo "  docker-compose logs | grep -i 'email\|brevo\|api key'"
echo ""
