"""
Report generators for different output formats.
"""

from typing import Dict, Any

from eol_check.reporters.base import BaseReporter
from eol_check.reporters.text import TextReporter
from eol_check.reporters.json_reporter import JsonReporter
from eol_check.reporters.csv_reporter import CsvReporter
from eol_check.reporters.html_reporter import HtmlReporter


def get_reporter(format_name: str) -> BaseReporter:
    """Get a reporter for the specified format.
    
    Args:
        format_name: Name of the format (text, json, csv, html)
        
    Returns:
        Reporter instance
    """
    reporters = {
        "text": TextReporter,
        "json": JsonReporter,
        "csv": CsvReporter,
        "html": HtmlReporter,
    }
    
    reporter_class = reporters.get(format_name.lower(), TextReporter)
    return reporter_class()
