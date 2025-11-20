# Quick Start - Advanced Mode

Get up and running with all advanced features in 5 minutes!

## Step 1: Install (30 seconds)

```bash
git clone https://github.com/FuadPoroshtica/Real-debrid.git
cd Real-debrid
./install.sh
```

## Step 2: Configure (2 minutes)

### Option A: Simple TUI Setup
```bash
./start.py
# Follow the wizard
```

### Option B: Advanced YAML Config
```bash
cp config_advanced.yml ~/.config/rdmount/config.yml
nano ~/.config/rdmount/config.yml
# Edit your API token and paths
```

Minimum required config:
```yaml
realdebrid:
  api_token: "YOUR_REAL_DEBRID_TOKEN"  # Get from https://real-debrid.com/apitoken

mount:
  mountpoint: ~/realdebrid

media:
  movies_path: ~/media/movies
  tv_path: ~/media/tv
```

## Step 3: Start Services (1 minute)

### All-in-One (Recommended)

```bash
./start.py
# Interactive menu with all features
```

### Individual Services

**Terminal 1 - Mount Real-Debrid:**
```bash
./rdmount.py mount ~/realdebrid --daemon
```

**Terminal 2 - WebDAV Server (optional):**
```bash
python3 webdav_server.py
# Enables rclone support at http://localhost:9999
```

**Terminal 3 - Health Monitor (optional):**
```bash
python3 health_manager.py watch 300
# Monitors torrent health every 5 minutes
```

**Terminal 4 - Resolver Watcher (optional):**
```bash
python3 resolver.py watch 60
# Auto-organizes new content every minute
```

## Step 4: Configure Media Server (1 minute)

### For Jellyfin:
1. Dashboard → Libraries → Add Media Library
2. Movies: Add `~/media/movies`
3. TV Shows: Add `~/media/tv`

### For Plex:
1. Settings → Libraries → Add Library
2. Movies: Browse to `~/media/movies`
3. TV Shows: Browse to `~/media/tv`

### For Radarr/Sonarr:
1. Settings → Media Management → Root Folders
2. Radarr: Add `~/media/movies`
3. Sonarr: Add `~/media/tv`

## Done! 🎉

Your setup is now:
- ✅ Mounting Real-Debrid torrents
- ✅ Organizing files for *arr apps
- ✅ Ready for Jellyfin/Plex
- ✅ Health monitoring (if enabled)
- ✅ WebDAV access (if enabled)

---

## What You Get

### Basic Features
- FUSE mount of Real-Debrid
- Streaming with no local storage
- Organized symlinks for movies/TV
- Beautiful TUI interface

### Advanced Features (Inspired by Zurg)
- **WebDAV server** - rclone compatible
- **Health checks** - prevents scanner issues
- **Auto-repair** - fixes failed torrents
- **Library hooks** - auto-scan media servers
- **RAR cleanup** - removes archive-only torrents
- **Regex filtering** - advanced file organization
- **VFS caching** - performance optimization
- **Integration APIs** - Plex, Jellyfin, Radarr, Sonarr

---

## Common Workflows

### Minimal Setup (Just Jellyfin)

```bash
# 1. Start TUI
./start.py

# 2. Run setup wizard
# - Enter API token
# - Set mount point
# - Skip *arr integration

# 3. Mount Real-Debrid
# Choose: Mount Real-Debrid

# 4. Point Jellyfin to ~/realdebrid
```

### Full *arr Stack

```bash
# 1. Configure with *arr integration
./start.py
# Enable *arr stack in setup

# 2. Mount and start resolver
# Choose: Mount Real-Debrid
# Choose: Start Resolver Watcher

# 3. Configure Radarr/Sonarr with media paths
```

### Power User (All Features)

```yaml
# Create config.yml with all features enabled
realdebrid:
  enable_health_checks: true
  enable_repair: true
  auto_delete_rar_torrents: true

mount:
  enable_webdav: true

hooks:
  on_library_update:
    enabled: true
```

Then run all services:
```bash
# Terminal 1: Main TUI
./start.py

# Terminal 2: WebDAV
python3 webdav_server.py

# Terminal 3: Health monitor
python3 health_manager.py watch 300
```

---

## Testing Your Setup

### Check Mount
```bash
ls ~/realdebrid
# Should show your torrents
```

### Check Symlinks
```bash
ls ~/media/movies
ls ~/media/tv
# Should show organized content
```

### Check WebDAV (if enabled)
```bash
curl http://localhost:9999/
# Should return file listing
```

### Check Health
```bash
python3 health_manager.py summary
# Shows health status
```

---

## Troubleshooting

### Mount not working?
```bash
# Check if FUSE is installed
fusermount -V

# Check if mount point exists
ls ~/realdebrid

# Try manual mount
./rdmount.py mount ~/realdebrid
```

### Symlinks not created?
```bash
# Run resolver manually
python3 resolver.py

# Check resolver is enabled in config
grep "enable_resolver" ~/.config/rdmount/config.yml
```

### WebDAV not accessible?
```bash
# Check if running
ps aux | grep webdav

# Test locally
curl http://localhost:9999/

# Check port is open
sudo netstat -tlnp | grep 9999
```

---

## Next Steps

1. **Read ADVANCED.md** - Learn all features in detail
2. **Configure hooks** - Auto-scan your media server
3. **Enable health checks** - Prevent library issues
4. **Try WebDAV + rclone** - Additional caching layer
5. **Customize directories** - Advanced filtering and organization

---

## Pro Tips

💡 **Use resolver watcher** - Automatically organizes new content
```bash
python3 resolver.py watch 60
```

💡 **Enable health monitoring** - Catches issues early
```bash
python3 health_manager.py watch 300
```

💡 **Use WebDAV with rclone** - Extra caching and remote access
```bash
rclone mount realdebrid: /mnt/rd --vfs-cache-mode full
```

💡 **Set up hooks** - Media server auto-scans on new content
```yaml
hooks:
  on_library_update:
    enabled: true
```

💡 **Run as systemd service** - Auto-start on boot
```bash
# TUI will help you set this up
./start.py
# Choose setup, enable auto-start
```

---

## Need Help?

- **Basic usage**: See README.md
- **Advanced features**: See ADVANCED.md
- **Config options**: See config_advanced.yml
- **Issues**: Open GitHub issue

---

**You now have the most advanced Real-Debrid solution available! 🚀**
