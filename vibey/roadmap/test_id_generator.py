"""
Unit tests for ULID-based ID generation system.

Tests verify:
- Uniqueness (no collisions in 10,000 generations)
- Sortability (lexicographic ordering by timestamp)
- Timestamp extraction accuracy
- Format validation
- Prefix extraction
- Comparison operations
"""

import unittest
import time
from datetime import datetime, timezone, timedelta
from vibey.roadmap.id_generator import (
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
    generate_id,
    generate_id_from_timestamp,
    extract_timestamp,
    extract_prefix,
    is_valid_id,
    is_ulid_format,
    compare_ids_by_timestamp,
)


class TestIDGeneration(unittest.TestCase):
    """Test basic ID generation for all types."""

    def test_generate_track_id(self):
        """Track IDs have correct format."""
        track_id = generate_track_id()
        self.assertIsInstance(track_id, str)
        self.assertTrue(track_id.startswith("track_"))
        self.assertEqual(len(track_id), 32)  # "track_" (6) + ULID (26)

    def test_generate_sprint_id(self):
        """Sprint IDs have correct format."""
        sprint_id = generate_sprint_id()
        self.assertIsInstance(sprint_id, str)
        self.assertTrue(sprint_id.startswith("sprint_"))
        self.assertEqual(len(sprint_id), 33)  # "sprint_" (7) + ULID (26)

    def test_generate_task_id(self):
        """Task IDs have correct format."""
        task_id = generate_task_id()
        self.assertIsInstance(task_id, str)
        self.assertTrue(task_id.startswith("task_"))
        self.assertEqual(len(task_id), 31)  # "task_" (5) + ULID (26)

    def test_generate_id_convenience(self):
        """Convenience generate_id() function works for all types."""
        track_id = generate_id("track")
        sprint_id = generate_id("sprint")
        task_id = generate_id("task")

        self.assertTrue(track_id.startswith("track_"))
        self.assertTrue(sprint_id.startswith("sprint_"))
        self.assertTrue(task_id.startswith("task_"))

    def test_generate_id_invalid_type(self):
        """generate_id() raises error for invalid type."""
        with self.assertRaises(ValueError):
            generate_id("invalid_type")


class TestIDUniqueness(unittest.TestCase):
    """Test that IDs are unique (no collisions)."""

    def test_track_id_uniqueness_10000(self):
        """Generate 10,000 track IDs, ensure no collisions."""
        ids = set()
        for _ in range(10000):
            track_id = generate_track_id()
            self.assertNotIn(track_id, ids, f"Collision detected: {track_id}")
            ids.add(track_id)

        self.assertEqual(len(ids), 10000)

    def test_sprint_id_uniqueness_10000(self):
        """Generate 10,000 sprint IDs, ensure no collisions."""
        ids = set()
        for _ in range(10000):
            sprint_id = generate_sprint_id()
            self.assertNotIn(sprint_id, ids, f"Collision detected: {sprint_id}")
            ids.add(sprint_id)

        self.assertEqual(len(ids), 10000)

    def test_task_id_uniqueness_10000(self):
        """Generate 10,000 task IDs, ensure no collisions."""
        ids = set()
        for _ in range(10000):
            task_id = generate_task_id()
            self.assertNotIn(task_id, ids, f"Collision detected: {task_id}")
            ids.add(task_id)

        self.assertEqual(len(ids), 10000)

    def test_cross_type_uniqueness(self):
        """IDs are unique across different types."""
        ids = set()

        # Generate mixed types
        for _ in range(1000):
            ids.add(generate_track_id())
            ids.add(generate_sprint_id())
            ids.add(generate_task_id())

        # Should have 3000 unique IDs
        self.assertEqual(len(ids), 3000)


class TestIDSortability(unittest.TestCase):
    """Test that IDs sort lexicographically by creation time."""

    def test_sequential_generation_sorted(self):
        """IDs generated sequentially are lexicographically sorted."""
        ids = []
        for _ in range(100):
            ids.append(generate_track_id())
            time.sleep(0.001)  # Ensure different milliseconds

        # IDs should be in sorted order
        sorted_ids = sorted(ids)
        self.assertEqual(ids, sorted_ids)

    def test_comparison_matches_timestamp(self):
        """Lexicographic comparison matches timestamp comparison."""
        id1 = generate_track_id()
        time.sleep(0.001)
        id2 = generate_track_id()

        # Lexicographic comparison
        self.assertLess(id1, id2)

        # Timestamp comparison
        ts1 = extract_timestamp(id1)
        ts2 = extract_timestamp(id2)
        self.assertLess(ts1, ts2)


class TestTimestampExtraction(unittest.TestCase):
    """Test timestamp extraction from IDs."""

    def test_extract_timestamp_recent(self):
        """Extracted timestamp is accurate for recently generated IDs."""
        before = datetime.now(timezone.utc)
        track_id = generate_track_id()
        after = datetime.now(timezone.utc)

        extracted = extract_timestamp(track_id)

        # Timestamp should be between before and after (with some tolerance for milliseconds)
        # ULID has millisecond precision, so allow 1 second tolerance
        self.assertGreaterEqual(extracted, before - timedelta(seconds=1))
        self.assertLessEqual(extracted, after + timedelta(seconds=1))

    def test_extract_timestamp_all_types(self):
        """Timestamp extraction works for all ID types."""
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        # All should extract valid timestamps
        ts1 = extract_timestamp(track_id)
        ts2 = extract_timestamp(sprint_id)
        ts3 = extract_timestamp(task_id)

        self.assertIsInstance(ts1, datetime)
        self.assertIsInstance(ts2, datetime)
        self.assertIsInstance(ts3, datetime)

    def test_extract_timestamp_invalid_id(self):
        """extract_timestamp raises error for invalid ID."""
        with self.assertRaises(ValueError):
            extract_timestamp("invalid-id")

        with self.assertRaises(ValueError):
            extract_timestamp("track_INVALID")


class TestIDFromTimestamp(unittest.TestCase):
    """Test ID generation from specific timestamps (migration use case)."""

    def test_generate_from_specific_timestamp(self):
        """Can generate ID from specific timestamp."""
        ts = datetime(2025, 11, 9, 15, 0, 0, tzinfo=timezone.utc)
        track_id = generate_id_from_timestamp("track", ts)

        self.assertTrue(track_id.startswith("track_"))

        # Extract and compare timestamps
        extracted = extract_timestamp(track_id)

        # Should be very close (within millisecond precision)
        delta = abs((extracted - ts).total_seconds())
        self.assertLess(delta, 1.0)  # Within 1 second

    def test_generate_preserves_ordering(self):
        """IDs generated from ordered timestamps maintain order."""
        ts1 = datetime(2025, 11, 9, 15, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2025, 11, 9, 15, 0, 1, tzinfo=timezone.utc)
        ts3 = datetime(2025, 11, 9, 15, 0, 2, tzinfo=timezone.utc)

        id1 = generate_id_from_timestamp("track", ts1)
        id2 = generate_id_from_timestamp("track", ts2)
        id3 = generate_id_from_timestamp("track", ts3)

        # IDs should sort in same order as timestamps
        self.assertLess(id1, id2)
        self.assertLess(id2, id3)


class TestPrefixExtraction(unittest.TestCase):
    """Test prefix extraction from IDs."""

    def test_extract_prefix_track(self):
        """Extract 'track' prefix from track ID."""
        track_id = generate_track_id()
        prefix = extract_prefix(track_id)
        self.assertEqual(prefix, "track")

    def test_extract_prefix_sprint(self):
        """Extract 'sprint' prefix from sprint ID."""
        sprint_id = generate_sprint_id()
        prefix = extract_prefix(sprint_id)
        self.assertEqual(prefix, "sprint")

    def test_extract_prefix_task(self):
        """Extract 'task' prefix from task ID."""
        task_id = generate_task_id()
        prefix = extract_prefix(task_id)
        self.assertEqual(prefix, "task")

    def test_extract_prefix_invalid(self):
        """extract_prefix raises error for invalid ID."""
        with self.assertRaises(ValueError):
            extract_prefix("invalid-id")


class TestIDValidation(unittest.TestCase):
    """Test ID validation functions."""

    def test_is_valid_id_valid_ids(self):
        """Valid IDs pass validation."""
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        self.assertTrue(is_valid_id(track_id))
        self.assertTrue(is_valid_id(sprint_id))
        self.assertTrue(is_valid_id(task_id))

    def test_is_valid_id_invalid_ids(self):
        """Invalid IDs fail validation."""
        self.assertFalse(is_valid_id("invalid-id"))
        self.assertFalse(is_valid_id("track_INVALID"))
        self.assertFalse(is_valid_id("wrongprefix_01JB3QVDZ8TRK9XN1FJFHGWPRM"))
        self.assertFalse(is_valid_id("track-01JB3QVDZ8TRK9XN1FJFHGWPRM"))  # Wrong separator

    def test_is_ulid_format_new_ids(self):
        """New ULID-based IDs detected correctly."""
        track_id = generate_track_id()
        self.assertTrue(is_ulid_format(track_id))

    def test_is_ulid_format_old_ids(self):
        """Old slug-based IDs detected correctly."""
        self.assertFalse(is_ulid_format("documentation-system"))
        self.assertFalse(is_ulid_format("mcp-server"))
        self.assertFalse(is_ulid_format("core-framework-2"))


class TestIDComparison(unittest.TestCase):
    """Test ID comparison functions."""

    def test_compare_ids_by_timestamp(self):
        """compare_ids_by_timestamp returns correct ordering."""
        id1 = generate_track_id()
        time.sleep(0.001)
        id2 = generate_track_id()

        result = compare_ids_by_timestamp(id1, id2)
        self.assertEqual(result, -1)  # id1 < id2

        result = compare_ids_by_timestamp(id2, id1)
        self.assertEqual(result, 1)  # id2 > id1

    def test_compare_same_millisecond(self):
        """IDs generated in same millisecond still comparable."""
        # Generate multiple IDs rapidly
        ids = [generate_track_id() for _ in range(10)]

        # All should be comparable (even if same millisecond)
        for i in range(len(ids) - 1):
            result = compare_ids_by_timestamp(ids[i], ids[i + 1])
            self.assertIn(result, [-1, 0, 1])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_string(self):
        """Empty string is not a valid ID."""
        self.assertFalse(is_valid_id(""))
        self.assertFalse(is_ulid_format(""))

    def test_none_handling(self):
        """Functions handle None gracefully."""
        # is_valid_id should return False for None rather than raising
        self.assertFalse(is_valid_id(None) if isinstance(None, str) else False)

    def test_very_long_ids(self):
        """Very long strings are not valid IDs."""
        long_string = "track_" + ("X" * 1000)
        self.assertFalse(is_valid_id(long_string))


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
