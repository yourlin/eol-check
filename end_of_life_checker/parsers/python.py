"""
Parsers for Python projects.
"""

import json
import os
import re
import subprocess
from typing import Dict, List, Any, Set

import toml

from end_of_life_checker.parsers.base import BaseParser


class PipParser(BaseParser):
    """Parser for pip requirements.txt files."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from requirements.txt.
        
        Returns:
            List of dictionaries with dependency information
        """
        requirements_path = os.path.join(self.project_path, "requirements.txt")
        dependencies = []
        
        # First parse direct dependencies from requirements.txt
        direct_deps = self._parse_requirements_file(requirements_path)
        dependencies.extend(direct_deps)
        
        # Then try to get complete dependency tree using pip
        transitive_deps = self._get_pip_dependency_tree()
        if transitive_deps:
            # Add only new dependencies that aren't already in the list
            existing_names = {dep["name"] for dep in dependencies}
            for dep in transitive_deps:
                if dep["name"] not in existing_names:
                    dependencies.append(dep)
                    existing_names.add(dep["name"])
        
        return dependencies
    
    def _parse_requirements_file(self, requirements_path: str) -> List[Dict[str, Any]]:
        """Parse a requirements.txt file.
        
        Args:
            requirements_path: Path to requirements.txt file
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        try:
            with open(requirements_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    
                    # Skip options and editable installs
                    if line.startswith("-") or line.startswith("--"):
                        continue
                    
                    # Parse package name and version
                    match = re.match(r"([a-zA-Z0-9_.-]+)([<>=!~]+)([a-zA-Z0-9_.-]+)", line)
                    if match:
                        name, operator, version = match.groups()
                        dependencies.append({
                            "name": name.strip(),
                            "version": version.strip(),
                            "type": "python",
                        })
                    else:
                        # Just package name without version
                        name = line.split("#")[0].strip()  # Remove inline comments
                        if name:
                            dependencies.append({
                                "name": name,
                                "version": "latest",
                                "type": "python",
                            })
        except Exception as e:
            print(f"Error parsing requirements.txt: {e}")
        
        return dependencies
    
    def _get_pip_dependency_tree(self) -> List[Dict[str, Any]]:
        """Get complete dependency tree using pip.
        
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run pip list command in JSON format
            cmd = ["pip", "list", "--format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the JSON output
            packages = json.loads(result.stdout)
            
            for package in packages:
                name = package.get("name")
                version = package.get("version")
                
                if name and version:
                    # Create a unique key to avoid duplicates
                    dep_key = f"{name}:{version}"
                    if dep_key in processed_deps:
                        continue
                    
                    processed_deps.add(dep_key)
                    
                    # Try to determine if it's a direct or transitive dependency
                    # This is an approximation since pip doesn't provide this info directly
                    is_direct = self._is_direct_dependency(name)
                    
                    dependencies.append({
                        "name": name,
                        "version": version,
                        "type": "python",
                        "transitive": not is_direct
                    })
            
            return dependencies
        except Exception as e:
            print(f"Error getting pip dependency tree: {e}")
            return []
    
    def _is_direct_dependency(self, package_name: str) -> bool:
        """Check if a package is a direct dependency.
        
        Args:
            package_name: Package name
            
        Returns:
            True if it's a direct dependency, False otherwise
        """
        requirements_path = os.path.join(self.project_path, "requirements.txt")
        try:
            with open(requirements_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Simple check: if the package name appears in requirements.txt
                # This is not perfect but a reasonable approximation
                return re.search(rf"\b{re.escape(package_name)}\b", content) is not None
        except Exception:
            return False


class PoetryParser(BaseParser):
    """Parser for Poetry pyproject.toml files."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from pyproject.toml.
        
        Returns:
            List of dictionaries with dependency information
        """
        pyproject_path = os.path.join(self.project_path, "pyproject.toml")
        dependencies = []
        
        # First parse direct dependencies from pyproject.toml
        direct_deps = self._parse_pyproject_toml(pyproject_path)
        dependencies.extend(direct_deps)
        
        # Then try to get complete dependency tree using poetry
        transitive_deps = self._get_poetry_dependency_tree()
        if transitive_deps:
            # Add only new dependencies that aren't already in the list
            existing_names = {dep["name"] for dep in dependencies}
            for dep in transitive_deps:
                if dep["name"] not in existing_names:
                    dependencies.append(dep)
                    existing_names.add(dep["name"])
        
        return dependencies
    
    def _parse_pyproject_toml(self, pyproject_path: str) -> List[Dict[str, Any]]:
        """Parse a pyproject.toml file.
        
        Args:
            pyproject_path: Path to pyproject.toml file
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                pyproject = toml.load(f)
            
            # Get dependencies
            deps = pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for name, version_info in deps.items():
                if name == "python":
                    continue  # Skip Python itself
                
                if isinstance(version_info, str):
                    version = version_info
                elif isinstance(version_info, dict):
                    version = version_info.get("version", "latest")
                else:
                    version = "latest"
                
                # Clean up version string
                version = version.replace("^", "").replace("~", "")
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "python",
                })
            
            # Get dev dependencies
            dev_deps = pyproject.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})
            for name, version_info in dev_deps.items():
                if isinstance(version_info, str):
                    version = version_info
                elif isinstance(version_info, dict):
                    version = version_info.get("version", "latest")
                else:
                    version = "latest"
                
                # Clean up version string
                version = version.replace("^", "").replace("~", "")
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "python",
                    "dev": True,
                })
        
        except Exception as e:
            print(f"Error parsing pyproject.toml: {e}")
        
        return dependencies
    
    def _get_poetry_dependency_tree(self) -> List[Dict[str, Any]]:
        """Get complete dependency tree using poetry.
        
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run poetry show command
            cmd = ["poetry", "show", "--no-ansi"]
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, check=True)
            
            # Parse the output
            lines = result.stdout.splitlines()
            current_package = None
            is_direct = True
            
            for line in lines:
                # New package entry starts with a name and version
                package_match = re.match(r"^([a-zA-Z0-9_.-]+)\s+([0-9a-zA-Z.-]+)", line)
                if package_match:
                    name, version = package_match.groups()
                    current_package = name
                    
                    # Create a unique key to avoid duplicates
                    dep_key = f"{name}:{version}"
                    if dep_key not in processed_deps:
                        processed_deps.add(dep_key)
                        dependencies.append({
                            "name": name,
                            "version": version,
                            "type": "python",
                            "transitive": False  # Direct dependency
                        })
                
                # Dependencies of the current package
                elif current_package and "└──" in line or "├──" in line:
                    dep_match = re.search(r"[└├]──\s+([a-zA-Z0-9_.-]+)\s+([0-9a-zA-Z.-]+)", line)
                    if dep_match:
                        name, version = dep_match.groups()
                        
                        # Create a unique key to avoid duplicates
                        dep_key = f"{name}:{version}"
                        if dep_key not in processed_deps:
                            processed_deps.add(dep_key)
                            dependencies.append({
                                "name": name,
                                "version": version,
                                "type": "python",
                                "transitive": True  # Transitive dependency
                            })
            
            return dependencies
        except Exception as e:
            print(f"Error getting poetry dependency tree: {e}")
            return []


class PipenvParser(BaseParser):
    """Parser for Pipenv Pipfile files."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from Pipfile.
        
        Returns:
            List of dictionaries with dependency information
        """
        pipfile_path = os.path.join(self.project_path, "Pipfile")
        dependencies = []
        
        # First parse direct dependencies from Pipfile
        direct_deps = self._parse_pipfile(pipfile_path)
        dependencies.extend(direct_deps)
        
        # Then try to get complete dependency tree using pipenv
        transitive_deps = self._get_pipenv_dependency_tree()
        if transitive_deps:
            # Add only new dependencies that aren't already in the list
            existing_names = {dep["name"] for dep in dependencies}
            for dep in transitive_deps:
                if dep["name"] not in existing_names:
                    dependencies.append(dep)
                    existing_names.add(dep["name"])
        
        return dependencies
    
    def _parse_pipfile(self, pipfile_path: str) -> List[Dict[str, Any]]:
        """Parse a Pipfile.
        
        Args:
            pipfile_path: Path to Pipfile
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        try:
            with open(pipfile_path, "r", encoding="utf-8") as f:
                pipfile = toml.load(f)
            
            # Get regular dependencies
            deps = pipfile.get("packages", {})
            for name, version_info in deps.items():
                if isinstance(version_info, str):
                    version = version_info
                elif isinstance(version_info, dict):
                    version = version_info.get("version", "latest")
                else:
                    version = "latest"
                
                # Clean up version string
                version = version.replace("==", "").replace(">=", "").replace("~=", "")
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "python",
                })
            
            # Get dev dependencies
            dev_deps = pipfile.get("dev-packages", {})
            for name, version_info in dev_deps.items():
                if isinstance(version_info, str):
                    version = version_info
                elif isinstance(version_info, dict):
                    version = version_info.get("version", "latest")
                else:
                    version = "latest"
                
                # Clean up version string
                version = version.replace("==", "").replace(">=", "").replace("~=", "")
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "python",
                    "dev": True,
                })
        
        except Exception as e:
            print(f"Error parsing Pipfile: {e}")
        
        return dependencies
    
    def _get_pipenv_dependency_tree(self) -> List[Dict[str, Any]]:
        """Get complete dependency tree using pipenv.
        
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run pipenv graph command
            cmd = ["pipenv", "graph", "--json"]
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, check=True)
            
            # Parse the JSON output
            packages = json.loads(result.stdout)
            
            # Process the dependency tree
            for package in packages:
                self._process_pipenv_package(package, dependencies, processed_deps, is_direct=True)
            
            return dependencies
        except Exception as e:
            print(f"Error getting pipenv dependency tree: {e}")
            return []
    
    def _process_pipenv_package(self, package: Dict, dependencies: List, processed_deps: Set, is_direct: bool = False):
        """Process a package from pipenv graph output.
        
        Args:
            package: Package information
            dependencies: List to add dependencies to
            processed_deps: Set of already processed dependencies
            is_direct: Whether this is a direct dependency
        """
        name = package.get("package", {}).get("key", "")
        version = package.get("package", {}).get("installed", "")
        
        if name and version:
            # Create a unique key to avoid duplicates
            dep_key = f"{name}:{version}"
            if dep_key not in processed_deps:
                processed_deps.add(dep_key)
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "python",
                    "transitive": not is_direct
                })
        
        # Process dependencies recursively
        for dep in package.get("dependencies", []):
            self._process_pipenv_package(dep, dependencies, processed_deps, is_direct=False)
