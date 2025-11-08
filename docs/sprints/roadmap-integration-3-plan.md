# Sprint Plan: Migration & Deprecation

**Sprint ID:** roadmap-integration-3
**Sprint Name:** Migration & Deprecation
**Track:** roadmap-integration
**Duration:** 2 weeks (estimated)
**Priority:** High
**Status:** Not Started

---

## Sprint Goal

Complete the roadmap integration track by migrating existing users from the legacy sprint-state system to the new roadmap system, deprecating legacy scripts, and providing comprehensive migration documentation.

**Success Criteria:**
- Migration script successfully converts legacy state to roadmap format
- All `/vibey` command workflow documentation updated
- User migration guide complete with examples
- Legacy scripts marked as deprecated with clear warnings
- Integration tests pass with 100% success rate
- Zero breaking changes for existing users

---

## Background

### Problem

Vibey currently maintains **two parallel sprint state management systems**:

1. **Legacy System** (`docs/sprints/*.yaml`) - Used by `/vibey` commands
2. **Roadmap System** (`.vibey/`) - Advanced features, not integrated

**Impact:**
- Code duplication: ~1,657 lines
- Users can't access advanced roadmap features
- Maintenance burden on both systems
- Confusion about which system to use

### Solution

This sprint completes the integration by:
1. Creating migration path from legacy → roadmap
2. Updating documentation to guide users
3. Deprecating legacy scripts (not removing, just marking deprecated)
4. Providing clear upgrade instructions

---

## Tasks

### Task 1: Create Migration Script
**ID:** roadmap-integration-3-task-001
**Priority:** High
**Estimated:** 8 hours
**Agents:** web-developer, test-engineer

**Description:**
Create `migrate-to-roadmap.py` script that automatically converts legacy sprint state files to roadmap format.

**Requirements:**
- Read all `docs/sprints/sprint-*-state.yaml` files
- Convert to `.vibey/` structure (roadmap, tracks, sprints, tasks)
- Preserve all data (tasks, agents, quality gates, progress)
- Generate roadmap.yaml with proper metadata
- Create track for migrated sprints
- Validate output matches legacy state
- Provide dry-run mode
- Generate migration report

**Input:**
```bash
python3 .claude/scripts/migrate-to-roadmap.py \
  --legacy-dir docs/sprints \
  --output-dir .vibey \
  --dry-run
```

**Output:**
- `.vibey/roadmap.yaml`
- `.vibey/tracks/migrated-sprints.yaml`
- `.vibey/sprints/sprint-<n>.yaml`
- `.vibey/tasks/sprint-<n>-tasks.yaml`
- Migration report (JSON/markdown)

**Validation:**
- All tasks preserved
- All agent assignments intact
- All quality gates transferred
- Progress percentages match
- No data loss

**Edge Cases:**
- Empty sprint files
- Missing fields
- Incompatible formats
- Partial migrations

---

### Task 2: Update /vibey Command Workflow Documentation
**ID:** roadmap-integration-3-task-002
**Priority:** High
**Estimated:** 4 hours
**Agents:** docs-writer

**Description:**
Update all `/vibey` command documentation to reflect roadmap system integration.

**Files to Update:**
1. `docs/getting-started/QUICK_START.md`
   - Update sprint planning section
   - Add roadmap initialization
   - Update state file locations

2. `docs/getting-started/USER_JOURNEY.md`
   - Update all workflow examples
   - Show `.vibey/` structure
   - Update CLI commands

3. `docs/guides/WORKFLOW_SELECTION_GUIDE.md`
   - Update sprint planning workflow
   - Add roadmap features
   - Update examples

4. `docs/reference/COMMANDS.md`
   - Update `/vibey` command documentation
   - Update `/vibey plan` documentation
   - Update `/vibey code` documentation
   - Add roadmap CLI reference

**Key Changes:**
- Replace `docs/sprints/*.yaml` with `.vibey/`
- Update script names (roadmap → instead of sprint-state)
- Add multi-sprint capabilities
- Show dependency management
- Update example outputs

**Before/After Examples:**
Show side-by-side comparisons of old vs new workflows.

---

### Task 3: Create User Migration Guide
**ID:** roadmap-integration-3-task-003
**Priority:** High
**Estimated:** 6 hours
**Agents:** docs-writer, web-developer

**Description:**
Create comprehensive migration guide for users transitioning from legacy to roadmap system.

**Guide Structure:**

#### 1. Introduction
- Why migrate?
- What changes?
- What stays the same?
- Timeline expectations

#### 2. Pre-Migration Checklist
- Backup current state
- Review open sprints
- Complete in-progress tasks (optional)
- Update framework to v1.2.1+

#### 3. Migration Steps
**Step 1: Backup**
```bash
cp -r docs/sprints docs/sprints.backup
cp .claude/CLAUDE.md .claude/CLAUDE.md.backup
```

**Step 2: Run Migration**
```bash
python3 .claude/scripts/migrate-to-roadmap.py \
  --legacy-dir docs/sprints \
  --output-dir .vibey \
  --create-track migrated-sprints
```

**Step 3: Validate**
```bash
python3 .claude/scripts/roadmap status
python3 .claude/scripts/roadmap validate
```

**Step 4: Test**
```bash
/vibey code  # Should show roadmap dashboard
```

**Step 5: Cleanup (Optional)**
```bash
mkdir -p archive/legacy-sprints
mv docs/sprints archive/legacy-sprints
```

#### 4. What Changed
- File locations (docs/sprints → .vibey)
- CLI commands (sprint-state → roadmap)
- State structure (flat → hierarchical)
- New capabilities available

#### 5. New Features Available
- Multi-sprint planning
- Cross-sprint dependencies
- Blocker detection
- Track organization
- Agent workload balancing
- Task recommendations

#### 6. Troubleshooting
- Migration fails
- Data mismatch
- Missing tasks
- Rollback procedure

#### 7. FAQ
- "Do I have to migrate?"
- "Will my current sprint break?"
- "Can I rollback?"
- "What about custom scripts?"

---

### Task 4: Deprecate Legacy Sprint-State Scripts
**ID:** roadmap-integration-3-task-004
**Priority:** Medium
**Estimated:** 3 hours
**Agents:** web-developer

**Description:**
Mark legacy scripts as deprecated with clear warnings and migration instructions.

**Scripts to Deprecate:**
1. `create-sprint-state.py`
2. `update-sprint-state.py`
3. `query-sprint-state.py`
4. `update-sprint-marker.py`

**Deprecation Strategy:**
- Add deprecation warning at top of each script
- Show migration command
- Keep scripts functional (don't remove)
- Set deprecation date (6 months out)
- Update `--help` text

**Deprecation Warning Template:**
```python
#!/usr/bin/env python3
"""
⚠️  DEPRECATED: This script is deprecated as of 2025-11-08

This script is part of the legacy sprint-state system and will be removed
in Vibey Framework v2.0.0 (estimated 2026-05-08).

MIGRATION:
Please migrate to the roadmap system:

    python3 .claude/scripts/migrate-to-roadmap.py --help

For more information:
- Migration Guide: docs/guides/MIGRATION_TO_ROADMAP.md
- Roadmap System: docs/reference/ROADMAP_SYSTEM.md
- Help: /vibey help

This script will continue to work, but is no longer maintained.
"""

import sys
import warnings

warnings.warn(
    "create-sprint-state.py is deprecated. "
    "Use 'roadmap plan create' instead. "
    "See docs/guides/MIGRATION_TO_ROADMAP.md",
    DeprecationWarning,
    stacklevel=2
)

# Original script continues...
```

**Update Commands:**
- Add aliases in roadmap CLI for backward compatibility
- `sprint-state create` → `roadmap plan create`
- `sprint-state update` → `roadmap update`
- `sprint-state query` → `roadmap show`

---

### Task 5: Run Final Integration Tests
**ID:** roadmap-integration-3-task-005
**Priority:** High
**Estimated:** 5 hours
**Agents:** test-engineer

**Description:**
Create and run comprehensive integration tests for the complete roadmap integration.

**Test Suites:**

#### 1. Migration Tests
- `test_migration.py` (new)
  - Test legacy → roadmap conversion
  - Verify data integrity
  - Test dry-run mode
  - Test partial migrations
  - Test error handling
  - Test rollback capability

#### 2. Integration Tests
- `test_roadmap_integration.py` (extend existing)
  - Test `/vibey deployment` creates `.vibey/`
  - Test `/vibey plan` creates roadmap sprint
  - Test `/vibey code` reads from roadmap
  - Test Vibey Manager roadmap commands
  - Test backward compatibility

#### 3. End-to-End Tests
- `test_e2e_workflow.py` (new)
  - Full workflow: deploy → plan → code → complete
  - Test with roadmap system
  - Test quality gates
  - Test multi-sprint scenario
  - Test dependency handling

**Quality Gates:**
- Integration Testing: ≥95% (blocking)
- Migration Testing: 100% (blocking)
- Documentation Complete: ≥90% (blocking)

**Test Coverage Requirements:**
- Migration script: 100%
- Integration points: 100%
- Error paths: ≥80%
- Edge cases: ≥90%

---

### Task 6: Update Track Completion Documentation
**ID:** roadmap-integration-3-task-006
**Priority:** Medium
**Estimated:** 2 hours
**Agents:** docs-writer

**Description:**
Create final documentation for roadmap-integration track completion.

**Deliverables:**

#### 1. Track Completion Summary
- `.vibey/track_summaries/roadmap-integration-COMPLETED.md`
- All 3 sprints summary
- Total impact metrics
- Before/after comparison
- Code reduction achieved
- User benefits delivered

#### 2. Release Notes
- `CHANGELOG.md` update
- v1.2.1 → v1.3.0 (minor version bump)
- Breaking changes: None
- Deprecations: Legacy sprint-state scripts
- New features: Full roadmap integration
- Migration instructions

#### 3. Announcement Draft
- User-facing announcement
- Highlight benefits
- Migration timeline
- Support resources

---

## Dependencies

**Sprint 1 (Complete):**
- ✅ Roadmap initialization in `/vibey deployment`
- ✅ Roadmap sprint creation in `/vibey plan`

**Sprint 2 (Complete):**
- ✅ Roadmap progress tracking in `/vibey code`
- ✅ Extended Vibey Manager with roadmap commands

**External Dependencies:**
- None

---

## Deliverables

1. ✅ Migration script (`migrate-to-roadmap.py`)
2. ✅ Updated /vibey command workflow documentation
3. ✅ User migration guide (`MIGRATION_TO_ROADMAP.md`)
4. ✅ Deprecated legacy scripts (with warnings)
5. ✅ Integration test suite (migration + e2e)
6. ✅ Track completion documentation

---

## Risk Management

### Risk 1: Data Loss During Migration
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Dry-run mode by default
- Require explicit --confirm flag
- Automatic backup before migration
- Validation after migration
- Rollback capability

### Risk 2: User Resistance to Migration
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Keep legacy scripts functional
- Provide clear migration guide
- Show benefits prominently
- Offer migration support
- Gradual deprecation timeline (6 months)

### Risk 3: Backward Compatibility Breaking
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Thorough integration testing
- Maintain command aliases
- Preserve data formats
- Version detection in scripts
- Clear upgrade path

### Risk 4: Incomplete Documentation
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Comprehensive review checklist
- User testing with docs
- Examples for all scenarios
- FAQ section
- Video walkthrough (optional)

---

## Success Criteria

### Functional
- ✅ Migration script converts all legacy data accurately
- ✅ All `/vibey` commands work with roadmap system
- ✅ Integration tests pass with ≥95% success rate
- ✅ Migration tests pass with 100% success rate
- ✅ No data loss in migration process
- ✅ Rollback capability works

### Documentation
- ✅ All command documentation updated
- ✅ Migration guide complete with examples
- ✅ Troubleshooting section comprehensive
- ✅ FAQ answers common questions
- ✅ Release notes complete

### Quality
- ✅ Code follows framework conventions
- ✅ No linting errors
- ✅ Performance acceptable (<1s migration)
- ✅ Error messages clear and actionable
- ✅ Logging comprehensive

### User Experience
- ✅ Migration process straightforward
- ✅ Clear benefits communicated
- ✅ Support resources available
- ✅ Backward compatibility maintained
- ✅ Zero breaking changes

---

## Timeline

**Week 1:**
- Days 1-2: Task 1 (Migration script)
- Days 3-4: Task 2 (Documentation updates)
- Day 5: Task 3 (Migration guide)

**Week 2:**
- Days 6-7: Task 4 (Deprecation)
- Days 8-9: Task 5 (Integration tests)
- Day 10: Task 6 (Track completion docs)

**Total:** 10 working days (2 weeks)

---

## Phase Breakdown

### Phase 1: Migration Foundation (Tasks 1-2)
**Duration:** 12 hours
**Goal:** Build migration tooling and update core docs

### Phase 2: User Enablement (Tasks 3-4)
**Duration:** 9 hours
**Goal:** Provide migration guide and deprecate legacy

### Phase 3: Validation & Completion (Tasks 5-6)
**Duration:** 7 hours
**Goal:** Test thoroughly and document completion

**Total Estimated:** 28 hours

---

## Quality Gates

### Development Phase
- Migration script dry-run passes
- Data validation shows 100% accuracy
- Documentation builds without errors
- Legacy scripts show deprecation warnings

### Completion Phase
- Integration tests: ≥95% pass rate
- Migration tests: 100% pass rate
- Documentation: ≥90% complete
- User testing: Positive feedback

### Production Phase
- Migration tested on 3+ real projects
- Rollback procedure verified
- Performance benchmarks met
- Support documentation ready

---

## Metrics to Track

**Migration Success:**
- Total projects migrated: Target 100% of existing users
- Migration time: Target <2 minutes
- Data accuracy: Target 100%
- Rollback usage: Target <5%

**Code Quality:**
- Test coverage: Target ≥95%
- Linting errors: Target 0
- Documentation coverage: Target 100%
- Bug reports: Target <3 critical

**User Impact:**
- Code eliminated: Target ~1,657 lines
- New features unlocked: 10+ capabilities
- Migration friction: Target "Easy" rating
- User satisfaction: Target ≥90%

---

## References

**Documentation:**
- [ROADMAP_INTEGRATION_GAP.md](../development/ROADMAP_INTEGRATION_GAP.md)
- [Roadmap Object Hierarchy](../development/ROADMAP_OBJECT_HIERARCHY.md)
- [Progress Tracking Guide](../guides/PROGRESS_TRACKING.md)

**Commands:**
- `/vibey` - Main framework command
- `/vibey plan` - Sprint planning
- `/vibey code` - Sprint execution
- Roadmap CLI - Advanced roadmap management

**Scripts:**
- Legacy: `create-sprint-state.py`, `update-sprint-state.py`, `query-sprint-state.py`
- New: `roadmap` CLI with 15+ commands

---

## Appendix: Legacy System Analysis

### Files in Legacy System

**Scripts (4 files, 1,657 lines):**
- `create-sprint-state.py` (304 lines)
- `update-sprint-state.py` (526 lines)
- `query-sprint-state.py` (504 lines)
- `update-sprint-marker.py` (323 lines)

**State Files:**
- `docs/sprints/sprint-<n>-state.yaml` (per sprint)
- `docs/sprints/sprint-<n>-plan.md` (per sprint)

### Roadmap System Equivalent

**Scripts (1 unified CLI, 345 lines + libraries):**
- `roadmap` - Unified CLI
- `roadmap-lib/` - Shared libraries (cache, query, update, etc.)

**State Files:**
- `.vibey/roadmap.yaml` - One file for entire roadmap
- `.vibey/tracks/<track-id>.yaml` - Per track
- `.vibey/sprints/<sprint-id>.yaml` - Per sprint
- `.vibey/tasks/<sprint-id>-tasks.yaml` - Per sprint tasks

### Code Reduction

**Before:** 1,657 lines (legacy scripts) + scattered state files
**After:** 345 lines (unified CLI) + structured `.vibey/` directory
**Reduction:** ~1,300 lines eliminated (79% reduction)

---

**Sprint Created:** 2025-11-08
**Sprint Author:** sprint-planner, docs-writer
**Review Status:** Ready for execution
