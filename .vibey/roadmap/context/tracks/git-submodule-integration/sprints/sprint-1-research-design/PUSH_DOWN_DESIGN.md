# Requirements Push-Down Mechanism Design

**Task:** 01KCMP2MN4SVE70FB55TXAV2EH
**Date:** 2025-12-19
**Status:** Complete

---

## Overview

This document defines how requirements push down from a parent project roadmap to submodule roadmaps. The design integrates with the Unified Ticket Architecture's Triangle Model.

---

## 1. Core Concept

**Push-down** = Parent roadmap creates a requirement that a submodule must fulfill.

```
PARENT ROADMAP                           SUBMODULE ROADMAP
┌──────────────────────┐                ┌──────────────────────┐
│ Ticket: AUTH-001     │                │ Ticket: AUTH-001-SUB │
│ "Add OAuth support"  │──────────────▶│ "Implement OAuth"    │
│ Type: Requirement    │  CrossRepo    │ Type: Implementation │
│ Owner: Parent        │  Requirement  │ Owner: Submodule     │
└──────────────────────┘                └──────────────────────┘
```

---

## 2. CrossRepoRequirement Entity

**Extends the Triangle Model with cross-repo relationships:**

```python
@dataclass
class CrossRepoRequirement:
    """Links a parent ticket to a derived submodule ticket."""
    id: str                              # ULID

    # Source (parent)
    source_roadmap_id: str               # Parent roadmap ID
    source_ticket_id: str                # Parent ticket that created requirement

    # Target (submodule)
    target_roadmap_id: str               # Submodule roadmap ID
    target_ticket_id: Optional[str]      # Derived ticket in submodule (may not exist yet)
    target_submodule_path: str           # Path to submodule (for routing)

    # Requirement definition
    requirement_type: RequirementType
    requirement_spec: RequirementSpec    # What is being required
    acceptance_criteria: List[str]       # How to verify completion

    # Ownership
    ownership_model: OwnershipModel
    push_mode: PushMode

    # Lifecycle
    created_at: datetime
    pushed_at: Optional[datetime]        # When requirement was sent to submodule
    acknowledged_at: Optional[datetime]  # When submodule accepted
    fulfilled_at: Optional[datetime]     # When submodule completed

    # Status
    status: RequirementStatus


class RequirementType(Enum):
    FEATURE = "feature"           # Implement new capability
    BUGFIX = "bugfix"             # Fix specific issue
    UPGRADE = "upgrade"           # Update dependency/version
    COMPLIANCE = "compliance"     # Meet standard/regulation
    INTERFACE = "interface"       # Implement specific API


class OwnershipModel(Enum):
    PARENT_OWNED = "parent_owned"       # Parent defines, submodule implements
    SUBMODULE_OWNED = "submodule_owned" # Submodule owns, parent just tracks
    SHARED = "shared"                   # Both can modify


class PushMode(Enum):
    AUTOMATIC = "automatic"       # Create ticket in submodule automatically
    NOTIFICATION = "notification" # Notify submodule, manual ticket creation
    MANUAL = "manual"             # No automatic action


class RequirementStatus(Enum):
    DRAFT = "draft"               # Not yet pushed
    PUSHED = "pushed"             # Sent to submodule
    ACKNOWLEDGED = "acknowledged" # Submodule accepted
    IN_PROGRESS = "in_progress"   # Work started
    FULFILLED = "fulfilled"       # Requirement met
    REJECTED = "rejected"         # Submodule rejected
    CANCELLED = "cancelled"       # Parent cancelled
```

---

## 3. RequirementSpec: What Gets Pushed

```python
@dataclass
class RequirementSpec:
    """Specification of what the requirement entails."""

    # Basic info
    title: str
    description: str

    # Artifact requirements (integrates with Triangle Model)
    required_artifacts: List[ArtifactRequirement]

    # Interface requirements
    interface_contracts: List[InterfaceContract]

    # Timeline (advisory)
    suggested_priority: Optional[str]
    suggested_deadline: Optional[datetime]

    # Context for submodule
    parent_context: str                  # Why this is needed
    related_parent_tickets: List[str]    # Other relevant parent tickets


@dataclass
class ArtifactRequirement:
    """Specifies an artifact that must be created/modified."""
    artifact_type: str                   # "source_file", "test", "doc", etc.
    path_pattern: Optional[str]          # Expected path pattern
    description: str                     # What the artifact should contain


@dataclass
class InterfaceContract:
    """Specifies an interface/API that must be implemented."""
    interface_type: str                  # "function", "class", "endpoint", etc.
    signature: str                       # Expected signature/schema
    description: str
```

---

## 4. Push-Down Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PUSH-DOWN FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 1: Parent Creates Requirement                                  │
│    • User runs: vibey submodule push-requirement <ticket> <submodule>│
│    • Creates CrossRepoRequirement with status=DRAFT                  │
│    • Stores in parent's .vibey/roadmap/cross_repo_requirements/      │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 2: Validate & Push                                             │
│    • Verify submodule exists and has Vibey roadmap                   │
│    • Serialize RequirementSpec to portable format                    │
│    • Write to submodule's .vibey/roadmap/incoming_requirements/      │
│    • Update status to PUSHED                                         │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 3: Submodule Receives                                          │
│    • Submodule user runs: vibey submodule incoming                   │
│    • Shows pending requirements from parent                          │
│    • User decides: accept, reject, or defer                          │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 4: Submodule Acknowledges                                      │
│    • If accepted: vibey submodule accept-requirement <req-id>        │
│    • Creates derived ticket in submodule roadmap                     │
│    • Links via target_ticket_id in CrossRepoRequirement              │
│    • Updates status to ACKNOWLEDGED                                  │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 5: Work & Completion                                           │
│    • Submodule works on derived ticket                               │
│    • Uses standard Vibey workflow (commits, artifacts, etc.)         │
│    • When complete: status propagates via pull-up mechanism          │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 6: Parent Verification                                         │
│    • Parent's criterion system checks fulfillment                    │
│    • May use CrossRepoCriterion target type                          │
│    • Updates CrossRepoRequirement status to FULFILLED                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Storage Structure

### 5.1 Parent Side

```
.vibey/roadmap/
├── cross_repo_requirements/
│   ├── 01KCX_REQ_001.yaml      # CrossRepoRequirement entity
│   └── 01KCX_REQ_002.yaml
```

**Example 01KCX_REQ_001.yaml:**
```yaml
cross_repo_requirement:
  id: 01KCX_REQ_001
  source_roadmap_id: parent-app-v2
  source_ticket_id: 01TASK_AUTH_OAUTH

  target_roadmap_id: auth-lib-v1
  target_ticket_id: 01TASK_IMPL_OAUTH  # Set after acknowledgment
  target_submodule_path: libs/auth

  requirement_type: feature
  requirement_spec:
    title: Implement OAuth 2.0 support
    description: Add OAuth 2.0 authorization code flow
    required_artifacts:
      - artifact_type: source_file
        path_pattern: "src/oauth/*.py"
        description: OAuth implementation
      - artifact_type: test
        path_pattern: "tests/test_oauth*.py"
        description: OAuth test coverage
    interface_contracts:
      - interface_type: function
        signature: "def oauth_authorize(client_id: str, scope: List[str]) -> AuthUrl"
        description: Initiate OAuth flow
    parent_context: "Main app needs OAuth for enterprise customers"

  ownership_model: parent_owned
  push_mode: automatic

  created_at: '2025-12-19T19:00:00+00:00'
  pushed_at: '2025-12-19T19:01:00+00:00'
  acknowledged_at: '2025-12-19T19:10:00+00:00'
  fulfilled_at: null

  status: in_progress
```

### 5.2 Submodule Side

```
.vibey/roadmap/
├── incoming_requirements/
│   └── from-parent-app-v2/
│       └── 01KCX_REQ_001.yaml  # Received requirement
```

---

## 6. Triangle Model Integration

### 6.1 Artifact Association Propagation

When a requirement specifies `required_artifacts`, and the submodule creates them:

```
Parent:                              Submodule:
┌──────────────────┐                ┌──────────────────┐
│ Ticket: AUTH-001 │                │ Ticket: IMPL-001 │
│ (Requirement)    │                │ (Implementation) │
└────────┬─────────┘                └────────┬─────────┘
         │                                   │
         │ CrossRepoRequirement              │ TicketArtifactAssociation
         │                                   ▼
         │                          ┌──────────────────┐
         │                          │ Artifact: oauth.py│
         └─────────────────────────▶│ (in submodule)   │
           CrossRepoArtifactRef     └──────────────────┘
```

### 6.2 CrossRepoArtifactRef Entity

```python
@dataclass
class CrossRepoArtifactRef:
    """References an artifact in another repo."""
    id: str
    source_roadmap_id: str           # Roadmap making the reference
    source_ticket_id: str            # Ticket with the requirement
    target_roadmap_id: str           # Submodule roadmap
    target_artifact_id: str          # Artifact in submodule
    reference_type: str              # "required" | "produced" | "monitors"
    created_at: datetime
```

---

## 7. API Design

### 7.1 CLI Commands

```bash
# Create and push requirement
vibey submodule push-requirement <parent-ticket> <submodule-path> \
  --title "Implement OAuth" \
  --description "..." \
  --mode automatic

# List requirements pushed to submodules
vibey submodule requirements --direction outgoing

# In submodule: list incoming requirements
vibey submodule requirements --direction incoming

# In submodule: accept requirement
vibey submodule accept-requirement <requirement-id>

# In submodule: reject requirement
vibey submodule reject-requirement <requirement-id> --reason "..."

# Check requirement status
vibey submodule requirement-status <requirement-id>
```

### 7.2 MCP Tools

```python
@mcp_tool
def submodule_push_requirement(
    parent_ticket_id: str,
    submodule_path: str,
    requirement_spec: RequirementSpec,
    push_mode: str = "automatic"
) -> CrossRepoRequirement:
    """Push a requirement to a submodule."""

@mcp_tool
def submodule_requirements(
    direction: str,  # "incoming" | "outgoing"
    status_filter: Optional[str] = None
) -> List[CrossRepoRequirement]:
    """List cross-repo requirements."""

@mcp_tool
def submodule_accept_requirement(
    requirement_id: str,
    create_ticket: bool = True
) -> AcceptResult:
    """Accept an incoming requirement."""
```

---

## 8. Criterion Integration

### 8.1 CrossRepoCriterion Target

Extend the criterion system to support cross-repo targets:

```python
class CrossRepoCriterionTarget(CriterionTarget):
    """Target that checks status in another repo."""
    target_type: str = "cross_repo"

    # What to check
    submodule_path: str
    requirement_id: str

    # Acceptance criteria
    required_status: RequirementStatus = RequirementStatus.FULFILLED

    def evaluate(self, context: EvaluationContext) -> CriterionResult:
        requirement = context.get_cross_repo_requirement(self.requirement_id)
        return CriterionResult(
            met=requirement.status == self.required_status,
            message=f"Requirement {self.requirement_id}: {requirement.status}"
        )
```

### 8.2 Usage in Parent Ticket

```yaml
# Parent ticket with cross-repo criterion
task:
  id: 01TASK_AUTH_OAUTH
  title: Add OAuth support to main app
  criteria:
    - id: crit-submodule-oauth
      name: Auth lib implements OAuth
      target:
        target_type: cross_repo
        submodule_path: libs/auth
        requirement_id: 01KCX_REQ_001
        required_status: fulfilled
```

---

## 9. Conflict Resolution

### 9.1 What Happens When...

| Scenario | Resolution |
|----------|------------|
| Submodule rejects requirement | Parent notified, must revise or cancel |
| Submodule modifies spec | Changes tracked, parent can approve/reject |
| Parent cancels after push | Submodule notified, can keep or remove ticket |
| Submodule fulfills differently | Parent criterion evaluates actual result |
| Version mismatch | Requirement includes parent commit SHA for reference |

### 9.2 Conflict States

```python
class RequirementConflict(BaseModel):
    requirement_id: str
    conflict_type: ConflictType
    parent_state: dict
    submodule_state: dict
    detected_at: datetime
    resolved_at: Optional[datetime]
    resolution: Optional[str]

class ConflictType(Enum):
    SPEC_MODIFIED = "spec_modified"
    STATUS_MISMATCH = "status_mismatch"
    UNACKNOWLEDGED_CHANGE = "unacknowledged_change"
```

---

## 10. Implementation Guidance

### 10.1 File Locations

| Component | Location |
|-----------|----------|
| CrossRepoRequirement model | `vibey/roadmap/models/cross_repo.py` |
| RequirementPusher class | `vibey/operations/submodule/push.py` |
| CLI commands | `vibey/cli/submodule.py` |
| MCP tools | `vibey/mcp/tools/submodule.py` |
| CrossRepoCriterion | `vibey/roadmap/criteria/cross_repo.py` |

### 10.2 Serialization

- YAML for cross_repo_requirements/ storage
- SQLite table for queryability:

```sql
CREATE TABLE cross_repo_requirements (
    id TEXT PRIMARY KEY,
    source_roadmap_id TEXT NOT NULL,
    source_ticket_id TEXT NOT NULL,
    target_roadmap_id TEXT,
    target_ticket_id TEXT,
    target_submodule_path TEXT NOT NULL,
    requirement_type TEXT NOT NULL,
    requirement_spec_json TEXT NOT NULL,
    ownership_model TEXT NOT NULL,
    push_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    pushed_at TEXT,
    acknowledged_at TEXT,
    fulfilled_at TEXT
);
```

---

## Next Steps

1. → Task 4: Design pull-up mechanism (how fulfillment propagates back)
2. → Task 5: Design cross-repo dependencies (task-to-task across repos)
3. → Task 6: Consolidate into design document with implementation specs
