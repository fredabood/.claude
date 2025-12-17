"""
Sequential Orchestration for Gemini.

Gemini Code Assist uses sequential command execution (one command at a time),
unlike Claude Code which supports parallel subagent spawning. This module
provides orchestration guidance to help users chain commands effectively.

Key Features:
1. Command chains - Suggested sequences for multi-step workflows
2. Orchestration hints - Guidance on workflow execution order
3. Step dependencies - Which commands should follow which

Zero-Drift: All sequences derived from workflow frontmatter.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional

from vibey.mcp.discovery.workflows import WorkflowDefinition, WorkflowDiscovery
from vibey.mcp.discovery.agents import AgentDefinition, AgentDiscovery

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """A single step in a workflow sequence."""
    order: int
    name: str
    agent_id: str
    agent_name: str
    command_id: str
    duration: str
    description: Optional[str] = None


@dataclass
class CommandChain:
    """A sequence of commands for a workflow."""
    workflow_id: str
    workflow_name: str
    steps: List[WorkflowStep]
    total_steps: int
    estimated_duration: str
    complexity: str

    def get_next_step(self, current_step: int) -> Optional[WorkflowStep]:
        """Get the next step after current_step."""
        for step in self.steps:
            if step.order == current_step + 1:
                return step
        return None

    def to_markdown(self) -> str:
        """Generate markdown documentation for this chain."""
        lines = [
            f"### {self.workflow_name}",
            f"**Complexity:** {self.complexity} | **Duration:** {self.estimated_duration}",
            "",
            "**Command Sequence:**",
        ]

        for step in self.steps:
            cmd = f"`/vibey:{step.command_id}`" if not step.command_id.startswith("agent-") else f"`/vibey:{step.command_id}`"
            lines.append(f"{step.order}. {step.name} → {cmd}")

        return "\n".join(lines)


@dataclass
class OrchestrationResult:
    """Complete orchestration analysis result."""
    chains: List[CommandChain]
    agent_to_command: Dict[str, str]
    workflow_to_chain: Dict[str, str]
    orchestration_hints: str


class SequentialOrchestrator:
    """
    Analyzes workflows and generates sequential orchestration guidance.

    Gemini doesn't support subagent spawning, so complex workflows need
    to be broken into sequential command chains with clear "next step"
    guidance.

    Example:
        >>> orchestrator = SequentialOrchestrator(Path("/path/to/vibey"))
        >>> result = orchestrator.analyze()
        >>> print(result.orchestration_hints)
    """

    def __init__(self, root_dir: Path):
        """
        Initialize orchestrator.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)
        self.agent_discovery = AgentDiscovery(root_dir)

    def analyze(self) -> OrchestrationResult:
        """
        Analyze all workflows and generate orchestration guidance.

        Returns:
            OrchestrationResult with chains, mappings, and hints
        """
        workflows = self.workflow_discovery.discover()
        agents = self.agent_discovery.discover()

        # Build agent ID to command ID mapping
        agent_to_command = self._build_agent_command_map(agents)

        # Analyze each workflow
        chains = []
        workflow_to_chain = {}

        for workflow in workflows:
            chain = self._analyze_workflow(workflow, agent_to_command)
            if chain:
                chains.append(chain)
                workflow_to_chain[workflow.id] = chain.workflow_id

        # Generate orchestration hints
        hints = self._generate_orchestration_hints(chains, agents)

        return OrchestrationResult(
            chains=chains,
            agent_to_command=agent_to_command,
            workflow_to_chain=workflow_to_chain,
            orchestration_hints=hints,
        )

    def _build_agent_command_map(self, agents: List[AgentDefinition]) -> Dict[str, str]:
        """Map agent IDs to their command IDs."""
        mapping = {}
        for agent in agents:
            command_id = f"agent-{agent.id}"
            mapping[agent.id] = command_id
            # Also map common variations
            mapping[agent.id.replace("-", "_")] = command_id
            if hasattr(agent, 'name'):
                mapping[agent.name.lower().replace(" ", "-")] = command_id
        return mapping

    def _analyze_workflow(
        self,
        workflow: WorkflowDefinition,
        agent_map: Dict[str, str],
    ) -> Optional[CommandChain]:
        """Analyze a workflow and extract its command chain."""
        if not hasattr(workflow, 'steps') or not workflow.steps:
            # Simple workflow without steps
            return None

        steps = []
        for i, step_data in enumerate(workflow.steps, 1):
            # Handle dict or object steps
            if isinstance(step_data, dict):
                order = step_data.get('order', i)
                name = step_data.get('name', f'Step {i}')
                agent_raw = step_data.get('agent', 'unknown')
                duration = step_data.get('duration', 'varies')
                description = step_data.get('description')
            else:
                order = getattr(step_data, 'order', i)
                name = getattr(step_data, 'name', f'Step {i}')
                agent_raw = getattr(step_data, 'agent', 'unknown')
                duration = getattr(step_data, 'duration', 'varies')
                description = getattr(step_data, 'description', None)

            # Clean up agent ID (remove Jinja2 templates)
            agent_id = self._clean_agent_id(agent_raw)
            command_id = agent_map.get(agent_id, f"agent-{agent_id}")

            steps.append(WorkflowStep(
                order=order,
                name=name,
                agent_id=agent_id,
                agent_name=agent_id.replace("-", " ").title(),
                command_id=command_id,
                duration=str(duration),
                description=description,
            ))

        if not steps:
            return None

        return CommandChain(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            steps=sorted(steps, key=lambda s: s.order),
            total_steps=len(steps),
            estimated_duration=getattr(workflow, 'duration', 'varies'),
            complexity=getattr(workflow, 'complexity', 'medium'),
        )

    def _clean_agent_id(self, agent_raw: str) -> str:
        """Clean agent ID from Jinja2 templates."""
        if not agent_raw:
            return "unknown"

        # Remove Jinja2 template syntax
        agent = agent_raw
        if "{%" in agent or "{{" in agent:
            # Extract default/fallback agent from template
            # Pattern: {%-else-%}agent-name{%-endif-%}
            if "-else-" in agent and "-endif-" in agent:
                parts = agent.split("-else-")
                if len(parts) > 1:
                    after_else = parts[1]
                    if "-endif-" in after_else:
                        agent = after_else.split("-endif-")[0].strip("{}-% ")
                    else:
                        agent = after_else.strip("{}-% ")
            else:
                # Just strip template markers
                agent = agent.strip("{}-% ")

        # Clean up any remaining template chars
        agent = agent.replace("{", "").replace("}", "").replace("%", "")
        agent = agent.strip()

        return agent if agent else "unknown"

    def _generate_orchestration_hints(
        self,
        chains: List[CommandChain],
        agents: List[AgentDefinition],
    ) -> str:
        """Generate orchestration guidance markdown."""
        lines = [
            "## Sequential Workflow Execution",
            "",
            "Gemini Code Assist executes commands sequentially. For complex multi-step",
            "workflows, follow the command chains below in order.",
            "",
            "### How to Execute Multi-Step Workflows",
            "",
            "1. Start with the first command in the chain",
            "2. Review the output and provide any requested input",
            "3. Run the next command when ready",
            "4. Repeat until workflow is complete",
            "",
            "**Tip:** Use `/vibey:status` between steps to track progress.",
            "",
            "---",
            "",
        ]

        # Group chains by complexity
        simple_chains = [c for c in chains if c.complexity == 'low' or c.total_steps <= 3]
        medium_chains = [c for c in chains if c.complexity == 'medium' and c.total_steps > 3]
        complex_chains = [c for c in chains if c.complexity == 'high' or c.total_steps > 6]

        if complex_chains:
            lines.append("### Complex Workflows (6+ steps)")
            lines.append("")
            for chain in complex_chains:
                lines.append(chain.to_markdown())
                lines.append("")

        if medium_chains:
            lines.append("### Standard Workflows (4-6 steps)")
            lines.append("")
            for chain in medium_chains:
                lines.append(chain.to_markdown())
                lines.append("")

        if simple_chains:
            lines.append("### Quick Workflows (1-3 steps)")
            lines.append("")
            for chain in simple_chains[:5]:  # Top 5 simple ones
                lines.append(chain.to_markdown())
                lines.append("")

        # Add agent quick reference
        lines.extend([
            "---",
            "",
            "### Agent Quick Reference",
            "",
            "Run any agent directly with `/vibey:agent-{id}`:",
            "",
        ])

        # Group agents by type
        agent_by_type: Dict[str, List[AgentDefinition]] = {}
        for agent in agents:
            agent_type = getattr(agent, 'type', 'other')
            if agent_type not in agent_by_type:
                agent_by_type[agent_type] = []
            agent_by_type[agent_type].append(agent)

        for agent_type, type_agents in sorted(agent_by_type.items()):
            lines.append(f"**{agent_type.title()}:**")
            for agent in type_agents:
                cmd_id = f"agent-{agent.id}"
                desc = getattr(agent, 'description', '')[:50] if hasattr(agent, 'description') else ''
                lines.append(f"- `/vibey:{cmd_id}` - {desc}...")
            lines.append("")

        return "\n".join(lines)

    def get_next_step_hint(self, workflow_id: str, current_step: int) -> Optional[str]:
        """
        Get a hint for the next step in a workflow.

        Args:
            workflow_id: ID of the current workflow
            current_step: Current step number (1-indexed)

        Returns:
            Hint string or None if no next step
        """
        result = self.analyze()

        for chain in result.chains:
            if chain.workflow_id == workflow_id:
                next_step = chain.get_next_step(current_step)
                if next_step:
                    return (
                        f"Next: Run `/vibey:{next_step.command_id}` "
                        f"for {next_step.name} ({next_step.duration})"
                    )
                else:
                    return "Workflow complete! Run `/vibey:status` to review."

        return None


def generate_command_with_chain_hint(
    workflow: WorkflowDefinition,
    chain: Optional[CommandChain],
) -> str:
    """
    Generate TOML command content with chain hints.

    Adds "Next step" suggestions for sequential execution guidance.
    """
    description = workflow.description or f"Run {workflow.name} workflow"

    # Build the prompt with chain hints
    prompt_lines = [
        f"Execute the {workflow.name} workflow.",
        "",
    ]

    if chain and chain.steps:
        prompt_lines.extend([
            "**Sequential Execution Guide:**",
        ])
        for step in chain.steps:
            prompt_lines.append(
                f"{step.order}. {step.name} → `/vibey:{step.command_id}`"
            )
        prompt_lines.append("")

    prompt_lines.extend([
        "Use the appropriate MCP tools based on the workflow steps.",
        "{{args}}",
    ])

    # Generate TOML content
    content = f'''# {workflow.name}
# DO NOT EDIT - regenerate with: vibey export gemini

description = "{description}"

prompt = """
{chr(10).join(prompt_lines)}
"""
'''
    return content
