#!/bin/bash

echo "Deadline Checker Bot - Secure Deployment"
echo "========================================"

if [ ! -f "deploy-config.sh" ]; then
    echo "Configuration file not found!"
    echo ""
    echo "Setup instructions:"
    echo "1. Copy the example config: cp deploy-config.example deploy-config.sh"
    echo "2. Edit deploy-config.sh with your server details:"
    echo "   - SERVER_HOST: Your server IP address"
    echo "   - SERVER_USER: Your server username"
    echo "   - SERVER_PATH: Path to your project on server"
    echo "   - USE_PASSWORD: Authentication method"
    echo ""
    echo "deploy-config.sh is ignored by git for security reasons"
    exit 1
fi

source deploy-config.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

if [ "$SERVER_HOST" = "YOUR_SERVER_IP_HERE" ] || [ -z "$SERVER_HOST" ]; then
    print_error "Please update deploy-config.sh with your actual server IP address!"
    exit 1
fi

print_status "Deploying to $SERVER_USER@$SERVER_HOST:$SERVER_PATH"

if [ "$USE_PASSWORD" = "true" ]; then
    print_warning "Using password authentication - you will be prompted for your password"
else
    print_status "Using SSH key authentication"
fi

print_status "Step 1: Pushing changes to git repository..."
git push origin develop
if [ $? -eq 0 ]; then
    print_success "Code pushed to git repository successfully!"
else
    print_error "Failed to push to git repository"
    exit 1
fi

if [ "$USE_PASSWORD" = "true" ]; then
    SSH_CMD="ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST"
else
    SSH_CMD="ssh -i $SSH_KEY_PATH $SERVER_USER@$SERVER_HOST"
fi

print_status "Step 2: Connecting to server and updating code..."
$SSH_CMD "cd $SERVER_PATH && git pull origin develop"
if [ $? -eq 0 ]; then
    print_success "Code updated on server successfully!"
else
    print_error "Failed to update code on server"
    exit 1
fi

print_status "Step 3: Checking Docker status on server..."
$SSH_CMD "docker --version > /dev/null 2>&1"
if [ $? -eq 0 ]; then
    print_success "Docker is available on server"
else
    print_error "Docker is not installed or not running on server"
    print_status "Please install Docker on your server first"
    exit 1
fi

print_status "Step 4: Stopping existing containers..."
$SSH_CMD "cd $SERVER_PATH && docker-compose down"
if [ $? -eq 0 ]; then
    print_success "Existing containers stopped"
else
    print_warning "No existing containers to stop or failed to stop them"
fi

print_status "Step 5: Building and starting new containers..."
$SSH_CMD "cd $SERVER_PATH && docker-compose build --no-cache && docker-compose up -d"
if [ $? -eq 0 ]; then
    print_success "Containers built and started successfully!"
else
    print_error "Failed to build or start containers"
    exit 1
fi

print_status "Step 6: Checking container status..."
$SSH_CMD "cd $SERVER_PATH && docker-compose ps"
if [ $? -eq 0 ]; then
    print_success "Deployment completed successfully!"
else
    print_warning "Deployment completed but couldn't verify container status"
fi

print_status "Step 7: Showing recent logs..."
$SSH_CMD "cd $SERVER_PATH && docker-compose logs --tail=20"

echo ""
print_success "Deployment completed!"
echo ""
print_status "Useful commands for server management:"
echo "  View logs:      $SSH_CMD 'cd $SERVER_PATH && docker-compose logs -f'"
echo "  Stop bot:       $SSH_CMD 'cd $SERVER_PATH && docker-compose down'"
echo "  Restart bot:    $SSH_CMD 'cd $SERVER_PATH && docker-compose restart'"
echo "  Check status:   $SSH_CMD 'cd $SERVER_PATH && docker-compose ps'"
echo "  Shell access:   $SSH_CMD 'cd $SERVER_PATH && docker-compose exec deadline_checker bash'"