"""
MCP Tool Generator.

Converts AgentDefinition and WorkflowDefinition objects into
MCP tool schema format for dynamic tool discovery.
"""

import logging
from typing import Dict, Any, List, Optional

from .agents import AgentDefinition
from .workflows import WorkflowDefinition
from .handoffs import HandoffDefinition

logger = logging.getLogger(__name__)


# Map our types to JSON Schema types
TYPE_MAP = {
    'string': 'string',
    'integer': 'integer',
    'boolean': 'boolean',
    'array': 'array',
    'object': 'object',
    'number': 'number',
}


class ToolGenerator:
    """
    Generate MCP tool definitions from Vibey assets.

    Converts AgentDefinition and WorkflowDefinition objects into
    the MCP tool schema format that can be returned by list_tools().

    Example:
        >>> generator = ToolGenerator()
        >>> tool = generator.agent_to_tool(agent_definition)
        >>> print(tool['name'])
        'vibey_test_engineer'
    """

    def __init__(self, tool_prefix: str = "vibey"):
        """
        Initialize tool generator.

        Args:
            tool_prefix: Prefix for tool names (default: "vibey")
        """
        self.tool_prefix = tool_prefix

    def agent_to_tool(self, agent: AgentDefinition) -> Dict[str, Any]:
        """
        Convert an AgentDefinition to an MCP tool schema.

        Args:
            agent: AgentDefinition object

        Returns:
            MCP tool definition dict
        """
        tool_name = f"{self.tool_prefix}_{agent.id.replace('-', '_')}"

        # Build input schema from agent inputs
        properties = {}
        required = []

        for inp in agent.inputs:
            prop_name = inp.get('name', '')
            if not prop_name:
                continue

            prop_type = TYPE_MAP.get(inp.get('type', 'string'), 'string')
            prop_def = {
                'type': prop_type,
                'description': inp.get('description', ''),
            }

            # Add default if specified
            if 'default' in inp:
                prop_def['default'] = inp['default']

            properties[prop_name] = prop_def

            if inp.get('required', False):
                required.append(prop_name)

        # Build description including triggers for context
        description = agent.description or f"{agent.name} agent"
        if agent.triggers.get('keywords'):
            keywords = agent.triggers['keywords'][:5]  # First 5 keywords
            description += f" (triggers: {', '.join(keywords)})"

        return {
            'name': tool_name,
            'title': agent.name,
            'description': description,
            'inputSchema': {
                'type': 'object',
                'properties': properties,
                'required': required,
            },
            # Store metadata for routing
            '_metadata': {
                'asset_type': 'agent',
                'asset_id': agent.id,
                'agent_type': agent.type,
                'triggers': agent.triggers,
                'aliases': agent.aliases,
            }
        }

    def workflow_to_tool(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """
        Convert a WorkflowDefinition to an MCP tool schema.

        Args:
            workflow: WorkflowDefinition object

        Returns:
            MCP tool definition dict
        """
        tool_name = f"{self.tool_prefix}_workflow_{workflow.id.replace('-', '_')}"

        # Build input schema from workflow inputs
        properties = {}
        required = []

        for inp in workflow.inputs:
            prop_name = inp.get('name', '')
            if not prop_name:
                continue

            prop_type = TYPE_MAP.get(inp.get('type', 'string'), 'string')
            prop_def = {
                'type': prop_type,
                'description': inp.get('description', ''),
            }

            # Add default if specified
            if 'default' in inp:
                prop_def['default'] = inp['default']

            properties[prop_name] = prop_def

            if inp.get('required', False):
                required.append(prop_name)

        # Build description including steps summary
        description = workflow.description or f"{workflow.name} workflow"
        if workflow.steps:
            step_count = len(workflow.steps)
            description += f" ({step_count} steps"
            if workflow.duration:
                description += f", {workflow.duration}"
            description += ")"

        return {
            'name': tool_name,
            'title': f"Workflow: {workflow.name}",
            'description': description,
            'inputSchema': {
                'type': 'object',
                'properties': properties,
                'required': required,
            },
            # Store metadata for routing
            '_metadata': {
                'asset_type': 'workflow',
                'asset_id': workflow.id,
                'workflow_type': workflow.type,
                'steps': [
                    {'order': s.order, 'name': s.name, 'agent': s.agent}
                    for s in workflow.steps
                ],
                'quality_gates': [
                    {'name': g.name, 'type': g.type, 'threshold': g.threshold}
                    for g in workflow.quality_gates
                ],
            }
        }

    def handoff_to_tool(self, handoff: HandoffDefinition) -> Dict[str, Any]:
        """
        Convert a HandoffDefinition to an MCP tool schema.

        Each handoff becomes a tool that renders the handoff template
        with the provided variable values.

        Args:
            handoff: HandoffDefinition object

        Returns:
            MCP tool definition dict
        """
        tool_name = f"{self.tool_prefix}_handoff_{handoff.id.replace('-', '_')}"

        # Build input schema from handoff variables
        properties = {}
        required = []

        for var in handoff.variables:
            prop_type = TYPE_MAP.get(var.type, "string")
            prop_def = {
                "type": prop_type,
                "description": var.description or f"Variable: {var.name}",
            }

            if var.default is not None:
                prop_def["default"] = var.default

            properties[var.name] = prop_def

            if var.required:
                required.append(var.name)

        # Build description with agent routing info
        description = f"{handoff.name}: {handoff.purpose}"
        description += f" (from: {handoff.from_agent}, to: {', '.join(handoff.to_agents)})"

        return {
            "name": tool_name,
            "title": f"Handoff: {handoff.name}",
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "_metadata": {
                "asset_type": "handoff",
                "asset_id": handoff.id,
                "from_agent": handoff.from_agent,
                "to_agents": handoff.to_agents,
                "version": handoff.version,
            },
        }

    def generate_all_tools(
        self,
        agents: List[AgentDefinition],
        workflows: List[WorkflowDefinition],
        handoffs: Optional[List[HandoffDefinition]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate MCP tools for all agents, workflows, and handoffs.

        Args:
            agents: List of AgentDefinition objects
            workflows: List of WorkflowDefinition objects
            handoffs: Optional list of HandoffDefinition objects

        Returns:
            List of MCP tool definitions
        """
        tools = []

        # Generate agent tools
        for agent in agents:
            try:
                tool = self.agent_to_tool(agent)
                tools.append(tool)
                logger.debug(f"Generated tool: {tool['name']}")
            except Exception as e:
                logger.error(f"Error generating tool for agent {agent.id}: {e}")

        # Generate workflow tools
        for workflow in workflows:
            try:
                tool = self.workflow_to_tool(workflow)
                tools.append(tool)
                logger.debug(f"Generated tool: {tool['name']}")
            except Exception as e:
                logger.error(f"Error generating tool for workflow {workflow.id}: {e}")

        # Generate handoff tools
        if handoffs:
            for handoff in handoffs:
                try:
                    tool = self.handoff_to_tool(handoff)
                    tools.append(tool)
                    logger.debug(f"Generated tool: {tool['name']}")
                except Exception as e:
                    logger.error(f"Error generating tool for handoff {handoff.id}: {e}")

        handoff_count = len(handoffs) if handoffs else 0
        logger.info(
            f"Generated {len(tools)} tools "
            f"({len(agents)} agents, {len(workflows)} workflows, {handoff_count} handoffs)"
        )
        return tools
