#!/bin/bash
set -e

echo "Starting Real-Debrid Mount..."

# Check for API token
if [ -z "$RD_API_TOKEN" ]; then
    echo "ERROR: RD_API_TOKEN environment variable not set"
    exit 1
fi

# Create config directory
mkdir -p /config

# Create basic config
cat > /config/config.json << EOF
{
    "api_token": "$RD_API_TOKEN",
    "mountpoint": "/mnt/realdebrid",
    "enable_arr_stack": true,
    "movies_path": "/media/movies",
    "tv_path": "/media/tv"
}
EOF

# Start WebDAV if enabled
if [ "$ENABLE_WEBDAV" = "true" ]; then
    echo "Starting WebDAV server..."
    python3 /app/webdav_server.py --mount /mnt/realdebrid &
fi

# Start health checks if enabled
if [ "$ENABLE_HEALTH_CHECKS" = "true" ]; then
    echo "Starting health monitor..."
    python3 /app/health_manager.py watch 300 &
fi

# Mount Real-Debrid
echo "Mounting Real-Debrid..."
python3 /app/rdmount.py mount /mnt/realdebrid --daemon

# Keep container running
tail -f /dev/null
