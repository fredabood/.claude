"""
MCP Resource Provider for Workflows.

Provides MCP Resources for vibey workflow content, enabling:
- Direct workflow content access via URI
- Workflow step enumeration
- Quality gate extraction
- Workflow metadata queries
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from .provider import ResourceProvider
from .types import (
    Resource,
    ResourceContent,
    ResourceTemplate,
    RESOURCE_CATEGORY_WORKFLOWS,
    MIME_TYPE_MARKDOWN,
    MIME_TYPE_JSON,
)
from .exceptions import ResourceNotFoundError

from ..discovery.workflows import WorkflowDiscovery, WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowResourceProvider(ResourceProvider):
    """
    Provides MCP Resources for workflow content.

    Exposes vibey workflows as MCP Resources with support for:
    - Full workflow content (markdown)
    - Workflow steps (JSON)
    - Workflow metadata (JSON)
    - Workflow quality gates (JSON)

    Example:
        >>> provider = WorkflowResourceProvider(Path("/path/to/vibey"))
        >>> templates = provider.get_templates()
        >>> resources = provider.list_resources("vibey://workflows/{workflow_id}")
        >>> content = await provider.read_resource("vibey://workflows/sprint-planning")
    """

    URI_CATEGORY = RESOURCE_CATEGORY_WORKFLOWS

    def __init__(self, content_root: Path):
        """
        Initialize workflow resource provider.

        Args:
            content_root: Root directory for content discovery
        """
        super().__init__(content_root)
        self.discovery = WorkflowDiscovery(content_root)
        self._cache: Optional[List[WorkflowDefinition]] = None

    def get_templates(self) -> List[ResourceTemplate]:
        """
        Return workflow resource templates.

        Returns:
            List of ResourceTemplate definitions for workflow resources
        """
        return [
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}",
                name="Workflow Definition",
                description="Full workflow definition with steps and gates",
                mimeType=MIME_TYPE_MARKDOWN,
            ),
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}/steps",
                name="Workflow Steps",
                description="Workflow steps as structured JSON",
                mimeType=MIME_TYPE_JSON,
            ),
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}/metadata",
                name="Workflow Metadata",
                description="Workflow frontmatter metadata",
                mimeType=MIME_TYPE_JSON,
            ),
            ResourceTemplate(
                uriTemplate="vibey://workflows/{workflow_id}/quality-gates",
                name="Workflow Quality Gates",
                description="Quality gates defined in this workflow",
                mimeType=MIME_TYPE_JSON,
            ),
        ]

    def list_resources(self, uri_template: str) -> List[Resource]:
        """
        List all workflows as resources for a given template.

        Args:
            uri_template: URI template pattern to match

        Returns:
            List of Resource objects matching the template
        """
        workflows = self._get_workflows()
        resources = []

        for wf in workflows:
            if "metadata" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}/metadata",
                    name=f"{wf.name} - Metadata",
                    description=f"Metadata for {wf.name}",
                    mimeType=MIME_TYPE_JSON,
                    metadata={"type": wf.type, "complexity": wf.complexity},
                ))
            elif "steps" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}/steps",
                    name=f"{wf.name} - Steps",
                    description=f"{len(wf.steps)} steps in workflow",
                    mimeType=MIME_TYPE_JSON,
                    metadata={"step_count": len(wf.steps)},
                ))
            elif "quality-gates" in uri_template:
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}/quality-gates",
                    name=f"{wf.name} - Quality Gates",
                    description=f"{len(wf.quality_gates)} quality gates",
                    mimeType=MIME_TYPE_JSON,
                    metadata={"gate_count": len(wf.quality_gates)},
                ))
            else:
                # Full workflow resource
                resources.append(Resource(
                    uri=f"vibey://workflows/{wf.id}",
                    name=wf.name,
                    description=wf.description,
                    mimeType=MIME_TYPE_MARKDOWN,
                    metadata={
                        "type": wf.type,
                        "complexity": wf.complexity,
                        "duration": wf.duration,
                        "steps": len(wf.steps),
                        "gates": len(wf.quality_gates),
                    },
                ))

        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Read workflow resource content by URI.

        Args:
            uri: Resource URI (e.g., "vibey://workflows/sprint-planning")

        Returns:
            ResourceContent with the workflow data

        Raises:
            ResourceNotFoundError: If workflow doesn't exist
        """
        # Parse URI: vibey://workflows/{id}[/subresource]
        parsed = self.parse_uri(uri)
        workflow_id = parsed["id"]
        subresource = parsed.get("subresource")

        workflow = self._find_workflow(workflow_id)
        if not workflow:
            raise ResourceNotFoundError(uri, f"Workflow not found: {workflow_id}")

        if subresource == "steps":
            return await self._read_steps(workflow, uri)
        elif subresource == "metadata":
            return await self._read_metadata(workflow, uri)
        elif subresource == "quality-gates":
            return await self._read_quality_gates(workflow, uri)
        else:
            return await self._read_full_workflow(workflow, uri)

    async def _read_full_workflow(
        self, wf: WorkflowDefinition, uri: str
    ) -> ResourceContent:
        """
        Read full workflow markdown content.

        Args:
            wf: WorkflowDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with markdown text
        """
        if wf.filepath and wf.filepath.exists():
            content = wf.filepath.read_text()
        else:
            content = self._generate_workflow_markdown(wf)

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_MARKDOWN,
            text=content,
        )

    async def _read_steps(
        self, wf: WorkflowDefinition, uri: str
    ) -> ResourceContent:
        """
        Read workflow steps as JSON.

        Args:
            wf: WorkflowDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with JSON steps data
        """
        steps_data = [
            {
                "order": step.order,
                "name": step.name,
                "agent": step.agent,
                "duration": step.duration,
                "inputs": step.inputs,
                "outputs": step.outputs,
            }
            for step in wf.steps
        ]

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_JSON,
            text=json.dumps(
                {"workflow_id": wf.id, "workflow_name": wf.name, "steps": steps_data},
                indent=2,
            ),
        )

    async def _read_metadata(
        self, wf: WorkflowDefinition, uri: str
    ) -> ResourceContent:
        """
        Read workflow metadata as JSON.

        Args:
            wf: WorkflowDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with JSON metadata
        """
        metadata = {
            "id": wf.id,
            "name": wf.name,
            "type": wf.type,
            "version": wf.version,
            "description": wf.description,
            "complexity": wf.complexity,
            "duration": wf.duration,
            "step_count": len(wf.steps),
            "quality_gate_count": len(wf.quality_gates),
            "project_types": wf.project_types,
        }

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_JSON,
            text=json.dumps(metadata, indent=2),
        )

    async def _read_quality_gates(
        self, wf: WorkflowDefinition, uri: str
    ) -> ResourceContent:
        """
        Read workflow quality gates as JSON.

        Args:
            wf: WorkflowDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with JSON quality gates data
        """
        gates_data = [
            {
                "name": gate.name,
                "type": gate.type,
                "threshold": gate.threshold,
                "blocking": gate.blocking,
            }
            for gate in wf.quality_gates
        ]

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_JSON,
            text=json.dumps(
                {"workflow_id": wf.id, "quality_gates": gates_data},
                indent=2,
            ),
        )

    def _get_workflows(self) -> List[WorkflowDefinition]:
        """
        Get all workflows (cached).

        Returns:
            List of WorkflowDefinition objects
        """
        if self._cache is None:
            self._cache = self.discovery.discover()
        return self._cache

    def _find_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Find workflow by ID.

        Args:
            workflow_id: Workflow ID to find

        Returns:
            WorkflowDefinition or None if not found
        """
        for wf in self._get_workflows():
            if wf.id == workflow_id:
                return wf
        return None

    def _generate_workflow_markdown(self, wf: WorkflowDefinition) -> str:
        """
        Generate markdown from workflow definition.

        Used when workflow file is not available but definition exists.

        Args:
            wf: WorkflowDefinition to convert

        Returns:
            Markdown string representation
        """
        lines = [
            f"# {wf.name}",
            "",
            f"**Type:** {wf.type}",
            f"**Complexity:** {wf.complexity}",
            f"**Version:** {wf.version}",
        ]

        if wf.duration:
            lines.append(f"**Duration:** {wf.duration}")

        if wf.description:
            lines.extend(["", wf.description, ""])

        if wf.steps:
            lines.extend(["", "## Steps", ""])
            for step in wf.steps:
                lines.append(f"{step.order}. **{step.name}**")
                if step.agent:
                    lines.append(f"   - Agent: {step.agent}")
                if step.duration:
                    lines.append(f"   - Duration: {step.duration}")
                if step.inputs:
                    lines.append(f"   - Inputs: {', '.join(step.inputs)}")
                if step.outputs:
                    lines.append(f"   - Outputs: {', '.join(step.outputs)}")

        if wf.quality_gates:
            lines.extend(["", "## Quality Gates", ""])
            for gate in wf.quality_gates:
                blocking = " [BLOCKING]" if gate.blocking else ""
                lines.append(f"- **{gate.name}** ({gate.type}){blocking}")
                if gate.threshold:
                    lines.append(f"  - Threshold: {gate.threshold}")

        return "\n".join(lines)

    def invalidate_cache(self) -> None:
        """Invalidate workflow cache."""
        self._cache = None
        logger.debug("Workflow resource cache invalidated")
