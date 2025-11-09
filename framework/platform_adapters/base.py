"""
Platform Adapter Base Class

Abstract base class for platform-specific deployment adapters.

Each AI coding platform (Claude Code, Goose, Cursor) has unique requirements
for file structure, naming conventions, and instruction formats. The adapter
pattern allows us to maintain a platform-agnostic core while supporting
multiple deployment targets.

Usage:
    from framework.platform_adapters.base import PlatformAdapter

    class MyPlatformAdapter(PlatformAdapter):
        def get_deployment_dir(self) -> Path:
            return Path(".myplatform")

        # ... implement other abstract methods

Created: 2025-11-09
Sprint: core-framework-2, Task 5
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# Optional jinja2 import (fallback to None if not available)
try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = None
    FileSystemLoader = None
    Template = None


class PlatformAdapter(ABC):
    """
    Base class for platform-specific deployment adapters.

    Each platform (Claude Code, Goose, Cursor) gets its own adapter
    that knows how to generate deployments from .vibey/config/.

    Core Responsibilities:
    - Define deployment directory (.claude/, .goose/, .cursor/)
    - Generate main instructions file (CLAUDE.md, README.md, .cursorrules)
    - Generate agent files in platform-specific format
    - Generate workflow files in platform-specific format
    - Handle platform-specific quirks and requirements
    """

    def __init__(self, vibey_dir: Path = None):
        """
        Initialize platform adapter.

        Args:
            vibey_dir: Path to .vibey directory (auto-detected if not provided)
        """
        self.vibey_dir = vibey_dir or self._find_vibey_dir()
        self.config_dir = self.vibey_dir / "config"
        self.templates_dir = self.vibey_dir / "templates"
        self.roadmap_dir = self.vibey_dir / "roadmap"

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment (if available)
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader([
                    str(self.templates_dir),
                    str(Path(__file__).parent.parent / "templates")  # Fallback to framework templates
                ]),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.jinja_env = None

    @staticmethod
    def _find_vibey_dir() -> Path:
        """Find .vibey directory"""
        current = Path.cwd()
        while current != current.parent:
            vibey_dir = current / ".vibey"
            if vibey_dir.exists() and vibey_dir.is_dir():
                return vibey_dir
            current = current.parent

        raise FileNotFoundError(".vibey directory not found")

    # ========================================================================
    # Abstract Methods - Must be implemented by each platform adapter
    # ========================================================================

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Return platform name.

        Returns:
            Platform name (e.g., "claude-code", "goose", "cursor")
        """
        pass

    @abstractmethod
    def get_deployment_dir(self) -> Path:
        """
        Return the platform's deployment directory.

        Returns:
            Path to deployment directory (e.g., .claude/, .goose/, .cursor/)
        """
        pass

    @abstractmethod
    def get_instructions_filename(self) -> str:
        """
        Return the main instructions file name.

        Returns:
            Instructions filename (e.g., "CLAUDE.md", "README.md", ".cursorrules")
        """
        pass

    @abstractmethod
    def generate_instructions_file(self) -> str:
        """
        Generate main instructions file content.

        This is the primary file the platform reads (CLAUDE.md, README.md, etc.).

        Returns:
            Instructions file content (Markdown or platform-specific format)
        """
        pass

    @abstractmethod
    def generate_agent_file(self, agent_config: Dict) -> str:
        """
        Generate agent file content for this platform.

        Args:
            agent_config: Agent configuration from .vibey/config/agents/<agent>.yaml

        Returns:
            Agent file content in platform-specific format
        """
        pass

    @abstractmethod
    def generate_workflow_file(self, workflow_config: Dict) -> str:
        """
        Generate workflow file content for this platform.

        Args:
            workflow_config: Workflow config from .vibey/config/workflows/<workflow>.yaml

        Returns:
            Workflow file content in platform-specific format
        """
        pass

    # ========================================================================
    # Platform-specific naming (can be overridden)
    # ========================================================================

    def get_agent_filename(self, agent_id: str) -> str:
        """
        Get filename for agent.

        Default: <agent-id>.md
        Override for platform-specific naming.

        Args:
            agent_id: Agent ID (e.g., "web-developer")

        Returns:
            Filename (e.g., "web-developer.md")
        """
        return f"{agent_id}.md"

    def get_workflow_filename(self, workflow_id: str) -> str:
        """
        Get filename for workflow.

        Default: <workflow-id>.md
        Override for platform-specific naming.

        Args:
            workflow_id: Workflow ID (e.g., "sprint-planning")

        Returns:
            Filename (e.g., "sprint-planning.md")
        """
        return f"{workflow_id}.md"

    def get_agents_dirname(self) -> str:
        """
        Get directory name for agents.

        Default: "agents"
        Override if platform uses different name (e.g., "extensions").

        Returns:
            Directory name
        """
        return "agents"

    def get_workflows_dirname(self) -> str:
        """
        Get directory name for workflows.

        Default: "workflows"
        Override if platform uses different name (e.g., "recipes").

        Returns:
            Directory name
        """
        return "workflows"

    # ========================================================================
    # Config loading utilities
    # ========================================================================

    def load_project_config(self) -> Dict:
        """Load project.yaml configuration"""
        config_file = self.config_dir / "project.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def load_framework_config(self) -> Dict:
        """Load framework.yaml configuration"""
        config_file = self.config_dir / "framework.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def load_agent_config(self, agent_id: str) -> Dict:
        """Load agent configuration"""
        config_file = self.config_dir / "agents" / f"{agent_id}.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def load_all_agents(self) -> List[Dict]:
        """Load all agent configurations"""
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

    def load_workflow_config(self, workflow_id: str) -> Dict:
        """Load workflow configuration"""
        config_file = self.config_dir / "workflows" / f"{workflow_id}.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def load_all_workflows(self) -> List[Dict]:
        """Load all workflow configurations"""
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

    def load_quality_gates(self) -> Dict:
        """Load quality gates configuration"""
        config_file = self.config_dir / "quality-gates.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    # ========================================================================
    # Template rendering utilities
    # ========================================================================

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        fallback_content: Optional[str] = None
    ) -> str:
        """
        Render Jinja2 template with context.

        Args:
            template_name: Template filename (e.g., "agent.md.j2")
            context: Template context variables
            fallback_content: Fallback content if template not found

        Returns:
            Rendered content
        """
        if not JINJA2_AVAILABLE or self.jinja_env is None:
            if fallback_content:
                return fallback_content
            raise RuntimeError(
                f"Jinja2 not available and no fallback content provided. "
                f"Install jinja2: pip install jinja2"
            )

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            if fallback_content:
                return fallback_content
            raise

    # ========================================================================
    # Deployment generation (main public API)
    # ========================================================================

    def deploy(
        self,
        clean: bool = True,
        validate: bool = True,
        backup: bool = True
    ) -> None:
        """
        Generate complete deployment for this platform.

        This is the main entry point for deployment generation.

        Args:
            clean: Delete existing deployment before generating
            validate: Validate configs before deployment
            backup: Backup existing deployment before overwriting

        Raises:
            ValueError: If validation fails
        """
        deployment_dir = self.get_deployment_dir()

        # Backup existing deployment
        if backup and deployment_dir.exists():
            self._backup_deployment(deployment_dir)

        # Clean deployment directory
        if clean and deployment_dir.exists():
            import shutil
            shutil.rmtree(deployment_dir)

        # Create deployment directory
        deployment_dir.mkdir(parents=True, exist_ok=True)

        # Generate instructions file
        print(f"📝 Generating {self.get_instructions_filename()}...")
        instructions = self.generate_instructions_file()
        instructions_path = deployment_dir / self.get_instructions_filename()
        instructions_path.write_text(instructions)

        # Generate agents
        agents = self.load_all_agents()
        if agents:
            agents_dir = deployment_dir / self.get_agents_dirname()
            agents_dir.mkdir(parents=True, exist_ok=True)

            print(f"🤖 Generating {len(agents)} agent(s)...")
            for agent_config in agents:
                agent_id = agent_config.get('agent', {}).get('id')
                if agent_id:
                    content = self.generate_agent_file(agent_config)
                    filename = self.get_agent_filename(agent_id)
                    (agents_dir / filename).write_text(content)

        # Generate workflows
        workflows = self.load_all_workflows()
        if workflows:
            workflows_dir = deployment_dir / self.get_workflows_dirname()
            workflows_dir.mkdir(parents=True, exist_ok=True)

            print(f"📋 Generating {len(workflows)} workflow(s)...")
            for workflow_config in workflows:
                workflow_id = workflow_config.get('workflow', {}).get('id')
                if workflow_id:
                    content = self.generate_workflow_file(workflow_config)
                    filename = self.get_workflow_filename(workflow_id)
                    (workflows_dir / filename).write_text(content)

        print(f"\n✅ Deployment generated at: {deployment_dir}")

    def _backup_deployment(self, deployment_dir: Path) -> None:
        """Backup existing deployment"""
        import shutil
        from datetime import datetime

        backup_dir = self.vibey_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform_name = self.get_platform_name()
        backup_path = backup_dir / f"{platform_name}_{timestamp}"

        shutil.copytree(deployment_dir, backup_path)
        print(f"💾 Backed up to: {backup_path}")

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_config(self) -> bool:
        """
        Validate configuration before deployment.

        Returns:
            True if valid, False otherwise
        """
        # Check required files exist
        if not (self.config_dir / "project.yaml").exists():
            print("❌ Missing project.yaml")
            return False

        if not (self.config_dir / "framework.yaml").exists():
            print("❌ Missing framework.yaml")
            return False

        # Check at least one agent exists
        agents_dir = self.config_dir / "agents"
        if not agents_dir.exists() or not list(agents_dir.glob("*.yaml")):
            print("⚠️  Warning: No agents configured")

        return True
