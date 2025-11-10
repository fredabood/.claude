# Update roadmap state management scripts

**ID:** `documentation-system-1-task-005`  
**Sprint:** `documentation-system-1`  
**Type:** development  
**Status:** ✅ Completed  
**Priority:** 🟡 Medium  

## Description

Update all Python scripts to use new hierarchical structure instead
of flat directory layout.

Implementation:
- Update framework/roadmap/state_manager.py
- Update framework/scripts/roadmap.py
- Change paths from .vibey/tracks/ to .vibey/roadmap/[track-id]/
- Change paths from .vibey/sprints/ to .vibey/roadmap/[track-id]/[sprint-id]/
- Change paths from .vibey/tasks/ to .vibey/roadmap/[track-id]/[sprint-id]/[task-id]/
- Use path helper functions consistently
- Update all YAML loading/saving

Acceptance Criteria:
- All scripts use new hierarchical paths
- Backward compatibility maintained temporarily
- Path helper functions used consistently
- YAML loading/saving works correctly
- No broken references


## Details

- **Estimated Tokens:** 4,000
- **Complexity:** medium

## Timeline

- **Created:** 2025-11-09 21:29 UTC
- **Started:** 2025-11-09 22:07 UTC
- **Completed:** 2025-11-09 22:25 UTC

---

*Generated from task.yaml on 2025-11-09 19:14 UTC*
