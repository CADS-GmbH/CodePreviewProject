"""Setup configuration for squish-mcp CLI package."""

from setuptools import setup

setup(
    name="squish-mcp",
    version="0.1.0",
    description="CLI and server utilities for Squish MCP",
    py_modules=["cli", "config", "mcp_server"],
    install_requires=["click>=8.1.7,<9.0.0", "rich>=13.7.1,<14.0.0"],
    entry_points={"console_scripts": ["squish-mcp=cli:main"]},
)
