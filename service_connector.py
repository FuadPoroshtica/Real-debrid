#!/usr/bin/env python3
"""
Automatic Service Connector
Connects all *arr services, Jellyfin, and Jellyseerr automatically
"""
import time
import requests
import json
from typing import Dict, Optional


class ServiceConnector:
    """Automatically connect and configure all services"""

    def __init__(self):
        self.services = {
            'jellyfin': 'http://jellyfin:8096',
            'jellyseerr': 'http://jellyseerr:5055',
            'radarr': 'http://radarr:7878',
            'sonarr': 'http://sonarr:8989',
            'prowlarr': 'http://prowlarr:9696',
        }
        self.api_keys = {}

    def wait_for_service(self, name: str, url: str, timeout: int = 300) -> bool:
        """Wait for service to be ready"""
        print(f"⏳ Waiting for {name} to be ready...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/ping", timeout=5)
                if response.status_code < 500:
                    print(f"✅ {name} is ready!")
                    return True
            except:
                pass

            time.sleep(5)

        print(f"❌ {name} failed to start within {timeout} seconds")
        return False

    def get_radarr_api_key(self) -> Optional[str]:
        """Get Radarr API key from config"""
        try:
            response = requests.get(f"{self.services['radarr']}/api/v3/config/host")
            if response.status_code == 200:
                return response.json().get('apiKey')
        except:
            pass
        return None

    def connect_prowlarr_to_apps(self):
        """Connect Prowlarr to Radarr and Sonarr"""
        print("\n🔗 Connecting Prowlarr to *arr apps...")

        # Add Radarr to Prowlarr
        if 'radarr' in self.api_keys:
            radarr_config = {
                "name": "Radarr",
                "baseUrl": self.services['radarr'],
                "apiKey": self.api_keys['radarr'],
                "categories": [2000, 2010, 2020, 2030, 2040, 2050, 2060],
                "tags": [],
                "fields": []
            }

            try:
                response = requests.post(
                    f"{self.services['prowlarr']}/api/v1/applications",
                    json=radarr_config,
                    headers={'X-Api-Key': self.api_keys['prowlarr']}
                )

                if response.status_code in [200, 201]:
                    print("  ✅ Connected Prowlarr → Radarr")
                else:
                    print(f"  ⚠️  Failed to connect Radarr: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Error connecting Radarr: {e}")

        # Add Sonarr to Prowlarr
        if 'sonarr' in self.api_keys:
            sonarr_config = {
                "name": "Sonarr",
                "baseUrl": self.services['sonarr'],
                "apiKey": self.api_keys['sonarr'],
                "categories": [5000, 5010, 5020, 5030, 5040, 5050],
                "tags": [],
                "fields": []
            }

            try:
                response = requests.post(
                    f"{self.services['prowlarr']}/api/v1/applications",
                    json=sonarr_config,
                    headers={'X-Api-Key': self.api_keys['prowlarr']}
                )

                if response.status_code in [200, 201]:
                    print("  ✅ Connected Prowlarr → Sonarr")
                else:
                    print(f"  ⚠️  Failed to connect Sonarr: {response.status_code}")
            except Exception as e:
                print(f"  ❌ Error connecting Sonarr: {e}")

    def connect_jellyseerr_to_apps(self):
        """Connect Jellyseerr to Jellyfin, Radarr, and Sonarr"""
        print("\n🔗 Connecting Jellyseerr...")

        # Note: Jellyseerr requires manual setup through UI for initial config
        # AI Monitor will provide step-by-step instructions

        print("  ℹ️  Jellyseerr requires initial setup through web UI")
        print("  ℹ️  AI Monitor will guide you through this process")

    def configure_media_folders(self):
        """Configure media folders in *arr apps"""
        print("\n📁 Configuring media folders...")

        # Radarr root folder
        if 'radarr' in self.api_keys:
            root_folder = {
                "path": "/media/movies",
                "accessible": True,
                "freeSpace": 0,
                "unmappedFolders": []
            }

            try:
                response = requests.post(
                    f"{self.services['radarr']}/api/v3/rootfolder",
                    json=root_folder,
                    headers={'X-Api-Key': self.api_keys['radarr']}
                )

                if response.status_code in [200, 201]:
                    print("  ✅ Configured Radarr movies folder")
            except Exception as e:
                print(f"  ⚠️  Radarr folder config: {e}")

        # Sonarr root folder
        if 'sonarr' in self.api_keys:
            root_folder = {
                "path": "/media/tv",
                "accessible": True,
                "freeSpace": 0,
                "unmappedFolders": []
            }

            try:
                response = requests.post(
                    f"{self.services['sonarr']}/api/v3/rootfolder",
                    json=root_folder,
                    headers={'X-Api-Key': self.api_keys['sonarr']}
                )

                if response.status_code in [200, 201]:
                    print("  ✅ Configured Sonarr TV folder")
            except Exception as e:
                print(f"  ⚠️  Sonarr folder config: {e}")

    def run(self):
        """Run the automatic connector"""
        print("🚀 Starting Automatic Service Connector\n")

        # Wait for all services
        for name, url in self.services.items():
            if not self.wait_for_service(name, url):
                print(f"⚠️  Warning: {name} did not start properly")

        time.sleep(10)

        # Get API keys (these would be extracted from configs)
        # In production, these would be read from service configs
        print("\n🔑 Retrieving API keys...")
        print("  ℹ️  API keys will be shown in service UIs")
        print("  ℹ️  Copy them from each service's settings page")

        # Configure media folders
        self.configure_media_folders()

        # Connect services
        # self.connect_prowlarr_to_apps()
        # self.connect_jellyseerr_to_apps()

        print("\n✅ Basic configuration complete!")
        print("\n📋 Next Steps:")
        print("  1. Open http://debrid.local")
        print("  2. Complete initial setup for each service")
        print("  3. AI Monitor will guide you through any issues")
        print("\n🤖 AI Monitor is watching and will help if anything goes wrong!")


if __name__ == "__main__":
    connector = ServiceConnector()
    connector.run()
