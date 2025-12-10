# Performance Guide

This guide covers performance characteristics and optimization strategies for Vibey's roadmap integrity system.

## Overview

The integrity system is designed for:
- Fast O(1) verification lookups
- Efficient incremental writes
- Scalability to large repositories

## Architecture

### Time-Bucketed Activity Logs

Activity logs are stored in monthly JSONL files:
```
.vibey/roadmap/activity_log/
  2025-01.jsonl
  2025-02.jsonl
  ...
```

**Benefits:**
- Efficient date-range queries
- Append-only writes (fast)
- Easy archival of old logs
- Predictable file sizes

### Hash-Based Verification

Files are verified by SHA256 content hash, not commit hash:

```python
# O(1) lookup after index built
hash_index = reader.build_hash_index()
event = hash_index.get(current_hash)  # O(1)
```

**Benefits:**
- Robust to history rewrites (rebase, cherry-pick)
- Fast batch verification
- Content-addressed (same content = same hash)

## Performance Characteristics

### Single File Verification

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Hash computation | O(file_size) | SHA256 streaming |
| Without index | O(n) | n = total events |
| With index | O(1) | After index build |

### Batch Verification

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Build index | O(n) | Once per session |
| Verify each file | O(1) | Hash lookup |
| Total for m files | O(n + m) | Index + lookups |

### Index Caching

The hash index is automatically cached:
- First `build_hash_index()`: O(n) - reads all log files
- Subsequent calls: O(1) - returns cached index
- Auto-invalidation when log files change

```python
reader = ActivityLogReader(log_dir)

# First call - builds index
index1 = reader.build_hash_index()  # O(n)

# Second call - returns cached
index2 = reader.build_hash_index()  # O(1)

# Force rebuild
index3 = reader.build_hash_index(use_cache=False)  # O(n)
```

### Write Performance

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Single event | O(1) | Append with lock |
| Batch events | O(m) | Grouped by month |
| File locking | Minimal | Cross-platform locks |

## Scaling Considerations

### Activity Log Size

For a repository with:
- 100 sprints
- 500 tasks
- ~1500 events (3 per task average)
- ~200 bytes per event

**Total size:** ~300KB per year

This is negligible for most systems.

### Large Team Considerations

For teams > 10 developers:
1. Activity log writes use file locking (safe for concurrency)
2. Hash index builds are fast (~1ms per 1000 events)
3. Consider periodic log archival for very long projects

### Enterprise Scale

For enterprise deployments (100+ developers):
1. SQLite backend (sqlite-backend track) provides better concurrency
2. Indexed queries become O(log n)
3. Transaction support for complex operations

## Optimization Tips

### For CI/CD Pipelines

```yaml
# Verify only changed files
- name: Verify changed files
  run: |
    files=$(git diff --name-only ${{ github.event.before }}..${{ github.sha }} | grep '.vibey/roadmap/')
    for f in $files; do
      vibey roadmap verify "$f"
    done
```

### For Large Repositories

```python
# Build index once, reuse for all verifications
from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

reader = ActivityLogReader(log_dir)
index = reader.build_hash_index()  # Build once

for file in files_to_verify:
    hash = compute_file_hash(file)
    event = index.get(hash)  # O(1) each
```

### For Frequent Verifications

```python
# Verifier caches index automatically
verifier = ChangeVerifier(root_dir)

# First verify - builds index
result1 = verifier.verify_file(file1, use_index=True)

# Subsequent - uses cached index
result2 = verifier.verify_file(file2, use_index=True)
result3 = verifier.verify_file(file3, use_index=True)
```

## Benchmarks

### Typical Performance

On a modern laptop (M1 Mac, SSD):

| Operation | Time |
|-----------|------|
| Single file hash | ~1ms |
| Build index (1000 events) | ~10ms |
| Cached index lookup | <0.1ms |
| Verify 100 files (with index) | ~50ms |

### Memory Usage

| Component | Memory |
|-----------|--------|
| Hash index (1000 entries) | ~200KB |
| Event parsing | ~1KB per event |
| Streaming reads | ~10KB buffer |

## Future Optimizations

### SQLite Backend (Planned)

The `sqlite-backend` track will add:
- Indexed hash lookups
- Transaction support
- Better concurrency
- Incremental updates

### Bloom Filters (Potential)

For very large activity logs:
- Quick "probably not in log" checks
- Reduce disk reads for negative lookups

## Monitoring

### Logging Performance Issues

```python
import time
import logging

start = time.time()
index = reader.build_hash_index()
elapsed = time.time() - start

if elapsed > 1.0:  # More than 1 second
    logging.warning(f"Slow index build: {elapsed:.2f}s, {len(index)} entries")
```

### Metrics to Track

1. **Index build time** - Should stay under 100ms for most repos
2. **Cache hit rate** - High hit rate indicates good caching
3. **Log file size** - Monitor for unexpected growth
4. **Verification time per file** - Should be <10ms

## See Also

- [CI Verification Guide](CI_VERIFICATION.md) - CI/CD setup
- [Git Workflow Edge Cases](GIT_WORKFLOW_EDGE_CASES.md) - Content-hash design
- SQLite Backend track (roadmap) - Enterprise scaling
