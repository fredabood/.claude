# ADR-0001: Use ULIDs for Entity Identifiers

## Status

Accepted

## Context

The Vibey roadmap system needs unique identifiers for tracks, sprints, and tasks. These identifiers must:

- Be globally unique without coordination (decentralized generation)
- Be sortable by creation time (for chronological ordering)
- Be usable in filenames (no special characters)
- Be reasonably short (for CLI usage)
- Support collision-free generation across sessions

Options considered:
- Auto-incrementing integers
- UUIDs (v4, random)
- ULIDs (Universally Unique Lexicographically Sortable Identifiers)
- Slug-based IDs (human-readable like `my-track-sprint-1-task-001`)

## Decision

Use ULIDs for all entity identifiers in the roadmap system.

**Format:** `01KC81GRE3GXVPVSCMD19FC4Z7` (26 characters, Crockford Base32)

**Structure:**
```
01KC81GRE3GXVPVSCMD19FC4Z7
└───────┬───────┘└────┬────┘
    Timestamp      Randomness
    (48 bits)      (80 bits)
```

## Consequences

### Positive

- **Time-sortable**: IDs sort chronologically by default without explicit timestamps
- **URL/filename safe**: No special characters (unlike UUID dashes)
- **Decentralized**: Can generate without database or coordination
- **Short enough**: 26 chars vs 36 for UUID (no dashes)
- **Monotonic**: Multiple IDs generated in same millisecond sort consistently
- **Case-insensitive**: Crockford Base32 allows lowercase matching

### Negative

- **Less human-readable**: `01KC81GRE3GX...` vs `sprint-1-task-001`
- **Library dependency**: Requires ULID library (python-ulid)
- **Migration required**: Existing slug-based references need conversion

### Neutral

- Similar length to UUIDs in practice (when UUID dashes are removed)
- Learning curve for developers unfamiliar with ULIDs

## Alternatives Considered

### Auto-incrementing Integers

**Pros:**
- Simple, human-readable
- Very short (1, 2, 100, etc.)

**Cons:**
- Requires central coordination
- Not suitable for distributed generation
- Leaks information about entity count

### UUIDs (v4)

**Pros:**
- Well-known standard
- Good library support

**Cons:**
- Not sortable by time
- Longer with dashes (36 chars)
- Less filename-friendly

### Slug-based IDs

**Pros:**
- Human-readable (`sprint-planning-task-001`)
- Self-documenting

**Cons:**
- Rename complexity (slugs derived from names)
- Collision potential
- Variable length

## References

- [ULID Specification](https://github.com/ulid/spec)
- [python-ulid library](https://github.com/ahawker/ulid)
- Migration implementation in Sprint 4 of sqlite-backend track
