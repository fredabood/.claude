"""
Requirement system for the unified ticket architecture.

This module implements criterion templates that cascade down the ticket
hierarchy and instantiate as actual criteria when applicable.

Design Principle: Requirements are reusable criterion templates.
They define WHAT criteria should exist, not the criteria themselves.
When applied to a ticket, they generate actual Criterion instances.

Key Concepts:
- Requirement: A criterion template with inheritance behavior
- CriterionTemplate: Defines how to generate a Criterion
- ApplicabilityRules: When a requirement applies to a ticket
- RequirementResolver: Resolves effective requirements from hierarchy
- RequirementInstantiator: Converts requirements to criteria

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from vibey.roadmap.models.ticket.enums import (
    CriterionTargetType,
    EnforcementMode,
    InheritMode,
    TaskType,
    ThresholdComparison,
    TicketStatus,
    TicketType,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.completable import Criterion


class CriterionTemplate(BaseModel):
    """
    Template for generating criteria.

    CriterionTemplate defines HOW to generate a Criterion instance.
    It contains the target type, configuration, and description template
    that will be used when the requirement is instantiated on a ticket.

    Example:
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={
                "metric_name": "coverage",
                "threshold": 85.0,
                "comparison": "gte"
            },
            description_template="Test coverage must be at least {threshold}%"
        )
    """

    target_type: CriterionTargetType = Field(
        description="Type of criterion target to generate"
    )
    target_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific configuration for the target"
    )
    description_template: str = Field(
        description="Template string for criterion description (can use {ticket} placeholder)"
    )
    blocks_transition_to: TicketStatus = Field(
        default=TicketStatus.COMPLETED,
        description="Which state transition this criterion guards"
    )

    def render_description(self, ticket_id: str, ticket_name: str) -> str:
        """
        Render the description template with ticket info and config values.

        Args:
            ticket_id: ID of the ticket
            ticket_name: Name of the ticket

        Returns:
            Rendered description string
        """
        # Build context for template rendering
        context = {
            "ticket_id": ticket_id,
            "ticket_name": ticket_name,
            **self.target_config  # Include all config values
        }
        try:
            return self.description_template.format(**context)
        except KeyError:
            # If template has unknown placeholders, return as-is
            return self.description_template


class ApplicabilityRules(BaseModel):
    """
    Rules for when a requirement applies to a ticket.

    ApplicabilityRules defines CONDITIONS that must be met for a
    requirement to apply. If no rules are specified, the requirement
    applies to all tickets.

    Examples:
        # Apply only to tasks
        ApplicabilityRules(ticket_types=[TicketType.TASK])

        # Apply only to development tasks
        ApplicabilityRules(task_types=[TaskType.DEVELOPMENT])

        # Apply to tickets with code deliverables
        ApplicabilityRules(has_file_patterns=["*.py", "*.ts", "*.js"])

        # Apply to tickets with test criteria
        ApplicabilityRules(has_criterion_types=[CriterionTargetType.TEST_PASSES])
    """

    ticket_types: Optional[List[TicketType]] = Field(
        default=None,
        description="Only apply to these ticket types (roadmap, track, sprint, task)"
    )
    task_types: Optional[List[TaskType]] = Field(
        default=None,
        description="Only apply to these task types (development, documentation, etc.)"
    )
    has_criterion_types: Optional[List[CriterionTargetType]] = Field(
        default=None,
        description="Only apply if ticket has criteria of these types"
    )
    has_file_patterns: Optional[List[str]] = Field(
        default=None,
        description="Only apply if ticket has file criteria matching these patterns"
    )
    exclude_ticket_types: Optional[List[TicketType]] = Field(
        default=None,
        description="Exclude these ticket types"
    )
    exclude_task_types: Optional[List[TaskType]] = Field(
        default=None,
        description="Exclude these task types"
    )

    def matches(
        self,
        ticket_type: Optional[TicketType] = None,
        task_type: Optional[TaskType] = None,
        criterion_types: Optional[List[CriterionTargetType]] = None,
        file_paths: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if this requirement applies to a ticket.

        All specified rules must match (AND logic).
        Unspecified rules are considered to match.

        Args:
            ticket_type: The ticket's type (roadmap, track, sprint, task)
            task_type: The task's type (if ticket is a task)
            criterion_types: Types of criteria the ticket has
            file_paths: File paths from FileExistsTarget criteria

        Returns:
            True if all specified rules match
        """
        # Check ticket type inclusion
        if self.ticket_types is not None:
            if ticket_type is None or ticket_type not in self.ticket_types:
                return False

        # Check ticket type exclusion
        if self.exclude_ticket_types is not None:
            if ticket_type in self.exclude_ticket_types:
                return False

        # Check task type inclusion
        if self.task_types is not None:
            if task_type is None or task_type not in self.task_types:
                return False

        # Check task type exclusion
        if self.exclude_task_types is not None:
            if task_type in self.exclude_task_types:
                return False

        # Check has criterion types
        if self.has_criterion_types is not None:
            if criterion_types is None:
                return False
            if not any(ct in criterion_types for ct in self.has_criterion_types):
                return False

        # Check has file patterns
        if self.has_file_patterns is not None:
            if not self._matches_file_patterns(file_paths):
                return False

        return True

    def _matches_file_patterns(self, file_paths: Optional[List[str]]) -> bool:
        """Check if any file path matches any pattern."""
        if file_paths is None or not file_paths:
            return False

        import fnmatch

        for path in file_paths:
            for pattern in self.has_file_patterns or []:
                if fnmatch.fnmatch(path, pattern):
                    return True
        return False


class Requirement(BaseModel):
    """
    A criterion template that cascades down the ticket hierarchy.

    Requirements are defined on parent tickets and cascade to children.
    When a ticket is created/updated, its effective requirements are
    resolved and instantiated as actual Criterion objects.

    Inheritance Behavior:
    - INHERIT: Use stricter of local vs ancestor requirement
    - OVERRIDE: Replace ancestor requirement entirely
    - SKIP: Explicitly mark as not applicable (requires justification)

    Enforcement:
    - BLOCKING: Prevents status transition if criterion not met
    - WARNING: Shows warning but allows transition
    - AUDIT: Logs only, no user feedback

    Example:
        Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Code must have test coverage",
            criterion_template=CriterionTemplate(
                target_type=CriterionTargetType.THRESHOLD,
                target_config={"metric_name": "coverage", "threshold": 85.0},
                description_template="Test coverage >= {threshold}%"
            ),
            applicability=ApplicabilityRules(
                has_file_patterns=["*.py"]
            ),
            inherit_mode=InheritMode.INHERIT,
            enforcement=EnforcementMode.BLOCKING
        )
    """

    # Identity
    id: str = Field(description="Unique identifier for this requirement")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="What this requirement enforces")

    # Template
    criterion_template: CriterionTemplate = Field(
        description="Template for generating criterion"
    )

    # Applicability
    applicability: ApplicabilityRules = Field(
        default_factory=ApplicabilityRules,
        description="Rules for when this requirement applies"
    )

    # Inheritance
    inherit_mode: InheritMode = Field(
        default=InheritMode.INHERIT,
        description="How this requirement interacts with inherited requirements"
    )

    # Enforcement
    enforcement: EnforcementMode = Field(
        default=EnforcementMode.BLOCKING,
        description="How strictly this requirement is enforced"
    )

    # Enforceability (set by ancestors)
    enforceable: bool = Field(
        default=False,
        description="If True, descendants cannot OVERRIDE or SKIP this requirement"
    )

    # Skip justification
    skip_justification: Optional[str] = Field(
        default=None,
        description="Required justification when inherit_mode=SKIP"
    )

    @model_validator(mode="after")
    def validate_skip_justification(self) -> "Requirement":
        """Ensure SKIP mode has justification."""
        if self.inherit_mode == InheritMode.SKIP and not self.skip_justification:
            raise ValueError(
                f"Requirement '{self.id}' with SKIP mode requires skip_justification"
            )
        return self

    def is_applicable(
        self,
        ticket_type: Optional[TicketType] = None,
        task_type: Optional[TaskType] = None,
        criterion_types: Optional[List[CriterionTargetType]] = None,
        file_paths: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if this requirement applies to a ticket.

        Args:
            ticket_type: The ticket's type
            task_type: The task's type (if applicable)
            criterion_types: Types of criteria the ticket has
            file_paths: File paths from FileExistsTarget criteria

        Returns:
            True if requirement applies
        """
        return self.applicability.matches(
            ticket_type=ticket_type,
            task_type=task_type,
            criterion_types=criterion_types,
            file_paths=file_paths,
        )

    def compare_strictness(self, other: "Requirement") -> int:
        """
        Compare strictness of this requirement vs another.

        Used in INHERIT mode to determine which requirement to use.
        Returns:
            -1: this is less strict
            0: equal strictness
            1: this is more strict

        For threshold-based requirements:
        - GTE/GT: higher threshold is stricter
        - LTE/LT: lower threshold is stricter
        - EQ: only equal if same threshold
        """
        if self.id != other.id:
            raise ValueError("Can only compare requirements with same ID")

        # Get thresholds from config
        my_threshold = self.criterion_template.target_config.get("threshold")
        other_threshold = other.criterion_template.target_config.get("threshold")

        if my_threshold is None or other_threshold is None:
            # Non-threshold requirements: compare by enforcement strictness
            enforcement_order = [
                EnforcementMode.AUDIT,
                EnforcementMode.WARNING,
                EnforcementMode.BLOCKING,
            ]
            my_idx = enforcement_order.index(self.enforcement)
            other_idx = enforcement_order.index(other.enforcement)
            if my_idx > other_idx:
                return 1
            elif my_idx < other_idx:
                return -1
            return 0

        # Threshold comparison depends on comparison type
        comparison = self.criterion_template.target_config.get(
            "comparison", ThresholdComparison.GTE
        )
        if isinstance(comparison, str):
            comparison = ThresholdComparison(comparison)

        if comparison in (ThresholdComparison.GTE, ThresholdComparison.GT):
            # Higher is stricter
            if my_threshold > other_threshold:
                return 1
            elif my_threshold < other_threshold:
                return -1
        elif comparison in (ThresholdComparison.LTE, ThresholdComparison.LT):
            # Lower is stricter
            if my_threshold < other_threshold:
                return 1
            elif my_threshold > other_threshold:
                return -1
        # EQ: equal only if same threshold
        return 0

    def get_stricter(self, other: "Requirement") -> "Requirement":
        """Return the stricter of this requirement and another."""
        cmp = self.compare_strictness(other)
        return self if cmp >= 0 else other


class RequirementResolver:
    """
    Resolves effective requirements for a ticket.

    The resolver collects requirements from the ticket's ancestors
    (roadmap → track → sprint) and local requirements, then resolves
    inheritance to produce the final set of effective requirements.

    Algorithm:
    1. Gather requirements from ancestors (parent first)
    2. Partition inherited into enforceable vs non-enforceable
    3. For each local requirement:
       - If ancestor is enforceable: use ancestor (cannot override)
       - If OVERRIDE: replace ancestor requirement
       - If SKIP: exclude requirement (with justification)
       - If INHERIT: use stricter of local vs ancestor
    4. Filter to only applicable requirements
    5. Return final list
    """

    def resolve(
        self,
        local_requirements: List[Requirement],
        ancestor_requirements: List[Requirement],
        ticket_type: Optional[TicketType] = None,
        task_type: Optional[TaskType] = None,
        criterion_types: Optional[List[CriterionTargetType]] = None,
        file_paths: Optional[List[str]] = None,
    ) -> List[Requirement]:
        """
        Resolve effective requirements for a ticket.

        Args:
            local_requirements: Requirements defined on this ticket
            ancestor_requirements: Requirements inherited from ancestors
            ticket_type: The ticket's type
            task_type: The task's type (if applicable)
            criterion_types: Types of criteria the ticket has
            file_paths: File paths from FileExistsTarget criteria

        Returns:
            List of effective requirements after resolution
        """
        effective: List[Requirement] = []
        processed_ids: set = set()

        # Index inherited requirements by ID
        inherited_by_id: Dict[str, Requirement] = {
            r.id: r for r in ancestor_requirements
        }

        # First pass: enforceable requirements from ancestors
        for req in ancestor_requirements:
            if req.enforceable:
                effective.append(req)
                processed_ids.add(req.id)

        # Second pass: process local requirements
        for local_req in local_requirements:
            # Skip if already handled by enforceable ancestor
            if local_req.id in processed_ids:
                continue

            if local_req.inherit_mode == InheritMode.SKIP:
                # Skip requires justification (validated in Requirement)
                processed_ids.add(local_req.id)
                continue

            if local_req.inherit_mode == InheritMode.OVERRIDE:
                # Override: use local requirement
                effective.append(local_req)
                processed_ids.add(local_req.id)
                continue

            # INHERIT mode: use stricter of local vs ancestor
            inherited = inherited_by_id.get(local_req.id)
            if inherited:
                stricter = local_req.get_stricter(inherited)
                effective.append(stricter)
            else:
                effective.append(local_req)
            processed_ids.add(local_req.id)

        # Third pass: add inherited requirements not overridden locally
        for req in ancestor_requirements:
            if req.id not in processed_ids:
                effective.append(req)

        # Filter to applicable requirements
        return [
            r for r in effective
            if r.is_applicable(
                ticket_type=ticket_type,
                task_type=task_type,
                criterion_types=criterion_types,
                file_paths=file_paths,
            )
        ]


class RequirementInstantiator:
    """
    Instantiates requirements as criteria on a ticket.

    The instantiator takes resolved requirements and generates actual
    Criterion objects that can be added to a ticket's criteria list.

    This is called when:
    - Ticket is created
    - Ticket criteria are modified (may affect applicability)
    - Requirements are updated on ancestors
    """

    def instantiate(
        self,
        requirements: List[Requirement],
        ticket_id: str,
        ticket_name: str,
    ) -> List["Criterion"]:
        """
        Convert requirements to criteria for a ticket.

        Args:
            requirements: Resolved requirements to instantiate
            ticket_id: ID of the ticket
            ticket_name: Name of the ticket

        Returns:
            List of Criterion objects ready to be added to ticket
        """
        from vibey.roadmap.models.ticket.completable import Criterion
        from vibey.roadmap.models.ticket.targets import create_target

        criteria = []
        for req in requirements:
            template = req.criterion_template

            # Create target from template config
            target = create_target(template.target_type, template.target_config)

            # Generate criterion
            criterion = Criterion(
                id=f"{req.id}-{ticket_id}",
                description=template.render_description(ticket_id, ticket_name),
                target=target,
                blocks_transition_to=template.blocks_transition_to,
                required=req.enforcement == EnforcementMode.BLOCKING,
            )
            criteria.append(criterion)

        return criteria


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CriterionTemplate",
    "ApplicabilityRules",
    "Requirement",
    "RequirementResolver",
    "RequirementInstantiator",
]
