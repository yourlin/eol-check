"""
Client for the endoflife.date API.
"""

import json
import re
import time
from typing import Dict, Optional, Any, List

import requests

from end_of_life_checker.utils.cache import Cache
from end_of_life_checker.utils.logger import debug, info, warning, error
from end_of_life_checker.utils.version import normalize_version


class EndOfLifeClient:
    """Client for interacting with the endoflife.date API."""
    
    BASE_URL = "https://endoflife.date/api"
    DEFAULT_CACHE_TTL = 24 * 60 * 60  # 1 day in seconds
    
    def __init__(
        self,
        cache: Cache,
        offline_mode: bool = False,
        force_update: bool = False,
        cache_ttl: int = None,
    ):
        """Initialize the client.
        
        Args:
            cache: Cache instance for storing API responses
            offline_mode: If True, only use cached data
            force_update: If True, ignore cache and fetch fresh data
            cache_ttl: Cache time-to-live in seconds (default: 1 day)
        """
        self.cache = cache
        self.offline_mode = offline_mode
        self.force_update = force_update
        self.cache_ttl = cache_ttl if cache_ttl is not None else self.DEFAULT_CACHE_TTL
        
        # Map of package managers to endoflife.date product names
        self.product_mapping = {
            # Node.js packages
            "react": "react",
            "angular": "angular",
            "vue": "vue",
            "node": "nodejs",
            "nodejs": "nodejs",
            
            # Python packages
            "django": "django",
            "python": "python",
            
            # Java packages
            "spring": "spring",
            "spring-boot": "spring-boot",
            "java": "java",
            "spring-boot-starter-parent": "spring-boot",
            
            # Add more mappings as needed
        }
        
        # Cache for product availability
        self.available_products_cache = {}
    
    def _fetch_from_api(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data from the API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Data as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        debug(f"Fetching from API: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def _get_with_cache(self, endpoint: str) -> Dict[str, Any]:
        """Get data from cache or API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Data as dictionary
        """
        # Remove .json extension if it's in the endpoint to avoid double extension in cache key
        if endpoint.endswith(".json"):
            clean_endpoint = endpoint[:-5]
        else:
            clean_endpoint = endpoint
            
        cache_key = f"eol_api_{clean_endpoint}"
        
        # Debug info
        if self.offline_mode or self.force_update:
            debug(f"Cache mode: offline={self.offline_mode}, force_update={self.force_update}")
        
        # Check if we should use cache
        if not self.force_update:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                if self.offline_mode:
                    info(f"Using cached data for {endpoint}")
                return cached_data
        
        # If offline mode and no cache, raise error
        if self.offline_mode:
            error_msg = f"No cached data available for {endpoint} and offline mode is enabled"
            error(error_msg)
            raise ValueError(error_msg)
        
        # Fetch from API
        data = self._fetch_from_api(endpoint)
        
        # Update cache
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
        
        return data
    
    def _get_product_name(self, package_name: str) -> str:
        """Get the product name for a package.
        
        Args:
            package_name: Package name
            
        Returns:
            Product name
        """
        # Convert to lowercase for case-insensitive matching
        package_name_lower = package_name.lower()
        
        # Check if we have a direct mapping
        if package_name_lower in self.product_mapping:
            return self.product_mapping[package_name_lower]
        
        # Try to normalize the name
        normalized_name = package_name_lower.replace("_", "-")
        if normalized_name in self.product_mapping:
            return self.product_mapping[normalized_name]
        
        # Default to the package name itself
        return package_name_lower
    
    def _is_product_available(self, product_name: str) -> bool:
        """Check if a product is available in the API.
        
        Args:
            product_name: Product name
            
        Returns:
            True if the product is available, False otherwise
        """
        # Check cache first
        if product_name in self.available_products_cache:
            return self.available_products_cache[product_name]
        
        try:
            # Try to fetch product info
            self._get_with_cache(product_name)
            self.available_products_cache[product_name] = True
            return True
        except Exception:
            self.available_products_cache[product_name] = False
            return False
    
    def get_product_versions(self, product_name: str) -> List[Dict[str, Any]]:
        """Get all versions for a product.
        
        Args:
            product_name: Product name
            
        Returns:
            List of version information
        """
        return self._get_with_cache(product_name)
    
    def get_eol_info(self, package_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get EOL information for a package version.
        
        Args:
            package_name: Package name
            version: Package version
            
        Returns:
            EOL information or None if not found
        """
        product_name = self._get_product_name(package_name)
        debug(f"Looking up EOL info for {package_name} {version} (product: {product_name})")
        
        # Check if the product is available
        if not self._is_product_available(product_name):
            debug(f"Product {product_name} not available in endoflife.date API")
            return None
        
        try:
            # Get all versions for the product
            versions = self.get_product_versions(product_name)
            
            # Normalize the version for comparison
            normalized_version = normalize_version(version)
            
            # Find the matching version
            for ver_info in versions:
                if "cycle" in ver_info:
                    ver_cycle = ver_info["cycle"]
                    
                    # Try to match the version with the cycle
                    if normalized_version.startswith(ver_cycle):
                        debug(f"Found exact match for {package_name} {version}: cycle {ver_cycle}")
                        return ver_info
            
            # If no exact match, try to find the closest match
            for ver_info in versions:
                if "cycle" in ver_info:
                    ver_cycle = ver_info["cycle"]
                    
                    # Check if the major version matches
                    if normalized_version.split(".")[0] == ver_cycle.split(".")[0]:
                        debug(f"Found closest match for {package_name} {version}: cycle {ver_cycle}")
                        return ver_info
            
            debug(f"No EOL info found for {package_name} {version}")
            return None
        
        except Exception as e:
            # If there's an error, return None
            warning(f"Error getting EOL info for {package_name} {version}: {e}")
            return None
