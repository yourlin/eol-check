"""
Text reporter for generating plain text reports.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from end_of_life_checker.reporters.base import BaseReporter


class TextReporter(BaseReporter):
    """Reporter for plain text output."""
    
    # Status emoji mapping
    STATUS_EMOJIS = {
        "CRITICAL": "🔴",
        "WARNING": "🟠",
        "OK": "🟢", 
        "UNKNOWN": "❓",
        "ERROR": "⚠️"
    }
    
    def generate_report(
        self,
        results: Dict[str, Any],
        project_path: str,
        scan_date: datetime,
        threshold_days: int,
        execution_time: float = None,
    ) -> str:
        """Generate a plain text report.
        
        Args:
            results: Check results
            project_path: Path to the project
            scan_date: Date of the scan
            threshold_days: Days before EOL to start warning
            execution_time: Total execution time in seconds (optional)
            
        Returns:
            Report as string
        """
        lines = []
        
        # Header
        lines.append("End of Life Checker Report")
        lines.append("=========================")
        lines.append(f"Project: {results.get('project_name', 'Unknown')} ({results.get('project_path', project_path)})")
        lines.append(f"Scan Date: {scan_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add execution time if provided
        if execution_time is not None:
            # Format execution time
            if execution_time < 1:
                time_str = f"{execution_time * 1000:.0f} ms"
            elif execution_time < 60:
                time_str = f"{execution_time:.2f} seconds"
            else:
                minutes = int(execution_time // 60)
                seconds = execution_time % 60
                time_str = f"{minutes} min {seconds:.2f} sec"
            
            lines.append(f"Execution Time: {time_str}")
        
        lines.append("")
        
        # Summary
        summary = results.get("summary", {})
        critical_count = summary.get("critical", 0)
        warning_count = summary.get("warning", 0)
        ok_count = summary.get("ok", 0)
        
        if critical_count > 0:
            lines.append(f"{self.STATUS_EMOJIS['CRITICAL']} {critical_count} dependencies have reached end of life")
        
        if warning_count > 0:
            lines.append(f"{self.STATUS_EMOJIS['WARNING']} {warning_count} dependencies will reach end of life within {threshold_days} days")
        
        if ok_count > 0:
            lines.append(f"{self.STATUS_EMOJIS['OK']} {ok_count} dependencies are up to date")
        
        if critical_count == 0 and warning_count == 0 and ok_count == 0:
            lines.append("No dependencies found or analyzed")
        
        lines.append("")
        
        # Details
        if results.get("dependencies"):
            lines.append("Details:")
            lines.append("--------")
            
            # Sort dependencies by status (critical first, then warning, then ok)
            sorted_deps = sorted(
                results["dependencies"],
                key=lambda d: {"CRITICAL": 0, "WARNING": 1, "OK": 2, "UNKNOWN": 3, "ERROR": 4}.get(d["status"], 5)
            )
            
            for dep in sorted_deps:
                name = dep["name"]
                version = dep["version"]
                status = dep["status"]
                eol_date = dep.get("eol_date")
                days_remaining = dep.get("days_remaining")
                recommended = dep.get("recommended_version")
                has_breaking_changes = dep.get("has_breaking_changes", False)
                
                emoji = self.STATUS_EMOJIS.get(status, "❓")
                
                if status == "CRITICAL":
                    if eol_date and days_remaining is not None:
                        lines.append(f"{emoji} {name} {version} - EOL since {eol_date} ({abs(days_remaining)} days ago)")
                    else:
                        lines.append(f"{emoji} {name} {version} - Has reached end of life")
                
                elif status == "WARNING":
                    if eol_date and days_remaining is not None:
                        lines.append(f"{emoji} {name} {version} - EOL in {days_remaining} days ({eol_date})")
                    else:
                        lines.append(f"{emoji} {name} {version} - Will reach end of life soon")
                
                elif status == "OK":
                    if eol_date and days_remaining is not None:
                        lines.append(f"{emoji} {name} {version} - EOL in {days_remaining} days ({eol_date})")
                    else:
                        lines.append(f"{emoji} {name} {version} - No EOL date available")
                
                elif status == "UNKNOWN":
                    lines.append(f"{emoji} {name} {version} - No EOL information available")
                
                elif status == "ERROR":
                    lines.append(f"{emoji} {name} {version} - Error checking EOL status: {dep.get('error', 'Unknown error')}")
                
                # Add recommendation if available
                if recommended:
                    breaking_emoji = "⚠️ " if has_breaking_changes else ""
                    lines.append(f"  → Recommended upgrade: {breaking_emoji}{name} {recommended}")
                    if has_breaking_changes:
                        lines.append(f"    ⚠️ Warning: This upgrade contains breaking changes (major version change)")
                
                lines.append("")
        
        return "\n".join(lines)
