#!/usr/bin/env python3
"""
Real-Debrid Download Client Bridge
Acts as a download client for Radarr/Sonarr to send magnet links to Real-Debrid
"""
from flask import Flask, request, jsonify
import requests
import os
import hashlib

app = Flask(__name__)

RD_API_TOKEN = os.getenv('RD_API_TOKEN')
RD_API_BASE = 'https://api.real-debrid.com/rest/1.0'

# Fake torrent tracking
torrents = {}


@app.route('/api/v2/app/version')
def get_version():
    """qBittorrent API compatibility"""
    return 'v4.3.9'


@app.route('/api/v2/auth/login', methods=['POST'])
def login():
    """Fake login for compatibility"""
    return 'Ok.'


@app.route('/api/v2/torrents/add', methods=['POST'])
def add_torrent():
    """Add magnet to Real-Debrid"""
    urls = request.form.get('urls', '')

    if not urls:
        return jsonify({'error': 'No URL provided'}), 400

    # Add to Real-Debrid
    headers = {'Authorization': f'Bearer {RD_API_TOKEN}'}
    response = requests.post(
        f'{RD_API_BASE}/torrents/addMagnet',
        headers=headers,
        data={'magnet': urls}
    )

    if response.status_code in [200, 201]:
        data = response.json()
        torrent_id = data.get('id')
        torrent_hash = hashlib.md5(urls.encode()).hexdigest()

        # Track it
        torrents[torrent_hash] = {
            'id': torrent_id,
            'hash': torrent_hash,
            'name': data.get('filename', 'Unknown'),
            'progress': 0,
            'state': 'downloading'
        }

        # Select all files
        requests.post(
            f'{RD_API_BASE}/torrents/selectFiles/{torrent_id}',
            headers=headers,
            data={'files': 'all'}
        )

        return 'Ok.'

    return jsonify({'error': 'Failed to add to Real-Debrid'}), 500


@app.route('/api/v2/torrents/info')
def get_torrents():
    """Get torrent list (fake - always shows complete)"""
    result = []

    # Get actual torrents from Real-Debrid
    headers = {'Authorization': f'Bearer {RD_API_TOKEN}'}
    response = requests.get(f'{RD_API_BASE}/torrents', headers=headers)

    if response.status_code == 200:
        rd_torrents = response.json()
        for torrent in rd_torrents:
            torrent_hash = torrent.get('hash', '')
            result.append({
                'hash': torrent_hash,
                'name': torrent.get('filename', 'Unknown'),
                'progress': 1.0 if torrent.get('status') == 'downloaded' else 0.5,
                'state': 'uploading' if torrent.get('status') == 'downloaded' else 'downloading',
                'category': '',
                'save_path': '/mnt/realdebrid',
                'dlspeed': 0,
                'upspeed': 0,
                'downloaded': torrent.get('bytes', 0),
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
        'save_path': '/mnt/realdebrid',
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
    """Delete torrent from Real-Debrid"""
    hashes = request.form.get('hashes', '').split('|')

    for torrent_hash in hashes:
        if torrent_hash in torrents:
            torrent_id = torrents[torrent_hash]['id']
            headers = {'Authorization': f'Bearer {RD_API_TOKEN}'}
            requests.delete(f'{RD_API_BASE}/torrents/delete/{torrent_id}', headers=headers)
            del torrents[torrent_hash]

    return 'Ok.'


if __name__ == '__main__':
    if not RD_API_TOKEN:
        print("ERROR: RD_API_TOKEN environment variable not set")
        exit(1)

    print("\n" + "="*60)
    print("🔌 Real-Debrid Download Client Bridge")
    print("="*60)
    print("\nqBittorrent-compatible API for Radarr/Sonarr")
    print("Listening on: http://0.0.0.0:8080")
    print("\nConfigure in Radarr/Sonarr:")
    print("  Type: qBittorrent")
    print("  Host: rd-bridge")
    print("  Port: 8080")
    print("  Username: (leave empty)")
    print("  Password: (leave empty)")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=8080, debug=False)
