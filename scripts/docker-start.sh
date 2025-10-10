#!/bin/bash

# Deadline Checker Bot - Docker Start Script
# This script starts the Deadline Checker Bot using Docker Compose

echo "🚀 Starting Deadline Checker Bot..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   Run: open -a Docker"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one with your BOT_TOKEN."
    echo "   Example: echo 'BOT_TOKEN=your_token_here' > .env"
    exit 1
fi

# Check if .config directory exists
if [ ! -d ".config" ]; then
    echo "⚠️  .config directory not found. Creating it..."
    mkdir -p .config/gspread
    echo "   Please add your Google Sheets credentials to .config/gspread/credentials.json"
fi

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

echo "🔨 Building Docker image..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "🚀 Starting container..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ Bot started successfully!"
        echo ""
        echo "📊 Container Status:"
        docker-compose ps
        echo ""
        echo "📋 Useful commands:"
        echo "   View logs:    docker-compose logs -f"
        echo "   Stop bot:     docker-compose down"
        echo "   Restart:      docker-compose restart"
        echo "   Status:       docker-compose ps"
    else
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi
