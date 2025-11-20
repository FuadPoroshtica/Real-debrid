"""
Advanced Configuration Manager
Handles YAML configuration with validation and defaults
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConfigManager:
    """Advanced configuration management inspired by zurg"""

    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".config" / "rdmount" / "config.yml",
        Path.home() / ".config" / "rdmount" / "config_advanced.yml",
        Path("config.yml"),
        Path("config_advanced.yml"),
    ]

    DEFAULT_CONFIG = {
        "version": "v1",
        "realdebrid": {
            "api_token": "",
            "check_interval": 60,
            "enable_health_checks": True,
            "enable_repair": True,
            "auto_delete_rar_torrents": True,
            "concurrent_workers": 5,
            "api_timeout": 30,
            "max_retries": 3,
        },
        "mount": {
            "mountpoint": str(Path.home() / "realdebrid"),
            "enable_webdav": False,
            "webdav": {
                "host": "0.0.0.0",
                "port": 9999,
                "username": "",
                "password": "",
            },
            "fuse_options": {
                "allow_other": True,
                "default_permissions": False,
                "auto_cache": True,
                "kernel_cache": False,
                "entry_timeout": 30,
                "attr_timeout": 30,
                "negative_timeout": 5,
            },
            "vfs_cache": {
                "enabled": True,
                "mode": "full",
                "dir_cache_time": 10,
                "max_age": 3600,
                "poll_interval": 60,
            },
        },
        "media": {
            "movies_path": str(Path.home() / "media" / "movies"),
            "tv_path": str(Path.home() / "media" / "tv"),
            "enable_resolver": True,
            "resolver_watch": False,
            "resolver_watch_interval": 60,
        },
        "directories": [],
        "hooks": {
            "on_library_update": {"enabled": False, "commands": []},
            "on_torrent_complete": {"enabled": False, "commands": []},
            "on_health_check_fail": {"enabled": False, "commands": []},
        },
        "cleanup": {
            "enabled": True,
            "remove_old_torrents_days": 0,
            "remove_incomplete": False,
            "remove_empty_dirs": True,
            "rar_handling": {
                "auto_extract": False,
                "delete_after_extract": False,
                "delete_rar_only_torrents": True,
            },
        },
        "performance": {
            "enable_cache": True,
            "cache_size": 512,
            "cache_ttl": 300,
            "prefetch_metadata": True,
            "parallel_downloads": 3,
            "read_ahead_kb": 4096,
            "use_http2": True,
        },
        "logging": {
            "level": "info",
            "file": str(Path.home() / ".config" / "rdmount" / "rdmount.log"),
            "rotation": {"enabled": True, "max_size_mb": 10, "max_files": 5},
            "debug": False,
        },
        "integrations": {
            "plex": {"enabled": False, "url": "", "token": "", "library_sections": []},
            "jellyfin": {"enabled": False, "url": "", "api_key": ""},
            "radarr": {"enabled": False, "url": "", "api_key": ""},
            "sonarr": {"enabled": False, "url": "", "api_key": ""},
        },
        "experimental": {
            "transcoding_proxy": False,
            "direct_play_optimization": True,
            "smart_caching": False,
            "bandwidth_limit": 0,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config file (auto-detected if None)
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()

    def _find_config(self) -> Optional[Path]:
        """Find config file in default locations"""
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path
        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if not self.config_path or not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r') as f:
                loaded = yaml.safe_load(f) or {}

            # Merge with defaults
            return self._deep_merge(self.DEFAULT_CONFIG.copy(), loaded)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def save(self, path: Optional[Path] = None):
        """Save configuration to file"""
        save_path = path or self.config_path

        if not save_path:
            save_path = self.DEFAULT_CONFIG_PATHS[0]

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        self.config_path = save_path

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-separated path

        Args:
            key_path: Dot-separated key path (e.g., "realdebrid.api_token")
            default: Default value if key not found

        Returns:
            Config value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set config value by dot-separated path

        Args:
            key_path: Dot-separated key path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def validate(self) -> List[str]:
        """
        Validate configuration

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        api_token = self.get("realdebrid.api_token")
        if not api_token:
            errors.append("Real-Debrid API token is required")

        mountpoint = self.get("mount.mountpoint")
        if not mountpoint:
            errors.append("Mount point is required")

        # Validate WebDAV config if enabled
        if self.get("mount.enable_webdav"):
            port = self.get("mount.webdav.port")
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("WebDAV port must be between 1-65535")

        # Validate paths
        for path_key in ["media.movies_path", "media.tv_path"]:
            path = self.get(path_key)
            if path:
                expanded = os.path.expanduser(path)
                parent = Path(expanded).parent
                if not parent.exists():
                    errors.append(f"Parent directory for {path_key} does not exist: {parent}")

        # Validate directories config
        directories = self.get("directories", [])
        for idx, dir_config in enumerate(directories):
            if not isinstance(dir_config, dict):
                errors.append(f"Directory config {idx} must be a dictionary")
                continue

            if "path" not in dir_config:
                errors.append(f"Directory config {idx} missing 'path' field")

            # Validate regex patterns
            filters = dir_config.get("filters", {})
            for regex_list_key in ["include_regex", "exclude_regex"]:
                regex_list = filters.get(regex_list_key, [])
                for regex_pattern in regex_list:
                    try:
                        re.compile(regex_pattern)
                    except re.error as e:
                        errors.append(f"Invalid regex in directory {idx} {regex_list_key}: {e}")

        return errors

    def get_directory_filters(self, directory_path: str) -> Optional[Dict]:
        """Get filters for a specific directory path"""
        directories = self.get("directories", [])
        for dir_config in directories:
            if dir_config.get("path") == directory_path:
                return dir_config.get("filters", {})
        return None

    def get_hooks(self, hook_type: str) -> List[Dict]:
        """Get hooks for a specific event type"""
        hook_config = self.get(f"hooks.{hook_type}", {})
        if hook_config.get("enabled"):
            return hook_config.get("commands", [])
        return []

    def is_feature_enabled(self, feature_path: str) -> bool:
        """Check if a feature is enabled"""
        return bool(self.get(feature_path, False))

    def expand_path(self, path: str) -> str:
        """Expand path with ~ and environment variables"""
        return os.path.expanduser(os.path.expandvars(path))

    def get_realdebrid_config(self) -> Dict:
        """Get Real-Debrid configuration"""
        return self.get("realdebrid", {})

    def get_mount_config(self) -> Dict:
        """Get mount configuration"""
        return self.get("mount", {})

    def get_media_config(self) -> Dict:
        """Get media configuration"""
        return self.get("media", {})

    def get_performance_config(self) -> Dict:
        """Get performance configuration"""
        return self.get("performance", {})

    def __repr__(self) -> str:
        return f"ConfigManager(config_path={self.config_path})"


# Convenience function
def load_config(path: Optional[Path] = None) -> ConfigManager:
    """Load configuration from file or defaults"""
    return ConfigManager(path)
