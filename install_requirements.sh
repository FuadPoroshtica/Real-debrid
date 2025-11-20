#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
#  Install Python Requirements
#  Handles externally-managed-environment issue
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Installing Python Requirements...${NC}\n"

# Check if running on modern Python with externally-managed-environment
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)

echo -e "${YELLOW}Detected Python $PYTHON_VERSION${NC}\n"

# Method 1: Try virtual environment (recommended)
echo -e "${BLUE}Method 1: Creating virtual environment (recommended)...${NC}"
if python3 -m venv venv 2>/dev/null; then
    echo -e "${GREEN}✅ Virtual environment created${NC}"

    echo "Installing requirements in virtual environment..."
    ./venv/bin/pip install --quiet --upgrade pip
    ./venv/bin/pip install -r requirements.txt

    echo -e "\n${GREEN}✅ All requirements installed in virtual environment!${NC}"
    echo -e "\n${YELLOW}To use the virtual environment:${NC}"
    echo -e "  source venv/bin/activate"
    echo -e "  python start.py"
    echo -e "\n${YELLOW}Or run directly:${NC}"
    echo -e "  ./venv/bin/python start.py"
    exit 0
fi

# Method 2: Try system-wide with --break-system-packages
echo -e "\n${YELLOW}Method 2: Installing system-wide (requires --break-system-packages)...${NC}"
read -p "This will modify system Python packages. Continue? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip3 install --break-system-packages -r requirements.txt
    echo -e "\n${GREEN}✅ Requirements installed system-wide${NC}"
    exit 0
fi

# Method 3: Docker-only usage
echo -e "\n${YELLOW}Method 3: Use Docker deployment (no local Python packages needed)${NC}"
echo -e "For Docker deployment, you don't need to install requirements locally."
echo -e "Just run: ${GREEN}./deploy.sh${NC}"
echo -e "\nAll Python packages will be installed inside Docker containers."
