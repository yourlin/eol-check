"""
JSON reporter for generating JSON reports.
"""

import json
from datetime import datetime
from typing import Dict, Any

from eol_check.reporters.base import BaseReporter


class JsonReporter(BaseReporter):
    """Reporter for JSON output."""
    
    def generate_report(
        self,
        results: Dict[str, Any],
        project_path: str,
        scan_date: datetime,
        threshold_days: int,
    ) -> str:
        """Generate a JSON report.
        
        Args:
            results: Check results
            project_path: Path to the project
            scan_date: Date of the scan
            threshold_days: Days before EOL to start warning
            
        Returns:
            Report as JSON string
        """
        report = {
            "project_name": results.get("project_name", "Unknown"),
            "project_path": results.get("project_path", project_path),
            "scan_date": scan_date.isoformat(),
            "threshold_days": threshold_days,
            "summary": results.get("summary", {}),
            "dependencies": results.get("dependencies", []),
        }
        
        return json.dumps(report, indent=2)
