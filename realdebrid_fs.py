"""
Real-Debrid FUSE Filesystem
Mount Real-Debrid torrents as a virtual filesystem
"""
import os
import stat
import errno
import time
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from typing import Dict, List
import requests
from realdebrid_api import RealDebridAPI


class RealDebridFS(LoggingMixIn, Operations):
    """FUSE filesystem for Real-Debrid"""

    def __init__(self, api_token: str):
        """
        Initialize filesystem

        Args:
            api_token: Real-Debrid API token
        """
        self.api = RealDebridAPI(api_token)
        self.fd_counter = 0
        self.open_files = {}  # fd -> file info
        self._attr_cache = {}
        self._attr_cache_time = {}
        self._cache_ttl = 30

    def _get_path_parts(self, path: str) -> List[str]:
        """Split path into parts, removing empty strings"""
        return [p for p in path.split('/') if p]

    def _get_torrents_structure(self) -> Dict:
        """Get cached torrents structure"""
        cache_key = "torrents_structure"
        current_time = time.time()

        if cache_key in self._attr_cache:
            if current_time - self._attr_cache_time.get(cache_key, 0) < self._cache_ttl:
                return self._attr_cache[cache_key]

        torrents = self.api.get_torrents()
        structure = {}

        for torrent in torrents:
            if torrent.get("status") != "downloaded":
                continue

            torrent_id = torrent["id"]
            torrent_name = torrent.get("filename", f"torrent_{torrent_id}")

            # Sanitize filename
            torrent_name = "".join(c for c in torrent_name if c.isalnum() or c in (' ', '-', '_', '.'))

            structure[torrent_name] = {
                "id": torrent_id,
                "type": "dir",
                "files": {}
            }

            # Get torrent info for files
            try:
                info = self.api.get_torrent_info(torrent_id)
                for file_info in info.get("files", []):
                    file_path = file_info.get("path", "")
                    if file_path.startswith("/"):
                        file_path = file_path[1:]

                    structure[torrent_name]["files"][file_path] = {
                        "id": file_info["id"],
                        "size": file_info.get("bytes", 0),
                        "link": file_info.get("links", [None])[0],
                        "type": "file"
                    }
            except Exception as e:
                print(f"Error getting torrent info for {torrent_id}: {e}")

        self._attr_cache[cache_key] = structure
        self._attr_cache_time[cache_key] = current_time
        return structure

    def _resolve_path(self, path: str):
        """Resolve path to file/directory info"""
        if path == "/":
            return {"type": "root"}

        parts = self._get_path_parts(path)
        structure = self._get_torrents_structure()

        if len(parts) == 1:
            # Torrent directory
            torrent_name = parts[0]
            if torrent_name in structure:
                return structure[torrent_name]
            return None

        if len(parts) >= 2:
            # File within torrent
            torrent_name = parts[0]
            file_path = "/".join(parts[1:])

            if torrent_name in structure:
                files = structure[torrent_name]["files"]
                if file_path in files:
                    return files[file_path]

        return None

    def getattr(self, path, fh=None):
        """Get file attributes"""
        resolved = self._resolve_path(path)

        if resolved is None:
            raise FuseOSError(errno.ENOENT)

        # Default timestamps
        now = time.time()

        if resolved["type"] == "root" or resolved["type"] == "dir":
            return {
                "st_mode": stat.S_IFDIR | 0o755,
                "st_nlink": 2,
                "st_size": 4096,
                "st_ctime": now,
                "st_mtime": now,
                "st_atime": now,
            }
        else:
            return {
                "st_mode": stat.S_IFREG | 0o444,
                "st_nlink": 1,
                "st_size": resolved.get("size", 0),
                "st_ctime": now,
                "st_mtime": now,
                "st_atime": now,
            }

    def readdir(self, path, fh):
        """Read directory contents"""
        resolved = self._resolve_path(path)

        if resolved is None:
            raise FuseOSError(errno.ENOENT)

        entries = [".", ".."]

        if resolved["type"] == "root":
            structure = self._get_torrents_structure()
            entries.extend(structure.keys())
        elif resolved["type"] == "dir":
            # List files in torrent
            files = resolved.get("files", {})
            # Get unique directory names and file names at this level
            for file_path in files.keys():
                parts = file_path.split("/")
                if len(parts) > 0:
                    entries.append(parts[0])

        return list(set(entries))

    def open(self, path, flags):
        """Open file"""
        resolved = self._resolve_path(path)

        if resolved is None or resolved["type"] != "file":
            raise FuseOSError(errno.ENOENT)

        self.fd_counter += 1
        fd = self.fd_counter

        self.open_files[fd] = {
            "path": path,
            "info": resolved,
            "session": None,
            "download_url": None
        }

        return fd

    def read(self, path, size, offset, fh):
        """Read file data"""
        if fh not in self.open_files:
            raise FuseOSError(errno.EBADF)

        file_info = self.open_files[fh]["info"]
        link = file_info.get("link")

        if not link:
            raise FuseOSError(errno.EIO)

        # Get download URL if not cached
        if not self.open_files[fh]["download_url"]:
            try:
                download_url = self.api.get_download_link(link)
                self.open_files[fh]["download_url"] = download_url
            except Exception as e:
                print(f"Error getting download link: {e}")
                raise FuseOSError(errno.EIO)

        download_url = self.open_files[fh]["download_url"]

        # Stream file content using range request
        try:
            headers = {
                "Range": f"bytes={offset}-{offset + size - 1}"
            }
            response = requests.get(download_url, headers=headers, stream=True)

            if response.status_code in (200, 206):
                return response.content
            else:
                raise FuseOSError(errno.EIO)
        except Exception as e:
            print(f"Error reading file: {e}")
            raise FuseOSError(errno.EIO)

    def release(self, path, fh):
        """Close file"""
        if fh in self.open_files:
            del self.open_files[fh]
        return 0

    # Read-only filesystem methods
    def chmod(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(errno.EROFS)

    def create(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def rename(self, old, new):
        raise FuseOSError(errno.EROFS)

    def rmdir(self, path):
        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def unlink(self, path):
        raise FuseOSError(errno.EROFS)

    def write(self, path, data, offset, fh):
        raise FuseOSError(errno.EROFS)


def mount_realdebrid(api_token: str, mountpoint: str, foreground: bool = False):
    """
    Mount Real-Debrid filesystem

    Args:
        api_token: Real-Debrid API token
        mountpoint: Directory to mount at
        foreground: Run in foreground (default: False)
    """
    # Verify API token
    api = RealDebridAPI(api_token)
    try:
        user_info = api.get_user_info()
        print(f"Authenticated as: {user_info.get('username', 'Unknown')}")
    except Exception as e:
        print(f"Error: Failed to authenticate with Real-Debrid API: {e}")
        return

    # Create mountpoint if it doesn't exist
    os.makedirs(mountpoint, exist_ok=True)

    print(f"Mounting Real-Debrid at: {mountpoint}")

    # Mount filesystem
    fs = RealDebridFS(api_token)
    FUSE(fs, mountpoint, nothreads=True, foreground=foreground, ro=True, allow_other=True)
