"""
PM Adapter Types - Supporting types for the PM adapter system.

This module provides the supporting types used by PM tool adapters including:
- SyncDirection: Direction of synchronization operations
- SyncResult: Result of sync operations
- SyncConflict: Details of sync conflicts
- ConflictResolution: How to resolve sync conflicts
- PMCapabilities: Capability declarations for adapters

Reference: UNIFIED_ADAPTER_ARCHITECTURE.md Part 3.2
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from vibey.core.ticket import HierarchyType


class SyncDirection(str, Enum):
    """Direction of synchronization operations."""

    IMPORT = "import"
    """Import data from external system into Vibey."""

    EXPORT = "export"
    """Export data from Vibey to external system."""

    BIDIRECTIONAL = "bidirectional"
    """Two-way sync, merging changes from both systems."""


class ConflictResolution(str, Enum):
    """How to resolve conflicts during sync."""

    LOCAL_WINS = "local_wins"
    """Local (Vibey) version takes precedence."""

    REMOTE_WINS = "remote_wins"
    """Remote (external) version takes precedence."""

    MANUAL = "manual"
    """Require manual resolution by user."""

    MERGE = "merge"
    """Attempt automatic merge of changes."""


class SyncConflict(BaseModel):
    """Details of a sync conflict between local and remote state."""

    ticket_id: str
    """ID of the ticket with conflict."""

    field_name: str
    """Name of the conflicting field."""

    local_value: Any
    """Current local (Vibey) value."""

    remote_value: Any
    """Current remote (external) value."""

    local_modified_at: Optional[datetime] = None
    """When local value was last modified."""

    remote_modified_at: Optional[datetime] = None
    """When remote value was last modified."""

    resolution: Optional[ConflictResolution] = None
    """How this conflict was/should be resolved."""

    resolved_value: Any = None
    """The final resolved value (if resolved)."""


class SyncResult(BaseModel):
    """Result of a sync operation."""

    success: bool
    """Whether the sync completed successfully."""

    direction: SyncDirection
    """Direction of the sync operation."""

    items_imported: int = 0
    """Number of items imported from external system."""

    items_exported: int = 0
    """Number of items exported to external system."""

    items_updated: int = 0
    """Number of items updated (in bidirectional sync)."""

    items_skipped: int = 0
    """Number of items skipped due to errors or conflicts."""

    conflicts: List[SyncConflict] = Field(default_factory=list)
    """List of conflicts encountered during sync."""

    errors: List[str] = Field(default_factory=list)
    """Error messages from failed operations."""

    warnings: List[str] = Field(default_factory=list)
    """Warning messages from non-fatal issues."""

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """When the sync operation started."""

    completed_at: Optional[datetime] = None
    """When the sync operation completed."""

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate sync duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def total_items(self) -> int:
        """Total items processed."""
        return self.items_imported + self.items_exported + self.items_updated

    def complete(self, success: bool = True) -> "SyncResult":
        """Mark the sync as complete and return self for chaining."""
        self.completed_at = datetime.now(timezone.utc)
        self.success = success
        return self


@dataclass
class PMCapabilities:
    """
    Capability declarations for a PM adapter.

    This allows adapters to declare what features they support,
    enabling the CLI/MCP to adapt behavior accordingly.
    """

    # Hierarchy support
    supported_hierarchy_types: List[HierarchyType] = field(
        default_factory=lambda: list(HierarchyType)
    )
    """Which hierarchy types this adapter supports."""

    # Feature flags
    supports_sprints: bool = True
    """Whether adapter supports sprint/iteration concept."""

    supports_bidirectional_sync: bool = False
    """Whether adapter supports two-way sync with external system."""

    supports_webhooks: bool = False
    """Whether adapter supports real-time webhooks for updates."""

    supports_attachments: bool = False
    """Whether adapter supports file attachments on tickets."""

    supports_comments: bool = False
    """Whether adapter supports comments/discussion on tickets."""

    supports_time_tracking: bool = False
    """Whether adapter supports time tracking features."""

    supports_custom_fields: bool = False
    """Whether adapter supports user-defined custom fields."""

    supports_bulk_operations: bool = False
    """Whether adapter supports bulk create/update/delete."""

    # Limits
    max_description_length: Optional[int] = None
    """Maximum length of ticket descriptions (None = unlimited)."""

    max_title_length: Optional[int] = None
    """Maximum length of ticket titles (None = unlimited)."""

    max_labels: Optional[int] = None
    """Maximum number of labels per ticket (None = unlimited)."""

    max_children: Optional[int] = None
    """Maximum number of children per container (None = unlimited)."""

    # Rate limiting
    rate_limit_requests_per_minute: Optional[int] = None
    """API rate limit in requests per minute (None = unlimited)."""

    rate_limit_requests_per_hour: Optional[int] = None
    """API rate limit in requests per hour (None = unlimited)."""


@dataclass
class AdapterInfo:
    """
    Information about a registered PM adapter.

    Used by the registry to track available adapters.
    """

    name: str
    """Unique adapter identifier (e.g., 'vibey', 'jira')."""

    display_name: str
    """Human-readable name for UI display."""

    description: str = ""
    """Description of the adapter and what it connects to."""

    version: str = "1.0.0"
    """Adapter version."""

    capabilities: PMCapabilities = field(default_factory=PMCapabilities)
    """Adapter capabilities."""

    is_available: bool = True
    """Whether the adapter is currently available/configured."""

    error_message: Optional[str] = None
    """Error message if adapter is not available."""
