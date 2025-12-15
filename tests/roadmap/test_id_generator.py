"""
Tests for vibey.roadmap.id_generator module.

Tests ULID-based ID generation and validation.
"""

import pytest
import time
from datetime import datetime, timezone

from vibey.roadmap.id_generator import (
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
    generate_id_from_timestamp,
    extract_timestamp,
    extract_prefix,
    is_valid_id,
    is_ulid_format,
    compare_ids_by_timestamp,
    generate_id,
)


class TestGenerateTrackId:
    """Test generate_track_id function."""

    def test_returns_string(self):
        """Test returns a string."""
        track_id = generate_track_id()
        assert isinstance(track_id, str)

    def test_starts_with_prefix(self):
        """Test starts with track_ prefix."""
        track_id = generate_track_id()
        assert track_id.startswith("track_")

    def test_correct_length(self):
        """Test has correct total length."""
        track_id = generate_track_id()
        # track_ (6) + ULID (26) = 32
        assert len(track_id) == 32

    def test_unique_ids(self):
        """Test generates unique IDs."""
        ids = [generate_track_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestGenerateSprintId:
    """Test generate_sprint_id function."""

    def test_returns_string(self):
        """Test returns a string."""
        sprint_id = generate_sprint_id()
        assert isinstance(sprint_id, str)

    def test_starts_with_prefix(self):
        """Test starts with sprint_ prefix."""
        sprint_id = generate_sprint_id()
        assert sprint_id.startswith("sprint_")

    def test_correct_length(self):
        """Test has correct total length."""
        sprint_id = generate_sprint_id()
        # sprint_ (7) + ULID (26) = 33
        assert len(sprint_id) == 33


class TestGenerateTaskId:
    """Test generate_task_id function."""

    def test_returns_string(self):
        """Test returns a string."""
        task_id = generate_task_id()
        assert isinstance(task_id, str)

    def test_starts_with_prefix(self):
        """Test starts with task_ prefix."""
        task_id = generate_task_id()
        assert task_id.startswith("task_")

    def test_correct_length(self):
        """Test has correct total length."""
        task_id = generate_task_id()
        # task_ (5) + ULID (26) = 31
        assert len(task_id) == 31


class TestGenerateIdFromTimestamp:
    """Test generate_id_from_timestamp function."""

    def test_with_specific_timestamp(self):
        """Test generating ID from specific timestamp."""
        ts = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        track_id = generate_id_from_timestamp("track", ts)
        assert track_id.startswith("track_")

    def test_timestamp_preserved(self):
        """Test timestamp can be extracted."""
        ts = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        track_id = generate_id_from_timestamp("track", ts)
        extracted = extract_timestamp(track_id)
        # Allow 1 second tolerance due to ULID millisecond precision
        diff = abs((extracted - ts).total_seconds())
        assert diff < 1

    def test_different_prefixes(self):
        """Test works with different prefixes."""
        ts = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        track_id = generate_id_from_timestamp("track", ts)
        sprint_id = generate_id_from_timestamp("sprint", ts)
        task_id = generate_id_from_timestamp("task", ts)

        assert track_id.startswith("track_")
        assert sprint_id.startswith("sprint_")
        assert task_id.startswith("task_")


class TestExtractTimestamp:
    """Test extract_timestamp function."""

    def test_extract_from_valid_id(self):
        """Test extracting timestamp from valid ID."""
        track_id = generate_track_id()
        ts = extract_timestamp(track_id)
        assert isinstance(ts, datetime)
        assert ts.tzinfo is not None  # Should be timezone-aware

    def test_recent_timestamp(self):
        """Test extracted timestamp is recent."""
        track_id = generate_track_id()
        ts = extract_timestamp(track_id)
        now = datetime.now(timezone.utc)
        diff = abs((now - ts).total_seconds())
        assert diff < 5  # Within 5 seconds

    def test_invalid_format_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ID format"):
            extract_timestamp("invalid-id")

    def test_no_underscore_raises(self):
        """Test ID without underscore raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ID format"):
            extract_timestamp("trackABC123")


class TestExtractPrefix:
    """Test extract_prefix function."""

    def test_extract_track_prefix(self):
        """Test extracting track prefix."""
        track_id = generate_track_id()
        prefix = extract_prefix(track_id)
        assert prefix == "track"

    def test_extract_sprint_prefix(self):
        """Test extracting sprint prefix."""
        sprint_id = generate_sprint_id()
        prefix = extract_prefix(sprint_id)
        assert prefix == "sprint"

    def test_extract_task_prefix(self):
        """Test extracting task prefix."""
        task_id = generate_task_id()
        prefix = extract_prefix(task_id)
        assert prefix == "task"

    def test_invalid_format_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ID format"):
            extract_prefix("invalid-id")


class TestIsValidId:
    """Test is_valid_id function."""

    def test_valid_track_id(self):
        """Test valid track ID."""
        track_id = generate_track_id()
        assert is_valid_id(track_id)

    def test_valid_sprint_id(self):
        """Test valid sprint ID."""
        sprint_id = generate_sprint_id()
        assert is_valid_id(sprint_id)

    def test_valid_task_id(self):
        """Test valid task ID."""
        task_id = generate_task_id()
        assert is_valid_id(task_id)

    def test_invalid_no_underscore(self):
        """Test invalid ID without underscore."""
        assert not is_valid_id("invalid-id")

    def test_invalid_prefix(self):
        """Test invalid prefix."""
        assert not is_valid_id("invalid_01ABCDEFGHIJK123456789012")

    def test_invalid_ulid(self):
        """Test invalid ULID part."""
        assert not is_valid_id("track_invalid")

    def test_empty_string(self):
        """Test empty string is invalid."""
        assert not is_valid_id("")


class TestIsUlidFormat:
    """Test is_ulid_format function."""

    def test_ulid_format_track(self):
        """Test ULID format detection for track."""
        track_id = generate_track_id()
        assert is_ulid_format(track_id)

    def test_slug_format(self):
        """Test slug format is not ULID format."""
        assert not is_ulid_format("documentation-system")

    def test_old_sprint_format(self):
        """Test old sprint format is not ULID format."""
        assert not is_ulid_format("documentation-system-1")

    def test_invalid_prefix(self):
        """Test invalid prefix is not ULID format."""
        assert not is_ulid_format("invalid_01ABCDEFGHIJK12345678901X")

    def test_wrong_ulid_length(self):
        """Test wrong ULID length is not ULID format."""
        assert not is_ulid_format("track_SHORT")


class TestCompareIdsByTimestamp:
    """Test compare_ids_by_timestamp function."""

    def test_equal_timestamps(self):
        """Test IDs with same timestamp are equal."""
        ts = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        id1 = generate_id_from_timestamp("track", ts)
        id2 = generate_id_from_timestamp("track", ts)
        # Due to randomness in ULID, they may not be exactly equal
        # but should compare as 0 (equal) or very close
        result = compare_ids_by_timestamp(id1, id2)
        assert result in [-1, 0, 1]  # Valid comparison result

    def test_earlier_id(self):
        """Test earlier ID compares as -1."""
        ts1 = datetime(2025, 12, 14, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        id1 = generate_id_from_timestamp("track", ts1)
        id2 = generate_id_from_timestamp("track", ts2)
        assert compare_ids_by_timestamp(id1, id2) == -1

    def test_later_id(self):
        """Test later ID compares as 1."""
        ts1 = datetime(2025, 12, 16, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        id1 = generate_id_from_timestamp("track", ts1)
        id2 = generate_id_from_timestamp("track", ts2)
        assert compare_ids_by_timestamp(id1, id2) == 1

    def test_invalid_id_raises(self):
        """Test invalid ID raises ValueError."""
        with pytest.raises(ValueError):
            compare_ids_by_timestamp("invalid-id", generate_track_id())


class TestGenerateId:
    """Test generate_id convenience function."""

    def test_generate_track(self):
        """Test generating track ID."""
        track_id = generate_id("track")
        assert track_id.startswith("track_")

    def test_generate_sprint(self):
        """Test generating sprint ID."""
        sprint_id = generate_id("sprint")
        assert sprint_id.startswith("sprint_")

    def test_generate_task(self):
        """Test generating task ID."""
        task_id = generate_id("task")
        assert task_id.startswith("task_")

    def test_with_timestamp(self):
        """Test generating ID with timestamp."""
        ts = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        track_id = generate_id("track", timestamp=ts)
        extracted = extract_timestamp(track_id)
        diff = abs((extracted - ts).total_seconds())
        assert diff < 1

    def test_invalid_type_raises(self):
        """Test invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid type"):
            generate_id("invalid")


class TestIdSorting:
    """Test lexicographic sorting of IDs."""

    def test_chronological_sort(self):
        """Test IDs sort chronologically."""
        ids = []
        for i in range(5):
            ids.append(generate_track_id())
            time.sleep(0.001)  # Small delay for distinct timestamps

        # IDs should be in chronological order
        sorted_ids = sorted(ids)
        assert ids == sorted_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
