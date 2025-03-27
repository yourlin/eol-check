"""
Base parser class for project dependencies.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseParser(ABC):
    """Base class for project parsers."""
    
    def __init__(self, project_path: str):
        """Initialize the parser.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path
    
    @abstractmethod
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from the project.
        
        Returns:
            List of dictionaries with dependency information
        """
        pass
