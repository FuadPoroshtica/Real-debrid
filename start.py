#!/usr/bin/env python3
"""
Real-Debrid Mount - Interactive Setup & Management
Beautiful TUI with excellent error handling
"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.markdown import Markdown
    import inquirer
except ImportError:
    print("⚠️  Missing required dependencies!")
    print("\nPlease install dependencies first:")
    print("  pip3 install -r requirements.txt")
    print("\nOr run:")
    print("  ./install.sh")
    sys.exit(1)

from realdebrid_api import RealDebridAPI

console = Console()

CONFIG_DIR = Path.home() / ".config" / "rdmount"
CONFIG_FILE = CONFIG_DIR / "config.json"
SYSTEMD_SERVICE = "/etc/systemd/system/realdebrid-mount.service"


class Colors:
    """Color constants for consistent UI"""
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "cyan"
    PROMPT = "magenta"


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def show_header():
    """Display beautiful header"""
    clear_screen()
    header = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        Real-Debrid Mount for Jellyfin                   ║
║        Simple • Fast • Reliable                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    console.print(header, style="bold cyan")
    console.print()


def show_error(message, details=None):
    """Display error message with details"""
    console.print(f"\n❌ [bold red]Error:[/bold red] {message}")
    if details:
        console.print(f"   [dim]{details}[/dim]")
    console.print()


def show_success(message):
    """Display success message"""
    console.print(f"✅ [bold green]{message}[/bold green]")


def show_warning(message):
    """Display warning message"""
    console.print(f"⚠️  [bold yellow]{message}[/bold yellow]")


def show_info(message):
    """Display info message"""
    console.print(f"ℹ️  [cyan]{message}[/cyan]")


def load_config():
    """Load configuration with error handling"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        show_error(f"Failed to load configuration", str(e))
        return {}


def save_config(config):
    """Save configuration with error handling"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        show_error(f"Failed to save configuration", str(e))
        return False


def check_dependencies():
    """Check if required system dependencies are installed"""
    console.print("\n[cyan]Checking system dependencies...[/cyan]")

    issues = []

    # Check Python version
    if sys.version_info < (3, 7):
        issues.append("Python 3.7 or higher is required")
    else:
        show_success(f"Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check FUSE
    try:
        result = subprocess.run(['which', 'fusermount'], capture_output=True)
        if result.returncode == 0:
            show_success("FUSE is installed")
        else:
            issues.append("FUSE is not installed")
    except Exception:
        issues.append("Unable to check FUSE installation")

    # Check pip packages
    try:
        import fuse
        show_success("fusepy module available")
    except ImportError:
        issues.append("fusepy not installed - run: pip3 install -r requirements.txt")

    if issues:
        console.print()
        show_error("Missing dependencies:")
        for issue in issues:
            console.print(f"  • {issue}")
        console.print("\n[yellow]Run ./install.sh to install dependencies[/yellow]")
        return False

    console.print()
    return True


def validate_api_token(token):
    """Validate Real-Debrid API token"""
    if not token or len(token) < 20:
        return False, "API token appears to be invalid (too short)"

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Validating API token...", total=None)
            api = RealDebridAPI(token)
            user_info = api.get_user_info()

        return True, user_info
    except Exception as e:
        return False, str(e)


def setup_wizard():
    """Interactive setup wizard"""
    show_header()
    console.print("[bold cyan]🚀 Setup Wizard[/bold cyan]")
    console.print()
    console.print("This wizard will help you configure Real-Debrid Mount.")
    console.print()

    config = load_config()

    # Step 1: API Token
    console.print("[bold]Step 1:[/bold] Real-Debrid API Token")
    console.print()

    if config.get("api_token"):
        show_info("Existing API token found")
        if not Confirm.ask("Would you like to use the existing token?", default=True):
            config["api_token"] = None

    if not config.get("api_token"):
        console.print("[dim]Get your token from:[/dim] https://real-debrid.com/apitoken")
        console.print()

        max_attempts = 3
        for attempt in range(max_attempts):
            token = Prompt.ask("Enter your API token", password=True)

            valid, result = validate_api_token(token)
            if valid:
                config["api_token"] = token
                console.print()
                show_success("API token validated!")
                console.print(f"  Username: [bold]{result.get('username', 'Unknown')}[/bold]")
                console.print(f"  Account: [bold]{result.get('type', 'Unknown')}[/bold]")
                console.print()
                break
            else:
                show_error(f"Invalid API token", result)
                if attempt < max_attempts - 1:
                    console.print(f"[yellow]Attempts remaining: {max_attempts - attempt - 1}[/yellow]")
                    console.print()
        else:
            show_error("Failed to validate API token after 3 attempts")
            return False

    # Step 2: Mount Point
    console.print("[bold]Step 2:[/bold] Mount Point Configuration")
    console.print()

    default_mount = config.get("mountpoint", str(Path.home() / "realdebrid"))
    mountpoint = Prompt.ask(
        "Where should Real-Debrid be mounted?",
        default=default_mount
    )
    mountpoint = os.path.expanduser(mountpoint)
    config["mountpoint"] = mountpoint

    console.print()

    # Step 3: *arr Stack Integration
    console.print("[bold]Step 3:[/bold] *arr Stack Integration (Optional)")
    console.print("[dim]Configure paths for Radarr, Sonarr, Jellyseerr, Prowlarr[/dim]")
    console.print()

    enable_arr = Confirm.ask(
        "Enable *arr stack integration? (creates organized symlinks for media)",
        default=True
    )
    config["enable_arr_stack"] = enable_arr

    if enable_arr:
        default_movies = config.get("movies_path", str(Path.home() / "media" / "movies"))
        movies_path = Prompt.ask(
            "Movies library path (for Radarr/Jellyfin)",
            default=default_movies
        )
        config["movies_path"] = os.path.expanduser(movies_path)

        default_tv = config.get("tv_path", str(Path.home() / "media" / "tv"))
        tv_path = Prompt.ask(
            "TV Shows library path (for Sonarr/Jellyfin)",
            default=default_tv
        )
        config["tv_path"] = os.path.expanduser(tv_path)

        console.print()
        show_info(f"Movies: {config['movies_path']}")
        show_info(f"TV Shows: {config['tv_path']}")

    console.print()

    # Step 4: Auto-start
    console.print("[bold]Step 4:[/bold] Auto-start Configuration")
    console.print()

    auto_start = Confirm.ask(
        "Would you like to auto-mount on system boot? (requires sudo)",
        default=False
    )
    config["auto_start"] = auto_start

    console.print()

    # Save configuration
    if save_config(config):
        show_success(f"Configuration saved to {CONFIG_FILE}")
        console.print()
        return True
    else:
        return False


def create_systemd_service(config):
    """Create systemd service for auto-start"""
    try:
        mountpoint = config.get("mountpoint")
        script_path = os.path.abspath(__file__).replace("start.py", "rdmount.py")
        username = os.getenv("USER")

        service_content = f"""[Unit]
Description=Real-Debrid FUSE Mount
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={username}
ExecStart=/usr/bin/python3 {script_path} mount {mountpoint} --daemon
ExecStop=/usr/bin/fusermount -u {mountpoint}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

        # Write service file (requires sudo)
        console.print("\n[yellow]Creating systemd service (requires sudo)...[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Setting up systemd service...", total=None)

            # Write service file
            process = subprocess.Popen(
                ['sudo', 'tee', SYSTEMD_SERVICE],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=service_content.encode())

            if process.returncode != 0:
                raise Exception("Failed to create service file")

            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)

            # Enable service
            subprocess.run(['sudo', 'systemctl', 'enable', 'realdebrid-mount.service'], check=True)

        show_success("Systemd service created and enabled")
        return True

    except subprocess.CalledProcessError as e:
        show_error("Failed to create systemd service", str(e))
        return False
    except Exception as e:
        show_error("Failed to setup auto-start", str(e))
        return False


def mount_realdebrid_interactive(config):
    """Mount Real-Debrid with progress feedback"""
    mountpoint = config.get("mountpoint")
    api_token = config.get("api_token")

    if not api_token:
        show_error("No API token configured. Run setup first.")
        return False

    # Create mountpoint
    try:
        os.makedirs(mountpoint, exist_ok=True)
    except Exception as e:
        show_error(f"Failed to create mountpoint directory", str(e))
        return False

    # Check if already mounted
    try:
        result = subprocess.run(['mount'], capture_output=True, text=True)
        if mountpoint in result.stdout:
            show_warning(f"{mountpoint} is already mounted")
            if not Confirm.ask("Unmount and remount?", default=False):
                return False
            unmount_realdebrid(mountpoint)
    except Exception:
        pass

    console.print()
    console.print(f"[bold cyan]Mounting Real-Debrid to:[/bold cyan] {mountpoint}")
    console.print()

    try:
        # Import here to avoid circular dependencies
        from realdebrid_fs import mount_realdebrid

        # Run in background
        script_path = os.path.abspath(__file__).replace("start.py", "rdmount.py")
        process = subprocess.Popen(
            [sys.executable, script_path, 'mount', mountpoint, '--daemon'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(2)  # Give it time to mount

        # Check if mounted
        result = subprocess.run(['mount'], capture_output=True, text=True)
        if mountpoint in result.stdout:
            show_success("Real-Debrid mounted successfully!")
            console.print()
            show_info(f"Mount point: {mountpoint}")
            console.print()
            return True
        else:
            show_error("Mount may have failed. Check logs for details.")
            return False

    except Exception as e:
        show_error("Failed to mount Real-Debrid", str(e))
        return False


def unmount_realdebrid(mountpoint=None):
    """Unmount Real-Debrid"""
    config = load_config()
    if not mountpoint:
        mountpoint = config.get("mountpoint")

    if not mountpoint:
        show_error("No mountpoint configured")
        return False

    try:
        subprocess.run(['fusermount', '-u', mountpoint], check=True)
        show_success(f"Unmounted: {mountpoint}")
        return True
    except subprocess.CalledProcessError:
        show_error(f"Failed to unmount {mountpoint}")
        return False


def show_status():
    """Show current status"""
    show_header()
    console.print("[bold cyan]📊 Status[/bold cyan]")
    console.print()

    config = load_config()

    # Configuration status
    table = Table(title="Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row(
        "API Token",
        "✅ Configured" if config.get("api_token") else "❌ Not configured"
    )
    table.add_row(
        "Mount Point",
        config.get("mountpoint", "Not set")
    )
    table.add_row(
        "Auto-start",
        "Enabled" if config.get("auto_start") else "Disabled"
    )

    console.print(table)
    console.print()

    # Mount status
    mountpoint = config.get("mountpoint")
    if mountpoint:
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if mountpoint in result.stdout:
                show_success(f"Real-Debrid is mounted at: {mountpoint}")
            else:
                show_info(f"Real-Debrid is not currently mounted")
        except Exception:
            show_warning("Unable to check mount status")

    # Account info
    if config.get("api_token"):
        try:
            api = RealDebridAPI(config["api_token"])
            user_info = api.get_user_info()

            console.print()
            account_table = Table(title="Account Information", box=box.ROUNDED)
            account_table.add_column("Property", style="cyan")
            account_table.add_column("Value", style="white")

            account_table.add_row("Username", user_info.get("username", "Unknown"))
            account_table.add_row("Email", user_info.get("email", "Unknown"))
            account_table.add_row("Account Type", user_info.get("type", "Unknown"))
            account_table.add_row("Points", str(user_info.get("points", 0)))

            console.print(account_table)

            # Torrents
            torrents = api.get_torrents()
            console.print()
            console.print(f"[cyan]Active Torrents:[/cyan] {len(torrents)}")

        except Exception as e:
            show_error("Failed to fetch account info", str(e))

    console.print()


def run_resolver():
    """Run resolver to create symlinks for *arr stack"""
    show_header()
    console.print("[bold cyan]🔄 *arr Stack Resolver[/bold cyan]")
    console.print()

    config = load_config()

    if not config.get("enable_arr_stack"):
        show_warning("*arr stack integration is not enabled")
        console.print("Enable it in setup to use this feature.")
        return False

    if not config.get("api_token"):
        show_error("Not configured. Run setup first.")
        return False

    mountpoint = config.get("mountpoint")
    if not mountpoint or not Path(mountpoint).exists():
        show_error("Real-Debrid is not mounted")
        console.print("Mount it first using 'Mount Real-Debrid' option.")
        return False

    media_paths = {
        'movies': config.get('movies_path', str(Path.home() / 'media' / 'movies')),
        'tv': config.get('tv_path', str(Path.home() / 'media' / 'tv'))
    }

    try:
        from resolver import MediaResolver

        console.print("Creating symlinks for Radarr, Sonarr, and Jellyfin...")
        console.print()

        resolver = MediaResolver(config['api_token'], mountpoint, media_paths)
        stats = resolver.resolve_all()

        console.print()
        show_success(f"Resolved {stats['total']} files")
        console.print(f"  Movies: [bold]{stats['movies']}[/bold]")
        console.print(f"  TV Shows: [bold]{stats['tv']}[/bold]")

        console.print()
        show_info(f"Movies folder: {media_paths['movies']}")
        show_info(f"TV Shows folder: {media_paths['tv']}")

        return True

    except Exception as e:
        show_error("Failed to run resolver", str(e))
        return False


def start_resolver_watcher():
    """Start resolver in watch mode"""
    show_header()
    console.print("[bold cyan]👀 Resolver Watch Mode[/bold cyan]")
    console.print()

    config = load_config()

    if not config.get("enable_arr_stack"):
        show_warning("*arr stack integration is not enabled")
        console.print("Enable it in setup to use this feature.")
        return False

    interval = Prompt.ask(
        "Check interval in seconds",
        default="60"
    )

    try:
        interval = int(interval)
    except ValueError:
        show_error("Invalid interval")
        return False

    console.print()
    console.print(f"[cyan]Starting resolver watcher (checking every {interval}s)...[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    try:
        from resolver import MediaResolver

        media_paths = {
            'movies': config.get('movies_path', str(Path.home() / 'media' / 'movies')),
            'tv': config.get('tv_path', str(Path.home() / 'media' / 'tv'))
        }

        resolver = MediaResolver(config['api_token'], config['mountpoint'], media_paths)
        resolver.watch_and_resolve(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped resolver watcher[/yellow]")
    except Exception as e:
        show_error("Resolver watcher failed", str(e))


def show_arr_stack_guide():
    """Show *arr stack integration guide"""
    show_header()
    console.print("[bold cyan]📚 *arr Stack Integration Guide[/bold cyan]")
    console.print()

    config = load_config()
    movies_path = config.get("movies_path", "~/media/movies")
    tv_path = config.get("tv_path", "~/media/tv")

    guide = f"""
## Overview

This tool creates organized symlinks from Real-Debrid torrents to your media libraries,
making them compatible with:

- **Radarr** - Movie management
- **Sonarr** - TV show management
- **Jellyseerr** - Request management
- **Prowlarr** - Indexer management
- **Jellyfin** - Media server

## Setup Steps

### 1. Mount Real-Debrid
```bash
./start.py
# Choose: Mount Real-Debrid
```

### 2. Run Resolver
```bash
./start.py
# Choose: Run *arr Resolver (One-time)
```

This creates organized symlinks:
- Movies → `{movies_path}/MovieName (Year)/file.mkv`
- TV Shows → `{tv_path}/ShowName/Season 01/episode.mkv`

### 3. Configure Your *arr Apps

**Radarr:**
- Add root folder: `{movies_path}`
- The resolver automatically organizes movies by title and year

**Sonarr:**
- Add root folder: `{tv_path}`
- The resolver organizes shows by season folders

**Jellyfin:**
- Add library for Movies: `{movies_path}`
- Add library for TV Shows: `{tv_path}`
- Enable hardware transcoding if needed

**Jellyseerr:**
- Connect to your Radarr and Sonarr instances
- Requests will automatically appear when resolved

### 4. Automatic Resolution (Optional)

For automatic symlink creation:
```bash
./start.py
# Choose: Start Resolver Watcher
```

This monitors for new torrents and creates symlinks automatically.

## How It Works

1. Real-Debrid downloads torrents
2. FUSE mount makes them accessible
3. Resolver scans for new media
4. Creates organized symlinks for *arr apps
5. *arr apps can now manage and serve the media

## Tips

- Run resolver after adding new torrents
- Use watcher mode for automatic resolution
- Symlinks use minimal disk space (just pointers)
- Real-Debrid handles the actual storage
    """

    md = Markdown(guide)
    console.print(md)
    console.print()


def show_jellyfin_instructions():
    """Show Jellyfin integration instructions"""
    show_header()
    console.print("[bold cyan]📺 Jellyfin Integration Guide[/bold cyan]")
    console.print()

    config = load_config()
    mountpoint = config.get("mountpoint", "~/realdebrid")

    instructions = f"""
## Step 1: Ensure Real-Debrid is Mounted

Make sure Real-Debrid is mounted and running:
```bash
./start.py mount
```

## Step 2: Add Library to Jellyfin

1. Open Jellyfin web interface
2. Go to **Dashboard** → **Libraries**
3. Click **Add Media Library**
4. Choose library type:
   - **Movies** for movie content
   - **TV Shows** for series
5. Add folder: `{os.path.abspath(os.path.expanduser(mountpoint))}`
6. Configure as needed
7. Click **OK**

## Step 3: Scan Library

Jellyfin will automatically scan and index your media files.
Files are streamed directly from Real-Debrid when played.

## Tips

- Each torrent appears as a folder in the mount point
- Jellyfin will recognize video files automatically
- Ensure transcoding is enabled for compatibility
- For best performance, use direct play when possible
    """

    md = Markdown(instructions)
    console.print(md)
    console.print()


def main_menu():
    """Display main menu and handle user choice"""
    while True:
        show_header()
        console.print("[bold cyan]Main Menu[/bold cyan]")
        console.print()

        config = load_config()

        choices = [
            ("Setup / Reconfigure", "setup"),
            ("Mount Real-Debrid", "mount"),
            ("Unmount Real-Debrid", "unmount"),
            ("Show Status", "status"),
        ]

        # Add resolver options if enabled
        if config.get("enable_arr_stack"):
            choices.extend([
                ("Run *arr Resolver (One-time)", "resolver"),
                ("Start Resolver Watcher (Background)", "watcher"),
                ("*arr Stack Integration Guide", "arr_guide"),
            ])

        choices.extend([
            ("Jellyfin Integration Guide", "jellyfin"),
            ("Exit", "exit")
        ])

        questions = [
            inquirer.List(
                'action',
                message="What would you like to do?",
                choices=[c[0] for c in choices]
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            break

        selected = answers['action']
        action = next(c[1] for c in choices if c[0] == selected)

        console.print()

        if action == "setup":
            if setup_wizard():
                config = load_config()
                if config.get("auto_start"):
                    create_systemd_service(config)

                console.print()
                if Confirm.ask("Would you like to mount Real-Debrid now?", default=True):
                    mount_realdebrid_interactive(config)

            console.print()
            Prompt.ask("Press Enter to continue")

        elif action == "mount":
            config = load_config()
            if not config.get("api_token"):
                show_error("Not configured. Run setup first.")
            else:
                mount_realdebrid_interactive(config)

            console.print()
            Prompt.ask("Press Enter to continue")

        elif action == "unmount":
            unmount_realdebrid()
            console.print()
            Prompt.ask("Press Enter to continue")

        elif action == "status":
            show_status()
            console.print()
            Prompt.ask("Press Enter to continue")

        elif action == "resolver":
            run_resolver()
            console.print()
            Prompt.ask("Press Enter to continue")

        elif action == "watcher":
            start_resolver_watcher()
            console.print()
            Prompt.ask("Press Enter to continue")

        elif action == "arr_guide":
            show_arr_stack_guide()
            Prompt.ask("Press Enter to continue")

        elif action == "jellyfin":
            show_jellyfin_instructions()
            Prompt.ask("Press Enter to continue")

        elif action == "exit":
            console.print("[cyan]Goodbye! 👋[/cyan]")
            break


def main():
    """Main entry point"""
    try:
        show_header()

        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)

        console.print()

        # Check if setup is needed
        config = load_config()
        if not config.get("api_token"):
            show_info("First time setup required")
            console.print()
            if Confirm.ask("Would you like to run the setup wizard?", default=True):
                if not setup_wizard():
                    sys.exit(1)

                config = load_config()
                if config.get("auto_start"):
                    create_systemd_service(config)

                console.print()
                if Confirm.ask("Would you like to mount Real-Debrid now?", default=True):
                    mount_realdebrid_interactive(config)

                console.print()
                Prompt.ask("Press Enter to continue to main menu")

        # Show main menu
        main_menu()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        show_error("Unexpected error occurred", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
