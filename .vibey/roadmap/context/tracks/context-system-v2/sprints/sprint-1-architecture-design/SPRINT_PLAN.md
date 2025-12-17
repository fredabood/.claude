# Sprint 1: Context Architecture Design

## Overview
- **Track:** Context System V2
- **Sprint ID:** 01KCMTY4ACHZQ53CH90J7ZSAAV
- **Tasks:** 3
- **Focus:** Design comprehensive context management architecture with git integration

## Success Criteria
- [ ] Context architecture document complete
- [ ] Hybrid context management design approved
- [ ] Directory restructure plan ready for implementation

---

## Task 1: Create CONTEXT_ARCHITECTURE.md
**ID:** `01KCMGX0XQSJDP4XBC9G34T1K7`
**Priority:** High | **Complexity:** Complex | **Type:** Documentation

### Problem
No central design document exists for context engineering system.

### Implementation Steps
1. Create architecture document structure:
   ```markdown
   # Context System Architecture

   ## Overview
   Purpose: Enable AI assistants to maintain contextual understanding
   across sessions and task boundaries.

   ## Core Concepts
   - Plan Context: Pre-work preparation and design
   - Runtime Context: Active session state
   - Post-Mortem Context: Completed work summaries

   ## Data Flow
   [Diagram showing context flow through system]

   ## Persistence Model
   - YAML for human-readable artifacts
   - Git for version control and linking
   - SQLite for queries

   ## API Surface
   - CLI commands
   - MCP tools
   - Python API
   ```

2. Document data flow:
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │                     CONTEXT LIFECYCLE                       │
   └─────────────────────────────────────────────────────────────┘

   PLANNING PHASE                EXECUTION PHASE              COMPLETION
   ───────────────────────────────────────────────────────────────────────
   ┌─────────────┐             ┌─────────────┐             ┌─────────────┐
   │ plan_context│  ────────▶  │runtime_ctxt │  ────────▶  │ post_mortem │
   │             │             │             │             │             │
   │ - goals     │             │ - active    │             │ - summary   │
   │ - approach  │             │ - files     │             │ - files     │
   │ - refs      │             │ - decisions │             │ - lessons   │
   └─────────────┘             └─────────────┘             └─────────────┘
         ▲                           │                           │
         │                           │                           │
         └───────────────────────────┴───────────────────────────┘
                         Git commit linking
   ```

3. Define API specifications:
   ```python
   # Context API Surface

   class ContextManager:
       def get_plan_context(self, ticket_id: str) -> PlanContext:
           """Get pre-work planning context for ticket."""

       def get_runtime_context(self, ticket_id: str) -> RuntimeContext:
           """Get current execution context for ticket."""

       def save_post_mortem(self, ticket_id: str, summary: PostMortem) -> None:
           """Save completion summary for ticket."""

       def link_commit(self, ticket_id: str, commit_sha: str) -> None:
           """Link git commit to ticket context."""
   ```

4. Document persistence strategy:
   - Plan context: `.vibey/roadmap/context/plans/{ticket-slug}/`
   - Runtime context: `.vibey/context/sessions/{ticket_id}.json`
   - Post-mortems: `.vibey/roadmap/context/post-mortems/{ticket_id}.md`

### Deliverables
- `docs/architecture/CONTEXT_ARCHITECTURE.md`
- Data flow diagrams
- API specifications
- Persistence model documentation

### Acceptance Criteria
- [ ] Architecture document complete
- [ ] All three context types documented
- [ ] Git integration strategy defined
- [ ] API surface specified

---

## Task 2: Design Hybrid Context Management with Git Integration
**ID:** `01KCMMJK5AQ727JVKPCED8RXVT`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Need to design context management that integrates deeply with git, capturing three dimensions: plan, runtime, and post-mortem.

### Design Principles
1. **Context is ticket-centric**: Context belongs to tickets, not sessions
2. **Git is the linking mechanism**: Commits associate context with work
3. **Three phases**: Plan → Runtime → Post-mortem
4. **Automatic association**: Timestamp + file matching links context to tasks

### Implementation Steps
1. Design ticket context structure:
   ```python
   @dataclass
   class TicketContext:
       """Unified context for a ticket across all phases."""

       ticket_id: str

       # Phase 1: Planning (pre-work)
       plan: PlanContext = None  # What we intend to do

       # Phase 2: Runtime (during work)
       runtime: RuntimeContext = None  # What model has during work

       # Phase 3: Post-mortem (after work)
       post_mortem: PostMortemContext = None  # Summary of accomplishment

       # Git linking
       commits: List[CommitLink] = field(default_factory=list)
   ```

2. Design plan context:
   ```python
   @dataclass
   class PlanContext:
       """Pre-work planning context."""

       goals: List[str]  # What we're trying to accomplish
       approach: str  # How we plan to do it
       references: List[Reference]  # Relevant files/docs
       constraints: List[str]  # Limitations to consider
       success_criteria: List[str]  # How we'll know we're done

       # Metadata
       created_at: datetime
       created_by: str  # Agent or human
       approved: bool = False
   ```

3. Design runtime context:
   ```python
   @dataclass
   class RuntimeContext:
       """Active session context during work."""

       active_files: List[Path]  # Files currently being worked on
       decisions: List[Decision]  # Decisions made during work
       discoveries: List[str]  # Things learned during work
       blockers: List[str]  # Issues encountered
       progress_notes: List[str]  # Status updates

       # Session tracking
       session_id: str
       started_at: datetime
       last_updated: datetime
       token_usage: int
   ```

4. Design post-mortem context:
   ```python
   @dataclass
   class PostMortemContext:
       """Completion summary after work."""

       summary: str  # What was accomplished
       files_changed: List[FileChange]  # Files modified
       key_decisions: List[str]  # Important choices made
       lessons_learned: List[str]  # What to remember
       follow_up_items: List[str]  # Things for future work

       # Completion metadata
       completed_at: datetime
       duration_hours: float
       token_total: int
   ```

5. Design git integration:
   ```python
   @dataclass
   class CommitLink:
       """Links git commit to ticket context."""

       commit_sha: str
       timestamp: datetime
       files_changed: List[str]
       message: str
       linked_via: str  # 'timestamp_range' | 'file_match' | 'manual'

   def auto_link_commits(ticket: Ticket) -> List[CommitLink]:
       """
       Auto-link commits to ticket based on:
       1. Timestamp within task start/complete window
       2. File overlap with known ticket files
       """
       commits = []
       for commit in get_commits_in_range(ticket.started, ticket.completed):
           if files_overlap(commit.files, ticket.known_files):
               commits.append(CommitLink(
                   commit_sha=commit.sha,
                   timestamp=commit.timestamp,
                   files_changed=commit.files,
                   message=commit.message,
                   linked_via='timestamp_range+file_match'
               ))
       return commits
   ```

### Deliverables
- `CONTEXT_DESIGN.md` - Full design document
- Data model specifications
- Git integration design
- API design for context operations

### Acceptance Criteria
- [ ] Three-phase model designed
- [ ] Git integration specified
- [ ] Auto-linking algorithm defined
- [ ] API surface documented

---

## Task 3: Rename Context Directory to Plans, Add Post-Mortem Structure
**ID:** `01KCMMK1MSFBZAM880C9K3BWPB`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Current `context/` directory is functionally `plans/`. Need to restructure for clarity.

### Current State
```
.vibey/roadmap/context/
├── tracks/
│   └── {track-slug}/
│       └── sprints/
│           └── {sprint-slug}/
│               ├── SPRINT_PLAN.md
│               └── {artifact}.md
```

### Target State
```
.vibey/roadmap/
├── plans/                    # Pre-work artifacts (renamed from context/)
│   └── tracks/
│       └── {track-slug}/
│           └── sprints/
│               └── {sprint-slug}/
│                   ├── SPRINT_PLAN.md
│                   └── {design}.md
│
├── runtime/                  # Runtime context (new)
│   └── sessions/
│       └── {ticket_id}.json
│
└── post-mortems/             # Completion summaries (new)
    └── {ticket_id}.md
```

### Implementation Steps
1. Create migration plan:
   ```python
   # Migration steps:
   # 1. Rename .vibey/roadmap/context/ → .vibey/roadmap/plans/
   # 2. Update all code references
   # 3. Create empty runtime/ and post-mortems/ directories
   # 4. Update git to track rename
   ```

2. Identify code references to update:
   ```bash
   grep -rn "context/" vibey/
   grep -rn '"context"' vibey/
   grep -rn "context_dir\|context_path" vibey/
   ```

3. Create migration script:
   ```python
   # scripts/migrate_context_structure.py

   import os
   import shutil
   from pathlib import Path

   def migrate_context_to_plans(roadmap_dir: Path):
       """Migrate context/ to plans/ structure."""

       context_dir = roadmap_dir / "context"
       plans_dir = roadmap_dir / "plans"
       runtime_dir = roadmap_dir / "runtime" / "sessions"
       postmortems_dir = roadmap_dir / "post-mortems"

       # 1. Rename context/ to plans/
       if context_dir.exists():
           shutil.move(str(context_dir), str(plans_dir))
           print(f"Renamed {context_dir} → {plans_dir}")

       # 2. Create new directories
       runtime_dir.mkdir(parents=True, exist_ok=True)
       postmortems_dir.mkdir(parents=True, exist_ok=True)
       print(f"Created {runtime_dir}")
       print(f"Created {postmortems_dir}")

       # 3. Create .gitkeep files
       (runtime_dir / ".gitkeep").touch()
       (postmortems_dir / ".gitkeep").touch()

   if __name__ == "__main__":
       migrate_context_to_plans(Path(".vibey/roadmap"))
   ```

4. Update path constants:
   ```python
   # vibey/common/paths.py

   class RoadmapPaths:
       # OLD
       # def context_dir(self, ...) -> Path:
       #     return self.base / "context" / ...

       # NEW
       def plans_dir(self, track_slug: str = None, sprint_slug: str = None) -> Path:
           path = self.base / "plans"
           if track_slug:
               path = path / "tracks" / track_slug
           if sprint_slug:
               path = path / "sprints" / sprint_slug
           return path

       def runtime_session(self, ticket_id: str) -> Path:
           return self.base / "runtime" / "sessions" / f"{ticket_id}.json"

       def post_mortem(self, ticket_id: str) -> Path:
           return self.base / "post-mortems" / f"{ticket_id}.md"
   ```

5. Update all references:
   - `vibey/cli/commands.py`
   - `vibey/operations/roadmap/*.py`
   - `vibey/mcp/tools/*.py`
   - Tests

### Deliverables
- Migration script
- Updated path utilities
- Updated code references
- Git commit tracking rename

### Acceptance Criteria
- [ ] Directory renamed via git (preserves history)
- [ ] New directories created
- [ ] All code references updated
- [ ] Tests pass with new structure

---

## Sprint Completion Checklist
- [ ] CONTEXT_ARCHITECTURE.md created
- [ ] Hybrid context design document complete
- [ ] Three-phase model fully specified
- [ ] Git integration design approved
- [ ] Directory restructure planned
- [ ] Migration script ready
