#!/usr/bin/env python3
"""
Setup script for End of Life Checker.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="end-of-life-checker",
    version="0.1.0",
    author="End of Life Checker Team",
    author_email="info@example.com",
    description="A tool to check the end-of-life status of software dependencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/end-of-life-checker",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/end-of-life-checker/issues",
        "Documentation": "https://github.com/yourusername/end-of-life-checker",
        "Source Code": "https://github.com/yourusername/end-of-life-checker",
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Software Distribution",
    ],
    keywords="dependency, eol, end-of-life, security, maintenance, java, python, nodejs",
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "toml>=0.10.2",
    ],
    entry_points={
        "console_scripts": [
            "eol-check=end_of_life_checker.cli:main",
        ],
    },
)
