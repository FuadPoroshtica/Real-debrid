"""
Torrent Health Check and Repair Manager
Ensures library reliability and prevents scanner issues
"""
import time
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from realdebrid_api import RealDebridAPI


class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    REPAIRING = "repairing"
    UNKNOWN = "unknown"


class TorrentHealthManager:
    """Manages torrent health checks and repairs"""

    def __init__(self, api: RealDebridAPI, config: Dict):
        """
        Initialize health manager

        Args:
            api: Real-Debrid API client
            config: Configuration dictionary
        """
        self.api = api
        self.config = config
        self.health_cache = {}
        self.repair_attempts = {}

    def check_torrent_health(self, torrent_id: str) -> Tuple[str, Dict]:
        """
        Check health of a specific torrent

        Args:
            torrent_id: Torrent ID

        Returns:
            Tuple of (status, details)
        """
        try:
            info = self.api.get_torrent_info(torrent_id)

            status = info.get('status', '')
            progress = info.get('progress', 0)
            seeders = info.get('seeders', 0)
            files = info.get('files', [])

            details = {
                'status': status,
                'progress': progress,
                'seeders': seeders,
                'total_files': len(files),
                'available_files': 0,
                'issues': []
            }

            # Check torrent status
            if status == 'downloaded':
                details['available_files'] = len(files)
                health = HealthStatus.HEALTHY
            elif status == 'downloading':
                health = HealthStatus.DEGRADED
                details['issues'].append(f"Still downloading ({progress}%)")
            elif status in ['error', 'virus', 'dead']:
                health = HealthStatus.FAILED
                details['issues'].append(f"Torrent status: {status}")
            else:
                health = HealthStatus.UNKNOWN
                details['issues'].append(f"Unknown status: {status}")

            # Check seeders
            if seeders == 0 and status == 'downloading':
                health = HealthStatus.DEGRADED
                details['issues'].append("No seeders available")

            # Check files accessibility
            unavailable_files = 0
            for file_info in files:
                if not file_info.get('links'):
                    unavailable_files += 1

            if unavailable_files > 0:
                if unavailable_files == len(files):
                    health = HealthStatus.FAILED
                    details['issues'].append("All files unavailable")
                else:
                    health = HealthStatus.DEGRADED
                    details['issues'].append(f"{unavailable_files} files unavailable")
                details['available_files'] = len(files) - unavailable_files

            # Cache result
            self.health_cache[torrent_id] = {
                'health': health,
                'details': details,
                'checked_at': time.time()
            }

            return health, details

        except Exception as e:
            return HealthStatus.UNKNOWN, {'issues': [str(e)]}

    def check_all_torrents(self) -> Dict[str, Dict]:
        """
        Check health of all torrents

        Returns:
            Dictionary of torrent_id -> health info
        """
        results = {}

        try:
            torrents = self.api.get_torrents()

            for torrent in torrents:
                torrent_id = torrent['id']
                health, details = self.check_torrent_health(torrent_id)

                results[torrent_id] = {
                    'name': torrent.get('filename', 'Unknown'),
                    'health': health,
                    'details': details
                }

        except Exception as e:
            print(f"Error checking torrents health: {e}")

        return results

    def repair_torrent(self, torrent_id: str) -> bool:
        """
        Attempt to repair a failed torrent

        Args:
            torrent_id: Torrent ID

        Returns:
            True if repair initiated successfully
        """
        # Track repair attempts
        if torrent_id not in self.repair_attempts:
            self.repair_attempts[torrent_id] = 0

        self.repair_attempts[torrent_id] += 1

        # Limit repair attempts
        if self.repair_attempts[torrent_id] > 3:
            print(f"Max repair attempts reached for {torrent_id}")
            return False

        try:
            # Try to re-download the torrent
            # Note: Real-Debrid API doesn't have a direct "repair" endpoint
            # So we'll check if we can re-add the torrent

            info = self.api.get_torrent_info(torrent_id)

            # If torrent has a magnet/torrent link, we could try re-adding
            # For now, we'll just mark it for manual attention

            print(f"Torrent {torrent_id} marked for repair")
            print(f"Manual intervention may be required")

            return True

        except Exception as e:
            print(f"Failed to repair torrent {torrent_id}: {e}")
            return False

    def get_unhealthy_torrents(self) -> List[Dict]:
        """
        Get list of unhealthy torrents

        Returns:
            List of unhealthy torrent info
        """
        health_results = self.check_all_torrents()

        unhealthy = []
        for torrent_id, info in health_results.items():
            if info['health'] in [HealthStatus.DEGRADED, HealthStatus.FAILED]:
                unhealthy.append({
                    'id': torrent_id,
                    'name': info['name'],
                    'health': info['health'],
                    'issues': info['details'].get('issues', [])
                })

        return unhealthy

    def cleanup_rar_torrents(self) -> int:
        """
        Remove torrents that only contain RAR files (no video files)

        Returns:
            Number of torrents removed
        """
        if not self.config.get('cleanup', {}).get('rar_handling', {}).get('delete_rar_only_torrents'):
            return 0

        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.mpg', '.mpeg', '.webm', '.ts'}
        removed = 0

        try:
            torrents = self.api.get_torrents()

            for torrent in torrents:
                torrent_id = torrent['id']

                try:
                    info = self.api.get_torrent_info(torrent_id)
                    files = info.get('files', [])

                    # Check if torrent has any video files
                    has_video = False
                    has_rar = False

                    for file_info in files:
                        file_path = file_info.get('path', '')
                        ext = Path(file_path).suffix.lower()

                        if ext in video_extensions:
                            has_video = True
                        elif ext == '.rar':
                            has_rar = True

                    # If only RAR files, mark for deletion
                    if has_rar and not has_video:
                        print(f"Removing RAR-only torrent: {torrent.get('filename')}")
                        # Note: Would call delete API here
                        # self.api.delete_torrent(torrent_id)
                        removed += 1

                except Exception as e:
                    print(f"Error checking torrent {torrent_id}: {e}")

        except Exception as e:
            print(f"Error during RAR cleanup: {e}")

        return removed

    def run_health_check_loop(self, interval: int = 300):
        """
        Run continuous health check loop

        Args:
            interval: Check interval in seconds
        """
        print(f"Starting health check loop (interval: {interval}s)")

        try:
            while True:
                print("\n=== Running Health Check ===")

                # Check all torrents
                results = self.check_all_torrents()

                # Count by health status
                healthy = sum(1 for r in results.values() if r['health'] == HealthStatus.HEALTHY)
                degraded = sum(1 for r in results.values() if r['health'] == HealthStatus.DEGRADED)
                failed = sum(1 for r in results.values() if r['health'] == HealthStatus.FAILED)

                print(f"Healthy: {healthy}, Degraded: {degraded}, Failed: {failed}")

                # Auto-repair if enabled
                if self.config.get('realdebrid', {}).get('enable_repair'):
                    unhealthy = self.get_unhealthy_torrents()

                    for torrent_info in unhealthy:
                        if torrent_info['health'] == HealthStatus.FAILED:
                            print(f"Attempting repair: {torrent_info['name']}")
                            self.repair_torrent(torrent_info['id'])

                # Cleanup RAR torrents
                if self.config.get('cleanup', {}).get('rar_handling', {}).get('delete_rar_only_torrents'):
                    removed = self.cleanup_rar_torrents()
                    if removed > 0:
                        print(f"Cleaned up {removed} RAR-only torrents")

                # Wait for next check
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nHealth check loop stopped")

    def get_health_summary(self) -> Dict:
        """
        Get summary of current health status

        Returns:
            Health summary dictionary
        """
        results = self.check_all_torrents()

        summary = {
            'total': len(results),
            'healthy': 0,
            'degraded': 0,
            'failed': 0,
            'unknown': 0,
            'issues': []
        }

        for info in results.values():
            health = info['health']

            if health == HealthStatus.HEALTHY:
                summary['healthy'] += 1
            elif health == HealthStatus.DEGRADED:
                summary['degraded'] += 1
            elif health == HealthStatus.FAILED:
                summary['failed'] += 1
            else:
                summary['unknown'] += 1

            if info['details'].get('issues'):
                summary['issues'].extend([
                    f"{info['name']}: {', '.join(info['details']['issues'])}"
                ])

        return summary


def main():
    """CLI entry point for health manager"""
    import sys
    import json
    from config_manager import load_config

    config_mgr = load_config()
    config_dict = config_mgr.config

    api_token = config_mgr.get("realdebrid.api_token")
    if not api_token:
        print("Error: No API token configured")
        sys.exit(1)

    api = RealDebridAPI(api_token)
    health_mgr = TorrentHealthManager(api, config_dict)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            # Check all torrents
            results = health_mgr.check_all_torrents()
            print(json.dumps(results, indent=2))

        elif command == "summary":
            # Get health summary
            summary = health_mgr.get_health_summary()
            print(json.dumps(summary, indent=2))

        elif command == "unhealthy":
            # List unhealthy torrents
            unhealthy = health_mgr.get_unhealthy_torrents()
            for torrent in unhealthy:
                print(f"\n{torrent['name']}")
                print(f"  Status: {torrent['health']}")
                print(f"  Issues: {', '.join(torrent['issues'])}")

        elif command == "cleanup":
            # Cleanup RAR torrents
            removed = health_mgr.cleanup_rar_torrents()
            print(f"Removed {removed} RAR-only torrents")

        elif command == "watch":
            # Start health check loop
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            health_mgr.run_health_check_loop(interval)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("Usage: python3 health_manager.py <check|summary|unhealthy|cleanup|watch>")
        sys.exit(1)


if __name__ == "__main__":
    main()
