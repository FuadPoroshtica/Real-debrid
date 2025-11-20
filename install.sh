#!/bin/bash
# Installation script for Real-Debrid Mount

set -e

echo "==================================="
echo "Real-Debrid Mount - Installation"
echo "==================================="
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

echo "✓ Python 3 found"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

echo "✓ pip3 found"

# Install system dependencies for FUSE
echo ""
echo "Installing system dependencies..."

if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y fuse libfuse-dev
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y fuse fuse-devel
elif command -v dnf &> /dev/null; then
    # Fedora
    sudo dnf install -y fuse fuse-devel
elif command -v pacman &> /dev/null; then
    # Arch Linux
    sudo pacman -S --noconfirm fuse2
else
    echo "Warning: Could not detect package manager."
    echo "Please manually install FUSE if not already installed."
fi

echo "✓ System dependencies installed"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "✓ Python dependencies installed"

# Add to PATH (optional)
echo ""
echo "==================================="
echo "Installation Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Get your API token from: https://real-debrid.com/apitoken"
echo "2. Run: ./rdmount.py setup"
echo "3. Run: ./rdmount.py mount ~/realdebrid"
echo ""
echo "For Jellyfin integration, add the mount point as a media library."
echo ""
