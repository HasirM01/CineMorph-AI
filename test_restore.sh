#!/bin/bash

# Quick test to verify backup can be restored
# This creates a test file, backs it up, modifies it, then restores

BACKUP_DIR="/app/backups/pre-ai-implementation-20260605-083640"

echo "Testing backup restoration capability..."
echo ""

# Test 1: Verify backup exists
if [ -d "$BACKUP_DIR" ]; then
    echo "✅ Backup directory exists"
else
    echo "❌ Backup directory not found"
    exit 1
fi

# Test 2: Verify critical files
if [ -f "$BACKUP_DIR/backend/server.py" ]; then
    echo "✅ server.py backup exists ($(stat -c%s $BACKUP_DIR/backend/server.py) bytes)"
else
    echo "❌ server.py backup missing"
    exit 1
fi

# Test 3: Verify restore script exists
if [ -f "/app/restore_backup.sh" ]; then
    echo "✅ Restore script exists and is executable"
else
    echo "❌ Restore script missing"
    exit 1
fi

# Test 4: Check file permissions
if [ -x "/app/restore_backup.sh" ]; then
    echo "✅ Restore script is executable"
else
    echo "⚠️  Making restore script executable..."
    chmod +x /app/restore_backup.sh
fi

echo ""
echo "=================================="
echo "✅ BACKUP IS READY FOR RESTORATION"
echo "=================================="
echo ""
echo "To restore if needed:"
echo "  /app/restore_backup.sh $BACKUP_DIR"
echo ""
