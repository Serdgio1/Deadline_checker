#!/bin/bash

# Deadline Checker Bot - Password-based Deployment Script
# This script deploys the bot using password authentication

echo "🚀 Deadline Checker Bot - Password Deployment"
echo "=============================================="

# Configuration - UPDATE THESE VALUES FOR YOUR SERVER
SERVER_USER="root"
SERVER_HOST="YOUR_SERVER_IP_HERE"
SERVER_PATH="/root/itmo_bot/Deadline_checker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Deploying to $SERVER_USER@$SERVER_HOST:$SERVER_PATH"
print_warning "You will be prompted for your server password multiple times"

# Step 1: Push to git repository
print_status "Step 1: Pushing changes to git repository..."
git push origin develop
if [ $? -eq 0 ]; then
    print_success "Code pushed to git repository successfully!"
else
    print_error "Failed to push to git repository"
    exit 1
fi

# Step 2: Connect to server and pull changes
print_status "Step 2: Connecting to server and updating code..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && git pull origin develop"
if [ $? -eq 0 ]; then
    print_success "Code updated on server successfully!"
else
    print_error "Failed to update code on server"
    exit 1
fi

# Step 3: Check if Docker is running on server
print_status "Step 3: Checking Docker status on server..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "docker --version > /dev/null 2>&1"
if [ $? -eq 0 ]; then
    print_success "Docker is available on server"
else
    print_error "Docker is not installed or not running on server"
    print_status "Please install Docker on your server first"
    exit 1
fi

# Step 4: Stop existing containers
print_status "Step 4: Stopping existing containers..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose down"
if [ $? -eq 0 ]; then
    print_success "Existing containers stopped"
else
    print_warning "No existing containers to stop or failed to stop them"
fi

# Step 5: Build and start new containers
print_status "Step 5: Building and starting new containers..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose build --no-cache && docker-compose up -d"
if [ $? -eq 0 ]; then
    print_success "Containers built and started successfully!"
else
    print_error "Failed to build or start containers"
    exit 1
fi

# Step 6: Check container status
print_status "Step 6: Checking container status..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose ps"
if [ $? -eq 0 ]; then
    print_success "Deployment completed successfully!"
else
    print_warning "Deployment completed but couldn't verify container status"
fi

# Step 7: Show logs
print_status "Step 7: Showing recent logs..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose logs --tail=20"

echo ""
print_success "🎉 Deployment completed!"
echo ""
print_status "Useful commands for server management:"
echo "  View logs:      ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose logs -f'"
echo "  Stop bot:       ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose down'"
echo "  Restart bot:    ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose restart'"
echo "  Check status:   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose ps'"
echo "  Shell access:   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose exec deadline_checker bash'"
