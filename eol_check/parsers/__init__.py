"""
Parsers for different project types.
"""

import os
from typing import List, Optional

from eol_check.parsers.base import BaseParser
from eol_check.parsers.java import MavenParser, GradleParser
from eol_check.parsers.nodejs import NpmParser, YarnParser
from eol_check.parsers.python import PipParser, PoetryParser, PipenvParser


def get_parsers_for_project(project_path: str) -> List[BaseParser]:
    """Get all appropriate parsers for a project.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        List of parser instances for the project
    """
    parsers = []
    
    # Check for Python projects
    if os.path.exists(os.path.join(project_path, "requirements.txt")):
        parsers.append(PipParser(project_path))
    
    if os.path.exists(os.path.join(project_path, "pyproject.toml")):
        parsers.append(PoetryParser(project_path))
    
    if os.path.exists(os.path.join(project_path, "Pipfile")):
        parsers.append(PipenvParser(project_path))
    
    # Check for Node.js projects
    if os.path.exists(os.path.join(project_path, "package.json")):
        if os.path.exists(os.path.join(project_path, "yarn.lock")):
            parsers.append(YarnParser(project_path))
        else:
            parsers.append(NpmParser(project_path))
    
    # Check for Java projects
    if os.path.exists(os.path.join(project_path, "pom.xml")):
        parsers.append(MavenParser(project_path))
    
    if os.path.exists(os.path.join(project_path, "build.gradle")):
        parsers.append(GradleParser(project_path))
    
    return parsers


def get_parser_for_project(project_path: str) -> Optional[BaseParser]:
    """Get the first appropriate parser for a project (legacy function).
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Parser instance or None if no parser is found
    """
    parsers = get_parsers_for_project(project_path)
    return parsers[0] if parsers else None
