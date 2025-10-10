# 🚀 Server Deployment Guide

## ✅ **Container Stopped & Code Updated**

Your local container has been stopped and all changes have been pushed to your git repository.

## 📋 **Deployment Steps**

### **Option 1: Automated Deployment (Recommended)**

#### **For Password Authentication (Easiest):**

1. **Run the password deployment script:**
   ```bash
   ./deploy-with-password.sh
   ```
   This script is already configured for your server and will prompt you for your password when needed.

#### **For SSH Key Authentication:**

1. **Edit the deployment script:**
   ```bash
   nano deploy.sh
   ```
2. **Update these variables at the top of the file:**

   ```bash
   SERVER_USER="root"
   SERVER_HOST="88.218.122.148"
   SERVER_PATH="/root/itmo_bot/Deadline_checker"
   USE_PASSWORD="false"  # Set to "false" for SSH key authentication
   SSH_KEY_PATH="~/.ssh/your_private_key"
   ```

3. **Run the deployment:**
   ```bash
   ./deploy.sh
   ```

### **Option 2: Manual Deployment**

1. **Connect to your server:**

   ```bash
   ssh your_username@your_server_ip
   ```

2. **Navigate to your project directory:**

   ```bash
   cd /path/to/your/project
   ```

3. **Pull the latest changes:**

   ```bash
   git pull origin develop
   ```

4. **Stop existing containers:**

   ```bash
   docker-compose down
   ```

5. **Build and start new containers:**

   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

6. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

## 🔧 **Server Requirements**

Make sure your server has:

- ✅ Docker installed and running
- ✅ Docker Compose installed
- ✅ Git installed
- ✅ SSH access configured
- ✅ `.env` file with `BOT_TOKEN`
- ✅ Google Sheets credentials in `.config/gspread/credentials.json`

## 📁 **Server File Structure**

Your server should have this structure:

```
/path/to/your/project/
├── .env                    # Bot token
├── .config/
│   └── gspread/
│       └── credentials.json  # Google Sheets API credentials
├── docker-compose.yml
├── Dockerfile
├── main.py
└── ... (other project files)
```

## 🛠️ **Server Setup Commands**

If you need to set up the project on a fresh server:

```bash
# Clone the repository
git clone https://github.com/Serdgio1/Deadline_checker.git
cd Deadline_checker

# Create necessary directories
mkdir -p .config/gspread
mkdir -p logs

# Create .env file
echo "BOT_TOKEN=your_bot_token_here" > .env

# Add Google Sheets credentials
# Copy your credentials.json to .config/gspread/credentials.json

# Start the bot
docker-compose up -d
```

## 📊 **Monitoring Commands**

Once deployed, use these commands to monitor your bot:

```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart if needed
docker-compose restart

# Stop the bot
docker-compose down

# Access container shell
docker-compose exec deadline_checker bash
```

## 🔒 **Security Notes**

- ✅ Bot runs as non-root user
- ✅ Health checks enabled
- ✅ Log rotation configured
- ✅ Network isolation
- ✅ Secure environment handling

## 🆘 **Troubleshooting**

### Common Issues:

1. **Docker not running:**

   ```bash
   sudo systemctl start docker
   ```

2. **Permission issues:**

   ```bash
   sudo chown -R $USER:$USER .
   ```

3. **Environment variables missing:**

   ```bash
   # Check .env file exists and has BOT_TOKEN
   cat .env
   ```

4. **Google Sheets API issues:**
   ```bash
   # Verify credentials file exists
   ls -la .config/gspread/credentials.json
   ```

## 📞 **Support**

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify all requirements are met
3. Check the troubleshooting section above

Your bot is now ready for production deployment! 🎉
