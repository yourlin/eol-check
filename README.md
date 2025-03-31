# End of Life Checker

[English](README.md) | [中文](README_zh.md)

A command-line tool to check the end-of-life (EOL) status of software dependencies in your projects by comparing them with data from [endoflife.date](https://endoflife.date/).

> **Special Note**: This tool was developed entirely with the assistance of Amazon Q CLI, showcasing the capabilities of AI-assisted development.

## Overview

End of Life Checker helps developers identify outdated dependencies in their projects that may pose security risks or compatibility issues. The tool scans project files to detect dependencies and their versions, then checks them against the EOL data to provide alerts and recommendations.

## Requirements

- Python 3.8 or higher
- Required packages (automatically installed):
  - requests>=2.25.0
  - toml>=0.10.2
  - streamlit>=1.22.0
  - numpy<2.0.0

## Features

- Support for multiple programming languages and frameworks:
  - Java (Maven, Gradle)
    - Complete dependency tree analysis including transitive dependencies
    - Parent POM inheritance support
    - Dependency management resolution
  - Node.js (npm, yarn)
  - Python (pip, poetry, pipenv)
- Command-line interface for easy integration into CI/CD pipelines
- Graphical user interface for interactive usage
- Detailed reports showing:
  - Dependencies approaching EOL
  - Dependencies that have reached EOL
  - Recommended upgrade paths with breaking changes warnings (⚠️)
  - Beautiful emoji-based status indicators (🔴 🟠 🟢 ❓)
  - Execution time and progress tracking
  - Project name and full path information
- Configurable warning thresholds (e.g., alert 90 days before EOL)
- Export reports in multiple formats (JSON, CSV, HTML)
- Offline mode with cached EOL data

## Installation

### From PyPI (Recommended)

```bash
pip install eol-check
```

### From Source

For the latest development version or to contribute to the project:

```bash
# Clone the repository
git clone https://github.com/yourlin/eol-check.git
cd eol-check

# Install in development mode
pip install -e .
```

Installing from source allows you to modify the code and immediately see the effects without reinstalling.

### Publishing to PyPI

For maintainers who want to publish a new version to PyPI:

```bash
# Update version in setup.py first
python -m build
twine check dist/*
twine upload dist/*
```

Alternatively, create a new release on GitHub to trigger the automated publishing workflow.

## Usage

Basic usage:

```bash
eol-check /path/to/project
```

With options:

```bash
eol-check /path/to/project --format json --output report.json --threshold 180
```

Launch the graphical user interface:

```bash
eol-check --ui
```

## Options

- `--format`: Output format (text, json, csv, html). Default: text
- `--output`: Save report to file instead of stdout
- `--threshold`: Days before EOL to start warning. Default: 90
- `--offline`: Use cached EOL data instead of fetching from endoflife.date
- `--update`: Force update of cached EOL data
- `--cache-ttl`: Cache time-to-live duration. Default: 1d. Formats: '1d' (1 day), '12h' (12 hours), '30m' (30 minutes)
- `--verbose`: Show detailed information about the checking process, including API availability messages and debug output
- `--ignore-file`: Path to file containing dependencies to ignore (one dependency name per line)
- `--max-workers`: Maximum number of parallel workers for API requests (default: CPU count * 2)
- `--ui`: Launch the graphical user interface

### Ignore File Format

The ignore file should contain one dependency name per line. Comments can be added using the `#` character.

Example `ignore.txt`:
```
# These dependencies are internal and don't need EOL checking
internal-lib
legacy-component
# This one has a custom support contract
enterprise-framework
```

## Supported Project Types

- Java: pom.xml, build.gradle
  - Requires Maven/Gradle installed for complete dependency analysis
  - Falls back to basic parsing if build tools are not available
- Node.js: package.json, package-lock.json, yarn.lock
  - Requires npm/yarn installed for complete dependency analysis
  - Falls back to basic parsing if build tools are not available
- Python: requirements.txt, Pipfile, pyproject.toml
  - Requires pip/poetry/pipenv installed for complete dependency analysis
  - Falls back to basic parsing if build tools are not available

## Advanced Features

### Breaking Changes Detection

The tool automatically detects when a recommended upgrade involves a major version change (e.g., upgrading from 2.x to 3.x) and marks these with a warning emoji (⚠️) to indicate potential breaking changes.

### Transitive Dependency Analysis

For Java projects, the tool analyzes the complete dependency tree including:
- Direct dependencies declared in your project
- Transitive dependencies pulled in by your direct dependencies
- Dependencies managed by parent POMs
- Dependencies from dependency management sections

This ensures you get alerts about EOL status for all libraries your application actually uses, not just the ones you directly declare.

### Graphical User Interface

The tool provides a user-friendly Streamlit-based GUI that can be launched with the `--ui` parameter:
- Project selection and scanning
- Interactive dependency analysis results
- Cache management interface
- About section with project information

The GUI makes it easy for non-technical users to check their project dependencies without needing to use command-line options.

### CI/CD Integration

The tool is designed to be easily integrated into CI/CD pipelines:
- Exit code 0: No issues found
- Exit code 1: Error running the tool
- Exit code 2: Critical issues found (dependencies that have reached EOL)

This allows you to fail builds or trigger alerts when critical dependencies are detected.

Example integration with GitHub Actions:
```yaml
name: Check Dependencies EOL

on:
  schedule:
    - cron: '0 8 * * 1'  # Run every Monday at 8:00 AM
  workflow_dispatch:  # Allow manual trigger

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install eol-check
        run: pip install eol-check
        
      - name: Check dependencies
        run: eol-check . --format json --output eol-report.json
        
      - name: Upload report as artifact
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: eol-report
          path: eol-report.json
```

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Symptom: Slow performance or errors about "too many requests"
   - Solution: Use the `--max-workers` option to reduce the number of parallel requests, or use `--offline` mode with cached data

2. **Missing Dependencies**
   - Symptom: The tool doesn't detect all dependencies you expect
   - Solution: Make sure you're using the right build tool (Maven, npm, etc.) and that it's properly installed. The tool falls back to basic parsing if build tools aren't available.

3. **Unknown EOL Status**
   - Symptom: Many dependencies show as "UNKNOWN" status
   - Solution: The endoflife.date API might not have data for those dependencies. Consider contributing to the endoflife.date project.

### Verbose Mode

Use the `--verbose` flag to get more detailed information about what's happening:
- API request details and responses
- Cache usage information
- Dependency resolution process
- Detailed error messages and stack traces

This is particularly useful when troubleshooting issues or when you want to understand how the tool is processing your project.

## License

MIT
