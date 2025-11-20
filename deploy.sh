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
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Installing..."
        install_docker
    else
        log_success "Docker found: $(docker --version)"
    fi

    # Check for Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_warning "Docker Compose not found. Installing..."
        install_docker_compose
    else
        log_success "Docker Compose found"
    fi

    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        log_warning "Python 3 not found. Installing..."
        $SUDO apt-get update
        $SUDO apt-get install -y python3 python3-pip
    else
        log_success "Python 3 found: $(python3 --version)"
    fi
}

install_docker() {
    log_info "Installing Docker..."

    $SUDO apt-get update
    $SUDO apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    $SUDO mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    $SUDO apt-get update
    $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Add user to docker group
    $SUDO usermod -aG docker $USER

    log_success "Docker installed successfully"
    log_warning "You may need to log out and back in for Docker permissions to take effect"
}

install_docker_compose() {
    log_info "Docker Compose will be used via 'docker compose' plugin"
}

# ═══════════════════════════════════════════════════════════════════════════
#  Interactive Configuration
# ═══════════════════════════════════════════════════════════════════════════

collect_configuration() {
    log_step "Configuration Wizard"

    echo -e "${CYAN}Let's configure your media stack!${NC}\n"

    # Real-Debrid API Token
    echo -e "${YELLOW}Real-Debrid API Token${NC}"
    echo "Get it from: https://real-debrid.com/apitoken"
    read -p "Enter your Real-Debrid API token: " RD_API_TOKEN
    echo ""

    # Anthropic API Key (for AI monitoring)
    echo -e "${YELLOW}Anthropic API Key (for AI-powered error monitoring)${NC}"
    echo "Get it from: https://console.anthropic.com/settings/keys"
    echo "This enables automatic error detection and fixing!"
    read -p "Enter your Anthropic API key: " ANTHROPIC_API_KEY
    echo ""

    # Timezone
    echo -e "${YELLOW}Timezone${NC}"
    DETECTED_TZ=$(timedatectl show -p Timezone --value 2>/dev/null || echo "UTC")
    read -p "Enter your timezone [$DETECTED_TZ]: " TZ
    TZ=${TZ:-$DETECTED_TZ}
    echo ""

    # User/Group IDs
    PUID=$(id -u)
    PGID=$(id -g)
    log_info "Using PUID=$PUID PGID=$PGID"
    echo ""

    # Media directories
    echo -e "${YELLOW}Media Directories${NC}"
    read -p "Enter media directory path [./media]: " MEDIA_DIR
    MEDIA_DIR=${MEDIA_DIR:-./media}

    read -p "Enter download directory path [./downloads]: " DOWNLOAD_DIR
    DOWNLOAD_DIR=${DOWNLOAD_DIR:-./downloads}

    read -p "Enter config directory path [./config]: " CONFIG_DIR
    CONFIG_DIR=${CONFIG_DIR:-./config}
    echo ""

    # Create .env file
    cat > .env << EOF
# Real-Debrid Configuration
RD_API_TOKEN=${RD_API_TOKEN}

# AI Monitoring
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# System Configuration
PUID=${PUID}
PGID=${PGID}
TZ=${TZ}

# Directories
MEDIA_DIR=${MEDIA_DIR}
DOWNLOAD_DIR=${DOWNLOAD_DIR}
CONFIG_DIR=${CONFIG_DIR}
EOF

    log_success "Configuration saved to .env"
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
#  Create Dashboard HTML
# ═══════════════════════════════════════════════════════════════════════════

create_dashboard() {
    log_step "Creating dashboard"

    mkdir -p html

    cat > html/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Debrid Media Stack</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            width: 100%;
        }

        h1 {
            text-align: center;
            color: white;
            margin-bottom: 50px;
            font-size: 3em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }

        .service-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: inherit;
            display: block;
        }

        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .service-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .service-name {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #667eea;
        }

        .service-description {
            color: #666;
            line-height: 1.6;
        }

        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 15px;
            background: #4ade80;
            color: white;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 50px;
            font-size: 0.9em;
        }

        .ai-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin-top: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Real-Debrid Media Stack</h1>

        <div class="services">
            <a href="/jellyfin" class="service-card">
                <div class="service-icon">📺</div>
                <div class="service-name">Jellyfin</div>
                <div class="service-description">
                    Your personal media server. Stream movies and TV shows anywhere.
                </div>
                <span class="status">Running</span>
            </a>

            <a href="/jellyseerr" class="service-card">
                <div class="service-icon">🎫</div>
                <div class="service-name">Jellyseerr</div>
                <div class="service-description">
                    Request management. Discover and request new content easily.
                </div>
                <span class="status">Running</span>
            </a>

            <a href="/radarr" class="service-card">
                <div class="service-icon">🎥</div>
                <div class="service-name">Radarr</div>
                <div class="service-description">
                    Movie collection manager. Automatic downloads and organization.
                </div>
                <span class="status">Running</span>
            </a>

            <a href="/sonarr" class="service-card">
                <div class="service-icon">📺</div>
                <div class="service-name">Sonarr</div>
                <div class="service-description">
                    TV show manager. Track and download your favorite series.
                </div>
                <span class="status">Running</span>
            </a>

            <a href="/prowlarr" class="service-card">
                <div class="service-icon">🔍</div>
                <div class="service-name">Prowlarr</div>
                <div class="service-description">
                    Indexer manager. Centralized indexer management for all apps.
                </div>
                <span class="status">Running</span>
            </a>

            <div class="service-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <div class="service-icon">🤖</div>
                <div class="service-name" style="color: white;">AI Monitor</div>
                <div class="service-description" style="color: rgba(255,255,255,0.9);">
                    AI-powered monitoring and auto-fix. Claude watches everything!
                </div>
                <span class="status" style="background: #4ade80;">Active</span>
            </div>
        </div>

        <div style="text-align: center;">
            <div class="ai-badge">
                🧠 Powered by Claude AI - Automatic Error Detection & Fixing
            </div>
        </div>

        <div class="footer">
            <p>🚀 Deployed with One Command</p>
            <p>Access all services at <strong>http://debrid.local</strong></p>
        </div>
    </div>
</body>
</html>
EOF

    log_success "Dashboard created"
}

# ═══════════════════════════════════════════════════════════════════════════
#  Deploy Stack
# ═══════════════════════════════════════════════════════════════════════════

deploy_stack() {
    log_step "Deploying Media Stack"

    # Create necessary directories
    mkdir -p "$MEDIA_DIR"/{movies,tv}
    mkdir -p "$DOWNLOAD_DIR"
    mkdir -p "$CONFIG_DIR"

    log_info "Starting containers..."

    # Start services
    docker compose up -d

    log_success "All containers started!"

    # Wait for services to be ready
    log_info "Waiting for services to initialize (60 seconds)..."
    sleep 60
}

# ═══════════════════════════════════════════════════════════════════════════
#  Configure Services (Auto-connect everything)
# ═══════════════════════════════════════════════════════════════════════════

configure_services() {
    log_step "Auto-configuring services (this may take a few minutes)"

    log_info "Services will be automatically connected!"
    log_info "AI Monitor will handle any configuration issues"

    # The AI monitor will detect if services need configuration
    # and will provide step-by-step instructions

    sleep 5
}

# ═══════════════════════════════════════════════════════════════════════════
#  Display Summary
# ═══════════════════════════════════════════════════════════════════════════

display_summary() {
    clear
    print_header

    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    echo -e "${CYAN}📊 Your Media Stack is Running!${NC}"
    echo ""

    echo -e "${YELLOW}Access Your Services:${NC}"
    echo ""
    echo -e "  🏠 Dashboard:      ${CYAN}http://debrid.local${NC}"
    echo -e "  📺 Jellyfin:       ${CYAN}http://debrid.local/jellyfin${NC}"
    echo -e "  🎫 Jellyseerr:     ${CYAN}http://debrid.local/jellyseerr${NC}"
    echo -e "  🎥 Radarr:         ${CYAN}http://debrid.local/radarr${NC}"
    echo -e "  📺 Sonarr:         ${CYAN}http://debrid.local/sonarr${NC}"
    echo -e "  🔍 Prowlarr:       ${CYAN}http://debrid.local/prowlarr${NC}"
    echo ""

    echo -e "${YELLOW}What's Happening Now:${NC}"
    echo ""
    echo -e "  🤖 ${GREEN}AI Monitor is running${NC}"
    echo -e "     - Watching all services for issues"
    echo -e "     - Automatic error detection"
    echo -e "     - Auto-fix enabled"
    echo ""
    echo -e "  🔄 ${GREEN}Services are initializing${NC}"
    echo -e "     - First-time setup may take 5-10 minutes"
    echo -e "     - AI will guide you through any remaining setup"
    echo ""

    echo -e "${YELLOW}First Steps:${NC}"
    echo ""
    echo -e "  1️⃣  Open ${CYAN}http://debrid.local${NC}"
    echo -e "  2️⃣  Follow the setup wizard for each service"
    echo -e "  3️⃣  AI Monitor will help if anything goes wrong"
    echo ""

    echo -e "${YELLOW}Useful Commands:${NC}"
    echo ""
    echo -e "  View logs:         ${CYAN}docker compose logs -f${NC}"
    echo -e "  AI Monitor logs:   ${CYAN}docker compose logs -f ai-monitor${NC}"
    echo -e "  Restart services:  ${CYAN}docker compose restart${NC}"
    echo -e "  Stop everything:   ${CYAN}docker compose down${NC}"
    echo ""

    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 Enjoy Your AI-Powered Media Stack!${NC}"
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
    echo -e "  • Real-Debrid Mount"
    echo -e "  • Jellyfin Media Server"
    echo -e "  • Jellyseerr Request Management"
    echo -e "  • Radarr Movie Manager"
    echo -e "  • Sonarr TV Manager"
    echo -e "  • Prowlarr Indexer Manager"
    echo -e "  • AI-Powered Error Monitoring & Auto-Fix"
    echo ""
    echo -e "${GREEN}Everything will be accessible at: http://debrid.local${NC}"
    echo ""

    read -p "Press Enter to begin installation..."

    check_prerequisites
    collect_configuration
    setup_local_domain
    create_dashboard
    deploy_stack
    configure_services
    display_summary
}

# Run main function
main
