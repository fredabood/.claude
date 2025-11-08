# Architecture Decision: Text Files vs Database for Roadmap Storage

**Decision Date:** 2025-11-07
**Status:** ✅ Decided - Text Files with Caching Layer
**Deciders:** Vibey Framework Team

---

## Context and Problem Statement

The roadmap system uses YAML files in a graph-database-like pattern to manage project state:
- 4-tier hierarchy (Roadmap → Track → Sprint → Task)
- Complex dependency graphs
- Frequent queries and updates
- Agent-driven workflows

**Question:** Should we migrate from text files to a database (SQLite, PostgreSQL) for better performance and data integrity?

---

## Decision Drivers

### 1. Use Case Alignment
- **Primary users:** AI coding assistants (Claude Code, Goose, Cursor)
- **Workflow:** Read files → understand context → make changes
- **Integration:** Git-based version control is core to developer workflows

### 2. Multi-Platform Strategy
- Framework must work across Claude Code, Goose, Cursor
- All platforms prefer text files over databases
- Portability is a critical requirement

### 3. Scale Expectations
- **Typical project:** 4-10 tracks, 16-50 sprints, 50-200 tasks
- **Large project:** 10-20 tracks, 50-100 sprints, 200-500 tasks
- **Even at 500 tasks:** Linear scan < 200ms on modern hardware

### 4. Developer Experience
- Developers expect to see diffs in PRs
- Git blame, history, and branches are essential tools
- Transparent state (just cat a file to debug)

---

## Decision Outcome

**Chosen option:** Text Files (YAML) with In-Memory Caching Layer

### Rationale

#### Git-Native (Non-Negotiable) ⭐
- **Strength:** Version control works perfectly
  - Human-readable diffs
  - Branch-per-sprint workflows
  - Merge conflicts are understandable
  - Git blame shows who changed what
  - No binary file issues

- **Database weakness:** Binary files don't diff/merge
  - Conflicts require special tools
  - History not human-readable
  - Branch workflows break down

#### AI-Assistant-Native 🤖
- **Strength:** Claude/Goose/Cursor all read text files naturally
  - No serialization needed for context
  - Files are already in LLM context
  - Platform agnostic
  - No query translation layer

- **Database weakness:** State not in context by default
  - Need to export/serialize for AI
  - Platform coupling
  - Harder to port across assistants

#### Zero Setup 🚀
- **Strength:** Works immediately
  - No server, no migrations, no connections
  - Just Python + PyYAML
  - Works offline by default
  - Clone repo → works immediately

- **Database weakness:** Setup overhead
  - Schema migrations
  - Connection management
  - Version compatibility
  - Debugging requires DB tools

#### Transparency 👁️
- **Strength:** Direct file access
  - Developers can read/edit directly
  - Changes visible in git diff
  - Easy to debug (cat the file)
  - No schema migrations needed

- **Database weakness:** Opaque state
  - Need special tools to inspect
  - Schema changes require migrations
  - Debugging harder

#### Portability 📦
- **Strength:** Universal
  - Backup = copy directory
  - Works on any platform
  - No version compatibility issues
  - Easy to archive/restore

- **Database weakness:** Dependency complexity
  - SQLite minimum (adds dependency)
  - Or server (PostgreSQL, etc.)
  - Version compatibility issues

### Performance Analysis

**Current Scale (200 tasks):**
- Linear file scan: < 100ms
- Context loading queries: < 200ms total
- Most queries are by ID: Fast even without DB
- Graph traversal (rare): < 300ms

**Database Threshold:**
- Becomes compelling at: 1,000+ tasks, 100+ sprints
- Most real projects won't hit this (90%+ under 200 tasks)
- Vibey's own roadmap: ~53 tasks

**Caching Mitigation:**
- In-memory cache eliminates repeated file reads
- First query: ~100ms (build index)
- Subsequent queries: < 5ms (O(1) lookups)
- Cache invalidation on file changes

### Trade-offs

**What we gain:**
- ✅ Git-friendly workflows
- ✅ AI-assistant compatibility
- ✅ Zero setup complexity
- ✅ Complete transparency
- ✅ Universal portability
- ✅ Human-readable state

**What we lose:**
- ❌ ACID guarantees (but not needed for single-user workflows)
- ❌ Indexed queries (but caching solves this)
- ❌ Referential integrity enforcement (but validation handles this)
- ❌ Concurrent access (but rare in single-developer projects)

**What we mitigate with caching:**
- ✅ Performance (in-memory index)
- ✅ Query optimization (pre-computed graphs)
- ✅ Repeated reads (cache hits)

---

## Implementation: Caching Layer

### Design

```python
class RoadmapCache:
    """In-memory index for fast lookups"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

        # Indexes (lazy-loaded)
        self._task_index: Dict[str, Path] = {}          # id -> file_path
        self._sprint_index: Dict[str, Path] = {}        # id -> file_path
        self._track_index: Dict[str, Path] = {}         # id -> file_path

        # Pre-computed graphs (built on first query)
        self._dep_graph: Optional[Dict] = None          # Adjacency list
        self._reverse_dep_graph: Optional[Dict] = None  # Reverse edges

        # File modification tracking
        self._file_mtimes: Dict[Path, float] = {}

        # Cache statistics
        self._hits = 0
        self._misses = 0

    def get_task(self, task_id: str) -> Optional[Dict]:
        """O(1) lookup after first load"""
        if task_id in self._task_index:
            self._hits += 1
            return self._load_yaml(self._task_index[task_id])

        # Cache miss - scan and update index
        self._misses += 1
        self._build_task_index()
        return self._task_index.get(task_id)

    def invalidate(self, file_path: Path = None):
        """Invalidate cache on file changes"""
        if file_path:
            # Partial invalidation
            if file_path in self._file_mtimes:
                del self._file_mtimes[file_path]
        else:
            # Full invalidation
            self._task_index.clear()
            self._sprint_index.clear()
            self._track_index.clear()
            self._dep_graph = None
            self._reverse_dep_graph = None
            self._file_mtimes.clear()
```

### Cache Files (Optional, Gitignored)

```
.vibey/.cache/
  task_index.json      # id -> file_path mapping
  dep_graph.json       # Pre-computed adjacency list
  last_scan.txt        # Timestamp of last full scan
```

**Benefits:**
- Persist cache across CLI invocations
- Even faster startup (< 10ms)
- Rebuild only if files changed

**Trade-offs:**
- Need to detect file changes (mtime)
- Cache can become stale
- Add .cache/ to .gitignore

### Performance Targets

| Operation | Without Cache | With Cache | Target |
|-----------|--------------|------------|---------|
| Find task by ID | O(n) ~100ms | O(1) ~5ms | < 50ms |
| Load all tasks | O(n) ~150ms | O(1) ~10ms | < 100ms |
| Dependency graph | O(n²) ~300ms | O(1) ~20ms | < 200ms |
| Reverse deps | O(n²) ~300ms | O(1) ~20ms | < 200ms |

### Cache Invalidation Strategy

**On file write:**
```python
def update_task(task_id: str, updates: Dict):
    # Update YAML file
    save_yaml(file_path, data)

    # Invalidate cache for this file
    cache.invalidate(file_path)
```

**On CLI startup:**
```python
def check_cache_validity():
    # Check if any files modified since last cache build
    for file_path in roadmap_files:
        cached_mtime = cache.get_mtime(file_path)
        actual_mtime = file_path.stat().st_mtime

        if actual_mtime > cached_mtime:
            cache.invalidate(file_path)
```

---

## Alternative Considered: SQLite

### What It Would Look Like

```sql
-- Tables
CREATE TABLE roadmaps (id TEXT PRIMARY KEY, ...);
CREATE TABLE tracks (id TEXT PRIMARY KEY, roadmap_id TEXT, ...);
CREATE TABLE sprints (id TEXT PRIMARY KEY, track_id TEXT, ...);
CREATE TABLE tasks (id TEXT PRIMARY KEY, sprint_id TEXT, ...);
CREATE TABLE dependencies (
    source_id TEXT,
    target_id TEXT,
    type TEXT,
    PRIMARY KEY (source_id, target_id)
);

-- Indexes
CREATE INDEX idx_task_sprint ON tasks(sprint_id);
CREATE INDEX idx_sprint_track ON sprints(track_id);
CREATE INDEX idx_track_roadmap ON tracks(roadmap_id);
CREATE INDEX idx_dep_source ON dependencies(source_id);
CREATE INDEX idx_dep_target ON dependencies(target_id);
```

### Hybrid Approach (Dual Source)

```python
# Write to SQLite for performance
db.execute("UPDATE tasks SET status = ?", (status, task_id))

# Export to YAML on every change
export_to_yaml(db, ".vibey/")

# Git commits YAML files
# SQLite db is gitignored
```

**Problem:** Two sources of truth
- Which is authoritative?
- What if export fails?
- Complexity of keeping in sync

### Why We Rejected It

1. **Git-hostile** - Binary files break core workflows
2. **AI-unfriendly** - Need to serialize state for context
3. **Complexity** - Schema migrations, sync logic
4. **Premature optimization** - Not needed at current scale
5. **Platform coupling** - Harder to port to other assistants

---

## When to Reconsider Database

### Trigger Conditions

**Scale:**
- 1,000+ tasks across 100+ sprints
- Query performance degradation (> 500ms)
- File system performance issues

**Concurrency:**
- Multiple users editing simultaneously
- Conflict resolution becomes painful
- Need real-time collaboration

**Query Complexity:**
- Need joins, aggregations, complex filters
- Graph algorithms beyond simple BFS/DFS
- Real-time analytics on roadmap state

**Data Integrity:**
- ACID guarantees become critical
- Referential integrity failures causing issues
- Validation overhead becomes prohibitive

### Migration Path

If we hit these conditions:

**Phase 1: SQLite Backend (Optional)**
```bash
# Default: YAML files
roadmap status

# Opt-in to SQLite backend
roadmap --backend sqlite status
```

**Phase 2: Dual-Write**
- Write to both YAML and SQLite
- YAML remains source of truth
- SQLite for performance

**Phase 3: SQLite Primary**
- SQLite becomes source of truth
- Export YAML for git commits
- YAML becomes read-only view

**Phase 4: Consider PostgreSQL**
- Only if multi-user collaboration needed
- Hosted database for team access
- Keep YAML export for portability

---

## Consequences

### Positive

✅ **Git workflows work perfectly** - Diffs, merges, blame, history
✅ **AI assistants work natively** - No serialization layer
✅ **Zero setup friction** - Clone and run
✅ **Complete transparency** - Just read the files
✅ **Platform portability** - Works everywhere
✅ **Performance is acceptable** - With caching, meets targets

### Negative

❌ **Manual validation required** - No database constraints
❌ **No ACID guarantees** - Risk of partial updates (mitigated by atomic writes)
❌ **Concurrent access needs locking** - File locks for multi-user (rare)
❌ **Scale ceiling** - Won't work for 10,000+ tasks (but not needed)

### Neutral

⚖️ **Caching complexity** - Need to implement, but worth it
⚖️ **Query API** - Custom Python instead of SQL
⚖️ **File system dependent** - Performance varies by FS (but acceptable)

---

## Validation

### Success Metrics

**Performance (with caching):**
- [ ] Task lookup: < 50ms
- [ ] Load all tasks: < 100ms
- [ ] Dependency graph: < 200ms
- [ ] 90th percentile: < 300ms

**Developer Experience:**
- [ ] Git diff shows meaningful changes
- [ ] Merge conflicts are understandable
- [ ] No special tools needed to inspect state
- [ ] AI assistants can read state naturally

**Portability:**
- [ ] Works on Claude Code ✅
- [ ] Works on Goose (when ported)
- [ ] Works on Cursor (when ported)
- [ ] No platform-specific dependencies

### Benchmarking Plan

```bash
# Test with real Vibey roadmap (53 tasks)
time roadmap status          # Target: < 100ms
time roadmap list tasks      # Target: < 100ms
time roadmap deps --all      # Target: < 200ms
time roadmap context task-X  # Target: < 300ms

# Test with synthetic large roadmap (500 tasks)
./scripts/generate-test-roadmap.py --tasks 500
time roadmap status          # Target: < 200ms
time roadmap list tasks      # Target: < 200ms
time roadmap deps --all      # Target: < 500ms
```

---

## Related Decisions

- **YAML vs JSON**: Chose YAML for human-readability (see ROADMAP_OBJECT_HIERARCHY.md)
- **File Structure**: Separate files per sprint for merge-friendliness
- **Context Loading**: Hierarchical loading to manage large dependency graphs
- **Validation Strategy**: On-demand validation rather than constraint enforcement

---

## References

- **Design Document:** `ROADMAP_OBJECT_HIERARCHY.md`
- **Implementation Plan:** `ROADMAP_IMPLEMENTATION_PLAN.md`
- **Context Loading Strategy:** `CONTEXT_LOADING_STRATEGY.md`
- **Multi-Platform Roadmap:** `FRAMEWORK_ROADMAP.md`

---

## Notes

### Why This Decision Matters

The storage backend choice affects:
1. **Git workflows** - Core to developer experience
2. **AI integration** - Core to Vibey's value proposition
3. **Platform portability** - Core to multi-platform strategy
4. **Dogfooding** - Vibey manages itself with this system

Getting this wrong would undermine all four pillars.

### Lessons from Similar Systems

**Make (Makefile):** Text files, git-friendly, 40+ years strong
**Docker Compose (YAML):** Text files, works across platforms
**Kubernetes (YAML):** Text files, scales to 1,000s of resources
**Terraform (HCL):** Text files, manages complex infrastructure

**Pattern:** Declarative configuration + text files = developer-friendly

### Future Considerations

If we see performance issues at scale:
1. First: Profile and optimize current implementation
2. Second: Add caching layer (this decision)
3. Third: Consider optional SQLite backend
4. Last resort: Require database (only if multi-user needed)

Premature optimization is the root of all evil - Donald Knuth

---

**Decision finalized:** 2025-11-07
**Implementation target:** Core Framework Sprint 3 (Performance Optimization)
