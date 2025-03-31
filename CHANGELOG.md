# Changelog

## [0.2.0] - 2025-03-31

### Added
- Streamlit-based graphical user interface with `--ui` parameter
- Project scanning and dependency analysis in the UI
- Cache management interface in the UI
- About section with project information

### Fixed
- Fixed Streamlit page configuration initialization
- Fixed NumPy compatibility issues with PyArrow
- Fixed incorrectly identifying 'unknown' status as 'up to date' in result report
- Improved UI launcher to handle both direct and streamlit run modes

### Changed
- Optimized UI layout and user experience
- Updated dependency requirements

## [0.1.1] - Initial Release

### Added
- Initial release of End of Life Checker
- Support for Java, Node.js, and Python projects
- Command-line interface
- Multiple output formats (text, JSON, CSV, HTML)
- Configurable warning thresholds
- Offline mode with cached EOL data
