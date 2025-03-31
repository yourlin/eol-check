"""
About tab for the End of Life Checker UI.
"""

import streamlit as st

def render_about_tab():
    """Render the About tab."""
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
