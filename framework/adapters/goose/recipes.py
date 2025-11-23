"""
Goose Recipe Generator.

Translates Vibey workflow definitions into Goose recipe format.
Recipes reference MCP tools by name for zero duplication.
"""

import logging
from typing import Any, Dict, List

from framework.mcp.discovery import WorkflowDefinition

logger = logging.getLogger(__name__)


class RecipeGenerator:
    """
    Generate Goose recipes from Vibey workflows.

    Goose recipes are YAML-based workflow definitions that orchestrate
    multiple tools. This generator creates recipes that reference
    Vibey MCP tools by name.

    Example:
        >>> generator = RecipeGenerator(tool_prefix="vibey")
        >>> recipes = generator.generate_all(workflows)
        >>> for recipe in recipes:
        ...     print(f"{recipe['id']}: {len(recipe['steps'])} steps")
    """

    def __init__(self, tool_prefix: str = "vibey"):
        """
        Initialize recipe generator.

        Args:
            tool_prefix: Prefix used for MCP tools (default: "vibey")
        """
        self.tool_prefix = tool_prefix

    def generate_recipe(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """
        Generate a Goose recipe from a workflow definition.

        Args:
            workflow: WorkflowDefinition from discovery

        Returns:
            Goose recipe dict
        """
        recipe = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description or f"{workflow.name} workflow",
            "version": workflow.version,
        }

        # Add metadata
        if workflow.duration:
            recipe["estimated_duration"] = workflow.duration
        if workflow.complexity:
            recipe["complexity"] = workflow.complexity
        if workflow.project_types:
            recipe["project_types"] = workflow.project_types

        # Generate steps
        recipe["steps"] = self._generate_steps(workflow)

        # Generate quality gates
        if workflow.quality_gates:
            recipe["quality_gates"] = self._generate_quality_gates(workflow)

        return recipe

    def _generate_steps(self, workflow: WorkflowDefinition) -> List[Dict[str, Any]]:
        """Generate recipe steps from workflow steps."""
        steps = []

        for step in workflow.steps:
            recipe_step = {
                "order": step.order,
                "name": step.name,
            }

            # Reference MCP tool by name
            if step.agent:
                agent_id = step.agent.replace('-', '_')
                recipe_step["tool"] = f"{self.tool_prefix}_{agent_id}"

            # Add step metadata
            if step.duration:
                recipe_step["estimated_duration"] = step.duration

            if step.inputs:
                recipe_step["inputs"] = step.inputs

            if step.outputs:
                recipe_step["outputs"] = step.outputs

            steps.append(recipe_step)

        return steps

    def _generate_quality_gates(self, workflow: WorkflowDefinition) -> List[Dict[str, Any]]:
        """Generate quality gate definitions."""
        gates = []

        for gate in workflow.quality_gates:
            gate_def = {
                "name": gate.name,
                "type": gate.type,
            }

            if gate.threshold:
                gate_def["threshold"] = gate.threshold

            gate_def["blocking"] = gate.blocking

            gates.append(gate_def)

        return gates

    def generate_all(self, workflows: List[WorkflowDefinition]) -> List[Dict[str, Any]]:
        """
        Generate recipes for all workflows.

        Args:
            workflows: List of WorkflowDefinition objects

        Returns:
            List of Goose recipe dicts
        """
        recipes = []

        for workflow in workflows:
            try:
                recipe = self.generate_recipe(workflow)
                recipes.append(recipe)
                logger.debug(f"Generated recipe: {recipe['id']}")
            except Exception as e:
                logger.error(f"Failed to generate recipe for {workflow.id}: {e}")

        logger.info(f"Generated {len(recipes)} Goose recipes")
        return recipes

    def to_yaml(self, recipe: Dict[str, Any]) -> str:
        """
        Convert recipe to YAML string.

        Args:
            recipe: Recipe dict

        Returns:
            YAML-formatted string
        """
        import yaml
        return yaml.dump(recipe, default_flow_style=False, sort_keys=False)
