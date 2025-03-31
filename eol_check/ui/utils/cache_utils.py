"""
Cache utilities for the End of Life Checker UI.
"""

import json
import os
import time
from datetime import datetime

import streamlit as st

from eol_check.utils.cache import Cache


def load_cache_data():
    """Load and display cache data.
    
    Returns:
        list: List of cache data items.
    """
    cache = Cache()
    cache_dir = cache.cache_dir

    if not os.path.exists(cache_dir):
        st.warning(f"Cache directory does not exist: {cache_dir}")
        return []

    cache_files = [f for f in os.listdir(cache_dir) if f.endswith(".json")]

    if not cache_files:
        st.info("No cached data found.")
        return []

    cache_data = []
    for filename in cache_files:
        try:
            file_path = os.path.join(cache_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract key information
            key = filename.replace(".json", "").replace("_", "/")
            expires_at = data.get("expires_at", 0)
            expires_date = datetime.fromtimestamp(expires_at).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            is_expired = expires_at < time.time()

            # Try to determine if this is product availability data
            is_availability = "product_availability" in key

            # For product availability, the value is a boolean
            if is_availability:
                product_name = key.split("_")[-1]
                is_available = data.get('value', False)
                value_summary = f"API {'Available' if is_available else 'Unavailable'}"
                item_type = "Product Availability"
            else:
                # For regular API data, summarize the content
                value = data.get("value", {})
                if isinstance(value, dict):
                    if not value:
                        value_summary = "Empty (Not Found)"
                    else:
                        value_summary = f"{len(value)} items"
                elif isinstance(value, list):
                    value_summary = f"{len(value)} versions"
                else:
                    value_summary = (
                        str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    )

                item_type = "API Data"

            cache_data.append(
                {
                    "key": key,
                    "type": item_type,
                    "content": value_summary,
                    "expires_at": expires_date,
                    "is_expired": is_expired,
                    "file_path": file_path,
                }
            )

        except Exception as e:
            st.error(f"Error reading cache file {filename}: {e}")

    return cache_data


def parse_cache_ttl(value):
    """Parse cache TTL value from string.

    Args:
        value: Cache TTL string (e.g., "1d", "12h", "30m")

    Returns:
        Cache TTL in seconds
    """
    if value.endswith("d"):
        try:
            days = int(value[:-1])
            return days * 24 * 60 * 60
        except ValueError:
            pass
    elif value.endswith("h"):
        try:
            hours = int(value[:-1])
            return hours * 60 * 60
        except ValueError:
            pass
    elif value.endswith("m"):
        try:
            minutes = int(value[:-1])
            return minutes * 60
        except ValueError:
            pass

    return 24 * 60 * 60  # Default to 1 day
