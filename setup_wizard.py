#!/usr/bin/env python3
"""
Web-Based Setup Wizard for Real-Debrid Media Stack
Beautiful, friendly, and easy configuration interface
"""
from flask import Flask, render_template, request, jsonify, redirect
import os
import json
import subprocess
import threading
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)

SETUP_STATE_FILE = "/tmp/rdstack_setup_state.json"
CONFIG_FILE = ".env"


def load_state():
    """Load setup state"""
    if os.path.exists(SETUP_STATE_FILE):
        with open(SETUP_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"step": 1, "config": {}, "status": "configuring"}


def save_state(state):
    """Save setup state"""
    with open(SETUP_STATE_FILE, 'w') as f:
        json.dump(state, f)


@app.route('/')
@app.route('/setup')
@app.route('/deploying')
@app.route('/complete')
def index():
    """Main setup page - handles all states"""
    state = load_state()

    if state['status'] == 'deploying':
        return render_template('deploying.html')
    elif state['status'] == 'complete':
        return render_template('complete.html')
    else:
        return render_template('setup.html', step=state['step'])


@app.route('/api/save_config', methods=['POST'])
def save_config():
    """Save configuration from web form"""
    data = request.json
    state = load_state()

    # Update config
    state['config'].update(data)
    state['step'] = data.get('next_step', state['step'] + 1)

    save_state(state)

    return jsonify({"success": True, "next_step": state['step']})


@app.route('/api/start_deployment', methods=['POST'])
def start_deployment():
    """Start the deployment process"""
    state = load_state()
    config = state['config']

    # Get current user's UID and GID
    puid = os.getuid() if hasattr(os, 'getuid') else 1000
    pgid = os.getgid() if hasattr(os, 'getgid') else 1000

    # Create .env file
    env_content = f"""# Real-Debrid Configuration
RD_API_TOKEN={config.get('rd_api_token', '')}

# AI Monitoring
ANTHROPIC_API_KEY={config.get('anthropic_api_key', '')}

# System Configuration
PUID={puid}
PGID={pgid}
TZ={config.get('timezone', 'UTC')}

# Directories
MEDIA_DIR={config.get('media_dir', './media')}
DOWNLOAD_DIR={config.get('download_dir', './downloads')}
CONFIG_DIR={config.get('config_dir', './config')}

# User Configuration
ADMIN_USER={config.get('admin_user', 'admin')}
ADMIN_PASSWORD={config.get('admin_password', 'changeme')}
"""

    with open(CONFIG_FILE, 'w') as f:
        f.write(env_content)

    # Update state
    state['status'] = 'deploying'
    save_state(state)

    # Start deployment in background
    def deploy():
        try:
            # Create necessary directories
            media_dir = config.get('media_dir', './media')
            download_dir = config.get('download_dir', './downloads')
            config_dir_path = config.get('config_dir', './config')

            os.makedirs(f"{media_dir}/movies", exist_ok=True)
            os.makedirs(f"{media_dir}/tv", exist_ok=True)
            os.makedirs(download_dir, exist_ok=True)
            os.makedirs(config_dir_path, exist_ok=True)

            # Try docker compose (new) first, fallback to docker-compose (old)
            # Also try with sudo if regular command fails (for fresh Docker installs)
            try:
                subprocess.run(['docker', 'compose', 'up', '-d'], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(['docker-compose', 'up', '-d'], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Try with sudo (needed if Docker just installed)
                    try:
                        subprocess.run(['sudo', 'docker', 'compose', 'up', '-d'], check=True)
                    except:
                        subprocess.run(['sudo', 'docker-compose', 'up', '-d'], check=True)

            # Wait for services to initialize
            import time
            time.sleep(60)

            # Mark complete
            state = load_state()
            state['status'] = 'complete'
            save_state(state)
        except Exception as e:
            state = load_state()
            state['status'] = 'error'
            state['error'] = str(e)
            save_state(state)

    thread = threading.Thread(target=deploy)
    thread.daemon = True
    thread.start()

    return jsonify({"success": True})


@app.route('/api/status')
def get_status():
    """Get current deployment status"""
    state = load_state()
    return jsonify(state)


@app.errorhandler(404)
def page_not_found(e):
    """Redirect any 404s back to the main page"""
    return redirect('/')


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Start Flask server
    print("\n" + "="*60)
    print("🚀 Real-Debrid Media Stack Setup Wizard")
    print("="*60)
    print("\n📱 Open your browser and visit:")
    print("\n   👉 http://debrid.local")
    print("   👉 http://localhost:5000")
    print("\n" + "="*60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=False)
