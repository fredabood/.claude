"""
IntentionalRegressionHandler - Manage acknowledged regressions for deprecation/sunset.

This module provides a handler for intentional regressions that occur during
deprecation, sunset, or other planned changes. It allows teams to acknowledge
that certain quality criteria regressions are expected and intentional.

Key Features:
- Track acknowledged regressions with justification
- Support multiple regression reasons (deprecation, sunset, breaking change, etc.)
- Time-bounded acknowledgments with expiration
- Interactive prompting for acknowledgment collection
- YAML persistence for acknowledgment records

Storage: .vibey/implementation/acknowledgments.yaml

Usage:
    from vibey.services.implementation.acknowledgment import (
        IntentionalRegressionHandler,
        RegressionReason,
        RegressionAcknowledgment,
    )
    from pathlib import Path

    # Initialize handler
    handler = IntentionalRegressionHandler(
        storage_path=Path(".vibey/implementation/acknowledgments.yaml")
    )

    # Acknowledge a regression
    ack = handler.acknowledge_regression(
        criterion_ref="test/unit/auth_test.py::test_legacy_login",
        reason=RegressionReason.DEPRECATION,
        justification="Legacy login deprecated in v3.0, will be removed in v4.0",
        acknowledged_by="developer@example.com",
        related_ticket="PROJ-1234",
    )

    # Check if a criterion has an active acknowledgment
    if handler.is_acknowledged("test/unit/auth_test.py::test_legacy_login"):
        # Skip regression warning
        pass

    # Cleanup expired acknowledgments
    handler.cleanup_expired()

Design Reference:
- Implementation Mode Track Sprint 2
- Task: Implement IntentionalRegressionHandler for deprecation/sunset
"""

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from ulid import ULID


logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_ACKNOWLEDGMENT_EXPIRY_DAYS = 90
"""Default number of days before an acknowledgment expires."""

DEFAULT_STORAGE_PATH = Path(".vibey/implementation/acknowledgments.yaml")
"""Default path for acknowledgment storage."""


# =============================================================================
# ENUMS
# =============================================================================


class RegressionReason(str, Enum):
    """
    Reasons for intentional regressions.

    Values:
        DEPRECATION: Feature is being deprecated, temporary regression expected
        SUNSET: Feature is being permanently removed, regression is final
        BREAKING_CHANGE: Intentional breaking change requiring migration
        REFACTOR: Temporary regression during refactoring
        TEST_FLAKE: Test is flaky and being acknowledged temporarily
        EXTERNAL_DEP: Regression due to external dependency change
    """

    DEPRECATION = "deprecation"
    SUNSET = "sunset"
    BREAKING_CHANGE = "breaking_change"
    REFACTOR = "refactor"
    TEST_FLAKE = "test_flake"
    EXTERNAL_DEP = "external_dep"


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class RegressionAcknowledgment:
    """
    Record of an acknowledged intentional regression.

    Represents a documented acknowledgment that a particular regression is
    intentional and should not trigger quality gate failures.

    Attributes:
        regression_id: Unique identifier for this acknowledgment (ULID)
        criterion_ref: Reference to the regressed criterion (file path, test name, etc.)
        acknowledged_by: Who acknowledged the regression (email or username)
        acknowledged_at: When the acknowledgment was recorded
        reason: Why the regression is intentional
        justification: Detailed explanation of why this regression is acceptable
        related_ticket: Optional issue/ticket reference (e.g., "PROJ-1234")
        expires_at: When this acknowledgment expires (None for no expiry)

    Example:
        >>> ack = RegressionAcknowledgment(
        ...     criterion_ref="test/unit/legacy_test.py::test_old_feature",
        ...     acknowledged_by="developer@example.com",
        ...     reason=RegressionReason.DEPRECATION,
        ...     justification="Old feature deprecated in v2.0",
        ...     related_ticket="PROJ-456",
        ... )
    """

    regression_id: str = field(default_factory=lambda: str(ULID()))
    criterion_ref: str = ""
    acknowledged_by: str = ""
    acknowledged_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: RegressionReason = RegressionReason.DEPRECATION
    justification: str = ""
    related_ticket: Optional[str] = None
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Check if this acknowledgment has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if this acknowledgment is still active (not expired)."""
        return not self.is_expired

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get the number of days until this acknowledgment expires."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "regression_id": self.regression_id,
            "criterion_ref": self.criterion_ref,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat(),
            "reason": self.reason.value,
            "justification": self.justification,
            "related_ticket": self.related_ticket,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionAcknowledgment":
        """Create from dictionary (YAML deserialization)."""
        # Parse acknowledged_at
        acknowledged_at = data.get("acknowledged_at")
        if isinstance(acknowledged_at, str):
            acknowledged_at = datetime.fromisoformat(acknowledged_at.replace("Z", "+00:00"))
        elif acknowledged_at is None:
            acknowledged_at = datetime.now(timezone.utc)

        # Parse expires_at
        expires_at = data.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

        # Parse reason
        reason_str = data.get("reason", "deprecation")
        try:
            reason = RegressionReason(reason_str)
        except ValueError:
            reason = RegressionReason.DEPRECATION
            logger.warning(f"Unknown regression reason '{reason_str}', defaulting to DEPRECATION")

        return cls(
            regression_id=data.get("regression_id", str(ULID())),
            criterion_ref=data.get("criterion_ref", ""),
            acknowledged_by=data.get("acknowledged_by", ""),
            acknowledged_at=acknowledged_at,
            reason=reason,
            justification=data.get("justification", ""),
            related_ticket=data.get("related_ticket"),
            expires_at=expires_at,
        )


# =============================================================================
# INTENTIONAL REGRESSION HANDLER
# =============================================================================


class IntentionalRegressionHandler:
    """
    Manages acknowledged intentional regressions.

    Provides methods to acknowledge, track, and query intentional regressions
    that should not trigger quality gate failures. Acknowledgments are persisted
    to YAML for durability across sessions.

    Attributes:
        storage_path: Path to the YAML storage file
        acknowledgments: In-memory cache of acknowledgments
        default_expiry_days: Default days until acknowledgment expiry

    Example:
        >>> handler = IntentionalRegressionHandler()
        >>> handler.acknowledge_regression(
        ...     criterion_ref="tests/test_legacy.py::test_old_api",
        ...     reason=RegressionReason.SUNSET,
        ...     justification="API removed in v3.0",
        ...     acknowledged_by="developer@example.com",
        ... )
        >>> handler.is_acknowledged("tests/test_legacy.py::test_old_api")
        True
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        default_expiry_days: int = DEFAULT_ACKNOWLEDGMENT_EXPIRY_DAYS,
        console: Optional[Console] = None,
    ):
        """
        Initialize the handler.

        Args:
            storage_path: Path to YAML storage file (defaults to .vibey/implementation/acknowledgments.yaml)
            default_expiry_days: Default days until acknowledgment expires (default 90)
            console: Optional Rich Console for interactive prompts
        """
        self.storage_path = storage_path or DEFAULT_STORAGE_PATH
        self.default_expiry_days = default_expiry_days
        self.console = console or Console()
        self.acknowledgments: Dict[str, RegressionAcknowledgment] = {}

        # Load existing acknowledgments
        self._load()

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _load(self) -> None:
        """Load acknowledgments from storage file."""
        if not self.storage_path.exists():
            logger.debug(f"No acknowledgments file at {self.storage_path}")
            return

        try:
            with open(self.storage_path, "r") as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            acknowledgments_data = data.get("acknowledgments", [])
            for ack_data in acknowledgments_data:
                ack = RegressionAcknowledgment.from_dict(ack_data)
                self.acknowledgments[ack.criterion_ref] = ack

            logger.debug(f"Loaded {len(self.acknowledgments)} acknowledgments from {self.storage_path}")

        except yaml.YAMLError as e:
            logger.error(f"Failed to load acknowledgments: {e}")
        except Exception as e:
            logger.error(f"Error loading acknowledgments: {e}")

    def _save(self) -> None:
        """Persist acknowledgments to storage file."""
        try:
            # Ensure parent directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Build data structure
            data = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "acknowledgments": [
                    ack.to_dict() for ack in self.acknowledgments.values()
                ],
            }

            with open(self.storage_path, "w") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

            logger.debug(f"Saved {len(self.acknowledgments)} acknowledgments to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save acknowledgments: {e}")
            raise

    # =========================================================================
    # ACKNOWLEDGMENT OPERATIONS
    # =========================================================================

    def acknowledge_regression(
        self,
        criterion_ref: str,
        reason: RegressionReason,
        justification: str,
        acknowledged_by: str,
        related_ticket: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        expiry_days: Optional[int] = None,
    ) -> RegressionAcknowledgment:
        """
        Record acknowledgment for an intentional regression.

        Creates a new acknowledgment record for a criterion that is expected
        to regress intentionally. If an acknowledgment already exists for
        this criterion, it will be replaced.

        Args:
            criterion_ref: Reference to the regressed criterion (file path, test name, etc.)
            reason: Why the regression is intentional
            justification: Detailed explanation
            acknowledged_by: Who is acknowledging (email or username)
            related_ticket: Optional issue/ticket reference
            expires_at: When the acknowledgment expires (overrides expiry_days)
            expiry_days: Days until expiry (defaults to default_expiry_days)

        Returns:
            The created RegressionAcknowledgment

        Example:
            >>> ack = handler.acknowledge_regression(
            ...     criterion_ref="test/auth_test.py::test_legacy",
            ...     reason=RegressionReason.DEPRECATION,
            ...     justification="Legacy auth deprecated",
            ...     acknowledged_by="dev@example.com",
            ... )
        """
        # Calculate expiry time
        if expires_at is None:
            days = expiry_days if expiry_days is not None else self.default_expiry_days
            if days > 0:
                expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        # Create acknowledgment
        ack = RegressionAcknowledgment(
            criterion_ref=criterion_ref,
            acknowledged_by=acknowledged_by,
            reason=reason,
            justification=justification,
            related_ticket=related_ticket,
            expires_at=expires_at,
        )

        # Store and persist
        self.acknowledgments[criterion_ref] = ack
        self._save()

        logger.info(
            f"Acknowledged regression for '{criterion_ref}' "
            f"(reason={reason.value}, expires={expires_at})"
        )

        return ack

    def is_acknowledged(self, criterion_ref: str) -> bool:
        """
        Check if a criterion has an active acknowledgment.

        Args:
            criterion_ref: Reference to check

        Returns:
            True if there is an active (non-expired) acknowledgment
        """
        ack = self.acknowledgments.get(criterion_ref)
        if ack is None:
            return False
        return ack.is_active

    def get_acknowledgment(self, criterion_ref: str) -> Optional[RegressionAcknowledgment]:
        """
        Get acknowledgment details for a criterion.

        Args:
            criterion_ref: Reference to look up

        Returns:
            RegressionAcknowledgment if found, None otherwise
        """
        return self.acknowledgments.get(criterion_ref)

    def list_active_acknowledgments(self) -> List[RegressionAcknowledgment]:
        """
        List all active (non-expired) acknowledgments.

        Returns:
            List of active RegressionAcknowledgment instances
        """
        return [
            ack for ack in self.acknowledgments.values()
            if ack.is_active
        ]

    def list_expired_acknowledgments(self) -> List[RegressionAcknowledgment]:
        """
        List all expired acknowledgments.

        Returns:
            List of expired RegressionAcknowledgment instances
        """
        return [
            ack for ack in self.acknowledgments.values()
            if ack.is_expired
        ]

    def list_by_reason(self, reason: RegressionReason) -> List[RegressionAcknowledgment]:
        """
        List acknowledgments filtered by reason.

        Args:
            reason: The reason to filter by

        Returns:
            List of matching RegressionAcknowledgment instances
        """
        return [
            ack for ack in self.acknowledgments.values()
            if ack.reason == reason and ack.is_active
        ]

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def cleanup_expired(self) -> int:
        """
        Remove expired acknowledgments.

        Removes all acknowledgments that have passed their expiration date.
        Changes are persisted to storage.

        Returns:
            Number of acknowledgments removed
        """
        expired = [
            ref for ref, ack in self.acknowledgments.items()
            if ack.is_expired
        ]

        for ref in expired:
            del self.acknowledgments[ref]
            logger.debug(f"Removed expired acknowledgment: {ref}")

        if expired:
            self._save()
            logger.info(f"Cleaned up {len(expired)} expired acknowledgments")

        return len(expired)

    def remove_acknowledgment(self, criterion_ref: str) -> bool:
        """
        Remove a specific acknowledgment.

        Args:
            criterion_ref: Reference to remove

        Returns:
            True if an acknowledgment was removed, False if not found
        """
        if criterion_ref in self.acknowledgments:
            del self.acknowledgments[criterion_ref]
            self._save()
            logger.info(f"Removed acknowledgment for '{criterion_ref}'")
            return True
        return False

    # =========================================================================
    # INTERACTIVE PROMPTING
    # =========================================================================

    def prompt_for_acknowledgment(
        self,
        criterion_ref: str,
        context: Optional[str] = None,
    ) -> Optional[RegressionAcknowledgment]:
        """
        Interactive prompt to acknowledge a regression.

        Displays information about the regression and prompts the user
        for acknowledgment details.

        Args:
            criterion_ref: Reference to the criterion with regression
            context: Optional context about the regression

        Returns:
            RegressionAcknowledgment if user acknowledges, None if skipped
        """
        # Display prompt panel
        self._display_prompt(criterion_ref, context)

        # Ask if user wants to acknowledge
        should_acknowledge = self._prompt_yes_no("Acknowledge this regression?")
        if not should_acknowledge:
            self.console.print("[yellow]Skipped acknowledgment[/yellow]")
            return None

        # Collect acknowledgment details
        reason = self._prompt_reason()
        justification = self._prompt_text("Justification", required=True)
        acknowledged_by = self._prompt_text("Your email/username", required=True)
        related_ticket = self._prompt_text("Related ticket (optional)", required=False)
        expiry_days = self._prompt_expiry()

        # Create acknowledgment
        ack = self.acknowledge_regression(
            criterion_ref=criterion_ref,
            reason=reason,
            justification=justification,
            acknowledged_by=acknowledged_by,
            related_ticket=related_ticket if related_ticket else None,
            expiry_days=expiry_days,
        )

        self.console.print(f"[green]Acknowledged regression for '{criterion_ref}'[/green]")
        return ack

    async def prompt_for_acknowledgment_async(
        self,
        criterion_ref: str,
        context: Optional[str] = None,
        timeout: int = 300,
    ) -> Optional[RegressionAcknowledgment]:
        """
        Async interactive prompt to acknowledge a regression.

        Same as prompt_for_acknowledgment but with async timeout support.

        Args:
            criterion_ref: Reference to the criterion with regression
            context: Optional context about the regression
            timeout: Timeout in seconds (default 300)

        Returns:
            RegressionAcknowledgment if user acknowledges, None if skipped/timeout
        """
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.prompt_for_acknowledgment(criterion_ref, context)
                ),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError:
            self.console.print(f"\n[yellow]Acknowledgment prompt timed out after {timeout}s[/yellow]")
            return None

    def _display_prompt(self, criterion_ref: str, context: Optional[str]) -> None:
        """Display the acknowledgment prompt panel."""
        lines = []
        lines.append(f"[bold]Criterion:[/bold] {criterion_ref}")

        if context:
            lines.append("")
            lines.append(f"[dim]{context}[/dim]")

        lines.append("")
        lines.append("[yellow]This criterion has regressed. Would you like to acknowledge[/yellow]")
        lines.append("[yellow]this as an intentional regression?[/yellow]")

        content = "\n".join(lines)

        panel = Panel(
            content,
            title="[bold yellow]Regression Detected[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def _prompt_yes_no(self, message: str) -> bool:
        """Prompt for yes/no response."""
        response = Prompt.ask(
            f"{message} [y/n]",
            console=self.console,
            default="n",
        ).lower()
        return response in ("y", "yes")

    def _prompt_text(self, label: str, required: bool = True) -> str:
        """Prompt for text input."""
        while True:
            response = Prompt.ask(
                label,
                console=self.console,
                default="" if not required else None,
            )
            if response or not required:
                return response
            self.console.print("[red]This field is required[/red]")

    def _prompt_reason(self) -> RegressionReason:
        """Prompt for regression reason selection."""
        self.console.print("\n[bold]Select regression reason:[/bold]")
        for i, reason in enumerate(RegressionReason, 1):
            self.console.print(f"  {i}. {reason.value}")

        while True:
            choice = Prompt.ask(
                "Enter number",
                console=self.console,
                default="1",
            )
            try:
                idx = int(choice) - 1
                reasons = list(RegressionReason)
                if 0 <= idx < len(reasons):
                    return reasons[idx]
            except ValueError:
                pass
            self.console.print(f"[red]Invalid choice. Enter 1-{len(RegressionReason)}[/red]")

    def _prompt_expiry(self) -> int:
        """Prompt for expiry days."""
        self.console.print(f"\n[dim]Default expiry: {self.default_expiry_days} days[/dim]")
        response = Prompt.ask(
            "Days until expiry (0 for no expiry)",
            console=self.console,
            default=str(self.default_expiry_days),
        )
        try:
            return max(0, int(response))
        except ValueError:
            return self.default_expiry_days

    # =========================================================================
    # SUMMARY
    # =========================================================================

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of acknowledgment status.

        Returns:
            Dictionary with acknowledgment statistics
        """
        active = self.list_active_acknowledgments()
        expired = self.list_expired_acknowledgments()

        # Count by reason
        by_reason: Dict[str, int] = {}
        for ack in active:
            reason_val = ack.reason.value
            by_reason[reason_val] = by_reason.get(reason_val, 0) + 1

        # Find expiring soon (within 7 days)
        expiring_soon = [
            ack for ack in active
            if ack.days_until_expiry is not None and ack.days_until_expiry <= 7
        ]

        return {
            "total_active": len(active),
            "total_expired": len(expired),
            "expiring_soon": len(expiring_soon),
            "by_reason": by_reason,
            "storage_path": str(self.storage_path),
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enum
    "RegressionReason",
    # Data model
    "RegressionAcknowledgment",
    # Handler
    "IntentionalRegressionHandler",
    # Constants
    "DEFAULT_ACKNOWLEDGMENT_EXPIRY_DAYS",
    "DEFAULT_STORAGE_PATH",
]
