#!/bin/bash

# Deadline Checker Bot - Deployment Script
# This script deploys the bot to your server

echo "🚀 Deadline Checker Bot - Server Deployment"
echo "============================================="

# Configuration - UPDATE THESE VALUES
SERVER_USER="your_username"
SERVER_HOST="your_server_ip_or_domain"
SERVER_PATH="/path/to/your/project"
SSH_KEY_PATH="~/.ssh/your_key"  # Optional: specify SSH key path

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if required variables are set
if [ "$SERVER_USER" = "your_username" ] || [ "$SERVER_HOST" = "your_server_ip_or_domain" ] || [ "$SERVER_PATH" = "/path/to/your/project" ]; then
    print_error "Please update the configuration variables at the top of this script!"
    print_status "Edit deploy.sh and set:"
    echo "  - SERVER_USER: Your server username"
    echo "  - SERVER_HOST: Your server IP or domain"
    echo "  - SERVER_PATH: Path where project will be deployed"
    echo "  - SSH_KEY_PATH: Path to your SSH key (optional)"
    exit 1
fi

# Check if SSH key is provided and exists
if [ "$SSH_KEY_PATH" != "~/.ssh/your_key" ] && [ ! -f "${SSH_KEY_PATH/#\~/$HOME}" ]; then
    print_warning "SSH key not found at $SSH_KEY_PATH, using default SSH authentication"
    SSH_CMD="ssh $SERVER_USER@$SERVER_HOST"
    SCP_CMD="scp"
else
    SSH_CMD="ssh -i $SSH_KEY_PATH $SERVER_USER@$SERVER_HOST"
    SCP_CMD="scp -i $SSH_KEY_PATH"
fi

print_status "Starting deployment to $SERVER_USER@$SERVER_HOST:$SERVER_PATH"

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
$SSH_CMD "cd $SERVER_PATH && git pull origin develop"
if [ $? -eq 0 ]; then
    print_success "Code updated on server successfully!"
else
    print_error "Failed to update code on server"
    exit 1
fi

# Step 3: Check if Docker is running on server
print_status "Step 3: Checking Docker status on server..."
$SSH_CMD "docker --version > /dev/null 2>&1"
if [ $? -eq 0 ]; then
    print_success "Docker is available on server"
else
    print_error "Docker is not installed or not running on server"
    print_status "Please install Docker on your server first"
    exit 1
fi

# Step 4: Stop existing containers
print_status "Step 4: Stopping existing containers..."
$SSH_CMD "cd $SERVER_PATH && docker-compose down"
if [ $? -eq 0 ]; then
    print_success "Existing containers stopped"
else
    print_warning "No existing containers to stop or failed to stop them"
fi

# Step 5: Build and start new containers
print_status "Step 5: Building and starting new containers..."
$SSH_CMD "cd $SERVER_PATH && docker-compose build --no-cache && docker-compose up -d"
if [ $? -eq 0 ]; then
    print_success "Containers built and started successfully!"
else
    print_error "Failed to build or start containers"
    exit 1
fi

# Step 6: Check container status
print_status "Step 6: Checking container status..."
$SSH_CMD "cd $SERVER_PATH && docker-compose ps"
if [ $? -eq 0 ]; then
    print_success "Deployment completed successfully!"
else
    print_warning "Deployment completed but couldn't verify container status"
fi

# Step 7: Show logs
print_status "Step 7: Showing recent logs..."
$SSH_CMD "cd $SERVER_PATH && docker-compose logs --tail=20"

echo ""
print_success "🎉 Deployment completed!"
echo ""
print_status "Useful commands for server management:"
echo "  View logs:      $SSH_CMD 'cd $SERVER_PATH && docker-compose logs -f'"
echo "  Stop bot:       $SSH_CMD 'cd $SERVER_PATH && docker-compose down'"
echo "  Restart bot:    $SSH_CMD 'cd $SERVER_PATH && docker-compose restart'"
echo "  Check status:   $SSH_CMD 'cd $SERVER_PATH && docker-compose ps'"
echo "  Shell access:   $SSH_CMD 'cd $SERVER_PATH && docker-compose exec deadline_checker bash'"
