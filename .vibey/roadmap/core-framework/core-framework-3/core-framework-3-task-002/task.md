# Integrate cache into roadmap CLI commands

**ID:** `core-framework-3-task-002`  
**Sprint:** `core-framework-3`  
**Type:** development  
**Status:** ✅ Completed  
**Priority:** 🟡 Medium  

## Description

Update all roadmap CLI commands to use caching layer.

Commands to update:
- roadmap status (uses task index)
- roadmap show (uses all indexes)
- roadmap list (uses type-specific indexes)
- roadmap find (uses indexes + search)
- roadmap deps (uses dependency graphs)
- roadmap context (uses dependency graphs)
- roadmap recommend (uses task index + assignments)

Integration:
- Initialize cache once on CLI startup
- Invalidate cache after state-changing commands
- Track cache hit rate for monitoring
- Add --no-cache flag for debugging


## Details

- **Estimated Tokens:** 1
- **Complexity:** medium

## Timeline

- **Created:** 2025-11-08 10:10 UTC
- **Completed:** 2025-11-08 15:14 UTC

---

*Generated from task.yaml on 2025-11-09 19:14 UTC*
