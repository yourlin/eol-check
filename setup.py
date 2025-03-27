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
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
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
