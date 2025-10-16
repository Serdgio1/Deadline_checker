# Docker Setup Guide for Deadline Checker Bot

## 🐳 Docker Configuration Fixed

Your Docker setup has been improved with the following enhancements:

### ✅ **Fixed Issues:**

1. **Security Improvements:**

   - Added non-root user (`appuser`)
   - Proper file permissions
   - Secure environment variable handling

2. **Performance Optimizations:**

   - Added `.dockerignore` to reduce build context
   - Optimized layer caching
   - Added health checks

3. **Better Configuration:**
   - Proper volume mounting
   - Logging configuration
   - Network isolation
   - Environment file handling

## 🚀 **Quick Start**

### 1. Start Docker Desktop

Make sure Docker Desktop is running on your Mac.

### 2. Build and Run

```bash
# Build the image
docker-compose build

# Run the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 3. Development Mode

```bash
# Run with live logs
docker-compose up

# Rebuild and restart
docker-compose up --build
```

## 📁 **File Structure**

```
Deadline_checker/
├── Dockerfile              # ✅ Improved with security & performance
├── docker-compose.yml      # ✅ Enhanced configuration
├── .dockerignore           # ✅ NEW - Optimizes build process
├── docker-setup.md         # ✅ NEW - This guide
└── scripts/
    ├── docker-start.sh     # ✅ NEW - Helper script
    └── docker-stop.sh      # ✅ NEW - Helper script
```

## 🔧 **Configuration Details**

### Dockerfile Improvements:

- **Base Image:** `python:3.11-slim`
- **Security:** Non-root user execution
- **Health Check:** Database connectivity test
- **Environment:** Optimized Python settings
- **Dependencies:** System packages for compilation

### Docker Compose Features:

- **Restart Policy:** `unless-stopped`
- **Health Check:** SQLite database test
- **Logging:** JSON file with rotation
- **Volumes:** Persistent data storage
- **Network:** Isolated bridge network

## 🛠️ **Troubleshooting**

### Common Issues:

1. **Docker Daemon Not Running:**

   ```bash
   # Start Docker Desktop application
   open -a Docker
   ```

2. **Permission Issues:**

   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER .
   ```

3. **Build Failures:**

   ```bash
   # Clean build
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   ```

4. **Environment Variables:**
   Make sure your `.env` file exists:
   ```bash
   # Check .env file
   ls -la .env
   ```

## 📊 **Monitoring**

### Health Checks:

- Container health is monitored every 30 seconds
- Database connectivity is tested
- Automatic restart on failure

### Logs:

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs deadline_checker
```

### Container Status:

```bash
# Check container status
docker-compose ps

# View container details
docker inspect deadline_checker_container
```

## 🔒 **Security Features**

1. **Non-root User:** Container runs as `appuser`
2. **File Permissions:** Proper ownership and permissions
3. **Environment Isolation:** Secure environment variable handling
4. **Network Isolation:** Custom bridge network
5. **Volume Security:** Only necessary files mounted

## 📈 **Performance Features**

1. **Build Optimization:** `.dockerignore` reduces build context
2. **Layer Caching:** Optimized layer structure
3. **Health Monitoring:** Automatic health checks
4. **Log Rotation:** Prevents disk space issues
5. **Resource Management:** Proper restart policies

## 🎯 **Next Steps**

1. Start Docker Desktop
2. Run `docker-compose up -d`
3. Check logs with `docker-compose logs -f`
4. Verify bot functionality
5. Monitor with `docker-compose ps`

Your Docker setup is now production-ready! 🚀
