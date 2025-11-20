"""
Library Update Hooks Manager
Execute custom commands on library events
"""
import os
import subprocess
import asyncio
from typing import Dict, List, Optional
from pathlib import Path


class HooksManager:
    """Manages library update hooks and event triggers"""

    def __init__(self, config: Dict):
        """
        Initialize hooks manager

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.hooks_config = config.get('hooks', {})

    def _expand_template(self, template: str, variables: Dict) -> str:
        """
        Expand template variables in command string

        Args:
            template: Template string with {{variable}} placeholders
            variables: Dictionary of variable values

        Returns:
            Expanded string
        """
        result = template

        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        return result

    def _execute_command(self, command: Dict, variables: Dict, async_exec: bool = False):
        """
        Execute a hook command

        Args:
            command: Command configuration
            variables: Template variables
            async_exec: Execute asynchronously
        """
        cmd_type = command.get('type', 'shell')

        if cmd_type == 'shell':
            shell_cmd = self._expand_template(command.get('command', ''), variables)

            if not shell_cmd:
                return

            try:
                if async_exec or command.get('async', False):
                    # Run in background
                    subprocess.Popen(
                        shell_cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"✓ Executed (async): {shell_cmd[:60]}...")
                else:
                    # Run synchronously
                    result = subprocess.run(
                        shell_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        print(f"✓ Executed: {shell_cmd[:60]}...")
                        if result.stdout:
                            print(f"  Output: {result.stdout[:100]}")
                    else:
                        print(f"✗ Failed: {shell_cmd[:60]}...")
                        if result.stderr:
                            print(f"  Error: {result.stderr[:100]}")

            except subprocess.TimeoutExpired:
                print(f"⏱ Timeout: {shell_cmd[:60]}...")
            except Exception as e:
                print(f"✗ Error executing command: {e}")

        elif cmd_type == 'script':
            script_path = self._expand_template(command.get('path', ''), variables)

            if not script_path or not Path(script_path).exists():
                print(f"✗ Script not found: {script_path}")
                return

            try:
                if async_exec or command.get('async', False):
                    subprocess.Popen([script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"✓ Executed script (async): {script_path}")
                else:
                    result = subprocess.run(
                        [script_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        print(f"✓ Executed script: {script_path}")
                    else:
                        print(f"✗ Script failed: {script_path}")
                        if result.stderr:
                            print(f"  Error: {result.stderr[:100]}")

            except Exception as e:
                print(f"✗ Error executing script: {e}")

        elif cmd_type == 'notification':
            message = self._expand_template(command.get('message', ''), variables)
            print(f"📢 Notification: {message}")

            # Could integrate with notification services here
            # (ntfy, pushover, etc.)

    def trigger_hook(self, hook_type: str, variables: Optional[Dict] = None):
        """
        Trigger hooks for a specific event type

        Args:
            hook_type: Type of hook (on_library_update, on_torrent_complete, etc.)
            variables: Template variables for commands
        """
        hook_config = self.hooks_config.get(hook_type, {})

        if not hook_config.get('enabled', False):
            return

        variables = variables or {}
        commands = hook_config.get('commands', [])

        if not commands:
            return

        print(f"\n🔔 Triggering {hook_type} hooks...")

        for command in commands:
            self._execute_command(command, variables)

    def on_library_update(self, changes: Optional[Dict] = None):
        """
        Trigger library update hooks

        Args:
            changes: Dictionary of changes (added, removed, modified)
        """
        variables = {
            'changes': str(changes or {}),
            'timestamp': str(int(asyncio.get_event_loop().time()) if hasattr(asyncio, 'get_event_loop') else 0)
        }

        self.trigger_hook('on_library_update', variables)

    def on_torrent_complete(self, torrent_id: str, torrent_name: str):
        """
        Trigger torrent complete hooks

        Args:
            torrent_id: Torrent ID
            torrent_name: Torrent name
        """
        variables = {
            'torrent_id': torrent_id,
            'torrent_name': torrent_name
        }

        self.trigger_hook('on_torrent_complete', variables)

    def on_health_check_fail(self, torrent_id: str, torrent_name: str, issues: List[str]):
        """
        Trigger health check failure hooks

        Args:
            torrent_id: Torrent ID
            torrent_name: Torrent name
            issues: List of issues found
        """
        variables = {
            'torrent_id': torrent_id,
            'torrent_name': torrent_name,
            'issues': ', '.join(issues)
        }

        self.trigger_hook('on_health_check_fail', variables)

    def trigger_plex_scan(self):
        """Trigger Plex library scan"""
        plex_config = self.config.get('integrations', {}).get('plex', {})

        if not plex_config.get('enabled'):
            return

        url = plex_config.get('url', '')
        token = plex_config.get('token', '')
        sections = plex_config.get('library_sections', [])

        if not url or not token:
            print("✗ Plex integration not configured")
            return

        if sections:
            # Scan specific sections
            for section_id in sections:
                scan_url = f"{url}/library/sections/{section_id}/refresh?X-Plex-Token={token}"
                subprocess.Popen(['curl', '-X', 'POST', scan_url], stdout=subprocess.DEVNULL)
                print(f"✓ Triggered Plex scan for section {section_id}")
        else:
            # Scan all sections
            scan_url = f"{url}/library/sections/all/refresh?X-Plex-Token={token}"
            subprocess.Popen(['curl', '-X', 'POST', scan_url], stdout=subprocess.DEVNULL)
            print("✓ Triggered Plex library scan")

    def trigger_jellyfin_scan(self):
        """Trigger Jellyfin library scan"""
        jellyfin_config = self.config.get('integrations', {}).get('jellyfin', {})

        if not jellyfin_config.get('enabled'):
            return

        url = jellyfin_config.get('url', '')
        api_key = jellyfin_config.get('api_key', '')

        if not url or not api_key:
            print("✗ Jellyfin integration not configured")
            return

        scan_url = f"{url}/Library/Refresh?api_key={api_key}"
        subprocess.Popen(['curl', '-X', 'POST', scan_url], stdout=subprocess.DEVNULL)
        print("✓ Triggered Jellyfin library scan")

    def trigger_arr_scan(self, arr_type: str):
        """
        Trigger Radarr/Sonarr scan

        Args:
            arr_type: 'radarr' or 'sonarr'
        """
        arr_config = self.config.get('integrations', {}).get(arr_type, {})

        if not arr_config.get('enabled'):
            return

        url = arr_config.get('url', '')
        api_key = arr_config.get('api_key', '')

        if not url or not api_key:
            print(f"✗ {arr_type.capitalize()} integration not configured")
            return

        # Trigger RescanDisk command
        command_url = f"{url}/api/v3/command"
        command_data = '{"name": "RescanFolders"}'

        subprocess.Popen(
            ['curl', '-X', 'POST', command_url, '-H', f'X-Api-Key: {api_key}', '-H', 'Content-Type: application/json', '-d', command_data],
            stdout=subprocess.DEVNULL
        )
        print(f"✓ Triggered {arr_type.capitalize()} rescan")


def main():
    """CLI entry point for hooks manager"""
    import sys
    from config_manager import load_config

    config_mgr = load_config()
    hooks_mgr = HooksManager(config_mgr.config)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test-library-update":
            hooks_mgr.on_library_update({'added': 5, 'removed': 0, 'modified': 2})

        elif command == "test-torrent-complete":
            hooks_mgr.on_torrent_complete("test123", "Test Movie (2024)")

        elif command == "plex-scan":
            hooks_mgr.trigger_plex_scan()

        elif command == "jellyfin-scan":
            hooks_mgr.trigger_jellyfin_scan()

        elif command == "radarr-scan":
            hooks_mgr.trigger_arr_scan('radarr')

        elif command == "sonarr-scan":
            hooks_mgr.trigger_arr_scan('sonarr')

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("Usage: python3 hooks_manager.py <test-library-update|test-torrent-complete|plex-scan|jellyfin-scan|radarr-scan|sonarr-scan>")
        sys.exit(1)


if __name__ == "__main__":
    main()
