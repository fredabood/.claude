"""
ID Generation System - ULID-based collision-free identifiers

This module provides deterministic, collision-free ID generation for roadmap
objects (tracks, sprints, tasks) using ULIDs (Universally Unique
Lexicographically Sortable Identifiers).

Key Properties:
- Unique: 128-bit collision-free (2^80 IDs per millisecond)
- Sortable: Lexicographically by creation timestamp
- Deterministic: Timestamp-based generation
- Immutable: IDs never change after creation
- Reversible: Can extract creation timestamp from ID
- Compact: 32-33 characters total

Format: {type}_{ulid}
Examples:
- track_01JB3QVDZ8TRK9XN1FJFHGWPRM
- sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ
- task_01JB3QVE5NTSK2BPFQR8LVXABC
"""

from datetime import datetime, timezone
from typing import Optional
from ulid import ULID


def generate_track_id() -> str:
    """
    Generate a unique track ID using ULID.

    Returns:
        str: Track ID in format "track_{ulid}"

    Example:
        >>> track_id = generate_track_id()
        >>> print(track_id)
        track_01JB3QVDZ8TRK9XN1FJFHGWPRM
    """
    ulid = ULID()
    return f"track_{str(ulid)}"


def generate_sprint_id() -> str:
    """
    Generate a unique sprint ID using ULID.

    Returns:
        str: Sprint ID in format "sprint_{ulid}"

    Example:
        >>> sprint_id = generate_sprint_id()
        >>> print(sprint_id)
        sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ
    """
    ulid = ULID()
    return f"sprint_{str(ulid)}"


def generate_task_id() -> str:
    """
    Generate a unique task ID using ULID.

    Returns:
        str: Task ID in format "task_{ulid}"

    Example:
        >>> task_id = generate_task_id()
        >>> print(task_id)
        task_01JB3QVE5NTSK2BPFQR8LVXABC
    """
    ulid = ULID()
    return f"task_{str(ulid)}"


def generate_id_from_timestamp(prefix: str, timestamp: datetime) -> str:
    """
    Generate an ID from a specific timestamp (useful for migration).

    Args:
        prefix: ID prefix (e.g., "track", "sprint", "task")
        timestamp: Creation timestamp to encode in ULID

    Returns:
        str: ID in format "{prefix}_{ulid}"

    Example:
        >>> from datetime import datetime, timezone
        >>> ts = datetime(2025, 11, 9, 15, 0, 0, tzinfo=timezone.utc)
        >>> id = generate_id_from_timestamp("track", ts)
        >>> print(id)
        track_01JB3QVDZ8...
    """
    # Convert datetime to float (seconds since epoch)
    timestamp_float = timestamp.timestamp()
    ulid = ULID.from_timestamp(timestamp_float)
    return f"{prefix}_{str(ulid)}"


def extract_timestamp(id: str) -> datetime:
    """
    Extract creation timestamp from a ULID-based ID.

    Args:
        id: ID in format "{prefix}_{ulid}"

    Returns:
        datetime: Creation timestamp (UTC)

    Raises:
        ValueError: If ID format is invalid

    Example:
        >>> track_id = "track_01JB3QVDZ8TRK9XN1FJFHGWPRM"
        >>> ts = extract_timestamp(track_id)
        >>> print(ts)
        2025-11-09 15:00:00+00:00
    """
    if "_" not in id:
        raise ValueError(f"Invalid ID format: {id} (expected 'prefix_ulid')")

    parts = id.split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid ID format: {id} (expected 'prefix_ulid')")

    prefix, ulid_str = parts

    try:
        ulid = ULID.from_str(ulid_str)
        # Get timestamp as float (seconds since epoch) and convert to datetime
        timestamp_seconds = ulid.timestamp
        return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
    except Exception as e:
        raise ValueError(f"Invalid ULID in ID {id}: {e}")


def extract_prefix(id: str) -> str:
    """
    Extract type prefix from an ID.

    Args:
        id: ID in format "{prefix}_{ulid}"

    Returns:
        str: Type prefix (e.g., "track", "sprint", "task")

    Raises:
        ValueError: If ID format is invalid

    Example:
        >>> track_id = "track_01JB3QVDZ8TRK9XN1FJFHGWPRM"
        >>> prefix = extract_prefix(track_id)
        >>> print(prefix)
        track
    """
    if "_" not in id:
        raise ValueError(f"Invalid ID format: {id} (expected 'prefix_ulid')")

    return id.split("_", 1)[0]


def is_valid_id(id: str) -> bool:
    """
    Check if an ID is valid ULID-based format.

    Args:
        id: ID to validate

    Returns:
        bool: True if valid, False otherwise

    Example:
        >>> is_valid_id("track_01JB3QVDZ8TRK9XN1FJFHGWPRM")
        True
        >>> is_valid_id("invalid-id")
        False
    """
    try:
        if "_" not in id:
            return False

        parts = id.split("_", 1)
        if len(parts) != 2:
            return False

        prefix, ulid_str = parts

        # Validate prefix
        valid_prefixes = ["track", "sprint", "task"]
        if prefix not in valid_prefixes:
            return False

        # Validate ULID
        ULID.from_str(ulid_str)
        return True
    except Exception:
        return False


def is_ulid_format(id: str) -> bool:
    """
    Check if an ID uses ULID format (vs old slug format).

    This is useful during migration to distinguish between old IDs
    (e.g., "documentation-system") and new ULID-based IDs
    (e.g., "track_01JB3QVDZ8TRK9XN1FJFHGWPRM").

    Args:
        id: ID to check

    Returns:
        bool: True if ULID format, False if old format

    Example:
        >>> is_ulid_format("track_01JB3QVDZ8TRK9XN1FJFHGWPRM")
        True
        >>> is_ulid_format("documentation-system")
        False
    """
    if "_" not in id:
        return False

    parts = id.split("_", 1)
    if len(parts) != 2:
        return False

    prefix, ulid_str = parts

    # Check if prefix is valid
    valid_prefixes = ["track", "sprint", "task"]
    if prefix not in valid_prefixes:
        return False

    # Check if ULID part is 26 characters (base32 ULID length)
    return len(ulid_str) == 26


def is_raw_ulid(value: str) -> bool:
    """
    Check if a string is a raw ULID (26 alphanumeric chars, typically starting with 01).

    Raw ULIDs are used directly as IDs in YAML files without a type prefix.
    This is the standard format for roadmap entity IDs (tracks, sprints, tasks).

    Args:
        value: String to check

    Returns:
        bool: True if valid raw ULID format, False otherwise

    Example:
        >>> is_raw_ulid("01KCMGQHRKP26WEJK45T3HC6HW")
        True
        >>> is_raw_ulid("track_01KCMGQHRKP26WEJK45T3HC6HW")
        False
        >>> is_raw_ulid("documentation-system")
        False
    """
    if not value or len(value) != 26:
        return False
    # ULID uses Crockford's Base32: 0-9, A-Z (case insensitive, excludes I, L, O, U)
    # But for simplicity, we check alphanumeric (the ULID library handles strict validation)
    return value.isalnum()


def compare_ids_by_timestamp(id1: str, id2: str) -> int:
    """
    Compare two IDs by their creation timestamp.

    Args:
        id1: First ID
        id2: Second ID

    Returns:
        int: -1 if id1 < id2, 0 if equal, 1 if id1 > id2

    Raises:
        ValueError: If either ID is invalid

    Example:
        >>> id1 = generate_track_id()
        >>> time.sleep(0.001)
        >>> id2 = generate_track_id()
        >>> compare_ids_by_timestamp(id1, id2)
        -1
    """
    ts1 = extract_timestamp(id1)
    ts2 = extract_timestamp(id2)

    if ts1 < ts2:
        return -1
    elif ts1 > ts2:
        return 1
    else:
        return 0


# Convenience functions for common operations

def generate_id(type: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate an ID for any type, optionally with specific timestamp.

    Args:
        type: Object type ("track", "sprint", "task")
        timestamp: Optional creation timestamp (for migration)

    Returns:
        str: Generated ID

    Raises:
        ValueError: If type is invalid

    Example:
        >>> id = generate_id("track")
        >>> print(id)
        track_01JB3QVDZ8TRK9XN1FJFHGWPRM
    """
    valid_types = {
        "track": generate_track_id,
        "sprint": generate_sprint_id,
        "task": generate_task_id,
    }

    if type not in valid_types:
        raise ValueError(
            f"Invalid type: {type}. Must be one of {list(valid_types.keys())}"
        )

    if timestamp:
        return generate_id_from_timestamp(type, timestamp)
    else:
        return valid_types[type]()


if __name__ == "__main__":
    # Demo usage
    print("=== ULID ID Generation Demo ===\n")

    # Generate IDs
    track_id = generate_track_id()
    sprint_id = generate_sprint_id()
    task_id = generate_task_id()

    print(f"Track ID:  {track_id}")
    print(f"Sprint ID: {sprint_id}")
    print(f"Task ID:   {task_id}")

    # Extract timestamps
    print(f"\nTimestamps:")
    print(f"Track:  {extract_timestamp(track_id)}")
    print(f"Sprint: {extract_timestamp(sprint_id)}")
    print(f"Task:   {extract_timestamp(task_id)}")

    # Validation
    print(f"\nValidation:")
    print(f"Track ID valid:  {is_valid_id(track_id)}")
    print(f"Sprint ID valid: {is_valid_id(sprint_id)}")
    print(f"Invalid ID:      {is_valid_id('invalid-id')}")

    # Format detection
    print(f"\nFormat Detection:")
    print(f"ULID format: {is_ulid_format(track_id)}")
    print(f"Old format:  {is_ulid_format('documentation-system')}")

    # Sorting
    print(f"\nLexicographic Sorting:")
    print(f"IDs sort chronologically: {track_id < sprint_id < task_id}")
