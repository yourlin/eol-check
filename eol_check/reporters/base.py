"""
Base reporter class for generating reports.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any


class BaseReporter(ABC):
    """Base class for report generators."""
    
    @abstractmethod
    def generate_report(
        self,
        results: Dict[str, Any],
        project_path: str,
        scan_date: datetime,
        threshold_days: int,
        execution_time: float = None,
    ) -> str:
        """Generate a report from the check results.
        
        Args:
            results: Check results
            project_path: Path to the project
            scan_date: Date of the scan
            threshold_days: Days before EOL to start warning
            execution_time: Total execution time in seconds (optional)
            
        Returns:
            Report as string
        """
        pass
