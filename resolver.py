"""
Real-Debrid Resolver
Creates symlinks from Real-Debrid content for *arr stack compatibility
Works with: Radarr, Sonarr, Jellyseerr, Prowlarr, Jellyfin
"""
import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, List
from realdebrid_api import RealDebridAPI


class MediaResolver:
    """Resolves Real-Debrid torrents to organized media libraries"""

    def __init__(self, api_token: str, mount_path: str, media_paths: Dict[str, str]):
        """
        Initialize resolver

        Args:
            api_token: Real-Debrid API token
            mount_path: Path where Real-Debrid is mounted
            media_paths: Dict with 'movies' and 'tv' paths for symlinks
        """
        self.api = RealDebridAPI(api_token)
        self.mount_path = Path(mount_path)
        self.movies_path = Path(media_paths.get('movies', '~/media/movies')).expanduser()
        self.tv_path = Path(media_paths.get('tv', '~/media/tv')).expanduser()

        # Create directories
        self.movies_path.mkdir(parents=True, exist_ok=True)
        self.tv_path.mkdir(parents=True, exist_ok=True)

        # Track processed torrents
        self.processed = set()

    def is_video_file(self, filename: str) -> bool:
        """Check if file is a video"""
        video_extensions = {
            '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.m4v', '.mpg', '.mpeg', '.webm', '.ts'
        }
        return Path(filename).suffix.lower() in video_extensions

    def detect_media_type(self, name: str) -> str:
        """
        Detect if content is movie or TV show

        Args:
            name: Torrent or file name

        Returns:
            'movie' or 'tv'
        """
        # TV show patterns
        tv_patterns = [
            r'[Ss]\d{2}[Ee]\d{2}',  # S01E01
            r'\d{1,2}x\d{2}',        # 1x01
            r'Season\s*\d+',         # Season 1
            r'Complete\s*Series',    # Complete Series
        ]

        for pattern in tv_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return 'tv'

        return 'movie'

    def parse_tv_info(self, name: str) -> Optional[Dict]:
        """
        Parse TV show information from filename

        Args:
            name: Filename or torrent name

        Returns:
            Dict with show_name, season, episode or None
        """
        # Try S01E01 format
        match = re.search(r'(.+?)[.\s]+[Ss](\d{2})[Ee](\d{2})', name)
        if match:
            return {
                'show_name': self.clean_name(match.group(1)),
                'season': int(match.group(2)),
                'episode': int(match.group(3))
            }

        # Try 1x01 format
        match = re.search(r'(.+?)[.\s]+(\d{1,2})x(\d{2})', name)
        if match:
            return {
                'show_name': self.clean_name(match.group(1)),
                'season': int(match.group(2)),
                'episode': int(match.group(3))
            }

        # Try Season X format
        match = re.search(r'(.+?)[.\s]+Season[.\s]+(\d+)', name, re.IGNORECASE)
        if match:
            return {
                'show_name': self.clean_name(match.group(1)),
                'season': int(match.group(2)),
                'episode': None  # Full season
            }

        return None

    def clean_name(self, name: str) -> str:
        """Clean up media name"""
        # Remove common patterns
        name = re.sub(r'\[.*?\]', '', name)  # Remove [tags]
        name = re.sub(r'\(.*?\)', '', name)  # Remove (tags)
        name = re.sub(r'\d{4}p', '', name, re.IGNORECASE)  # Remove resolution
        name = re.sub(r'BluRay|BRRip|WEB-DL|WEBRip|HDTV', '', name, re.IGNORECASE)
        name = re.sub(r'x264|x265|H\.?264|H\.?265|HEVC', '', name, re.IGNORECASE)

        # Replace dots and underscores with spaces
        name = name.replace('.', ' ').replace('_', ' ')

        # Remove extra spaces
        name = ' '.join(name.split())

        return name.strip()

    def extract_year(self, name: str) -> Optional[int]:
        """Extract year from filename"""
        match = re.search(r'[(\[]?(19\d{2}|20\d{2})[)\]]?', name)
        if match:
            return int(match.group(1))
        return None

    def create_movie_symlink(self, source_path: Path, torrent_name: str) -> bool:
        """
        Create symlink for movie file

        Args:
            source_path: Path to source file in mount
            torrent_name: Name of torrent for organizing

        Returns:
            True if successful
        """
        try:
            # Clean movie name
            movie_name = self.clean_name(source_path.stem)
            year = self.extract_year(torrent_name)

            # Create folder name
            if year:
                folder_name = f"{movie_name} ({year})"
            else:
                folder_name = movie_name

            # Sanitize folder name
            folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_', '(', ')'))

            # Create movie folder
            movie_folder = self.movies_path / folder_name
            movie_folder.mkdir(parents=True, exist_ok=True)

            # Create symlink
            link_path = movie_folder / source_path.name
            if link_path.exists() or link_path.is_symlink():
                link_path.unlink()

            link_path.symlink_to(source_path.absolute())

            print(f"✅ Movie: {folder_name}/{source_path.name}")
            return True

        except Exception as e:
            print(f"❌ Failed to create movie symlink: {e}")
            return False

    def create_tv_symlink(self, source_path: Path, torrent_name: str) -> bool:
        """
        Create symlink for TV show file

        Args:
            source_path: Path to source file in mount
            torrent_name: Name of torrent for organizing

        Returns:
            True if successful
        """
        try:
            # Parse TV info
            tv_info = self.parse_tv_info(source_path.name) or self.parse_tv_info(torrent_name)

            if not tv_info:
                print(f"⚠️  Could not parse TV info from: {source_path.name}")
                return False

            show_name = tv_info['show_name']
            season = tv_info['season']

            # Sanitize show name
            show_name = "".join(c for c in show_name if c.isalnum() or c in (' ', '-', '_'))

            # Create show folder structure
            show_folder = self.tv_path / show_name
            season_folder = show_folder / f"Season {season:02d}"
            season_folder.mkdir(parents=True, exist_ok=True)

            # Create symlink
            link_path = season_folder / source_path.name
            if link_path.exists() or link_path.is_symlink():
                link_path.unlink()

            link_path.symlink_to(source_path.absolute())

            print(f"✅ TV Show: {show_name}/Season {season:02d}/{source_path.name}")
            return True

        except Exception as e:
            print(f"❌ Failed to create TV symlink: {e}")
            return False

    def resolve_torrent(self, torrent_id: str, torrent_name: str) -> int:
        """
        Resolve a single torrent by creating symlinks

        Args:
            torrent_id: Torrent ID
            torrent_name: Torrent name

        Returns:
            Number of files resolved
        """
        if torrent_id in self.processed:
            return 0

        try:
            # Get torrent info
            info = self.api.get_torrent_info(torrent_id)
            files = info.get('files', [])

            if not files:
                return 0

            resolved_count = 0
            media_type = self.detect_media_type(torrent_name)

            # Find torrent folder in mount
            torrent_folder = None
            for item in self.mount_path.iterdir():
                if item.is_dir() and torrent_id in item.name:
                    torrent_folder = item
                    break

            if not torrent_folder:
                # Try matching by name
                clean_torrent_name = self.clean_name(torrent_name)
                for item in self.mount_path.iterdir():
                    if item.is_dir() and clean_torrent_name.lower() in item.name.lower():
                        torrent_folder = item
                        break

            if not torrent_folder:
                print(f"⚠️  Could not find mount folder for: {torrent_name}")
                return 0

            # Process files
            for file_info in files:
                file_path_str = file_info.get('path', '')
                if file_path_str.startswith('/'):
                    file_path_str = file_path_str[1:]

                # Find file in mount
                source_path = torrent_folder / file_path_str

                if not source_path.exists():
                    continue

                if not self.is_video_file(source_path.name):
                    continue

                # Create appropriate symlink
                if media_type == 'movie':
                    if self.create_movie_symlink(source_path, torrent_name):
                        resolved_count += 1
                else:
                    if self.create_tv_symlink(source_path, torrent_name):
                        resolved_count += 1

            self.processed.add(torrent_id)
            return resolved_count

        except Exception as e:
            print(f"❌ Error resolving torrent {torrent_name}: {e}")
            return 0

    def resolve_all(self) -> Dict[str, int]:
        """
        Resolve all downloaded torrents

        Returns:
            Dict with statistics
        """
        stats = {
            'total': 0,
            'movies': 0,
            'tv': 0,
            'errors': 0
        }

        try:
            torrents = self.api.get_torrents()

            for torrent in torrents:
                if torrent.get('status') != 'downloaded':
                    continue

                torrent_id = torrent['id']
                torrent_name = torrent.get('filename', f'torrent_{torrent_id}')

                print(f"\n📦 Processing: {torrent_name}")

                resolved = self.resolve_torrent(torrent_id, torrent_name)
                stats['total'] += resolved

                media_type = self.detect_media_type(torrent_name)
                if media_type == 'movie':
                    stats['movies'] += resolved
                else:
                    stats['tv'] += resolved

        except Exception as e:
            print(f"\n❌ Error during resolution: {e}")
            stats['errors'] += 1

        return stats

    def watch_and_resolve(self, interval: int = 60):
        """
        Watch for new torrents and resolve them

        Args:
            interval: Check interval in seconds
        """
        print(f"👀 Watching for new torrents (checking every {interval}s)")
        print("Press Ctrl+C to stop")
        print()

        try:
            while True:
                stats = self.resolve_all()

                if stats['total'] > 0:
                    print(f"\n✨ Resolved {stats['total']} files ({stats['movies']} movies, {stats['tv']} TV shows)")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping watcher")


def main():
    """CLI entry point for resolver"""
    import sys
    import json
    from pathlib import Path

    config_file = Path.home() / ".config" / "rdmount" / "config.json"

    if not config_file.exists():
        print("❌ Configuration not found. Run ./start.py setup first.")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    api_token = config.get('api_token')
    mount_path = config.get('mountpoint')

    if not api_token or not mount_path:
        print("❌ Invalid configuration. Run ./start.py setup.")
        sys.exit(1)

    # Get media paths from config or use defaults
    media_paths = {
        'movies': config.get('movies_path', str(Path.home() / 'media' / 'movies')),
        'tv': config.get('tv_path', str(Path.home() / 'media' / 'tv'))
    }

    resolver = MediaResolver(api_token, mount_path, media_paths)

    if len(sys.argv) > 1 and sys.argv[1] == 'watch':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        resolver.watch_and_resolve(interval)
    else:
        print("🔄 Resolving all torrents...\n")
        stats = resolver.resolve_all()
        print(f"\n✅ Complete! Resolved {stats['total']} files")
        print(f"   Movies: {stats['movies']}")
        print(f"   TV Shows: {stats['tv']}")


if __name__ == "__main__":
    main()
