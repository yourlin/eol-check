"""
Version utility functions.
"""

import re
from typing import List, Optional, Tuple


def parse_version(version_str: str) -> List[int]:
    """Parse a version string into a list of integers.
    
    Args:
        version_str: Version string (e.g., "1.2.3")
        
    Returns:
        List of integers (e.g., [1, 2, 3])
    """
    # Extract numbers from version string
    parts = re.findall(r'\d+', version_str)
    
    # Convert to integers
    return [int(part) for part in parts]


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2
    """
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)
    
    # Compare parts
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = v1_parts[i] if i < len(v1_parts) else 0
        v2_part = v2_parts[i] if i < len(v2_parts) else 0
        
        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1
    
    return 0


def normalize_version(version_str: str) -> str:
    """Normalize a version string.
    
    Args:
        version_str: Version string
        
    Returns:
        Normalized version string
    """
    # Remove common prefixes
    version_str = re.sub(r'^v', '', version_str)
    
    # Extract version numbers
    parts = parse_version(version_str)
    
    # Join with dots
    return ".".join(str(part) for part in parts)


def extract_major_minor(version: str) -> str:
    """Extract major.minor version from a version string.
    
    Args:
        version: Version string (e.g., "2.7.16")
        
    Returns:
        Major.minor version (e.g., "2.7")
    """
    # Extract first two version components (major.minor)
    match = re.match(r'^(\d+\.\d+)', version)
    if match:
        return match.group(1)
    return version


def has_major_version_change(current_version: str, recommended_version: str) -> bool:
    """Check if there is a major version change between two versions.
    
    Args:
        current_version: Current version string
        recommended_version: Recommended version string
        
    Returns:
        True if there is a major version change, False otherwise
    """
    if not current_version or not recommended_version:
        return False
        
    current_parts = parse_version(current_version)
    recommended_parts = parse_version(recommended_version)
    
    if not current_parts or not recommended_parts:
        return False
        
    # Compare major version numbers
    return current_parts[0] != recommended_parts[0]
