#!/usr/bin/env python
"""Setup script for GameCubeDays IceFuse Dashboard."""

from setuptools import setup, find_packages

# Read the requirements from requirements.txt
def read_requirements(filename="requirements.txt"):
    """Read requirements from a file."""
    try:
        with open(filename, "r") as req_file:
            return [line.strip() for line in req_file if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        # Fallback to basic requirements if requirements.txt doesn't exist
        return [
            "requests>=2.28.0",
            "beautifulsoup4>=4.11.0",
            "pandas>=1.5.0",
            "numpy>=1.23.0",
            "matplotlib>=3.6.0",
            "seaborn>=0.12.0",
            "plotly>=5.11.0",
            "python-dotenv>=0.21.0",
            "google-auth>=2.16.0",
            "google-auth-oauthlib>=0.8.0",
            "google-auth-httplib2>=0.1.0",
            "google-api-python-client>=2.70.0",
            "selenium>=4.7.0",
            "webdriver-manager>=3.8.0",
            "lxml>=4.9.0",
            "pytz>=2022.7",
            "schedule>=1.1.0",
        ]

# Read README for long description
def read_long_description():
    """Read the README file for long description."""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "GameCubeDays IceFuse Dashboard - A GMod server data analytics platform"

setup(
    name="gamecubedays-icefuse-dashboard",
    version="1.0.0",
    author="GameCubeDays",
    description="A GMod server data scraper, processor, and visualizer for player analytics",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/GameCubeDays/GameCubeDays-IceFuse-Dashboard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "black>=22.12.0",
            "flake8>=6.0.0",
            "mypy>=0.991",
            "pre-commit>=2.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "icefuse-dashboard=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.txt", "*.csv", "*.yaml", "*.yml"],
    },
    zip_safe=False,
)
