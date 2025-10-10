#!/bin/bash

# Deadline Checker Bot - Docker Logs Script
# This script shows logs from the Deadline Checker Bot

echo "📋 Deadline Checker Bot Logs"
echo "=============================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running."
    exit 1
fi

# Show logs with follow option if requested
if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
    echo "🔄 Following logs (Press Ctrl+C to stop)..."
    docker-compose logs -f
else
    echo "📄 Recent logs:"
    docker-compose logs --tail=50
    echo ""
    echo "💡 To follow logs in real-time: $0 -f"
fi
