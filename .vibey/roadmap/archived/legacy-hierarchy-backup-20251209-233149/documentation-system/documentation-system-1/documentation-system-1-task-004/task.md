# Implement context directory management

**ID:** `documentation-system-1-task-004`  
**Sprint:** `documentation-system-1`  
**Type:** development  
**Status:** ✅ Completed  
**Priority:** 🟡 Medium  

## Description

Create CLI commands and helper functions for managing context
directories at track, sprint, and task levels.

Implementation:
- Add vibey roadmap add-context command
- Support --track, --sprint, --task flags
- Auto-create context directories if missing
- Copy/move files to appropriate context directory
- Update TOC to reference context files
- Validate context files exist

Acceptance Criteria:
- CLI command works for all three levels
- Context directories created automatically
- Files copied/moved correctly
- TOC updated to show context files
- Error handling for invalid paths


## Details

- **Estimated Tokens:** 3,000
- **Complexity:** medium

## Timeline

- **Created:** 2025-11-09 21:29 UTC
- **Completed:** 2025-11-09 22:02 UTC

---

*Generated from task.yaml on 2025-11-09 19:14 UTC*
