"""
Check Project tab for the End of Life Checker UI.
"""

import os
import time
from datetime import datetime

import streamlit as st

from eol_check.core import EOLChecker
from eol_check.reporters import get_reporter
from eol_check.utils.logger import configure_logger
from eol_check.ui.utils.cache_utils import parse_cache_ttl


def render_check_project_tab():
    """Render the Check Project tab."""
    st.header("Check Project")

    # Project path input
    project_path = st.text_input(
        "Project Path :red[*]",
        value=os.getcwd(),
        help="Path to the project directory to check",
    )

    # Options section
    st.subheader("Options")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        threshold = st.slider(
            "Warning Threshold (days) :red[*]",
            min_value=1,
            max_value=365,
            value=90,
            help="Days before EOL to start warning",
        )

        format_options = ["text", "json", "csv", "html"]
        output_format = st.selectbox(
            "Output Format :red[*]",
            options=format_options,
            index=0,
            help="Format for the output report",
        )

        max_workers = st.number_input(
            "Max Workers :red[*]",
            min_value=1,
            max_value=32,
            value=8,
            help="Maximum number of parallel workers for API requests",
        )

    with col_b:
        offline_mode = st.checkbox(
            "Offline Mode",
            value=False,
            help="Use cached EOL data instead of fetching from endoflife.date",
        )

        force_update = st.checkbox(
            "Force Update", value=False, help="Force update of cached EOL data"
        )

        verbose = st.checkbox(
            "Verbose",
            value=True,
            help="Show detailed information about the checking process",
        )

    with col_c:
        ttl_options = {
            "30 days": "30d",
            "7 days": "7d",
            "3 days": "3d",
            "1 day": "1d",
            "12 hours": "12h",
            "6 hours": "6h",
            "1 hour": "1h",
            "30 minutes": "30m",
        }
        cache_ttl = st.selectbox(
            "Cache TTL :red[*]",
            options=list(ttl_options.keys()),
            index=3,
            help="Cache time-to-live duration",
        )
        cache_ttl_value = ttl_options[cache_ttl]

        # Ignore file
        ignore_file = st.text_input(
            "Ignore File",
            value="",
            help="Path to file containing dependencies to ignore (one per line)",
        )

        # Output file
        output_file = st.text_input(
            "Output File",
            value="",
            help="Save report to file instead of displaying in UI (optional)",
        )

    # Command preview and run button
    st.subheader("Run Check")

    col_cmd, col_btn = st.columns([3, 1])

    with col_cmd:
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

    with col_btn:
        run_button = st.button(
            "Run Check", type="primary", use_container_width=True
        )

    # Results section (displayed below the options)
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
                        st.metric(
                            "Critical",
                            critical_count,
                            delta=None,
                            delta_color="inverse",
                        )

                    with col_stats2:
                        st.metric(
                            "Warning",
                            warning_count,
                            delta=None,
                            delta_color="inverse",
                        )

                    with col_stats3:
                        st.metric("OK", ok_count, delta=None, delta_color="normal")

                    with col_stats4:
                        st.metric(
                            "Unknown", unknown_count, delta=None, delta_color="off"
                        )

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
                                "ERROR": "⚠️",
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
                            has_breaking = (
                                "⚠️" if dep.get("has_breaking_changes") else ""
                            )

                            table_data.append(
                                {
                                    "Status": f"{status_emoji} {status}",
                                    "Name": dep["name"],
                                    "Version": dep["version"],
                                    "EOL Date": eol_date,
                                    "Days Remaining": days_text,
                                    "Recommended": f"{recommended} {has_breaking}".strip(),
                                }
                            )

                        st.dataframe(
                            table_data,
                            use_container_width=True,
                            column_config={
                                "Status": st.column_config.TextColumn("Status"),
                                "Name": st.column_config.TextColumn("Name"),
                                "Version": st.column_config.TextColumn("Version"),
                                "EOL Date": st.column_config.TextColumn("EOL Date"),
                                "Days Remaining": st.column_config.TextColumn(
                                    "Days Remaining"
                                ),
                                "Recommended": st.column_config.TextColumn(
                                    "Recommended"
                                ),
                            },
                        )
                except Exception as e:
                    st.error(f"Error checking project: {e}")
                    if verbose:
                        import traceback

                        st.code(traceback.format_exc(), language="python")
