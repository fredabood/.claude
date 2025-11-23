"""
Goose Platform Adapter.

Composes MCPAdapter for tool generation, adds Goose-specific features:
- Recipe generation from workflows
- Extension manifest generation
- Goose-specific configuration
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ..base import CompositeAdapter
from ..mcp import MCPAdapter
from ..types import ExportResult, PlatformCapabilities
from .recipes import RecipeGenerator
from .manifest import ManifestGenerator

logger = logging.getLogger(__name__)


class GooseAdapter(CompositeAdapter):
    """
    Goose platform adapter.

    Composes MCPAdapter for MCP tools and adds Goose-specific features:
    - Recipes generated from workflow frontmatter
    - Extension manifest for Goose registration
    - Goose-specific configuration files

    Example:
        >>> mcp_adapter = MCPAdapter(root_dir=Path('.'))
        >>> goose = GooseAdapter(mcp_adapter)
        >>>
        >>> # Tools delegated to MCPAdapter (no duplication)
        >>> tools = goose.get_tools()
        >>>
        >>> # Goose-specific: recipes
        >>> recipes = goose.get_recipes()
        >>>
        >>> # Export everything
        >>> result = goose.export(Path('./goose-export'))
    """

    platform_name = "goose"
    display_name = "Goose (Block)"
    description = "Goose AI agent framework with MCP tools and recipes"

    def __init__(self, mcp_adapter: MCPAdapter):
        """
        Initialize Goose adapter.

        Args:
            mcp_adapter: MCPAdapter instance for tool generation
        """
        super().__init__(mcp_adapter)

        # Goose-specific generators
        self._recipe_generator = RecipeGenerator(
            tool_prefix=mcp_adapter.tool_prefix
        )
        self._manifest_generator = ManifestGenerator()

        # Cache
        self._recipes_cache: List[Dict[str, Any]] = None

    @property
    def capabilities(self) -> PlatformCapabilities:
        """Goose capabilities (extends MCP capabilities)."""
        return PlatformCapabilities(
            agents=True,
            workflows=True,
            handoffs=False,
            real_time_discovery=True,
            recipes=True,  # Goose-specific
            extension_manifest=True,  # Goose-specific
        )

    @property
    def mcp_adapter(self) -> MCPAdapter:
        """Get the underlying MCP adapter."""
        return self._base

    def get_recipes(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all Goose recipes.

        Recipes are generated from workflow frontmatter and reference
        MCP tools by name.

        Args:
            force_refresh: Force regeneration

        Returns:
            List of Goose recipe dicts
        """
        if self._recipes_cache is None or force_refresh:
            workflows = self.mcp_adapter.get_workflows()
            self._recipes_cache = self._recipe_generator.generate_all(workflows)

        return self._recipes_cache

    def get_recipe_by_id(self, recipe_id: str) -> Dict[str, Any]:
        """
        Get a specific recipe by ID.

        Args:
            recipe_id: Recipe identifier

        Returns:
            Recipe dict or None
        """
        for recipe in self.get_recipes():
            if recipe.get('id') == recipe_id:
                return recipe
        return None

    def get_extension_manifest(self) -> Dict[str, Any]:
        """
        Get Goose extension manifest.

        Returns:
            Extension manifest dict
        """
        tools = self.get_tools()
        recipes = self.get_recipes()

        agent_count = len([t for t in tools if t.get('_metadata', {}).get('asset_type') == 'agent'])
        workflow_count = len([t for t in tools if t.get('_metadata', {}).get('asset_type') == 'workflow'])

        return self._manifest_generator.generate(
            tools_count=len(tools),
            agent_count=agent_count,
            workflow_count=workflow_count,
            recipe_count=len(recipes),
        )

    def export(self, output_dir: Path) -> ExportResult:
        """
        Export Goose-specific files.

        Creates:
        - goose-extension.yaml: Extension manifest
        - recipes/: Directory of recipe YAML files

        Args:
            output_dir: Directory to write files

        Returns:
            ExportResult with created files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        files = []
        errors = []
        warnings = []

        try:
            # Export extension manifest
            manifest = self.get_extension_manifest()
            manifest_path = output_dir / "goose-extension.yaml"
            manifest_path.write_text(
                yaml.dump(manifest, default_flow_style=False, sort_keys=False)
            )
            files.append(manifest_path)
            logger.info(f"Exported extension manifest to {manifest_path}")

            # Export recipes
            recipes_dir = output_dir / "recipes"
            recipes_dir.mkdir(parents=True, exist_ok=True)

            recipes = self.get_recipes()
            for recipe in recipes:
                recipe_id = recipe.get('id', 'unknown')
                recipe_path = recipes_dir / f"{recipe_id}.yaml"
                recipe_path.write_text(
                    yaml.dump(recipe, default_flow_style=False, sort_keys=False)
                )
                files.append(recipe_path)

            logger.info(f"Exported {len(recipes)} recipes to {recipes_dir}")

            # Export MCP tools (via base adapter)
            mcp_result = self.mcp_adapter.export(output_dir / "mcp")
            files.extend(mcp_result.files)
            errors.extend(mcp_result.errors)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            errors.append(str(e))

        return ExportResult(
            platform=self.platform_name,
            files=files,
            errors=errors,
            warnings=warnings,
        )

    def invalidate_cache(self) -> None:
        """Invalidate all caches."""
        self._recipes_cache = None
        self.mcp_adapter.invalidate_cache()

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        mcp_stats = self.mcp_adapter.get_stats()
        return {
            **mcp_stats,
            "recipes": len(self.get_recipes()),
            "platform": self.platform_name,
        }
