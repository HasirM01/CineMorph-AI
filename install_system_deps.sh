#!/bin/bash
# CineMorph AI - System Dependencies Installer
# This script ensures FFmpeg and other required dependencies are installed

set -e  # Exit on error

echo "=================================="
echo "CineMorph AI - Dependency Check"
echo "=================================="

# Check and install FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Installing..."
    apt-get update -qq
    apt-get install -y ffmpeg
    echo "✓ FFmpeg installed successfully"
else
    echo "✓ FFmpeg already installed"
fi

# Check and install ffprobe (usually comes with FFmpeg)
if ! command -v ffprobe &> /dev/null; then
    echo "⚠️  ffprobe not found. Installing..."
    apt-get install -y ffmpeg
    echo "✓ ffprobe installed successfully"
else
    echo "✓ ffprobe already installed"
fi

# Verify installations
echo ""
echo "Verifying installations..."
FFMPEG_VERSION=$(ffmpeg -version | head -n 1 | awk '{print $3}')
FFPROBE_VERSION=$(ffprobe -version | head -n 1 | awk '{print $3}')

echo "✓ FFmpeg version: $FFMPEG_VERSION"
echo "✓ ffprobe version: $FFPROBE_VERSION"
echo "✓ FFmpeg path: $(which ffmpeg)"
echo "✓ ffprobe path: $(which ffprobe)"

echo ""
echo "=================================="
echo "✓ All dependencies ready"
echo "=================================="

exit 0
