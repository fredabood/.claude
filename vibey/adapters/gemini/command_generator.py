"""
Gemini Command Generator.

Generates TOML custom commands from Vibey workflow frontmatter.
This ensures zero-drift: generated commands always match source workflows.

Gemini Command Structure:
- Located in .gemini/commands/ or ~/.gemini/commands/
- TOML format with description and prompt fields
- Supports shell injection with !{command}
- Namespaced with : (e.g., /vibey:sprint)
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from vibey.mcp.discovery.workflows import WorkflowDefinition, WorkflowDiscovery
from vibey.mcp.discovery.agents import AgentDefinition, AgentDiscovery

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCommand:
    """A single generated TOML command."""
    id: str
    filename: str
    content: str
    source_workflow: str


@dataclass
class CommandGenerationResult:
    """Result of command generation."""
    commands: List[GeneratedCommand]
    checksum: str
    generated_at: datetime
    manifest: Dict[str, Any] = field(default_factory=dict)


class GeminiCommandGenerator:
    """
    Generate Gemini TOML commands from Vibey workflow frontmatter.

    Zero-Drift Guarantee:
    - Reads directly from workflow frontmatter (single source of truth)
    - Generates checksum for drift detection
    - Produces manifest.json for validation

    Example:
        >>> generator = GeminiCommandGenerator(Path("/path/to/vibey"))
        >>> result = generator.generate()
        >>> for cmd in result.commands:
        ...     Path(f"commands/vibey/{cmd.filename}").write_text(cmd.content)
    """

    def __init__(self, root_dir: Path):
        """
        Initialize command generator.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)
        self.agent_discovery = AgentDiscovery(root_dir)

    def generate(self) -> CommandGenerationResult:
        """
        Generate TOML commands from all workflows.

        Returns:
            CommandGenerationResult with commands and metadata
        """
        workflows = self.workflow_discovery.discover()
        agents = self.agent_discovery.discover()

        commands = []

        # Generate workflow commands
        for workflow in workflows:
            cmd = self._generate_workflow_command(workflow)
            commands.append(cmd)

        # Generate agent shortcut commands
        for agent in agents:
            cmd = self._generate_agent_command(agent)
            commands.append(cmd)

        # Generate utility commands
        commands.extend(self._generate_utility_commands())

        # Calculate checksum
        all_content = "\n".join(c.content for c in commands)
        checksum = hashlib.sha256(all_content.encode()).hexdigest()[:16]

        # Build manifest
        manifest = self._build_manifest(commands, workflows, agents)

        return CommandGenerationResult(
            commands=commands,
            checksum=checksum,
            generated_at=datetime.now(timezone.utc),
            manifest=manifest,
        )

    def _generate_workflow_command(self, workflow: WorkflowDefinition) -> GeneratedCommand:
        """Generate a TOML command for a workflow."""
        # Build step instructions
        steps_text = ""
        if workflow.steps:
            steps_text = "\\n\\nSteps:\\n"
            for step in workflow.steps:
                steps_text += f"- {step.order}. {step.name}"
                if step.agent:
                    steps_text += f" (use {step.agent} agent)"
                steps_text += "\\n"

        # Build quality gates text
        gates_text = ""
        if workflow.quality_gates:
            gates_text = "\\n\\nQuality Gates:\\n"
            for gate in workflow.quality_gates:
                blocking = " (blocking)" if gate.blocking else ""
                gates_text += f"- {gate.name}: {gate.threshold}% threshold{blocking}\\n"

        description = workflow.description or f"Execute the {workflow.name} workflow"

        content = f'''# {workflow.name}
# Generated from: {workflow.filepath.name if workflow.filepath else 'unknown'}
# DO NOT EDIT - regenerate with: vibey export gemini

description = "{description}"

prompt = """
Execute the **{workflow.name}** workflow.

{workflow.description or 'This workflow helps organize development tasks.'}{steps_text}{gates_text}
Use the appropriate MCP tools (vibey_*) to execute each step.
Report progress and any blockers encountered.

{{{{args}}}}
"""
'''

        return GeneratedCommand(
            id=workflow.id,
            filename=f"{workflow.id}.toml",
            content=content,
            source_workflow=str(workflow.filepath) if workflow.filepath else "",
        )

    def _generate_agent_command(self, agent: AgentDefinition) -> GeneratedCommand:
        """Generate a shortcut command for an agent."""
        trigger_text = ""
        if agent.triggers:
            keywords = agent.triggers.get('keywords', [])
            if keywords:
                trigger_text = f"\\n\\nTrigger keywords: {', '.join(keywords[:5])}"

        inputs_text = ""
        if agent.inputs:
            inputs_text = "\\n\\nExpected inputs:\\n"
            for inp in agent.inputs:
                name = inp.get('name', 'input')
                desc = inp.get('description', '')
                required = " (required)" if inp.get('required', False) else ""
                inputs_text += f"- {name}: {desc}{required}\\n"

        description = agent.description or f"Invoke the {agent.name} agent"

        content = f'''# {agent.name}
# Generated from: {agent.filepath.name if agent.filepath else 'unknown'}
# DO NOT EDIT - regenerate with: vibey export gemini

description = "{description}"

prompt = """
Invoke the **{agent.name}** agent.

{agent.description or f'This agent specializes in {agent.type} tasks.'}{trigger_text}{inputs_text}
Use the MCP tool `vibey_{agent.id.replace('-', '_')}` or follow the agent's
specialized instructions for this task.

Task: {{{{args}}}}
"""
'''

        return GeneratedCommand(
            id=f"agent-{agent.id}",
            filename=f"agent-{agent.id}.toml",
            content=content,
            source_workflow=str(agent.filepath) if agent.filepath else "",
        )

    def _generate_utility_commands(self) -> List[GeneratedCommand]:
        """Generate utility commands for common operations."""
        commands = []

        # Status command
        commands.append(GeneratedCommand(
            id="status",
            filename="status.toml",
            content='''# Vibey Status
# DO NOT EDIT - regenerate with: vibey export gemini

description = "Check Vibey roadmap and sprint status"

prompt = """
Check the current Vibey roadmap status.

Use the MCP tool `vibey_roadmap_status` to get:
- Overall completion percentage
- Active tracks and sprints
- Current blockers
- Recent completions

{{args}}
"""
''',
            source_workflow="utility",
        ))

        # Sprint command
        commands.append(GeneratedCommand(
            id="sprint",
            filename="sprint.toml",
            content='''# Sprint Management
# DO NOT EDIT - regenerate with: vibey export gemini

description = "Manage sprints - start, complete, or query status"

prompt = """
Sprint management command.

Available operations:
- Start a sprint: `vibey_start_sprint`
- Complete a sprint: `vibey_complete_sprint`
- Query sprint: `vibey_query_sprint`

{{args}}
"""
''',
            source_workflow="utility",
        ))

        # Task command
        commands.append(GeneratedCommand(
            id="task",
            filename="task.toml",
            content='''# Task Management
# DO NOT EDIT - regenerate with: vibey export gemini

description = "Manage tasks - start, complete, or query"

prompt = """
Task management command.

Available operations:
- Start a task: `vibey_start_task`
- Complete a task: `vibey_complete_task`
- Query task: `vibey_query_task`

{{args}}
"""
''',
            source_workflow="utility",
        ))

        return commands

    def _build_manifest(
        self,
        commands: List[GeneratedCommand],
        workflows: List[WorkflowDefinition],
        agents: List[AgentDefinition],
    ) -> Dict[str, Any]:
        """Build manifest for validation."""
        return {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commands_count": len(commands),
            "workflows_count": len(workflows),
            "agents_count": len(agents),
            "commands": {cmd.id: cmd.filename for cmd in commands},
        }

    def write_to_directory(
        self,
        output_dir: Path,
        namespace: str = "vibey",
    ) -> CommandGenerationResult:
        """
        Generate and write all commands to directory.

        Args:
            output_dir: Base directory for commands (e.g., .gemini/commands)
            namespace: Command namespace (creates subdirectory)

        Returns:
            CommandGenerationResult with metadata
        """
        result = self.generate()

        # Create namespace directory
        namespace_dir = output_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)

        # Write each command
        for cmd in result.commands:
            cmd_path = namespace_dir / cmd.filename
            cmd_path.write_text(cmd.content, encoding='utf-8')
            logger.debug(f"Generated command: {cmd_path}")

        # Write manifest
        import json
        manifest_path = namespace_dir / "_manifest.json"
        manifest_path.write_text(
            json.dumps(result.manifest, indent=2),
            encoding='utf-8'
        )

        logger.info(
            f"Generated {len(result.commands)} Gemini commands "
            f"(checksum: {result.checksum})"
        )

        return result
