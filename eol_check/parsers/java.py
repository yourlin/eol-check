"""
Parsers for Java projects.
"""

import os
import re
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Set

from eol_check.parsers.base import BaseParser


class MavenParser(BaseParser):
    """Parser for Maven pom.xml files."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from pom.xml including transitive dependencies.
        
        Returns:
            List of dictionaries with dependency information
        """
        pom_path = os.path.join(self.project_path, "pom.xml")
        dependencies = []
        
        try:
            # Register namespaces
            ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            
            # Parse XML
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Extract Java version
            java_version = None
            java_elem = root.find(".//m:java.version", ns)
            if java_elem is not None:
                java_version = java_elem.text
            
            if java_version:
                dependencies.append({
                    "name": "java",
                    "version": java_version,
                    "type": "java",
                })
            
            # Try to get complete dependency tree using Maven
            maven_deps = self._get_maven_dependency_tree(pom_path)
            if maven_deps:
                dependencies.extend(maven_deps)
            else:
                # Fallback to basic parsing if Maven command fails
                basic_deps = self._parse_basic_dependencies(root, ns)
                dependencies.extend(basic_deps)
        
        except Exception as e:
            print(f"Error parsing pom.xml: {e}")
        
        return dependencies
    
    def _get_maven_dependency_tree(self, pom_path: str) -> List[Dict[str, Any]]:
        """Get complete dependency tree using Maven command.
        
        Args:
            pom_path: Path to pom.xml file
            
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run mvn dependency:tree command
            cmd = ["mvn", "dependency:tree", "-DoutputType=text", "-f", pom_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the dependency tree output
            for line in result.stdout.splitlines():
                # Skip non-dependency lines
                if not re.search(r'[+-\\|]', line):
                    continue
                    
                # Extract dependency information
                match = re.search(r'[+-\\|]\s+([^:]+):([^:]+):([^:]+):([^:]+)(?::([^:]+))?', line)
                if match:
                    groups = match.groups()
                    group_id = groups[0]
                    artifact_id = groups[1]
                    packaging = groups[2]
                    version = groups[3]
                    
                    # Create a unique key to avoid duplicates
                    dep_key = f"{group_id}:{artifact_id}:{version}"
                    if dep_key in processed_deps:
                        continue
                    
                    processed_deps.add(dep_key)
                    
                    # Determine if it's a direct or transitive dependency
                    is_direct = line.strip().startswith("+") or line.strip().startswith("\\")
                    
                    dependencies.append({
                        "name": artifact_id,
                        "version": version,
                        "type": "java",
                        "group_id": group_id,
                        "transitive": not is_direct
                    })
            
            return dependencies
        except Exception as e:
            print(f"Error getting Maven dependency tree: {e}")
            return []
    
    def _parse_basic_dependencies(self, root, ns) -> List[Dict[str, Any]]:
        """Parse basic dependencies from pom.xml as fallback.
        
        Args:
            root: XML root element
            ns: XML namespaces
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        # Extract properties for variable substitution
        properties = {}
        props_elem = root.find(".//m:properties", ns)
        if props_elem is not None:
            for prop in props_elem:
                tag = prop.tag.split("}")[-1]  # Remove namespace
                properties[tag] = prop.text
        
        # Extract parent POM information
        parent_elem = root.find(".//m:parent", ns)
        if parent_elem is not None:
            parent_group_id = parent_elem.find("m:groupId", ns)
            parent_artifact_id = parent_elem.find("m:artifactId", ns)
            parent_version = parent_elem.find("m:version", ns)
            
            if parent_group_id is not None and parent_artifact_id is not None and parent_version is not None:
                dependencies.append({
                    "name": parent_artifact_id.text,
                    "version": parent_version.text,
                    "type": "java",
                    "group_id": parent_group_id.text,
                    "is_parent": True
                })
        
        # Extract dependencies
        deps_elem = root.find(".//m:dependencies", ns)
        if deps_elem is not None:
            for dep in deps_elem.findall("m:dependency", ns):
                group_id = dep.find("m:groupId", ns)
                artifact_id = dep.find("m:artifactId", ns)
                version = dep.find("m:version", ns)
                
                if artifact_id is not None:
                    name = artifact_id.text
                    
                    # Get version, resolving property references if needed
                    version_str = "latest"
                    if version is not None:
                        version_str = version.text
                        
                        # Handle property references like ${version.spring}
                        if version_str.startswith("${") and version_str.endswith("}"):
                            prop_name = version_str[2:-1]
                            if prop_name in properties:
                                version_str = properties[prop_name]
                    
                    dependencies.append({
                        "name": name,
                        "version": version_str,
                        "type": "java",
                        "group_id": group_id.text if group_id is not None else None,
                    })
        
        return dependencies


class GradleParser(BaseParser):
    """Parser for Gradle build.gradle files."""
    
    def parse_dependencies(self) -> List[Dict[str, Any]]:
        """Parse dependencies from build.gradle including transitive dependencies.
        
        Returns:
            List of dictionaries with dependency information
        """
        gradle_path = os.path.join(self.project_path, "build.gradle")
        dependencies = []
        
        try:
            with open(gradle_path, "r", encoding="utf-8") as f:
                gradle_content = f.read()
            
            # Extract Java version
            java_version_match = re.search(r"sourceCompatibility\s*=\s*['\"]([^'\"]+)['\"]", gradle_content)
            if java_version_match:
                java_version = java_version_match.group(1)
                dependencies.append({
                    "name": "java",
                    "version": java_version,
                    "type": "java",
                })
            
            # Try to get complete dependency tree using Gradle
            gradle_deps = self._get_gradle_dependency_tree()
            if gradle_deps:
                dependencies.extend(gradle_deps)
            else:
                # Fallback to basic parsing if Gradle command fails
                basic_deps = self._parse_basic_dependencies(gradle_content)
                dependencies.extend(basic_deps)
        
        except Exception as e:
            print(f"Error parsing build.gradle: {e}")
        
        return dependencies
    
    def _get_gradle_dependency_tree(self) -> List[Dict[str, Any]]:
        """Get complete dependency tree using Gradle command.
        
        Returns:
            List of dependencies or empty list if command fails
        """
        dependencies = []
        processed_deps = set()  # To avoid duplicates
        
        try:
            # Run gradle dependencies command
            cmd = ["gradle", "dependencies", "--configuration", "runtimeClasspath"]
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, check=True)
            
            # Parse the dependency tree output
            for line in result.stdout.splitlines():
                # Skip non-dependency lines
                if not re.search(r'[+\\]---', line):
                    continue
                    
                # Extract dependency information
                match = re.search(r'[+\\]---\s+([^:]+):([^:]+):([^(\s]+)', line)
                if match:
                    group_id, artifact_id, version = match.groups()
                    
                    # Clean up version (remove any trailing characters)
                    version = version.strip()
                    
                    # Create a unique key to avoid duplicates
                    dep_key = f"{group_id}:{artifact_id}:{version}"
                    if dep_key in processed_deps:
                        continue
                    
                    processed_deps.add(dep_key)
                    
                    # Determine if it's a direct or transitive dependency
                    indent_level = len(line) - len(line.lstrip())
                    is_direct = indent_level <= 4  # Direct dependencies are at the top level
                    
                    dependencies.append({
                        "name": artifact_id,
                        "version": version,
                        "type": "java",
                        "group_id": group_id,
                        "transitive": not is_direct
                    })
            
            return dependencies
        except Exception as e:
            print(f"Error getting Gradle dependency tree: {e}")
            return []
    
    def _parse_basic_dependencies(self, gradle_content: str) -> List[Dict[str, Any]]:
        """Parse basic dependencies from build.gradle as fallback.
        
        Args:
            gradle_content: Content of build.gradle file
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        # Extract dependencies
        dep_block_match = re.search(r"dependencies\s*\{([^}]+)\}", gradle_content, re.DOTALL)
        if dep_block_match:
            dep_block = dep_block_match.group(1)
            
            # Find all dependency declarations
            dep_matches = re.finditer(r"(implementation|api|compile|runtime|testImplementation|testCompile)\s*['\"]([^'\"]+)['\"]", dep_block)
            
            for match in dep_matches:
                dep_type = match.group(1)
                dep_str = match.group(2)
                
                # Parse group:artifact:version format
                parts = dep_str.split(":")
                if len(parts) >= 3:
                    group_id = parts[0]
                    artifact_id = parts[1]
                    version = parts[2]
                    
                    dependencies.append({
                        "name": artifact_id,
                        "version": version,
                        "type": "java",
                        "group_id": group_id,
                        "dev": dep_type.startswith("test"),
                    })
        
        return dependencies
