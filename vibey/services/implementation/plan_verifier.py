"""
TaskPlanVerifier - Plan validation and generation for Implementation Mode.

This module provides the TaskPlanVerifier class for validating that tasks
have comprehensive implementation plans and generating plans when needed.

Plans are stored in the context directory structure:
.vibey/roadmap/context/sprints/{sprint-slug}/tasks/{task-slug}/TASK_PLAN.md

Required plan sections:
- Objective
- Approach (step-by-step)
- Files to modify/create
- Acceptance Criteria mapping table
- Risks and mitigations
- Estimates (tokens, complexity)

Usage:
    from vibey.services.implementation import TaskPlanVerifier
    from pathlib import Path

    # Initialize with context root
    verifier = TaskPlanVerifier(context_root=Path(".vibey/roadmap/context"))

    # Check if task has a valid plan
    if verifier.has_plan(task):
        plan = verifier.load_plan(task)
        print(f"Plan loaded: {len(plan)} characters")
    else:
        # Generate a plan
        plan = await verifier.generate_plan(task)
        verifier.save_plan(task, plan)

Design Reference:
- Implementation Mode Track Sprint 5
- Context System V2 Architecture
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================


# Required sections in a valid task plan
REQUIRED_PLAN_SECTIONS = [
    "Objective",
    "Approach",
    "Files",
    "Acceptance Criteria",
    "Risks",
    "Estimates",
]

# Section header patterns (case-insensitive)
SECTION_PATTERNS = {
    "Objective": r"^#+\s*(?:Objective|Goal|Purpose)",
    "Approach": r"^#+\s*(?:Approach|Steps|Implementation\s+Steps|Step-by-Step)",
    "Files": r"^#+\s*(?:Files|Files\s+to\s+(?:Modify|Create|Change))",
    "Acceptance Criteria": r"^#+\s*(?:Acceptance\s+Criteria|Criteria|Success\s+Criteria)",
    "Risks": r"^#+\s*(?:Risks|Risks\s+(?:and|&)\s+Mitigations)",
    "Estimates": r"^#+\s*(?:Estimates|Token\s+Estimates|Complexity)",
}


# Default plan template
PLAN_TEMPLATE = """# Task Plan: {task_name}

**Task ID:** {task_id}
**Sprint:** {sprint_slug}
**Created:** {created_at}

---

## Objective

{objective}

---

## Approach

### Step-by-Step Implementation

{approach_steps}

---

## Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
{files_table}

---

## Acceptance Criteria Mapping

| Criterion | Implementation | Verification |
|-----------|----------------|--------------|
{criteria_table}

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
{risks_table}

---

## Estimates

- **Complexity:** {complexity}
- **Estimated Input Tokens:** {input_tokens}
- **Estimated Output Tokens:** {output_tokens}
- **Confidence:** {confidence}

---

## Notes

{notes}
"""


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PlanValidationResult:
    """Result of plan validation."""

    is_valid: bool
    missing_sections: List[str] = field(default_factory=list)
    present_sections: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def completeness(self) -> float:
        """Calculate plan completeness as a percentage."""
        total = len(REQUIRED_PLAN_SECTIONS)
        present = len(self.present_sections)
        return (present / total) * 100 if total > 0 else 0.0


@dataclass
class PlanTemplate:
    """Template for generating task plans."""

    task_name: str
    task_id: str
    sprint_slug: str
    objective: str = ""
    approach_steps: str = ""
    files_table: str = ""
    criteria_table: str = ""
    risks_table: str = ""
    complexity: str = "moderate"
    input_tokens: str = "~5,000"
    output_tokens: str = "~2,000"
    confidence: str = "medium"
    notes: str = ""

    def render(self) -> str:
        """Render the template to markdown."""
        return PLAN_TEMPLATE.format(
            task_name=self.task_name,
            task_id=self.task_id,
            sprint_slug=self.sprint_slug,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            objective=self.objective or "(To be filled)",
            approach_steps=self.approach_steps or "1. (To be filled)",
            files_table=self.files_table or "| (To be filled) | | |",
            criteria_table=self.criteria_table or "| (To be filled) | | |",
            risks_table=self.risks_table or "| (To be filled) | | |",
            complexity=self.complexity,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            confidence=self.confidence,
            notes=self.notes or "(No additional notes)",
        )


# =============================================================================
# TASK PLAN VERIFIER
# =============================================================================


class TaskPlanVerifier:
    """
    Verify and manage task implementation plans.

    TaskPlanVerifier provides methods to:
    - Check if a task has a comprehensive plan
    - Validate plan structure and content
    - Generate plan templates
    - Load and save plans

    Plans are stored in the context directory structure:
    .vibey/roadmap/context/sprints/{sprint-slug}/tasks/{task-slug}/TASK_PLAN.md

    Attributes:
        context_root: Path to the context directory (.vibey/roadmap/context)

    Example:
        >>> verifier = TaskPlanVerifier(Path(".vibey/roadmap/context"))
        >>> if verifier.has_plan(task):
        ...     plan = verifier.load_plan(task)
        ... else:
        ...     plan = await verifier.generate_plan(task)
        ...     verifier.save_plan(task, plan)
    """

    def __init__(self, context_root: Path):
        """
        Initialize TaskPlanVerifier with context root directory.

        Args:
            context_root: Path to .vibey/roadmap/context directory
        """
        self.context_root = context_root

    # =========================================================================
    # PLAN PATH RESOLUTION
    # =========================================================================

    def get_plan_path(self, task: HierarchicalTicket) -> Path:
        """
        Get the path to a task's plan file.

        Plan files are stored at:
        {context_root}/sprints/{sprint-slug}/tasks/{task-slug}/TASK_PLAN.md

        Args:
            task: The HierarchicalTicket to get path for

        Returns:
            Path to the TASK_PLAN.md file (may not exist)
        """
        sprint_slug = self._get_sprint_slug(task)
        task_slug = self._get_task_slug(task)

        return (
            self.context_root
            / "sprints"
            / sprint_slug
            / "tasks"
            / task_slug
            / "TASK_PLAN.md"
        )

    def _get_sprint_slug(self, task: HierarchicalTicket) -> str:
        """
        Get the sprint slug for a task.

        Falls back to parent_ref or task ID if slug is not available.
        """
        # Try to get sprint from parent
        if task.parent_ref:
            # If task has a parent loaded, use its slug
            if hasattr(task, 'parent') and task.parent:
                parent = task.parent
                if hasattr(parent, 'slug') and parent.slug:
                    return parent.slug
            # Fall back to parent_ref as slug
            return task.parent_ref

        # No parent - use task's own context
        return task.slug if task.slug else task.id

    def _get_task_slug(self, task: HierarchicalTicket) -> str:
        """
        Get the task slug.

        Falls back to task ID if slug is not available.
        """
        if task.slug:
            return task.slug

        # Generate slug from name if available
        if task.name:
            # Convert to slug: lowercase, replace spaces with hyphens
            slug = task.name.lower()
            slug = re.sub(r'[^a-z0-9]+', '-', slug)
            slug = slug.strip('-')
            if slug:
                return slug

        # Fall back to ID
        return task.id

    # =========================================================================
    # PLAN EXISTENCE AND VALIDATION
    # =========================================================================

    def has_plan(self, task: HierarchicalTicket) -> bool:
        """
        Check if a task has a comprehensive plan.

        A task "has a plan" if:
        1. The plan file exists
        2. The plan is valid (has all required sections)

        Args:
            task: The HierarchicalTicket to check

        Returns:
            True if task has a valid plan, False otherwise
        """
        plan_path = self.get_plan_path(task)

        if not plan_path.exists():
            logger.debug(f"No plan file at {plan_path}")
            return False

        # Check if plan is valid
        result = self.is_plan_valid(plan_path)
        if not result.is_valid:
            logger.debug(
                f"Plan at {plan_path} is invalid. "
                f"Missing sections: {result.missing_sections}"
            )
            return False

        return True

    def is_plan_valid(self, plan_path: Path) -> PlanValidationResult:
        """
        Validate that a plan has all required sections.

        Required sections:
        - Objective
        - Approach (step-by-step)
        - Files to modify/create
        - Acceptance Criteria mapping table
        - Risks and mitigations
        - Estimates (tokens, complexity)

        Args:
            plan_path: Path to the TASK_PLAN.md file

        Returns:
            PlanValidationResult with validation details
        """
        if not plan_path.exists():
            return PlanValidationResult(
                is_valid=False,
                missing_sections=list(REQUIRED_PLAN_SECTIONS),
                present_sections=[],
                warnings=["Plan file does not exist"],
            )

        try:
            content = plan_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read plan at {plan_path}: {e}")
            return PlanValidationResult(
                is_valid=False,
                missing_sections=list(REQUIRED_PLAN_SECTIONS),
                present_sections=[],
                warnings=[f"Failed to read plan: {e}"],
            )

        # Check for each required section
        present_sections: List[str] = []
        missing_sections: List[str] = []
        warnings: List[str] = []

        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                present_sections.append(section_name)
            else:
                missing_sections.append(section_name)

        # Check for content after section headers (not just empty sections)
        for section in present_sections:
            pattern = SECTION_PATTERNS[section]
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                # Get content after the header until next header or end
                start = match.end()
                next_header = re.search(r'^#+\s+', content[start:], re.MULTILINE)
                if next_header:
                    section_content = content[start:start + next_header.start()]
                else:
                    section_content = content[start:]

                # Check if section has meaningful content
                stripped = section_content.strip()
                if not stripped or stripped in ("", "(To be filled)", "-"):
                    warnings.append(f"Section '{section}' appears to be empty")

        is_valid = len(missing_sections) == 0

        return PlanValidationResult(
            is_valid=is_valid,
            missing_sections=missing_sections,
            present_sections=present_sections,
            warnings=warnings,
        )

    # =========================================================================
    # PLAN LOADING AND SAVING
    # =========================================================================

    def load_plan(self, task: HierarchicalTicket) -> Optional[str]:
        """
        Load an existing plan for a task.

        Args:
            task: The HierarchicalTicket to load plan for

        Returns:
            Plan content as string, or None if no plan exists
        """
        plan_path = self.get_plan_path(task)

        if not plan_path.exists():
            logger.debug(f"No plan found at {plan_path}")
            return None

        try:
            return plan_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read plan at {plan_path}: {e}")
            return None

    def save_plan(self, task: HierarchicalTicket, plan_content: str) -> Path:
        """
        Save a plan to the task's context directory.

        Creates the directory structure if it doesn't exist.

        Args:
            task: The HierarchicalTicket to save plan for
            plan_content: The plan content to save

        Returns:
            Path to the saved plan file
        """
        plan_path = self.get_plan_path(task)

        # Create directory structure
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        # Write plan
        try:
            plan_path.write_text(plan_content, encoding="utf-8")
            logger.info(f"Saved plan to {plan_path}")
        except Exception as e:
            logger.error(f"Failed to save plan to {plan_path}: {e}")
            raise

        return plan_path

    # =========================================================================
    # PLAN GENERATION
    # =========================================================================

    async def generate_plan(self, task: HierarchicalTicket) -> str:
        """
        Generate a plan for a task using a template.

        This method creates a plan template pre-populated with:
        - Task information (name, ID, description)
        - Acceptance criteria from the task
        - Initial file list from task description
        - Placeholder sections for approach and risks

        For AI-powered plan generation, extend this method or use an
        external service to fill in the template.

        Args:
            task: The HierarchicalTicket to generate plan for

        Returns:
            Generated plan content as markdown string
        """
        sprint_slug = self._get_sprint_slug(task)

        # Build approach steps from task description
        approach_steps = self._generate_approach_from_description(task)

        # Build files table from task description
        files_table = self._generate_files_table(task)

        # Build criteria table from task criteria
        criteria_table = self._generate_criteria_table(task)

        # Default risks
        risks_table = self._generate_default_risks()

        # Extract estimates from task if available
        complexity, input_tokens, output_tokens = self._extract_estimates(task)

        # Build objective from description
        objective = task.description or f"Implement: {task.name}"

        # Create template
        template = PlanTemplate(
            task_name=task.name or "Untitled Task",
            task_id=task.id,
            sprint_slug=sprint_slug,
            objective=objective,
            approach_steps=approach_steps,
            files_table=files_table,
            criteria_table=criteria_table,
            risks_table=risks_table,
            complexity=complexity,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            confidence="medium",
            notes="",
        )

        return template.render()

    def _generate_approach_from_description(
        self, task: HierarchicalTicket
    ) -> str:
        """Generate approach steps from task description."""
        if not task.description:
            return "1. Read and understand the task requirements\n2. (To be filled)"

        # Basic step generation - can be enhanced with AI
        steps = [
            "1. Read and understand the task requirements",
            "2. Review relevant existing code",
        ]

        # Add steps based on common patterns in description
        desc_lower = task.description.lower()

        if "test" in desc_lower:
            steps.append("3. Write tests for the new functionality")
        if "create" in desc_lower or "implement" in desc_lower:
            steps.append("4. Implement the required changes")
        if "update" in desc_lower or "modify" in desc_lower:
            steps.append("4. Update the existing code")
        if "document" in desc_lower or "docs" in desc_lower:
            steps.append("5. Update documentation")

        steps.append(f"{len(steps) + 1}. Verify all acceptance criteria are met")
        steps.append(f"{len(steps) + 1}. Commit changes with proper message")

        return "\n".join(steps)

    def _generate_files_table(self, task: HierarchicalTicket) -> str:
        """Generate files table from task description."""
        files: List[Tuple[str, str, str]] = []

        if task.description:
            # Extract file paths from description
            # Pattern matches paths like: vibey/path/file.py, ./src/file.ts
            file_pattern = r'(?:^|[\s\`\"\'<>])([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]{1,10})(?:[\s\`\"\'<>]|$)'
            matches = re.findall(file_pattern, task.description)

            for match in matches:
                path = match.strip()
                # Skip URLs and common non-file patterns
                if path.startswith('http') or path.startswith('www.'):
                    continue
                if re.match(r'^\d+\.\d+', path):
                    continue

                files.append((f"`{path}`", "Modify", "(To be determined)"))

        if not files:
            return "| (To be filled) | Create/Modify | |"

        return "\n".join(
            f"| {path} | {action} | {desc} |"
            for path, action, desc in files
        )

    def _generate_criteria_table(self, task: HierarchicalTicket) -> str:
        """Generate criteria table from task criteria."""
        rows: List[str] = []

        for criterion in task.criteria:
            rows.append(
                f"| {criterion.description} | (To be filled) | (To be filled) |"
            )

        if not rows:
            # Add default row based on task name
            rows.append(f"| Implement: {task.name} | (To be filled) | (To be filled) |")

        return "\n".join(rows)

    def _generate_default_risks(self) -> str:
        """Generate default risk table."""
        default_risks = [
            ("Scope creep", "Medium", "Focus on acceptance criteria only"),
            ("Breaking existing functionality", "Medium", "Run full test suite before/after"),
            ("Incomplete understanding", "Low", "Review task description carefully"),
        ]

        return "\n".join(
            f"| {risk} | {impact} | {mitigation} |"
            for risk, impact, mitigation in default_risks
        )

    def _extract_estimates(
        self, task: HierarchicalTicket
    ) -> Tuple[str, str, str]:
        """Extract estimates from task token budgets."""
        complexity = "moderate"
        input_tokens = "~5,000"
        output_tokens = "~2,000"

        # Get complexity from task if available
        if hasattr(task, 'complexity') and task.complexity:
            complexity = task.complexity

        # Get token estimates if available
        if task.input_tokens and task.input_tokens.estimate:
            target = task.input_tokens.estimate.target
            if target:
                input_tokens = f"~{target:,}"

        if task.output_tokens and task.output_tokens.estimate:
            target = task.output_tokens.estimate.target
            if target:
                output_tokens = f"~{target:,}"

        return complexity, input_tokens, output_tokens


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TaskPlanVerifier",
    "PlanValidationResult",
    "PlanTemplate",
    "REQUIRED_PLAN_SECTIONS",
]
