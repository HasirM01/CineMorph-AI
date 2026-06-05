# CineMorph AI - Local Setup Guide

## After Cloning from GitHub

### 1. Install Backend Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Backend Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=cinemorph_ai
CORS_ORIGINS=http://localhost:3000
AI_MODE=mock  # Start with mock mode
```

### 3. Install Frontend Dependencies

```bash
cd ../frontend

# Install with Yarn (recommended)
yarn install

# Or with npm
npm install
```

### 4. Configure Frontend Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env
nano .env
```

Required environment variables:
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 5. Start MongoDB

```bash
# On macOS with Homebrew
brew services start mongodb-community

# On Linux
sudo systemctl start mongod

# Or with Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 6. Run Backend

```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: http://localhost:8001

### 7. Run Frontend

```bash
cd frontend
yarn start
```

Frontend will be available at: http://localhost:3000

### 8. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

### 9. Test the Application

1. Visit http://localhost:3000
2. Click "Sign In" (will redirect to Emergent auth in production)
3. For local testing without auth, modify the frontend to skip auth temporarily

### 10. Directory Structure

```
cinemorph-ai/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   ├── .env (create this)
│   └── storage/
│       ├── uploads/
│       ├── processed/
│       └── temp/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env (create this)
└── README.md
```

### Troubleshooting

**Backend won't start:**
- Check MongoDB is running: `mongosh` or `mongo`
- Verify Python version: `python --version` (need 3.9+)
- Check port 8001 is free: `lsof -i :8001`

**Frontend won't start:**
- Verify Node version: `node --version` (need 16+)
- Clear cache: `rm -rf node_modules && yarn install`
- Check port 3000 is free: `lsof -i :3000`

**CORS errors:**
- Ensure backend CORS_ORIGINS includes frontend URL
- Check backend .env has correct CORS_ORIGINS value

### Next Steps

1. Review `/app/README.md` for full documentation
2. Check `/app/auth_testing.md` for authentication setup
3. See `/app/design_guidelines.json` for UI specifications

### Development Mode vs Production

**Local Development:**
- Uses `AI_MODE=mock` (no costs)
- Local MongoDB instance
- Development servers (reload on change)

**Production (Emergent):**
- Uses `AI_MODE=real` (with Emergent LLM key)
- Production MongoDB
- Optimized builds
- Emergent authentication

