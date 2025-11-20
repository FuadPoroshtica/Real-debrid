#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
#  Real-Debrid Complete Media Stack Deployment
#  One command to rule them all!
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════
#  Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

print_header() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Real-Debrid Complete Media Stack                          ║
║   Powered by AI - One Command Deploy                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "\n${MAGENTA}🚀 $1${NC}\n"
}

# ═══════════════════════════════════════════════════════════════════════════
#  Prerequisite Checks
# ═══════════════════════════════════════════════════════════════════════════

check_prerequisites() {
    log_step "Checking Prerequisites"

    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This script must be run on Linux"
        log_info "Recommended: Ubuntu Server 20.04 or 22.04"
        exit 1
    fi

    log_success "Linux detected"

    # Check for root/sudo
    if [[ $EUID -eq 0 ]]; then
        SUDO=""
    else
        if ! command -v sudo &> /dev/null; then
            log_error "sudo is required but not installed"
            exit 1
        fi
        SUDO="sudo"
    fi

    log_success "Permissions OK"

    # Check for Docker
    DOCKER_INSTALLED_NOW=false
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Installing..."
        install_docker
    else
        log_success "Docker found: $(docker --version 2>/dev/null || $SUDO docker --version)"
    fi

    # Check for Docker Compose
    if ! docker compose version &> /dev/null 2>&1 && ! $SUDO docker compose version &> /dev/null 2>&1; then
        log_warning "Docker Compose not found. Installing..."
        install_docker_compose
    else
        log_success "Docker Compose found"
    fi

    # If Docker was just installed, use sudo for Docker commands
    if [ "$DOCKER_INSTALLED_NOW" = true ]; then
        log_warning "Docker was just installed. Using sudo for Docker commands in this session."
        log_info "After this script completes, logout and login for Docker permissions."
        export DOCKER_CMD="$SUDO docker"
        export DOCKER_COMPOSE_CMD="$SUDO docker compose"
    else
        export DOCKER_CMD="docker"
        export DOCKER_COMPOSE_CMD="docker compose"
    fi

    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        log_warning "Python 3 not found. Installing..."
        $SUDO apt-get update -qq
        $SUDO apt-get install -y python3 python3-pip python3-venv
    else
        log_success "Python 3 found: $(python3 --version)"
    fi
}

install_docker() {
    log_info "Installing Docker..."

    $SUDO apt-get update -qq
    $SUDO apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    $SUDO mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null

    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    $SUDO apt-get update -qq
    $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Add user to docker group
    $SUDO usermod -aG docker $USER

    # Start Docker service
    $SUDO systemctl start docker
    $SUDO systemctl enable docker

    log_success "Docker installed successfully"

    # Apply docker group immediately for this script using newgrp
    # This allows continuing without logout
    log_info "Applying Docker group permissions..."
    DOCKER_INSTALLED_NOW=true
}

install_docker_compose() {
    log_info "Docker Compose will be used via 'docker compose' plugin"
}

# ═══════════════════════════════════════════════════════════════════════════
#  Web-Based Configuration
# ═══════════════════════════════════════════════════════════════════════════

install_python_requirements() {
    log_step "Installing Python Requirements"

    # Install pip if not available
    if ! command -v pip3 &> /dev/null; then
        $SUDO apt-get update -qq
        $SUDO apt-get install -y python3-pip python3-venv
    fi

    # Create virtual environment for deployment
    log_info "Creating Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Install Flask in virtual environment
    log_info "Installing Flask and dependencies..."
    ./venv/bin/pip install --quiet flask 2>/dev/null || {
        log_warning "Virtual env install failed, trying system install..."
        pip3 install --break-system-packages flask 2>/dev/null || {
            log_error "Failed to install Flask"
            exit 1
        }
    }

    log_success "Python requirements installed"
}

launch_web_wizard() {
    log_step "Launching Web-Based Setup Wizard"

    echo -e "${CYAN}Starting beautiful web interface for configuration...${NC}\n"

    # Determine which Python to use
    if [ -f "venv/bin/python3" ]; then
        PYTHON_CMD="./venv/bin/python3"
        log_info "Using virtual environment Python"
    else
        PYTHON_CMD="python3"
        log_info "Using system Python"
    fi

    # Start Flask web server in background
    $PYTHON_CMD setup_wizard.py &
    FLASK_PID=$!

    log_info "Web server starting..."
    sleep 3

    # Check if Flask started successfully
    if ! kill -0 $FLASK_PID 2>/dev/null; then
        log_error "Failed to start web server"
        exit 1
    fi

    log_success "Web server running (PID: $FLASK_PID)"

    # Open browser automatically
    open_browser

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║  🌐  Please visit: ${CYAN}http://debrid.local:5000${GREEN}             ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║  Complete the setup wizard in your browser                ║${NC}"
    echo -e "${GREEN}║  The deployment will start automatically when you click   ║${NC}"
    echo -e "${GREEN}║  the 'Deploy' button                                      ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Wait for .env file to be created by the web wizard
    log_info "Waiting for configuration to complete..."

    while [ ! -f .env ]; do
        sleep 2
    done

    log_success "Configuration completed via web interface!"

    # Wait a bit more for deployment to start
    sleep 2
}

open_browser() {
    # Try to open browser automatically
    URL="http://debrid.local:5000"

    if command -v xdg-open &> /dev/null; then
        xdg-open "$URL" 2>/dev/null &
    elif command -v gnome-open &> /dev/null; then
        gnome-open "$URL" 2>/dev/null &
    elif command -v python3 &> /dev/null; then
        python3 -m webbrowser "$URL" 2>/dev/null &
    fi

    log_info "Browser should open automatically"
    log_info "If not, manually visit: ${CYAN}$URL${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
#  Setup Local Domain
# ═══════════════════════════════════════════════════════════════════════════

setup_local_domain() {
    log_step "Setting up debrid.local domain"

    # Add to /etc/hosts if not already there
    if ! grep -q "debrid.local" /etc/hosts; then
        echo "127.0.0.1 debrid.local" | $SUDO tee -a /etc/hosts > /dev/null
        log_success "Added debrid.local to /etc/hosts"
    else
        log_info "debrid.local already in /etc/hosts"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
#  Wait for Deployment
# ═══════════════════════════════════════════════════════════════════════════

wait_for_deployment() {
    log_step "Monitoring Deployment Progress"

    echo -e "${CYAN}The web interface is handling the deployment...${NC}\n"

    # Wait for docker-compose to start (triggered by web interface)
    log_info "Waiting for deployment to begin..."

    # Check if containers are starting
    WAIT_TIME=0
    MAX_WAIT=300  # 5 minutes max

    while [ $WAIT_TIME -lt $MAX_WAIT ]; do
        if $DOCKER_CMD ps --format '{{.Names}}' 2>/dev/null | grep -q jellyfin; then
            log_success "Deployment started!"
            break
        fi
        sleep 5
        WAIT_TIME=$((WAIT_TIME + 5))
    done

    if [ $WAIT_TIME -ge $MAX_WAIT ]; then
        log_warning "Deployment may still be in progress. Check the web interface."
        return
    fi

    # Wait for services to be healthy
    log_info "Services are initializing (this may take a few minutes)..."
    sleep 30
}

# ═══════════════════════════════════════════════════════════════════════════
#  Display Summary
# ═══════════════════════════════════════════════════════════════════════════

display_summary() {
    clear
    print_header

    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    echo -e "${CYAN}🚀 Your Media Stack is Being Deployed!${NC}"
    echo ""

    echo -e "${YELLOW}Access Your Services:${NC}"
    echo ""
    echo -e "  🌐 Main Access:    ${CYAN}http://debrid.local${NC}"
    echo ""
    echo -e "  📺 Jellyfin:       ${CYAN}http://debrid.local/jellyfin${NC}"
    echo -e "  🎫 Jellyseerr:     ${CYAN}http://debrid.local/jellyseerr${NC}"
    echo -e "  🎥 Radarr:         ${CYAN}http://debrid.local/radarr${NC}"
    echo -e "  📺 Sonarr:         ${CYAN}http://debrid.local/sonarr${NC}"
    echo -e "  🔍 Prowlarr:       ${CYAN}http://debrid.local/prowlarr${NC}"
    echo ""

    echo -e "${YELLOW}What's Happening Now:${NC}"
    echo ""
    echo -e "  🤖 ${GREEN}AI Monitor is starting${NC}"
    echo -e "     - Will watch all services for issues"
    echo -e "     - Automatic error detection and fixing"
    echo ""
    echo -e "  🔄 ${GREEN}Services are initializing${NC}"
    echo -e "     - First-time setup may take 5-10 minutes"
    echo -e "     - Visit ${CYAN}http://debrid.local${NC} to see progress"
    echo ""

    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo -e "  1️⃣  Visit ${CYAN}http://debrid.local${NC} in your browser"
    echo -e "  2️⃣  Wait for all services to show as 'Running'"
    echo -e "  3️⃣  Follow any remaining setup wizards"
    echo -e "  4️⃣  Start enjoying your media!"
    echo ""

    echo -e "${YELLOW}Useful Commands:${NC}"
    echo ""
    echo -e "  View logs:         ${CYAN}docker compose logs -f${NC}"
    echo -e "  AI Monitor logs:   ${CYAN}docker compose logs -f ai-monitor${NC}"
    echo -e "  Restart services:  ${CYAN}docker compose restart${NC}"
    echo -e "  Stop everything:   ${CYAN}docker compose down${NC}"
    echo ""

    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 One Command, Complete Media Stack!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  Main Execution
# ═══════════════════════════════════════════════════════════════════════════

main() {
    print_header

    echo -e "${CYAN}Welcome to the Ultimate Media Stack Deployment!${NC}\n"
    echo -e "${YELLOW}This will install and configure:${NC}"
    echo -e "  • Real-Debrid Mount with FUSE & WebDAV"
    echo -e "  • Jellyfin Media Server"
    echo -e "  • Jellyseerr Request Management"
    echo -e "  • Radarr Movie Manager"
    echo -e "  • Sonarr TV Manager"
    echo -e "  • Prowlarr Indexer Manager"
    echo -e "  • AI-Powered Error Monitoring & Auto-Fix (Claude)"
    echo ""
    echo -e "${GREEN}🌟 Everything accessible at: ${CYAN}http://debrid.local${NC}"
    echo ""
    echo -e "${MAGENTA}📱 You'll complete setup via a beautiful web interface!${NC}"
    echo ""

    read -p "Press Enter to begin installation..."

    check_prerequisites
    setup_local_domain
    install_python_requirements
    launch_web_wizard
    wait_for_deployment
    display_summary
}

# Run main function
main
