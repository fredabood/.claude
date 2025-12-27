# Submodule Isolation and Push-Down Design Decisions

**Date:** 2025-12-27
**Status:** Decided
**Decision Makers:** Fred Abood, Claude

---

## Context

When integrating Vibey roadmaps across parent and submodule repositories, a critical architectural question arises: how do we ensure submodule repos remain fully independent while enabling parent repos to coordinate work across them?

### The Core Problem

```
Repo C (parent)
├── .vibey/roadmap/          ← C's roadmap
├── libs/
│   ├── repo-a/              ← submodule (has own .vibey/)
│   └── repo-b/              ← submodule (has own .vibey/)
```

**Scenario**: Developer clones Repo A directly, not knowing it's also a submodule of C. Repo A's Vibey instance must work 100% correctly without access to C.

---

## Part 1: Submodule Isolation Architecture

### Options Considered

#### Option 1: Cross-Repo References (Rejected)

Store parent requirements in submodule's `.vibey/incoming/` directory.

```
A/.vibey/
├── roadmap/           # Core roadmap
└── incoming/          # Requirements from parent C
    └── from-C/
        └── requirements/
```

**Pros:**
- Clear separation of local vs external requirements
- A can see what parents expect

**Cons:**
- A has knowledge of parent C
- Requires external reference resolution
- Graceful degradation needed when parent unavailable
- Violates independence principle

#### Option 2: Standalone Submodules (Selected)

Submodule A has zero knowledge of parent C. All cross-repo data lives in parent only.

```
A/.vibey/
└── roadmap/           # 100% standalone, no external refs

C/.vibey/
├── roadmap/           # C's tasks, with blocked_by pointing to A
└── config/
    └── submodules.yaml  # C knows about A
```

**Pros:**
- A is completely independent
- No incoming/outgoing directories needed
- No graceful degradation needed (nothing to degrade)
- Clean separation of concerns

**Cons:**
- Parent must manage all cross-repo metadata
- Coordination is parent's responsibility

### Decision: Option 2 - Standalone Submodules

**Rationale:** Submodule independence is paramount. A developer working on Repo A directly should have a fully functional Vibey instance with no concept of parent repos.

---

## Part 2: Pull-Up (Progress Aggregation)

### Design Decision

Pull-up is **parent-initiated**. Parent C reads submodule roadmaps directly.

```
C runs: vibey submodule aggregate

Flow:
1. C reads .vibey/config/submodules.yaml (list of submodules)
2. For each submodule path:
   - Read submodule's .vibey/roadmap.db or YAML
   - Compute progress metrics
   - Update C's aggregated view
3. A and B do nothing - they're passive data sources
```

**Key Points:**
- No `outgoing/` directory in submodules
- Submodules are read-only from parent's perspective during aggregation
- Parent stores aggregation results in its own config/cache

---

## Part 3: Push-Down (Requirement Communication)

### Options Considered

#### Option A: Direct Write (Selected)

Parent C creates tasks directly in submodule A's roadmap.

```bash
# In parent C:
vibey submodule push \
  --to libs/repo-a \
  --title "Implement auth-v2" \
  --mode linked
```

**What happens:**
1. Vibey creates task YAML in `libs/repo-a/.vibey/roadmap/tasks/`
2. Vibey creates git commit in submodule A
3. Vibey creates corresponding task in C (if linked mode)
4. C's task stores link to A's task ULID
5. User commits submodule ref update in C

**Resulting state:**
```yaml
# C's task (stored in C)
task:
  id: 01KYY456
  title: Integrate auth-v2 from lib-a
  blocked_by:
    - blocker_id: "libs/repo-a:01KZZ789"
      blocker_type: external
      resolved_to: 01KZZ789
      current_status: not_started

# A's task (stored in A, created by C)
task:
  id: 01KZZ789
  title: Implement auth-v2
  # No reference to C - A remains independent
```

**Pros:**
- Fully automated, single command
- Precise ULID-to-ULID linking
- Task exists in both roadmaps
- Progress tracking is automatic

**Cons:**
- Modifies A's git history
- Requires write access to submodule
- May surprise A's maintainers if not coordinated

**Best for:** Monorepo-style projects, teams that own both repos.

---

#### Option B: PR/Issue Creation (Considered, Not Selected)

Parent C opens a GitHub issue or PR in submodule A's repository.

```bash
vibey submodule request \
  --to libs/repo-a \
  --title "Implement auth-v2" \
  --platform github
```

**What happens:**
1. Vibey calls GitHub API to create issue in repo-a
2. Issue body includes structured metadata
3. C's task gets `blocked_by` with issue URL as identifier
4. A's team triages issue, creates their own task if they accept

**Resulting state:**
```yaml
# C's task
task:
  id: 01KYY456
  blocked_by:
    - blocker_id: "github:org/repo-a#42"
      blocker_type: external
      current_status: open
```

**Pros:**
- Respects A's workflow and ownership
- Creates audit trail in A's issue tracker
- Works for repos you don't own
- Natural for open-source collaboration

**Cons:**
- Requires GitHub/GitLab API integration
- A must manually create Vibey task from issue
- Status sync requires polling external API
- Adds external service dependency

**Best for:** Cross-team or open-source projects.

---

#### Option C: External Dependency Tracking Only (Considered, Not Selected)

Parent C tracks what it needs from A, but doesn't push anything.

```bash
vibey roadmap create task \
  --title "Integrate auth-v2 from lib-a" \
  --blocked-by "libs/repo-a:auth-v2" \
  --blocker-type external
```

**What happens:**
1. C creates its own task with external dependency
2. Dependency uses human-readable identifier, not ULID
3. C's team communicates with A's team out-of-band
4. A's team creates their own task (or doesn't)
5. C can poll A's roadmap to check if matching work exists

**Resulting state:**
```yaml
# C's task
task:
  id: 01KYY456
  blocked_by:
    - blocker_id: "libs/repo-a:auth-v2"
      blocker_type: external
      current_status: unknown
```

**Pros:**
- A stays completely independent
- No external API dependencies
- Clean separation of concerns
- Works offline

**Cons:**
- Requires manual coordination
- No guaranteed task exists in A
- Identifier matching is fuzzy (not ULID)
- C can't force A to do anything

**Best for:** Loosely coupled projects, maximum independence.

---

### Hybrid Approach: Configurable Modes

The selected design supports all three patterns via configuration:

| Mode | Parent Task | Submodule Task | Link Storage |
|------|-------------|----------------|--------------|
| `parent_only` | Created | None | N/A |
| `submodule_only` | None | Created | N/A |
| `linked` | Created | Created | Parent stores ULID mapping |

**Configuration:**
```yaml
# C's .vibey/config/submodules.yaml
submodules:
  - path: libs/repo-a
    default_push_mode: linked

  - path: libs/repo-b
    default_push_mode: parent_only
```

**Per-requirement override:**
```bash
vibey submodule push \
  --to libs/repo-a \
  --title "Implement auth-v2" \
  --mode submodule_only  # Override default
```

### Decision: Direct Write with Linked Mode Default

**Selected:** Option A (Direct Write) with hybrid mode support.

**Default mode:** `linked` - Create task in both parent and submodule, with ULID mapping stored in parent.

**Rationale:**
- Provides full automation for the common case
- ULID-to-ULID linking eliminates fuzzy matching
- Configurable modes support different team structures
- Link stored only in parent preserves submodule independence

---

## Part 4: Submodule Registry

### Options Considered

#### Option A: Mirror .gitmodules Automatically

Parse `.gitmodules` file, auto-discover submodules with Vibey roadmaps.

**Pros:** Zero configuration
**Cons:** Can't customize or exclude submodules

#### Option B: Explicit Configuration Only

User manually configures all submodules in `.vibey/config/submodules.yaml`.

**Pros:** Full control
**Cons:** Manual setup required

#### Option C: Auto-Discover with Override (Selected)

Auto-discover from `.gitmodules`, allow explicit override.

```bash
vibey submodule discover
# Finds submodules, creates submodules.yaml
# User can edit to customize
```

**Pros:**
- Convenience of auto-discovery
- Control via explicit configuration
- Best of both approaches

### Decision: Option C - Auto-Discover with Override

---

## Part 5: Identifier Namespace

### Question

When C references a dependency in A, where does the identifier live?

### Decision: Parent's Namespace with ULID Resolution

- C defines human-readable identifiers for its needs
- When `linked` mode creates tasks in both repos, C stores A's task ULID
- ULID-to-ULID mapping eliminates namespace ambiguity

```yaml
# C's dependency
blocked_by:
  - blocker_id: "libs/repo-a:auth-v2"      # C's human-readable label
    blocker_type: external
    resolved_to: 01KZZ789                   # A's actual task ULID
```

---

## Summary of Decisions

| Decision | Selected Option | Rationale |
|----------|-----------------|-----------|
| Isolation model | Standalone submodules | Maximum independence for A |
| Pull-up | Parent-initiated | A is passive data source |
| Push-down | Direct write (Option A) | Full automation, precise linking |
| Push modes | Hybrid (linked default) | Flexibility for different needs |
| Registry | Auto-discover + override | Convenience with control |
| Identifier namespace | Parent with ULID resolution | Precision without ambiguity |

---

## Implementation Impact

With these decisions, the Sprint 2 isolation task scope simplifies to:

**Removed (not needed):**
- `.vibey/incoming/` directory structure
- `.vibey/outgoing/` directory structure
- Submodule detection in A (A doesn't know it's a submodule)
- External reference resolution in A
- Graceful degradation logic in A

**Added:**
- Submodule registry in C (`.vibey/config/submodules.yaml`)
- Direct write capability for push-down
- ULID mapping storage in C's `blocked_by` fields
- Aggregation logic in C to read submodule roadmaps
