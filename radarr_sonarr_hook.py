#!/usr/bin/env python3
"""
Radarr/Sonarr Real-Debrid Integration Hook
This script acts as a bridge between *arr apps and Real-Debrid
"""
import os
import sys
import json
import requests
import time
from pathlib import Path

class RealDebridDownloadClient:
    def __init__(self):
        self.api_token = os.getenv('RD_API_TOKEN')
        self.base_url = 'https://api.real-debrid.com/rest/1.0'

    def add_magnet(self, magnet_link: str) -> dict:
        """Add a magnet link to Real-Debrid"""
        headers = {'Authorization': f'Bearer {self.api_token}'}
        data = {'magnet': magnet_link}

        response = requests.post(
            f'{self.base_url}/torrents/addMagnet',
            headers=headers,
            data=data
        )

        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to add magnet: {response.text}")

    def select_files(self, torrent_id: str):
        """Select all files in torrent"""
        headers = {'Authorization': f'Bearer {self.api_token}'}

        # Get torrent info
        response = requests.get(
            f'{self.base_url}/torrents/info/{torrent_id}',
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get torrent info: {response.text}")

        torrent_info = response.json()

        # Select all files
        file_ids = ','.join(str(f['id']) for f in torrent_info.get('files', []))

        if file_ids:
            select_response = requests.post(
                f'{self.base_url}/torrents/selectFiles/{torrent_id}',
                headers=headers,
                data={'files': file_ids}
            )

            if select_response.status_code != 204:
                raise Exception(f"Failed to select files: {select_response.text}")

    def process_download(self, event_data: dict):
        """Process download request from Radarr/Sonarr"""
        # Extract magnet link from event data
        magnet = event_data.get('release', {}).get('downloadUrl')

        if not magnet:
            print("ERROR: No magnet link found in event data")
            return

        print(f"Adding to Real-Debrid: {magnet[:50]}...")

        try:
            # Add magnet
            result = self.add_magnet(magnet)
            torrent_id = result.get('id')

            print(f"✅ Added to Real-Debrid: ID {torrent_id}")

            # Select all files
            time.sleep(2)
            self.select_files(torrent_id)

            print(f"✅ Files selected and downloading")

        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

def main():
    """Main hook handler"""
    # Get event type from environment or args
    event_type = os.getenv('radarr_eventtype') or os.getenv('sonarr_eventtype')

    if event_type == 'Grab':
        # This event fires when *arr grabs a release
        print("🔄 Processing download request...")

        # Read event data from environment
        event_data = {
            'release': {
                'downloadUrl': os.getenv('radarr_release_indexer') or os.getenv('sonarr_release_indexer')
            }
        }

        client = RealDebridDownloadClient()
        client.process_download(event_data)

    elif event_type == 'Download':
        # This event fires when download completes
        print("✅ Download complete, triggering media organization...")

        # The resolver will automatically detect and organize new files

    else:
        print(f"Unknown event type: {event_type}")

if __name__ == '__main__':
    main()
