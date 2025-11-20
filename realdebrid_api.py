"""
Real-Debrid API Client
Simple wrapper for Real-Debrid API interactions
"""
import requests
import time
from typing import List, Dict, Optional


class RealDebridAPI:
    """Client for interacting with Real-Debrid API"""

    BASE_URL = "https://api.real-debrid.com/rest/1.0"

    def __init__(self, api_token: str):
        """
        Initialize Real-Debrid API client

        Args:
            api_token: Real-Debrid API token
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}"
        })
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make GET request to API

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _get_cached(self, cache_key: str, fetch_func):
        """Get data from cache or fetch if expired"""
        current_time = time.time()

        if cache_key in self._cache:
            if current_time - self._cache_time[cache_key] < self._cache_ttl:
                return self._cache[cache_key]

        data = fetch_func()
        self._cache[cache_key] = data
        self._cache_time[cache_key] = current_time
        return data

    def get_user_info(self) -> Dict:
        """Get user account information"""
        return self._get("user")

    def get_torrents(self) -> List[Dict]:
        """
        Get list of user's torrents

        Returns:
            List of torrent information
        """
        return self._get_cached("torrents", lambda: self._get("torrents"))

    def get_torrent_info(self, torrent_id: str) -> Dict:
        """
        Get detailed information about a torrent

        Args:
            torrent_id: Torrent ID

        Returns:
            Torrent details including files
        """
        cache_key = f"torrent_{torrent_id}"
        return self._get_cached(cache_key, lambda: self._get(f"torrents/info/{torrent_id}"))

    def unrestrict_link(self, link: str) -> Dict:
        """
        Get unrestricted download link

        Args:
            link: Original link to unrestrict

        Returns:
            Unrestricted link information
        """
        url = f"{self.BASE_URL}/unrestrict/link"
        response = self.session.post(url, data={"link": link})
        response.raise_for_status()
        return response.json()

    def get_download_link(self, link: str) -> str:
        """
        Get direct download link

        Args:
            link: Link to unrestrict

        Returns:
            Direct download URL
        """
        result = self.unrestrict_link(link)
        return result.get("download", "")
