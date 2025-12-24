"""
Budget Validator Service for hierarchical token budget constraints.

This service provides optional validation for hierarchical budget relationships
between parent and child tickets. The validation is controlled by
TokenEnforcement.require_children_sum_valid flag.

Always-On Validation (in Ticket model):
1. TokenEstimate: min <= target <= max (validated in TokenEstimate model)
2. Tokens: budget >= estimate.target (validated in Tokens model)
3. Ticket: total_token_budget >= sum of input+output budgets (validated in Ticket model)

Optional Hierarchical Validation (this service):
4. Parent budget >= sum of children budgets (per direction)
5. Parent total_token_budget >= sum of children total_token_budgets

Usage:
    from vibey.services.budget_validator import BudgetValidator, ValidationError

    validator = BudgetValidator()

    # Validate hierarchical constraints for a parent ticket
    errors = validator.validate_children_sum(parent_ticket, direction='input')
    if errors:
        for error in errors:
            print(f"Validation error: {error.message}")

    # Validate when changing a child's budget
    error = validator.validate_on_child_budget_change(
        child_ticket,
        new_budget=5000,
        direction='input'
    )
    if error:
        print(f"Cannot set budget: {error.message}")

Design Reference: Sprint 3 - Budget Enforcement
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket import HierarchicalTicket


# =============================================================================
# VALIDATION ERROR
# =============================================================================


@dataclass
class BudgetValidationError:
    """
    Represents a budget validation failure.

    Attributes:
        message: Human-readable error message
        direction: Token direction that failed ('input', 'output', or 'total')
        parent_id: ID of the parent ticket
        parent_budget: Parent's budget for the direction
        children_sum: Sum of children's budgets
        child_id: Optional ID of the specific child causing the issue
    """

    message: str
    direction: str
    parent_id: str
    parent_budget: int
    children_sum: int
    child_id: Optional[str] = None


# =============================================================================
# TICKET LOADER PROTOCOL
# =============================================================================


class TicketLoader(Protocol):
    """Protocol for loading tickets by ID."""

    def load(self, ticket_id: str) -> "HierarchicalTicket":
        """Load a ticket by its ID."""
        ...


# =============================================================================
# BUDGET VALIDATOR SERVICE
# =============================================================================


class BudgetValidator:
    """
    Validates hierarchical token budget constraints.

    This validator checks optional constraints that are only enforced when
    TokenEnforcement.require_children_sum_valid is True on the parent ticket.

    Key Behaviors:
    - Only validates when enforcement flag is enabled
    - Validates per-direction (input, output) and total budgets
    - Can validate existing state or prospective changes
    - Returns structured error objects for programmatic handling
    """

    def __init__(self, loader: Optional[TicketLoader] = None):
        """
        Initialize the validator with an optional ticket loader.

        Args:
            loader: Optional TicketLoader for fetching related tickets.
                   If not provided, the validator will use HierarchicalTicket._loader.
        """
        self._loader = loader

    def _get_loader(self, ticket: "HierarchicalTicket") -> Optional[TicketLoader]:
        """Get the ticket loader, preferring explicit loader over class-level."""
        if self._loader is not None:
            return self._loader
        # Try to use the class-level loader from HierarchicalTicket
        return getattr(ticket.__class__, '_loader', None)

    def _get_budget(
        self,
        ticket: "HierarchicalTicket",
        direction: str
    ) -> Optional[int]:
        """
        Get the budget for a specific direction.

        Args:
            ticket: The ticket to get budget from
            direction: 'input', 'output', or 'total'

        Returns:
            The budget value or None if not set
        """
        if direction == 'input':
            return ticket.input_tokens.budget if ticket.input_tokens else None
        elif direction == 'output':
            return ticket.output_tokens.budget if ticket.output_tokens else None
        elif direction == 'total':
            return ticket.total_token_budget
        else:
            raise ValueError(f"Invalid direction: {direction}. Must be 'input', 'output', or 'total'")

    def _get_enforcement(
        self,
        ticket: "HierarchicalTicket",
        direction: str
    ) -> Optional["TokenEnforcement"]:
        """
        Get the enforcement settings for a specific direction.

        Args:
            ticket: The ticket to get enforcement from
            direction: 'input', 'output', or 'total'

        Returns:
            TokenEnforcement settings or None
        """
        if direction == 'input':
            return ticket.input_tokens.enforcement if ticket.input_tokens else None
        elif direction == 'output':
            return ticket.output_tokens.enforcement if ticket.output_tokens else None
        elif direction == 'total':
            return ticket.total_token_enforcement
        else:
            raise ValueError(f"Invalid direction: {direction}. Must be 'input', 'output', or 'total'")

    def _requires_children_sum_valid(
        self,
        ticket: "HierarchicalTicket",
        direction: str
    ) -> bool:
        """
        Check if require_children_sum_valid is enabled for the direction.

        Args:
            ticket: The ticket to check
            direction: 'input', 'output', or 'total'

        Returns:
            True if hierarchical validation is required
        """
        enforcement = self._get_enforcement(ticket, direction)
        if enforcement is None:
            return False
        return enforcement.require_children_sum_valid

    def validate_children_sum(
        self,
        parent: "HierarchicalTicket",
        direction: str,
    ) -> Optional[BudgetValidationError]:
        """
        Validate that sum(children budgets) <= parent budget.

        Only runs if parent enforcement has require_children_sum_valid=True.

        Args:
            parent: The parent ticket to validate
            direction: Token direction ('input', 'output', or 'total')

        Returns:
            BudgetValidationError if validation fails, None if passes or skipped
        """
        # Skip validation if not enabled
        if not self._requires_children_sum_valid(parent, direction):
            return None

        # Get parent budget
        parent_budget = self._get_budget(parent, direction)
        if parent_budget is None:
            return None  # No parent budget to validate against

        # Calculate children sum
        children_sum = 0
        for child in parent.children_tickets:
            child_budget = self._get_budget(child, direction)
            if child_budget is not None:
                children_sum += child_budget

        if children_sum > parent_budget:
            return BudgetValidationError(
                message=(
                    f"{direction} budget sum of children ({children_sum:,}) "
                    f"exceeds parent budget ({parent_budget:,})"
                ),
                direction=direction,
                parent_id=parent.id,
                parent_budget=parent_budget,
                children_sum=children_sum,
            )

        return None

    def validate_on_child_budget_change(
        self,
        child: "HierarchicalTicket",
        new_budget: int,
        direction: str,
    ) -> Optional[BudgetValidationError]:
        """
        Validate when a child's budget is set or changed.

        Checks if new budget would violate parent's constraint.

        Args:
            child: The child ticket being updated
            new_budget: The proposed new budget value
            direction: Token direction ('input', 'output', or 'total')

        Returns:
            BudgetValidationError if change would violate constraint, None if allowed
        """
        # Get parent
        parent = child.parent
        if parent is None:
            return None  # No parent, no constraint to check

        # Skip if parent doesn't require children sum validation
        if not self._requires_children_sum_valid(parent, direction):
            return None

        # Get parent budget
        parent_budget = self._get_budget(parent, direction)
        if parent_budget is None:
            return None  # No parent budget to validate against

        # Calculate what the sum would be with the new budget
        current_child_budget = self._get_budget(child, direction) or 0
        other_children_sum = 0
        for sibling in parent.children_tickets:
            if sibling.id != child.id:
                sibling_budget = self._get_budget(sibling, direction)
                if sibling_budget is not None:
                    other_children_sum += sibling_budget

        new_sum = other_children_sum + new_budget

        if new_sum > parent_budget:
            return BudgetValidationError(
                message=(
                    f"Setting {direction} budget to {new_budget:,} would make "
                    f"children sum ({new_sum:,}) exceed parent budget ({parent_budget:,})"
                ),
                direction=direction,
                parent_id=parent.id,
                parent_budget=parent_budget,
                children_sum=new_sum,
                child_id=child.id,
            )

        return None

    def validate_all_directions(
        self,
        parent: "HierarchicalTicket",
    ) -> List[BudgetValidationError]:
        """
        Validate children sum for all directions (input, output, total).

        Convenience method that checks all three directions at once.

        Args:
            parent: The parent ticket to validate

        Returns:
            List of BudgetValidationError for any failing validations
        """
        errors = []
        for direction in ('input', 'output', 'total'):
            error = self.validate_children_sum(parent, direction)
            if error:
                errors.append(error)
        return errors

    def can_create_child(
        self,
        parent: "HierarchicalTicket",
        child_input_budget: Optional[int] = None,
        child_output_budget: Optional[int] = None,
        child_total_budget: Optional[int] = None,
    ) -> List[BudgetValidationError]:
        """
        Check if a new child with proposed budgets can be created.

        Validates that adding a child with the specified budgets would not
        violate parent constraints.

        Args:
            parent: The parent ticket
            child_input_budget: Proposed input budget for new child
            child_output_budget: Proposed output budget for new child
            child_total_budget: Proposed total budget for new child

        Returns:
            List of BudgetValidationError for any violations
        """
        errors = []

        # Check each direction
        budget_map = {
            'input': child_input_budget,
            'output': child_output_budget,
            'total': child_total_budget,
        }

        for direction, proposed_budget in budget_map.items():
            if proposed_budget is None:
                continue

            if not self._requires_children_sum_valid(parent, direction):
                continue

            parent_budget = self._get_budget(parent, direction)
            if parent_budget is None:
                continue

            # Calculate existing children sum
            existing_sum = 0
            for child in parent.children_tickets:
                child_budget = self._get_budget(child, direction)
                if child_budget is not None:
                    existing_sum += child_budget

            # Check if adding proposed budget would exceed parent
            new_sum = existing_sum + proposed_budget
            if new_sum > parent_budget:
                errors.append(BudgetValidationError(
                    message=(
                        f"Creating child with {direction} budget {proposed_budget:,} would make "
                        f"children sum ({new_sum:,}) exceed parent budget ({parent_budget:,})"
                    ),
                    direction=direction,
                    parent_id=parent.id,
                    parent_budget=parent_budget,
                    children_sum=new_sum,
                ))

        return errors


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def validate_budget_hierarchy(
    ticket: "HierarchicalTicket",
    direction: str = 'total',
) -> Optional[BudgetValidationError]:
    """
    Convenience function to validate hierarchical budget constraint.

    Args:
        ticket: The parent ticket to validate
        direction: Token direction to check (default: 'total')

    Returns:
        BudgetValidationError if validation fails, None if passes
    """
    validator = BudgetValidator()
    return validator.validate_children_sum(ticket, direction)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BudgetValidator",
    "BudgetValidationError",
    "validate_budget_hierarchy",
]
