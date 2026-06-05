# CineMorph AI - System Dependencies

This document lists all system-level dependencies required for CineMorph AI to function properly.

---

## Critical Dependencies

### 1. FFmpeg (REQUIRED)
**Purpose:** Video/audio processing for AI dubbing pipeline

**Required For:**
- Audio extraction from uploaded videos
- Video duration detection (ffprobe)
- Multi-audio track MP4 generation
- Audio format conversion

**Installation:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**Verification:**
```bash
ffmpeg -version
ffprobe -version
```

**Minimum Version:** 4.x or higher  
**Tested Version:** 7:5.1.9-0+deb12u1

---

### 2. MongoDB (REQUIRED)
**Purpose:** Primary database for user data, movies, jobs

**Required For:**
- User authentication and sessions
- Movie metadata storage
- Dubbing job tracking
- Analytics data

**Installation:**
```bash
# MongoDB 7.0 Community Edition
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

**Verification:**
```bash
mongosh --eval "db.version()"
```

**Minimum Version:** 5.x or higher  
**Tested Version:** 7.0

---

### 3. Python 3.11+ (REQUIRED)
**Purpose:** Backend API server

**Required For:**
- FastAPI application
- AI integrations (emergentintegrations)
- MongoDB driver (Motor)
- Async task processing

**Installation:**
```bash
sudo apt-get install -y python3.11 python3.11-venv python3-pip
```

**Verification:**
```bash
python3 --version
```

**Minimum Version:** 3.11  
**Tested Version:** 3.11

---

### 4. Node.js 20+ (REQUIRED)
**Purpose:** Frontend build and runtime

**Required For:**
- React application build
- Yarn package manager
- Frontend development server

**Installation:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Verification:**
```bash
node --version
npm --version
```

**Minimum Version:** 20.x  
**Tested Version:** 20.x

---

### 5. Yarn (REQUIRED)
**Purpose:** Frontend package management

**Required For:**
- Installing React dependencies
- Building frontend assets
- Running development server

**Installation:**
```bash
npm install -g yarn
```

**Verification:**
```bash
yarn --version
```

**Minimum Version:** 1.22+

---

## Runtime Dependencies

### System Libraries
These are typically installed automatically with the above packages:

- **libssl** - SSL/TLS support
- **build-essential** - Compilation tools for native modules
- **git** - Version control (optional, for deployment)

**Installation:**
```bash
sudo apt-get install -y build-essential libssl-dev git
```

---

## Python Dependencies
Managed via `requirements.txt`:

```bash
cd /app/backend
pip install -r requirements.txt
```

**Key Packages:**
- fastapi
- uvicorn
- motor (MongoDB async driver)
- emergentintegrations (Emergent LLM integrations)
- python-dotenv
- aiofiles

---

## Node.js Dependencies
Managed via `package.json`:

```bash
cd /app/frontend
yarn install
```

**Key Packages:**
- react
- react-router-dom
- axios
- tailwindcss
- framer-motion
- shadcn/ui components

---

## Environment Configuration

### Backend (.env)
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
EMERGENT_LLM_KEY=sk-emergent-xxx
AI_MODE=real
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://your-backend-url.com
```

---

## Validation Checklist

Before deploying CineMorph AI, verify:

### System Dependencies
- [ ] FFmpeg installed and in PATH
- [ ] ffprobe installed and in PATH
- [ ] MongoDB running and accessible
- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] Yarn installed

### Services
- [ ] MongoDB service running (`sudo systemctl status mongod`)
- [ ] Backend service running (`sudo supervisorctl status backend`)
- [ ] Frontend service running (`sudo supervisorctl status frontend`)

### Health Checks
```bash
# Backend health
curl http://localhost:8001/api/config/ai

# Frontend health
curl http://localhost:3000

# MongoDB health
mongosh --eval "db.runCommand({ ping: 1 })"
```

---

## Troubleshooting

### FFmpeg Not Found
**Symptom:** Cost estimation fails with "No such file or directory: 'ffprobe'"

**Solution:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
sudo supervisorctl restart backend
```

### MongoDB Connection Failed
**Symptom:** Backend fails to start with MongoDB connection error

**Solution:**
```bash
sudo systemctl start mongod
sudo systemctl enable mongod  # Auto-start on boot
```

### Python Package Issues
**Symptom:** ImportError or ModuleNotFoundError

**Solution:**
```bash
cd /app/backend
pip install --upgrade pip
pip install -r requirements.txt
sudo supervisorctl restart backend
```

### Node.js/Yarn Issues
**Symptom:** Frontend build fails or dependencies missing

**Solution:**
```bash
cd /app/frontend
rm -rf node_modules
yarn install
sudo supervisorctl restart frontend
```

---

## Deployment Notes

### Production Checklist
1. Install all system dependencies
2. Set up environment variables
3. Run backend startup validation (automatic)
4. Verify FFmpeg availability at startup
5. Test cost estimation workflow
6. Monitor logs for any missing dependencies

### Docker Deployment (Recommended)
For containerized deployment, create a Dockerfile:

```dockerfile
FROM ubuntu:22.04

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3.11 \
    python3-pip \
    nodejs \
    npm \
    mongodb-org \
    && rm -rf /var/lib/apt/lists/*

# Application setup
COPY . /app
WORKDIR /app

# Backend
RUN pip install -r backend/requirements.txt

# Frontend
RUN npm install -g yarn
RUN cd frontend && yarn install && yarn build

EXPOSE 8001 3000
```

---

## Support

For issues related to dependencies:
1. Check this document for installation instructions
2. Verify versions match minimum requirements
3. Review RCA documents in `/app/` for known issues
4. Check backend logs: `/var/log/supervisor/backend.err.log`

---

**Last Updated:** June 5, 2026  
**Document Version:** 1.0
