# Add optional persistent cache to disk

**ID:** `core-framework-3-task-003`  
**Sprint:** `core-framework-3`  
**Type:** development  
**Status:** ✅ Completed  
**Priority:** 🟡 Medium  

## Description

Implement optional disk-based cache persistence for faster startup.

Cache Files (.vibey/.cache/, gitignored):
- task_index.json (id -> file_path mapping)
- sprint_index.json
- track_index.json
- dep_graph.json (pre-computed adjacency list)
- reverse_dep_graph.json
- last_scan.txt (timestamp of last full scan)

Features:
- Load cache from disk on startup if valid
- Check file mtimes to detect changes
- Rebuild cache if any files changed
- Write cache to disk after rebuild
- Add .vibey/.cache/ to .gitignore

Benefits:
- Startup time: < 10ms (vs 100ms rebuilding)
- Cross-invocation optimization
- Warm cache on first command


## Details

- **Estimated Tokens:** 1
- **Complexity:** medium

## Timeline

- **Created:** 2025-11-08 10:10 UTC
- **Completed:** 2025-11-08 15:15 UTC

---

*Generated from task.yaml on 2025-11-09 19:14 UTC*
