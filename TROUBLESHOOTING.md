# 🔧 Troubleshooting Guide

Common issues and solutions for Real-Debrid Media Stack deployment.

---

## 🐍 Python Issues

### Issue: `externally-managed-environment` error

**Symptoms:**
```
error: externally-managed-environment
× This environment is externally managed
```

**Cause:** Modern Ubuntu/Debian (23.04+, Debian 12+) protects system Python from pip installations.

**Solutions:**

#### Solution 1: Use the install script (Recommended)
```bash
./install_requirements.sh
```
This script will:
1. Try creating a virtual environment (recommended)
2. Fall back to `--break-system-packages` if you approve
3. Suggest Docker-only deployment

#### Solution 2: Manual virtual environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run any script
python start.py
```

#### Solution 3: Docker deployment only
For Docker deployment, you don't need to install Python packages locally:
```bash
./deploy.sh
```
All packages are installed inside Docker containers automatically.

#### Solution 4: System-wide (not recommended)
```bash
pip3 install --break-system-packages -r requirements.txt
```
⚠️ **Warning:** This can break system packages. Only use on dedicated servers.

---

## 🐳 Docker Issues

### Issue: Deploy script stops after installing Docker

**Symptoms:**
- Script installs Docker then exits
- No error message
- Web wizard doesn't start

**Cause:** Freshly installed Docker requires user to be in `docker` group, which requires logout/login.

**Solution 1: Automatic (script now handles this)**
The updated `deploy.sh` now automatically uses `sudo` for Docker commands if Docker was just installed.

Just re-run:
```bash
./deploy.sh
```

**Solution 2: Manual logout/login**
```bash
# After Docker installation completes:
logout
# Then login again and run:
./deploy.sh
```

**Solution 3: Use sudo for this session**
```bash
sudo ./deploy.sh
```

---

### Issue: Docker permission denied

**Symptoms:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add yourself to docker group
sudo usermod -aG docker $USER

# Apply group membership (choose one):
# Option 1: Logout and login
logout

# Option 2: Start new shell
newgrp docker

# Option 3: Use sudo for now
sudo docker compose up -d
```

---

### Issue: Docker Compose not found

**Symptoms:**
```
docker-compose: command not found
```

**Solution:**
Modern Docker uses `docker compose` (with space) instead of `docker-compose`.

The script automatically handles both versions. If you see this error:
```bash
# Check which version you have
docker compose version
# OR
docker-compose version

# Install Docker Compose plugin if needed
sudo apt-get install docker-compose-plugin
```

---

## 🌐 Web Wizard Issues

### Issue: Web wizard doesn't open

**Symptoms:**
- Browser doesn't open automatically
- Can't access http://debrid.local:5000

**Solutions:**

1. **Check if web server is running:**
```bash
ps aux | grep setup_wizard
```

2. **Try accessing directly:**
```bash
# Try localhost
http://localhost:5000

# Try IP address
http://127.0.0.1:5000

# Try debrid.local
http://debrid.local:5000
```

3. **Check if port 5000 is in use:**
```bash
sudo lsof -i :5000
```

4. **Start web wizard manually:**
```bash
# If using virtual environment
./venv/bin/python3 setup_wizard.py

# If installed system-wide
python3 setup_wizard.py
```

---

### Issue: `debrid.local` doesn't resolve

**Symptoms:**
- Browser can't find http://debrid.local

**Solution:**
```bash
# Check /etc/hosts
cat /etc/hosts | grep debrid

# Should show:
# 127.0.0.1 debrid.local

# If missing, add it:
echo "127.0.0.1 debrid.local" | sudo tee -a /etc/hosts

# Use IP instead:
http://127.0.0.1:5000
```

---

## 📦 Container Issues

### Issue: Containers fail to start

**Symptoms:**
- `docker compose ps` shows containers as "Exited"
- Services not accessible

**Solutions:**

1. **Check container logs:**
```bash
# All services
docker compose logs

# Specific service
docker compose logs jellyfin
docker compose logs realdebrid-mount
docker compose logs ai-monitor
```

2. **Check .env file exists:**
```bash
cat .env
```
Should contain:
```
RD_API_TOKEN=your_token_here
ANTHROPIC_API_KEY=your_key_here
...
```

3. **Restart containers:**
```bash
docker compose down
docker compose up -d
```

4. **Rebuild containers:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

### Issue: Real-Debrid mount fails

**Symptoms:**
- Container exits immediately
- Error: "FUSE not available"

**Solution:**
```bash
# Check if FUSE is available
ls -l /dev/fuse

# Install FUSE
sudo apt-get install fuse3

# Load FUSE kernel module
sudo modprobe fuse

# Check container logs
docker compose logs realdebrid-mount
```

---

## 🔑 API Key Issues

### Issue: Invalid API token

**Symptoms:**
- Mount fails with "Unauthorized"
- 401 errors in logs

**Solution:**
```bash
# Get new API token
# Visit: https://real-debrid.com/apitoken

# Update .env file
nano .env
# Change RD_API_TOKEN=your_new_token

# Restart containers
docker compose restart realdebrid-mount
```

---

## 🎬 Jellyfin Issues

### Issue: Jellyfin not showing content

**Symptoms:**
- Jellyfin is running but libraries are empty
- Content added in Radarr/Sonarr doesn't appear

**Solutions:**

1. **Check if resolver is running:**
```bash
docker compose logs realdebrid-mount | grep "resolver"
```

2. **Check media directories:**
```bash
ls -la ./media/movies/
ls -la ./media/tv/
```

3. **Manually trigger Jellyfin scan:**
- Open http://debrid.local/jellyfin
- Go to Dashboard → Libraries
- Click "Scan All Libraries"

4. **Check Jellyfin library paths:**
- Libraries should point to:
  - Movies: `/media/organized/movies`
  - TV Shows: `/media/organized/tv`

---

## 🔍 Radarr/Sonarr Issues

### Issue: No indexers available

**Symptoms:**
- Can't search for content
- "No indexers available" error

**Solution:**
1. Visit http://debrid.local/prowlarr
2. Add indexers (Settings → Indexers → Add)
3. Prowlarr will automatically sync to Radarr/Sonarr

---

### Issue: Downloads not starting

**Symptoms:**
- Content added but not downloading

**Solutions:**

1. **Check Real-Debrid account:**
- Visit https://real-debrid.com
- Verify premium is active
- Check torrent list

2. **Check Radarr/Sonarr logs:**
```bash
docker compose logs radarr
docker compose logs sonarr
```

3. **Check download client:**
- Settings → Download Clients
- Should have Real-Debrid configured

---

## 📊 General Debugging

### View all logs
```bash
docker compose logs -f
```

### Check service status
```bash
docker compose ps
```

### Restart everything
```bash
docker compose restart
```

### Complete reset (⚠️ DELETES DATA)
```bash
docker compose down -v
rm -rf ./config ./media ./downloads
./deploy.sh
```

### Check disk space
```bash
df -h
```

### Check memory usage
```bash
free -h
docker stats
```

---

## 🆘 Still Having Issues?

### Collect diagnostic information:

```bash
# System info
uname -a
docker --version
docker compose version
python3 --version

# Service status
docker compose ps

# Recent logs
docker compose logs --tail=100

# Disk space
df -h
```

### Then:
1. Check the AI monitor logs for automated fixes:
```bash
docker compose logs ai-monitor
```

2. Check existing issues: https://github.com/FuadPoroshtica/Real-debrid/issues

3. Create new issue with diagnostic info

---

## ✅ Quick Health Check

Run this to verify everything is working:

```bash
# Check all services
docker compose ps

# Should show all as "Up (healthy)":
# - jellyfin
# - radarr
# - sonarr
# - prowlarr
# - jellyseerr
# - nginx-proxy
# - realdebrid-mount
# - ai-monitor

# Test web access
curl -I http://debrid.local
# Should return: HTTP/1.1 200 OK

# Check mount
docker compose exec realdebrid-mount ls /mnt/realdebrid
```

If all checks pass, your system is healthy! 🎉
