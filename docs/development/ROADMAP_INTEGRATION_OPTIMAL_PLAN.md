# Roadmap Integration - Optimal Implementation Plan

**Track:** roadmap-integration
**Goal:** Replace legacy sprint-state system with roadmap system in /vibey commands
**Duration:** 3 weeks (2 sprints × 1.5 weeks)
**Priority:** 🔴 CRITICAL PATH
**Status:** Ready to Start

---

## Executive Summary

### The Situation

Vibey framework is **NOT deployed in production** yet. The codebase has:
- ✅ **Roadmap System** - Full-featured, tested, production-ready (`.vibey/`)
- ❌ **Legacy System** - Old sprint-state scripts that should be removed (`docs/sprints/*.yaml`)
- ⚠️ **Integration Gap** - `/vibey` commands still reference legacy scripts

### The Optimal Approach

**Since there are NO external users:**
1. ❌ **NO migration scripts needed** - Nothing to migrate
2. ❌ **NO backward compatibility** - No existing deployments
3. ❌ **NO deprecation period** - Just delete legacy code
4. ✅ **Clean replacement** - Wire roadmap directly into /vibey commands
5. ✅ **Remove legacy entirely** - Delete all sprint-state scripts

### New Timeline

**2 Sprints (3 weeks total):**
1. **Sprint 1:** Direct Integration (1.5 weeks) - Wire roadmap into /vibey commands
2. **Sprint 2:** Polish & Launch (1.5 weeks) - Testing, docs, cleanup

**Effort Reduction:** 126 hours → **60 hours** (52% reduction)

---

## What We're Removing from Original Plan

### ❌ Eliminated Complexity

**Sprint 3 (entire sprint deleted):**
- ❌ Migration script (12 hours saved)
- ❌ Migration command (4 hours saved)
- ❌ Deprecation warnings (6 hours saved)
- ❌ Backward compatibility (8 hours saved)
- ❌ Legacy documentation (8 hours saved)

**Throughout all sprints:**
- ❌ NO dual-system support
- ❌ NO auto-detection logic
- ❌ NO migration prompts
- ❌ NO "graceful transition"

### ✅ What We're Keeping

**Core integration work:**
- ✅ Update /vibey deployment → roadmap init
- ✅ Update /vibey plan → roadmap sprint creation
- ✅ Update /vibey code → roadmap progress tracking
- ✅ Extend Vibey Manager → roadmap commands
- ✅ Documentation updates

---

## Architecture Design (Simplified)

### Clean Data Flow

```
User: /vibey deployment
    ↓
Initialize Framework
    ├── Copy framework files → .claude/
    └── Initialize roadmap → .vibey/
        ├── roadmap.yaml
        ├── tracks/main.yaml
        └── (sprints/ and tasks/ created on demand)
    ↓
Done


User: /vibey plan
    ↓
Sprint Planning Dialog
    ↓
Create Roadmap Sprint
    ├── .vibey/sprints/sprint-N.yaml
    ├── .vibey/tasks/sprint-N-tasks.yaml
    └── Update .vibey/tracks/main.yaml
    ↓
Update CLAUDE.md marker
    ↓
Done


User: /vibey code
    ↓
Load Sprint from Roadmap
    └── roadmap-query.py show sprint-N
    ↓
User Actions
    ├── Start task → roadmap-update.py --start-task
    ├── Complete task → roadmap-update.py --complete-task
    └── Complete sprint → roadmap-update.py --complete-sprint
    ↓
Done
```

### File Structure (Clean)

```
project/
├── .claude/                          # Framework deployment
│   ├── CLAUDE.md
│   ├── project-config.yaml
│   ├── commands/
│   ├── agents/
│   └── scripts/
│       ├── roadmap                   # Main CLI (already exists)
│       ├── roadmap-*.py              # Roadmap scripts (already exist)
│       ├── generate-config.py        # Keep
│       ├── render-template.py        # Keep
│       └── update-sprint-marker.py   # Keep (updates CLAUDE.md)
│
└── .vibey/                           # Roadmap system (authoritative)
    ├── roadmap.yaml
    ├── tracks/
    │   └── main.yaml
    ├── sprints/
    │   ├── sprint-1.yaml
    │   └── sprint-2.yaml
    └── tasks/
        ├── sprint-1-tasks.yaml
        └── sprint-2-tasks.yaml
```

**NO `docs/sprints/*.yaml` state files - DELETED**

### Scripts to Delete

**Remove these entirely (no deprecation):**
- ❌ `create-sprint-state.py` (304 lines)
- ❌ `update-sprint-state.py` (526 lines)
- ❌ `query-sprint-state.py` (504 lines)
- ❌ `update-sprint-marker.py` can be SIMPLIFIED (just update CLAUDE.md, don't manage state)

**Total deletion:** ~1,334 lines of unnecessary code

---

## Sprint 1: Direct Integration (1.5 weeks, 32 hours)

**Goal:** Wire roadmap system directly into /vibey commands

### Task 1.1: Update /vibey Deployment (4 hours)

**File:** `framework/commands/vibey.md`

**Changes:**

1. **Add roadmap initialization (Line ~1111):**
```bash
# Initialize roadmap system
echo "📊 Initializing roadmap system..."
python3 .claude/scripts/roadmap init \
  --project-name "${PROJECT_NAME}" \
  --version "0.1.0"

echo "✓ Roadmap initialized (.vibey/)"
```

2. **Remove legacy directory creation:**
```bash
# DELETE THIS:
mkdir -p docs/sprints
```

**Testing:**
- [ ] Fresh deployment creates `.vibey/`
- [ ] NO `docs/sprints/` directory created
- [ ] Roadmap initialized with project name

---

### Task 1.2: Update /vibey plan Command (8 hours)

**File:** `framework/commands/vibey-plan.md`

**Changes:**

**Replace Lines 201-234 entirely:**

**OLD (DELETE):**
```bash
# Step 8: Create Sprint State File
python3 .claude/scripts/create-sprint-state.py \
  --plan-file "docs/sprints/sprint-$SPRINT_NUMBER-plan.md" \
  --output "docs/sprints/sprint-$SPRINT_NUMBER-state.yaml"

# Step 9: Update Sprint Marker
python3 .claude/scripts/update-sprint-marker.py \
  --sprint-number ${SPRINT_NUMBER} \
  --sprint-name "${SPRINT_NAME}"
```

**NEW (CLEAN):**
```bash
# Step 8: Create roadmap sprint
echo "📊 Creating sprint in roadmap..."

# Parse plan markdown and create sprint
python3 .claude/scripts/roadmap plan create \
  --track-id "main" \
  --sprint-id "sprint-${SPRINT_NUMBER}" \
  --name "${SPRINT_NAME}" \
  --goal "${SPRINT_GOAL}" \
  --from-plan "sprint-${SPRINT_NUMBER}-plan.md"

echo "✓ Sprint sprint-${SPRINT_NUMBER} created"
echo "✓ Tasks created from plan"
echo "✓ Dependencies detected"

# Step 9: Update CLAUDE.md sprint marker
python3 .claude/scripts/roadmap marker update \
  --sprint-id "sprint-${SPRINT_NUMBER}"

echo ""
echo "✅ Ready to execute sprint"
echo "   Start: /vibey code"
```

**New roadmap command needed:**
```bash
# roadmap plan create - Parse plan markdown, create sprint + tasks
# Already has most logic, just needs:
# - Parse markdown for phases/tasks
# - Create sprint YAML
# - Create tasks YAML
# - Auto-detect dependencies
# - Return summary
```

**Testing:**
- [ ] Sprint created in `.vibey/sprints/`
- [ ] Tasks extracted from plan
- [ ] Dependencies auto-detected
- [ ] CLAUDE.md updated
- [ ] NO `docs/sprints/*-state.yaml` created

---

### Task 1.3: Update /vibey code Dashboard (8 hours)

**File:** `framework/commands/vibey-code.md`

**Changes:**

**Line 21 - Change state variable:**
```bash
# OLD:
SPRINT_STATE="docs/sprints/sprint-${SPRINT_NUMBER}-state.yaml"

# NEW:
SPRINT_ID="sprint-${SPRINT_NUMBER}"
```

**Lines 54-80 - Replace dashboard queries:**
```bash
# OLD (DELETE ALL query-sprint-state.py calls):
python3 .claude/scripts/query-sprint-state.py --state "$SPRINT_STATE" dashboard

# NEW (CLEAN):
python3 .claude/scripts/roadmap show ${SPRINT_ID} --format rich
```

**Output should show:**
```
Sprint: sprint-1 (in_progress)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: ████████░░░░░░░░ 45% (5/11 tasks)

Active Tasks (2):
  • sprint-1-task-003 - Implement auth middleware [web-developer]
  • sprint-1-task-007 - Write API tests [test-engineer]

Completed (5):
  ✓ sprint-1-task-001 - Design database schema
  ✓ sprint-1-task-002 - Set up project structure
  ...

Quality Gates:
  ✓ Security Audit (passed, 92/85)
  → Performance Testing (running)
  ○ Documentation Review (not run)

Next: Continue with active tasks or mark tasks complete
```

**Testing:**
- [ ] Dashboard displays from roadmap
- [ ] Shows progress, tasks, quality gates
- [ ] NO state file references

---

### Task 1.4: Update /vibey code Progress Tracking (10 hours)

**File:** `framework/commands/vibey-code.md`

**Changes:**

Replace ALL `update-sprint-state.py` calls with `roadmap` commands:

**Start task (NEW):**
```bash
# User selects task from list
SELECTED_TASK="sprint-1-task-003"

# Start task
python3 .claude/scripts/roadmap start task ${SELECTED_TASK}
```

**Complete task:**
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" update-task \
  --phase "$PHASE" --task "$TASK" --completed

# NEW:
python3 .claude/scripts/roadmap complete task ${TASK_ID}
```

**Update quality gate:**
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" quality-gate \
  --gate "$GATE" --status passed --score 92

# NEW:
python3 .claude/scripts/roadmap gate update \
  --sprint-id ${SPRINT_ID} \
  --gate "${GATE_NAME}" \
  --status passed \
  --score 92
```

**Pause/Resume sprint:**
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" pause-sprint

# NEW:
python3 .claude/scripts/roadmap pause sprint ${SPRINT_ID}
```

**Complete sprint:**
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" complete-sprint

# NEW:
python3 .claude/scripts/roadmap complete sprint ${SPRINT_ID}
```

**Testing:**
- [ ] Task start/complete works
- [ ] Quality gates update
- [ ] Sprint pause/resume works
- [ ] Sprint completion triggers version bump
- [ ] All activity logged

---

### Task 1.5: Extend Vibey Manager (2 hours)

**File:** `framework/agents/core/vibey-manager.md`

**Changes:**

**Add roadmap section (Line ~320):**
```markdown
## Roadmap Management

### View Roadmap Status
```bash
roadmap status
```

### Show Sprint Details
```bash
roadmap show sprint-1 --with-tasks
```

### View Dependencies
```bash
roadmap deps sprint-2
```

### Agent Workload
```bash
roadmap agents --workload
```

### Find Blocked Tasks
```bash
roadmap find --blocked
```

See `roadmap --help` for full command reference.
```

**Testing:**
- [ ] Commands documented
- [ ] Examples work

---

## Sprint 2: Polish & Launch (1.5 weeks, 28 hours)

**Goal:** Clean up, test, document, and prepare for launch

### Task 2.1: Enhance roadmap CLI (8 hours)

**File:** `framework/scripts/roadmap` (main CLI)

**New subcommands to add:**

```bash
# Plan management
roadmap plan create --track-id main --from-plan sprint-1-plan.md

# Sprint marker
roadmap marker update --sprint-id sprint-1

# Task operations
roadmap start task <task-id>
roadmap complete task <task-id>

# Gate operations
roadmap gate update --sprint-id <id> --gate <name> --status <status>

# Sprint lifecycle
roadmap pause sprint <sprint-id>
roadmap resume sprint <sprint-id>
roadmap complete sprint <sprint-id>
```

**Implementation approach:**
- Most logic already exists in `roadmap-update.py` and `roadmap-query.py`
- Just expose through cleaner CLI interface
- Add argument parsing for new commands

**Testing:**
- [ ] All new commands work
- [ ] Help text clear
- [ ] Error handling robust

---

### Task 2.2: Delete Legacy Scripts (2 hours)

**Files to DELETE entirely:**
```bash
rm framework/scripts/create-sprint-state.py      # 304 lines
rm framework/scripts/update-sprint-state.py      # 526 lines
rm framework/scripts/query-sprint-state.py       # 504 lines
```

**Simplify update-sprint-marker.py:**
- Currently: 323 lines (manages state + updates CLAUDE.md)
- New: ~50 lines (just updates CLAUDE.md)
- Rename to: `update-claude-marker.py` for clarity

**Before:**
```python
def update_sprint_marker(sprint_number, sprint_name, state_file):
    # 300+ lines of state management
    # Plus marker update
```

**After:**
```python
def update_claude_marker(sprint_id):
    """Update CLAUDE.md with current sprint marker."""
    # Get sprint from roadmap
    sprint = roadmap.get_sprint(sprint_id)

    # Read CLAUDE.md
    claude_md = Path(".claude/CLAUDE.md").read_text()

    # Update marker section
    updated = update_sprint_section(claude_md, sprint)

    # Write back
    Path(".claude/CLAUDE.md").write_text(updated)
```

**Total deletion:** ~1,334 lines

**Testing:**
- [ ] Scripts deleted from codebase
- [ ] No broken references
- [ ] Framework still deploys

---

### Task 2.3: Integration Testing (8 hours)

**Complete end-to-end test:**

```bash
# 1. Fresh deployment
/vibey
# Verify: .vibey/ created, roadmap initialized

# 2. Sprint planning
/vibey plan
# Verify: sprint created in roadmap, tasks extracted

# 3. View roadmap
roadmap status
# Verify: shows sprint, tasks, progress

# 4. Execute sprint
/vibey code
# Verify: dashboard shows roadmap data

# 5. Complete tasks
# Select task → mark complete
# Verify: roadmap updated, progress shown

# 6. Update quality gate
# Run security audit → update gate
# Verify: gate status updated

# 7. Complete sprint
# All tasks done → complete sprint
# Verify: sprint marked complete, version bumped

# 8. Multi-sprint test
/vibey plan  # Sprint 2
# Add dependency on sprint-1-task-003
# Verify: dependency detected, shows in deps graph
```

**Test Matrix:**

| Scenario | Expected Behavior | Status |
|----------|------------------|--------|
| Fresh deployment | .vibey/ initialized | [ ] |
| Sprint planning | Sprint + tasks created | [ ] |
| Dashboard display | Shows roadmap data | [ ] |
| Task completion | Updates roadmap | [ ] |
| Quality gates | Status tracked | [ ] |
| Sprint completion | Version bumps | [ ] |
| Multi-sprint deps | Dependencies work | [ ] |
| Agent workload | Shows across sprints | [ ] |

---

### Task 2.4: Documentation Updates (6 hours)

**Files to update:**

1. **`docs/getting-started/QUICK_START.md`**
   - Remove references to `docs/sprints/*.yaml`
   - Show `.vibey/` structure
   - Update workflow examples

2. **`docs/guides/WORKFLOW_SELECTION_GUIDE.md`**
   - Update sprint planning flow
   - Show roadmap integration

3. **`README.md`**
   - Update feature list
   - Highlight roadmap capabilities
   - Multi-sprint dependency tracking

4. **`CLAUDE.md`** (framework context)
   - Update Python scripts list
   - Remove legacy script references
   - Add roadmap integration status

5. **Create `docs/reference/ROADMAP_CLI.md`** (NEW)
   - Complete CLI reference
   - All commands with examples
   - Workflow guides

**Documentation structure:**
```markdown
# Roadmap CLI Reference

## Overview
The `roadmap` command manages multi-sprint project planning.

## Commands

### Sprint Management
- `roadmap plan create` - Create sprint from plan
- `roadmap start sprint` - Start sprint execution
- `roadmap pause sprint` - Pause active sprint
- `roadmap complete sprint` - Complete sprint

### Task Management
- `roadmap start task` - Start task
- `roadmap complete task` - Complete task
- `roadmap find` - Find tasks by criteria

### Quality Gates
- `roadmap gate update` - Update gate status

### Queries
- `roadmap status` - Overall status
- `roadmap show` - Show specific object
- `roadmap deps` - Show dependencies
- `roadmap agents` - Agent assignments

### Examples
[Comprehensive examples for each command]
```

---

### Task 2.5: Final Cleanup & Release (4 hours)

**Code cleanup:**

1. **Remove references:**
   - Search codebase for `docs/sprints/*-state.yaml`
   - Search for `create-sprint-state.py`, `update-sprint-state.py`, `query-sprint-state.py`
   - Remove all references

2. **Update .gitignore:**
   ```
   # State management (authoritative in .vibey/)
   docs/sprints/*-state.yaml
   ```

3. **Update framework deployment:**
   - Remove copying of deleted scripts
   - Add roadmap scripts to deployment

**Release preparation:**

1. **Version bump:** 1.2.0 → 2.0.0
   - Major version (breaking change - removed scripts)

2. **CHANGELOG.md:**
   ```markdown
   ## [2.0.0] - 2025-01-XX

   ### Breaking Changes
   - Removed legacy sprint-state scripts
   - Replaced with roadmap system integration

   ### Added
   - Roadmap integration in /vibey commands
   - Multi-sprint dependency tracking
   - Enhanced progress visualization

   ### Removed
   - create-sprint-state.py (replaced by roadmap)
   - update-sprint-state.py (replaced by roadmap)
   - query-sprint-state.py (replaced by roadmap)
   ```

3. **Git tag:** `v2.0.0`

**Testing:**
- [ ] No broken references
- [ ] All /vibey commands work
- [ ] Documentation complete
- [ ] Version updated
- [ ] CHANGELOG accurate

---

## Summary: What Changed

### Original Plan (6 weeks, 126 hours)
- Sprint 1: Foundation & Planning (38h)
- Sprint 2: Progress Tracking (42h)
- Sprint 3: Migration & Deprecation (46h)

### Optimal Plan (3 weeks, 60 hours)
- Sprint 1: Direct Integration (32h)
- Sprint 2: Polish & Launch (28h)
- ~~Sprint 3: DELETED~~ (46h saved)

### Eliminated Work (52% reduction)

**No longer needed:**
- ❌ Migration script (400+ lines, 12 hours)
- ❌ Migration command (4 hours)
- ❌ Backward compatibility (8 hours)
- ❌ Dual-system support (throughout)
- ❌ Deprecation warnings (6 hours)
- ❌ Legacy documentation (8 hours)
- ❌ Migration testing (6 hours)
- ❌ Gradual transition logic (throughout)

**Total savings:** 46+ hours of unnecessary work

### What We're Doing

**Clean replacement:**
1. Wire roadmap directly into /vibey commands
2. Delete legacy scripts entirely (no deprecation)
3. Enhance roadmap CLI with missing commands
4. Test thoroughly
5. Document completely
6. Launch v2.0.0

---

## Key Benefits of Optimal Approach

### 1. Simpler Codebase
- No migration complexity
- No backward compatibility code
- No dual-system confusion
- Clean architecture from day one

### 2. Faster Implementation
- 3 weeks instead of 6 weeks
- 60 hours instead of 126 hours
- Focus on integration, not migration

### 3. Better Quality
- More time for testing (same % of time, less total time)
- Cleaner code (no compatibility hacks)
- Better documentation (no migration guides)

### 4. Easier Maintenance
- Single system (roadmap only)
- No legacy baggage
- No deprecated code paths

### 5. No User Confusion
- One way to do things (roadmap)
- Clear documentation
- No migration prompts

---

## Risks & Mitigation

### Risk: Internal Vibey dogfooding disrupted

**Impact:** Medium
**Probability:** Low

**Mitigation:**
- Vibey's own .vibey/ directory is already using roadmap system
- Just need to ensure /vibey commands work with it
- Test integration with Vibey's own roadmap

### Risk: Missed edge cases in integration

**Impact:** Medium
**Probability:** Medium

**Mitigation:**
- Comprehensive testing suite
- Test all /vibey command flows
- Test with multiple sprint scenarios

### Risk: Documentation gaps

**Impact:** Low
**Probability:** Low

**Mitigation:**
- Complete CLI reference
- Updated quick start
- Example workflows

---

## Success Metrics

### Quantitative
- [x] 0 legacy scripts remaining
- [x] 100% /vibey commands use roadmap
- [x] ~1,334 lines of code deleted
- [x] 0 migration scripts needed
- [x] 2.0.0 release in 3 weeks

### Qualitative
- [x] Clean, maintainable codebase
- [x] Single source of truth (roadmap)
- [x] No complexity from migration
- [x] Clear documentation
- [x] Ready for production deployment

---

## Timeline

### Week 1: Sprint 1 Start
- [ ] Day 1-2: Tasks 1.1 & 1.2 (deployment + planning)
- [ ] Day 3-4: Task 1.3 (dashboard)
- [ ] Day 5: Task 1.4 start (progress tracking)

### Week 2: Sprint 1 Complete
- [ ] Day 6-8: Task 1.4 complete (progress tracking)
- [ ] Day 9: Task 1.5 (Vibey Manager)
- [ ] Day 10: Sprint 1 testing

### Week 3: Sprint 2 (Polish & Launch)
- [ ] Day 11-13: Task 2.1 (enhance CLI)
- [ ] Day 14: Task 2.2 (delete legacy)
- [ ] Day 15-17: Task 2.3 (testing)
- [ ] Day 18-19: Task 2.4 (documentation)
- [ ] Day 20-21: Task 2.5 (cleanup & release)

**Milestone:** v2.0.0 Release (End of Week 3)

---

## Conclusion

This **optimal plan** is:
- ✅ **Simpler** - No migration complexity
- ✅ **Faster** - 3 weeks vs 6 weeks
- ✅ **Cleaner** - No legacy baggage
- ✅ **Better** - Focus on quality, not compatibility

**Ready to execute** - Clean integration, no compromises, optimal system design.
