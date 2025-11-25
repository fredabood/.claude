"""
Vibey Content Package.

Contains the framework content (agents, workflows, templates, schemas, examples)
that can be deployed to target projects.

This module provides accessor functions to get paths to content directories,
which work correctly for both:
- Editable installs (pip install -e .)
- Regular pip installs

Usage:
    from vibey.content import get_content_root, get_agents_dir

    # Get path to content root
    content_root = get_content_root()

    # Get path to agents directory
    agents_dir = get_agents_dir()

    # Iterate over agent files
    for agent_file in agents_dir.rglob('*.md'):
        print(agent_file.name)
"""

from pathlib import Path
from typing import Optional
import sys

# Cache for content root path
_content_root: Optional[Path] = None


def get_content_root() -> Path:
    """
    Get the root path to the content directory.

    Works for both editable installs and regular pip installs
    by using __file__ to locate the package.

    Returns:
        Path to the vibey/content/ directory
    """
    global _content_root
    if _content_root is None:
        # __file__ is vibey/content/__init__.py
        # So parent is vibey/content/
        _content_root = Path(__file__).parent
    return _content_root


def get_agents_dir() -> Path:
    """
    Get the path to the agents directory.

    Returns:
        Path to vibey/content/agents/
    """
    return get_content_root() / 'agents'


def get_workflows_dir() -> Path:
    """
    Get the path to the workflows directory.

    Returns:
        Path to vibey/content/workflows/
    """
    return get_content_root() / 'workflows'


def get_templates_dir() -> Path:
    """
    Get the path to the templates directory.

    Returns:
        Path to vibey/content/templates/
    """
    return get_content_root() / 'templates'


def get_schemas_dir() -> Path:
    """
    Get the path to the schemas directory.

    Returns:
        Path to vibey/content/schemas/
    """
    return get_content_root() / 'schemas'


def get_examples_dir() -> Path:
    """
    Get the path to the examples directory.

    Returns:
        Path to vibey/content/examples/
    """
    return get_content_root() / 'examples'


def get_config_dir() -> Path:
    """
    Get the path to the config directory.

    Returns:
        Path to vibey/content/config/
    """
    return get_content_root() / 'config'


# Export public API
__all__ = [
    'get_content_root',
    'get_agents_dir',
    'get_workflows_dir',
    'get_templates_dir',
    'get_schemas_dir',
    'get_examples_dir',
    'get_config_dir',
]
