# CLI Bugs Found During Roadmap Verification (2025-12-10)

## Bug #15: Database Init Uses Wrong Path for roadmap.yaml

**Status:** FIXED
**Severity:** Critical
**Found:** 2025-12-10
**Fixed:** 2025-12-10

### Description

The database init command (`vibey roadmap db init` / `rebuild`) looked for `roadmap.yaml` at the OLD deprecated location instead of the canonical location.

### Actual Location (Correct)
```
.vibey/roadmap/roadmap.yaml
```

### Expected by Code (Wrong)
```
.vibey/roadmap.yaml
```

### Root Cause

In `vibey/cli/commands.py` line 1826:
```python
# OLD (wrong)
roadmap_yaml = vibey_dir / "roadmap.yaml"

# NEW (fixed)
roadmap_yaml = vibey_dir / "roadmap" / "roadmap.yaml"
```

### Fix Applied

Changed line 1826-1827 in `vibey/cli/commands.py`:
```python
# Canonical location is .vibey/roadmap/roadmap.yaml (not .vibey/roadmap.yaml)
roadmap_yaml = vibey_dir / "roadmap" / "roadmap.yaml"
```

---

## Bug #16: Database Loader Expects Hierarchical Structure

**Status:** OPEN
**Severity:** High
**Found:** 2025-12-10

### Description

The `_load_roadmap_to_db()` function in `vibey/cli/commands.py` expects the OLD hierarchical directory structure but the actual roadmap uses flat ULID structure.

### Current Structure (Actual)
```
.vibey/roadmap/
├── roadmap.yaml
├── tracks/
│   ├── .id                    # slug→ULID mapping
│   ├── 01KC2D0JK06MN77ZHAGAHF5VKB.yaml  # aider-port
│   └── ...
├── sprints/
│   ├── .id                    # slug→ULID mapping
│   └── {ulid}.yaml
└── tasks/
    ├── .id                    # slug→ULID mapping
    └── {ulid}.yaml
```

### Expected Structure (Code Expects)
```
.vibey/roadmap/
├── roadmap.yaml
├── aider-port/              # track slug directory
│   ├── track.yaml
│   ├── sprint-1/           # sprint directory
│   │   ├── sprint.yaml
│   │   └── task-001/       # task directory
│   │       └── task.yaml
```

### Root Cause

In `_load_roadmap_to_db()` (lines 1913-1918):
```python
for track_summary in roadmap.tracks:
    track_dir = roadmap_dir / track_summary.id  # Looks for roadmap/track-slug/
    track_yaml = track_dir / "track.yaml"       # Looks for track.yaml in that dir

    if not track_yaml.exists():  # Always fails with flat structure
        continue
```

### Impact

- Database cannot be populated from YAML files
- `vibey roadmap db rebuild` results in 0 tracks, 0 sprints, 0 tasks
- Users must use YAML backend (no SQLite database file)

### Workaround

Delete or rename the `.vibey/roadmap.db` file to force YAML backend:
```bash
mv .vibey/roadmap.db .vibey/roadmap.db.disabled
```

### Proposed Fix

Update `_load_roadmap_to_db()` to:
1. Read the `.id` mapping file to get slug→ULID mappings
2. Look for track files at `roadmap/tracks/{ulid}.yaml`
3. Look for sprint files at `roadmap/sprints/{ulid}.yaml`
4. Look for task files at `roadmap/tasks/{ulid}.yaml`

---

## Bug #17: Track IDs Display as ULIDs Instead of Slugs

**Status:** OPEN
**Severity:** Low
**Found:** 2025-12-10

### Description

The `vibey roadmap status` command displays track IDs as ULIDs instead of human-readable slugs.

### Actual Output
```
📊 Tracks: 39

🔵 01KC2D0JK06MN77ZHAGAHF5VKB
   Aider Platform Port
   Progress: 8/8 tasks (100%)
```

### Expected Output
```
📊 Tracks: 39

🔵 aider-port
   Aider Platform Port
   Progress: 8/8 tasks (100%)
```

### Root Cause

The `format_roadmap_summary()` function in `vibey/cli/formatters.py` displays `track.get('id')` which is the ULID from the YAML file, not the human-readable slug.

### Proposed Fix

1. Store both `id` (ULID) and `slug` in track data
2. Display slug in status output, use ULID internally for file lookups
3. Or: Load the `.id` mapping file and reverse-lookup slug from ULID

---

## Summary

| Bug | Title | Severity | Status |
|-----|-------|----------|--------|
| #15 | Database init uses wrong path | Critical | FIXED |
| #16 | Database loader expects hierarchical structure | High | OPEN |
| #17 | Track IDs display as ULIDs | Low | OPEN |
