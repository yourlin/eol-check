"""
Main UI module for the End of Life Checker.
"""

import os
import sys
import subprocess
import streamlit as st

from eol_check.ui.tabs.check_project import render_check_project_tab
from eol_check.ui.tabs.cache_management import render_cache_management_tab
from eol_check.ui.tabs.about import render_about_tab

def run_ui():
    """Run the Streamlit UI."""
    # Set Streamlit page config - MUST be the first Streamlit command
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
        
        :red[*] Required fields
        """
    )

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Check Project", "Cache Management", "About"])

    with tab1:
        render_check_project_tab()

    with tab2:
        render_cache_management_tab()

    with tab3:
        render_about_tab()


def main():
    """Entry point for the UI."""
    try:
        # 直接尝试启动 Streamlit
        script_path = os.path.abspath(__file__)
        cmd = ["streamlit", "run", script_path]
        subprocess.run(cmd)

    except Exception as e:
        print(f"Error launching UI: {e}")


if __name__ == "__main__":
    run_ui()
