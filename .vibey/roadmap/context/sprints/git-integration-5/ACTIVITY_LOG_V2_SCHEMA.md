# Activity Log V2 Schema: Command-Level Granularity

**Task:** git-integration-5-task-001
**Status:** In Progress
**Created:** 2025-12-10

---

## Overview

This document defines the V2 activity log schema that changes from **field-level** to **command-level** granularity. The key principle: **one CLI command = one activity log entry**.

## Design Goals

1. **Atomic operations** - Each CLI command creates exactly one entry
2. **Verification support** - Include file hashes for integrity verification
3. **Signing support** - Include signature fields for Phase 4
4. **Backward compatibility** - Reader can parse both V1 and V2 formats
5. **Field history preserved** - `changes[]` array allows field-level queries

---

## V1 Schema (Current - Field-Level)

```python
@dataclass
class ActivityEvent:
    timestamp: str           # ISO8601
    object_type: str         # "track", "sprint", "task", "roadmap"
    object_id: str           # ULID
    field: str               # Single field name
    old_value: Any           # Previous value
    new_value: Any           # New value
    changed_by: str          # "cli", "manual", etc.
    reason: Optional[str]    # User-provided reason
    commit: Optional[str]    # Git commit hash
    source: str              # "manual" default
```

**Problem:** One CLI command updating multiple fields creates multiple entries:

```bash
vibey roadmap update task 01KC... --status completed --title "New title"
```

Creates 2 entries:
```jsonl
{"field": "status", "old_value": "in_progress", "new_value": "completed", ...}
{"field": "title", "old_value": "Old title", "new_value": "New title", ...}
```

---

## V2 Schema (New - Command-Level)

### FieldChange Dataclass

```python
@dataclass
class FieldChange:
    """Single field change within a command."""
    field: str       # Field name
    old: Any         # Previous value (null for new fields)
    new: Any         # New value
```

### CommandActivityEvent Dataclass

```python
@dataclass
class CommandActivityEvent:
    """
    Single activity event representing one CLI command.

    Command-level granularity: one CLI command = one entry.
    """
    # Identity
    id: str                          # Unique event ID (ULID)
    timestamp: str                   # ISO8601 with timezone

    # Command info
    command: str                     # Full CLI command string

    # Target object
    object_type: str                 # "track", "sprint", "task", "roadmap"
    object_id: str                   # ULID of modified object

    # Changes (array of field changes)
    changes: List[FieldChange]       # All field changes from this command

    # File verification
    file_path: str                   # Relative path to YAML file
    file_hash_before: Optional[str]  # SHA256 before change (null for create)
    file_hash_after: str             # SHA256 after change

    # Attribution
    changed_by: str                  # "cli", "migration", "hook", etc.
    reason: Optional[str]            # User-provided reason

    # Signing (Phase 4)
    signature: Optional[str]         # Ed25519 signature (base64)
    signer: Optional[str]            # Signer identity
```

### Example V2 Entry

```jsonl
{
  "id": "01KC3AD7AH3SRTJR88J63VWMWS",
  "timestamp": "2025-12-10T16:40:00.000000+00:00",
  "command": "vibey roadmap update task 01KC... --status completed --title 'New title'",
  "object_type": "task",
  "object_id": "01KC2D0JK7READW9KAK1HBX4B3",
  "changes": [
    {"field": "status", "old": "in_progress", "new": "completed"},
    {"field": "title", "old": "Old title", "new": "New title"}
  ],
  "file_path": ".vibey/roadmap/tasks/01KC2D0JK7READW9KAK1HBX4B3.yaml",
  "file_hash_before": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
  "file_hash_after": "f6e5d4c3b2a198765432109876543210987654321098765432109876543210fe",
  "changed_by": "cli",
  "reason": null,
  "signature": null,
  "signer": null
}
```

---

## Field Specifications

### id
- **Type:** String (ULID)
- **Required:** Yes
- **Description:** Unique identifier for this event, generated at write time
- **Format:** 26-character ULID (e.g., `01KC3AD7AH3SRTJR88J63VWMWS`)

### timestamp
- **Type:** String (ISO8601)
- **Required:** Yes
- **Description:** When the command was executed
- **Format:** `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`

### command
- **Type:** String
- **Required:** Yes
- **Description:** Full CLI command that was executed
- **Example:** `"vibey roadmap update task 01KC... --status completed"`
- **Note:** Passwords/secrets should be redacted before logging

### object_type
- **Type:** String (enum)
- **Required:** Yes
- **Values:** `"roadmap"`, `"track"`, `"sprint"`, `"task"`

### object_id
- **Type:** String (ULID)
- **Required:** Yes
- **Description:** ID of the object that was modified

### changes
- **Type:** Array of FieldChange
- **Required:** Yes (can be empty for non-field operations)
- **Description:** All field-level changes made by this command

### file_path
- **Type:** String
- **Required:** Yes
- **Description:** Relative path from project root to YAML file
- **Example:** `".vibey/roadmap/tasks/01KC...yaml"`

### file_hash_before
- **Type:** String or null
- **Required:** No (null for create operations)
- **Description:** SHA256 hash of file contents before the change
- **Format:** 64-character lowercase hex

### file_hash_after
- **Type:** String
- **Required:** Yes
- **Description:** SHA256 hash of file contents after the change
- **Format:** 64-character lowercase hex

### changed_by
- **Type:** String
- **Required:** Yes
- **Description:** Source of the change
- **Values:** `"cli"`, `"migration"`, `"hook"`, `"manual"`, `"system"`

### reason
- **Type:** String or null
- **Required:** No
- **Description:** User-provided reason for the change

### signature
- **Type:** String or null
- **Required:** No (Phase 4)
- **Description:** Ed25519 signature of canonical event data
- **Format:** Base64-encoded signature

### signer
- **Type:** String or null
- **Required:** No (Phase 4)
- **Description:** Identity of the signer (matches authorized-signers filename)

---

## Canonical Serialization for Signing

When signing an event, only specific fields are included to ensure deterministic signatures:

```python
def canonical_bytes(self) -> bytes:
    """Deterministic serialization for signing."""
    # Sort changes by field name for determinism
    sorted_changes = sorted(
        [{"field": c.field, "old": c.old, "new": c.new} for c in self.changes],
        key=lambda c: c["field"]
    )

    data = {
        "id": self.id,
        "timestamp": self.timestamp,
        "command": self.command,
        "object_type": self.object_type,
        "object_id": self.object_id,
        "changes": sorted_changes,
        "file_hash_before": self.file_hash_before,
        "file_hash_after": self.file_hash_after,
    }

    # Deterministic JSON: sorted keys, no whitespace
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
```

---

## Backward Compatibility

### Reading V1 Entries

When parsing an entry without the `changes` field, convert to V2 format:

```python
def from_json_line(cls, line: str) -> 'CommandActivityEvent':
    data = json.loads(line.strip())

    # V1 format detection: has 'field' but not 'changes'
    if 'field' in data and 'changes' not in data:
        # Convert V1 to V2
        return cls(
            id=data.get('id', generate_ulid()),  # Generate if missing
            timestamp=data['timestamp'],
            command=data.get('command', f"[legacy] {data.get('source', 'manual')}"),
            object_type=data['object_type'],
            object_id=data['object_id'],
            changes=[FieldChange(
                field=data['field'],
                old=data['old_value'],
                new=data['new_value']
            )],
            file_path=data.get('file_path', ''),
            file_hash_before=data.get('file_hash_before'),
            file_hash_after=data.get('file_hash_after', ''),
            changed_by=data['changed_by'],
            reason=data.get('reason'),
            signature=None,
            signer=None,
        )

    # V2 format
    return cls(...)
```

### Writing V2 Entries

V2 entries include all new fields. Old readers will fail gracefully if they encounter unknown fields.

---

## Migration Strategy

### Phase 1: Add V2 Support
1. Add `CommandActivityEvent` and `FieldChange` dataclasses
2. Update `ActivityLogWriter` with `log_command()` method
3. Update `ActivityLogReader` to parse both formats

### Phase 2: Update CLI
1. Update all CLI write commands to use `log_command()`
2. Capture full command string before execution
3. Collect all field changes into list
4. Compute file hashes before and after

### Phase 3: Migrate Existing Data
1. Group consecutive V1 entries by timestamp/object_id
2. Merge into V2 entries where possible
3. Entries that can't be grouped become single-change V2 entries

---

## File Hash Computation

```python
import hashlib

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
```

---

## Verification Algorithm

```python
def verify_file(file_path: Path, reader: ActivityLogReader) -> bool:
    """Verify file has matching activity log entry."""
    current_hash = compute_file_hash(file_path)
    entry = reader.find_by_hash(current_hash)

    if entry is None:
        return False  # No matching entry

    if entry.signature and not verify_signature(entry):
        return False  # Invalid signature

    return True
```

---

## Success Criteria

- [ ] `CommandActivityEvent` dataclass defined with all fields
- [ ] `FieldChange` dataclass defined
- [ ] Canonical serialization method specified
- [ ] Backward compatibility approach documented
- [ ] Migration strategy documented
- [ ] File hash computation specified
- [ ] Verification algorithm specified

---

## Related Documents

- **TASK_PLANS.md** - Full sprint implementation plan
- **UNIFIED_TICKET_ARCHITECTURE.md** - Criterion-based blocking model

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-10 | Initial schema design |
