# Sprint 1: Task Extraction - Task Plans

**Sprint ID**: `01KC7H29E0Z5BC7HK1CK222153`
**Track**: Embedded Task Migration
**Priority**: CRITICAL

---

## Task 001: Create embedded task extraction script

**Task ID**: `01KC7H29E0Z5BC7HK1CK222158`
**Estimated Tokens**: 50,000
**Complexity**: Complex

### Objective
Create a Python script that extracts all 1,330 embedded tasks from 202 sprint YAML files to standalone task files.

### Implementation Plan

#### Step 1: Script Structure
```
vibey/operations/migrations/extract_embedded_tasks.py
```

```python
"""
Extract Embedded Tasks to Standalone Files

Scans sprint YAML files for embedded tasks[] arrays and creates
standalone task files in .vibey/roadmap/tasks/{ulid}.yaml
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
from ulid import ULID
import yaml
import shutil

class EmbeddedTaskExtractor:
    def __init__(self, roadmap_dir: Path, dry_run: bool = True):
        self.roadmap_dir = roadmap_dir
        self.sprints_dir = roadmap_dir / "sprints"
        self.tasks_dir = roadmap_dir / "tasks"
        self.dry_run = dry_run
        self.slug_to_ulid: Dict[str, str] = {}
        self.stats = {"extracted": 0, "skipped": 0, "errors": []}

    def load_existing_mappings(self) -> None:
        """Load slug -> ULID mappings from existing task files."""
        pass

    def extract_all(self) -> Dict:
        """Extract all embedded tasks."""
        pass

    def extract_from_sprint(self, sprint_file: Path) -> int:
        """Extract tasks from a single sprint file."""
        pass

    def convert_to_standalone(self, embedded: Dict, sprint_id: str,
                              track_id: str) -> Dict:
        """Convert embedded task format to standalone format."""
        pass
```

#### Step 2: Key Functions

**load_existing_mappings()**
- Scan all `tasks/*.yaml` files
- Build dict: `{slug: ulid}` from task files with slug field
- Build dict: `{id: filepath}` for duplicate detection

**extract_from_sprint()**
```python
def extract_from_sprint(self, sprint_file: Path) -> int:
    data = yaml.safe_load(sprint_file.read_text())
    sprint = data.get('sprint', {})
    embedded_tasks = sprint.get('tasks', [])

    if not embedded_tasks:
        return 0

    sprint_id = sprint['id']
    track_id = sprint['track_id']
    extracted = 0

    for task in embedded_tasks:
        task_id = task.get('id', '')

        # Check if already exists as standalone
        if self._standalone_exists(task_id):
            self.stats['skipped'] += 1
            continue

        # Generate ULID for legacy slug IDs
        if not self._is_ulid(task_id):
            new_ulid = str(ULID())
            slug = task_id
        else:
            new_ulid = task_id
            slug = task.get('slug')

        standalone = self.convert_to_standalone(
            task, sprint_id, track_id, new_ulid, slug
        )

        if not self.dry_run:
            task_path = self.tasks_dir / f"{new_ulid}.yaml"
            task_path.write_text(yaml.dump({'task': standalone}))

        extracted += 1

    return extracted
```

**convert_to_standalone()**
```python
def convert_to_standalone(self, embedded: Dict, sprint_id: str,
                          track_id: str, ulid: str, slug: str) -> Dict:
    return {
        'id': ulid,
        'sprint_id': sprint_id,
        'track_id': track_id,
        'roadmap_id': 'vibey-framework-v2',
        'task_type': embedded.get('task_type', 'development'),
        'title': embedded.get('title') or embedded.get('name', 'Untitled'),
        'description': embedded.get('description', ''),
        'status': embedded.get('status', 'not_started'),
        'blocked': embedded.get('blocked', False),
        'created': embedded.get('created', datetime.now(timezone.utc).isoformat()),
        'started': embedded.get('started'),
        'completed': embedded.get('completed'),
        'assigned_agent': embedded.get('assigned_agent'),
        'priority': embedded.get('priority', 'medium'),
        'phase_label': embedded.get('phase_label'),
        'estimated_tokens': embedded.get('estimated_tokens', 10000),
        'actual_tokens': embedded.get('actual_tokens'),
        'complexity': embedded.get('complexity', 'medium'),
        'gate_info': embedded.get('gate_info'),
        'audit_results': embedded.get('audit_results'),
        'dependencies': [],
        'blocked_by': [],
        'depends_on': [],
        'depended_on_by': [],
        'deliverables': [],
        'commits': [],
        'metadata': {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'token_efficiency': None,
            'duration_hours': None
        },
        'slug': slug,
        'parent_ref': sprint_id,
        'criteria': [],
        'sequence': embedded.get('sequence', 1)
    }
```

#### Step 3: CLI Integration
Add to `vibey/cli/commands.py`:
```python
@roadmap.command("extract-embedded")
@click.option("--dry-run/--execute", default=True)
def extract_embedded_cmd(dry_run: bool):
    """Extract embedded tasks to standalone files."""
    from vibey.operations.migrations.extract_embedded_tasks import (
        EmbeddedTaskExtractor
    )
    extractor = EmbeddedTaskExtractor(
        roadmap_dir=Path(".vibey/roadmap"),
        dry_run=dry_run
    )
    result = extractor.extract_all()
    # Print results...
```

### Acceptance Criteria
- [ ] Script handles all edge cases (missing fields, legacy formats)
- [ ] Dry-run mode shows what would be created without modifying files
- [ ] Backup created before any modifications
- [ ] Comprehensive logging of all operations
- [ ] Error handling for malformed YAML

### Files to Create/Modify
- `vibey/operations/migrations/extract_embedded_tasks.py` (NEW)
- `vibey/cli/commands.py` (ADD command)

---

## Task 002: Build slug to ULID mapping for embedded tasks

**Task ID**: `01KC7H29E0Z5BC7HK1CK222159`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Build comprehensive mapping from legacy slug-based task IDs to ULIDs.

### Implementation Plan

#### Step 1: Scan Existing Task Files
```python
def build_slug_mapping(tasks_dir: Path) -> Dict[str, str]:
    """Build slug -> ULID mapping from existing tasks."""
    mapping = {}

    for task_file in tasks_dir.glob("*.yaml"):
        data = yaml.safe_load(task_file.read_text())
        task = data.get('task', {})

        task_id = task.get('id', '')
        slug = task.get('slug', '')

        if slug:
            mapping[slug] = task_id

        # Also map id -> id for existing ULIDs
        mapping[task_id] = task_id

    return mapping
```

#### Step 2: Scan Embedded Tasks for Unknown Slugs
```python
def find_unmapped_slugs(sprints_dir: Path, mapping: Dict) -> List[str]:
    """Find slugs in embedded tasks that aren't mapped."""
    unmapped = []

    for sprint_file in sprints_dir.glob("*.yaml"):
        data = yaml.safe_load(sprint_file.read_text())
        for task in data.get('sprint', {}).get('tasks', []):
            task_id = task.get('id', '')
            if task_id and task_id not in mapping:
                unmapped.append(task_id)

    return unmapped
```

#### Step 3: Persist Mapping
```python
def save_mapping(mapping: Dict, output_path: Path):
    """Save mapping to JSON file for future reference."""
    import json
    with open(output_path, 'w') as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
```

### Acceptance Criteria
- [ ] All existing task slugs mapped
- [ ] Unmapped slugs identified
- [ ] Mapping persisted to JSON file
- [ ] Mapping used by extraction script

### Files to Create
- `.vibey/roadmap/context/task_slug_mapping.json`

---

## Task 003: Execute extraction for all 1,330 embedded tasks

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215A`
**Estimated Tokens**: 30,000
**Complexity**: Medium
**Blocked By**: Task 001, Task 002

### Objective
Run the extraction script to create standalone files for all embedded tasks.

### Execution Plan

#### Step 1: Pre-flight Checks
```bash
# 1. Verify current state
ls -la .vibey/roadmap/tasks/*.yaml | wc -l  # Should be ~1129

# 2. Count embedded tasks
python3 -c "
import yaml
from pathlib import Path
total = 0
for f in Path('.vibey/roadmap/sprints').glob('*.yaml'):
    data = yaml.safe_load(f.read_text())
    tasks = data.get('sprint', {}).get('tasks', [])
    total += len(tasks)
print(f'Embedded tasks: {total}')
"
```

#### Step 2: Dry Run
```bash
vibey roadmap extract-embedded --dry-run
```

Review output:
- Tasks to be created
- Slugs to be mapped
- Any warnings/errors

#### Step 3: Create Backup
```bash
# Full backup of roadmap directory
cp -r .vibey/roadmap .vibey/roadmap.backup.$(date +%Y%m%d_%H%M%S)
```

#### Step 4: Execute
```bash
vibey roadmap extract-embedded --execute
```

#### Step 5: Verify
```bash
# Count new task files
ls -la .vibey/roadmap/tasks/*.yaml | wc -l  # Should be ~2459

# Verify specific tracks
sqlite3 .vibey/roadmap.db "
SELECT t.name, COUNT(tk.id) as tasks
FROM tracks t
JOIN sprints s ON s.track_id = t.id
JOIN tasks tk ON tk.sprint_id = s.id
WHERE t.name IN ('Goose Platform Port', 'JetBrains Port')
GROUP BY t.name;
"
```

### Acceptance Criteria
- [ ] All 1,330 embedded tasks extracted
- [ ] No duplicate files created
- [ ] All data preserved correctly
- [ ] Backup available for rollback

### Rollback Plan
```bash
# If something goes wrong:
rm -rf .vibey/roadmap
mv .vibey/roadmap.backup.* .vibey/roadmap
vibey roadmap db rebuild
```

---

## Task 004: Rebuild database and verify task counts

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215B`
**Estimated Tokens**: 15,000
**Complexity**: Simple
**Blocked By**: Task 003

### Objective
Rebuild the SQLite database and verify all tracks show correct task counts.

### Execution Plan

#### Step 1: Rebuild Database
```bash
vibey roadmap db rebuild
```

Expected output:
```
Loaded 40 tracks, 207 sprints, ~2459 tasks
```

#### Step 2: Verify Track Counts
```bash
# All tracks with tasks
sqlite3 .vibey/roadmap.db "
SELECT t.name, t.status,
       COUNT(DISTINCT s.id) as sprints,
       COUNT(tk.id) as tasks
FROM tracks t
LEFT JOIN sprints s ON s.track_id = t.id
LEFT JOIN tasks tk ON tk.sprint_id = s.id
GROUP BY t.id
ORDER BY tasks DESC;
"
```

#### Step 3: Verify Key Tracks
```bash
# Goose Port - should have ~34 tasks
sqlite3 .vibey/roadmap.db "
SELECT s.name, COUNT(tk.id) as tasks
FROM sprints s
JOIN tasks tk ON tk.sprint_id = s.id
WHERE s.track_id = '01KC7H29E0Z5BC7HK1CK222BS'  -- goose-port track id
GROUP BY s.id;
"

# JetBrains Port
sqlite3 .vibey/roadmap.db "
SELECT s.name, COUNT(tk.id) as tasks
FROM sprints s
JOIN tasks tk ON tk.sprint_id = s.id
WHERE s.track_id = '01KC2D0JK9JKQXGQW6MQEB0JZP'
GROUP BY s.id;
"
```

#### Step 4: Compare DB vs Files
```bash
python3 -c "
from pathlib import Path
import sqlite3

# Count files
file_count = len(list(Path('.vibey/roadmap/tasks').glob('*.yaml')))

# Count DB
conn = sqlite3.connect('.vibey/roadmap.db')
db_count = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]

print(f'Task files: {file_count}')
print(f'DB tasks: {db_count}')
print(f'Match: {file_count == db_count}')
"
```

### Acceptance Criteria
- [ ] Database rebuilds without errors
- [ ] All ~2,459 tasks loaded
- [ ] Goose Port shows 34+ tasks
- [ ] JetBrains Port shows correct tasks
- [ ] File count matches DB count

---

## Sprint 1 Summary

| Task | Title | Tokens | Complexity | Dependencies |
|------|-------|--------|------------|--------------|
| 001 | Create extraction script | 50,000 | Complex | None |
| 002 | Build slug mapping | 20,000 | Medium | None |
| 003 | Execute extraction | 30,000 | Medium | 001, 002 |
| 004 | Rebuild and verify DB | 15,000 | Simple | 003 |

**Total Estimated Tokens**: 115,000
**Estimated Duration**: 3 days
**Critical Path**: 001 → 003 → 004
