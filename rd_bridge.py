#!/usr/bin/env python3
"""
Debrid Download Client Bridge
Acts as a download client for Radarr/Sonarr to send magnet links to Real-Debrid or AllDebrid
"""
from flask import Flask, request, jsonify
import requests
import os
import hashlib

app = Flask(__name__)

# Configuration - Auto-detect service based on environment variables
RD_API_TOKEN = os.getenv('RD_API_TOKEN')
AD_API_TOKEN = os.getenv('AD_API_TOKEN')

# Determine which service to use
if AD_API_TOKEN:
    SERVICE = 'alldebrid'
    API_TOKEN = AD_API_TOKEN
    API_BASE = 'https://api.alldebrid.com/v4'
    MOUNT_PATH = '/mnt/alldebrid'
elif RD_API_TOKEN:
    SERVICE = 'realdebrid'
    API_TOKEN = RD_API_TOKEN
    API_BASE = 'https://api.real-debrid.com/rest/1.0'
    MOUNT_PATH = '/mnt/realdebrid'
else:
    SERVICE = None
    API_TOKEN = None

# Torrent tracking
torrents = {}


class DebridAPI:
    """Abstraction layer for Real-Debrid and AllDebrid APIs"""

    @staticmethod
    def add_magnet(magnet_url):
        """Add magnet to debrid service"""
        headers = {'Authorization': f'Bearer {API_TOKEN}'}

        if SERVICE == 'realdebrid':
            response = requests.post(
                f'{API_BASE}/torrents/addMagnet',
                headers=headers,
                data={'magnet': magnet_url}
            )
            if response.status_code in [200, 201]:
                data = response.json()
                torrent_id = data.get('id')

                # Auto-select all files for Real-Debrid
                requests.post(
                    f'{API_BASE}/torrents/selectFiles/{torrent_id}',
                    headers=headers,
                    data={'files': 'all'}
                )

                return {
                    'success': True,
                    'id': torrent_id,
                    'filename': data.get('filename', 'Unknown')
                }

        elif SERVICE == 'alldebrid':
            response = requests.post(
                f'{API_BASE}/magnet/upload',
                headers=headers,
                data={'magnets[]': magnet_url}
            )
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('status') == 'success' and data.get('data', {}).get('magnets'):
                    magnet_info = data['data']['magnets'][0]
                    return {
                        'success': True,
                        'id': magnet_info.get('id'),
                        'filename': magnet_info.get('filename', 'Unknown')
                    }

        return {'success': False, 'error': 'Failed to add magnet'}

    @staticmethod
    def get_torrents():
        """Get torrent list from debrid service"""
        headers = {'Authorization': f'Bearer {API_TOKEN}'}
        result = []

        if SERVICE == 'realdebrid':
            response = requests.get(f'{API_BASE}/torrents', headers=headers)
            if response.status_code == 200:
                rd_torrents = response.json()
                for torrent in rd_torrents:
                    result.append({
                        'id': torrent.get('id'),
                        'hash': torrent.get('hash', ''),
                        'name': torrent.get('filename', 'Unknown'),
                        'progress': 1.0 if torrent.get('status') == 'downloaded' else 0.5,
                        'state': 'uploading' if torrent.get('status') == 'downloaded' else 'downloading',
                        'bytes': torrent.get('bytes', 0)
                    })

        elif SERVICE == 'alldebrid':
            response = requests.get(f'{API_BASE}/magnet/status', headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and data.get('data', {}).get('magnets'):
                    for magnet in data['data']['magnets']:
                        # Calculate progress
                        downloaded = magnet.get('downloaded', 0)
                        size = magnet.get('size', 1)
                        progress = downloaded / size if size > 0 else 0

                        # Determine state
                        status_code = magnet.get('statusCode', 0)
                        if status_code == 4:  # Ready
                            state = 'uploading'
                            progress = 1.0
                        elif status_code in [0, 1, 2, 3]:  # Processing/Downloading
                            state = 'downloading'
                        else:
                            state = 'error'

                        result.append({
                            'id': magnet.get('id'),
                            'hash': magnet.get('hash', ''),
                            'name': magnet.get('filename', 'Unknown'),
                            'progress': progress,
                            'state': state,
                            'bytes': magnet.get('size', 0)
                        })

        return result

    @staticmethod
    def delete_torrent(torrent_id):
        """Delete torrent from debrid service"""
        headers = {'Authorization': f'Bearer {API_TOKEN}'}

        if SERVICE == 'realdebrid':
            response = requests.delete(
                f'{API_BASE}/torrents/delete/{torrent_id}',
                headers=headers
            )
            return response.status_code in [200, 204]

        elif SERVICE == 'alldebrid':
            response = requests.post(
                f'{API_BASE}/magnet/delete',
                headers=headers,
                data={'id': torrent_id}
            )
            return response.status_code == 200

        return False


# qBittorrent-compatible API endpoints

@app.route('/api/v2/app/version')
def get_version():
    """qBittorrent API compatibility"""
    return 'v4.3.9'


@app.route('/api/v2/app/webapiVersion')
def get_webapi_version():
    """qBittorrent Web API version"""
    return '2.8.3'


@app.route('/version/api')
def get_api_version():
    """Legacy qBittorrent API version endpoint"""
    return '2.8.3'


@app.route('/api/v2/auth/login', methods=['POST'])
def login():
    """Fake login for compatibility"""
    return 'Ok.'


@app.route('/api/v2/torrents/add', methods=['POST'])
def add_torrent():
    """Add magnet to debrid service"""
    urls = request.form.get('urls', '')

    if not urls:
        return jsonify({'error': 'No URL provided'}), 400

    result = DebridAPI.add_magnet(urls)

    if result['success']:
        torrent_hash = hashlib.md5(urls.encode()).hexdigest()
        torrents[torrent_hash] = {
            'id': result['id'],
            'hash': torrent_hash,
            'name': result['filename']
        }
        return 'Ok.'

    return jsonify({'error': result.get('error', 'Failed to add magnet')}), 500


@app.route('/api/v2/torrents/info')
def get_torrents_info():
    """Get torrent list from debrid service"""
    result = []

    debrid_torrents = DebridAPI.get_torrents()
    for torrent in debrid_torrents:
        result.append({
            'hash': torrent['hash'],
            'name': torrent['name'],
            'progress': torrent['progress'],
            'state': torrent['state'],
            'category': '',
            'save_path': MOUNT_PATH,
            'dlspeed': 0,
            'upspeed': 0,
            'downloaded': torrent['bytes'],
            'uploaded': 0,
            'ratio': 0,
            'eta': 0,
            'added_on': 0
        })

    return jsonify(result)


@app.route('/api/v2/torrents/properties')
def get_properties():
    """Get torrent properties"""
    return jsonify({
        'save_path': MOUNT_PATH,
        'creation_date': 0,
        'piece_size': 0,
        'comment': '',
        'total_wasted': 0,
        'total_uploaded': 0,
        'total_downloaded': 0,
        'up_limit': -1,
        'dl_limit': -1,
        'time_elapsed': 0,
        'seeding_time': 0,
        'nb_connections': 0,
        'share_ratio': 0
    })


@app.route('/api/v2/torrents/delete', methods=['POST'])
def delete_torrent():
    """Delete torrent from debrid service"""
    hashes = request.form.get('hashes', '').split('|')

    for torrent_hash in hashes:
        if torrent_hash in torrents:
            torrent_id = torrents[torrent_hash]['id']
            DebridAPI.delete_torrent(torrent_id)
            del torrents[torrent_hash]

    return 'Ok.'


if __name__ == '__main__':
    if not API_TOKEN:
        print("ERROR: No API token configured!")
        print("Set either RD_API_TOKEN or AD_API_TOKEN environment variable")
        exit(1)

    service_name = "AllDebrid" if SERVICE == 'alldebrid' else "Real-Debrid"

    print("\n" + "="*60)
    print(f"🔌 {service_name} Download Client Bridge")
    print("="*60)
    print("\nqBittorrent-compatible API for Radarr/Sonarr")
    print(f"Service: {service_name}")
    print(f"Mount path: {MOUNT_PATH}")
    print("Listening on: http://0.0.0.0:8080")
    print("\nConfigure in Radarr/Sonarr:")
    print("  Type: qBittorrent")
    print("  Host: rd-bridge")
    print("  Port: 8080")
    print("  Username: (leave empty)")
    print("  Password: (leave empty)")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=8080, debug=False)
