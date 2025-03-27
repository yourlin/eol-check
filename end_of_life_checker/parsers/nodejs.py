"""
Parsers for Node.js projects.
"""

import json
import os
import re
import subprocess
from typing import Dict, List, Any, Set

from end_of_life_checker.parsers.base import BaseParser


class NpmParser(BaseParser):
    """Parser for npm package.json files."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from package.json and npm list.
        
        Returns:
            List of dictionaries with dependency information
        """
        package_json_path = os.path.join(self.project_path, "package.json")
        dependencies = []
        
        # First parse direct dependencies from package.json
        direct_deps = self._parse_package_json(package_json_path)
        dependencies.extend(direct_deps)
        
        # Then try to get complete dependency tree using npm
        transitive_deps = self._get_npm_dependency_tree()
        if transitive_deps:
            # Add only new dependencies that aren't already in the list
            existing_names = {dep["name"] for dep in dependencies}
            for dep in transitive_deps:
                if dep["name"] not in existing_names:
                    dependencies.append(dep)
                    existing_names.add(dep["name"])
        
        return dependencies
    
    def _parse_package_json(self, package_json_path: str) -> List[Dict[str, Any]]:
        """Parse a package.json file.
        
        Args:
            package_json_path: Path to package.json file
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)
            
            # Parse regular dependencies
            deps = package_data.get("dependencies", {})
            for name, version in deps.items():
                # Clean up version string
                version = version.replace("^", "").replace("~", "")
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "nodejs",
                })
            
            # Parse dev dependencies
            dev_deps = package_data.get("devDependencies", {})
            for name, version in dev_deps.items():
                # Clean up version string
                version = version.replace("^", "").replace("~", "")
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "nodejs",
                    "dev": True,
                })
            
            # Check for Node.js version
            engines = package_data.get("engines", {})
            node_version = engines.get("node")
            if node_version:
                # Clean up version string
                node_version = node_version.replace(">=", "").replace("^", "").replace("~", "")
                
                dependencies.append({
                    "name": "node",
                    "version": node_version,
                    "type": "nodejs",
                })
        
        except Exception as e:
            print(f"Error parsing package.json: {e}")
        
        return dependencies
    
    def _get_npm_dependency_tree(self) -> List[Dict[str, Any]]:
        """Get complete dependency tree using npm.
        
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run npm list command in JSON format
            cmd = ["npm", "list", "--json", "--all"]
            # Don't use check=True here to handle non-zero exit codes gracefully
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True)
            
            # Check if the command was successful enough to produce valid JSON
            if result.stdout and result.stdout.strip():
                try:
                    # Parse the JSON output
                    npm_list = json.loads(result.stdout)
                    
                    # Process the dependency tree
                    self._process_npm_dependencies(npm_list, dependencies, processed_deps)
                    
                    return dependencies
                except json.JSONDecodeError as json_err:
                    print(f"Error parsing npm list output: {json_err}")
                    return []
            else:
                print("npm list command produced no output")
                return []
        except Exception as e:
            print(f"Error getting npm dependency tree: {e}")
            return []
    
    def _process_npm_dependencies(self, package_data: Dict, dependencies: List, processed_deps: Set, parent: str = None):
        """Process dependencies from npm list output recursively.
        
        Args:
            package_data: Package data from npm list
            dependencies: List to add dependencies to
            processed_deps: Set of already processed dependencies
            parent: Name of the parent package
        """
        # Skip the root package
        if parent is not None:
            name = package_data.get("name", "").split("@")[0]
            version = package_data.get("version")
            
            if name and version:
                # Create a unique key to avoid duplicates
                dep_key = f"{name}:{version}"
                if dep_key not in processed_deps:
                    processed_deps.add(dep_key)
                    
                    # Determine if it's a direct dependency
                    is_direct = parent is None or parent == package_data.get("name")
                    
                    dependencies.append({
                        "name": name,
                        "version": version,
                        "type": "nodejs",
                        "transitive": not is_direct
                    })
        
        # Process dependencies recursively
        deps = package_data.get("dependencies", {})
        for dep_name, dep_data in deps.items():
            self._process_npm_dependencies(dep_data, dependencies, processed_deps, 
                                          parent=package_data.get("name"))


class YarnParser(BaseParser):
    """Parser for Yarn projects."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from package.json, yarn.lock and yarn list.
        
        Returns:
            List of dictionaries with dependency information
        """
        # First get dependencies from package.json
        npm_parser = NpmParser(self.project_path)
        direct_deps = npm_parser._parse_package_json(os.path.join(self.project_path, "package.json"))
        dependencies = direct_deps
        
        # Then try to get more precise versions from yarn.lock
        self._update_from_yarn_lock(dependencies)
        
        # Then try to get complete dependency tree using yarn
        transitive_deps = self._get_yarn_dependency_tree()
        if transitive_deps:
            # Add only new dependencies that aren't already in the list
            existing_names = {dep["name"] for dep in dependencies}
            for dep in transitive_deps:
                if dep["name"] not in existing_names:
                    dependencies.append(dep)
                    existing_names.add(dep["name"])
        
        return dependencies
    
    def _update_from_yarn_lock(self, dependencies: List[Dict[str, Any]]):
        """Update dependency versions from yarn.lock.
        
        Args:
            dependencies: List of dependencies to update
        """
        yarn_lock_path = os.path.join(self.project_path, "yarn.lock")
        
        try:
            with open(yarn_lock_path, "r", encoding="utf-8") as f:
                yarn_lock_content = f.read()
            
            # Create a map of package names to versions
            version_map = {}
            
            # Parse yarn.lock
            package_blocks = re.split(r"\n\n", yarn_lock_content)
            for block in package_blocks:
                if not block.strip():
                    continue
                
                # Extract package name and version
                match = re.match(r'"?([^@\n]+)@[^"]*"?:', block)
                if match:
                    package_name = match.group(1)
                    version_match = re.search(r"version\s+\"([^\"]+)\"", block)
                    if version_match:
                        version = version_match.group(1)
                        version_map[package_name] = version
            
            # Update dependencies with more precise versions
            for dep in dependencies:
                if dep["name"] in version_map:
                    dep["version"] = version_map[dep["name"]]
        
        except Exception as e:
            print(f"Error parsing yarn.lock: {e}")
    
    def _get_yarn_dependency_tree(self) -> List[Dict[str, Any]]:
        """Get complete dependency tree using yarn.
        
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run yarn list command in JSON format
            cmd = ["yarn", "list", "--json", "--no-progress"]
            # Don't use check=True here to handle non-zero exit codes gracefully
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True)
            
            # Check if the command was successful enough to produce valid JSON
            if result.stdout and result.stdout.strip():
                try:
                    # Parse the JSON output
                    yarn_list = json.loads(result.stdout)
                    
                    # Process the dependency tree
                    for dep_data in yarn_list.get("data", {}).get("trees", []):
                        self._process_yarn_dependency(dep_data, dependencies, processed_deps)
                    
                    return dependencies
                except json.JSONDecodeError as json_err:
                    print(f"Error parsing yarn list output: {json_err}")
                    return []
            else:
                print("yarn list command produced no output")
                return []
        except Exception as e:
            print(f"Error getting yarn dependency tree: {e}")
            return []
    
    def _process_yarn_dependency(self, dep_data: str, dependencies: List, processed_deps: Set, is_direct: bool = True):
        """Process a dependency from yarn list output.
        
        Args:
            dep_data: Dependency data string from yarn list
            dependencies: List to add dependencies to
            processed_deps: Set of already processed dependencies
            is_direct: Whether this is a direct dependency
        """
        # Parse the dependency string
        # Format is usually: package@version [dependencies...]
        match = re.match(r"([^@]+)@([^@\s]+)", dep_data)
        if match:
            name, version = match.groups()
            
            # Create a unique key to avoid duplicates
            dep_key = f"{name}:{version}"
            if dep_key not in processed_deps:
                processed_deps.add(dep_key)
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "nodejs",
                    "transitive": not is_direct
                })
            
            # Process child dependencies
            child_deps = re.findall(r"└─\s+([^@]+@[^@\s]+)", dep_data)
            for child in child_deps:
                self._process_yarn_dependency(child, dependencies, processed_deps, is_direct=False)
