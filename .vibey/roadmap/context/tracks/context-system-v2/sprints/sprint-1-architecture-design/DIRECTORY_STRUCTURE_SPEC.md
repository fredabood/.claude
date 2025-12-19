# Context Directory Structure Specification

**Task ID:** 01KCMMK1MSFBZAM880C9K3BWPB
**Sprint:** Sprint 1: Context Architecture Design
**Track:** Context System V2
**Status:** Complete
**Created:** 2025-12-19

---

## Overview

This document defines the complete directory structure and YAML schemas for the Context System V2, which provides structured context management across three phases: planning, runtime, and post-mortem. The design integrates with the Unified Ticket Architecture (UTA) using relationship entities rather than standalone models.

---

## Part 1: Directory Structure

### 1.1 Target Layout

```
.vibey/roadmap/context/
├── plans/                           # Pre-work planning artifacts
│   └── {ticket_id}/                 # Directory per ticket (ULID)
│       ├── plan.yaml                # Structured metadata + artifact index
│       ├── DESIGN_ANALYSIS.md       # Optional: Deep analysis artifact
│       ├── IMPLEMENTATION_PLAN.md   # Optional: Step-by-step approach
│       └── {custom_artifact}.md     # Optional: Any additional artifacts
│
├── runtime/                         # Active session state
│   └── {ticket_id}.yaml             # Single file per ticket
│
└── post-mortems/                    # Completion summaries
    └── {ticket_id}.yaml             # Single file per ticket
```

### 1.2 Design Rationale

| Directory | File Structure | Rationale |
|-----------|---------------|-----------|
| `plans/` | Directory per ticket | Plans can have multiple markdown artifacts; directory allows extensibility |
| `runtime/` | Single YAML file | Runtime state is structured data only; no markdown needed |
| `post-mortems/` | Single YAML file | Summaries are structured; referenced commits provide detail |

### 1.3 Naming Conventions

- **Ticket directories/files**: Use ULID (26 characters, e.g., `01KCMMK1MSFBZAM880C9K3BWPB`)
- **Plan artifacts**: SCREAMING_SNAKE_CASE with `.md` extension (e.g., `DESIGN_ANALYSIS.md`)
- **Core metadata files**: Always `plan.yaml` for plans

---

## Part 2: Plan Context Schema

The plan context captures pre-work preparation and design thinking before implementation begins.

### 2.1 Full Schema

```yaml
# File: .vibey/roadmap/context/plans/{ticket_id}/plan.yaml
# Purpose: Pre-work planning metadata with artifact index

plan_context:
  # === IDENTITY ===
  ticket_id: "01KCMMK1MSFBZAM880C9K3BWPB"  # Required: ULID of the ticket
  version: "1.0"                            # Schema version for migrations

  # === LIFECYCLE ===
  created_at: "2025-12-19T10:00:00Z"        # Required: ISO 8601 timestamp
  created_by: "claude"                      # Required: Who created the plan
  updated_at: "2025-12-19T14:30:00Z"        # Optional: Last modification
  approved: false                           # Optional: Has plan been reviewed
  approved_by: null                         # Optional: Who approved
  approved_at: null                         # Optional: When approved

  # === PLANNING CONTENT ===
  goals:                                    # Required: What we're trying to achieve
    - "Implement user authentication"
    - "Support JWT and session-based auth"

  approach: |                               # Required: High-level approach
    Use existing auth library with decorator pattern.
    Add middleware for request validation.

  constraints:                              # Optional: Limitations to work within
    - "Must be backwards compatible"
    - "No breaking changes to existing endpoints"
    - "Performance impact < 10ms per request"

  success_criteria:                         # Required: How we know we're done
    - "All endpoints require authentication"
    - "Tests pass with both auth methods"
    - "Documentation updated"

  assumptions:                              # Optional: Things we're assuming to be true
    - "PyJWT library is available"
    - "Database supports token storage"

  risks:                                    # Optional: Known risks
    - description: "Middleware order may conflict with rate limiter"
      mitigation: "Test with rate limiter enabled"
      likelihood: "medium"

  # === ARTIFACT ASSOCIATIONS ===
  # These reference TicketArtifactAssociation entities in the UTA
  known_files:                              # Files we expect to modify
    - path: "src/auth.py"
      source: "plan_reference"              # How this was associated
      added: "2025-12-19T10:00:00Z"
      notes: "Main authentication module"   # Optional context
    - path: "src/middleware.py"
      source: "plan_reference"
      added: "2025-12-19T10:00:00Z"
    - path: "tests/test_auth.py"
      source: "plan_reference"
      added: "2025-12-19T10:00:00Z"

  # === PLAN ARTIFACTS ===
  # Index of markdown files in this directory
  artifacts:                                # Optional: Detailed analysis documents
    - file: "DESIGN_ANALYSIS.md"
      purpose: "Deep dive on existing auth system"
      tokens_estimate: 4500                 # Helps AI decide whether to load
      required_for_start: true              # Must read before starting work
    - file: "IMPLEMENTATION_PLAN.md"
      purpose: "Step-by-step implementation approach"
      tokens_estimate: 3200
      required_for_start: false
    - file: "API_DESIGN.md"
      purpose: "Endpoint contract definitions"
      tokens_estimate: 2100
      required_for_start: false

  # === CONTEXT REFERENCES ===
  # Links to related tickets for additional context
  related_tickets:                          # Optional: Related work
    - ticket_id: "01TASK_RELATED_1"
      relationship: "depends_on"            # depends_on | blocks | related_to
      notes: "Database migration must complete first"
    - ticket_id: "01TASK_RELATED_2"
      relationship: "related_to"
      notes: "Similar pattern used in that implementation"

  # === METADATA ===
  tags:                                     # Optional: Categorization
    - "authentication"
    - "security"
    - "api"
```

### 2.2 Required vs Optional Fields

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `ticket_id` | Yes | - | ULID of parent ticket |
| `version` | Yes | "1.0" | Schema version |
| `created_at` | Yes | - | ISO 8601 timestamp |
| `created_by` | Yes | - | Agent or user identifier |
| `goals` | Yes | - | List of goal strings |
| `approach` | Yes | - | Multiline string |
| `success_criteria` | Yes | - | List of criteria strings |
| `approved` | No | false | Plan review status |
| `constraints` | No | [] | List of constraint strings |
| `assumptions` | No | [] | List of assumption strings |
| `risks` | No | [] | List of risk objects |
| `known_files` | No | [] | List of file association objects |
| `artifacts` | No | [] | List of artifact index objects |
| `related_tickets` | No | [] | List of ticket reference objects |
| `tags` | No | [] | List of tag strings |

### 2.3 Known File Sources

The `source` field in `known_files` tracks how the file became associated with this ticket, aligning with the UTA's `AssociationSource` enum:

| Source | Description |
|--------|-------------|
| `plan_reference` | Added during planning phase |
| `runtime_tracking` | Added during active work via MCP |
| `commit_bootstrap` | Added when first commit references ticket |
| `manual` | Explicitly added via CLI command |
| `criterion_target` | Referenced by a FileExistsTarget criterion |

---

## Part 3: Runtime Context Schema

The runtime context captures active session state during task execution.

### 3.1 Full Schema

```yaml
# File: .vibey/roadmap/context/runtime/{ticket_id}.yaml
# Purpose: Active session state tracking

runtime_context:
  # === IDENTITY ===
  ticket_id: "01KCMMK1MSFBZAM880C9K3BWPB"  # Required: ULID of the ticket
  version: "1.0"                            # Schema version

  # === SESSION ===
  session_id: "sess_abc123def456"           # Required: Unique session identifier
  started_at: "2025-12-19T11:00:00Z"        # Required: When work began
  last_updated: "2025-12-19T14:30:00Z"      # Required: Last activity timestamp
  agent_id: "claude-opus-4-5"               # Optional: Which AI agent

  # === ACTIVE STATE ===
  active_files:                             # Files currently being worked on
    - path: "src/auth.py"
      opened_at: "2025-12-19T11:05:00Z"
      status: "modified"                    # opened | modified | saved
    - path: "src/jwt_handler.py"
      opened_at: "2025-12-19T12:30:00Z"
      status: "modified"

  # === DECISIONS ===
  decisions:                                # Choices made during implementation
    - decision: "Chose PyJWT over python-jose"
      rationale: "Better maintained, simpler API, smaller footprint"
      timestamp: "2025-12-19T12:15:00Z"
      alternatives_considered:              # Optional: What else was evaluated
        - "python-jose: More features but heavier"
        - "authlib: Too complex for our needs"
    - decision: "Use decorator pattern for auth"
      rationale: "Cleaner than middleware, more explicit"
      timestamp: "2025-12-19T13:00:00Z"

  # === DISCOVERIES ===
  discoveries:                              # Things learned during work
    - finding: "Existing rate limiter conflicts with auth middleware order"
      impact: "high"                        # low | medium | high
      timestamp: "2025-12-19T13:30:00Z"
      resolution: "Auth middleware must run before rate limiter"
    - finding: "User model already has token_hash field"
      impact: "low"
      timestamp: "2025-12-19T14:00:00Z"
      resolution: "Can reuse existing field, no migration needed"

  # === BLOCKERS ===
  blockers:                                 # Current impediments
    - description: "Need DB migration for refresh tokens table"
      severity: "blocking"                  # blocking | degraded | monitoring
      identified_at: "2025-12-19T14:15:00Z"
      ticket_id: null                       # Optional: If blocker has its own ticket
      workaround: null                      # Optional: Temporary solution
    - description: "CI pipeline failing on unrelated test"
      severity: "degraded"
      identified_at: "2025-12-19T14:20:00Z"
      workaround: "Skip failing test locally"

  # === PROGRESS ===
  checkpoint:                               # Current progress summary
    last_checkpoint: "2025-12-19T14:30:00Z"
    summary: "JWT validation working, decorator pattern implemented"
    next_steps:
      - "Add refresh token support"
      - "Write integration tests"
      - "Update API documentation"
    completion_estimate: 75                 # Percentage complete (0-100)

  # === TOKEN TRACKING ===
  token_usage:                              # Context window usage
    total_tokens: 45000                     # Cumulative tokens this session
    plan_tokens: 8000                       # Tokens from loading plan context
    code_tokens: 25000                      # Tokens from reading code files
    output_tokens: 12000                    # Tokens generated

  # === TOOL USAGE ===
  tool_invocations:                         # Optional: Track tool usage patterns
    read_file: 42
    edit_file: 18
    grep: 15
    bash: 8
```

### 3.2 Required vs Optional Fields

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `ticket_id` | Yes | - | ULID of parent ticket |
| `version` | Yes | "1.0" | Schema version |
| `session_id` | Yes | - | Unique session identifier |
| `started_at` | Yes | - | ISO 8601 timestamp |
| `last_updated` | Yes | - | ISO 8601 timestamp |
| `agent_id` | No | null | AI agent identifier |
| `active_files` | No | [] | List of active file objects |
| `decisions` | No | [] | List of decision objects |
| `discoveries` | No | [] | List of discovery objects |
| `blockers` | No | [] | List of blocker objects |
| `checkpoint` | No | null | Progress checkpoint object |
| `token_usage` | No | null | Token tracking object |
| `tool_invocations` | No | {} | Tool usage counts |

### 3.3 Session Lifecycle

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   CREATE    │────▶│    UPDATE    │────▶│   ARCHIVE   │
│             │     │              │     │             │
│ session_id  │     │ last_updated │     │ → post-     │
│ started_at  │     │ decisions    │     │   mortem    │
│ ticket_id   │     │ discoveries  │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
     │                    │                    │
     │                    │                    │
     └────────────────────┴────────────────────┘
                          │
                    Runtime YAML
                    (single file)
```

---

## Part 4: Post-Mortem Schema

The post-mortem context captures completion summaries for future reference and learning.

### 4.1 Full Schema

```yaml
# File: .vibey/roadmap/context/post-mortems/{ticket_id}.yaml
# Purpose: Completion summary and lessons learned

post_mortem:
  # === IDENTITY ===
  ticket_id: "01KCMMK1MSFBZAM880C9K3BWPB"  # Required: ULID of the ticket
  version: "1.0"                            # Schema version

  # === COMPLETION ===
  completed_at: "2025-12-19T16:00:00Z"      # Required: When work finished
  duration_hours: 5.0                       # Required: Total time spent
  session_count: 2                          # Optional: Number of sessions

  # === SUMMARY ===
  summary: |                                # Required: What was accomplished
    Implemented JWT authentication with decorator pattern.
    All endpoints now require auth, with support for both
    JWT tokens and session-based authentication.

  outcome: "success"                        # success | partial | failed | abandoned

  # === FILES CHANGED ===
  files_changed:                            # Files modified during work
    - path: "src/auth.py"
      change_type: "modified"               # added | modified | deleted | renamed
      lines_added: 150
      lines_removed: 20
    - path: "src/jwt_handler.py"
      change_type: "added"
      lines_added: 200
      lines_removed: 0
    - path: "src/middleware.py"
      change_type: "modified"
      lines_added: 45
      lines_removed: 10
    - path: "tests/test_auth.py"
      change_type: "added"
      lines_added: 300
      lines_removed: 0

  # === KEY DECISIONS ===
  key_decisions:                            # Important choices made
    - decision: "PyJWT for token handling"
      rationale: "Simpler API, better maintained"
      impact: "Core dependency for auth system"
    - decision: "Decorator pattern for cleaner code"
      rationale: "More explicit than middleware, easier to test"
      impact: "All protected endpoints use @require_auth"

  # === LESSONS LEARNED ===
  lessons_learned:                          # What to remember for future
    - lesson: "Middleware order matters"
      details: "Auth must come before rate limiting"
      applies_to:                           # Tags for searchability
        - "middleware"
        - "authentication"
    - lesson: "Test with all auth methods"
      details: "JWT and session auth have different edge cases"
      applies_to:
        - "testing"
        - "authentication"

  # === FOLLOW-UP ITEMS ===
  follow_up_items:                          # Work identified but not done
    - description: "Add refresh token support"
      priority: "high"
      ticket_created: "01KCFOLLOWUP1"       # Optional: If follow-up ticket exists
    - description: "Document auth flow in API docs"
      priority: "medium"
      ticket_created: null
    - description: "Add rate limiting per user"
      priority: "low"
      ticket_created: null

  # === COMMIT LINKS ===
  # These reference TicketCommitLink entities in the UTA
  commit_links:                             # Commits associated with this work
    - sha: "abc1234567890def"
      message: "feat(auth): Add JWT validation"
      reference_type: "TASK_REFERENCE"      # TASK_REFERENCE | COMPLETION_CLAIM
      signals:
        file_overlap:
          matched: true
          overlapping_artifact_ids:
            - "art_src_auth"
            - "art_src_jwt"
          confidence: 1.0
        message_ref:
          matched: true
          ticket_ids:
            - "01KCMMK1MSFBZAM880C9K3BWPB"
          reference_type: "TASK_REFERENCE"
          confidence: 1.0
        manual: null
      aggregate_confidence: 1.0
    - sha: "def4567890abc123"
      message: "feat(auth): Add decorator pattern and tests\n\nCompletes: 01KCMMK1MSFBZAM880C9K3BWPB"
      reference_type: "COMPLETION_CLAIM"
      signals:
        file_overlap:
          matched: true
          overlapping_artifact_ids:
            - "art_src_auth"
            - "art_tests_auth"
          confidence: 1.0
        message_ref:
          matched: true
          ticket_ids:
            - "01KCMMK1MSFBZAM880C9K3BWPB"
          reference_type: "COMPLETION_CLAIM"
          confidence: 1.0
        manual: null
      aggregate_confidence: 1.0

  # === METRICS ===
  metrics:                                  # Optional: Quantitative data
    token_usage:
      total: 125000
      plan_context: 15000
      code_reading: 60000
      generation: 50000
    files_touched: 4
    lines_changed: 695
    test_coverage_delta: "+15%"

  # === METADATA ===
  archived_at: "2025-12-19T16:05:00Z"       # When post-mortem was created
  archived_by: "claude"                      # Who created post-mortem
  runtime_session_ids:                       # Sessions that contributed
    - "sess_abc123def456"
    - "sess_xyz789ghi012"
```

### 4.2 Required vs Optional Fields

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `ticket_id` | Yes | - | ULID of parent ticket |
| `version` | Yes | "1.0" | Schema version |
| `completed_at` | Yes | - | ISO 8601 timestamp |
| `duration_hours` | Yes | - | Total time as float |
| `summary` | Yes | - | Multiline string |
| `outcome` | Yes | - | success/partial/failed/abandoned |
| `files_changed` | No | [] | List of file change objects |
| `key_decisions` | No | [] | List of decision objects |
| `lessons_learned` | No | [] | List of lesson objects |
| `follow_up_items` | No | [] | List of follow-up objects |
| `commit_links` | No | [] | List of commit link objects |
| `metrics` | No | null | Metrics object |
| `session_count` | No | 1 | Number of sessions |
| `archived_at` | No | null | ISO 8601 timestamp |
| `archived_by` | No | null | Who created post-mortem |
| `runtime_session_ids` | No | [] | List of session IDs |

### 4.3 Commit Link Signal Schema

The `signals` object in commit links aligns with the UTA's `LinkSignals` model:

```yaml
signals:
  file_overlap:                    # FileOverlapSignal
    matched: boolean               # Whether overlap was detected
    overlapping_artifact_ids: []   # Artifact IDs that overlapped
    confidence: float              # 0.0-1.0, based on overlap ratio

  message_ref:                     # MessageRefSignal
    matched: boolean               # Whether Task:/Completes: found
    ticket_ids: []                 # Ticket IDs referenced
    reference_type: string         # TASK_REFERENCE | COMPLETION_CLAIM
    confidence: float              # Always 1.0 when matched

  manual:                          # ManualSignal (nullable)
    matched: boolean
    linked_by: string              # User who linked
    linked_at: string              # ISO 8601 timestamp
    confidence: float              # Always 1.0
```

---

## Part 5: Path Utilities Design

### 5.1 ContextPaths Class

```python
"""
Path utilities for Context System V2.

File: vibey/roadmap/context/paths.py
"""

from pathlib import Path
from typing import Optional


class ContextPaths:
    """Centralized path resolution for context directories."""

    def __init__(self, roadmap_dir: Path):
        """
        Initialize context paths.

        Args:
            roadmap_dir: Path to .vibey/roadmap directory
        """
        self.roadmap_dir = roadmap_dir
        self.base = roadmap_dir / "context"

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

    def plan_artifact(self, ticket_id: str, filename: str) -> Path:
        """
        Get path to a plan artifact file.

        Args:
            ticket_id: ULID of the ticket
            filename: Name of artifact file (e.g., 'DESIGN_ANALYSIS.md')

        Returns:
            Path to plans/{ticket_id}/{filename}
        """
        return self.plans_dir(ticket_id) / filename

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

    # === QUERIES ===

    def list_plans(self) -> list[str]:
        """
        List all ticket IDs that have plan contexts.

        Returns:
            List of ticket ULIDs with plan directories
        """
        plans_dir = self.plans_dir()
        if not plans_dir.exists():
            return []
        return [
            d.name for d in plans_dir.iterdir()
            if d.is_dir() and self._is_valid_ulid(d.name)
        ]

    def list_runtime(self) -> list[str]:
        """
        List all ticket IDs that have active runtime contexts.

        Returns:
            List of ticket ULIDs with runtime files
        """
        runtime_dir = self.runtime_dir()
        if not runtime_dir.exists():
            return []
        return [
            f.stem for f in runtime_dir.glob("*.yaml")
            if self._is_valid_ulid(f.stem)
        ]

    def list_post_mortems(self) -> list[str]:
        """
        List all ticket IDs that have post-mortems.

        Returns:
            List of ticket ULIDs with post-mortem files
        """
        pm_dir = self.post_mortems_dir()
        if not pm_dir.exists():
            return []
        return [
            f.stem for f in pm_dir.glob("*.yaml")
            if self._is_valid_ulid(f.stem)
        ]

    def get_context_status(self, ticket_id: str) -> dict:
        """
        Get context status for a ticket.

        Args:
            ticket_id: ULID of the ticket

        Returns:
            Dict with has_plan, has_runtime, has_post_mortem booleans
        """
        return {
            "has_plan": self.plan_exists(ticket_id),
            "has_runtime": self.runtime_exists(ticket_id),
            "has_post_mortem": self.post_mortem_exists(ticket_id),
        }

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
                f"Invalid ticket ID: {ticket_id}. "
                "Expected 26-character ULID."
            )

    @staticmethod
    def _is_valid_ulid(value: str) -> bool:
        """Check if string appears to be a valid ULID."""
        if len(value) != 26:
            return False
        # ULIDs use Crockford's Base32 alphabet
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        return all(c.upper() in valid_chars for c in value)
```

### 5.2 Usage Examples

```python
from pathlib import Path
from vibey.roadmap.context.paths import ContextPaths

# Initialize
roadmap_dir = Path(".vibey/roadmap")
ctx_paths = ContextPaths(roadmap_dir)

# Ensure directories exist
ctx_paths.ensure_directories()

# Work with plan context
ticket_id = "01KCMMK1MSFBZAM880C9K3BWPB"
plan_yaml = ctx_paths.plan_yaml(ticket_id)
design_doc = ctx_paths.plan_artifact(ticket_id, "DESIGN_ANALYSIS.md")

# Work with runtime context
runtime_yaml = ctx_paths.runtime_yaml(ticket_id)

# Work with post-mortems
post_mortem = ctx_paths.post_mortem_yaml(ticket_id)

# Query context status
status = ctx_paths.get_context_status(ticket_id)
# {'has_plan': True, 'has_runtime': True, 'has_post_mortem': False}

# List all tickets with runtime contexts
active_tickets = ctx_paths.list_runtime()
```

---

## Part 6: Migration Notes

### 6.1 Current State

The existing `.vibey/roadmap/context/` directory contains:

```
context/
├── EMBEDDED_TASK_MIGRATION_PLAN.md    # Legacy planning doc
├── PLATFORM_COMPATIBILITY_REFACTOR_PLAN.md  # Legacy planning doc
├── task_slug_mapping.json             # Migration artifact
├── tasks/                             # Empty or legacy
├── tracks/                            # Track-specific context
│   └── context-system-v2/             # Current track planning
│       └── sprints/
│           ├── sprint-0-planning-design-review/
│           └── sprint-1-architecture-design/
└── sprints/                           # Sprint-specific context
    └── {sprint-name}/
        └── various artifacts
```

### 6.2 Migration Strategy

**Phase 1: Create New Structure (Non-Breaking)**
1. Create `context/plans/`, `context/runtime/`, `context/post-mortems/` directories
2. New contexts use new structure
3. Existing content remains in place

**Phase 2: Migrate Active Contexts**
1. Identify tasks with active work
2. Create plan contexts from existing artifacts where applicable
3. Track runtime state for in-progress work

**Phase 3: Archive Legacy Content**
1. Move `tracks/` content to archival location
2. Move `sprints/` content to archival location
3. Keep `task_slug_mapping.json` for reference
4. Legacy planning docs become historical artifacts

### 6.3 Compatibility Considerations

| Concern | Approach |
|---------|----------|
| Existing sprint contexts | Remain functional; not migrated automatically |
| Track-specific contexts | Remain functional; manual migration when ready |
| Legacy planning docs | Archive or convert to post-mortems |
| CLI commands | Add new commands for new structure; deprecate old |

### 6.4 Migration CLI Commands (Proposed)

```bash
# Initialize new context directories
vibey context init

# Migrate existing context to new format
vibey context migrate --ticket-id 01TASK123

# Archive legacy content
vibey context archive-legacy

# Validate context structure
vibey context validate
```

---

## Part 7: Integration with Unified Ticket Architecture

### 7.1 Relationship Entity Mappings

| Context Schema Field | UTA Entity | Notes |
|---------------------|------------|-------|
| `known_files` | `TicketArtifactAssociation` | Source field maps to `association_source` |
| `commit_links` | `TicketCommitLink` | Signals map to `LinkSignals` |
| `commit_links.signals.file_overlap` | `FileOverlapSignal` | Confidence from overlap ratio |
| `commit_links.signals.message_ref` | `MessageRefSignal` | From `Task:` / `Completes:` parsing |
| `files_changed` | `CommitArtifactChange` | Change type maps to `ChangeType` enum |

### 7.2 Pre-Commit Hook Integration

When the unified pre-commit hook runs:

1. **Plan Context Read**: Loads `known_files` to compare against staged files
2. **Triangle Validation**: Uses plan context as expected file set
3. **Post-Mortem Write**: On completion, generates post-mortem from runtime context

### 7.3 MCP Tool Integration

| MCP Tool | Context Type | Operation |
|----------|-------------|-----------|
| `context_plan_create` | Plan | Create new plan context |
| `context_plan_get` | Plan | Read plan context |
| `context_plan_add_artifact` | Plan | Add artifact reference |
| `context_runtime_start` | Runtime | Begin session |
| `context_runtime_update` | Runtime | Update state |
| `context_runtime_log_decision` | Runtime | Add decision |
| `context_post_mortem_create` | Post-Mortem | Generate from runtime |
| `context_post_mortem_get` | Post-Mortem | Read post-mortem |

---

## Part 8: Validation Rules

### 8.1 Plan Context Validation

```python
def validate_plan_context(plan: dict) -> list[str]:
    """Validate plan context structure."""
    errors = []

    ctx = plan.get("plan_context", {})

    # Required fields
    if not ctx.get("ticket_id"):
        errors.append("Missing required field: ticket_id")
    if not ctx.get("goals"):
        errors.append("Missing required field: goals")
    if not ctx.get("approach"):
        errors.append("Missing required field: approach")
    if not ctx.get("success_criteria"):
        errors.append("Missing required field: success_criteria")

    # Validate ticket_id format
    ticket_id = ctx.get("ticket_id", "")
    if ticket_id and not is_valid_ulid(ticket_id):
        errors.append(f"Invalid ULID format: {ticket_id}")

    # Validate known_files sources
    valid_sources = {
        "plan_reference", "runtime_tracking",
        "commit_bootstrap", "manual", "criterion_target"
    }
    for file in ctx.get("known_files", []):
        if file.get("source") not in valid_sources:
            errors.append(f"Invalid source for file {file.get('path')}")

    return errors
```

### 8.2 Runtime Context Validation

```python
def validate_runtime_context(runtime: dict) -> list[str]:
    """Validate runtime context structure."""
    errors = []

    ctx = runtime.get("runtime_context", {})

    # Required fields
    for field in ["ticket_id", "session_id", "started_at", "last_updated"]:
        if not ctx.get(field):
            errors.append(f"Missing required field: {field}")

    # Validate timestamps
    for ts_field in ["started_at", "last_updated"]:
        ts = ctx.get(ts_field)
        if ts and not is_valid_iso8601(ts):
            errors.append(f"Invalid timestamp format: {ts_field}")

    # Validate blocker severity
    valid_severities = {"blocking", "degraded", "monitoring"}
    for blocker in ctx.get("blockers", []):
        if blocker.get("severity") not in valid_severities:
            errors.append(f"Invalid blocker severity: {blocker.get('severity')}")

    return errors
```

### 8.3 Post-Mortem Validation

```python
def validate_post_mortem(pm: dict) -> list[str]:
    """Validate post-mortem structure."""
    errors = []

    ctx = pm.get("post_mortem", {})

    # Required fields
    for field in ["ticket_id", "completed_at", "duration_hours", "summary", "outcome"]:
        if not ctx.get(field):
            errors.append(f"Missing required field: {field}")

    # Validate outcome
    valid_outcomes = {"success", "partial", "failed", "abandoned"}
    if ctx.get("outcome") not in valid_outcomes:
        errors.append(f"Invalid outcome: {ctx.get('outcome')}")

    # Validate commit link signals
    for link in ctx.get("commit_links", []):
        signals = link.get("signals", {})
        for signal_type in ["file_overlap", "message_ref"]:
            if signal := signals.get(signal_type):
                if "matched" not in signal:
                    errors.append(f"Missing 'matched' in {signal_type} signal")
                if "confidence" in signal:
                    conf = signal["confidence"]
                    if not (0.0 <= conf <= 1.0):
                        errors.append(f"Confidence out of range: {conf}")

    return errors
```

---

## Appendix A: Complete File Examples

### A.1 Example Plan Context

```yaml
# File: .vibey/roadmap/context/plans/01KCMMK1MSFBZAM880C9K3BWPB/plan.yaml

plan_context:
  ticket_id: "01KCMMK1MSFBZAM880C9K3BWPB"
  version: "1.0"
  created_at: "2025-12-19T10:00:00Z"
  created_by: "claude"
  approved: true
  approved_by: "user"
  approved_at: "2025-12-19T10:30:00Z"

  goals:
    - "Define context directory structure with YAML schemas"
    - "Create path utilities for context operations"
    - "Document migration strategy for existing content"

  approach: |
    Create comprehensive specification document covering:
    1. Directory layout for plans/runtime/post-mortems
    2. Complete YAML schemas with examples
    3. Python path utility class design
    4. Migration notes for existing context content

  constraints:
    - "Must integrate with Unified Ticket Architecture"
    - "YAML schemas must be consistent with existing roadmap patterns"
    - "Path utilities must use standard library only"

  success_criteria:
    - "All three context types have complete YAML schemas"
    - "Path utility class designed with all required methods"
    - "Migration strategy documented"

  known_files:
    - path: ".vibey/roadmap/context/tracks/context-system-v2/sprints/sprint-0-planning-design-review/DESIGN_DECISIONS.md"
      source: "plan_reference"
      added: "2025-12-19T10:00:00Z"
      notes: "Design decisions from Sprint 0"
    - path: ".vibey/roadmap/context/tracks/context-system-v2/sprints/sprint-1-architecture-design/SPRINT_PLAN.md"
      source: "plan_reference"
      added: "2025-12-19T10:00:00Z"
      notes: "Sprint 1 task definitions"

  artifacts: []

  tags:
    - "context-system"
    - "architecture"
    - "specification"
```

### A.2 Example Runtime Context

```yaml
# File: .vibey/roadmap/context/runtime/01KCMMK1MSFBZAM880C9K3BWPB.yaml

runtime_context:
  ticket_id: "01KCMMK1MSFBZAM880C9K3BWPB"
  version: "1.0"
  session_id: "sess_20251219_claude_opus"
  started_at: "2025-12-19T10:45:00Z"
  last_updated: "2025-12-19T12:30:00Z"
  agent_id: "claude-opus-4-5"

  active_files:
    - path: "DIRECTORY_STRUCTURE_SPEC.md"
      opened_at: "2025-12-19T10:50:00Z"
      status: "modified"

  decisions:
    - decision: "Use ULID-based directory names for plans"
      rationale: "Consistent with existing roadmap YAML file naming"
      timestamp: "2025-12-19T11:00:00Z"
    - decision: "Single YAML file for runtime and post-mortem"
      rationale: "No need for multiple artifacts; all structured data"
      timestamp: "2025-12-19T11:15:00Z"

  discoveries:
    - finding: "Existing context/ has track-specific subdirectories"
      impact: "medium"
      timestamp: "2025-12-19T11:30:00Z"
      resolution: "Include migration strategy in spec"

  blockers: []

  checkpoint:
    last_checkpoint: "2025-12-19T12:30:00Z"
    summary: "YAML schemas complete, working on path utilities"
    next_steps:
      - "Complete path utility class design"
      - "Add migration notes section"
      - "Create example files"
    completion_estimate: 80

  token_usage:
    total_tokens: 35000
    plan_tokens: 5000
    code_tokens: 20000
    output_tokens: 10000
```

### A.3 Example Post-Mortem

```yaml
# File: .vibey/roadmap/context/post-mortems/01KCMMK1MSFBZAM880C9K3BWPB.yaml

post_mortem:
  ticket_id: "01KCMMK1MSFBZAM880C9K3BWPB"
  version: "1.0"
  completed_at: "2025-12-19T13:00:00Z"
  duration_hours: 2.25
  session_count: 1

  summary: |
    Created comprehensive directory structure specification for Context System V2.
    Defined complete YAML schemas for plan, runtime, and post-mortem contexts.
    Designed path utility class with all required methods.
    Documented migration strategy for existing context content.

  outcome: "success"

  files_changed:
    - path: ".vibey/roadmap/context/tracks/context-system-v2/sprints/sprint-1-architecture-design/DIRECTORY_STRUCTURE_SPEC.md"
      change_type: "added"
      lines_added: 950
      lines_removed: 0

  key_decisions:
    - decision: "Directory per ticket for plans, single file for runtime/post-mortem"
      rationale: "Plans need artifacts; others are pure structured data"
      impact: "Defines storage layout for all context types"
    - decision: "Integrate with UTA relationship entities"
      rationale: "Leverage existing architecture rather than standalone models"
      impact: "Known files and commit links use UTA entities"

  lessons_learned:
    - lesson: "Read design decisions before starting"
      details: "Sprint 0 decisions informed all schema choices"
      applies_to:
        - "planning"
        - "context-system"

  follow_up_items:
    - description: "Implement ContextPaths class"
      priority: "high"
      ticket_created: null
    - description: "Create CLI commands for context operations"
      priority: "high"
      ticket_created: null

  commit_links: []

  metrics:
    token_usage:
      total: 45000
      plan_context: 5000
      code_reading: 25000
      generation: 15000
    files_touched: 1
    lines_changed: 950

  archived_at: "2025-12-19T13:05:00Z"
  archived_by: "claude"
  runtime_session_ids:
    - "sess_20251219_claude_opus"
```

---

## Appendix B: Schema Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-19 | Initial specification |

---

## References

- [Sprint 0 Design Decisions](sprint-0-planning-design-review/DESIGN_DECISIONS.md)
- [Sprint 1 Plan](SPRINT_PLAN.md)
- [Unified Ticket Architecture](../../../../../docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md)
- [ADR-0001: ULID Identifiers](../../../../../docs/architecture/adr/0001-ulid-identifiers.md)
- [ADR-0002: Flat Directory Structure](../../../../../docs/architecture/adr/0002-flat-directory-structure.md)
