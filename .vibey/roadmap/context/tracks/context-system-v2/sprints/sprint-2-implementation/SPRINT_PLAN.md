# Sprint 2: Context Implementation (Integrated Architecture)

## Overview
- **Track:** Context System V2
- **Sprint ID:** 01KCMTY669JGT3WYPZB78ATWBT
- **Focus:** Implement relationship entities, triangle validation, and context management
- **Reference:** Sprint 0 DESIGN_DECISIONS.md (Integrated Architecture)

## Key Architectural Decision

**This sprint implements relationships within the existing Unified Ticket Architecture:**
- No standalone `CommitLink` → Use `TicketCommitLink`
- No standalone `KnownFile` → Use `TicketArtifactAssociation`
- New `CommitArtifactChange` relationship entity
- Unified pre-commit hook with triangle validation

## Success Criteria
- [ ] Three relationship entity models implemented
- [ ] SQLite schema extended with relationship tables
- [ ] Unified pre-commit hook with triangle validation
- [ ] `Task:` and `Completes:` commit message parsing
- [ ] Context integrated into ticket data structure
- [ ] MCP tools for relationship management
- [ ] CLI commands for artifact association

---

## Task 1: Implement Relationship Entity Models
**ID:** `01KCMNCZS970T6MSXDY2CZA2YH`
**Priority:** Critical | **Complexity:** Complex | **Type:** Development

### Problem
Need to define the three relationship entities that form the triangle model.

### Implementation

**Location:** `vibey/roadmap/models/relationships.py`

```python
from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ReferenceType(str, Enum):
    TASK_REFERENCE = "task_reference"      # Task: line
    COMPLETION_CLAIM = "completion_claim"  # Completes: line


class AssociationSource(str, Enum):
    PLAN_REFERENCE = "plan_reference"
    RUNTIME_TRACKING = "runtime_tracking"
    COMMIT_BOOTSTRAP = "commit_bootstrap"
    MANUAL = "manual"
    CRITERION_TARGET = "criterion_target"


class ChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class FileOverlapSignal(BaseModel):
    matched: bool
    overlapping_artifact_ids: List[str] = Field(default_factory=list)
    confidence: float


class MessageRefSignal(BaseModel):
    matched: bool
    ticket_ids: List[str] = Field(default_factory=list)
    reference_type: Optional[ReferenceType] = None
    confidence: float = 1.0


class ManualSignal(BaseModel):
    matched: bool
    linked_by: Optional[str] = None
    linked_at: Optional[datetime] = None
    confidence: float = 1.0


class LinkSignals(BaseModel):
    file_overlap: Optional[FileOverlapSignal] = None
    message_ref: Optional[MessageRefSignal] = None
    manual: Optional[ManualSignal] = None


class TicketCommitLink(BaseModel):
    """Ticket <-> GitCommit relationship."""
    ticket_id: str
    commit_sha: str
    reference_type: ReferenceType
    signals: LinkSignals
    aggregate_confidence: float
    linked_at: datetime
    link_source: str  # pre_commit_hook | post_commit | manual


class TicketArtifactAssociation(BaseModel):
    """Ticket <-> Artifact relationship."""
    ticket_id: str
    artifact_id: str
    association_source: AssociationSource
    added_at: datetime
    added_by: Optional[str] = None


class CommitArtifactChange(BaseModel):
    """GitCommit <-> Artifact relationship."""
    commit_sha: str
    artifact_id: str
    change_type: ChangeType
    previous_path: Optional[str] = None  # For renames
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    recorded_at: datetime
```

### Acceptance Criteria
- [ ] All three relationship models implemented
- [ ] Enums for ReferenceType, AssociationSource, ChangeType
- [ ] Signal models for link detection
- [ ] Unit tests for model validation

---

## Task 2: Extend SQLite Schema with Relationship Tables
**Priority:** Critical | **Complexity:** Medium | **Type:** Development

### Problem
Need database tables for the three relationship entities.

### Implementation

```sql
-- TicketCommitLink: Ticket <-> GitCommit
CREATE TABLE ticket_commit_links (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    reference_type TEXT NOT NULL,  -- task_reference | completion_claim
    signals TEXT NOT NULL,          -- JSON: LinkSignals
    aggregate_confidence REAL NOT NULL,
    linked_at TEXT NOT NULL,
    link_source TEXT NOT NULL,

    UNIQUE(ticket_id, commit_sha, reference_type),
    FOREIGN KEY (ticket_id) REFERENCES tasks(id),
    FOREIGN KEY (commit_sha) REFERENCES git_commits(sha)
);

CREATE INDEX idx_tcl_ticket ON ticket_commit_links(ticket_id);
CREATE INDEX idx_tcl_commit ON ticket_commit_links(commit_sha);
CREATE INDEX idx_tcl_type ON ticket_commit_links(reference_type);


-- TicketArtifactAssociation: Ticket <-> Artifact
CREATE TABLE ticket_artifact_associations (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    association_source TEXT NOT NULL,
    added_at TEXT NOT NULL,
    added_by TEXT,

    UNIQUE(ticket_id, artifact_id),
    FOREIGN KEY (ticket_id) REFERENCES tasks(id),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX idx_taa_ticket ON ticket_artifact_associations(ticket_id);
CREATE INDEX idx_taa_artifact ON ticket_artifact_associations(artifact_id);
CREATE INDEX idx_taa_source ON ticket_artifact_associations(association_source);


-- CommitArtifactChange: GitCommit <-> Artifact
CREATE TABLE commit_artifact_changes (
    id TEXT PRIMARY KEY,
    commit_sha TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- added | modified | deleted | renamed
    previous_path TEXT,
    lines_added INTEGER,
    lines_removed INTEGER,
    recorded_at TEXT NOT NULL,

    UNIQUE(commit_sha, artifact_id),
    FOREIGN KEY (commit_sha) REFERENCES git_commits(sha),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX idx_cac_commit ON commit_artifact_changes(commit_sha);
CREATE INDEX idx_cac_artifact ON commit_artifact_changes(artifact_id);
CREATE INDEX idx_cac_type ON commit_artifact_changes(change_type);
```

### Views for Triangle Queries

```sql
-- Commits that touched a ticket (via any path)
CREATE VIEW v_ticket_commits AS
SELECT DISTINCT
    tcl.ticket_id,
    tcl.commit_sha,
    tcl.reference_type,
    tcl.aggregate_confidence
FROM ticket_commit_links tcl;

-- Artifacts associated with a ticket (via any source)
CREATE VIEW v_ticket_artifacts AS
SELECT DISTINCT
    taa.ticket_id,
    taa.artifact_id,
    a.paths,
    taa.association_source
FROM ticket_artifact_associations taa
JOIN artifacts a ON a.id = taa.artifact_id;

-- Full triangle: ticket -> commit -> artifacts changed
CREATE VIEW v_ticket_commit_artifacts AS
SELECT
    tcl.ticket_id,
    tcl.commit_sha,
    cac.artifact_id,
    cac.change_type,
    taa.association_source IS NOT NULL AS artifact_was_associated
FROM ticket_commit_links tcl
JOIN commit_artifact_changes cac ON cac.commit_sha = tcl.commit_sha
LEFT JOIN ticket_artifact_associations taa
    ON taa.ticket_id = tcl.ticket_id AND taa.artifact_id = cac.artifact_id;
```

### Acceptance Criteria
- [ ] Three relationship tables created
- [ ] Appropriate indexes for query performance
- [ ] Views for triangle queries
- [ ] Migration script for existing databases

---

## Task 3: Implement Unified Pre-Commit Hook with Triangle Validation
**ID:** `01KCMNDFWS0C2N2FJJBZRR3FC8`
**Priority:** Critical | **Complexity:** Complex | **Type:** Development

### Problem
Need a single pre-commit hook that validates across all three relationship edges.

### Implementation

**Location:** `vibey/operations/git/hooks/pre_commit.py`

```python
def run_pre_commit_hook(commit_message: str, staged_files: List[str], config: HookConfig) -> HookResult:
    """
    Unified pre-commit hook with triangle validation.

    Phases:
    1. Collect Data - parse message, resolve artifacts
    2. Triangle Validation - check consistency across relationships
    3. Completion Verification - verify criteria for Completes: claims
    4. Persist Relationships - create relationship records
    """

    # Phase 1: Collect Data
    task_refs = parse_task_references(commit_message)      # Task: lines
    completion_refs = parse_completion_claims(commit_message)  # Completes: lines
    staged_artifacts = resolve_to_artifacts(staged_files)

    # Phase 2: Triangle Validation
    validation_results = []
    for ticket_id in task_refs:
        result = validate_triangle(
            ticket_id=ticket_id,
            staged_artifacts=staged_artifacts,
            config=config.artifact_consistency
        )
        validation_results.append(result)

    # Handle validation issues based on mode
    if config.artifact_consistency.mode == "prompt":
        # Interactive resolution
        resolutions = prompt_for_resolutions(validation_results)
        apply_resolutions(resolutions)
    elif config.artifact_consistency.mode == "strict":
        if any(r.has_issues for r in validation_results):
            return HookResult(blocked=True, reasons=format_issues(validation_results))

    # Phase 3: Completion Verification
    for ticket_id in completion_refs:
        ticket = load_ticket(ticket_id)
        can_complete, reasons = ticket.can_transition_to(TicketStatus.COMPLETED)
        if not can_complete:
            return HookResult(
                blocked=True,
                reasons=[f"Cannot complete {ticket_id}: {r}" for r in reasons]
            )

    # Phase 4: Persist Relationships (done post-commit)
    return HookResult(
        blocked=False,
        pending_relationships=build_pending_relationships(
            task_refs, completion_refs, staged_artifacts
        )
    )
```

### Acceptance Criteria
- [ ] Four-phase hook implementation
- [ ] `Task:` and `Completes:` parsing
- [ ] Triangle validation logic
- [ ] Configurable modes (off/warn/prompt/strict)
- [ ] Integration with existing `can_transition_to()`

---

## Task 4: Implement Commit Message Template System
**ID:** `01KCQDE6HGQ909SDAYK1JM0DTB`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Need templated commit message format with both `Task:` and `Completes:` markers.

### Template

```
# <type>(<scope>): <subject>
#
# Task: <TASK_ID>           # Associates commit with task
# Completes: <TASK_ID>      # Claims task completion (optional)
#
# <body>
#
# Currently in-progress tasks:
# - 01TASK_A: Description of task A
# - 01TASK_B: Description of task B
```

### Implementation

```python
@cli.command('setup-template')
def setup_commit_template():
    """Install git commit message template."""
    # Get in-progress tasks
    in_progress = get_tasks_by_status(Status.IN_PROGRESS)

    # Generate template with hints
    template = generate_template(in_progress)

    # Write to .git/commit-template
    template_path = Path('.git/commit-template')
    template_path.write_text(template)

    # Configure git
    subprocess.run(['git', 'config', 'commit.template', str(template_path)])
```

### Acceptance Criteria
- [ ] Template file generation
- [ ] `vibey git setup-template` CLI command
- [ ] In-progress tasks shown as hints
- [ ] Both `Task:` and `Completes:` documented

---

## Task 5: Extend GitCommit Model
**Priority:** Medium | **Complexity:** Simple | **Type:** Development

### Problem
GitCommit needs to parse both `Task:` and `Completes:` lines.

### Implementation

```python
class GitCommit(BaseModel):
    sha: str
    message: str
    date: datetime
    author: str
    platform: str

    # Existing
    completes_tickets: List[str] = Field(default_factory=list)

    # New
    references_tickets: List[str] = Field(default_factory=list)

    @classmethod
    def from_git(cls, sha: str, repo_path: Path, platform: str) -> "GitCommit":
        # ... existing parsing ...

        # Parse both markers
        references = []
        completes = []
        for line in body.split('\n'):
            if line.startswith('Task:'):
                refs = line.replace('Task:', '').strip().split(',')
                references.extend(r.strip() for r in refs)
            elif line.startswith('Completes:'):
                ticket_id = line.replace('Completes:', '').strip()
                completes.append(ticket_id)

        return cls(
            # ... existing fields ...
            references_tickets=references,
            completes_tickets=completes
        )
```

### Acceptance Criteria
- [ ] `references_tickets` field added
- [ ] Parsing handles both single and comma-separated IDs
- [ ] Backwards compatible with existing commits

---

## Task 6: Add Context Management MCP Tools
**ID:** `01KCMGXG7BMKQNSFY2HS4G14XK`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
AI assistants need MCP tools to manage relationships.

### MCP Tools

```python
@mcp_tool
def associate_artifact(ticket_id: str, artifact_id: str, source: str = "runtime_tracking") -> dict:
    """Associate an artifact with a ticket."""
    assoc = TicketArtifactAssociation(
        ticket_id=ticket_id,
        artifact_id=artifact_id,
        association_source=AssociationSource(source),
        added_at=datetime.now(timezone.utc)
    )
    save_association(assoc)
    return {"status": "success", "association_id": assoc.id}


@mcp_tool
def get_ticket_artifacts(ticket_id: str) -> dict:
    """Get all artifacts associated with a ticket."""
    associations = query_associations(ticket_id=ticket_id)
    return {
        "ticket_id": ticket_id,
        "artifacts": [
            {"artifact_id": a.artifact_id, "source": a.association_source}
            for a in associations
        ]
    }


@mcp_tool
def get_ticket_commits(ticket_id: str) -> dict:
    """Get all commits linked to a ticket."""
    links = query_commit_links(ticket_id=ticket_id)
    return {
        "ticket_id": ticket_id,
        "commits": [
            {"sha": l.commit_sha, "type": l.reference_type, "confidence": l.aggregate_confidence}
            for l in links
        ]
    }


@mcp_tool
def get_artifact_history(artifact_id: str) -> dict:
    """Get commit history for an artifact."""
    changes = query_artifact_changes(artifact_id=artifact_id)
    return {
        "artifact_id": artifact_id,
        "changes": [
            {"sha": c.commit_sha, "type": c.change_type, "at": c.recorded_at.isoformat()}
            for c in changes
        ]
    }
```

### Acceptance Criteria
- [ ] `associate_artifact` tool
- [ ] `get_ticket_artifacts` tool
- [ ] `get_ticket_commits` tool
- [ ] `get_artifact_history` tool
- [ ] Tools registered in MCP server

---

## Task 7: Add CLI Commands for Relationship Management
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Commands

```bash
# Associate artifact with ticket
vibey task add-artifact <ticket_id> <artifact_id_or_path>

# List ticket's artifacts
vibey task artifacts <ticket_id>

# List ticket's commits
vibey task commits <ticket_id>

# Link commit to ticket manually
vibey task link-commit <ticket_id> <commit_sha>

# Show artifact history
vibey artifact history <artifact_id>

# Validate triangle consistency
vibey validate triangle <ticket_id>
```

### Acceptance Criteria
- [ ] All commands implemented
- [ ] Consistent output formatting
- [ ] Error handling for invalid IDs

---

## Task 8: Integrate Context into Three-Phase Model
**ID:** `01KCMNEG4CXW4NK7W55VDMBXXM`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Plan/Runtime/Post-Mortem contexts should reference artifacts, not raw files.

### Implementation

```python
class PlanContext(BaseModel):
    goals: List[str] = []
    approach: str = ""
    constraints: List[str] = []
    success_criteria: List[str] = []

    # Reference artifacts, not files
    artifact_refs: List[ArtifactRef] = Field(default_factory=list)

    created_at: datetime
    approved: bool = False


class ArtifactRef(BaseModel):
    artifact_id: str
    purpose: str
    tokens_estimate: Optional[int] = None
```

When plan context is set, automatically create `TicketArtifactAssociation` records with `source=plan_reference`.

### Acceptance Criteria
- [ ] Context models reference artifacts
- [ ] Auto-create associations from plan references
- [ ] Token estimates preserved

---

## Task 9: Post-Mortem Generation from Relationships
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Post-mortems should be generated from relationship data.

### Implementation

```python
def generate_post_mortem(ticket_id: str) -> PostMortemContext:
    # Get all commits linked to ticket
    commit_links = query_commit_links(ticket_id=ticket_id)

    # Get all artifacts changed by those commits
    artifacts_changed = set()
    for link in commit_links:
        changes = query_artifact_changes(commit_sha=link.commit_sha)
        artifacts_changed.update(c.artifact_id for c in changes)

    # Get artifact details
    artifacts = [get_artifact(aid) for aid in artifacts_changed]
    files_changed = []
    for a in artifacts:
        files_changed.extend(a.paths)

    return PostMortemContext(
        summary=f"Completed with {len(commit_links)} commits, {len(files_changed)} files changed",
        files_changed=files_changed,
        commit_count=len(commit_links),
        # ... other fields
    )
```

### Acceptance Criteria
- [ ] Post-mortem uses relationship data
- [ ] Accurate file change tracking
- [ ] Commit count included

---

## Task 10: Documentation and Testing
**Priority:** Medium | **Complexity:** Medium | **Type:** Documentation

### Deliverables
- [ ] Update CLI_REFERENCE.md with new commands
- [ ] Update MCP_REFERENCE.md with new tools
- [ ] Create RELATIONSHIP_MODEL.md architecture doc
- [ ] Unit tests for relationship models
- [ ] Integration tests for pre-commit hook
- [ ] Integration tests for triangle validation

---

## Sprint Completion Checklist

- [ ] Three relationship entity models implemented
- [ ] SQLite schema extended with tables and views
- [ ] Unified pre-commit hook with triangle validation
- [ ] `Task:` and `Completes:` parsing in GitCommit
- [ ] Commit message template system
- [ ] MCP tools for relationship management
- [ ] CLI commands for relationship management
- [ ] Context models reference artifacts
- [ ] Post-mortem generation from relationships
- [ ] Documentation updated
- [ ] Tests passing
