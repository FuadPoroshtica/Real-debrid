#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
#  Setup debrid.local for local network access
#  Makes Real-Debrid Media Stack the primary service on this server
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}     Setting up debrid.local for Network Access             ${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "${YELLOW}Server IP detected: ${GREEN}$SERVER_IP${NC}"
echo ""

# 1. Add to server's /etc/hosts
echo -e "${CYAN}[1/3] Configuring server /etc/hosts...${NC}"
if grep -q "debrid.local" /etc/hosts; then
    echo "✅ debrid.local already in /etc/hosts"
else
    echo "127.0.0.1 debrid.local" | sudo tee -a /etc/hosts > /dev/null
    echo "✅ Added debrid.local to server /etc/hosts"
fi
echo ""

# 2. Configure nginx to be the default server
echo -e "${CYAN}[2/3] Making nginx the default web server...${NC}"

# Check if nginx container is running
if docker ps | grep -q nginx-proxy; then
    echo "✅ Nginx is running"

    # Disable any other web servers on port 80
    if command -v systemctl &> /dev/null; then
        for service in apache2 nginx lighttpd; do
            if systemctl is-active --quiet $service 2>/dev/null; then
                echo "⚠️  Stopping system $service (conflicts with Docker nginx)..."
                sudo systemctl stop $service
                sudo systemctl disable $service
                echo "   ✅ Stopped $service"
            fi
        done
    fi

    echo "✅ Port 80 is now owned by Real-Debrid Media Stack"
else
    echo "⚠️  Nginx container not running. Start deployment first:"
    echo "   sudo docker compose up -d"
fi
echo ""

# 3. Instructions for accessing from other devices
echo -e "${CYAN}[3/3] Network Access Instructions${NC}"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  How to Access from Other Devices on Your Network        ${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Option 1: Use IP Address (Works Immediately)${NC}"
echo -e "  Main:      http://$SERVER_IP"
echo -e "  Jellyfin:  http://$SERVER_IP/jellyfin"
echo -e "  Radarr:    http://$SERVER_IP/radarr"
echo -e "  Sonarr:    http://$SERVER_IP/sonarr"
echo ""
echo -e "${GREEN}Option 2: Use debrid.local (Requires setup on each device)${NC}"
echo ""

# Instructions for different operating systems
echo -e "${CYAN}📱 On Windows:${NC}"
echo "  1. Open Notepad as Administrator"
echo "  2. Open: C:\\Windows\\System32\\drivers\\etc\\hosts"
echo "  3. Add this line at the bottom:"
echo -e "     ${YELLOW}$SERVER_IP debrid.local${NC}"
echo "  4. Save and close"
echo ""

echo -e "${CYAN}🍎 On Mac/Linux:${NC}"
echo "  Run this command:"
echo -e "  ${YELLOW}echo '$SERVER_IP debrid.local' | sudo tee -a /etc/hosts${NC}"
echo ""

echo -e "${CYAN}📱 On Phone/Tablet:${NC}"
echo "  Android: Requires root access or DNS app"
echo "  iOS: Not easily possible without jailbreak"
echo -e "  ${GREEN}→ Just use the IP address: http://$SERVER_IP${NC}"
echo ""

echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 4. Create a bookmark file
echo -e "${CYAN}Creating quick access bookmark...${NC}"
cat > ~/debrid-access.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=http://$SERVER_IP">
    <title>Redirecting to Real-Debrid Media Stack...</title>
</head>
<body>
    <h1>Redirecting to Real-Debrid Media Stack...</h1>
    <p>If not redirected, <a href="http://$SERVER_IP">click here</a></p>
    <hr>
    <h2>Quick Links:</h2>
    <ul>
        <li><a href="http://$SERVER_IP">Main Dashboard</a></li>
        <li><a href="http://$SERVER_IP/jellyfin">Jellyfin</a></li>
        <li><a href="http://$SERVER_IP/radarr">Radarr</a></li>
        <li><a href="http://$SERVER_IP/sonarr">Sonarr</a></li>
        <li><a href="http://$SERVER_IP/prowlarr">Prowlarr</a></li>
        <li><a href="http://$SERVER_IP/jellyseerr">Jellyseerr</a></li>
    </ul>
</body>
</html>
EOF

echo "✅ Created ~/debrid-access.html"
echo ""

# 5. Display summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}This server is now dedicated to Real-Debrid Media Stack!${NC}"
echo ""
echo -e "${YELLOW}Access Your Stack:${NC}"
echo -e "  From this server:     ${GREEN}http://debrid.local${NC}"
echo -e "  From other devices:   ${GREEN}http://$SERVER_IP${NC}"
echo ""
echo -e "${YELLOW}Quick Access Bookmark:${NC}"
echo -e "  Open: ${GREEN}~/debrid-access.html${NC} in your browser"
echo -e "  Then bookmark it!"
echo ""
echo -e "${YELLOW}Port 80 Status:${NC}"
echo -e "  ${GREEN}Owned by Real-Debrid Media Stack${NC}"
echo -e "  Any system web servers have been disabled"
echo ""
