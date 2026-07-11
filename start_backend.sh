#!/bin/bash
# Backend startup wrapper with dependency check

# Run dependency installer
/app/install_system_deps.sh

# Start backend
cd /app/backend
exec uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
