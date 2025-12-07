"""
Entry point for running vibey CLI as a module.

Usage: python -m vibey.cli [command]

This file allows clean module execution without RuntimeWarning.
"""

from vibey.cli.main import cli

if __name__ == "__main__":
    cli()
