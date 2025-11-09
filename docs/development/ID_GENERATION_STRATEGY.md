# ID Generation Strategy - Deterministic & Collision-Free

**Date:** 2025-11-09
**Status:** Design Proposal
**Purpose:** Define deterministic ID generation strategy that prevents collisions and enables stable references

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Current System Issues](#current-system-issues)
3. [Design Requirements](#design-requirements)
4. [Proposed Solution](#proposed-solution)
5. [Implementation Plan](#implementation-plan)
6. [Migration Strategy](#migration-strategy)

---

## Problem Statement

### Current ID Scheme

**Tracks:** Human-readable slugs (e.g., `mcp-server`, `documentation-system`)
**Sprints:** Track slug + sequential number (e.g., `mcp-server-1`, `documentation-system-2`)
**Tasks:** Sprint ID + task number (e.g., `mcp-server-1-task-001`)

### Collision Risks

**Problem 1: Track Renaming**
```yaml
# Track created as "doc-system"
id: doc-system

# Later renamed to "documentation-system"
id: documentation-system  # NEW ID - breaks all references!

# Sprints still reference old ID
sprint:
  id: doc-system-1
  track_id: documentation-system  # MISMATCH!
```

**Problem 2: Sprint Reordering**
```yaml
# Sprint 1 created
id: mcp-server-1

# Later, new sprint inserted before it
# Current Sprint 1 becomes Sprint 2
id: mcp-server-2  # COLLISION if we rename!

# Or we keep ID, but now:
id: mcp-server-1  # Sprint 1 ID, but actually Sprint 2 (confusing!)
```

**Problem 3: Task Renumbering**
```yaml
# Task 1 created
id: mcp-server-1-task-001

# Task inserted before it
# Current task-001 becomes task-002
id: mcp-server-1-task-002  # COLLISION or confusion
```

**Problem 4: Cross-Track Sprint Moves**
```yaml
# Sprint created in track A
id: track-a-1
track_id: track-a

# Later moved to track B
id: track-a-1  # Still has track-a in ID!
track_id: track-b  # But belongs to track-b (confusing!)
```

---

## Current System Issues

### 1. ID Stability

**Issue:** IDs change when objects are renamed or reordered
**Impact:** Breaks references, loses history, confuses users

**Example:**
```yaml
# Original
track:
  id: docs-sys
  name: Documentation System

# After rename
track:
  id: documentation-system  # Changed!
  name: Documentation System
```

All references to `docs-sys` now broken:
- Sprint references: `track_id: docs-sys` (invalid)
- Dependency references: `depends_on: [docs-sys]` (broken)
- File paths: `.vibey/roadmap/docs-sys/` (orphaned)
- Git history: Lost connection to previous work

### 2. Sequential Numbering Fragility

**Issue:** Sequential numbers assume fixed ordering
**Impact:** Reordering breaks numbering scheme

**Example:**
```yaml
# Original sprints
sprints:
- id: mcp-server-1  # Sprint 1
- id: mcp-server-2  # Sprint 2

# Insert new sprint at beginning
sprints:
- id: mcp-server-0  # New Sprint 1 (awkward ID!)
- id: mcp-server-1  # Now Sprint 2 (ID says 1)
- id: mcp-server-2  # Now Sprint 3 (ID says 2)
```

### 3. Human-Readable vs. Immutable Conflict

**Issue:** Human-readable IDs encourage changing them when names change
**Impact:** Tradeoff between readability and stability

**Current approach:** Human-readable (e.g., `documentation-system`)
**Cost:** IDs change with renames, breaking references

**Alternative:** Immutable UUIDs (e.g., `550e8400-e29b-41d4-a716-446655440000`)
**Cost:** Unreadable, hard to work with manually

### 4. No Creation Timestamp Encoding

**Issue:** Can't determine object creation order from ID alone
**Impact:** Requires reading YAML to determine age

### 5. No Collision Prevention

**Issue:** Nothing prevents creating duplicate IDs
**Impact:** Manual prevention required, errors possible

---

## Design Requirements

### Must Have

1. **Deterministic:** Same inputs → same ID (reproducible)
2. **Unique:** No collisions across entire roadmap
3. **Immutable:** Never changes after creation
4. **Sortable:** IDs sort chronologically by creation time
5. **Namespaced:** Clear hierarchy (roadmap/track/sprint/task)
6. **Reversible:** Can extract metadata from ID

### Should Have

7. **Human-Readable:** Somewhat readable (not pure UUID)
8. **Compact:** Reasonably short (< 50 characters)
9. **URL-Safe:** Works in file paths, URLs
10. **Git-Friendly:** No special characters that break git

### Nice to Have

11. **Memorable:** Easier to reference than UUIDs
12. **Contextual:** Hints at object type/hierarchy
13. **Backwards Compatible:** Works with existing system

---

## Proposed Solution

### Hybrid Approach: Timestamp + Counter + Hash

**Format:** `{prefix}-{timestamp}-{counter}-{hash}`

**Components:**
- `prefix`: Object type (track, sprint, task)
- `timestamp`: Unix timestamp (10 digits) or YYYYMMDD-HHMMSS
- `counter`: Sequential counter within timestamp (3 digits)
- `hash`: Short hash of object metadata (6-8 characters)

**Examples:**
```yaml
# Track
id: track-20251109-150000-001-a1b2c3d4

# Sprint
id: sprint-20251109-153000-001-e5f6g7h8

# Task
id: task-20251109-154500-001-i9j0k1l2
```

### Alternative: ULID (Universally Unique Lexicographically Sortable Identifier)

**Format:** `01ARZ3NDEKTSV4RRFFQ69G5FAV`

**Structure:**
- 26 characters (base32 encoded)
- First 48 bits: Unix timestamp (millisecond precision)
- Remaining 80 bits: Random component
- Lexicographically sortable
- No collisions (128-bit uniqueness)

**Examples:**
```yaml
# Track
id: 01JB3QVDZ8TRK9XN1FJFHGWPRM

# Sprint
id: 01JB3QVE2CSPRT7KDHM4JQWXYZ

# Task
id: 01JB3QVE5NTSK2BPFQR8LVXABC
```

**Benefits:**
- Industry standard (used by many systems)
- Truly collision-free (128-bit entropy)
- Sortable by creation time
- Compact (26 characters)
- Monotonic (within same millisecond)
- URL-safe (base32 alphabet)

**Drawbacks:**
- Not human-readable
- Opaque (can't see metadata)

### Recommended: ULID with Human-Readable Prefix

**Format:** `{prefix}_{ulid}`

**Examples:**
```yaml
# Track: Documentation System
id: track_01JB3QVDZ8TRK9XN1FJFHGWPRM
name: Hierarchical Documentation & Context Management System

# Sprint: Sprint 1
id: sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ
name: Hierarchical Structure & Core Generation
track_id: track_01JB3QVDZ8TRK9XN1FJFHGWPRM

# Task: Task 1
id: task_01JB3QVE5NTSK2BPFQR8LVXABC
name: Design and implement hierarchical directory structure
sprint_id: sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ
```

**Benefits:**
- ✅ Deterministic (timestamp-based)
- ✅ Unique (128-bit collision-free)
- ✅ Immutable (never changes)
- ✅ Sortable (lexicographically by creation time)
- ✅ Namespaced (prefix indicates type)
- ✅ Reversible (extract timestamp from ULID)
- ✅ Compact (prefix + 26 chars = ~32 chars)
- ✅ URL-safe (base32 + underscore)
- ✅ Git-friendly (no special chars)

**Tradeoffs:**
- ⚠️ Not fully human-readable (ULID portion opaque)
- ⚠️ Longer than simple slugs (32 vs. 15-20 chars)
- ✅ More readable than pure UUIDs
- ✅ Prefix provides context

---

## Detailed Design

### ID Format Specification

**Pattern:** `{type}_{ulid}`

**Components:**

1. **Type Prefix** (required):
   - `track_` - Track-level object
   - `sprint_` - Sprint-level object
   - `task_` - Task-level object
   - Future: `milestone_`, `epic_`, etc.

2. **ULID** (26 characters, required):
   - Format: `[0-9A-HJKMNP-TV-Z]{26}` (base32, no I, L, O, U)
   - Example: `01JB3QVDZ8TRK9XN1FJFHGWPRM`
   - Structure:
     - Characters 1-10: Timestamp (milliseconds since Unix epoch)
     - Characters 11-26: Random component (80 bits)

**Total Length:** 32-33 characters (type + underscore + ULID)

### ULID Properties

**Timestamp Encoding:**
```
Characters 1-10 encode timestamp in base32
01JB3QVDZ8 = 1731168000000 ms = 2025-11-09 15:00:00 UTC
```

**Monotonicity:**
- Within same millisecond: Incrementing random component
- Across milliseconds: Timestamp increases naturally
- Result: Always sortable, even for concurrent creation

**Collision Resistance:**
- 80 bits of randomness per ID
- 2^80 = 1.2 × 10^24 possible IDs per millisecond
- Collision probability: Negligible for human-scale usage

**Example ULID Breakdown:**
```
01JB3QVDZ8TRK9XN1FJFHGWPRM
├─ 01JB3QVDZ8 ────────────────── Timestamp (ms since epoch)
└─ TRK9XN1FJFHGWPRM ────────────── Random component
```

### Directory Structure with ULIDs

```
.vibey/roadmap/
├── table_of_contents.json
├── roadmap.yaml
│
├── track_01JB3QVDZ8TRK9XN1FJFHGWPRM/
│   ├── track.yaml
│   ├── track.md
│   ├── table_of_contents.json
│   └── context/
│       └── design.md
│   └── sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ/
│       ├── sprint.yaml
│       ├── sprint.md
│       ├── table_of_contents.json
│       └── context/
│       └── task_01JB3QVE5NTSK2BPFQR8LVXABC/
│           ├── task.yaml
│           ├── task.md
│           └── context/
│               └── research.md
```

**Pros:**
- ✅ Guaranteed unique (no collisions)
- ✅ Stable (never changes)
- ✅ Sortable (chronological)

**Cons:**
- ❌ Directory names not human-readable
- ❌ Hard to find specific track by browsing
- ❌ Git diffs show ULID instead of meaningful name

### Alternative: Human-Readable Directories with ULID Files

```
.vibey/roadmap/
├── table_of_contents.json
├── roadmap.yaml
│
├── documentation-system/              # Human-readable directory
│   ├── track_01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml
│   ├── track.md                       # Generated, references ULID
│   ├── table_of_contents.json
│   ├── .track_id                      # Hidden file: track_01JB3QVDZ8...
│   └── context/
│   └── sprint-1-hierarchical-structure/   # Human-readable
│       ├── sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ.yaml
│       ├── sprint.md
│       ├── .sprint_id                 # Hidden file
│       └── task-001-implement-hierarchy/
│           ├── task_01JB3QVE5NTSK2BPFQR8LVXABC.yaml
│           ├── task.md
│           └── .task_id               # Hidden file
```

**Pros:**
- ✅ Human-readable directory structure
- ✅ Stable IDs in YAML files
- ✅ Best of both worlds

**Cons:**
- ❌ Potential directory name conflicts (mitigated by .track_id validation)
- ❌ Directory rename doesn't affect ID (feature or bug?)

### Recommended: Hybrid Approach

**Use ULIDs for IDs, human-readable for directories:**

```
.vibey/roadmap/
├── documentation-system/                    # Slug directory (mutable)
│   ├── .id → track_01JB3QVDZ8TRK9XN1FJFHGWPRM   # Symlink or hidden file
│   ├── track.yaml                           # id: track_01JB3QVDZ8...
│   └── hierarchical-structure/              # Sprint slug directory
│       ├── .id → sprint_01JB3QVE2C...       # Sprint ID reference
│       ├── sprint.yaml                      # id: sprint_01JB3QVE2C...
│       └── implement-hierarchy/             # Task slug directory
│           ├── .id → task_01JB3QVE5N...     # Task ID reference
│           └── task.yaml                    # id: task_01JB3QVE5N...
```

**Benefits:**
- ✅ Human-readable browsing (documentation-system/)
- ✅ Stable IDs (ULIDs in YAML)
- ✅ Validation: `.id` file ensures directory matches object
- ✅ Git-friendly: Meaningful directory names in diffs
- ✅ Rename-safe: Directory rename doesn't affect ID

**Implementation:**
```python
def create_track_directory(track_id, slug):
    """Create track directory with ID validation."""
    dir_path = f".vibey/roadmap/{slug}"
    os.makedirs(dir_path, exist_ok=True)

    # Write .id file for validation
    with open(f"{dir_path}/.id", "w") as f:
        f.write(track_id)

    return dir_path

def validate_directory_id(dir_path, expected_id):
    """Ensure directory .id matches expected ID."""
    id_file = f"{dir_path}/.id"
    if not os.path.exists(id_file):
        raise ValueError(f"Missing .id file in {dir_path}")

    with open(id_file) as f:
        actual_id = f.read().strip()

    if actual_id != expected_id:
        raise ValueError(
            f"Directory {dir_path} .id mismatch: "
            f"expected {expected_id}, got {actual_id}"
        )
```

---

## Implementation Plan

### Phase 1: ULID Generation Library (1 day)

**Add ULID dependency:**
```python
# requirements.txt
python-ulid==2.2.0  # or ulid-py
```

**Create ID generator:**
```python
# framework/roadmap/id_generator.py
from ulid import ULID
from datetime import datetime

def generate_track_id() -> str:
    """Generate unique track ID."""
    ulid = ULID()
    return f"track_{str(ulid)}"

def generate_sprint_id() -> str:
    """Generate unique sprint ID."""
    ulid = ULID()
    return f"sprint_{str(ulid)}"

def generate_task_id() -> str:
    """Generate unique task ID."""
    ulid = ULID()
    return f"task_{str(ulid)}"

def extract_timestamp(id: str) -> datetime:
    """Extract creation timestamp from ULID."""
    # Remove prefix
    ulid_str = id.split("_")[1]
    ulid = ULID.from_str(ulid_str)
    return ulid.timestamp().datetime
```

### Phase 2: Update State Management (2 days)

**Update track creation:**
```python
# framework/roadmap/state_manager.py
from .id_generator import generate_track_id

def create_track(name: str, slug: str, **kwargs):
    """Create new track with ULID."""
    track_id = generate_track_id()

    track = {
        "id": track_id,
        "name": name,
        "slug": slug,  # For human-readable directories
        "created": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }

    # Create directory structure
    dir_path = f".vibey/roadmap/{slug}"
    os.makedirs(dir_path, exist_ok=True)

    # Write .id file
    with open(f"{dir_path}/.id", "w") as f:
        f.write(track_id)

    # Write YAML
    with open(f"{dir_path}/track.yaml", "w") as f:
        yaml.dump({"track": track}, f)

    return track_id
```

### Phase 3: Migration Script (3 days)

**Migrate existing IDs:**
```python
# framework/scripts/migrate_to_ulids.py
import yaml
from ulid import ULID

def migrate_roadmap():
    """Migrate all objects to ULID-based IDs."""

    # 1. Generate ULID for each existing object
    # 2. Create ID mapping (old → new)
    # 3. Update all references
    # 4. Update directory structure
    # 5. Validate no broken references

    id_mapping = {}

    # Migrate tracks
    for track_file in glob(".vibey/tracks/*.yaml"):
        track = yaml.safe_load(open(track_file))
        old_id = track["track"]["id"]

        # Generate ULID with same timestamp as creation date
        created = track["track"]["created"]
        ulid = ULID.from_timestamp(datetime.fromisoformat(created))
        new_id = f"track_{str(ulid)}"

        id_mapping[old_id] = new_id
        track["track"]["id"] = new_id
        track["track"]["slug"] = old_id  # Preserve as slug

        # ... save and update references
```

### Phase 4: Update Documentation (1 day)

- Update ID generation documentation
- Update CLI command documentation
- Update migration guide
- Update examples

### Phase 5: Testing (2 days)

- Test ULID generation (uniqueness, sortability)
- Test ID extraction (timestamp recovery)
- Test migration script (no data loss)
- Test reference updates (all valid)
- Test directory structure (validation works)

---

## Migration Strategy

### Migration Approach

**Option 1: Big Bang Migration**
- Migrate all IDs at once
- One large breaking change
- Requires coordination

**Option 2: Gradual Migration**
- New objects use ULIDs
- Old objects keep current IDs
- Support both formats during transition
- Eventually migrate old objects

**Recommended: Gradual Migration**

### Migration Steps

**Step 1: Add ULID Support (Non-Breaking)**
```python
# Support both old and new ID formats
def is_ulid_format(id: str) -> bool:
    parts = id.split("_")
    return len(parts) == 2 and len(parts[1]) == 26

def get_track_path(track_id: str) -> str:
    if is_ulid_format(track_id):
        # New format: Find by .id file
        for dir in glob(".vibey/roadmap/*/"):
            id_file = f"{dir}/.id"
            if os.path.exists(id_file):
                if open(id_file).read().strip() == track_id:
                    return dir
    else:
        # Old format: Direct path
        return f".vibey/roadmap/{track_id}/"
```

**Step 2: Generate ULIDs for New Objects**
```python
# New tracks automatically get ULIDs
track_id = generate_track_id()  # track_01JB...
```

**Step 3: Migrate Existing Objects (Scripted)**
```bash
python3 framework/scripts/migrate_to_ulids.py --dry-run
python3 framework/scripts/migrate_to_ulids.py --execute
```

**Step 4: Deprecate Old Format**
```python
# After migration complete, remove old format support
```

---

## Validation & Testing

### ULID Generation Tests

```python
def test_ulid_uniqueness():
    """Generate 10,000 IDs, ensure no collisions."""
    ids = set()
    for _ in range(10000):
        track_id = generate_track_id()
        assert track_id not in ids
        ids.add(track_id)

def test_ulid_sortability():
    """IDs generated later sort after earlier ones."""
    id1 = generate_track_id()
    time.sleep(0.001)  # Ensure different millisecond
    id2 = generate_track_id()
    assert id1 < id2  # Lexicographic sorting

def test_timestamp_extraction():
    """Can extract creation timestamp from ID."""
    before = datetime.now(timezone.utc)
    track_id = generate_track_id()
    after = datetime.now(timezone.utc)

    extracted = extract_timestamp(track_id)
    assert before <= extracted <= after
```

### Migration Tests

```python
def test_migration_preserves_data():
    """Migration doesn't lose any data."""
    # Count objects before migration
    before_counts = count_all_objects()

    # Run migration
    migrate_roadmap()

    # Count objects after migration
    after_counts = count_all_objects()

    assert before_counts == after_counts

def test_migration_updates_references():
    """All references updated to new IDs."""
    migrate_roadmap()

    # Check all track references in sprints
    for sprint_file in glob(".vibey/roadmap/**/sprint.yaml"):
        sprint = yaml.safe_load(open(sprint_file))
        track_id = sprint["sprint"]["track_id"]

        # Ensure track exists with this ID
        assert track_exists(track_id)
```

---

## Conclusion

### Recommended Solution

**Adopt ULID-based IDs with human-readable directory slugs:**

1. **IDs:** `{type}_{ulid}` (e.g., `track_01JB3QVDZ8TRK9XN1FJFHGWPRM`)
2. **Directories:** Human-readable slugs (e.g., `documentation-system/`)
3. **Validation:** `.id` files ensure directory ↔ ID mapping

### Benefits

- ✅ **Collision-Free:** 128-bit uniqueness guarantees
- ✅ **Immutable:** IDs never change, even if names/order change
- ✅ **Sortable:** Lexicographically sortable by creation time
- ✅ **Deterministic:** Timestamp-based generation
- ✅ **Human-Readable Browsing:** Directory slugs easy to navigate
- ✅ **Git-Friendly:** Meaningful directory names in diffs
- ✅ **Reversible:** Extract creation timestamp from ID

### Implementation Timeline

- **Phase 1:** ULID library integration (1 day)
- **Phase 2:** State management updates (2 days)
- **Phase 3:** Migration script (3 days)
- **Phase 4:** Documentation updates (1 day)
- **Phase 5:** Testing & validation (2 days)

**Total:** 9 days (~2 weeks)

### Next Steps

1. Approve ULID-based ID strategy
2. Add to documentation-system track Sprint 1 (as new task)
3. Implement during documentation system development
4. Migrate existing objects as part of hierarchy migration (Sprint 3)

---

**Document Status:** Complete - Ready for Review
**Recommended Decision:** APPROVE ULID-based ID generation
**Integration:** Add to documentation-system track as foundational component
