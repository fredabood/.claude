# Task 10: Audit Roadmap State for Orphans and Broken References

**Task ID**: `01KDDE9NEKAH3BM9PRFPHNNCNC`
**Type**: research
**Priority**: high
**Estimated Tokens**: 3,000

## Objective

Check for orphan entities (tasks without valid sprints, sprints without valid tracks), broken references (blocked_by/depends_on pointing to nonexistent IDs), and structural integrity issues.

## Methodology

### Step 1: Find Orphan Tasks (No Valid Sprint)

```sql
-- Tasks with missing or invalid sprint_id
SELECT t.id, t.title, t.sprint_id
FROM tasks t
LEFT JOIN sprints s ON t.sprint_id = s.id
WHERE s.id IS NULL;

-- Tasks with empty sprint_id
SELECT id, title FROM tasks WHERE sprint_id IS NULL OR sprint_id = '';
```

### Step 2: Find Orphan Sprints (No Valid Track)

```sql
-- Sprints with missing or invalid track_id
SELECT s.id, s.name, s.track_id
FROM sprints s
LEFT JOIN tracks t ON s.track_id = t.id
WHERE t.id IS NULL;

-- Sprints with empty track_id
SELECT id, name FROM sprints WHERE track_id IS NULL OR track_id = '';
```

### Step 3: Find Broken blocked_by References

```sql
-- Check tasks table
SELECT t.id, t.title, 'blocked_by' as ref_type, bb.value as ref_id
FROM tasks t, json_each(t.blocked_by) bb
WHERE NOT EXISTS (SELECT 1 FROM tasks t2 WHERE t2.id = bb.value)
AND NOT EXISTS (SELECT 1 FROM sprints s WHERE s.id = bb.value);

-- Check sprints table
SELECT s.id, s.name, 'blocked_by' as ref_type, bb.value as ref_id
FROM sprints s, json_each(s.blocked_by) bb
WHERE NOT EXISTS (SELECT 1 FROM sprints s2 WHERE s2.id = bb.value)
AND NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id = bb.value);
```

### Step 4: Find Broken depends_on References

```sql
-- Similar to blocked_by
SELECT t.id, t.title, 'depends_on' as ref_type, d.value as ref_id
FROM tasks t, json_each(t.depends_on) d
WHERE NOT EXISTS (SELECT 1 FROM tasks t2 WHERE t2.id = d.value)
AND NOT EXISTS (SELECT 1 FROM sprints s WHERE s.id = d.value);
```

### Step 5: Check for Circular Dependencies

```python
# Python script to detect cycles
import sqlite3
from collections import defaultdict

def find_cycles(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build dependency graph
    graph = defaultdict(list)
    cursor.execute("SELECT id, blocked_by FROM tasks WHERE blocked_by != '[]'")
    for task_id, blocked_by in cursor.fetchall():
        import json
        deps = json.loads(blocked_by)
        for dep in deps:
            graph[task_id].append(dep)

    # DFS to find cycles
    visited = set()
    rec_stack = set()
    cycles = []

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor, path + [neighbor])
            elif neighbor in rec_stack:
                cycles.append(path[path.index(neighbor):] + [neighbor])
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [node])

    return cycles
```

### Step 6: Verify .id File Mappings

```bash
# Check all .id files point to existing entities
for id_file in $(find .vibey/roadmap -name ".id"); do
    while IFS=: read slug ulid; do
        if ! sqlite3 .vibey/roadmap.db "SELECT 1 FROM tasks WHERE id='$ulid' UNION SELECT 1 FROM sprints WHERE id='$ulid' UNION SELECT 1 FROM tracks WHERE id='$ulid'" | grep -q 1; then
            echo "BROKEN .id MAPPING: $slug -> $ulid (in $id_file)"
        fi
    done < "$id_file"
done
```

### Step 7: Find Invalid Parent References in YAML

```bash
# Check YAML files for parent_ref (v2 format issues)
grep -r "parent_ref:" .vibey/roadmap/tasks/*.yaml | while read line; do
    echo "V2 FORMAT REMNANT: $line"
done
```

### Step 8: Database vs YAML Consistency

```bash
# Count entities
yaml_tracks=$(ls .vibey/roadmap/tracks/*.yaml 2>/dev/null | wc -l)
yaml_sprints=$(ls .vibey/roadmap/sprints/*.yaml 2>/dev/null | wc -l)
yaml_tasks=$(ls .vibey/roadmap/tasks/*.yaml 2>/dev/null | wc -l)

db_tracks=$(sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM tracks")
db_sprints=$(sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM sprints")
db_tasks=$(sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM tasks")

echo "Tracks: YAML=$yaml_tracks, DB=$db_tracks"
echo "Sprints: YAML=$yaml_sprints, DB=$db_sprints"
echo "Tasks: YAML=$yaml_tasks, DB=$db_tasks"
```

## Expected Output

```markdown
## Roadmap State Audit Results

### Orphan Entities
| Type | ID | Title | Missing Reference |
|------|-----|-------|-------------------|
| Task | 01K... | Widget impl | sprint_id invalid |
| Sprint | 01K... | Sprint 5 | track_id invalid |

### Broken References
| Entity | Field | References | Status |
|--------|-------|------------|--------|
| 01K... | blocked_by | 01KXXX | ID not found |

### Circular Dependencies
| Cycle | Entities |
|-------|----------|
| 1 | A -> B -> C -> A |

### .id File Issues
| File | Slug | ULID | Issue |
|------|------|------|-------|
| tasks/.id | my-task | 01K... | ULID not in DB |

### YAML/DB Consistency
| Entity | YAML | Database | Diff |
|--------|------|----------|------|
| Tracks | 25 | 25 | 0 |
| Sprints | 200 | 198 | +2 |
| Tasks | 1600 | 1595 | +5 |
```

## Success Criteria

- [ ] Orphan tasks identified
- [ ] Orphan sprints identified
- [ ] Broken blocked_by references found
- [ ] Broken depends_on references found
- [ ] Circular dependencies detected
- [ ] .id file mappings verified
- [ ] YAML/DB consistency checked

## Tools

- SQLite CLI
- Python (for cycle detection)
- Bash (for file checks)

## Deliverables

1. `roadmap-state-audit-results.json` - Structured findings
2. Fix scripts for common issues
3. Summary section for final report
