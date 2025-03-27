"""
Cache utility for storing API responses.
"""

import json
import os
import time
from typing import Any, Dict, Optional

from end_of_life_checker.utils.logger import debug, info


class Cache:
    """Simple file-based cache for API responses."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to ~/.cache/end-of-life-checker/
        """
        if cache_dir is None:
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(home_dir, ".cache", "end-of-life-checker")
        
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        # Convert key to a valid filename
        filename = key.replace("/", "_").replace(":", "_")
        
        # Remove .json extension if it's already in the key to avoid double extension
        if filename.endswith(".json"):
            filename = filename[:-5]
            
        return os.path.join(self.cache_dir, f"{filename}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            debug(f"Cache miss for {key} (file not found)")
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if "expires_at" in cache_data and cache_data["expires_at"] < time.time():
                debug(f"Cache expired for {key} (expired at {time.ctime(cache_data['expires_at'])})")
                return None
            
            # Cache hit
            debug(f"Cache hit for {key} (expires at {time.ctime(cache_data['expires_at'])})")
            return cache_data["value"]
        
        except Exception as e:
            debug(f"Error reading cache for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 day)
        """
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            "value": value,
            "expires_at": time.time() + ttl,
        }
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
            debug(f"Cache updated for {key} (expires at {time.ctime(cache_data['expires_at'])})")
        except Exception as e:
            debug(f"Error writing cache for {key}: {e}")
            # Ignore cache write errors
            pass
    
    def clear(self) -> None:
        """Clear all cached data."""
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except Exception:
                    pass
        info(f"Cache cleared from {self.cache_dir}")
