"""
Documentation Generator

Generates comprehensive project documentation from .vibey/config/ files.

Usage:
    from vibey.operations.docs.generator import DocumentationGenerator

    generator = DocumentationGenerator()
    generator.generate_all()

Created: 2025-11-09
Sprint: core-framework-2, Task 8
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yaml


class DocumentationGenerator:
    """
    Generate project documentation from Vibey configuration.

    Creates comprehensive markdown documentation including:
    - Project overview
    - Architecture documentation
    - Agent reference
    - Workflow reference
    - Configuration reference
    - API documentation
    """

    def __init__(self, vibey_dir: Path = None, output_dir: Path = None):
        """
        Initialize documentation generator.

        Args:
            vibey_dir: Path to .vibey directory (auto-detected if not provided)
            output_dir: Path to output directory (default: docs/)
        """
        self.vibey_dir = vibey_dir or self._find_vibey_dir()
        self.config_dir = self.vibey_dir / "config"
        self.project_root = self.vibey_dir.parent
        self.output_dir = output_dir or (self.project_root / "docs")

        # Load configurations
        self.project_config = self._load_project_config()
        self.framework_config = self._load_framework_config()
        self.agents = self._load_all_agents()
        self.workflows = self._load_all_workflows()
        self.quality_gates = self._load_quality_gates()

    @staticmethod
    def _find_vibey_dir() -> Path:
        """Find .vibey directory."""
        current = Path.cwd()
        while current != current.parent:
            vibey_dir = current / ".vibey"
            if vibey_dir.exists() and vibey_dir.is_dir():
                return vibey_dir
            current = current.parent

        raise FileNotFoundError(".vibey directory not found")

    def _load_project_config(self) -> Dict:
        """Load project.yaml configuration."""
        config_file = self.config_dir / "project.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def _load_framework_config(self) -> Dict:
        """Load framework.yaml configuration."""
        config_file = self.config_dir / "framework.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def _load_all_agents(self) -> List[Dict]:
        """Load all agent configurations."""
        agents_dir = self.config_dir / "agents"
        if not agents_dir.exists():
            return []

        agents = []
        for config_file in sorted(agents_dir.glob("*.yaml")):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                if config:
                    agents.append(config)

        return agents

    def _load_all_workflows(self) -> List[Dict]:
        """Load all workflow configurations."""
        workflows_dir = self.config_dir / "workflows"
        if not workflows_dir.exists():
            return []

        workflows = []
        for config_file in sorted(workflows_dir.glob("*.yaml")):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                if config:
                    workflows.append(config)

        return workflows

    def _load_quality_gates(self) -> Dict:
        """Load quality gates configuration."""
        config_file = self.config_dir / "quality-gates.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def generate_all(self, overwrite: bool = False) -> List[Path]:
        """
        Generate all documentation.

        Args:
            overwrite: Overwrite existing files (default: False)

        Returns:
            List of generated file paths
        """
        generated_files = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate each document
        print("📚 Generating documentation...\n")

        files_to_generate = [
            ("README.md", self.generate_readme),
            ("ARCHITECTURE.md", self.generate_architecture),
            ("AGENTS.md", self.generate_agents_reference),
            ("WORKFLOWS.md", self.generate_workflows_reference),
            ("CONFIGURATION.md", self.generate_configuration_reference),
        ]

        for filename, generator_func in files_to_generate:
            output_file = self.output_dir / filename

            if output_file.exists() and not overwrite:
                print(f"⏭️  Skipping {filename} (already exists)")
                continue

            print(f"📝 Generating {filename}...")
            content = generator_func()
            output_file.write_text(content)
            generated_files.append(output_file)

        return generated_files

    def generate_readme(self) -> str:
        """Generate README.md."""
        project = self.project_config.get('project', {})
        tech_stack = self.project_config.get('tech_stack', {})

        content = f"""# {project.get('name', 'Project')}

{project.get('description', 'No description provided.')}

**Version:** {project.get('version', '1.0.0')}
**Project Type:** {project.get('type', 'unknown')}

---

## Overview

This project uses the **Vibey Agent Framework** for intelligent development orchestration.

"""

        # Tech stack
        if tech_stack:
            content += "## Tech Stack\n\n"

            if tech_stack.get('languages'):
                content += f"**Languages:** {', '.join(tech_stack['languages'])}\n\n"

            if tech_stack.get('frameworks'):
                content += f"**Frameworks:** {', '.join(tech_stack['frameworks'])}\n\n"

            if tech_stack.get('databases'):
                content += f"**Databases:** {', '.join(tech_stack['databases'])}\n\n"

        # Quick links
        content += """---

## Documentation

- [Architecture](ARCHITECTURE.md) - System architecture and design decisions
- [Agents](AGENTS.md) - Available agents and their capabilities
- [Workflows](WORKFLOWS.md) - Structured workflows for common tasks
- [Configuration](CONFIGURATION.md) - Configuration reference

---

## Getting Started

"""

        dev = self.project_config.get('development', {})

        if dev.get('setup_commands'):
            content += "### Setup\n\n```bash\n"
            for cmd in dev['setup_commands']:
                content += f"{cmd}\n"
            content += "```\n\n"

        if dev.get('build_commands'):
            content += "### Build\n\n```bash\n"
            for cmd in dev['build_commands']:
                content += f"{cmd}\n"
            content += "```\n\n"

        if dev.get('test_commands'):
            content += "### Test\n\n```bash\n"
            for cmd in dev['test_commands']:
                content += f"{cmd}\n"
            content += "```\n\n"

        # Vibey framework
        orchestration = self.framework_config.get('orchestration', {})
        content += f"""---

## Vibey Agent Framework

This project is managed using the Vibey Agent Framework.

**Orchestration Mode:** {orchestration.get('mode', 'balanced')}

### Available Agents

"""

        for agent in self.agents:
            agent_data = agent.get('agent', {})
            content += f"- **{agent_data.get('name', 'Unknown')}** - {agent_data.get('description', 'No description')}\n"

        content += "\nSee [AGENTS.md](AGENTS.md) for detailed agent documentation.\n"

        # Footer
        content += f"""
---

*Documentation generated by Vibey Agent Framework on {datetime.now().strftime('%Y-%m-%d')}*
"""

        return content

    def generate_architecture(self) -> str:
        """Generate ARCHITECTURE.md."""
        project = self.project_config.get('project', {})
        dev = self.project_config.get('development', {})

        content = f"""# {project.get('name', 'Project')} - Architecture

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

---

## System Overview

{project.get('description', 'No description provided.')}

**Project Type:** {project.get('type', 'unknown')}
**Version:** {project.get('version', '1.0.0')}

---

## Project Structure

"""

        # Directory structure
        if dev.get('source_directory'):
            content += f"**Source Code:** `{dev['source_directory']}/`\n"
        if dev.get('test_directory'):
            content += f"**Tests:** `{dev['test_directory']}/`\n"
        if dev.get('docs_directory'):
            content += f"**Documentation:** `{dev['docs_directory']}/`\n"

        content += "\n---\n\n"

        # Architecture
        arch = dev.get('architecture', {})
        if arch:
            content += "## Architecture Patterns\n\n"

            if arch.get('patterns'):
                content += "**Design Patterns:**\n"
                for pattern in arch['patterns']:
                    content += f"- {pattern}\n"
                content += "\n"

            if arch.get('principles'):
                content += "**Principles:**\n"
                for principle in arch['principles']:
                    content += f"- {principle}\n"
                content += "\n"

            if arch.get('constraints'):
                content += "**Constraints:**\n"
                for constraint in arch['constraints']:
                    content += f"- {constraint}\n"
                content += "\n"

        # Quality gates
        gates = self.quality_gates.get('gates', [])
        if gates:
            content += "---\n\n## Quality Gates\n\n"
            content += "The following quality gates are enforced:\n\n"

            for gate in gates:
                content += f"### {gate.get('name', 'Unknown Gate')}\n\n"
                content += f"{gate.get('description', 'No description')}\n\n"
                content += f"**Severity:** {gate.get('severity', 'error')}\n\n"

                if gate.get('checks'):
                    content += "**Checks:**\n"
                    for check in gate['checks']:
                        content += f"- {check.get('name', 'Unknown check')}"
                        if check.get('threshold'):
                            content += f" (Threshold: {check['threshold']})"
                        content += "\n"
                    content += "\n"

        # Footer
        content += f"""---

*Architecture documentation generated by Vibey Agent Framework*
"""

        return content

    def generate_agents_reference(self) -> str:
        """Generate AGENTS.md."""
        project = self.project_config.get('project', {})

        content = f"""# {project.get('name', 'Project')} - Agents Reference

This document describes all available agents in this project.

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

---

## Overview

Agents are specialized AI assistants that handle specific types of tasks.

**Total Agents:** {len(self.agents)}

---

"""

        for agent in self.agents:
            agent_data = agent.get('agent', {})

            content += f"## {agent_data.get('name', 'Unknown Agent')}\n\n"
            content += f"**Agent ID:** `{agent_data.get('id', 'unknown')}`\n\n"
            content += f"{agent_data.get('description', 'No description provided.')}\n\n"

            # Role
            if agent_data.get('role'):
                content += f"**Role:** {agent_data['role']}\n\n"

            # Triggers
            triggers = agent_data.get('triggers', {})
            if triggers:
                content += "### When to Use\n\n"

                if triggers.get('keywords'):
                    content += "**Keywords:** "
                    content += ", ".join(f"`{kw}`" for kw in triggers['keywords'])
                    content += "\n\n"

                if triggers.get('patterns'):
                    content += "**Patterns:**\n"
                    for pattern in triggers['patterns']:
                        content += f"- {pattern}\n"
                    content += "\n"

            # Capabilities
            if agent_data.get('capabilities'):
                content += "### Capabilities\n\n"
                for capability in agent_data['capabilities']:
                    content += f"- {capability}\n"
                content += "\n"

            # Quality criteria
            if agent_data.get('quality_criteria'):
                content += "### Quality Standards\n\n"
                for criterion in agent_data['quality_criteria']:
                    content += f"- {criterion}\n"
                content += "\n"

            content += "---\n\n"

        # Footer
        content += f"""*Agents reference generated by Vibey Agent Framework*
"""

        return content

    def generate_workflows_reference(self) -> str:
        """Generate WORKFLOWS.md."""
        project = self.project_config.get('project', {})

        content = f"""# {project.get('name', 'Project')} - Workflows Reference

This document describes all available workflows in this project.

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

---

## Overview

Workflows are structured processes that guide you through complex tasks.

**Total Workflows:** {len(self.workflows)}

---

"""

        for workflow in self.workflows:
            workflow_data = workflow.get('workflow', {})

            content += f"## {workflow_data.get('name', 'Unknown Workflow')}\n\n"
            content += f"**Workflow ID:** `{workflow_data.get('id', 'unknown')}`\n\n"
            content += f"{workflow_data.get('description', 'No description provided.')}\n\n"

            # Metadata
            content += f"**Duration:** {workflow_data.get('estimated_duration', 'Unknown')}\n"
            content += f"**Complexity:** {workflow_data.get('complexity', 'Medium')}\n\n"

            # Prerequisites
            if workflow_data.get('prerequisites'):
                content += "### Prerequisites\n\n"
                for prereq in workflow_data['prerequisites']:
                    content += f"- {prereq}\n"
                content += "\n"

            # Steps
            steps = workflow_data.get('steps', [])
            if steps:
                content += "### Steps\n\n"
                for i, step in enumerate(steps, 1):
                    content += f"{i}. **{step.get('name', f'Step {i}')}**\n"
                    if step.get('description'):
                        content += f"   {step['description']}\n"
                    if step.get('agent'):
                        content += f"   *Agent: {step['agent']}*\n"
                    content += "\n"

            # Outcomes
            if workflow_data.get('outcomes'):
                content += "### Expected Outcomes\n\n"
                for outcome in workflow_data['outcomes']:
                    content += f"- {outcome}\n"
                content += "\n"

            content += "---\n\n"

        # Footer
        content += f"""*Workflows reference generated by Vibey Agent Framework*
"""

        return content

    def generate_configuration_reference(self) -> str:
        """Generate CONFIGURATION.md."""
        project = self.project_config.get('project', {})

        content = f"""# {project.get('name', 'Project')} - Configuration Reference

This document describes the Vibey configuration for this project.

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

---

## Configuration Files

All Vibey configuration is stored in `.vibey/config/`:

- `project.yaml` - Project metadata and settings
- `framework.yaml` - Framework behavior and orchestration
- `agents/*.yaml` - Agent configurations
- `workflows/*.yaml` - Workflow configurations
- `quality-gates.yaml` - Quality gate definitions

---

## Project Configuration

**File:** `.vibey/config/project.yaml`

```yaml
project:
  name: {project.get('name', 'Unknown')}
  type: {project.get('type', 'unknown')}
  version: {project.get('version', '1.0.0')}
  description: {project.get('description', 'No description')}
```

---

## Framework Configuration

**File:** `.vibey/config/framework.yaml`

"""

        orchestration = self.framework_config.get('orchestration', {})
        if orchestration:
            content += "### Orchestration\n\n"
            content += f"**Mode:** `{orchestration.get('mode', 'balanced')}`\n\n"

            if orchestration.get('coordinator_enabled') is not None:
                content += f"**Coordinator Enabled:** {orchestration['coordinator_enabled']}\n\n"

        # Context loading
        context = self.framework_config.get('context_loading', {})
        if context:
            content += "### Context Loading\n\n"
            if context.get('max_distance'):
                content += f"**Max Distance:** {context['max_distance']}\n"
            if context.get('dependency_mode'):
                content += f"**Dependency Mode:** {context['dependency_mode']}\n"
            content += "\n"

        # Quality
        quality = self.framework_config.get('quality', {})
        if quality:
            content += "### Quality Settings\n\n"
            if quality.get('enforce_gates'):
                content += f"**Enforce Gates:** {quality['enforce_gates']}\n"
            if quality.get('block_on_failure'):
                content += f"**Block on Failure:** {quality['block_on_failure']}\n"
            content += "\n"

        content += "---\n\n"

        # Agents
        content += f"## Agents ({len(self.agents)})\n\n"
        for agent in self.agents:
            agent_data = agent.get('agent', {})
            content += f"- **{agent_data.get('name', 'Unknown')}** (`{agent_data.get('id', 'unknown')}`)\n"
        content += "\n"

        # Workflows
        content += f"## Workflows ({len(self.workflows)})\n\n"
        for workflow in self.workflows:
            workflow_data = workflow.get('workflow', {})
            content += f"- **{workflow_data.get('name', 'Unknown')}** (`{workflow_data.get('id', 'unknown')}`)\n"
        content += "\n"

        # Footer
        content += """---

## Modifying Configuration

To modify the configuration:

1. Edit files in `.vibey/config/`
2. Validate configuration: `python3 framework/scripts/validate-vibey-config.py`
3. Regenerate deployment: `python3 framework/scripts/deploy.py --platform <platform>`

---

*Configuration reference generated by Vibey Agent Framework*
"""

        return content


def main():
    """Demo the documentation generator."""
    print("📚 Documentation Generator\n")
    print("=" * 60)

    try:
        generator = DocumentationGenerator()

        print(f"\n.vibey directory: {generator.vibey_dir}")
        print(f"Output directory: {generator.output_dir}\n")

        print(f"Loaded configuration:")
        print(f"  - Project: {generator.project_config.get('project', {}).get('name', 'Unknown')}")
        print(f"  - Agents: {len(generator.agents)}")
        print(f"  - Workflows: {len(generator.workflows)}")
        print()

        # Generate all documentation
        generated_files = generator.generate_all(overwrite=False)

        print(f"\n✅ Generated {len(generated_files)} documentation file(s):")
        for file_path in generated_files:
            print(f"   - {file_path.relative_to(generator.project_root)}")

        print("\n" + "=" * 60)
        print("✅ Documentation generation complete!")

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
