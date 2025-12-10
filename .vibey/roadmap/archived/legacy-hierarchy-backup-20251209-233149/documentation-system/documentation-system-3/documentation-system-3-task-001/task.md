# Build migration script for existing tracks

**ID:** `documentation-system-3-task-001`  
**Sprint:** `documentation-system-3`  
**Type:** development  
**Status:** ⚪ Not Started  
**Priority:** 🟡 Medium  

## Description

Create comprehensive migration script to move existing roadmap files
from flat structure to hierarchical structure.

Implementation:
- Create framework/scripts/migrate_to_hierarchy.py
- Move .vibey/tracks/*.yaml → .vibey/roadmap/[track-id]/[track-id].yaml
- Move .vibey/sprints/*.yaml → .vibey/roadmap/[track-id]/[sprint-id]/[sprint-id].yaml
- Move .vibey/tasks/*.yaml → .vibey/roadmap/[track-id]/[sprint-id]/[task-id]/[task-id].yaml
- Detect and move related docs from docs/development/ to context/
- Generate TOC JSON files for migrated objects
- Generate markdown views for migrated objects
- Update roadmap.yaml with new structure
- Support --dry-run mode (preview changes)
- Create migration backup

Acceptance Criteria:
- Script successfully migrates all tracks
- No data loss during migration
- All relationships preserved
- Context files moved to appropriate locations
- Generated files (TOC, MD) created correctly
- Dry-run shows accurate preview
- Backup created before migration


## Details

- **Estimated Tokens:** 5,000
- **Complexity:** medium

## Timeline

- **Created:** 2025-11-09 21:29 UTC

---

*Generated from task.yaml on 2025-11-09 19:14 UTC*
