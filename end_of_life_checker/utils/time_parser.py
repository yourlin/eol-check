"""
Utility for parsing time duration strings.
"""

import re
from typing import Optional


def parse_duration(duration_str: str) -> Optional[int]:
    """Parse a duration string into seconds.
    
    Supports formats like:
    - 1d (1 day)
    - 2h (2 hours)
    - 30m (30 minutes)
    - 45s (45 seconds)
    - 1d12h (1 day and 12 hours)
    - 2h30m (2 hours and 30 minutes)
    
    Args:
        duration_str: Duration string to parse
        
    Returns:
        Duration in seconds or None if invalid format
    """
    if not duration_str:
        return None
    
    # Convert to lowercase
    duration_str = duration_str.lower()
    
    # Check if it's just a number (assume seconds)
    if duration_str.isdigit():
        return int(duration_str)
    
    # Define time units in seconds
    units = {
        'd': 86400,  # days
        'h': 3600,   # hours
        'm': 60,     # minutes
        's': 1       # seconds
    }
    
    # Extract all time components
    pattern = r'(\d+)([dhms])'
    matches = re.findall(pattern, duration_str)
    
    if not matches:
        return None
    
    total_seconds = 0
    for value, unit in matches:
        total_seconds += int(value) * units[unit]
    
    return total_seconds


def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        result = f"{minutes}m"
        if seconds > 0:
            result += f"{seconds}s"
        return result
    
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        result = f"{hours}h"
        if minutes > 0:
            result += f"{minutes}m"
        return result
    
    days, hours = divmod(hours, 24)
    result = f"{days}d"
    if hours > 0:
        result += f"{hours}h"
    return result
