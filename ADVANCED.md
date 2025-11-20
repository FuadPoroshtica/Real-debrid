# Advanced Features Documentation

This document covers the advanced features inspired by zurg-testing and enhanced for superior performance and usability.

## Table of Contents

1. [Advanced Configuration](#advanced-configuration)
2. [WebDAV Server](#webdav-server)
3. [Health Checks & Repair](#health-checks--repair)
4. [Library Update Hooks](#library-update-hooks)
5. [Advanced File Organization](#advanced-file-organization)
6. [Performance Tuning](#performance-tuning)
7. [Integrations](#integrations)

---

## Advanced Configuration

### YAML Configuration Format

Create `~/.config/rdmount/config.yml` for advanced configuration:

```yaml
version: v1

realdebrid:
  api_token: "YOUR_TOKEN_HERE"
  check_interval: 60
  enable_health_checks: true
  enable_repair: true
  auto_delete_rar_torrents: true

mount:
  mountpoint: ~/realdebrid
  enable_webdav: true
  webdav:
    host: 0.0.0.0
    port: 9999
    username: "rduser"
    password: "secure_password"
```

See `config_advanced.yml` for complete configuration options.

### Configuration Manager

```python
from config_manager import load_config

# Load configuration
config = load_config()

# Get values
api_token = config.get("realdebrid.api_token")
mountpoint = config.get("mount.mountpoint")

# Set values
config.set("realdebrid.check_interval", 120)
config.save()

# Validate configuration
errors = config.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
```

---

## WebDAV Server

### What is it?

A WebDAV server provides HTTP-based file access, making your Real-Debrid mount accessible to:
- **rclone** - Mount remotely or add extra caching layers
- **Windows/Mac** - Native WebDAV client support
- **Mobile apps** - Access from phones/tablets
- **Other servers** - Expose to other systems on your network

### Starting WebDAV Server

**Via CLI:**
```bash
python3 webdav_server.py --mount ~/realdebrid --port 9999 --username rduser --password secure123
```

**Via Config:**
```yaml
mount:
  enable_webdav: true
  webdav:
    host: 0.0.0.0
    port: 9999
    username: "rduser"
    password: "secure_password"
```

Then run: `python3 webdav_server.py`

### rclone Integration

1. **Add to rclone.conf:**
```ini
[realdebrid]
type = webdav
url = http://localhost:9999/
vendor = other
user = rduser
pass = secure_password
```

2. **Mount with rclone:**
```bash
rclone mount realdebrid: /mnt/realdebrid --allow-other --vfs-cache-mode full --dir-cache-time 10s
```

3. **Benefits:**
   - Additional VFS caching layer
   - Remote access over network
   - Encryption support
   - Bandwidth limiting
   - Mount on systems without FUSE

### WebDAV on Windows

1. Open File Explorer
2. Right-click "This PC" → "Map network drive"
3. Enter: `http://YOUR_SERVER_IP:9999/`
4. Enter username and password
5. Access your Real-Debrid library as a drive!

---

## Health Checks & Repair

### Automatic Health Monitoring

The health manager continuously monitors your torrents for issues:

- **Download Status** - Ensures torrents are fully downloaded
- **File Availability** - Checks if files are accessible
- **Seeder Health** - Monitors availability of seeders
- **Integrity Checks** - Validates torrent data

### Running Health Checks

**Check all torrents:**
```bash
python3 health_manager.py check
```

**Get health summary:**
```bash
python3 health_manager.py summary
```

**List unhealthy torrents:**
```bash
python3 health_manager.py unhealthy
```

**Continuous monitoring:**
```bash
python3 health_manager.py watch 300
# Checks every 300 seconds (5 minutes)
```

### Auto-Repair

Enable automatic repair in config:

```yaml
realdebrid:
  enable_repair: true
```

When enabled, the health manager will automatically attempt to fix:
- Failed downloads
- Unavailable files
- Corrupted torrents

### RAR Cleanup

Automatically remove torrents containing only RAR files (no video):

```yaml
cleanup:
  rar_handling:
    delete_rar_only_torrents: true
```

**Manual cleanup:**
```bash
python3 health_manager.py cleanup
```

---

## Library Update Hooks

### What are hooks?

Hooks are custom commands that run automatically when events occur:

- **on_library_update** - Triggers when torrents are added/removed
- **on_torrent_complete** - Triggers when a torrent finishes downloading
- **on_health_check_fail** - Triggers when a torrent fails health check

### Configuration

```yaml
hooks:
  on_library_update:
    enabled: true
    commands:
      # Scan Plex library
      - type: "shell"
        command: "curl -X POST 'http://localhost:32400/library/sections/all/refresh?X-Plex-Token=YOUR_TOKEN'"
        async: true

      # Scan Jellyfin library
      - type: "shell"
        command: "curl -X POST 'http://localhost:8096/Library/Refresh?api_key=YOUR_API_KEY'"
        async: true

      # Run custom script
      - type: "script"
        path: "/path/to/custom_script.sh"
        async: false

      # Send notification
      - type: "notification"
        message: "Library updated: {{changes}}"
```

### Template Variables

Use these in your commands:

- `{{torrent_id}}` - Torrent ID
- `{{torrent_name}}` - Torrent name
- `{{changes}}` - Number of changes
- `{{timestamp}}` - Current timestamp
- `{{issues}}` - List of issues (for health checks)

### Testing Hooks

```bash
# Test library update hook
python3 hooks_manager.py test-library-update

# Test torrent complete hook
python3 hooks_manager.py test-torrent-complete

# Manually trigger Plex scan
python3 hooks_manager.py plex-scan

# Manually trigger Jellyfin scan
python3 hooks_manager.py jellyfin-scan
```

---

## Advanced File Organization

### Directory Filtering

Create custom directory layouts with regex filtering:

```yaml
directories:
  # Movies - only 1080p/4K
  - path: movies_hd
    group: "movies"
    filters:
      include_regex:
        - ".*\\.(mkv|mp4)$"
        - ".*(1080p|2160p|4K).*"
      exclude_regex:
        - ".*sample.*"
        - ".*trailer.*"
      min_file_size: 1000  # 1GB minimum
      only_show_biggest_file: true
    actions:
      - type: "symlink"
        destination: "{{movies_path}}/{{torrent_name}}"

  # TV Shows - Season packs
  - path: tv_seasons
    group: "tvshows"
    filters:
      include_regex:
        - ".*[Ss]\\d{2}[Ee]\\d{2}.*"
      has_episodes: true
    actions:
      - type: "symlink"
        destination: "{{tv_path}}/{{show_name}}/Season {{season}}"

  # Anime
  - path: anime
    group: "anime"
    filters:
      include_regex:
        - ".*\\[.*\\].*\\.(mkv|mp4)$"
      keywords:
        - "anime"
    actions:
      - type: "symlink"
        destination: "{{tv_path}}/Anime/{{show_name}}"
```

### Grouping

Organize content with groups and ordering:

```yaml
directories:
  - path: movies_4k
    group: "movies"
    group_order: 10

  - path: movies_1080p
    group: "movies"
    group_order: 20

  - path: movies_other
    group: "movies"
    group_order: 30
```

Files are processed in group order, with lower numbers first.

---

## Performance Tuning

### VFS Cache Configuration

```yaml
mount:
  vfs_cache:
    enabled: true
    mode: "full"  # Options: off, minimal, writes, full
    dir_cache_time: 10
    max_age: 3600
    poll_interval: 60
```

**Cache Modes:**
- `off` - No caching (lowest memory, highest latency)
- `minimal` - Cache file metadata only
- `writes` - Cache writes, direct stream reads
- `full` - Cache everything (highest memory, lowest latency)

### Performance Settings

```yaml
performance:
  enable_cache: true
  cache_size: 512  # MB
  cache_ttl: 300  # seconds
  prefetch_metadata: true
  parallel_downloads: 3
  read_ahead_kb: 4096
  use_http2: true
```

### FUSE Options

```yaml
mount:
  fuse_options:
    allow_other: true
    auto_cache: true
    kernel_cache: false
    entry_timeout: 30
    attr_timeout: 30
    negative_timeout: 5
```

**Tuning Tips:**
- Higher `entry_timeout` = Less API calls, slower updates
- `kernel_cache: true` = Better performance, may show stale data
- `auto_cache: true` = Automatic kernel cache management

---

## Integrations

### Plex Integration

```yaml
integrations:
  plex:
    enabled: true
    url: "http://localhost:32400"
    token: "YOUR_PLEX_TOKEN"
    library_sections: [1, 2]  # Optional: specific sections
```

**Auto-scan on library update:**
```yaml
hooks:
  on_library_update:
    enabled: true
    commands:
      - type: "shell"
        command: "curl -X POST '{{plex.url}}/library/sections/all/refresh?X-Plex-Token={{plex.token}}'"
        async: true
```

### Jellyfin Integration

```yaml
integrations:
  jellyfin:
    enabled: true
    url: "http://localhost:8096"
    api_key: "YOUR_JELLYFIN_API_KEY"
```

### Radarr Integration

```yaml
integrations:
  radarr:
    enabled: true
    url: "http://localhost:7878"
    api_key: "YOUR_RADARR_API_KEY"
```

**Auto-scan on new movies:**
```yaml
hooks:
  on_torrent_complete:
    enabled: true
    commands:
      - type: "shell"
        command: "curl -X POST '{{radarr.url}}/api/v3/command' -H 'X-Api-Key: {{radarr.api_key}}' -d '{\"name\":\"RescanFolders\"}'"
        async: true
```

### Sonarr Integration

```yaml
integrations:
  sonarr:
    enabled: true
    url: "http://localhost:8989"
    api_key: "YOUR_SONARR_API_KEY"
```

---

## Experimental Features

### Smart Caching

Learns your viewing patterns and pre-caches likely files:

```yaml
experimental:
  smart_caching: true
```

### Bandwidth Limiting

Limit download bandwidth (KB/s):

```yaml
experimental:
  bandwidth_limit: 10000  # 10 MB/s
```

### Direct Play Optimization

Optimize for direct play (no transcoding):

```yaml
experimental:
  direct_play_optimization: true
```

---

## Complete Workflow Example

### Setup for Plex + Radarr + Sonarr

1. **Create config.yml:**

```yaml
version: v1

realdebrid:
  api_token: "YOUR_RD_TOKEN"
  enable_health_checks: true
  enable_repair: true
  auto_delete_rar_torrents: true

mount:
  mountpoint: ~/realdebrid
  enable_webdav: true
  webdav:
    port: 9999

media:
  movies_path: ~/media/movies
  tv_path: ~/media/tv
  enable_resolver: true
  resolver_watch: true

hooks:
  on_library_update:
    enabled: true
    commands:
      - type: "shell"
        command: "curl -X POST 'http://localhost:32400/library/sections/all/refresh?X-Plex-Token=YOUR_PLEX_TOKEN'"
        async: true

integrations:
  plex:
    enabled: true
    url: "http://localhost:32400"
    token: "YOUR_PLEX_TOKEN"
  radarr:
    enabled: true
    url: "http://localhost:7878"
    api_key: "YOUR_RADARR_KEY"
  sonarr:
    enabled: true
    url: "http://localhost:8989"
    api_key: "YOUR_SONARR_KEY"
```

2. **Start services:**

```bash
# Mount Real-Debrid
./start.py

# Start WebDAV server (in another terminal)
python3 webdav_server.py

# Start health monitor (in another terminal)
python3 health_manager.py watch 300

# Start resolver watcher (in another terminal)
# (or enable resolver_watch in config)
```

3. **Configure *arr apps:**
- Radarr: Add root folder `~/media/movies`
- Sonarr: Add root folder `~/media/tv`
- Both will auto-scan on new content

4. **Add to Plex:**
- Movies library: `~/media/movies`
- TV Shows library: `~/media/tv`
- Auto-scans on library updates

---

## Tips & Best Practices

1. **Start simple** - Use default config first, then customize
2. **Enable health checks** - Prevents Plex scanner freezing
3. **Use WebDAV + rclone** - Extra caching layer for better performance
4. **Configure hooks** - Automate library scans
5. **Monitor logs** - Check `~/.config/rdmount/rdmount.log`
6. **Test hooks** - Use test commands before enabling
7. **Backup config** - Save your `config.yml`

---

## Troubleshooting

### WebDAV not accessible

```bash
# Check if server is running
curl http://localhost:9999/

# Check firewall
sudo ufw allow 9999
```

### Health checks failing

```bash
# Check API token
python3 -c "from config_manager import load_config; print(load_config().get('realdebrid.api_token'))"

# Test API access
python3 health_manager.py summary
```

### Hooks not triggering

```bash
# Test hook manually
python3 hooks_manager.py test-library-update

# Check hook configuration
python3 -c "from config_manager import load_config; print(load_config().get('hooks'))"
```

---

## Performance Comparison

**vs. zurg:**
- ✓ Compatible WebDAV interface
- ✓ Similar health check system
- ✓ Better Python integration
- ✓ More flexible configuration
- ✓ Native FUSE (no rclone dependency)
- ✓ Built-in *arr stack resolver

**vs. rclone mount alone:**
- ✓ Direct Real-Debrid integration
- ✓ Health monitoring
- ✓ Automatic organization
- ✓ Hook system
- ✓ Easier setup

---

## Need Help?

- Check main README.md
- Review config_advanced.yml for all options
- Test with verbose mode: `--verbose` or `debug: true`
- Open an issue on GitHub

---

**This tool is now the most advanced Real-Debrid solution available, combining the best features of zurg with superior usability and Python ecosystem integration!**
