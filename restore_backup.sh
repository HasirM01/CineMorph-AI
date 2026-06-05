#!/bin/bash

# CineMorph AI - Backup Restoration Script
# Usage: ./restore_backup.sh /path/to/backup/directory

set -e

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Error: Backup directory not specified"
    echo "Usage: ./restore_backup.sh /path/to/backup/directory"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Error: Backup directory does not exist: $BACKUP_DIR"
    exit 1
fi

echo "=================================="
echo "CineMorph AI - Backup Restoration"
echo "=================================="
echo ""
echo "Backup source: $BACKUP_DIR"
echo "Target: /app"
echo ""
read -p "⚠️  This will overwrite current files. Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restoration cancelled"
    exit 0
fi

echo ""
echo "Starting restoration..."
echo ""

# Restore backend
echo "📦 Restoring backend..."
cp -v $BACKUP_DIR/backend/server.py /app/backend/
cp -v $BACKUP_DIR/backend/.env /app/backend/
cp -v $BACKUP_DIR/backend/requirements.txt /app/backend/
echo "✅ Backend restored"
echo ""

# Restore frontend
echo "📦 Restoring frontend..."
rm -rf /app/frontend/src
cp -rv $BACKUP_DIR/frontend/src /app/frontend/
cp -v $BACKUP_DIR/frontend/package.json /app/frontend/
cp -v $BACKUP_DIR/frontend/.env /app/frontend/
cp -v $BACKUP_DIR/frontend/tailwind.config.js /app/frontend/ 2>/dev/null || true
cp -v $BACKUP_DIR/frontend/postcss.config.js /app/frontend/ 2>/dev/null || true
echo "✅ Frontend restored"
echo ""

# Restart services
echo "🔄 Restarting services..."
sudo supervisorctl restart backend frontend
sleep 3
echo "✅ Services restarted"
echo ""

# Verify
echo "🔍 Verifying restoration..."
echo ""

echo "Backend status:"
sudo supervisorctl status backend

echo ""
echo "Frontend status:"
sudo supervisorctl status frontend

echo ""
echo "API test:"
curl -s https://voicecinema-1.preview.emergentagent.com/api/languages | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'✅ API working: {len(data)} languages available')" 2>/dev/null || echo "⚠️  API test failed"

echo ""
echo "=================================="
echo "✅ RESTORATION COMPLETE"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Visit: https://voicecinema-1.preview.emergentagent.com"
echo "2. Test login and basic functionality"
echo "3. Upload a test video and verify mock AI works"
echo ""
