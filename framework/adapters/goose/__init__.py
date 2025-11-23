"""
Goose Platform Adapter.

Generates Goose recipes and extension manifest from Vibey assets.
Composes MCPAdapter for tool generation.
"""

from .adapter import GooseAdapter
from .recipes import RecipeGenerator
from .manifest import ManifestGenerator

__all__ = ["GooseAdapter", "RecipeGenerator", "ManifestGenerator"]
