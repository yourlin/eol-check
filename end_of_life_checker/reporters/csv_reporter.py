"""
CSV reporter for generating CSV reports.
"""

import csv
import io
from datetime import datetime
from typing import Dict, Any

from end_of_life_checker.reporters.base import BaseReporter


class CsvReporter(BaseReporter):
    """Reporter for CSV output."""
    
    def generate_report(
        self,
        results: Dict[str, Any],
        project_path: str,
        scan_date: datetime,
        threshold_days: int,
    ) -> str:
        """Generate a CSV report.
        
        Args:
            results: Check results
            project_path: Path to the project
            scan_date: Date of the scan
            threshold_days: Days before EOL to start warning
            
        Returns:
            Report as CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Project",
            "Name",
            "Version",
            "Type",
            "Status",
            "EOL Date",
            "Days Remaining",
            "Recommended Version",
            "Is Dev Dependency",
        ])
        
        # Write dependencies
        project_name = f"{results.get('project_name', 'Unknown')}"
        for dep in results.get("dependencies", []):
            writer.writerow([
                project_name,
                dep.get("name", ""),
                dep.get("version", ""),
                dep.get("type", ""),
                dep.get("status", ""),
                dep.get("eol_date", ""),
                dep.get("days_remaining", ""),
                dep.get("recommended_version", ""),
                "Yes" if dep.get("dev", False) else "No",
            ])
        
        return output.getvalue()
