"""
Context Freshness Tracking for Context System V2.

This module provides freshness tracking for context artifacts to help
AI assistants understand when context data may be stale.

Task: 01KCMGXCCH84MG5BWK8MY8ZT83
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class FreshnessLevel(str, Enum):
    """Freshness level for context artifacts."""

    FRESH = "fresh"  # Modified recently
    STALE = "stale"  # Not modified in a while
    OUTDATED = "outdated"  # Significantly outdated
    UNKNOWN = "unknown"  # Can't determine


@dataclass
class FreshnessConfig:
    """Configuration for freshness thresholds."""

    fresh_hours: int = 24  # Fresh if modified within 24 hours
    stale_hours: int = 72  # Stale if modified within 72 hours
    # Outdated if older than stale_hours


@dataclass
class FreshnessInfo:
    """Freshness information for a context item."""

    level: FreshnessLevel
    last_modified: Optional[datetime]
    age_hours: Optional[float]
    message: str


class ContextPaths:
    """
    Path utilities for Context System V2.

    Provides centralized path resolution for context directories.
    Based on the directory structure specification.
    """

    def __init__(self, roadmap_dir: Optional[Path] = None):
        """
        Initialize context paths.

        Args:
            roadmap_dir: Path to .vibey/roadmap directory.
                         If None, uses current working directory.
        """
        if roadmap_dir is None:
            roadmap_dir = Path.cwd() / ".vibey" / "roadmap"
        self.roadmap_dir = Path(roadmap_dir)
        self.base = self.roadmap_dir / "context"

    # === PLANS ===

    def plans_dir(self, ticket_id: Optional[str] = None) -> Path:
        """
        Get plans directory path.

        Args:
            ticket_id: Optional ULID to get specific ticket's plan directory

        Returns:
            Path to plans/ or plans/{ticket_id}/
        """
        path = self.base / "plans"
        if ticket_id:
            self._validate_ulid(ticket_id)
            path = path / ticket_id
        return path

    def plan_yaml(self, ticket_id: str) -> Path:
        """
        Get path to plan.yaml for a ticket.

        Args:
            ticket_id: ULID of the ticket

        Returns:
            Path to plans/{ticket_id}/plan.yaml
        """
        return self.plans_dir(ticket_id) / "plan.yaml"

    def plan_exists(self, ticket_id: str) -> bool:
        """Check if plan context exists for ticket."""
        return self.plan_yaml(ticket_id).exists()

    # === RUNTIME ===

    def runtime_dir(self) -> Path:
        """Get runtime directory path."""
        return self.base / "runtime"

    def runtime_yaml(self, ticket_id: str) -> Path:
        """
        Get path to runtime context YAML for a ticket.

        Args:
            ticket_id: ULID of the ticket

        Returns:
            Path to runtime/{ticket_id}.yaml
        """
        self._validate_ulid(ticket_id)
        return self.runtime_dir() / f"{ticket_id}.yaml"

    def runtime_exists(self, ticket_id: str) -> bool:
        """Check if runtime context exists for ticket."""
        return self.runtime_yaml(ticket_id).exists()

    # === POST-MORTEMS ===

    def post_mortems_dir(self) -> Path:
        """Get post-mortems directory path."""
        return self.base / "post-mortems"

    def post_mortem_yaml(self, ticket_id: str) -> Path:
        """
        Get path to post-mortem YAML for a ticket.

        Args:
            ticket_id: ULID of the ticket

        Returns:
            Path to post-mortems/{ticket_id}.yaml
        """
        self._validate_ulid(ticket_id)
        return self.post_mortems_dir() / f"{ticket_id}.yaml"

    def post_mortem_exists(self, ticket_id: str) -> bool:
        """Check if post-mortem exists for ticket."""
        return self.post_mortem_yaml(ticket_id).exists()

    # === INITIALIZATION ===

    def ensure_directories(self) -> None:
        """Create context directory structure if it doesn't exist."""
        self.plans_dir().mkdir(parents=True, exist_ok=True)
        self.runtime_dir().mkdir(parents=True, exist_ok=True)
        self.post_mortems_dir().mkdir(parents=True, exist_ok=True)

    # === VALIDATION ===

    def _validate_ulid(self, ticket_id: str) -> None:
        """Validate that string is a valid ULID."""
        if not self._is_valid_ulid(ticket_id):
            raise ValueError(
                f"Invalid ticket ID: {ticket_id}. " "Expected 26-character ULID."
            )

    @staticmethod
    def _is_valid_ulid(value: str) -> bool:
        """Check if string appears to be a valid ULID."""
        if len(value) != 26:
            return False
        # ULIDs use Crockford's Base32 alphabet
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        return all(c.upper() in valid_chars for c in value)


def check_file_freshness(
    file_path: Path, config: Optional[FreshnessConfig] = None
) -> FreshnessInfo:
    """
    Check freshness of a file based on modification time.

    Args:
        file_path: Path to the file to check
        config: Optional freshness configuration (defaults to FreshnessConfig())

    Returns:
        FreshnessInfo with level, last_modified, age_hours, and message
    """
    config = config or FreshnessConfig()

    if not file_path.exists():
        return FreshnessInfo(
            level=FreshnessLevel.UNKNOWN,
            last_modified=None,
            age_hours=None,
            message=f"File does not exist: {file_path}",
        )

    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = now - mtime
    age_hours = age.total_seconds() / 3600

    if age_hours < config.fresh_hours:
        level = FreshnessLevel.FRESH
        message = f"Fresh (modified {age_hours:.1f} hours ago)"
    elif age_hours < config.stale_hours:
        level = FreshnessLevel.STALE
        message = f"Stale (modified {age_hours:.1f} hours ago)"
    else:
        level = FreshnessLevel.OUTDATED
        message = f"Outdated (modified {age_hours:.1f} hours ago)"

    return FreshnessInfo(
        level=level,
        last_modified=mtime,
        age_hours=age_hours,
        message=message,
    )


def check_context_freshness(
    ticket_id: str,
    roadmap_dir: Optional[Path] = None,
    config: Optional[FreshnessConfig] = None,
) -> Dict[str, FreshnessInfo]:
    """
    Check freshness of all context files for a ticket.

    Args:
        ticket_id: ULID of the ticket
        roadmap_dir: Optional path to .vibey/roadmap directory
        config: Optional freshness configuration

    Returns:
        Dict mapping context type ("plan", "runtime", "post_mortem") to FreshnessInfo
    """
    paths = ContextPaths(roadmap_dir)
    config = config or FreshnessConfig()
    results = {}

    # Check plan context
    plan_path = paths.plan_yaml(ticket_id)
    if plan_path.exists():
        results["plan"] = check_file_freshness(plan_path, config)

    # Check runtime context
    runtime_path = paths.runtime_yaml(ticket_id)
    if runtime_path.exists():
        results["runtime"] = check_file_freshness(runtime_path, config)

    # Check post-mortem
    pm_path = paths.post_mortem_yaml(ticket_id)
    if pm_path.exists():
        results["post_mortem"] = check_file_freshness(pm_path, config)

    return results


def get_overall_freshness(freshness_results: Dict[str, FreshnessInfo]) -> FreshnessLevel:
    """
    Get the overall freshness level from multiple context freshness results.

    Returns the "worst" freshness level found (OUTDATED > STALE > FRESH > UNKNOWN).

    Args:
        freshness_results: Dict from check_context_freshness()

    Returns:
        Overall FreshnessLevel
    """
    if not freshness_results:
        return FreshnessLevel.UNKNOWN

    # Priority: OUTDATED > STALE > FRESH > UNKNOWN
    priority = {
        FreshnessLevel.OUTDATED: 3,
        FreshnessLevel.STALE: 2,
        FreshnessLevel.FRESH: 1,
        FreshnessLevel.UNKNOWN: 0,
    }

    worst_level = FreshnessLevel.UNKNOWN
    worst_priority = 0

    for info in freshness_results.values():
        level_priority = priority.get(info.level, 0)
        if level_priority > worst_priority:
            worst_priority = level_priority
            worst_level = info.level

    return worst_level


def format_freshness_report(
    ticket_id: str, freshness_results: Dict[str, FreshnessInfo]
) -> str:
    """
    Format a human-readable freshness report.

    Args:
        ticket_id: ULID of the ticket
        freshness_results: Dict from check_context_freshness()

    Returns:
        Formatted string report
    """
    lines = [f"Context Freshness Report for {ticket_id}", "=" * 60]

    if not freshness_results:
        lines.append("No context files found for this ticket.")
        return "\n".join(lines)

    overall = get_overall_freshness(freshness_results)
    lines.append(f"Overall Status: {overall.value.upper()}")
    lines.append("-" * 60)

    for context_type, info in freshness_results.items():
        display_name = context_type.replace("_", " ").title()
        status_icon = _get_status_icon(info.level)
        lines.append(f"{status_icon} {display_name}: {info.message}")
        if info.last_modified:
            lines.append(f"   Last modified: {info.last_modified.isoformat()}")

    return "\n".join(lines)


def _get_status_icon(level: FreshnessLevel) -> str:
    """Get a status icon for a freshness level."""
    icons = {
        FreshnessLevel.FRESH: "[OK]",
        FreshnessLevel.STALE: "[!]",
        FreshnessLevel.OUTDATED: "[!!]",
        FreshnessLevel.UNKNOWN: "[?]",
    }
    return icons.get(level, "[?]")


__all__ = [
    # Enums
    "FreshnessLevel",
    # Config
    "FreshnessConfig",
    # Data classes
    "FreshnessInfo",
    # Path utilities
    "ContextPaths",
    # Functions
    "check_file_freshness",
    "check_context_freshness",
    "get_overall_freshness",
    "format_freshness_report",
]
