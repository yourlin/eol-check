"""
HTML reporter for generating HTML reports.
"""

from datetime import datetime
from typing import Dict, Any

from eol_check.reporters.base import BaseReporter


class HtmlReporter(BaseReporter):
    """Reporter for HTML output."""
    
    def generate_report(
        self,
        results: Dict[str, Any],
        project_path: str,
        scan_date: datetime,
        threshold_days: int,
    ) -> str:
        """Generate an HTML report.
        
        Args:
            results: Check results
            project_path: Path to the project
            scan_date: Date of the scan
            threshold_days: Days before EOL to start warning
            
        Returns:
            Report as HTML string
        """
        summary = results.get("summary", {})
        critical_count = summary.get("critical", 0)
        warning_count = summary.get("warning", 0)
        ok_count = summary.get("ok", 0)
        
        # Start building HTML
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang=\"en\">")
        html.append("<head>")
        html.append("  <meta charset=\"UTF-8\">")
        html.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        html.append("  <title>End of Life Checker Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("    h1 { color: #333; }")
        html.append("    .summary { margin: 20px 0; }")
        html.append("    .critical { color: #d9534f; }")
        html.append("    .warning { color: #f0ad4e; }")
        html.append("    .ok { color: #5cb85c; }")
        html.append("    table { border-collapse: collapse; width: 100%; }")
        html.append("    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("    th { background-color: #f2f2f2; }")
        html.append("    tr:nth-child(even) { background-color: #f9f9f9; }")
        html.append("    .recommended { margin-top: 5px; font-style: italic; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        
        # Header
        html.append("  <h1>End of Life Checker Report</h1>")
        html.append(f"  <p><strong>Project:</strong> {results.get('project_name', 'Unknown')} ({results.get('project_path', project_path)})</p>")
        html.append(f"  <p><strong>Scan Date:</strong> {scan_date.strftime('%Y-%m-%d')}</p>")
        
        # Summary
        html.append("  <div class=\"summary\">")
        html.append("    <h2>Summary</h2>")
        
        if critical_count > 0:
            html.append(f"    <p class=\"critical\">CRITICAL: {critical_count} dependencies have reached end of life</p>")
        
        if warning_count > 0:
            html.append(f"    <p class=\"warning\">WARNING: {warning_count} dependencies will reach end of life within {threshold_days} days</p>")
        
        if ok_count > 0:
            html.append(f"    <p class=\"ok\">OK: {ok_count} dependencies are up to date</p>")
        
        if critical_count == 0 and warning_count == 0 and ok_count == 0:
            html.append("    <p>No dependencies found or analyzed</p>")
        
        html.append("  </div>")
        
        # Details
        if results.get("dependencies"):
            html.append("  <div class=\"details\">")
            html.append("    <h2>Details</h2>")
            html.append("    <table>")
            html.append("      <tr>")
            html.append("        <th>Status</th>")
            html.append("        <th>Name</th>")
            html.append("        <th>Version</th>")
            html.append("        <th>Type</th>")
            html.append("        <th>EOL Date</th>")
            html.append("        <th>Days Remaining</th>")
            html.append("        <th>Recommended Version</th>")
            html.append("      </tr>")
            
            # Sort dependencies by status (critical first, then warning, then ok)
            sorted_deps = sorted(
                results["dependencies"],
                key=lambda d: {"CRITICAL": 0, "WARNING": 1, "OK": 2, "UNKNOWN": 3, "ERROR": 4}.get(d["status"], 5)
            )
            
            for dep in sorted_deps:
                name = dep["name"]
                version = dep["version"]
                status = dep["status"]
                dep_type = dep.get("type", "")
                eol_date = dep.get("eol_date", "")
                days_remaining = dep.get("days_remaining")
                recommended = dep.get("recommended_version", "")
                
                # Set row class based on status
                row_class = status.lower() if status in ["CRITICAL", "WARNING", "OK"] else ""
                
                html.append(f"      <tr class=\"{row_class}\">")
                html.append(f"        <td>{status}</td>")
                html.append(f"        <td>{name}</td>")
                html.append(f"        <td>{version}</td>")
                html.append(f"        <td>{dep_type}</td>")
                html.append(f"        <td>{eol_date}</td>")
                
                # Format days remaining
                if days_remaining is not None:
                    if days_remaining < 0:
                        days_text = f"{abs(days_remaining)} days ago"
                    else:
                        days_text = f"{days_remaining} days"
                    html.append(f"        <td>{days_text}</td>")
                else:
                    html.append("        <td>Unknown</td>")
                
                # Recommended version
                if recommended:
                    html.append(f"        <td>{recommended}</td>")
                else:
                    html.append("        <td>-</td>")
                
                html.append("      </tr>")
            
            html.append("    </table>")
            html.append("  </div>")
        
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
