# Real-Debrid Mount for Jellyfin

A simple Python tool that mounts your Real-Debrid account as a virtual drive on Linux using FUSE, making it easy to integrate with Jellyfin or other media servers.

## Features

- Mount Real-Debrid torrents as a virtual filesystem
- Read-only access to downloaded torrents
- Lazy loading and streaming support
- Simple CLI interface
- Easy Jellyfin integration
- Caching for improved performance

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
```

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

### Basic Commands

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
├── rdmount.py              # Main CLI script
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