"""
Streamlit UI for the End of Life Checker.
This module is kept for backward compatibility.
The UI functionality has been moved to the eol_check.ui package.
"""

from eol_check.ui.main import run_ui, main

# Re-export for backward compatibility
__all__ = ["run_ui", "main"]
