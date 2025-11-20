# 🤖 Complete Automation Guide

## How Everything Works Together Automatically

This guide explains how your entire media stack works automatically from adding a movie/show to watching it in Jellyfin.

---

## 🔄 The Automated Workflow

### Step 1: Add Content via Radarr/Sonarr
```
You search for a movie/show in Radarr/Sonarr
         ↓
Click "Add and Search"
```

### Step 2: Automatic Torrent Discovery
```
Prowlarr automatically provides indexers
         ↓
Radarr/Sonarr finds best torrent
         ↓
Sends magnet link to Real-Debrid API
```

### Step 3: Real-Debrid Downloads
```
Real-Debrid adds torrent
         ↓
Downloads at high speed (premium servers)
         ↓
Files appear in Real-Debrid mount
```

### Step 4: Automatic Organization
```
Resolver watches mount point (every 60 seconds)
         ↓
Detects new video files
         ↓
Identifies movie vs TV show
         ↓
Creates organized symlinks:
  • Movies → /media/movies/Movie Name (Year)/
  • TV Shows → /media/tv/Show Name/Season X/
```

### Step 5: Jellyfin Automatically Updates
```
Resolver triggers Jellyfin library scan
         ↓
Jellyfin detects new content
         ↓
Downloads metadata and artwork
         ↓
Content appears in Jellyfin
         ↓
🎬 Ready to watch!
```

---

## ⏱️ Timing

- **Real-Debrid download**: 10 seconds - 5 minutes (depends on torrent size)
- **Resolver detection**: Maximum 60 seconds (check interval)
- **Jellyfin scan**: 10-30 seconds
- **Total**: Usually 2-6 minutes from adding to watching!

---

## 📋 Service Roles

### Real-Debrid Mount
- **What**: FUSE filesystem that makes torrents appear as local files
- **Auto-configured**: Yes, at deployment
- **User action needed**: None

### Jellyfin
- **What**: Media server that you use to watch content
- **Auto-configured**: Partial - you need to add libraries on first run
- **User action needed**:
  1. Visit http://debrid.local/jellyfin
  2. Create admin account
  3. Add library: Movies → `/media/organized/movies`
  4. Add library: TV Shows → `/media/organized/tv`
  5. Done! Future content appears automatically

### Prowlarr
- **What**: Indexer manager that provides torrent sources
- **Auto-configured**: Automatically connects to Radarr/Sonarr
- **User action needed**:
  1. Visit http://debrid.local/prowlarr
  2. Add your preferred indexers (1337x, RARBG, etc.)
  3. Prowlarr syncs them to Radarr/Sonarr automatically

### Radarr
- **What**: Movie manager
- **Auto-configured**: Yes - root folder set to `/movies`
- **User action needed**:
  1. Search and add movies
  2. Everything else is automatic!

### Sonarr
- **What**: TV show manager
- **Auto-configured**: Yes - root folder set to `/tv`
- **User action needed**:
  1. Search and add shows
  2. Everything else is automatic!

### Jellyseerr (Optional)
- **What**: Beautiful request interface
- **Auto-configured**: No (optional)
- **User action needed**:
  1. Connect to Jellyfin
  2. Connect to Radarr and Sonarr
  3. Now you have a beautiful UI for requests!

---

## 🎯 Usage Examples

### Example 1: Adding a Movie

**What you do:**
1. Open Radarr at http://debrid.local/radarr
2. Search for "The Matrix"
3. Click "Add Movie" and "Search"

**What happens automatically:**
1. Radarr finds best torrent from Prowlarr
2. Sends magnet to Real-Debrid
3. Real-Debrid downloads (fast!)
4. File appears in mount
5. Resolver creates: `/media/movies/The Matrix (1999)/The.Matrix.1999.1080p.mkv`
6. Triggers Jellyfin scan
7. Movie appears in Jellyfin!

**Time**: 2-5 minutes total

---

### Example 2: Adding a TV Show

**What you do:**
1. Open Sonarr at http://debrid.local/sonarr
2. Search for "Breaking Bad"
3. Select quality profile
4. Click "Add" and "Search All"

**What happens automatically:**
1. Sonarr searches for all seasons
2. Finds torrents via Prowlarr
3. Sends to Real-Debrid
4. Real-Debrid downloads all episodes
5. Resolver organizes: `/media/tv/Breaking Bad/Season 01/Breaking.Bad.S01E01.mkv`
6. Jellyfin scans and adds all episodes
7. Entire show appears in Jellyfin!

**Time**: 5-15 minutes for complete series

---

## 🔧 Automatic Background Processes

### Resolver Watcher
- **Runs**: Every 60 seconds
- **Does**:
  - Checks Real-Debrid mount for new files
  - Detects media type (movie/TV)
  - Creates organized symlinks
  - Triggers Jellyfin scan
- **Location**: Runs inside realdebrid-mount container
- **Logs**: `docker compose logs -f realdebrid-mount`

### Health Monitor
- **Runs**: Every 5 minutes
- **Does**:
  - Checks all torrent health
  - Removes broken torrents
  - Cleans up RAR-only content
- **Location**: Runs inside realdebrid-mount container
- **Logs**: `docker compose logs -f realdebrid-mount`

### AI Monitor
- **Runs**: Every 60 seconds
- **Does**:
  - Monitors all service logs
  - Detects errors
  - Provides human-friendly explanations
  - Auto-fixes when safe
- **Location**: Separate ai-monitor container
- **Logs**: `docker compose logs -f ai-monitor`

---

## 🎬 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    YOU (The User)                           │
│                                                             │
│  Radarr/Sonarr:   Search and add content                  │
│  Jellyfin:        Watch content                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  RADARR / SONARR                            │
│                                                             │
│  - Searches for content via Prowlarr                       │
│  - Grabs best torrent                                      │
│  - Sends magnet to Real-Debrid                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   REAL-DEBRID                               │
│                                                             │
│  - Receives magnet link                                    │
│  - Downloads at high speed (premium)                       │
│  - Makes files available via API                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                REAL-DEBRID FUSE MOUNT                       │
│                                                             │
│  - Mounts torrents as filesystem                           │
│  - Streams on-demand (no local storage)                    │
│  - Available at /mnt/realdebrid                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   RESOLVER (AUTO)                           │
│                                                             │
│  - Watches mount every 60s                                 │
│  - Detects new video files                                 │
│  - Creates organized symlinks                              │
│  - /media/movies/ and /media/tv/                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              JELLYFIN LIBRARY SCAN (AUTO)                   │
│                                                             │
│  - Triggered by resolver                                   │
│  - Scans for new content                                   │
│  - Downloads metadata                                      │
│  - Updates library                                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   JELLYFIN (YOU WATCH!)                     │
│                                                             │
│  - Content appears in library                              │
│  - Full metadata and artwork                               │
│  - Ready to stream!                                        │
│  - 🎬 Enjoy!                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Environment Variables (Auto-configured)

The deployment automatically sets these:

```bash
RD_API_TOKEN          # Your Real-Debrid token
JELLYFIN_URL          # http://jellyfin:8096
JELLYFIN_API_KEY      # Auto-generated after Jellyfin setup
ENABLE_WEBDAV         # true
ENABLE_HEALTH_CHECKS  # true
```

---

## 📝 Manual Steps Summary

### First Time Only:

1. **Jellyfin** (2 minutes):
   - Create admin account
   - Add Movies library: `/media/organized/movies`
   - Add TV Shows library: `/media/organized/tv`

2. **Prowlarr** (3 minutes):
   - Add 2-3 indexers (1337x, RARBG, etc.)

3. **Done!** Everything else is automatic

### Every Time You Want Content:

1. Open Radarr or Sonarr
2. Search and add
3. Wait 2-5 minutes
4. Watch in Jellyfin!

---

## 🐛 Troubleshooting

### Content not appearing in Jellyfin?

**Check resolver logs:**
```bash
docker compose logs -f realdebrid-mount | grep Resolved
```

Should show:
```
✨ Resolved 1 files (1 movies, 0 TV shows)
📺 Triggered Jellyfin library scan
```

**Manually trigger scan:**
```bash
# In Jellyfin web UI:
Dashboard → Libraries → Scan All Libraries
```

### Radarr/Sonarr not finding torrents?

**Check Prowlarr:**
1. Visit http://debrid.local/prowlarr
2. Check indexers are added and working
3. Test search in Prowlarr directly

### Real-Debrid not downloading?

**Check mount:**
```bash
docker compose logs realdebrid-mount
```

**Check Real-Debrid account:**
- Visit https://real-debrid.com
- Check torrents list
- Verify premium is active

---

## 📊 Monitoring Your Stack

### View all logs:
```bash
docker compose logs -f
```

### View specific service:
```bash
docker compose logs -f jellyfin
docker compose logs -f radarr
docker compose logs -f realdebrid-mount
docker compose logs -f ai-monitor
```

### Check service health:
```bash
docker compose ps
```

All should show "(healthy)" status.

---

## 🎉 Enjoy Your Automated Media Stack!

Once initial setup is complete:
- **Add content** in Radarr/Sonarr
- **Wait a few minutes**
- **Watch in Jellyfin**

No manual file management!
No complex configuration!
Just add and watch! 🍿
