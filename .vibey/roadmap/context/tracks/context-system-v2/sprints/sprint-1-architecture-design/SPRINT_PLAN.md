# Sprint 1: Context Architecture Design

## Overview
- **Track:** Context System V2
- **Sprint ID:** 01KCMTY4ACHZQ53CH90J7ZSAAV
- **Tasks:** 3
- **Focus:** Design comprehensive context management architecture with git integration
- **Prerequisites:** Sprint 0 design decisions approved

## Design Decisions (from Sprint 0)

Reference: `sprint-0-planning-design-review/DESIGN_DECISIONS.md`

Key decisions incorporated:
- Hybrid YAML + Markdown approach (YAML indexes markdown artifacts)
- Storage: `context/plans/`, `context/runtime/`, `context/post-mortems/`
- Git linking: file overlap + message ref + manual (no timestamp)
- Pre-commit hook with bidirectional validation
- Configurable enforcement levels
- Commit message template

## Success Criteria
- [ ] Context architecture document complete
- [ ] Hybrid YAML + Markdown structure defined
- [ ] Git linking design with pre-commit hook specified
- [ ] Directory structure ready for implementation

---

## Task 1: Create CONTEXT_ARCHITECTURE.md
**ID:** `01KCMGX0XQSJDP4XBC9G34T1K7`
**Priority:** High | **Complexity:** Complex | **Type:** Documentation

### Problem
No central design document exists for context engineering system.

### Implementation Steps

1. Create architecture document incorporating Sprint 0 decisions:
   ```markdown
   # Context System Architecture

   ## Overview
   Purpose: Enable AI assistants to maintain contextual understanding
   across sessions and task boundaries.

   ## Core Concepts
   - Plan Context: Pre-work preparation and design
   - Runtime Context: Active session state
   - Post-Mortem Context: Completed work summaries

   ## Storage Model
   - YAML for structured metadata (always loaded, small)
   - Markdown for lengthy artifacts (loaded on demand)
   - SQLite for queries
   - Git for version control and commit linking

   ## Hybrid YAML + Markdown
   YAML files index markdown artifacts:
   - AI sees what exists and purpose
   - AI decides what to load based on need
   - Large context preserved without forced token cost
   ```

2. Document the three-phase lifecycle:
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │                     CONTEXT LIFECYCLE                       │
   └─────────────────────────────────────────────────────────────┘

   PLANNING PHASE           EXECUTION PHASE           COMPLETION
   ─────────────────────────────────────────────────────────────
   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
   │  PLAN CONTEXT   │ ──▶ │ RUNTIME CONTEXT │ ──▶ │   POST-MORTEM   │
   │                 │     │                 │     │                 │
   │  • Goals        │     │  • Active files │     │  • Summary      │
   │  • Approach     │     │  • Decisions    │     │  • Files changed│
   │  • Artifacts[]  │     │  • Discoveries  │     │  • Lessons      │
   │  • Constraints  │     │  • Blockers     │     │  • Follow-ups   │
   └─────────────────┘     └─────────────────┘     └─────────────────┘
           │                       │                       │
           └───────────────────────┴───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    GIT COMMITS      │
                    │  (file + msg link)  │
                    └─────────────────────┘
   ```

3. Document storage structure:
   ```
   .vibey/roadmap/context/
   ├── plans/                    # Pre-work artifacts
   │   └── {ticket_id}/
   │       ├── plan.yaml         # Structured metadata
   │       ├── DESIGN_ANALYSIS.md
   │       └── IMPLEMENTATION_PLAN.md
   │
   ├── runtime/                  # Active session state
   │   └── {ticket_id}.yaml
   │
   └── post-mortems/             # Completion summaries
       └── {ticket_id}.yaml
   ```

4. Define API surface:
   ```python
   class ContextManager:
       def get_plan_context(self, ticket_id: str) -> PlanContext:
           """Get pre-work planning context for ticket."""

       def get_plan_artifacts(self, ticket_id: str) -> List[ArtifactRef]:
           """List available artifacts without loading content."""

       def load_artifact(self, ticket_id: str, filename: str) -> str:
           """Load specific artifact content on demand."""

       def get_runtime_context(self, ticket_id: str) -> RuntimeContext:
           """Get current execution context for ticket."""

       def save_post_mortem(self, ticket_id: str, summary: PostMortem) -> None:
           """Save completion summary for ticket."""
   ```

### Deliverables
- `docs/architecture/CONTEXT_ARCHITECTURE.md`
- Data flow diagrams
- API specifications
- Storage model documentation

### Acceptance Criteria
- [ ] Architecture document complete
- [ ] Hybrid YAML + Markdown model documented
- [ ] Three context phases specified
- [ ] API surface defined
- [ ] Storage paths documented

---

## Task 2: Design Git Integration with Pre-Commit Hook
**ID:** `01KCMMJK5AQ727JVKPCED8RXVT`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Need to design git commit linking that validates consistency between commit files, message refs, and task YAML.

### Design Principles (from Sprint 0)
1. **No timestamp-based linking** - Was source of parallel task ambiguity
2. **Three link signals**: file overlap, message reference, manual
3. **Bidirectional validation** - Neither YAML nor message assumed correct
4. **Files can belong to multiple tasks** - Real work isn't cleanly partitioned
5. **Configurable enforcement** - Different tolerance for friction

### Implementation Steps

1. Design commit link data model:
   ```python
   @dataclass
   class CommitLink:
       """Links git commit to ticket context."""

       sha: str
       message: str
       files: List[str]
       linked_at: datetime

       signals: CommitLinkSignals
       aggregate_confidence: float
       link_source: str  # 'pre_commit_hook' | 'reconciliation' | 'manual'

   @dataclass
   class CommitLinkSignals:
       file_overlap: FileOverlapSignal
       message_ref: MessageRefSignal
       manual: ManualSignal

   @dataclass
   class FileOverlapSignal:
       matched: bool
       files: List[str]  # Which files overlapped
       confidence: float

   @dataclass
   class MessageRefSignal:
       matched: bool
       task_ids: List[str]  # Task IDs found in message
       confidence: float

   @dataclass
   class ManualSignal:
       matched: bool
       linked_by: str  # User who linked
       confidence: float = 1.0
   ```

2. Design pre-commit hook flow:
   ```python
   def pre_commit_hook():
       """Validate commit against task tracking."""

       # 1. Get staged files and commit message
       staged_files = get_staged_files()
       message = get_commit_message()

       # 2. Parse task references from message
       task_refs = parse_task_refs(message)

       # 3. For each referenced task, check file consistency
       for task_id in task_refs:
           task_files = load_task_known_files(task_id)
           discrepancies = compare_files(staged_files, task_files)

           if discrepancies.files_not_in_yaml:
               # Files in commit but not tracked in task YAML
               handle_discrepancy(task_id, discrepancies, 'files_not_in_yaml')

       # 4. Check for files matching OTHER tasks (not referenced)
       for file in staged_files:
           other_tasks = find_tasks_tracking_file(file)
           if other_tasks and not any(t in task_refs for t in other_tasks):
               suggest_adding_task_ref(other_tasks)

       # 5. Check for files matching NO tasks
       untracked = find_untracked_files(staged_files)
       if untracked:
           flag_untracked_work(untracked)
   ```

3. Design resolution options:
   ```python
   class DiscrepancyResolution(Enum):
       UPDATE_YAML = "update_yaml"      # Add files to task tracking
       UPDATE_MESSAGE = "update_message" # Change task reference
       ADD_REFERENCE = "add_reference"   # Include additional task
       PROCEED = "proceed"               # Override, commit as-is
       CANCEL = "cancel"                 # Abort commit
   ```

4. Design configuration:
   ```yaml
   # .vibey/config/git_hooks.yaml
   pre_commit:
     enabled: true
     mode: prompt  # off | warn | prompt | strict

     on_mismatch:
       files_not_in_yaml: prompt    # warn | prompt | block
       yaml_files_not_in_commit: ignore  # Normal
       no_task_ref: warn            # warn | prompt | block

     template:
       auto_install: true
       path: .gitmessage
   ```

5. Design commit message template:
   ```
   # <type>(<scope>): <subject>
   #
   # Task: <TASK_ID or TASK_IDS>
   #
   # <body>
   #
   # ─────────────────────────────────────────────────────────
   # TYPE: feat|fix|docs|style|refactor|test|chore
   # TASK: vibey task ID(s), comma-separated for multiple
   #       Example: 01KCQ9YS0KE8WSYKZ21XG6WBQX
   #       Example: 01TASK_A, 01TASK_B
   # ─────────────────────────────────────────────────────────
   ```

### Deliverables
- `GIT_INTEGRATION_DESIGN.md` - Full design document
- Commit link data model
- Pre-commit hook specification
- Configuration schema
- Commit message template

### Acceptance Criteria
- [ ] Three link signals designed (file, message, manual)
- [ ] Pre-commit hook flow specified
- [ ] Bidirectional validation defined
- [ ] Resolution options documented
- [ ] Configuration schema complete
- [ ] Commit message template created

---

## Task 3: Define Context Directory Structure
**ID:** `01KCMMK1MSFBZAM880C9K3BWPB`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Need to define the context directory structure with subdirectories for plans, runtime, and post-mortems.

### Target State (from Sprint 0)
```
.vibey/roadmap/context/
├── plans/                    # Pre-work artifacts
│   └── {ticket_id}/
│       ├── plan.yaml         # Structured metadata + artifact index
│       ├── DESIGN_ANALYSIS.md
│       ├── IMPLEMENTATION_PLAN.md
│       └── API_DESIGN.md
│
├── runtime/                  # Active session state
│   └── {ticket_id}.yaml
│
└── post-mortems/             # Completion summaries
    └── {ticket_id}.yaml
```

### Implementation Steps

1. Define plan context YAML schema:
   ```yaml
   # context/plans/{ticket_id}/plan.yaml
   plan_context:
     ticket_id: 01TASK123
     created_at: '2025-12-17T10:00:00Z'
     created_by: claude
     approved: false

     goals:
       - "Implement user authentication"
       - "Support JWT and session-based auth"

     approach: |
       Use existing auth library, add middleware pattern.

     constraints:
       - "Must be backwards compatible"
       - "No breaking changes to existing endpoints"

     success_criteria:
       - "All endpoints require authentication"
       - "Tests pass with both auth methods"

     known_files:
       - path: src/auth.py
         source: plan_reference
         added: '2025-12-17T10:00:00Z'
       - path: src/middleware.py
         source: plan_reference
         added: '2025-12-17T10:00:00Z'

     artifacts:
       - file: DESIGN_ANALYSIS.md
         purpose: "Deep dive on existing auth system"
         tokens_estimate: 4500
       - file: IMPLEMENTATION_PLAN.md
         purpose: "Step-by-step implementation approach"
         tokens_estimate: 3200
   ```

2. Define runtime context YAML schema:
   ```yaml
   # context/runtime/{ticket_id}.yaml
   runtime_context:
     ticket_id: 01TASK123
     session_id: sess_abc123
     started_at: '2025-12-17T11:00:00Z'
     last_updated: '2025-12-17T14:30:00Z'

     active_files:
       - src/auth.py
       - src/jwt_handler.py

     decisions:
       - decision: "Chose PyJWT over python-jose"
         rationale: "Better maintained, simpler API"
         timestamp: '2025-12-17T12:15:00Z'

     discoveries:
       - "Existing rate limiter conflicts with auth middleware order"

     blockers:
       - "Need DB migration for user tokens table"

     token_usage: 45000
   ```

3. Define post-mortem YAML schema:
   ```yaml
   # context/post-mortems/{ticket_id}.yaml
   post_mortem:
     ticket_id: 01TASK123
     completed_at: '2025-12-17T16:00:00Z'
     duration_hours: 5.0

     summary: |
       Implemented JWT authentication with decorator pattern.
       All endpoints now require auth, tests passing.

     files_changed:
       - src/auth.py
       - src/jwt_handler.py
       - src/middleware.py
       - tests/test_auth.py

     key_decisions:
       - "PyJWT for token handling"
       - "Decorator pattern for cleaner code"

     lessons_learned:
       - "Middleware order matters - auth must come before rate limiting"

     follow_up_items:
       - "Add refresh token support"
       - "Document auth flow in API docs"

     commit_links:
       - sha: abc1234
         message: "feat(auth): Add JWT validation"
         files: [src/auth.py, src/jwt_handler.py]
         signals:
           file_overlap: {matched: true, confidence: 1.0}
           message_ref: {matched: true, confidence: 1.0}
   ```

4. Define path utilities:
   ```python
   class ContextPaths:
       def __init__(self, roadmap_dir: Path):
           self.base = roadmap_dir / "context"

       def plans_dir(self, ticket_id: str = None) -> Path:
           path = self.base / "plans"
           if ticket_id:
               path = path / ticket_id
           return path

       def plan_yaml(self, ticket_id: str) -> Path:
           return self.plans_dir(ticket_id) / "plan.yaml"

       def plan_artifact(self, ticket_id: str, filename: str) -> Path:
           return self.plans_dir(ticket_id) / filename

       def runtime_yaml(self, ticket_id: str) -> Path:
           return self.base / "runtime" / f"{ticket_id}.yaml"

       def post_mortem_yaml(self, ticket_id: str) -> Path:
           return self.base / "post-mortems" / f"{ticket_id}.yaml"
   ```

### Deliverables
- Directory structure specification
- YAML schemas for all three context types
- Path utility design
- Migration notes for existing context/ content

### Acceptance Criteria
- [ ] Plans directory structure defined
- [ ] Runtime directory structure defined
- [ ] Post-mortems directory structure defined
- [ ] YAML schemas complete for all three types
- [ ] Path utilities designed
- [ ] Artifact indexing in plan.yaml specified

---

## Sprint Completion Checklist
- [ ] CONTEXT_ARCHITECTURE.md created
- [ ] Hybrid YAML + Markdown model documented
- [ ] Git integration with pre-commit hook designed
- [ ] Bidirectional validation specified
- [ ] Commit message template defined
- [ ] Directory structure with all three subdirs specified
- [ ] YAML schemas for plans, runtime, post-mortems complete
