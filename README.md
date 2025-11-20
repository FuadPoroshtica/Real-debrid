# Real-Debrid Mount for Jellyfin

**The most advanced and easy-to-use Real-Debrid solution - combining the best of zurg with superior usability!**

A powerful Python tool that mounts your Real-Debrid account as a virtual drive on Linux using FUSE, with advanced features for Jellyfin, Plex, and the entire *arr stack.

## 🚀 Quick Start

```bash
./install.sh
./start.py
```

That's it! The beautiful TUI will guide you through everything.

## ✨ Features

### Core Features
- **Beautiful TUI** - Interactive menu-driven interface with rich formatting
- **FUSE Mount** - Mount Real-Debrid torrents as a virtual filesystem
- ***arr Stack Integration** - Full support for Radarr, Sonarr, Jellyseerr, Prowlarr
- **Automatic Organization** - Smart file organization by media type
- **Symlink Resolver** - Creates organized symlinks for media management
- **Lazy Loading** - Stream on-demand, no local storage required
- **Jellyfin & Plex Ready** - Direct integration with media servers
- **Excellent Error Handling** - Clear, actionable error messages
- **Auto-mount Support** - Systemd service for mounting on boot

### Advanced Features (Inspired by Zurg)
- **WebDAV Server** - rclone-compatible interface for remote mounting
- **Health Monitoring** - Automatic torrent health checks and repair
- **Library Hooks** - Auto-scan Plex/Jellyfin on library updates
- **RAR Cleanup** - Automatically removes archive-only torrents
- **Regex Filtering** - Advanced file organization with patterns
- **VFS Caching** - Configurable caching for optimal performance
- **YAML Configuration** - Powerful configuration system
- **Integration APIs** - Native Plex, Jellyfin, Radarr, Sonarr support

**📚 See [ADVANCED.md](ADVANCED.md) for complete advanced features documentation**
**⚡ See [QUICKSTART_ADVANCED.md](QUICKSTART_ADVANCED.md) for 5-minute setup guide**

## Requirements

- Linux operating system
- Python 3.7 or higher
- FUSE (Filesystem in Userspace)
- Active Real-Debrid premium account

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/FuadPoroshtica/Real-debrid.git
cd Real-debrid

# Run installation script
./install.sh

# Start the interactive TUI
./start.py
```

That's it! The TUI will guide you through the rest of the setup.

### Manual Installation

1. Install system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y fuse libfuse-dev python3 python3-pip
```

**Fedora:**
```bash
sudo dnf install -y fuse fuse-devel python3 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S fuse2 python python-pip
```

2. Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

## Configuration

### 1. Get Your API Token

1. Log in to your Real-Debrid account
2. Visit: https://real-debrid.com/apitoken
3. Copy your API token

### 2. Setup the Tool

Run the setup command and enter your API token:

```bash
./rdmount.py setup
```

Or provide the token directly:

```bash
./rdmount.py setup --token YOUR_API_TOKEN
```

The configuration will be saved to `~/.config/rdmount/config.json`

## Usage

### Quick Start with TUI

The easiest way to use this tool is through the interactive TUI:

```bash
./start.py
```

The TUI provides a beautiful menu-driven interface for:
- Setup and configuration
- Mounting/unmounting
- Status monitoring
- *arr stack integration
- Jellyfin setup guides

### Basic Commands (CLI)

**Mount Real-Debrid:**
```bash
./rdmount.py mount ~/realdebrid
```

**Mount in background (daemon mode):**
```bash
./rdmount.py mount ~/realdebrid --daemon
```

**Unmount:**
```bash
./rdmount.py unmount ~/realdebrid
```

**Show account information:**
```bash
./rdmount.py info
```

**Help:**
```bash
./rdmount.py --help
```

### Filesystem Structure

Once mounted, your Real-Debrid torrents will be organized as:

```
~/realdebrid/
├── TorrentName1/
│   ├── file1.mkv
│   ├── file2.mkv
│   └── subfolder/
│       └── file3.mkv
├── TorrentName2/
│   └── movie.mp4
└── ...
```

## *arr Stack Integration

This tool includes full support for the *arr stack, creating organized symlinks that work seamlessly with:

- **Radarr** - Automated movie management
- **Sonarr** - Automated TV show management
- **Jellyseerr** - Request management interface
- **Prowlarr** - Indexer aggregation
- **Jellyfin** - Media server

### How It Works

1. **Real-Debrid** downloads your torrents to the cloud
2. **FUSE Mount** makes them accessible as a local filesystem
3. **Resolver** creates organized symlinks:
   - Movies → `~/media/movies/MovieName (Year)/file.mkv`
   - TV Shows → `~/media/tv/ShowName/Season 01/episode.mkv`
4. ***arr apps** can now manage and serve the media

### Setup with TUI

The easiest way is using the interactive TUI:

```bash
./start.py
```

1. Choose "Setup / Reconfigure"
2. Enable *arr stack integration
3. Configure your media paths
4. Mount Real-Debrid
5. Run the resolver

### Manual Setup

1. **Configure paths in config:**
   ```bash
   nano ~/.config/rdmount/config.json
   ```

   Add:
   ```json
   {
     "enable_arr_stack": true,
     "movies_path": "~/media/movies",
     "tv_path": "~/media/tv"
   }
   ```

2. **Mount Real-Debrid:**
   ```bash
   ./rdmount.py mount ~/realdebrid --daemon
   ```

3. **Run resolver (one-time):**
   ```bash
   python3 resolver.py
   ```

4. **Or start resolver watcher (continuous):**
   ```bash
   python3 resolver.py watch 60
   ```
   (Checks every 60 seconds for new torrents)

### Configure *arr Apps

**Radarr Setup:**
```
Settings → Media Management → Root Folders
Add: ~/media/movies
```

**Sonarr Setup:**
```
Settings → Media Management → Root Folders
Add: ~/media/tv
```

**Jellyseerr Setup:**
```
Settings → Services
Add Radarr and Sonarr with above paths
```

**Prowlarr Setup:**
```
Connect to Radarr and Sonarr instances
Configure indexers as needed
```

### Resolver Commands

**One-time resolution:**
```bash
python3 resolver.py
```

**Watch mode (auto-resolve new torrents):**
```bash
python3 resolver.py watch 60
```

**Or use the TUI menu for easier access**

### File Organization

The resolver automatically organizes files based on naming patterns:

**Movies (detected by):**
- Year in filename (2024, 2023, etc.)
- No season/episode patterns
- Organized as: `MovieName (Year)/file.mkv`

**TV Shows (detected by):**
- S01E01 patterns
- 1x01 patterns
- "Season" in name
- Organized as: `ShowName/Season 01/file.mkv`

## Jellyfin Integration

### Setup Steps

1. **Mount Real-Debrid:**
   ```bash
   ./rdmount.py mount ~/realdebrid --daemon
   ```

2. **Add to Jellyfin:**
   - Open Jellyfin web interface
   - Go to Dashboard → Libraries
   - Click "Add Media Library"
   - Choose library type (Movies, TV Shows, etc.)
   - Add folder: `/home/YOUR_USERNAME/realdebrid`
   - Click OK

3. **Scan Library:**
   - Jellyfin will automatically scan and add your media
   - Files are streamed directly from Real-Debrid when played

### Auto-mount on Boot (Optional)

To automatically mount on system startup, you can create a systemd service:

1. Create service file:
   ```bash
   sudo nano /etc/systemd/system/realdebrid-mount.service
   ```

2. Add the following content (replace paths and username):
   ```ini
   [Unit]
   Description=Real-Debrid FUSE Mount
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=YOUR_USERNAME
   ExecStart=/usr/bin/python3 /path/to/Real-debrid/rdmount.py mount /home/YOUR_USERNAME/realdebrid --daemon
   ExecStop=/usr/bin/fusermount -u /home/YOUR_USERNAME/realdebrid
   Restart=on-failure
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable realdebrid-mount.service
   sudo systemctl start realdebrid-mount.service
   ```

## Troubleshooting

### Permission Denied Error

If you get permission errors when mounting:

```bash
sudo usermod -a -G fuse $USER
```

Log out and log back in for changes to take effect.

### FUSE Not Found

Make sure FUSE is installed:
```bash
# Check if FUSE is installed
modprobe fuse
```

### Mount Point Busy

If you get "Device or resource busy":
```bash
./rdmount.py unmount ~/realdebrid
# Or force unmount:
fusermount -u ~/realdebrid
```

### API Authentication Failed

- Verify your API token is correct
- Check your Real-Debrid account is active and premium
- Re-run setup: `./rdmount.py setup`

## How It Works

1. **FUSE Filesystem**: Uses Python FUSE bindings to create a virtual filesystem
2. **Real-Debrid API**: Fetches torrent list and file information from Real-Debrid
3. **Lazy Loading**: Files are streamed on-demand, no local storage required
4. **Caching**: Torrent structure is cached to reduce API calls
5. **HTTP Range Requests**: Supports seeking in media files

## Limitations

- Read-only filesystem (no modifications allowed)
- Requires active internet connection
- Performance depends on Real-Debrid server speed
- Only shows torrents with "downloaded" status

## Project Structure

```
Real-debrid/
├── start.py                # 🎯 Interactive TUI (START HERE!)
├── rdmount.py              # CLI mount tool
├── resolver.py             # Symlink resolver for *arr stack
├── realdebrid_api.py       # Real-Debrid API client
├── realdebrid_fs.py        # FUSE filesystem implementation
├── requirements.txt        # Python dependencies
├── install.sh              # Installation script
├── config.example.json     # Configuration example
└── README.md               # This file
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is not affiliated with or endorsed by Real-Debrid. Use at your own risk and ensure you comply with Real-Debrid's terms of service.

## Support

For issues or questions:
- Open an issue on GitHub
- Check Real-Debrid API documentation: https://api.real-debrid.com/

## Credits

- Built with [fusepy](https://github.com/fusepy/fusepy)
- Uses [Real-Debrid API](https://api.real-debrid.com/)

---

**Note**: This tool requires a premium Real-Debrid account. Get one at https://real-debrid.com/