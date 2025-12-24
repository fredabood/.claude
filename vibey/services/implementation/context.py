"""
TaskContextBuilder - Assemble execution context for task implementation.

This module provides the TaskContextBuilder class for assembling complete
execution context for AI agents to implement tasks.

Context includes:
1. Task description and acceptance criteria
2. Parent context (sprint goals, track objectives)
3. Relevant files from task plan
4. Dependency outputs (what completed tasks produced)
5. System prompt with execution instructions

Usage:
    from vibey.services.implementation import TaskContextBuilder, TaskContext
    from pathlib import Path

    # Initialize with roadmap root
    builder = TaskContextBuilder(roadmap_root=Path(".vibey/roadmap"))

    # Build context for a task
    context = builder.build_context(task)

    # Access context components
    print(context.system_prompt)
    print(context.task_description)
    for criterion in context.acceptance_criteria:
        print(f"- {criterion}")

Design Reference:
- Implementation Mode Track Sprint 2
- ADR-0002: Flat Directory Structure
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.enums import TicketStatus

logger = logging.getLogger(__name__)


# =============================================================================
# TASK CONTEXT DATACLASS
# =============================================================================


@dataclass
class TaskContext:
    """
    Complete execution context for a task.

    Contains all information an AI agent needs to implement a task,
    including the task itself, system prompt, acceptance criteria,
    relevant files, and parent context.

    Attributes:
        task: The HierarchicalTicket to implement
        system_prompt: Instructions for the agent on how to execute
        task_description: Full description of what to implement
        acceptance_criteria: List of criteria that must be met
        relevant_files: Files mentioned in the task/plan that may need modification
        parent_context: Context from sprint/track (goals, objectives)
        max_tokens: Optional token limit for the execution
    """

    task: HierarchicalTicket
    system_prompt: str
    task_description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    relevant_files: List[Path] = field(default_factory=list)
    parent_context: Optional[str] = None
    max_tokens: Optional[int] = None

    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self.task.id

    @property
    def task_name(self) -> str:
        """Get the task name."""
        return self.task.name

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "system_prompt": self.system_prompt,
            "task_description": self.task_description,
            "acceptance_criteria": self.acceptance_criteria,
            "relevant_files": [str(f) for f in self.relevant_files],
            "parent_context": self.parent_context,
            "max_tokens": self.max_tokens,
        }


# =============================================================================
# TASK CONTEXT BUILDER
# =============================================================================


class TaskContextBuilder:
    """
    Build execution context for task implementation.

    TaskContextBuilder assembles all information an AI agent needs to
    implement a task, including the task description, acceptance criteria,
    relevant files, and a system prompt with execution instructions.

    Attributes:
        root: Path to the roadmap directory (.vibey/roadmap)

    Example:
        >>> builder = TaskContextBuilder(Path(".vibey/roadmap"))
        >>> context = builder.build_context(task)
        >>> print(context.system_prompt)
    """

    def __init__(self, roadmap_root: Path):
        """
        Initialize TaskContextBuilder with roadmap root directory.

        Args:
            roadmap_root: Path to .vibey/roadmap directory
        """
        self.root = roadmap_root

    def build_context(self, task: HierarchicalTicket) -> TaskContext:
        """
        Assemble complete context for task execution.

        Context includes:
        1. Task description and acceptance criteria
        2. Parent context (sprint goals, track objectives)
        3. Relevant files from task plan
        4. Dependency outputs (what completed tasks produced)
        5. System prompt with execution instructions

        Args:
            task: The HierarchicalTicket to build context for

        Returns:
            TaskContext with all execution context assembled
        """
        # Build task description
        task_description = self._build_task_description(task)

        # Extract acceptance criteria from task criteria
        acceptance_criteria = self._extract_acceptance_criteria(task)

        # Get relevant files from task and plan
        relevant_files = self.get_relevant_files(task)

        # Build parent context (sprint/track goals)
        parent_context = self._build_parent_context(task)

        # Build system prompt
        system_prompt = self.build_system_prompt(task)

        # Get max tokens if specified
        max_tokens = self._get_max_tokens(task)

        return TaskContext(
            task=task,
            system_prompt=system_prompt,
            task_description=task_description,
            acceptance_criteria=acceptance_criteria,
            relevant_files=relevant_files,
            parent_context=parent_context,
            max_tokens=max_tokens,
        )

    def load_task_plan(self, task: HierarchicalTicket) -> Optional[str]:
        """
        Load task plan markdown if it exists.

        Task plans are stored in .vibey/roadmap/context/tasks/{task_id}/

        Args:
            task: The HierarchicalTicket to load plan for

        Returns:
            Plan content as string, or None if no plan exists
        """
        # Check multiple possible plan file locations
        plan_paths = [
            self.root / "context" / "tasks" / task.id / "plan.md",
            self.root / "context" / "tasks" / task.id / "PLAN.md",
            self.root / "context" / "tasks" / task.id / "implementation.md",
            self.root / "context" / "tasks" / task.id / "IMPLEMENTATION.md",
        ]

        for plan_path in plan_paths:
            if plan_path.exists():
                try:
                    return plan_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Failed to read plan at {plan_path}: {e}")

        return None

    def get_relevant_files(self, task: HierarchicalTicket) -> List[Path]:
        """
        Extract file paths mentioned in task/plan.

        Parses the task description and plan for file path patterns
        and returns a list of paths that likely need modification.

        Args:
            task: The HierarchicalTicket to extract files for

        Returns:
            List of Path objects for relevant files
        """
        files: List[Path] = []
        seen: set = set()

        # Collect text to search for file paths
        text_sources = []

        # Add task description
        if task.description:
            text_sources.append(task.description)

        # Add plan content if available
        plan = self.load_task_plan(task)
        if plan:
            text_sources.append(plan)

        # Parse file paths from all text sources
        for text in text_sources:
            extracted = self._extract_file_paths(text)
            for file_path in extracted:
                if file_path not in seen:
                    seen.add(file_path)
                    files.append(Path(file_path))

        return files

    def build_system_prompt(self, task: HierarchicalTicket) -> str:
        """
        Generate system prompt for agent execution.

        Creates a prompt that tells the agent:
        - What task to complete
        - What files to modify
        - What success looks like

        Args:
            task: The HierarchicalTicket to generate prompt for

        Returns:
            System prompt string for agent execution
        """
        # Get relevant files for the prompt
        relevant_files = self.get_relevant_files(task)
        files_section = self._format_files_section(relevant_files)

        # Get acceptance criteria
        criteria = self._extract_acceptance_criteria(task)
        criteria_section = self._format_criteria_section(criteria)

        # Get task plan if available
        plan = self.load_task_plan(task)
        plan_section = self._format_plan_section(plan)

        # Build the system prompt
        prompt = f"""You are implementing a development task.

## Task Information

**Task ID:** {task.id}
**Task Name:** {task.name}
**Status:** {task.status.value}
**Priority:** {task.priority.value}

## Task Description

{task.description or "No description provided."}

{plan_section}

{files_section}

{criteria_section}

## Instructions

1. Read and understand the task requirements
2. Examine the relevant files listed above
3. Implement the changes needed to satisfy all acceptance criteria
4. Ensure your implementation is complete and follows project coding standards
5. Create commits with clear messages referencing this task

## Success Criteria

Your implementation is successful when ALL acceptance criteria are met.
The task should be fully functional without requiring additional work.

## Commit Message Format

Use this format for your commit messages:
```
<type>(<scope>): <description>

Task: {task.id}
```

Where type is one of: feat, fix, refactor, test, docs, chore
"""
        return prompt.strip()

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _build_task_description(self, task: HierarchicalTicket) -> str:
        """Build the full task description."""
        parts = []

        if task.name:
            parts.append(f"# {task.name}")

        if task.description:
            parts.append(task.description)

        # Add plan content if available
        plan = self.load_task_plan(task)
        if plan:
            parts.append("\n## Implementation Plan\n")
            parts.append(plan)

        return "\n\n".join(parts)

    def _extract_acceptance_criteria(self, task: HierarchicalTicket) -> List[str]:
        """
        Extract acceptance criteria from task criteria.

        Looks at criteria that block COMPLETED transition to determine
        what needs to be accomplished.
        """
        criteria_list = []

        # Get criteria that block completion
        for criterion in task.criteria:
            if criterion.blocks_transition_to == TicketStatus.COMPLETED:
                criteria_list.append(criterion.description)

        # If no criteria defined, provide a default
        if not criteria_list and task.description:
            criteria_list.append(f"Implement: {task.name}")

        return criteria_list

    def _build_parent_context(self, task: HierarchicalTicket) -> Optional[str]:
        """
        Build context from parent tickets (sprint/track goals).

        Traverses up the hierarchy to gather context about the
        broader goals this task contributes to.
        """
        context_parts = []

        try:
            # Try to get parent context via the loader
            if task.parent_ref and hasattr(task, 'parent') and task.parent:
                parent = task.parent
                if parent.name:
                    context_parts.append(f"**Sprint:** {parent.name}")
                if parent.description:
                    context_parts.append(f"Sprint Goal: {parent.description}")

                # Try to get track (grandparent) context
                if parent.parent_ref and hasattr(parent, 'parent') and parent.parent:
                    track = parent.parent
                    if track.name:
                        context_parts.append(f"**Track:** {track.name}")
                    if track.description:
                        context_parts.append(f"Track Objective: {track.description}")

        except Exception as e:
            logger.debug(f"Could not load parent context: {e}")

        return "\n".join(context_parts) if context_parts else None

    def _get_max_tokens(self, task: HierarchicalTicket) -> Optional[int]:
        """Get max tokens from task token budget if specified."""
        if task.total_token_budget is not None:
            return task.total_token_budget

        # Check output tokens budget as fallback
        if task.output_tokens and task.output_tokens.budget:
            return task.output_tokens.budget

        return None

    def _extract_file_paths(self, text: str) -> List[str]:
        """
        Extract file paths from text using pattern matching.

        Looks for common file path patterns like:
        - vibey/path/to/file.py
        - ./path/to/file.ts
        - /absolute/path/file.md
        - path/to/file.yaml
        """
        paths = []

        # Pattern for file paths with extensions
        # Matches paths like: vibey/cli/main.py, ./src/file.ts, path/to/file.yaml
        file_pattern = r'(?:^|[\s\`\"\'<>])([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]{1,10})(?:[\s\`\"\'<>]|$)'

        # Find all matches
        matches = re.findall(file_pattern, text)

        for match in matches:
            # Clean up the path
            path = match.strip()

            # Skip URLs and common non-file patterns
            if path.startswith('http') or path.startswith('www.'):
                continue

            # Skip version numbers like 3.9, 2.5.0
            if re.match(r'^\d+\.\d+', path):
                continue

            # Skip patterns that are clearly not file paths
            if path in ('e.g.', 'i.e.', 'etc.'):
                continue

            paths.append(path)

        return paths

    def _format_files_section(self, files: List[Path]) -> str:
        """Format the relevant files section for the prompt."""
        if not files:
            return "## Relevant Files\n\nNo specific files identified. Explore the codebase as needed."

        files_list = "\n".join(f"- `{f}`" for f in files)
        return f"## Relevant Files\n\nThe following files may need to be modified:\n\n{files_list}"

    def _format_criteria_section(self, criteria: List[str]) -> str:
        """Format the acceptance criteria section for the prompt."""
        if not criteria:
            return "## Acceptance Criteria\n\nNo specific acceptance criteria defined."

        criteria_list = "\n".join(f"- [ ] {c}" for c in criteria)
        return f"## Acceptance Criteria\n\nYour implementation must satisfy:\n\n{criteria_list}"

    def _format_plan_section(self, plan: Optional[str]) -> str:
        """Format the implementation plan section for the prompt."""
        if not plan:
            return ""

        return f"## Implementation Plan\n\n{plan}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TaskContext",
    "TaskContextBuilder",
]
