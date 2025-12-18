"""
Integration test fixtures for the unified ticket architecture.

Provides shared fixtures for testing:
- CLI command execution
- Ticket model interactions
- Basic test setup

Note: Complex isolated environments with full roadmap structures are not
practical due to the loader architecture expecting specific file patterns.
Tests should use CLI-based approaches or the actual project data.
"""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def roadmap_root(project_root):
    """Return the roadmap root directory."""
    return project_root / ".vibey" / "roadmap"


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()
