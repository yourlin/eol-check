"""
Command-line interface for the End of Life Checker.
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Optional

from eol_check.core import EOLChecker
from eol_check.reporters import get_reporter
from eol_check.utils.logger import configure_logger, info, error, debug


def parse_cache_ttl(value: str) -> int:
    """Parse cache TTL value from string.
    
    Args:
        value: Cache TTL string (e.g., "1d", "12h", "30m")
        
    Returns:
        Cache TTL in seconds
        
    Raises:
        argparse.ArgumentTypeError: If the value is invalid
    """
    # Simple implementation for now
    if value.endswith('d'):
        try:
            days = int(value[:-1])
            return days * 24 * 60 * 60
        except ValueError:
            pass
    elif value.endswith('h'):
        try:
            hours = int(value[:-1])
            return hours * 60 * 60
        except ValueError:
            pass
    elif value.endswith('m'):
        try:
            minutes = int(value[:-1])
            return minutes * 60
        except ValueError:
            pass
    
    raise argparse.ArgumentTypeError(
        f"Invalid cache TTL format: {value}. "
        "Use formats like '1d' (1 day), '12h' (12 hours), '30m' (30 minutes)."
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Check the end-of-life status of software dependencies in your projects."
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        help="Path to the project directory to check",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        help="Save report to file instead of stdout",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=90,
        help="Days before EOL to start warning (default: 90)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use cached EOL data instead of fetching from endoflife.date",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Force update of cached EOL data",
    )
    parser.add_argument(
        "--cache-ttl",
        type=parse_cache_ttl,
        default="1d",
        help="Cache time-to-live duration (default: 1d). "
             "Formats: '1d' (1 day), '12h' (12 hours), '30m' (30 minutes).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information about the checking process",
    )
    parser.add_argument(
        "--ignore-file",
        help="Path to file containing dependencies to ignore",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers for API requests (default: CPU count * 2)",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the graphical user interface",
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Launch UI if requested
    if args.ui:
        try:
            from eol_check.ui import main as ui_main
            ui_main()
            return
        except ImportError:
            error("Could not import streamlit. Please install it with 'pip install streamlit'.")
            sys.exit(1)
    
    # Ensure project path is provided for CLI mode
    if not args.project_path:
        error("Project path is required when not using the UI mode.")
        error("Use 'eol-check /path/to/project' or 'eol-check --ui' to launch the UI.")
        sys.exit(1)
    
    # Configure logger based on verbose flag
    configure_logger(verbose=args.verbose)
    
    # Validate project path
    if not os.path.exists(args.project_path):
        error(f"Project path '{args.project_path}' does not exist.")
        sys.exit(1)
    
    # Initialize the checker - verbose flag controls debug output, not progress bar
    checker = EOLChecker(
        threshold_days=args.threshold,
        offline_mode=args.offline,
        force_update=args.update,
        verbose=args.verbose,
        ignore_file=args.ignore_file,
        cache_ttl=args.cache_ttl,
        max_workers=args.max_workers,
    )
    
    # Run the check
    try:
        info(f"Starting EOL check for project: {args.project_path}")
        results = checker.check_project(args.project_path)
        info(f"EOL check completed in {results['execution_time']:.2f} seconds")
    except Exception as e:
        error(f"Error checking project: {e}")
        if args.verbose:
            import traceback
            error(traceback.format_exc())
        sys.exit(1)
    
    # Generate the report
    reporter = get_reporter(args.format)
    
    # Get execution time from results if available
    execution_time = results.get("execution_time")
    
    report = reporter.generate_report(
        results=results,
        project_path=args.project_path,
        scan_date=datetime.now(),
        threshold_days=args.threshold,
        execution_time=execution_time,
    )
    
    # Output the report
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        except Exception as e:
            print(f"Error saving report: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(report)
    
    # Exit with non-zero status if critical issues found
    if results.get("summary", {}).get("critical", 0) > 0:
        sys.exit(2)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
