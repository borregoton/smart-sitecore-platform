"""
Smart Sitecore CLI Setup
Project20 v2.0 - Real Data Only

Installation:
    pip install -e .

Usage:
    smart-sitecore --help
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open("../README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Smart Sitecore Health Assessment CLI - Real Data Only"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []

setup(
    name="smart-sitecore-cli",
    version="2.0.0",
    author="Smart Platform Team",
    author_email="info@smartplatform.dev",
    description="Smart Sitecore Health Assessment CLI - Real Data Only",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/smart-sitecore-cli",

    packages=find_packages(),
    include_package_data=True,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.8",
    install_requires=read_requirements(),

    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0"
        ],
        "reporting": [
            "jinja2>=3.1.0",
            "weasyprint>=59.0",
            "matplotlib>=3.6.0",
            "plotly>=5.15.0"
        ]
    },

    entry_points={
        "console_scripts": [
            "smart-sitecore=smart_sitecore.cli:cli",
        ],
    },

    project_urls={
        "Bug Reports": "https://github.com/your-org/smart-sitecore-cli/issues",
        "Source": "https://github.com/your-org/smart-sitecore-cli",
        "Documentation": "https://docs.smartplatform.dev",
    },

    keywords=[
        "sitecore",
        "cms",
        "health-check",
        "analysis",
        "performance",
        "seo",
        "security",
        "content-management",
        "graphql",
        "cli"
    ],

    package_data={
        "smart_sitecore": [
            "templates/*.html",
            "templates/*.css",
            "config/*.json"
        ]
    },
)