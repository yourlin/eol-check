"""
Report generators for different output formats.
"""

from typing import Dict, Any

from end_of_life_checker.reporters.base import BaseReporter
from end_of_life_checker.reporters.text import TextReporter
from end_of_life_checker.reporters.json_reporter import JsonReporter
from end_of_life_checker.reporters.csv_reporter import CsvReporter
from end_of_life_checker.reporters.html_reporter import HtmlReporter


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
