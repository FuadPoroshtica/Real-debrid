#!/usr/bin/env python3
"""
Real-Debrid Mount Tool
Simple CLI to mount Real-Debrid as a virtual drive
"""
import argparse
import os
import sys
import json
import subprocess
from pathlib import Path
from realdebrid_fs import mount_realdebrid
from realdebrid_api import RealDebridAPI


CONFIG_FILE = os.path.expanduser("~/.config/rdmount/config.json")


def load_config():
    """Load configuration from file"""
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config):
    """Save configuration to file"""
    config_dir = os.path.dirname(CONFIG_FILE)
    os.makedirs(config_dir, exist_ok=True)

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def setup_command(args):
    """Setup Real-Debrid API token"""
    config = load_config()

    if args.token:
        api_token = args.token
    else:
        print("Enter your Real-Debrid API token:")
        print("(Get it from: https://real-debrid.com/apitoken)")
        api_token = input("API Token: ").strip()

    if not api_token:
        print("Error: API token is required")
        return 1

    # Verify token
    try:
        api = RealDebridAPI(api_token)
        user_info = api.get_user_info()
        print(f"\nAuthentication successful!")
        print(f"Username: {user_info.get('username', 'Unknown')}")
        print(f"Email: {user_info.get('email', 'Unknown')}")
        print(f"Account type: {user_info.get('type', 'Unknown')}")

        config["api_token"] = api_token
        save_config(config)
        print(f"\nConfiguration saved to: {CONFIG_FILE}")
        return 0
    except Exception as e:
        print(f"\nError: Failed to authenticate: {e}")
        return 1


def mount_command(args):
    """Mount Real-Debrid filesystem"""
    config = load_config()

    api_token = args.token or config.get("api_token")

    if not api_token:
        print("Error: No API token configured.")
        print("Run 'rdmount.py setup' first or use --token option")
        return 1

    mountpoint = os.path.expanduser(args.mountpoint)

    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint, exist_ok=True)

    # Check if already mounted
    try:
        result = subprocess.run(['mount'], capture_output=True, text=True)
        if mountpoint in result.stdout:
            print(f"Warning: {mountpoint} appears to be already mounted")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1
    except Exception:
        pass

    print(f"Mounting Real-Debrid to: {mountpoint}")
    print("Press Ctrl+C to unmount\n")

    try:
        mount_realdebrid(api_token, mountpoint, foreground=not args.daemon)
    except KeyboardInterrupt:
        print("\nUnmounting...")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


def unmount_command(args):
    """Unmount Real-Debrid filesystem"""
    mountpoint = os.path.expanduser(args.mountpoint)

    try:
        subprocess.run(['fusermount', '-u', mountpoint], check=True)
        print(f"Unmounted: {mountpoint}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error unmounting: {e}")
        return 1


def info_command(args):
    """Display account information"""
    config = load_config()

    api_token = args.token or config.get("api_token")

    if not api_token:
        print("Error: No API token configured.")
        print("Run 'rdmount.py setup' first")
        return 1

    try:
        api = RealDebridAPI(api_token)
        user_info = api.get_user_info()

        print("Real-Debrid Account Information:")
        print(f"  Username: {user_info.get('username', 'Unknown')}")
        print(f"  Email: {user_info.get('email', 'Unknown')}")
        print(f"  Account type: {user_info.get('type', 'Unknown')}")
        print(f"  Premium until: {user_info.get('expiration', 'Unknown')}")
        print(f"  Points: {user_info.get('points', 0)}")

        # List torrents
        torrents = api.get_torrents()
        print(f"\nActive torrents: {len(torrents)}")

        if torrents:
            print("\nRecent torrents:")
            for torrent in torrents[:5]:
                status = torrent.get('status', 'unknown')
                filename = torrent.get('filename', 'Unknown')
                print(f"  [{status}] {filename}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Mount Real-Debrid as a virtual drive for Jellyfin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup API token
  %(prog)s setup

  # Mount to default location
  %(prog)s mount ~/realdebrid

  # Mount in background
  %(prog)s mount ~/realdebrid --daemon

  # Unmount
  %(prog)s unmount ~/realdebrid

  # Show account info
  %(prog)s info
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Configure Real-Debrid API token')
    setup_parser.add_argument('--token', help='API token (if not provided, will prompt)')
    setup_parser.set_defaults(func=setup_command)

    # Mount command
    mount_parser = subparsers.add_parser('mount', help='Mount Real-Debrid filesystem')
    mount_parser.add_argument('mountpoint', help='Directory to mount at')
    mount_parser.add_argument('--token', help='Override configured API token')
    mount_parser.add_argument('--daemon', action='store_true', help='Run in background')
    mount_parser.set_defaults(func=mount_command)

    # Unmount command
    unmount_parser = subparsers.add_parser('unmount', help='Unmount filesystem')
    unmount_parser.add_argument('mountpoint', help='Directory to unmount')
    unmount_parser.set_defaults(func=unmount_command)

    # Info command
    info_parser = subparsers.add_parser('info', help='Display account information')
    info_parser.add_argument('--token', help='Override configured API token')
    info_parser.set_defaults(func=info_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
