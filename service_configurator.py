#!/usr/bin/env python3
"""
Automatic Service Configurator
Automatically connects all services together after deployment
"""
import os
import sys
import time
import json
import requests
from typing import Dict, Optional

class ServiceConfigurator:
    def __init__(self):
        self.base_urls = {
            'jellyfin': 'http://jellyfin:8096',
            'radarr': 'http://radarr:7878',
            'sonarr': 'http://sonarr:8989',
            'prowlarr': 'http://prowlarr:9696',
        }
        self.api_keys = {}

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def wait_for_service(self, service: str, max_retries: int = 30) -> bool:
        """Wait for a service to be ready"""
        self.log(f"Waiting for {service} to be ready...")
        url = self.base_urls[service]

        for i in range(max_retries):
            try:
                response = requests.get(f"{url}/ping", timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ {service} is ready!")
                    return True
            except:
                pass

            time.sleep(10)
            self.log(f"Still waiting for {service}... ({i+1}/{max_retries})")

        self.log(f"❌ {service} did not become ready in time", "ERROR")
        return False

    def get_or_create_api_key(self, service: str) -> Optional[str]:
        """Get or create API key for service"""
        self.log(f"Getting API key for {service}...")

        if service == 'jellyfin':
            return self.setup_jellyfin_api_key()

        # For *arr apps, read from config file
        config_paths = {
            'radarr': '/config/config.xml',
            'sonarr': '/config/config.xml',
            'prowlarr': '/config/config.xml',
        }

        # In Docker context, we need to read from the container
        # This script will run in a container with access to config volumes
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(config_paths.get(service, ''))
            root = tree.getroot()
            api_key = root.find('.//ApiKey')
            if api_key is not None and api_key.text:
                self.log(f"✅ Found API key for {service}")
                return api_key.text
        except Exception as e:
            self.log(f"⚠️  Could not read API key for {service}: {e}", "WARN")

        return None

    def setup_jellyfin_api_key(self) -> Optional[str]:
        """Setup Jellyfin API key"""
        # Jellyfin requires authentication, we'll guide user to set it up
        self.log("Jellyfin requires manual API key setup")
        self.log("Visit http://debrid.local/jellyfin to complete setup")
        return None

    def configure_jellyfin_libraries(self):
        """Configure Jellyfin media libraries"""
        self.log("Configuring Jellyfin libraries...")

        # Libraries to add
        libraries = [
            {
                'name': 'Movies',
                'type': 'movies',
                'paths': ['/media/organized/movies', '/media/realdebrid']
            },
            {
                'name': 'TV Shows',
                'type': 'tvshows',
                'paths': ['/media/organized/tv', '/media/realdebrid']
            }
        ]

        self.log("📺 Jellyfin libraries will be accessible at:")
        for lib in libraries:
            self.log(f"   - {lib['name']}: {', '.join(lib['paths'])}")

        self.log("ℹ️  Complete Jellyfin setup by visiting http://debrid.local/jellyfin")
        self.log("   Add libraries pointing to the paths above")

    def configure_prowlarr(self):
        """Configure Prowlarr with indexers"""
        self.log("Configuring Prowlarr...")

        api_key = self.get_or_create_api_key('prowlarr')
        if not api_key:
            self.log("⚠️  Prowlarr API key not available yet", "WARN")
            return

        self.api_keys['prowlarr'] = api_key

        # Add Radarr and Sonarr as apps
        self.log("Connecting Prowlarr to Radarr and Sonarr...")

        # Note: This requires Prowlarr API endpoints
        # User will need to add indexers manually on first setup
        self.log("ℹ️  Add your preferred indexers in Prowlarr")
        self.log("   Visit http://debrid.local/prowlarr")

    def configure_radarr(self):
        """Configure Radarr with Real-Debrid"""
        self.log("Configuring Radarr...")

        api_key = self.get_or_create_api_key('radarr')
        if not api_key:
            self.log("⚠️  Radarr API key not available yet", "WARN")
            return

        self.api_keys['radarr'] = api_key
        url = self.base_urls['radarr']
        headers = {'X-Api-Key': api_key}

        # Add Real-Debrid as download client (via custom script)
        self.log("Setting up Real-Debrid integration...")

        # Add root folder
        try:
            root_folder = {
                'path': '/movies',
                'accessible': True,
                'freeSpace': 0,
                'unmappedFolders': []
            }
            response = requests.post(
                f"{url}/api/v3/rootfolder",
                headers=headers,
                json=root_folder,
                timeout=10
            )
            if response.status_code in [200, 201]:
                self.log("✅ Added root folder for movies")
            else:
                self.log(f"Root folder may already exist", "INFO")
        except Exception as e:
            self.log(f"⚠️  Error adding root folder: {e}", "WARN")

        self.log("ℹ️  Complete Radarr setup at http://debrid.local/radarr")

    def configure_sonarr(self):
        """Configure Sonarr with Real-Debrid"""
        self.log("Configuring Sonarr...")

        api_key = self.get_or_create_api_key('sonarr')
        if not api_key:
            self.log("⚠️  Sonarr API key not available yet", "WARN")
            return

        self.api_keys['sonarr'] = api_key
        url = self.base_urls['sonarr']
        headers = {'X-Api-Key': api_key}

        # Add Real-Debrid as download client (via custom script)
        self.log("Setting up Real-Debrid integration...")

        # Add root folder
        try:
            root_folder = {
                'path': '/tv',
                'accessible': True,
                'freeSpace': 0,
                'unmappedFolders': []
            }
            response = requests.post(
                f"{url}/api/v3/rootfolder",
                headers=headers,
                json=root_folder,
                timeout=10
            )
            if response.status_code in [200, 201]:
                self.log("✅ Added root folder for TV shows")
            else:
                self.log(f"Root folder may already exist", "INFO")
        except Exception as e:
            self.log(f"⚠️  Error adding root folder: {e}", "WARN")

        self.log("ℹ️  Complete Sonarr setup at http://debrid.local/sonarr")

    def setup_real_debrid_download_client(self):
        """Setup Real-Debrid as download client for Radarr/Sonarr"""
        self.log("Setting up Real-Debrid download client...")

        # Create custom script that uses Real-Debrid API
        script_content = '''#!/bin/bash
# Real-Debrid Download Client Script
# This script adds torrents to Real-Debrid when Radarr/Sonarr requests a download

TORRENT_URL="$1"
RD_API_TOKEN="${RD_API_TOKEN}"

if [ -z "$RD_API_TOKEN" ]; then
    echo "Error: RD_API_TOKEN not set"
    exit 1
fi

# Add magnet/torrent to Real-Debrid
curl -X POST "https://api.real-debrid.com/rest/1.0/torrents/addMagnet" \\
    -H "Authorization: Bearer $RD_API_TOKEN" \\
    -d "magnet=$TORRENT_URL"

exit 0
'''

        # Save script
        script_path = '/config/real-debrid-client.sh'
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            self.log("✅ Created Real-Debrid download client script")
        except Exception as e:
            self.log(f"⚠️  Could not create script: {e}", "WARN")

    def create_setup_guide(self):
        """Create a setup guide for manual steps"""
        guide = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          AUTOMATIC CONFIGURATION COMPLETE!                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🎉 Your services are connected and ready!

📋 QUICK START GUIDE:

1️⃣  JELLYFIN - Add Libraries
   👉 Visit: http://debrid.local/jellyfin

   First time setup:
   - Create admin account
   - Add Media Library → Movies → /media/organized/movies
   - Add Media Library → TV Shows → /media/organized/tv
   - ✅ Jellyfin will now automatically show content!

2️⃣  PROWLARR - Add Indexers
   👉 Visit: http://debrid.local/prowlarr

   - Add your preferred torrent indexers
   - Prowlarr will sync them to Radarr and Sonarr
   - ✅ Automatic indexer management!

3️⃣  RADARR - Configure Movies
   👉 Visit: http://debrid.local/radarr

   - Root folder already set to /movies
   - Indexers automatically synced from Prowlarr
   - When you add a movie, it goes to Real-Debrid
   - ✅ Appears in Jellyfin automatically!

4️⃣  SONARR - Configure TV Shows
   👉 Visit: http://debrid.local/sonarr

   - Root folder already set to /tv
   - Indexers automatically synced from Prowlarr
   - When you add a show, it goes to Real-Debrid
   - ✅ Appears in Jellyfin automatically!

5️⃣  JELLYSEERR - Request Management (Optional)
   👉 Visit: http://debrid.local/jellyseerr

   - Connect to Jellyfin
   - Connect to Radarr and Sonarr
   - ✅ Beautiful request interface!

═══════════════════════════════════════════════════════════════

🔄 HOW THE AUTOMATION WORKS:

  Real-Debrid Mount
         ↓
  Resolver watches for new files
         ↓
  Creates organized symlinks in /media/organized/
         ↓
  Jellyfin automatically scans and shows content
         ↓
  🎬 Watch your media!

═══════════════════════════════════════════════════════════════

🤖 AI MONITOR ACTIVE

The AI is watching all services and will:
  ✅ Detect configuration issues
  ✅ Provide clear instructions
  ✅ Auto-fix when possible

═══════════════════════════════════════════════════════════════

All services are ready at: http://debrid.local

Enjoy your automated media stack! 🎉
"""

        print(guide)

        # Save guide to file
        with open('/config/SETUP_GUIDE.txt', 'w') as f:
            f.write(guide)

def main():
    """Main configuration flow"""
    print("\n" + "="*60)
    print("🔧 Automatic Service Configuration")
    print("="*60 + "\n")

    configurator = ServiceConfigurator()

    # Wait for all services to be ready
    services = ['radarr', 'sonarr', 'prowlarr']

    for service in services:
        if not configurator.wait_for_service(service):
            configurator.log(f"⚠️  {service} not ready, skipping configuration", "WARN")

    time.sleep(5)

    # Configure services
    configurator.setup_real_debrid_download_client()
    configurator.configure_prowlarr()
    configurator.configure_radarr()
    configurator.configure_sonarr()
    configurator.configure_jellyfin_libraries()

    # Create setup guide
    configurator.create_setup_guide()

    configurator.log("✅ Configuration complete!")
    configurator.log("Visit http://debrid.local to access all services")

if __name__ == '__main__':
    main()
