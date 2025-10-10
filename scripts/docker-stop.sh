#!/bin/bash

# Deadline Checker Bot - Docker Stop Script
# This script stops the Deadline Checker Bot

echo "🛑 Stopping Deadline Checker Bot..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running."
    exit 1
fi

# Stop and remove containers
echo "📦 Stopping containers..."
docker-compose down

if [ $? -eq 0 ]; then
    echo "✅ Bot stopped successfully!"
    echo ""
    echo "📊 Container Status:"
    docker-compose ps
    echo ""
    echo "💡 To start again, run: ./scripts/docker-start.sh"
else
    echo "❌ Failed to stop containers"
    exit 1
fi
