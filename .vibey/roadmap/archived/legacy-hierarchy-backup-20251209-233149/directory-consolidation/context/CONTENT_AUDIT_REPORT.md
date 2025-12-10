# Content Audit Report
**Date:** 2025-11-23
**Sprint:** directory-consolidation-3

## Executive Summary

This audit identifies content duplication, misplaced files, and consolidation opportunities across three locations:
- `framework/` - Content files (agents, workflows, templates, docs)
- `docs/` - Documentation
- `.vibey/roadmap/*/context/` - Track-specific context files

### Key Findings
| Location | Total Files | Action Items |
|----------|-------------|--------------|
| framework/docs/ | 23 markdown | Merge into docs/ |
| docs/ | 171 markdown | 45 session-specific to relocate |
| .vibey/roadmap/*/context/ | 162 files | Archive completed track context |

---

## 1. framework/docs/ vs docs/ Duplication

### Duplicate Files (5)
Files with same name in both locations, but DIFFERENT content:

| File | framework/docs/ | docs/ | Recommendation |
|------|----------------|-------|----------------|
| PLATFORM_AGNOSTIC_ARCHITECTURE.md | 1459 lines | 1011 lines | Keep framework (newer/larger) |
| YAML_MARKDOWN_SEPARATION.md | 420 lines | 796 lines | Keep docs (larger) |
| TROUBLESHOOTING.md | 705 lines | 855 lines | Keep docs (larger) |
| README.md | 79 lines | 49 lines | Keep framework (more content) |
| ROADMAP_USER_GUIDE.md | 1248 lines | 844 lines | Keep framework (larger) |

### Unique Files in framework/docs/ (18)
These files exist ONLY in framework/docs/ and should be moved to docs/:

**framework/docs/development/** (9 files):
- ARCHITECTURE_DECISION_TEXT_VS_DATABASE.md
- CONTEXT_LOADING_STRATEGY.md
- DEPENDENCY_TRACKING_V2.md
- ROADMAP_EXAMPLES.md
- ROADMAP_MIGRATION_GUIDE.md
- ROADMAP_QUICK_REFERENCE.md

**framework/docs/getting-started/** (3 files):
- QUICK_START.md
- README.md
- USER_JOURNEY.md

**framework/docs/guides/** (5 files):
- ORCHESTRATION.md
- PROGRESS_TRACKING.md
- README.md
- SPRINT_DRIVEN_ORCHESTRATION.md
- WORKFLOW_SELECTION_GUIDE.md

**framework/docs/reference/** (3 files):
- COMMANDS.md
- README.md
- ROADMAP_SYSTEM.md

**framework/docs/** (root):
- FAQ.md

### Recommended Actions
1. **Delete** 5 duplicate files from framework/docs/ (docs/ versions authoritative for 3, framework/ for 2)
2. **Move** 18 unique files from framework/docs/ to appropriate docs/ subdirectories
3. **Delete** empty framework/docs/ directory after migration

---

## 2. docs/ File Categorization

### Summary
- **Total:** 171 markdown files
- **Session-specific:** ~45 files (should move to .vibey/roadmap/*/context/)
- **Permanent:** ~126 files (should stay in docs/)

### Session-Specific Files (45) - Relocate
These files are dated, one-time reports that belong in track context:

**Pattern: Dated (*2025*)** - 15 files
- COMPREHENSIVE_AUDIT_2025-11-13.md
- BACKUP_ARCHIVE_INVENTORY_2025-11-12.md
- TEST_FAILURES_ANALYSIS_2025-11-12.md
- etc.

**Pattern: SESSION_*** - 4 files
- SESSION_HANDOFF.md
- SESSION_2025-11-07_ROADMAP_INTEGRATION_GAP.md
- SESSION_SUMMARY_DOGFOODING_FIX.md
- SESSION_SUMMARY_MCP_IMPLEMENTATION.md

**Pattern: *_COMPLETE.md** - 9 files
- CLAUDE_PORT_SPRINT1_COMPLETE.md
- DOGFOODING_FIX_COMPLETE.md
- INTERFACE_UNIFICATION_SPRINT*_COMPLETE.md (4)
- MCP_SPRINT_2_COMPLETE.md
- MCP_TESTING_COMPLETE.md
- MANUAL_INTEGRATION_COMPLETE.md

**Pattern: *_SUMMARY.md** - 6 files
- TEST_SUITE_UPDATE_SUMMARY.md
- USER_JOURNEY_UPDATE_SUMMARY.md
- OUTSTANDING_ROADMAP_SUMMARY.md
- DOCUMENTATION_SYSTEM_IMPLEMENTATION_SUMMARY.md
- SPRINT_*_SUMMARY.md (2)

**Pattern: TEST_*** - 7 files
- TEST_ANALYSIS_AND_LIMITATIONS.md
- TEST_COVERAGE_ANALYSIS.md
- TEST_COVERAGE_GAP_ANALYSIS.md
- TEST_FAILURES_ANALYSIS_2025-11-12.md
- TEST_FIX_SESSION_2025-11-12.md
- TEST_SUITE_UPDATE_SUMMARY.md
- (in validation/) TEST_SUITE_MODERNIZATION_2025-11-11.md

**Pattern: *_AUDIT_*, *_ANALYSIS*, *_GAP*** - 7 files
- USER_JOURNEY_GAP_ANALYSIS.md
- INTERFACE_AUDIT_2025-11-12.md
- PLATFORM_TRACKING_ANALYSIS.md
- VELOCITY_THEATER_ANALYSIS.md
- DOCUMENTATION_GAP_ANALYSIS.md
- REMAINING_JOURNEY_GAPS.md
- RECURRING_ISSUES_FIXES_2025-11-13.md

### Recommended Actions
1. Move session-specific files to `.vibey/roadmap/[relevant-track]/context/`
2. Create archived/ subdirectory in docs/ for historical reference
3. Keep permanent documentation in place

---

## 3. .vibey/roadmap/*/context/ Cleanup

### Summary
- **Total:** 162 context files
- **Context directories:** 39
- **Completed tracks:** 27 (could archive)

### High-Volume Directories
| Directory | Files | Notes |
|-----------|-------|-------|
| roadmap-integrity-fixes/context/qa-reports/ | 18 | QA testing reports |
| roadmap-integrity-fixes/roadmap-integrity-fixes-8/context/ | 10 | Sprint 8 context |
| roadmap-integrity-fixes/context/status/ | 8 | Status reports |
| roadmap-integrity-fixes/context/gap-analysis/ | 6 | Analysis files |
| roadmap-integrity-fixes/context/forensic-agents/ | 6 | Forensic reports |

### Duplicate Pattern Analysis
- **TRACK_AUDIT_REPORT files:** 40 (multiple dated versions per track)
- **REMEDIATION_REPORT files:** 16

### Recommended Actions
1. **Keep latest** TRACK_AUDIT_REPORT per track, archive older versions
2. **Archive** context from completed tracks to `.vibey/roadmap/archived/`
3. **Consolidate** roadmap-integrity-fixes context (most files)
4. **Delete** redundant/superseded reports

---

## 4. Prioritized Action Plan

### Phase 1: High Priority (Sprint 4)
1. Merge framework/docs/ into docs/
   - Delete 5 duplicates (keep docs/ version for 3, merge framework/ content for 2)
   - Move 18 unique files to appropriate docs/ subdirectories
   - Delete empty framework/docs/

2. Relocate session-specific docs
   - Move 45 dated/session files to .vibey/roadmap/*/context/
   - Organize by relevant track

### Phase 2: Medium Priority
3. Archive completed track context
   - Create .vibey/roadmap/archived/ directory
   - Move context from 27 completed tracks
   - Keep structure but mark as archived

### Phase 3: Low Priority
4. Consolidate duplicate audit reports
   - Keep only latest TRACK_AUDIT_REPORT per track
   - Archive older versions

---

## 5. Risk Assessment

| Action | Risk Level | Mitigation |
|--------|------------|------------|
| Merge framework/docs/ | Low | Content preserved, just relocated |
| Move session docs | Low | Files still accessible in new location |
| Archive completed track context | Low | Archived, not deleted |
| Delete duplicate reports | Medium | Ensure latest version retained |

---

## 6. Expected Outcomes

After remediation:
- **framework/** contains ONLY: agents/, workflows/, templates/, config/, schemas/, examples/
- **docs/** contains ONLY permanent documentation (~126 files)
- **.vibey/roadmap/*/context/** is organized and archived for completed tracks
- Clear separation between permanent docs and session-specific context
