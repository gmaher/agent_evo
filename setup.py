"""Setup script for agent_evo CLI."""

from setuptools import setup, find_packages

setup(
    name="agent-evo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "pymongo>=4.0.0",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "evo-cli=agent_evo.cli.main:app",
        ],
    },
)