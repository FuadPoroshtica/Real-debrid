FROM python:3.11-slim

# Install FUSE and system dependencies
RUN apt-get update && apt-get install -y \
    fuse \
    libfuse-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY realdebrid_api.py .
COPY realdebrid_fs.py .
COPY rdmount.py .
COPY resolver.py .
COPY webdav_server.py .
COPY config_manager.py .
COPY health_manager.py .
COPY hooks_manager.py .
COPY start.py .

# Make scripts executable
RUN chmod +x *.py

# Create mount point
RUN mkdir -p /mnt/realdebrid

# Entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["mount"]
