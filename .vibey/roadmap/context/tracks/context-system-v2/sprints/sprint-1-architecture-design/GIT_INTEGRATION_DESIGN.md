# Git Integration Design with Pre-Commit Hook

**Task ID:** 01KCMMJK5AQ727JVKPCED8RXVT
**Sprint:** Sprint 1 - Context Architecture Design
**Track:** Context System V2
**Date:** 2025-12-19
**Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Integration with Unified Ticket Architecture](#integration-with-unified-ticket-architecture)
3. [Data Models](#data-models)
4. [Pre-Commit Hook Flow](#pre-commit-hook-flow)
5. [Resolution Options](#resolution-options)
6. [Configuration Schema](#configuration-schema)
7. [Commit Message Template](#commit-message-template)
8. [Implementation Notes](#implementation-notes)

---

## Overview

This document specifies the git integration design for the Context System V2, focusing on the pre-commit hook with triangle validation. The design validates consistency between:

- **Commit message** - Task references via `Task:` and `Completes:` markers
- **Staged files** - Artifacts being committed
- **Ticket associations** - Artifacts already associated with referenced tickets

### Design Principles (from Sprint 0)

| Principle | Description |
|-----------|-------------|
| No timestamp-based linking | Timestamp was source of parallel task ambiguity |
| Three link signals | File overlap, message reference, manual |
| Bidirectional validation | Neither YAML nor message assumed correct |
| Multi-task file ownership | Files can belong to multiple tasks |
| Configurable enforcement | Different tolerance for friction |

---

## Integration with Unified Ticket Architecture

**Critical:** This design integrates with the existing Unified Ticket Architecture rather than creating standalone entities.

### Entity Mapping

| Context System Concept | Unified Ticket Entity |
|-----------------------|----------------------|
| `CommitLink` | `TicketCommitLink` relationship entity |
| `KnownFile` | `TicketArtifactAssociation` relationship entity |
| File tracking | `Artifact` entity with provenance |
| Commit data | `GitCommit` entity |
| Completion criteria | `Completable`/`Criterion` system |

Reference: `docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md`

### Triangle Model

The pre-commit hook validates across all three relationship edges:

```
                         +-------------+
                         |   Ticket    |
                         +-------------+
                        /               \
                       /                 \
          TicketCommitLink          TicketArtifactAssociation
                     /                     \
                    /                       \
        +-------------+               +-------------+
        |  GitCommit  |---------------|  Artifact   |
        +-------------+               +-------------+
                    CommitArtifactChange
```

---

## Data Models

### Core Relationship Entities

These models integrate with the Unified Ticket Architecture:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ReferenceType(str, Enum):
    """Type of ticket reference in commit message."""
    TASK_REFERENCE = "task_reference"       # Task: marker
    COMPLETION_CLAIM = "completion_claim"   # Completes: marker


class ChangeType(str, Enum):
    """Type of change to an artifact."""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class AssociationSource(str, Enum):
    """How an artifact became associated with a ticket."""
    PLAN_REFERENCE = "plan_reference"       # Pre-work planning
    RUNTIME_TRACKING = "runtime_tracking"   # AI logs during work
    COMMIT_BOOTSTRAP = "commit_bootstrap"   # First commit establishes
    MANUAL = "manual"                       # CLI command
    CRITERION_TARGET = "criterion_target"   # FileExistsTarget reference


class LinkSource(str, Enum):
    """Where a commit-ticket link originated."""
    PRE_COMMIT_HOOK = "pre_commit_hook"
    POST_COMMIT = "post_commit"
    MANUAL = "manual"
    RECONCILIATION = "reconciliation"
```

### Link Signal Models

```python
@dataclass
class FileOverlapSignal:
    """Signal: Commit artifacts match ticket's artifact associations."""

    matched: bool
    overlapping_artifact_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def calculate_confidence(self, commit_artifact_count: int) -> float:
        """Confidence = overlap_count / commit_artifact_count."""
        if commit_artifact_count == 0:
            return 0.0
        self.confidence = len(self.overlapping_artifact_ids) / commit_artifact_count
        self.matched = self.confidence > 0
        return self.confidence


@dataclass
class MessageRefSignal:
    """Signal: Ticket ID found in commit message."""

    matched: bool
    ticket_ids: List[str] = field(default_factory=list)
    reference_type: ReferenceType = ReferenceType.TASK_REFERENCE
    confidence: float = 1.0  # Always 1.0 when matched


@dataclass
class ManualSignal:
    """Signal: User explicitly linked commit to ticket."""

    matched: bool
    linked_by: Optional[str] = None
    linked_at: Optional[datetime] = None
    confidence: float = 1.0  # Always 1.0 when manually linked


@dataclass
class LinkSignals:
    """Combined signals for commit-ticket relationship."""

    file_overlap: Optional[FileOverlapSignal] = None
    message_ref: Optional[MessageRefSignal] = None
    manual: Optional[ManualSignal] = None

    def calculate_aggregate_confidence(self) -> float:
        """
        Calculate aggregate confidence from all signals.

        Strategy: Use highest confidence among signals.
        Message ref and manual are always 1.0 when matched.
        File overlap varies based on overlap ratio.
        """
        confidences = []

        if self.file_overlap and self.file_overlap.matched:
            confidences.append(self.file_overlap.confidence)
        if self.message_ref and self.message_ref.matched:
            confidences.append(self.message_ref.confidence)
        if self.manual and self.manual.matched:
            confidences.append(self.manual.confidence)

        return max(confidences) if confidences else 0.0
```

### Relationship Entities

```python
@dataclass
class TicketCommitLink:
    """Relationship: Ticket <-> GitCommit."""

    ticket_id: str
    commit_sha: str
    reference_type: ReferenceType
    signals: LinkSignals
    aggregate_confidence: float
    linked_at: datetime
    link_source: LinkSource

    @classmethod
    def from_pre_commit(
        cls,
        ticket_id: str,
        commit_sha: str,
        reference_type: ReferenceType,
        signals: LinkSignals
    ) -> "TicketCommitLink":
        """Create link from pre-commit hook."""
        return cls(
            ticket_id=ticket_id,
            commit_sha=commit_sha,
            reference_type=reference_type,
            signals=signals,
            aggregate_confidence=signals.calculate_aggregate_confidence(),
            linked_at=datetime.now(),
            link_source=LinkSource.PRE_COMMIT_HOOK
        )


@dataclass
class TicketArtifactAssociation:
    """Relationship: Ticket <-> Artifact."""

    ticket_id: str
    artifact_id: str
    association_source: AssociationSource
    added_at: datetime
    added_by: Optional[str] = None

    @classmethod
    def from_commit_bootstrap(
        cls,
        ticket_id: str,
        artifact_id: str
    ) -> "TicketArtifactAssociation":
        """Create association when commit first links artifact to ticket."""
        return cls(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            association_source=AssociationSource.COMMIT_BOOTSTRAP,
            added_at=datetime.now(),
            added_by="pre_commit_hook"
        )


@dataclass
class CommitArtifactChange:
    """Relationship: GitCommit <-> Artifact."""

    commit_sha: str
    artifact_id: str
    change_type: ChangeType
    previous_path: Optional[str] = None  # For renames
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    recorded_at: datetime = field(default_factory=datetime.now)
```

### GitCommit Extension

```python
@dataclass
class GitCommit:
    """Git commit with parsed ticket references."""

    sha: str
    message: str
    date: datetime
    author: str
    platform: str

    # Parsed from "Completes:" lines
    completes_tickets: List[str] = field(default_factory=list)

    # Parsed from "Task:" lines (new)
    references_tickets: List[str] = field(default_factory=list)

    @classmethod
    def from_git(cls, sha: str, message: str, author: str, date: datetime) -> "GitCommit":
        """Parse commit from git data."""
        completes = cls._parse_markers(message, "Completes:")
        references = cls._parse_markers(message, "Task:")

        return cls(
            sha=sha,
            message=message,
            date=date,
            author=author,
            platform="local",  # Or detected from commit
            completes_tickets=completes,
            references_tickets=references
        )

    @staticmethod
    def _parse_markers(message: str, marker: str) -> List[str]:
        """Parse ticket IDs from marker lines."""
        import re

        ticket_ids = []
        pattern = rf"^{re.escape(marker)}\s*(.+)$"

        for line in message.split("\n"):
            match = re.match(pattern, line.strip(), re.IGNORECASE)
            if match:
                # Handle comma-separated IDs
                ids = [id.strip() for id in match.group(1).split(",")]
                ticket_ids.extend(ids)

        return ticket_ids
```

---

## Pre-Commit Hook Flow

The pre-commit hook executes in four phases:

```
+-------------------------------------------------------------------------+
|                      UNIFIED PRE-COMMIT HOOK                             |
+-------------------------------------------------------------------------+
|  PHASE 1: Collect Data                                                   |
|    - Parse commit message -> Task: and Completes: references             |
|    - Get staged files -> resolve to Artifact IDs (or create new)         |
|    - Build pending CommitArtifactChange records                          |
+-------------------------------------------------------------------------+
|  PHASE 2: Triangle Validation                                            |
|    For each Task: ticket_id:                                             |
|      A = Artifacts in staged files (CommitArtifactChange)                |
|      B = Artifacts associated with ticket (TicketArtifactAssociation)    |
|                                                                          |
|      Check 1: A intersection B - Files in both (expected, good)          |
|      Check 2: A - B - Staged NOT in ticket associations                  |
|               -> Prompt: "Add to ticket associations?"                   |
|      Check 3: B - A - Ticket associations NOT in staged                  |
|               -> Info only (not all files change each time)              |
+-------------------------------------------------------------------------+
|  PHASE 3: Completion Verification                                        |
|    For each Completes: ticket_id:                                        |
|      - ticket.can_transition_to(COMPLETED) must return True              |
|      - Block commit if criteria not met                                  |
+-------------------------------------------------------------------------+
|  PHASE 4: Persist Relationships                                          |
|    - Create TicketCommitLink for each Task:/Completes: reference         |
|    - Create CommitArtifactChange for each staged file                    |
|    - Update TicketArtifactAssociation if user approved additions         |
+-------------------------------------------------------------------------+
```

### Phase 1: Collect Data

```python
@dataclass
class PreCommitContext:
    """Context collected in Phase 1."""

    commit_sha: str
    commit_message: str
    staged_files: List[str]

    # Parsed references
    task_refs: List[str]           # From "Task:" lines
    completion_claims: List[str]   # From "Completes:" lines

    # Resolved to artifacts
    staged_artifacts: Dict[str, str]  # path -> artifact_id
    pending_changes: List[CommitArtifactChange]


def phase_1_collect_data() -> PreCommitContext:
    """
    Phase 1: Collect all data needed for validation.

    This phase is purely data gathering - no validation or prompts.
    """
    # Get staged files
    staged_files = get_staged_files()  # git diff --cached --name-only

    # Get commit message
    commit_message = get_commit_message()  # From COMMIT_EDITMSG or stdin

    # Get commit SHA (will be empty for pre-commit, populated post-commit)
    commit_sha = get_current_sha()  # git rev-parse HEAD

    # Parse task references from message
    task_refs = parse_markers(commit_message, "Task:")
    completion_claims = parse_markers(commit_message, "Completes:")

    # Resolve staged files to artifacts
    staged_artifacts = {}
    pending_changes = []

    for file_path in staged_files:
        artifact_id = resolve_or_create_artifact(file_path)
        change_type = detect_change_type(file_path)

        staged_artifacts[file_path] = artifact_id
        pending_changes.append(CommitArtifactChange(
            commit_sha=commit_sha,
            artifact_id=artifact_id,
            change_type=change_type,
            lines_added=count_lines_added(file_path),
            lines_removed=count_lines_removed(file_path)
        ))

    return PreCommitContext(
        commit_sha=commit_sha,
        commit_message=commit_message,
        staged_files=staged_files,
        task_refs=task_refs,
        completion_claims=completion_claims,
        staged_artifacts=staged_artifacts,
        pending_changes=pending_changes
    )
```

### Phase 2: Triangle Validation

```python
@dataclass
class TriangleValidationResult:
    """Result of triangle validation for one ticket."""

    ticket_id: str

    # Set operations
    overlap: Set[str]          # A intersection B - artifacts in both
    staged_only: Set[str]      # A - B - in commit but not ticket
    ticket_only: Set[str]      # B - A - in ticket but not commit

    # Validation status
    is_valid: bool
    requires_resolution: bool
    suggested_action: Optional[str] = None


def phase_2_triangle_validation(
    context: PreCommitContext,
    config: PreCommitConfig
) -> List[TriangleValidationResult]:
    """
    Phase 2: Validate triangle consistency for each referenced ticket.

    For each Task: reference, compare:
    - A = Artifacts in staged files
    - B = Artifacts associated with ticket
    """
    results = []

    for ticket_id in context.task_refs:
        # Get artifact sets
        A = set(context.staged_artifacts.values())  # Staged artifacts
        B = get_ticket_artifact_associations(ticket_id)  # Ticket artifacts

        # Set operations
        overlap = A & B          # In both
        staged_only = A - B      # In commit, not ticket
        ticket_only = B - A      # In ticket, not commit

        # Determine if resolution needed
        requires_resolution = False
        suggested_action = None

        if staged_only and config.artifact_consistency.staged_not_in_associations != "ignore":
            requires_resolution = True
            suggested_action = "Add artifacts to ticket associations"

        results.append(TriangleValidationResult(
            ticket_id=ticket_id,
            overlap=overlap,
            staged_only=staged_only,
            ticket_only=ticket_only,
            is_valid=not requires_resolution or config.artifact_consistency.mode == "warn",
            requires_resolution=requires_resolution,
            suggested_action=suggested_action
        ))

    # Also check for files matching OTHER tasks (not referenced)
    all_referenced = set(context.task_refs + context.completion_claims)
    for artifact_id in context.staged_artifacts.values():
        other_tickets = find_tickets_for_artifact(artifact_id)
        unreferenced = other_tickets - all_referenced

        if unreferenced and config.artifact_consistency.no_task_ref != "ignore":
            # Suggest adding task references
            results.append(TriangleValidationResult(
                ticket_id="<unreferenced>",
                overlap=set(),
                staged_only=set([artifact_id]),
                ticket_only=set(),
                is_valid=config.artifact_consistency.mode != "strict",
                requires_resolution=True,
                suggested_action=f"Consider adding Task: references for {unreferenced}"
            ))

    return results
```

### Phase 3: Completion Verification

```python
@dataclass
class CompletionVerificationResult:
    """Result of completion verification for one ticket."""

    ticket_id: str
    can_complete: bool
    blocking_reasons: List[str]
    unmet_criteria: List[str]


def phase_3_completion_verification(
    context: PreCommitContext,
    config: PreCommitConfig
) -> List[CompletionVerificationResult]:
    """
    Phase 3: Verify completion claims can be satisfied.

    For each Completes: reference:
    - Load ticket and check can_transition_to(COMPLETED)
    - Block commit if criteria not met
    """
    results = []

    for ticket_id in context.completion_claims:
        ticket = load_ticket(ticket_id)

        if ticket is None:
            results.append(CompletionVerificationResult(
                ticket_id=ticket_id,
                can_complete=False,
                blocking_reasons=[f"Ticket {ticket_id} not found"],
                unmet_criteria=[]
            ))
            continue

        # Use Unified Ticket Architecture's deterministic check
        can_complete, blocking_reasons = ticket.can_transition_to(TicketStatus.COMPLETED)

        # Get detailed unmet criteria
        unmet_criteria = [
            c.description
            for c in ticket.criteria
            if c.blocks_transition_to == TicketStatus.COMPLETED and not c.is_met
        ]

        results.append(CompletionVerificationResult(
            ticket_id=ticket_id,
            can_complete=can_complete,
            blocking_reasons=blocking_reasons,
            unmet_criteria=unmet_criteria
        ))

    return results
```

### Phase 4: Persist Relationships

```python
def phase_4_persist_relationships(
    context: PreCommitContext,
    triangle_results: List[TriangleValidationResult],
    user_resolutions: Dict[str, Resolution]
) -> None:
    """
    Phase 4: Persist all relationship entities.

    Only runs if Phases 2 and 3 passed (or user chose to proceed).
    """
    # Create TicketCommitLink for each Task: reference
    for ticket_id in context.task_refs:
        signals = build_signals(context, ticket_id)

        link = TicketCommitLink.from_pre_commit(
            ticket_id=ticket_id,
            commit_sha=context.commit_sha,
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=signals
        )
        save_ticket_commit_link(link)

    # Create TicketCommitLink for each Completes: reference
    for ticket_id in context.completion_claims:
        signals = build_signals(context, ticket_id)

        link = TicketCommitLink.from_pre_commit(
            ticket_id=ticket_id,
            commit_sha=context.commit_sha,
            reference_type=ReferenceType.COMPLETION_CLAIM,
            signals=signals
        )
        save_ticket_commit_link(link)

        # Also transition ticket to COMPLETED
        complete_ticket(ticket_id)

    # Create CommitArtifactChange for each staged file
    for change in context.pending_changes:
        change.commit_sha = context.commit_sha  # Now have real SHA
        save_commit_artifact_change(change)

    # Update TicketArtifactAssociation if user approved additions
    for result in triangle_results:
        resolution = user_resolutions.get(result.ticket_id)

        if resolution == Resolution.UPDATE_ASSOCIATIONS:
            for artifact_id in result.staged_only:
                association = TicketArtifactAssociation.from_commit_bootstrap(
                    ticket_id=result.ticket_id,
                    artifact_id=artifact_id
                )
                save_ticket_artifact_association(association)


def build_signals(context: PreCommitContext, ticket_id: str) -> LinkSignals:
    """Build link signals for a ticket reference."""

    # File overlap signal
    staged = set(context.staged_artifacts.values())
    ticket = get_ticket_artifact_associations(ticket_id)
    overlap = staged & ticket

    file_signal = FileOverlapSignal(
        matched=len(overlap) > 0,
        overlapping_artifact_ids=list(overlap)
    )
    file_signal.calculate_confidence(len(staged))

    # Message reference signal
    is_task_ref = ticket_id in context.task_refs
    is_completion = ticket_id in context.completion_claims

    message_signal = MessageRefSignal(
        matched=is_task_ref or is_completion,
        ticket_ids=[ticket_id],
        reference_type=ReferenceType.COMPLETION_CLAIM if is_completion else ReferenceType.TASK_REFERENCE
    )

    return LinkSignals(
        file_overlap=file_signal,
        message_ref=message_signal,
        manual=None
    )
```

---

## Resolution Options

When discrepancies are detected, users can choose from these resolutions:

```python
class Resolution(str, Enum):
    """User resolution for discrepancies."""

    UPDATE_ASSOCIATIONS = "update_associations"  # Add artifacts to ticket
    UPDATE_MESSAGE = "update_message"            # Change task reference
    ADD_REFERENCE = "add_reference"              # Include additional task
    PROCEED = "proceed"                          # Override, commit as-is
    CANCEL = "cancel"                            # Abort commit
```

### Resolution Descriptions

| Resolution | When to Use | Effect |
|------------|-------------|--------|
| `UPDATE_ASSOCIATIONS` | Staged files should be tracked by ticket | Creates TicketArtifactAssociation records |
| `UPDATE_MESSAGE` | Wrong task referenced | Re-opens editor to fix message |
| `ADD_REFERENCE` | Missing task reference | Adds Task: line to message |
| `PROCEED` | Override intentionally | Commits without updating associations |
| `CANCEL` | Need to reconsider | Aborts commit entirely |

### Resolution Flow

```
Pre-commit detects discrepancy
         |
         v
+-------------------+
| Display Options   |
| 1. Add to ticket  |
| 2. Edit message   |
| 3. Add reference  |
| 4. Proceed anyway |
| 5. Cancel         |
+-------------------+
         |
         v
   User selects
         |
   +-----+-----+
   |     |     |
   v     v     v
Update  Edit  Abort
 YAML  Message Commit
```

---

## Configuration Schema

```yaml
# .vibey/config/git_hooks.yaml

pre_commit:
  # Master switch
  enabled: true

  # Phase 2: Artifact/file consistency
  artifact_consistency:
    # Overall mode for artifact checks
    mode: prompt  # off | warn | prompt | strict

    # Specific behaviors
    on_mismatch:
      # Files in commit but not in ticket's associations
      staged_not_in_associations: prompt  # ignore | warn | prompt | block

      # Files in ticket's associations but not in commit
      # (Normal - not all files change each time)
      associations_not_in_staged: ignore  # ignore | warn

      # Staged files don't match ANY task associations
      no_task_ref: warn  # ignore | warn | prompt | block

  # Phase 3: Completion verification
  completion_verification:
    # Mode for completion claims
    mode: strict  # off | warn | strict

    # Block commit if Completes: claimed but criteria unmet
    block_on_unmet_criteria: true

    # Show progress for each criterion
    show_criteria_progress: true

  # Commit message template
  template:
    # Automatically install .gitmessage template
    auto_install: true

    # Path to template file
    path: .gitmessage

    # Configure git to use template
    configure_git: true

  # Output formatting
  output:
    # Use colors in terminal
    use_colors: true

    # Show detailed artifact paths
    show_artifact_paths: true

    # Verbosity level
    verbosity: normal  # quiet | normal | verbose
```

### Mode Behaviors

| Mode | Behavior |
|------|----------|
| `off` | Check skipped entirely |
| `warn` | Show issues, commit proceeds |
| `prompt` | Show issues, ask user for resolution |
| `strict` | Block commit until resolved |

### Configuration Loading

```python
@dataclass
class PreCommitConfig:
    """Configuration for pre-commit hook."""

    enabled: bool = True

    artifact_consistency: ArtifactConsistencyConfig = field(
        default_factory=ArtifactConsistencyConfig
    )
    completion_verification: CompletionVerificationConfig = field(
        default_factory=CompletionVerificationConfig
    )
    template: TemplateConfig = field(default_factory=TemplateConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(cls, config_path: Path = None) -> "PreCommitConfig":
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(".vibey/config/git_hooks.yaml")

        if not config_path.exists():
            return cls()  # Default configuration

        with open(config_path) as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data.get("pre_commit", {}))


@dataclass
class ArtifactConsistencyConfig:
    """Configuration for artifact consistency checks."""

    mode: str = "prompt"
    staged_not_in_associations: str = "prompt"
    associations_not_in_staged: str = "ignore"
    no_task_ref: str = "warn"


@dataclass
class CompletionVerificationConfig:
    """Configuration for completion verification."""

    mode: str = "strict"
    block_on_unmet_criteria: bool = True
    show_criteria_progress: bool = True
```

---

## Commit Message Template

### Template File

```
# <type>(<scope>): <subject>
#
# Task: <TASK_ID>
# Completes: <TASK_ID>  # Only if task is actually complete
#
# <body>
#
# -------------------------------------------------------------------------
# TYPE: feat | fix | docs | style | refactor | test | chore
#
# TASK MARKERS:
#   Task: <ULID>              - Associates commit with task (work was done)
#   Completes: <ULID>         - Claims task completion (triggers criteria check)
#
# MULTI-TASK FORMAT:
#   Task: 01TASK_A, 01TASK_B  - Multiple tasks on one line
#   Task: 01TASK_A            - Or separate lines
#   Task: 01TASK_B
#
# EXAMPLE:
#   feat(auth): Add JWT validation middleware
#
#   Task: 01KCQ9YS0KE8WSYKZ21XG6WBQX
#   Completes: 01KCQ9YS0KE8WSYKZ21XG6WBQX
#
#   Implements JWT token validation with configurable expiry.
#   Adds middleware for protected routes.
# -------------------------------------------------------------------------
```

### Template Installation

```bash
# Manual installation
vibey git setup-template

# Or automatically via configuration
# git_hooks.yaml: template.auto_install: true
```

### Setup Command Implementation

```python
def setup_commit_template(force: bool = False) -> None:
    """
    Install commit message template.

    1. Write .gitmessage file
    2. Configure git to use it
    """
    template_path = Path(".gitmessage")

    if template_path.exists() and not force:
        raise TemplateExistsError(
            f"{template_path} already exists. Use --force to overwrite."
        )

    # Write template
    template_content = get_template_content()
    template_path.write_text(template_content)

    # Configure git
    subprocess.run(
        ["git", "config", "commit.template", str(template_path)],
        check=True
    )

    print(f"Installed commit template at {template_path}")
    print("Git configured to use template for commit messages.")
```

### Message Parsing

```python
import re
from typing import Tuple, List


def parse_commit_message(message: str) -> Tuple[List[str], List[str]]:
    """
    Parse task references from commit message.

    Returns:
        Tuple of (task_refs, completion_claims)
    """
    task_refs = []
    completion_claims = []

    for line in message.split("\n"):
        line = line.strip()

        # Skip comments
        if line.startswith("#"):
            continue

        # Parse Task: lines
        task_match = re.match(r"^Task:\s*(.+)$", line, re.IGNORECASE)
        if task_match:
            ids = [id.strip() for id in task_match.group(1).split(",")]
            task_refs.extend(ids)
            continue

        # Parse Completes: lines
        completes_match = re.match(r"^Completes:\s*(.+)$", line, re.IGNORECASE)
        if completes_match:
            ids = [id.strip() for id in completes_match.group(1).split(",")]
            completion_claims.extend(ids)
            continue

    return task_refs, completion_claims


def validate_ulid(ulid: str) -> bool:
    """Validate ULID format (26 characters, Crockford base32)."""
    if len(ulid) != 26:
        return False

    valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
    return all(c.upper() in valid_chars for c in ulid)
```

---

## Implementation Notes

### Hook Installation

The pre-commit hook integrates with git's hook system:

```bash
# Install hook
vibey git install-hooks

# This creates/updates .git/hooks/pre-commit
```

```python
def install_pre_commit_hook(force: bool = False) -> None:
    """Install the pre-commit hook."""

    hook_path = Path(".git/hooks/pre-commit")

    if hook_path.exists() and not force:
        # Check if it's our hook or user's hook
        content = hook_path.read_text()
        if "vibey" not in content:
            raise HookExistsError(
                "Pre-commit hook exists. Use --force to overwrite or "
                "manually add 'vibey git pre-commit' to existing hook."
            )

    hook_content = """#!/bin/sh
# Vibey pre-commit hook
# Validates commit message task references and artifact consistency

vibey git pre-commit "$@"
exit $?
"""

    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)

    print(f"Installed pre-commit hook at {hook_path}")
```

### Error Handling

```python
class PreCommitError(Exception):
    """Base error for pre-commit hook."""
    pass


class ValidationError(PreCommitError):
    """Validation failed - commit should be blocked."""

    def __init__(self, phase: str, message: str, details: List[str] = None):
        self.phase = phase
        self.details = details or []
        super().__init__(f"Phase {phase}: {message}")


class CompletionBlockedError(ValidationError):
    """Completion claim cannot be satisfied."""

    def __init__(self, ticket_id: str, unmet_criteria: List[str]):
        self.ticket_id = ticket_id
        self.unmet_criteria = unmet_criteria
        super().__init__(
            phase="3",
            message=f"Cannot complete {ticket_id}",
            details=unmet_criteria
        )
```

### Testing Strategy

```python
# Test cases for pre-commit hook

def test_phase_1_parses_task_refs():
    """Message with Task: lines should be parsed correctly."""
    message = "feat: Add feature\n\nTask: 01TASK123\nTask: 01TASK456"
    context = phase_1_collect_data(message=message, staged_files=[])
    assert context.task_refs == ["01TASK123", "01TASK456"]


def test_phase_2_detects_staged_not_in_associations():
    """Staged files not in ticket should be flagged."""
    context = PreCommitContext(
        staged_artifacts={"src/new.py": "art_new"},
        task_refs=["01TASK123"]
    )
    # Mock ticket has no artifact associations
    results = phase_2_triangle_validation(context, config)
    assert results[0].staged_only == {"art_new"}
    assert results[0].requires_resolution


def test_phase_3_blocks_incomplete_completion():
    """Completes: claim with unmet criteria should block."""
    context = PreCommitContext(
        completion_claims=["01TASK_INCOMPLETE"]
    )
    # Mock ticket has unmet criteria
    results = phase_3_completion_verification(context, config)
    assert not results[0].can_complete
    assert len(results[0].unmet_criteria) > 0


def test_phase_4_persists_all_relationships():
    """All relationships should be persisted after successful validation."""
    # Run full hook flow
    # Assert TicketCommitLink created
    # Assert CommitArtifactChange created
    # Assert TicketArtifactAssociation created (if user approved)
```

### CLI Commands

```bash
# Pre-commit hook entry point (called by git hook)
vibey git pre-commit

# Install hooks
vibey git install-hooks
vibey git install-hooks --force

# Setup commit template
vibey git setup-template
vibey git setup-template --force

# Manual artifact association
vibey task add-artifact <task-id> <file-path>

# View commit links for ticket
vibey task commits <task-id>

# View tickets for commit
vibey git show-tickets <commit-sha>
```

---

## Appendix: Triangle Query Examples

With all three relationships, powerful queries become possible:

| Query | Method |
|-------|--------|
| What commits touched this ticket? | `TicketCommitLink WHERE ticket_id = X` |
| What artifacts are associated with this ticket? | `TicketArtifactAssociation WHERE ticket_id = X` |
| What artifacts did this commit change? | `CommitArtifactChange WHERE commit_sha = X` |
| What tickets were affected by changes to this artifact? | `Artifact -> TicketArtifactAssociation -> Ticket` |
| Did commit X change artifacts outside its referenced tickets? | `CommitArtifactChange NOT IN (TicketCommitLink -> TicketArtifactAssociation)` |
| Full history of this artifact? | `CommitArtifactChange WHERE artifact_id = X ORDER BY recorded_at` |
| Validate commit integrity | All three edges must be consistent |

---

## References

- Sprint 0 Design Decisions: `.vibey/roadmap/context/tracks/context-system-v2/sprints/sprint-0-planning-design-review/DESIGN_DECISIONS.md`
- Sprint 1 Plan: `.vibey/roadmap/context/tracks/context-system-v2/sprints/sprint-1-architecture-design/SPRINT_PLAN.md`
- Unified Ticket Architecture: `docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md`
