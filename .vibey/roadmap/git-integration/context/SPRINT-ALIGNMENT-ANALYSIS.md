# Sprint Alignment Analysis

**Purpose:** Verify Sprints 1-3 implement all features designed in Sprint 0

---

## Sprint 0 Architecture Key Features

### Core Features
- ✅ Primitive mapping (Roadmap→Repo, Task→Commit, etc.)
- ✅ Three-scenario source of truth (YAML-only, Hybrid, Git-primary)
- ✅ Commit conventions (conventional, footer, bracket formats)
- ✅ Branching strategies (trunk-based, feature, sprint, track, hierarchical)
- ✅ Enforcement modes (off, advisory, blocking, audit)
- ✅ State reconstruction (point-in-time, attribution, progress history)

### Advanced Features (from Addendum)
- ⚠️ Task tags (optional enhancement)
- ⚠️ Sprint tags (start/end markers)
- ⚠️ Tag repair automation (after squash/rebase)
- ⚠️ Hierarchical branching enforcement
- ⚠️ Strategy presets (configurable)
- ⚠️ Dynamic mode detection
- ⚠️ Git-primary sync command
- 🔮 Submodule aggregation (v2, future)

---

## Sprint 1: Git History & Commit Analysis

### ✅ Currently Included
1. Commit message parsing
2. Task-commit correlation
3. Git log analysis
4. Sprint velocity calculator
5. `vibey git analyze` command
6. Test suite
7. Documentation

### ❌ Missing from Sprint 0 Architecture

#### **Missing: State Reconstruction Commands**
From `006-state-reconstruction.md`:
- `vibey git state-at <ref>` - Show roadmap state at commit/tag/date
- `vibey git diff <ref1> <ref2>` - Compare two states
- `vibey git history <task-id>` - Show task change history
- `vibey git progress <sprint-id>` - Show progress over time
- `vibey git rollback <ref>` - Restore state from ref

**Impact:** High - These are core read-only features for historical analysis

#### **Missing: Tag Parsing Support**
From `008-addendum.md` Section 2:
- Parse sprint tags (`sprint/<id>/start`, `sprint/<id>/end`)
- Parse task tags (`track/sprint/task/marker`)
- Use tags for commit range queries

**Impact:** Medium - Tags provide explicit markers, faster queries

#### **Missing: All Commit Formats**
Currently mentions conventional and bracket, but missing:
- Footer reference format (`Task: task-id`)
- Inline references (detecting task IDs in message body)

**Impact:** Low - Can be added during implementation, but should be explicit

#### **Missing: Mode-Aware Parsing**
From `008-addendum.md` Section 7:
- Detect current source of truth mode
- Parse differently for Git-primary vs Hybrid mode

**Impact:** Medium - Important for Git-primary mode support

---

## Sprint 2: Git Hooks Core

### ✅ Currently Included
1. Pre-commit hook (YAML validation)
2. Commit-msg hook (task reference parsing)
3. Hook install/uninstall commands
4. Automatic task status updates
5. Branch-to-task linking
6. PR description generator
7. Test suite
8. Documentation

### ❌ Missing from Sprint 0 Architecture

#### **Missing: Sprint Tagging Commands**
From `008-addendum.md` Section 2:
- `vibey git tag sprint-start <sprint-id>` - Create start tag
- `vibey git tag sprint-end <sprint-id>` - Create end tag
- `vibey sprint start <id>` - Automated tagging
- `vibey sprint complete <id>` - Automated tagging

**Impact:** High - Sprint tags are fundamental to Sprint 0 design

#### **Missing: Task Tagging Support (Optional)**
From `008-addendum.md` Section 2:
- `vibey git tag task-start <task-id>`
- `vibey git tag task-end <task-id>`
- Configuration: `git.tags.task_tags.enabled`

**Impact:** Low - Optional enhancement, but should be configurable

#### **Missing: Git-Primary Sync Command**
From `008-addendum.md` Section 7:
- `vibey git sync` - Derive YAML from Git state
- Only relevant for Git-primary mode
- Auto-generates YAML files from branches/tags/commits

**Impact:** High - Critical for Git-primary mode functionality

#### **Missing: Source of Truth Mode Awareness**
From `008-addendum.md` Section 7:
- Hooks should respect current mode
- Git-primary: update Git, then sync to YAML
- Hybrid: update YAML, Git provides evidence
- YAML-only: skip Git operations

**Impact:** High - Hooks behave differently per mode

#### **Missing: Strategy Enforcement Configuration**
From `008-addendum.md` Section 6:
- Load strategy requirements from config
- Validate branch naming conventions
- Enforce required branches/tags
- Check against strategy rules

**Impact:** High - Core to strategy enforcement feature

#### **Missing: Hierarchical Branch Validation**
From `008-addendum.md` Section 5:
- Validate branch hierarchy (track → sprint → task)
- Enforce merge targets
- Check parent branch exists

**Impact:** Medium - Only needed for hierarchical strategy

---

## Sprint 3: Advanced Integration

### ✅ Currently Included
1. PR merge conflict detection
2. Quality gate CI integration
3. Blocker enforcement
4. Dependency-aware merge ordering
5. Error handling and recovery (`vibey git repair`, `vibey git validate`)
6. Integration test suite
7. Complete documentation

### ❌ Missing from Sprint 0 Architecture

#### **Missing: Tag Repair Automation**
From `008-addendum.md` Section 4:
- `vibey git repair-tags` - Fix dangling tags after rebase/squash
- `vibey git validate-tags` - Detect dangling tags
- Automatic repair hooks (post-rebase, post-merge)
- Configuration: `git.tags.repair.auto`

**Impact:** High - Critical for maintaining tag integrity

#### **Missing: Strategy Adoption Commands**
From `008-addendum.md` Section 6:
- `vibey git strategy adopt <preset>` - Adopt trunk-based/feature/gitflow/hierarchical
- `vibey git strategy validate` - Check compliance with chosen strategy
- Strategy presets configuration

**Impact:** High - User-facing feature for strategy selection

#### **Missing: Mode Switching**
From `008-addendum.md` Section 7:
- `vibey git mode` - Show current mode
- `vibey git mode switch <mode>` - Change modes
- Automatic fallback from Git-primary to Hybrid
- Migration workflows between modes

**Impact:** Medium - Nice-to-have, but mode can be changed via config

#### **Missing: Submodule Support (v2)**
From `008-addendum.md` Section 1:
- Submodule roadmap aggregation
- `vibey roadmap status --aggregate`
- Cross-repo dependencies

**Impact:** Low - Explicitly marked as v2/future work

---

## Summary of Gaps

### High Priority Gaps (Must Fix)

| Sprint | Missing Feature | Effort | Where Documented |
|--------|----------------|--------|------------------|
| 1 | State reconstruction commands | 8h | 006-state-reconstruction.md |
| 2 | Sprint tagging commands | 4h | 008-addendum.md §2 |
| 2 | Git-primary sync command | 6h | 008-addendum.md §7 |
| 2 | Mode-aware hooks | 4h | 008-addendum.md §7 |
| 2 | Strategy enforcement config | 6h | 008-addendum.md §6 |
| 3 | Tag repair automation | 6h | 008-addendum.md §4 |
| 3 | Strategy adoption commands | 4h | 008-addendum.md §6 |

**Total High Priority:** ~38 hours (add ~1.5 weeks to track)

### Medium Priority Gaps (Should Include)

| Sprint | Missing Feature | Effort | Where Documented |
|--------|----------------|--------|------------------|
| 1 | Tag parsing support | 3h | 008-addendum.md §2 |
| 1 | Mode-aware parsing | 2h | 008-addendum.md §7 |
| 2 | Hierarchical branch validation | 4h | 008-addendum.md §5 |
| 3 | Mode switching commands | 3h | 008-addendum.md §7 |

**Total Medium Priority:** ~12 hours (add ~0.5 weeks)

### Low Priority Gaps (Nice to Have)

| Sprint | Missing Feature | Effort | Where Documented |
|--------|----------------|--------|------------------|
| 1 | Inline commit format parsing | 2h | 003-commit-conventions.md |
| 2 | Task tagging (optional) | 4h | 008-addendum.md §2 |

**Total Low Priority:** ~6 hours

---

## Recommendations

### Option A: Add Missing Tasks to Current Sprints
- Expand Sprint 1 by 2 tasks (13h)
- Expand Sprint 2 by 3 tasks (20h)
- Expand Sprint 3 by 2 tasks (10h)
- **Total:** 43h additional work, ~1.5-2 weeks

**Pros:**
- Complete implementation of Sprint 0 design
- No need for Sprint 4
- All features in initial release

**Cons:**
- Longer sprints
- More complexity per sprint

### Option B: Add Sprint 4 for Advanced Features
- Keep Sprints 1-3 as-is (core features)
- Create Sprint 4 for:
  - State reconstruction
  - Tag management
  - Strategy configuration
  - Mode switching
- **Total:** ~43h as separate sprint, 2 weeks

**Pros:**
- Sprints 1-3 stay focused
- Advanced features isolated
- Can defer Sprint 4 if needed

**Cons:**
- Longer track (5 sprints instead of 4)
- Delayed availability of some features

### Option C: Mark Some as v1.5/v2
- Sprint 1-3: Core v1 features (as-is)
- v1.5 release:
  - State reconstruction
  - Tag repair
  - Strategy presets
- v2 release:
  - Git-primary mode
  - Mode switching
  - Submodule aggregation

**Pros:**
- Fastest path to v1 release
- Can gather feedback before v1.5
- Incremental delivery

**Cons:**
- Features split across releases
- May confuse users about what's available

---

## My Recommendation

**Option A: Add Missing Tasks to Current Sprints**

**Rationale:**
1. Sprint 0 architecture is comprehensive and well-designed
2. Missing features are integral, not optional
3. Splitting features creates incomplete implementation
4. Better to launch with complete feature set
5. Only adds ~2 weeks to 9-week track (22% increase)

**Specific additions:**

### Sprint 1 → Sprint 1 Enhanced
Add 2 tasks:
- **Task 008:** Implement state reconstruction queries (state-at, diff, history, progress, rollback) - 8h
- **Task 009:** Add tag parsing and range queries - 3h
- **Updated estimate:** 2.5 weeks (was 2 weeks)

### Sprint 2 → Sprint 2 Enhanced
Add 3 tasks:
- **Task 009:** Implement sprint tagging system - 4h
- **Task 010:** Add Git-primary sync command - 6h
- **Task 011:** Implement source-of-truth mode detection and strategy enforcement - 6h
- **Updated estimate:** 3 weeks (was 2 weeks)

### Sprint 3 → Sprint 3 Enhanced
Add 2 tasks:
- **Task 008:** Implement tag repair automation - 6h
- **Task 009:** Add strategy preset adoption commands - 4h
- **Updated estimate:** 3.5 weeks (was 3 weeks)

**New track totals:**
- 4 sprints (unchanged)
- 36 tasks (was 29, +7)
- 11 weeks (was 9 weeks, +2)
- Complete Sprint 0 architecture implementation

---

## Next Steps

1. ✅ Review this analysis
2. ⏭️ Choose option (A, B, or C)
3. ⏭️ Update sprint YAML files
4. ⏭️ Verify task dependencies
5. ⏭️ Update track totals
6. ⏭️ Begin Sprint 1
