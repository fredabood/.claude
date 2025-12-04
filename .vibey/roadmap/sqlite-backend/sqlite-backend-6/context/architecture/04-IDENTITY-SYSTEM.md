# Identity System (ULID)

## Design Rationale

The current ID scheme (`sqlite-backend-6-task-004`) conflates **identity**, **hierarchy**, and **ordering** into a single mutable string. This causes:

| Problem | Current Behavior | Impact |
|---------|------------------|--------|
| **Renaming breaks references** | Track rename = new ID | All sprint/task references break |
| **Reordering requires renaming** | Task 004 becomes 005 | ID changes, git history lost |
| **Git history fragmented** | File path changes on rename | `git log --follow` required |
| **Order inferred from name** | "task-004" implies 4th | Can't reorder without renaming |
| **Priority conflated with order** | Higher number = later | Can't have high-priority task-015 |

---

## ULID-Based Identity

**Solution:** Use ULID (Universally Unique Lexicographically Sortable Identifier) for immutable identity.

**Format:** `{type}_{ulid}` (32-33 characters)

```
track_01JB3QVDZ8TRK9XN1FJFHGWPRM
      └─────────────────────────┘
              26-char ULID
```

**ULID Properties:**
- **Unique:** 128-bit collision-free
- **Sortable:** Lexicographically by creation time
- **Immutable:** Never changes after creation
- **Reversible:** Can extract creation timestamp

---

## Decoupling Identity, Ordering, and Display

| Concept | Field | Layer | Mutable | Purpose |
|---------|-------|-------|---------|---------|
| **Identity** | `id` | Completable | No | Stable reference, git history |
| **Display Name** | `name` | Completable | Yes | Human-readable label |
| **Parent Reference** | `parent_id` | HierarchicalTicket | No | Hierarchy navigation |
| **Ordering** | `sequence` | HierarchicalTicket | Yes | Sibling sort order |
| **Path Segment** | `slug` | HierarchicalTicket | Yes | Directory/URL path |

---

## Ordering Semantics

**`sequence: int`** - Explicit ordering among siblings

**Code:** [`sample_code/yaml/block_044.yaml`](../sample_code/yaml/block_044.yaml)

**Key Benefits:**
1. **No ID change** - Git history follows the task
2. **No reference updates** - Other tickets still reference same ULID
3. **Explicit ordering** - Not inferred from naming convention

---

## Directory Structure with Slugs

**Hybrid approach:** ULID for identity, slugs for paths

```
.vibey/roadmap/
├── sqlite-backend/                    # slug (mutable)
│   ├── .id                            # Contains: track_01JB3QVDZ8...
│   ├── track.yaml                     # id: track_01JB3QVDZ8...
│   └── unified-ticket-architecture/   # slug (mutable)
│       ├── .id                        # Contains: sprint_01JB3QVE2C...
│       ├── sprint.yaml                # id: sprint_01JB3QVE2C...
│       └── define-enum-types/         # slug (mutable)
│           ├── .id                    # Contains: task_01JB3QVE5N...
│           └── task.yaml              # id: task_01JB3QVE5N...
```

**Validation:** `.id` file ensures directory ↔ ULID mapping

**Code:** [`sample_code/models/func_validate_directory.py`](../sample_code/models/func_validate_directory.py)

---

## Reference Resolution

**All references use ULID, not slug:**

**Code:** [`sample_code/yaml/example_criteria_1.yaml`](../sample_code/yaml/example_criteria_1.yaml)

**Benefits:**
- Rename sprint → references still valid
- Move sprint between tracks → references still valid
- Git history tracks by ULID across renames

---

## Migration Strategy

| Phase | Sprint | Actions |
|-------|--------|---------|
| 1 | 6 | Add ULID generation, use existing `id_generator.py` |
| 2 | 6 | Add `parent_id`, `sequence`, `slug` to HierarchicalTicket |
| 3 | 8 | Update YAML loader to generate ULID if not present |
| 4 | 12 | Full migration: generate ULIDs, update refs, create `.id` files |

---

## ID Generator Integration

The ULID system is already implemented in `vibey/roadmap/id_generator.py`:

**Code:** [`sample_code/models/block_047.py`](../sample_code/models/block_047.py)

**Dependency:** Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps
    "python-ulid>=2.2.0",
]
```

---

## Database Schema Updates

**Code:** [`sample_code/sql/view_v_ticket_siblings.sql`](../sample_code/sql/view_v_ticket_siblings.sql)

---

## Benefits Summary

| Capability | Before (Slug-based ID) | After (ULID + Sequence) |
|------------|------------------------|-------------------------|
| **Rename entity** | ID changes, references break | Name/slug change, ID stable |
| **Reorder siblings** | IDs change, git history lost | Sequence changes, ID stable |
| **Git history** | Fragments on rename | Follows ULID across renames |
| **Priority** | Inferred from task number | Explicit `priority` field |
| **Directory browsing** | Uses ID directly | Uses human-readable slug |
| **Reference stability** | Breaks on any rename | Stable across all renames |
