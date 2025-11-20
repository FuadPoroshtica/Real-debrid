"""
WebDAV Server for Real-Debrid
Provides rclone-compatible WebDAV interface
"""
import os
import sys
from pathlib import Path
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from cheroot import wsgi


class RealDebridWebDAVProvider(FilesystemProvider):
    """Custom WebDAV provider for Real-Debrid mount"""

    def __init__(self, root_path, readonly=True):
        """
        Initialize WebDAV provider

        Args:
            root_path: Mount point path
            readonly: Read-only mode (default: True)
        """
        super().__init__(root_path, readonly=readonly)
        self.root_path = Path(root_path)

    def get_resource_inst(self, path, environ):
        """Get resource instance with caching"""
        return super().get_resource_inst(path, environ)


def start_webdav_server(mount_path: str, host: str = "0.0.0.0", port: int = 9999,
                       username: str = "", password: str = "", verbose: bool = False):
    """
    Start WebDAV server

    Args:
        mount_path: Path to Real-Debrid mount
        host: Server host
        port: Server port
        username: Optional authentication username
        password: Optional authentication password
        verbose: Enable verbose logging
    """
    if not os.path.exists(mount_path):
        print(f"Error: Mount path does not exist: {mount_path}")
        return False

    # Configure WebDAV provider
    provider = RealDebridWebDAVProvider(mount_path, readonly=True)

    # WebDAV configuration
    config = {
        "host": host,
        "port": port,
        "provider_mapping": {
            "/": provider
        },
        "verbose": 1 if verbose else 0,
        "enable_loggers": [],
        "property_manager": True,
        "lock_manager": True,
    }

    # Add authentication if credentials provided
    if username and password:
        config["simple_dc"] = {
            "user_mapping": {
                "/": {
                    username: {
                        "password": password,
                        "description": "Real-Debrid WebDAV User",
                        "roles": []
                    }
                }
            }
        }
        config["accept_basic"] = True
        config["accept_digest"] = True
        config["default_to_digest"] = True

    print(f"Starting WebDAV server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Mount: {mount_path}")

    if username:
        print(f"  Auth: Enabled (user: {username})")
        print(f"\nWebDAV URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/")
        print(f"Username: {username}")
        print(f"Password: {password}")
    else:
        print(f"  Auth: Disabled")
        print(f"\nWebDAV URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/")

    print(f"\nFor rclone, add this to your rclone.conf:")
    print(f"[realdebrid]")
    print(f"type = webdav")
    print(f"url = http://{host if host != '0.0.0.0' else 'localhost'}:{port}/")
    print(f"vendor = other")

    if username:
        print(f"user = {username}")
        print(f"pass = {password}")

    print(f"\nThen mount with: rclone mount realdebrid: /mnt/realdebrid --allow-other")
    print()

    try:
        # Create WSGI app
        app = WsgiDAVApp(config)

        # Create server
        server = wsgi.Server(
            (host, port),
            app,
            server_name=f"RealDebrid-WebDAV/{config.get('port')}"
        )

        print(f"✓ WebDAV server started successfully")
        print("Press Ctrl+C to stop\n")

        # Start server
        server.start()

    except KeyboardInterrupt:
        print("\n\nStopping WebDAV server...")
        return True
    except Exception as e:
        print(f"\n✗ Error starting WebDAV server: {e}")
        return False


def main():
    """CLI entry point for WebDAV server"""
    import argparse
    from config_manager import load_config

    parser = argparse.ArgumentParser(description="Real-Debrid WebDAV Server")
    parser.add_argument("--mount", help="Mount point path")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9999, help="Server port (default: 9999)")
    parser.add_argument("--username", help="Authentication username")
    parser.add_argument("--password", help="Authentication password")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Load config
    config_mgr = load_config()

    # Get mount path
    mount_path = args.mount or config_mgr.get("mount.mountpoint")

    if not mount_path:
        print("Error: No mount path specified. Use --mount or configure in config.yml")
        sys.exit(1)

    mount_path = os.path.expanduser(mount_path)

    # Get WebDAV config
    webdav_config = config_mgr.get("mount.webdav", {})

    host = args.host or webdav_config.get("host", "0.0.0.0")
    port = args.port or webdav_config.get("port", 9999)
    username = args.username or webdav_config.get("username", "")
    password = args.password or webdav_config.get("password", "")

    # Start server
    success = start_webdav_server(
        mount_path,
        host=host,
        port=port,
        username=username,
        password=password,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
