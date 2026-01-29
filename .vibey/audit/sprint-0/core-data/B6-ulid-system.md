# B6: ULID Identifier System Audit

**Task ID:** 01KFXFCF9P8YXT3XCAJFC1G07P
**Phase:** B6: Core Data Model
**Date:** 2026-01-29

## Executive Summary

Complete documentation of the Vibey ULID identifier system, which provides collision-free, time-sortable, URL-safe identifiers for all roadmap entities. The system uses the `python-ulid` library to generate 26-character Crockford Base32 identifiers with 48-bit timestamps and 80-bit randomness. Key finding: Vibey uses two ID formats - raw ULIDs (26 chars) for entity IDs in YAML files, and prefixed ULIDs (`track_`, `sprint_`, `task_`) for typed operations. Distributed generation is collision-free due to 80-bit randomness.

## Methodology

**Files Analyzed:**
- `vibey/roadmap/id_generator.py:1-369` - ULID generation and utilities
- `docs/architecture/adr/0001-ulid-identifiers.md` - Design rationale
- `vibey/operations/roadmap/*.py` - ULID usage patterns (16 files import ulid)

## Findings

### 2. ULID Structure Table

| Component | Bits | Encoding | Purpose | Example |
|-----------|------|----------|---------|---------|
| Timestamp | 48 | First 10 chars | Millisecond precision timestamp (49+ years from epoch) | `01KC81GRE3` |
| Randomness | 80 | Last 16 chars | Cryptographically random for collision prevention | `GXVPVSCMD19FC4Z7` |
| Total | 128 | 26 chars | Complete ULID | `01KC81GRE3GXVPVSCMD19FC4Z7` |

**Encoding Details:**
- **Alphabet:** Crockford Base32 (0-9, A-Z excluding I, L, O, U)
- **Case:** Case-insensitive (lowercase maps to uppercase)
- **Sorting:** Lexicographically sortable by creation time
- **Monotonicity:** Multiple IDs in same millisecond sort consistently (incrementing random portion)

### 3. ULID Usage Table

| Use Case | Format | Location | Example |
|----------|--------|----------|---------|
| Entity ID (track) | Raw ULID (26 chars) | `.vibey/roadmap/tracks/{id}.yaml` | `01KFW4F7KN9E7GTQTXEQXE8AKB` |
| Entity ID (sprint) | Raw ULID (26 chars) | `.vibey/roadmap/sprints/{id}.yaml` | `01KFW4GZHDNGAHCZYBGPFF51FZ` |
| Entity ID (task) | Raw ULID (26 chars) | `.vibey/roadmap/tasks/{id}.yaml` | `01KFXF1TJG5RD5FHTA9PDX2HMV` |
| Typed ID | `{type}_{ulid}` | Internal operations | `track_01JB3QVDZ8TRK9XN1FJFHGWPRM` |
| Session ID | Raw ULID | Session management | `01KC2D0JK9JKQXGQW6MQEB0JZP` |
| Activity log entry ID | Raw ULID | JSONL activity log | `01KC3F8MN2QWERTY5678ABCD` |
| Artifact ID | Raw ULID | Artifact tracking | `01KC81GRE3GXVPVSCMD19FC4Z7` |
| Submodule link ID | Raw ULID | Cross-repo linking | `01KCMGQHRKP26WEJK45T3HC6HW` |

### 4. Generation Patterns Table

| Location | Library | Trigger | Collision Risk |
|----------|---------|---------|----------------|
| `vibey/roadmap/id_generator.py:40` | `ulid.ULID()` | Track creation | ~10^-24 per ms |
| `vibey/roadmap/id_generator.py:56` | `ulid.ULID()` | Sprint creation | ~10^-24 per ms |
| `vibey/roadmap/id_generator.py:72` | `ulid.ULID()` | Task creation | ~10^-24 per ms |
| `vibey/services/implementation/state.py:51` | `ulid.ULID()` | State snapshot | ~10^-24 per ms |
| `vibey/services/implementation/bug_logger.py:59` | `ulid.ULID()` | Bug task creation | ~10^-24 per ms |
| `vibey/operations/submodule/push.py:162-282` | `ulid.ULID()` | Cross-repo task/link | ~10^-24 per ms |
| `vibey/operations/roadmap/session_manager.py:23` | `ulid.ULID()` | Session creation | ~10^-24 per ms |

**Collision Analysis:**
- 80 bits of randomness = 2^80 possible values = 1.2 × 10^24
- Probability of collision with 1 billion IDs in same millisecond = ~10^-15
- For practical purposes, collision-free in distributed systems

### 5. ID Operations Table

| Operation | Function | Input | Output | Use Case |
|-----------|----------|-------|--------|----------|
| Generate | `generate_track_id()` | None | `track_01JB3...` | Create new entity |
| Generate typed | `generate_id(type)` | `"track"` | `track_01JB3...` | Dynamic type creation |
| Generate from timestamp | `generate_id_from_timestamp(prefix, ts)` | `"track", datetime` | `track_01JB3...` | Migration |
| Extract timestamp | `extract_timestamp(id)` | `track_01JB3...` | `datetime` | Audit, sorting |
| Extract prefix | `extract_prefix(id)` | `track_01JB3...` | `"track"` | Type detection |
| Validate | `is_valid_id(id)` | `track_01JB3...` | `True/False` | Input validation |
| Format check | `is_ulid_format(id)` | Any string | `True/False` | Migration detection |
| Raw check | `is_raw_ulid(id)` | Any string | `True/False` | YAML ID validation |
| Compare | `compare_ids_by_timestamp(id1, id2)` | Two IDs | `-1/0/1` | Chronological ordering |

### 6. Remote ID Strategy Table

| Scenario | Challenge | Strategy | Implementation |
|----------|-----------|----------|----------------|
| Distributed generation | Multiple clients generate simultaneously | ULIDs are inherently collision-free (80-bit random) | No coordination required |
| Cross-system references | Entity created locally, referenced remotely | Use same ULID in both systems | Direct ULID replication |
| ID conflict | Two systems create entity with same ULID (astronomically unlikely) | Last-write-wins with timestamp tiebreaker | Compare ULID timestamps |
| Legacy slug migration | Old IDs like `sprint-1-task-001` | Map slug → ULID in `.id` file | `vibey/roadmap/identity/id_file.py` |
| ID lookup | Find entity by ULID | Flat directory with ULID filename | `{type}s/{ulid}.yaml` |
| Timestamp extraction | Get creation time from ID | Parse ULID prefix | `extract_timestamp()` function |
| Sorting | Order entities by creation time | Lexicographic sort on ULID | ULIDs naturally sort by time |

**Remote Mode Implementation:**

1. **No ID coordination needed**: Each client generates ULIDs independently
2. **Replication**: Copy ULID as-is to Delta Lake STRING column
3. **Primary key**: Use ULID as Delta Lake table primary key
4. **Time queries**: Extract timestamp for time-range queries
5. **Conflict detection**: Compare ULIDs lexicographically for ordering

```sql
-- Delta Lake ID storage
CREATE TABLE tasks (
    id STRING PRIMARY KEY,  -- Raw ULID: 01KFXF1TJG5RD5FHTA9PDX2HMV
    sprint_id STRING,       -- Foreign key: 01KFW4GZHDNGAHCZYBGPFF51FZ
    ...
);

-- Time-range query using ULID prefix
SELECT * FROM tasks
WHERE id >= '01KFW0000000000000000000'  -- Start of day
  AND id < '01KFXZ000000000000000000';  -- End of day
```

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| ULIDs are inherently distributed | No ID coordinator needed for remote mode | S | High |
| Raw ULIDs used in YAML filenames | Store as STRING in Delta Lake, use as primary key | S | High |
| Timestamp embedded in ID | Use for time-range queries without separate column | M | Medium |
| Slug → ULID mapping exists | Migrate `.id` files to Delta Lake lookup table | M | Low |
| python-ulid library | Ensure Delta Lake clients have ULID generation capability | S | High |
| Lexicographic sorting | Delta Lake STRING columns sort ULIDs correctly | S | High |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] ULID structure fully documented with bit layout: PASS (48-bit timestamp + 80-bit random)
- [x] >= 4 ULID usage patterns documented: PASS (8 usage patterns)
- [x] ID generation locations identified with library info: PASS (7 locations using `ulid.ULID()`)
- [x] Remote ID strategy addresses distributed generation: PASS (7 scenarios with strategies)

## References

- `vibey/roadmap/id_generator.py:1-369` - Complete ULID utilities module
- `docs/architecture/adr/0001-ulid-identifiers.md` - ADR for ULID adoption
- `vibey/roadmap/identity/id_file.py:102-200` - Slug ↔ ULID mapping
- [ULID Specification](https://github.com/ulid/spec) - Official ULID spec
- [python-ulid library](https://github.com/ahawker/ulid) - Python implementation
