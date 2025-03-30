"""
Core functionality for the End of Life Checker.
"""

import os
import sys
import time
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Any

from eol_check.api.endoflife_client import EndOfLifeClient
from eol_check.parsers import get_parsers_for_project
from eol_check.utils.cache import Cache
from eol_check.utils.logger import debug, info, warning, error
from eol_check.utils.request_pool import RequestPool


class EOLChecker:
    """Main class for checking end-of-life status of dependencies."""
    
    def __init__(
        self,
        threshold_days: int = 90,
        offline_mode: bool = False,
        force_update: bool = False,
        verbose: bool = False,
        ignore_file: Optional[str] = None,
        cache_ttl: int = None,
        max_workers: Optional[int] = None,
    ):
        """Initialize the EOL checker.
        
        Args:
            threshold_days: Days before EOL to start warning
            offline_mode: Use cached EOL data instead of fetching from endoflife.date
            force_update: Force update of cached EOL data
            verbose: Show detailed information about the checking process
            ignore_file: Path to file containing dependencies to ignore
            cache_ttl: Cache time-to-live in seconds
            max_workers: Maximum number of parallel workers for API requests
        """
        self.threshold_days = threshold_days
        self.offline_mode = offline_mode
        self.force_update = force_update
        self.verbose = verbose
        self.ignore_list = self._load_ignore_list(ignore_file) if ignore_file else []
        self.max_workers = max_workers
        
        self.cache = Cache()
        self.api_client = EndOfLifeClient(
            cache=self.cache,
            offline_mode=offline_mode,
            force_update=force_update,
            cache_ttl=cache_ttl,
        )
    
    def _load_ignore_list(self, ignore_file: str) -> List[str]:
        """Load list of dependencies to ignore from file."""
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not load ignore file: {e}")
            return []
    
    def _print_progress_bar(self, current: int, total: int, prefix: str = '', suffix: str = '', length: int = 50):
        """Print a progress bar to the console.
        
        Args:
            current: Current progress value
            total: Total value
            prefix: Prefix string
            suffix: Suffix string
            length: Character length of the progress bar
        """
        # Always show progress bar regardless of verbose mode
        percent = float(current) / float(total) if total > 0 else 0
        filled_length = int(length * percent)
        bar = '█' * filled_length + '-' * (length - filled_length)
        sys.stdout.write(f'\r{prefix} |{bar}| {current}/{total} ({percent:.1%}) {suffix}')
        sys.stdout.flush()  # Ensure output is flushed immediately
        if current == total:
            sys.stdout.write('\n')
    
    def check_project(self, project_path: str) -> Dict[str, Any]:
        """Check the EOL status of dependencies in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with check results
        """
        start_time = time.time()
        
        # Get absolute path for better reporting
        abs_project_path = os.path.abspath(project_path)
        project_name = os.path.basename(abs_project_path)
        
        if self.verbose:
            info(f"Checking project: {abs_project_path}")
        
        # Detect project type and get all appropriate parsers
        parsers = get_parsers_for_project(project_path)
        if not parsers:
            raise ValueError(f"Could not determine project type for {abs_project_path}")
        
        # Initialize results
        results = {
            "project_path": abs_project_path,
            "project_name": project_name,
            "dependencies": [],
            "summary": {
                "critical": 0,
                "warning": 0,
                "ok": 0,
                "unknown": 0,
            }
        }
        
        # Process each parser
        all_dependencies = []
        for parser in parsers:
            if self.verbose:
                print(f"Using parser: {parser.__class__.__name__}")
            
            # Parse dependencies
            dependencies = parser.parse_dependencies()
            
            if self.verbose:
                print(f"Found {len(dependencies)} dependencies with {parser.__class__.__name__}")
            
            all_dependencies.extend(dependencies)
        
        if self.verbose:
            print(f"Found {len(all_dependencies)} total dependencies across all parsers")
        
        # Filter out ignored dependencies
        all_dependencies = [dep for dep in all_dependencies if dep["name"] not in self.ignore_list]
        
        if self.verbose and self.ignore_list:
            print(f"Filtered to {len(all_dependencies)} dependencies after applying ignore list")
        
        # Check EOL status for each dependency
        today = datetime.now().date()
        total_deps = len(all_dependencies)
        
        # Use request pool for parallel API requests
        with RequestPool(max_workers=self.max_workers) as pool:
            # Define a function to check a single dependency
            def check_dependency(dep):
                try:
                    eol_info = self.api_client.get_eol_info(dep["name"], dep["version"])
                    
                    if not eol_info or "eol" not in eol_info:
                        # No EOL info available
                        return {
                            **dep,
                            "status": "UNKNOWN",
                            "eol_date": None,
                            "days_remaining": None,
                            "recommended_version": None,
                        }, "unknown"
                    else:
                        eol_date = datetime.strptime(eol_info["eol"], "%Y-%m-%d").date()
                        days_remaining = (eol_date - today).days
                        
                        if days_remaining < 0:
                            status = "CRITICAL"
                            summary_key = "critical"
                        elif days_remaining < self.threshold_days:
                            status = "WARNING"
                            summary_key = "warning"
                        else:
                            status = "OK"
                            summary_key = "ok"
                        
                        # Determine recommended version
                        recommended_version = None
                        has_breaking_changes = False
                        
                        if status in ["CRITICAL", "WARNING"]:
                            # For EOL or approaching EOL dependencies, find the latest non-EOL version
                            product_name = self.api_client._get_product_name(dep["name"])
                            if product_name:
                                try:
                                    all_versions = self.api_client.get_product_versions(product_name)
                                    # Sort versions by release date (newest first)
                                    active_versions = [v for v in all_versions if v.get("eol") is False or 
                                                      (isinstance(v.get("eol"), str) and 
                                                       datetime.strptime(v["eol"], "%Y-%m-%d").date() > today)]
                                    
                                    if active_versions:
                                        # Get the latest version that's not EOL
                                        latest_active = active_versions[0]
                                        recommended_version = latest_active.get("latest")
                                        
                                        # Check if this is a major version change
                                        from eol_check.utils.version import has_major_version_change
                                        if recommended_version and has_major_version_change(dep["version"], recommended_version):
                                            has_breaking_changes = True
                                    else:
                                        # If all versions are EOL, recommend the latest version
                                        recommended_version = eol_info.get("latest")
                                except Exception as e:
                                    if self.verbose:
                                        print(f"Error getting recommended version for {dep['name']}: {e}")
                        
                        return {
                            **dep,
                            "status": status,
                            "eol_date": eol_info["eol"],
                            "days_remaining": days_remaining,
                            "recommended_version": recommended_version,
                            "has_breaking_changes": has_breaking_changes,
                        }, summary_key
                except Exception as e:
                    if self.verbose:
                        print(f"Error checking {dep['name']}: {e}")
                    return {
                        **dep,
                        "status": "ERROR",
                        "error": str(e),
                    }, "unknown"
            
            # Show progress message
            info(f"Checking {total_deps} dependencies...")
            
            # Show cache status if verbose
            if self.verbose:
                cache_dir = self.api_client.cache.cache_dir
                cache_files = os.listdir(cache_dir) if os.path.exists(cache_dir) else []
                cache_count = len([f for f in cache_files if f.endswith('.json')])
                info(f"Using cache directory: {cache_dir}")
                info(f"Found {cache_count} cached items")
                info(f"Using {self.max_workers or 'default'} workers")
                info("")  # Add an empty line before progress bar
            
            # Process dependencies in parallel
            futures = []
            for dep in all_dependencies:
                future = pool.submit(check_dependency, dep)
                futures.append(future)
            
            # Track progress as futures complete
            dep_results = []
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
                dep_results.append(result)
                
                # Always update progress bar
                self._print_progress_bar(i + 1, total_deps, 
                                       prefix='Checking dependencies:', 
                                       suffix='Complete', length=40)
            
            # Update results
            for dep_result, summary_key in dep_results:
                results["dependencies"].append(dep_result)
                results["summary"][summary_key] += 1
        
        # Add execution time to results
        end_time = time.time()
        results["execution_time"] = end_time - start_time
        
        return results
