"""
Streamlit UI for the End of Life Checker.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from eol_check.core import EOLChecker
from eol_check.reporters import get_reporter
from eol_check.utils.cache import Cache
from eol_check.utils.logger import configure_logger, info, error, debug


def parse_cache_ttl(value):
    """Parse cache TTL value from string.
    
    Args:
        value: Cache TTL string (e.g., "1d", "12h", "30m")
        
    Returns:
        Cache TTL in seconds
    """
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
    
    return 24 * 60 * 60  # Default to 1 day


def load_cache_data():
    """Load and display cache data."""
    cache = Cache()
    cache_dir = cache.cache_dir
    
    if not os.path.exists(cache_dir):
        st.warning(f"Cache directory does not exist: {cache_dir}")
        return []
    
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
    
    if not cache_files:
        st.info("No cached data found.")
        return []
    
    cache_data = []
    for filename in cache_files:
        try:
            file_path = os.path.join(cache_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract key information
            key = filename.replace('.json', '').replace('_', '/')
            expires_at = data.get('expires_at', 0)
            expires_date = datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
            is_expired = expires_at < time.time()
            
            # Try to determine if this is product availability data
            is_availability = 'product_availability' in key
            
            # For product availability, the value is a boolean
            if is_availability:
                product_name = key.split('_')[-1]
                value_summary = f"Available: {data.get('value', False)}"
                item_type = "Product Availability"
            else:
                # For regular API data, summarize the content
                value = data.get('value', {})
                if isinstance(value, dict):
                    if not value:
                        value_summary = "Empty (Not Found)"
                    else:
                        value_summary = f"{len(value)} items"
                elif isinstance(value, list):
                    value_summary = f"{len(value)} versions"
                else:
                    value_summary = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                
                item_type = "API Data"
            
            cache_data.append({
                'key': key,
                'type': item_type,
                'content': value_summary,
                'expires_at': expires_date,
                'is_expired': is_expired,
                'file_path': file_path
            })
            
        except Exception as e:
            st.error(f"Error reading cache file {filename}: {e}")
    
    return cache_data


def run_ui():
    """Run the Streamlit UI."""
    st.set_page_config(
        page_title="End of Life Checker",
        page_icon="📅",
        layout="wide",
    )
    
    st.title("End of Life Checker")
    st.markdown(
        """
        Check the end-of-life (EOL) status of software dependencies in your projects
        by comparing them with data from [endoflife.date](https://endoflife.date/).
        """
    )
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Check Project", "Cache Management", "About"])
    
    with tab1:
        st.header("Check Project")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Project path input
            project_path = st.text_input(
                "Project Path",
                value=os.getcwd(),
                help="Path to the project directory to check"
            )
            
            # Options
            st.subheader("Options")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                threshold = st.slider(
                    "Warning Threshold (days)",
                    min_value=1,
                    max_value=365,
                    value=90,
                    help="Days before EOL to start warning"
                )
                
                format_options = ["text", "json", "csv", "html"]
                output_format = st.selectbox(
                    "Output Format",
                    options=format_options,
                    index=0,
                    help="Format for the output report"
                )
                
                max_workers = st.number_input(
                    "Max Workers",
                    min_value=1,
                    max_value=32,
                    value=8,
                    help="Maximum number of parallel workers for API requests"
                )
            
            with col_b:
                offline_mode = st.checkbox(
                    "Offline Mode",
                    value=False,
                    help="Use cached EOL data instead of fetching from endoflife.date"
                )
                
                force_update = st.checkbox(
                    "Force Update",
                    value=False,
                    help="Force update of cached EOL data"
                )
                
                verbose = st.checkbox(
                    "Verbose",
                    value=True,
                    help="Show detailed information about the checking process"
                )
                
                ttl_options = {
                    "1 day": "1d",
                    "12 hours": "12h",
                    "6 hours": "6h",
                    "1 hour": "1h",
                    "30 minutes": "30m"
                }
                cache_ttl = st.selectbox(
                    "Cache TTL",
                    options=list(ttl_options.keys()),
                    index=0,
                    help="Cache time-to-live duration"
                )
                cache_ttl_value = ttl_options[cache_ttl]
            
            # Ignore file
            ignore_file = st.text_input(
                "Ignore File",
                value="",
                help="Path to file containing dependencies to ignore (one per line)"
            )
            
            # Output file
            output_file = st.text_input(
                "Output File",
                value="",
                help="Save report to file instead of displaying in UI (optional)"
            )
        
        with col2:
            st.subheader("Run Check")
            st.write("Click the button below to start checking your project dependencies.")
            
            # Generate CLI command preview
            cli_command = f"eol-check {project_path}"
            if threshold != 90:
                cli_command += f" --threshold {threshold}"
            if output_format != "text":
                cli_command += f" --format {output_format}"
            if offline_mode:
                cli_command += " --offline"
            if force_update:
                cli_command += " --update"
            if verbose:
                cli_command += " --verbose"
            if cache_ttl_value != "1d":
                cli_command += f" --cache-ttl {cache_ttl_value}"
            if ignore_file:
                cli_command += f" --ignore-file {ignore_file}"
            if output_file:
                cli_command += f" --output {output_file}"
            if max_workers != 8:
                cli_command += f" --max-workers {max_workers}"
            
            st.code(cli_command, language="bash")
            
            run_button = st.button("Run Check", type="primary")
            
            if run_button:
                if not os.path.exists(project_path):
                    st.error(f"Project path '{project_path}' does not exist.")
                else:
                    with st.spinner("Checking dependencies..."):
                        try:
                            # Configure logger
                            configure_logger(verbose=verbose)
                            
                            # Initialize the checker
                            checker = EOLChecker(
                                threshold_days=threshold,
                                offline_mode=offline_mode,
                                force_update=force_update,
                                verbose=verbose,
                                ignore_file=ignore_file if ignore_file else None,
                                cache_ttl=parse_cache_ttl(cache_ttl_value),
                                max_workers=max_workers,
                            )
                            
                            # Run the check
                            start_time = time.time()
                            results = checker.check_project(project_path)
                            end_time = time.time()
                            execution_time = end_time - start_time
                            
                            # Generate the report
                            reporter = get_reporter(output_format)
                            report = reporter.generate_report(
                                results=results,
                                project_path=project_path,
                                scan_date=datetime.now(),
                                threshold_days=threshold,
                                execution_time=execution_time,
                            )
                            
                            # Save to file if specified
                            if output_file:
                                with open(output_file, "w", encoding="utf-8") as f:
                                    f.write(report)
                                st.success(f"Report saved to {output_file}")
                            
                            # Display the report
                            st.subheader("Results")
                            
                            # Summary statistics
                            summary = results.get("summary", {})
                            critical_count = summary.get("critical", 0)
                            warning_count = summary.get("warning", 0)
                            ok_count = summary.get("ok", 0)
                            unknown_count = summary.get("unknown", 0)
                            
                            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                            
                            with col_stats1:
                                st.metric("Critical", critical_count, delta=None, delta_color="inverse")
                            
                            with col_stats2:
                                st.metric("Warning", warning_count, delta=None, delta_color="inverse")
                            
                            with col_stats3:
                                st.metric("OK", ok_count, delta=None, delta_color="normal")
                            
                            with col_stats4:
                                st.metric("Unknown", unknown_count, delta=None, delta_color="off")
                            
                            # Format-specific display
                            if output_format == "html":
                                st.components.v1.html(report, height=600, scrolling=True)
                            elif output_format == "json":
                                st.json(results)
                            else:
                                st.text(report)
                            
                            # Detailed dependency table
                            if results.get("dependencies"):
                                st.subheader("Dependencies")
                                
                                # Prepare data for table
                                table_data = []
                                for dep in results["dependencies"]:
                                    status = dep["status"]
                                    status_emoji = {
                                        "CRITICAL": "🔴",
                                        "WARNING": "🟠",
                                        "OK": "🟢",
                                        "UNKNOWN": "❓",
                                        "ERROR": "⚠️"
                                    }.get(status, "")
                                    
                                    eol_date = dep.get("eol_date", "")
                                    days_remaining = dep.get("days_remaining")
                                    if days_remaining is not None:
                                        if days_remaining < 0:
                                            days_text = f"{abs(days_remaining)} days ago"
                                        else:
                                            days_text = f"{days_remaining} days"
                                    else:
                                        days_text = ""
                                    
                                    recommended = dep.get("recommended_version", "")
                                    has_breaking = "⚠️" if dep.get("has_breaking_changes") else ""
                                    
                                    table_data.append({
                                        "Status": f"{status_emoji} {status}",
                                        "Name": dep["name"],
                                        "Version": dep["version"],
                                        "EOL Date": eol_date,
                                        "Days Remaining": days_text,
                                        "Recommended": f"{recommended} {has_breaking}".strip()
                                    })
                                
                                st.dataframe(
                                    table_data,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "Status": st.column_config.TextColumn("Status"),
                                        "Name": st.column_config.TextColumn("Name"),
                                        "Version": st.column_config.TextColumn("Version"),
                                        "EOL Date": st.column_config.TextColumn("EOL Date"),
                                        "Days Remaining": st.column_config.TextColumn("Days Remaining"),
                                        "Recommended": st.column_config.TextColumn("Recommended")
                                    }
                                )
                            
                        except Exception as e:
                            st.error(f"Error checking project: {e}")
                            if verbose:
                                import traceback
                                st.code(traceback.format_exc(), language="python")
    
    with tab2:
        st.header("Cache Management")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Cached Data")
            cache = Cache()
            cache_dir = cache.cache_dir
            st.info(f"Cache directory: {cache_dir}")
            
            refresh_cache = st.button("Refresh Cache Data")
            
            if refresh_cache or 'cache_data' not in st.session_state:
                with st.spinner("Loading cache data..."):
                    st.session_state.cache_data = load_cache_data()
            
            # Display cache data
            if st.session_state.cache_data:
                # Filter options
                filter_options = ["All", "Product Availability", "API Data", "Expired Only", "Valid Only"]
                selected_filter = st.selectbox("Filter", filter_options)
                
                # Apply filters
                filtered_data = st.session_state.cache_data
                if selected_filter == "Product Availability":
                    filtered_data = [item for item in filtered_data if item['type'] == "Product Availability"]
                elif selected_filter == "API Data":
                    filtered_data = [item for item in filtered_data if item['type'] == "API Data"]
                elif selected_filter == "Expired Only":
                    filtered_data = [item for item in filtered_data if item['is_expired']]
                elif selected_filter == "Valid Only":
                    filtered_data = [item for item in filtered_data if not item['is_expired']]
                
                # Create a dataframe for display
                cache_table = []
                for item in filtered_data:
                    status = "Expired" if item['is_expired'] else "Valid"
                    status_emoji = "⏱️" if item['is_expired'] else "✅"
                    
                    cache_table.append({
                        "Status": f"{status_emoji} {status}",
                        "Type": item['type'],
                        "Key": item['key'],
                        "Content": item['content'],
                        "Expires": item['expires_at']
                    })
                
                st.dataframe(
                    cache_table,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.text(f"Total: {len(filtered_data)} items")
            else:
                st.info("No cache data available.")
        
        with col2:
            st.subheader("Cache Actions")
            
            # Clear cache button
            if st.button("Clear All Cache", type="secondary"):
                try:
                    cache = Cache()
                    cache.clear()
                    st.success("Cache cleared successfully!")
                    # Reset session state to force refresh
                    if 'cache_data' in st.session_state:
                        del st.session_state.cache_data
                except Exception as e:
                    st.error(f"Error clearing cache: {e}")
            
            # Clear expired cache
            if st.button("Clear Expired Cache"):
                try:
                    count = 0
                    for item in st.session_state.get('cache_data', []):
                        if item['is_expired'] and os.path.exists(item['file_path']):
                            os.remove(item['file_path'])
                            count += 1
                    
                    if count > 0:
                        st.success(f"Cleared {count} expired cache items!")
                        # Reset session state to force refresh
                        if 'cache_data' in st.session_state:
                            del st.session_state.cache_data
                    else:
                        st.info("No expired cache items to clear.")
                except Exception as e:
                    st.error(f"Error clearing expired cache: {e}")
    
    with tab3:
        st.header("About End of Life Checker")
        
        st.markdown(
            """
            End of Life Checker helps developers identify outdated dependencies in their projects 
            that may pose security risks or compatibility issues. The tool scans project files to 
            detect dependencies and their versions, then checks them against the EOL data to provide 
            alerts and recommendations.
            
            ### Features
            
            - Support for multiple programming languages and frameworks:
              - Java (Maven, Gradle)
              - Node.js (npm, yarn)
              - Python (pip, poetry, pipenv)
            - Detailed reports showing:
              - Dependencies approaching EOL
              - Dependencies that have reached EOL
              - Recommended upgrade paths with breaking changes warnings
              - Status indicators (🔴 🟠 🟢 ❓)
            - Configurable warning thresholds
            - Export reports in multiple formats
            - Offline mode with cached EOL data
            
            ### Links
            
            - [GitHub Repository](https://github.com/yourlin/eol-check)
            - [endoflife.date](https://endoflife.date/)
            
            ### License
            
            MIT
            """
        )


def main():
    """Entry point for the UI."""
    import sys
    import subprocess
    import os
    
    # Get the path to the current script
    script_path = os.path.abspath(__file__)
    
    # Launch streamlit with the current script
    cmd = ["streamlit", "run", script_path]
    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("Error: Streamlit not found. Please install it with 'pip install streamlit numpy<2.0.0'")
        sys.exit(1)


if __name__ == "__main__":
    main()
