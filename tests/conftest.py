"""
Shared pytest fixtures and configuration for Vibey framework tests.

This module provides common fixtures used across all test suites including:
- Temporary directory management
- Mock repository setup
- Test data fixtures
- Common test utilities
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test isolation.

    Yields:
        Path to temporary directory, automatically cleaned up after test.
    """
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_repo_path(temp_dir: Path) -> Path:
    """
    Create a mock repository path within temp directory.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to mock repository location
    """
    repo_path = temp_dir / "mock-repo"
    repo_path.mkdir(parents=True, exist_ok=True)
    return repo_path


@pytest.fixture
def vibey_test_config() -> dict:
    """
    Provide test configuration for Vibey framework.

    Returns:
        Dictionary with test configuration values
    """
    return {
        "framework_version": "1.3.0",
        "test_mode": True,
        "mock_git": True,
        "skip_external_calls": True,
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment variables before each test.

    Automatically used for all tests to ensure clean state.
    """
    # Store original environment
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["VIBEY_TEST_MODE"] = "1"
    os.environ["VIBEY_SKIP_GIT_HOOKS"] = "1"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_yaml_config() -> str:
    """
    Provide sample YAML configuration for testing.

    Returns:
        YAML configuration string
    """
    return """
project:
  name: test-project
  type: web-app
  version: 1.0.0

framework:
  orchestration_mode: balanced
  quality_gates_enabled: true

agents:
  - web-developer
  - test-engineer
"""


@pytest.fixture
def sample_roadmap_state() -> dict:
    """
    Provide sample roadmap state for testing.

    Returns:
        Dictionary representing roadmap state
    """
    return {
        "roadmap_id": "test-roadmap",
        "tracks_total": 1,
        "tracks_completed": 0,
        "sprints_total": 1,
        "sprints_completed": 0,
        "tasks_total": 5,
        "tasks_completed": 0,
    }


def pytest_configure(config):
    """
    Configure pytest with custom settings.

    Args:
        config: pytest configuration object
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions/classes"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for workflows"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests for complete user journeys"
    )
    config.addinivalue_line(
        "markers", "platform: Platform-specific tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time to run"
    )
    config.addinivalue_line(
        "markers", "requires_git: Tests that require git to be installed"
    )
