"""
Workflow Discovery Module.

Scans the vibey/content/workflows/ directory for workflow markdown files
and extracts their frontmatter for MCP tool generation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from .parser import FrontmatterParser
from vibey.content import get_workflows_dir

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """A single step in a workflow."""

    order: int
    name: str
    agent: str
    duration: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


@dataclass
class QualityGate:
    """A quality gate in a workflow."""

    name: str
    type: str
    threshold: int = 0
    blocking: bool = True


@dataclass
class WorkflowDefinition:
    """Parsed workflow definition from frontmatter."""

    id: str
    name: str
    type: str
    version: str
    description: str = ""
    duration: str = ""
    complexity: str = "medium"
    steps: List[WorkflowStep] = field(default_factory=list)
    quality_gates: List[QualityGate] = field(default_factory=list)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    project_types: List[str] = field(default_factory=list)
    filepath: Optional[Path] = None

    @classmethod
    def from_frontmatter(
        cls,
        frontmatter: Dict[str, Any],
        filepath: Optional[Path] = None
    ) -> "WorkflowDefinition":
        """Create WorkflowDefinition from parsed frontmatter."""
        # Parse steps
        steps = []
        for step_data in frontmatter.get('steps', []):
            steps.append(WorkflowStep(
                order=step_data.get('order', 0),
                name=step_data.get('name', ''),
                agent=step_data.get('agent', ''),
                duration=step_data.get('duration', ''),
                inputs=step_data.get('inputs', []),
                outputs=step_data.get('outputs', []),
            ))

        # Parse quality gates
        quality_gates = []
        for gate_data in frontmatter.get('quality_gates', []):
            quality_gates.append(QualityGate(
                name=gate_data.get('name', ''),
                type=gate_data.get('type', ''),
                threshold=gate_data.get('threshold', 0),
                blocking=gate_data.get('blocking', True),
            ))

        return cls(
            id=frontmatter.get('id', ''),
            name=frontmatter.get('name', ''),
            type=frontmatter.get('type', 'development'),
            version=frontmatter.get('version', '1.0.0'),
            description=frontmatter.get('description', ''),
            duration=frontmatter.get('duration', ''),
            complexity=frontmatter.get('complexity', 'medium'),
            steps=steps,
            quality_gates=quality_gates,
            inputs=frontmatter.get('inputs', []),
            project_types=frontmatter.get('project_types', []),
            filepath=filepath,
        )


class WorkflowDiscovery:
    """
    Discover workflows from vibey/content/workflows/ directory.

    Scans all markdown files, extracts frontmatter, and returns
    WorkflowDefinition objects for MCP tool generation.

    Example:
        >>> discovery = WorkflowDiscovery(Path("/path/to/vibey"))
        >>> workflows = discovery.discover()
        >>> for wf in workflows:
        ...     print(f"{wf.id}: {wf.name} ({len(wf.steps)} steps)")
    """

    REQUIRED_FIELDS = ['id', 'name', 'type', 'version']

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize workflow discovery.

        Args:
            root_dir: Root directory of Vibey repository (optional, uses package path if not provided)
        """
        self.root_dir = Path(root_dir) if root_dir else None

        # Determine workflows directory
        if self.root_dir:
            # When root_dir is provided (e.g., tests), look for workflows there
            # Check multiple possible paths in order of preference:
            # 1. vibey/content/workflows (package structure from repo root)
            # 2. content/workflows (test structure)
            # 3. framework/workflows (legacy structure)
            possible_paths = [
                self.root_dir / 'vibey' / 'content' / 'workflows',
                self.root_dir / 'content' / 'workflows',
                self.root_dir / 'framework' / 'workflows',
            ]
            self.workflows_dir = possible_paths[-1]  # Default to last option
            for path in possible_paths:
                if path.exists():
                    self.workflows_dir = path
                    break
        else:
            # Use content accessor for package-aware path resolution
            self.workflows_dir = get_workflows_dir()

        self.parser = FrontmatterParser()

    def discover(self) -> List[WorkflowDefinition]:
        """
        Discover all workflows in the workflows directory.

        Returns:
            List of WorkflowDefinition objects
        """
        if not self.workflows_dir.exists():
            logger.warning(f"Workflows directory not found: {self.workflows_dir}")
            return []

        workflows = []
        for filepath in self.workflows_dir.rglob('*.md'):
            # Skip README files
            if filepath.name.lower() == 'readme.md':
                continue

            workflow = self._parse_workflow_file(filepath)
            if workflow:
                workflows.append(workflow)
                logger.debug(f"Discovered workflow: {workflow.id}")

        logger.info(f"Discovered {len(workflows)} workflows")
        return workflows

    def _parse_workflow_file(self, filepath: Path) -> Optional[WorkflowDefinition]:
        """Parse a single workflow file."""
        try:
            frontmatter, _ = self.parser.parse_file(filepath)

            if frontmatter is None:
                logger.warning(f"No frontmatter in workflow file: {filepath}")
                return None

            # Validate required fields
            is_valid, errors = self.parser.validate_frontmatter(
                frontmatter,
                self.REQUIRED_FIELDS
            )

            if not is_valid:
                logger.warning(f"Invalid workflow {filepath}: {errors}")
                return None

            return WorkflowDefinition.from_frontmatter(frontmatter, filepath)

        except Exception as e:
            logger.error(f"Error parsing workflow {filepath}: {e}")
            return None

    def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get a specific workflow by ID.

        Args:
            workflow_id: Workflow ID to find

        Returns:
            WorkflowDefinition or None if not found
        """
        workflows = self.discover()
        for workflow in workflows:
            if workflow.id == workflow_id:
                return workflow
        return None

    def get_workflows_by_type(self, workflow_type: str) -> List[WorkflowDefinition]:
        """
        Get all workflows of a specific type.

        Args:
            workflow_type: Type to filter by (planning, development, etc.)

        Returns:
            List of matching WorkflowDefinition objects
        """
        workflows = self.discover()
        return [w for w in workflows if w.type == workflow_type]
