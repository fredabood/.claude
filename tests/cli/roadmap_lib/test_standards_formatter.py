"""
Tests for vibey.cli.roadmap_lib.standards_formatter module.

Tests standards formatting utilities for CLI display.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import actual enums from the models
from vibey.roadmap.models import EnforcementMode
from vibey.roadmap.standards.validator_base import ValidationStatus

from vibey.cli.roadmap_lib.standards_formatter import (
    format_enforcement,
    format_validation_status,
    format_source_level,
    format_standards_summary,
    format_standards_compliance,
    get_standards_for_item,
    get_standards_compliance_data,
)


class TestFormatEnforcement:
    """Test format_enforcement function."""

    def test_blocking_enforcement(self):
        """Test blocking enforcement format."""
        result = format_enforcement(EnforcementMode.BLOCKING)
        assert "BLOCKING" in result
        assert result.startswith("🔴")

    def test_warning_enforcement(self):
        """Test warning enforcement format."""
        result = format_enforcement(EnforcementMode.WARNING)
        assert "WARNING" in result
        assert result.startswith("🟡")

    def test_audit_enforcement(self):
        """Test audit enforcement format."""
        result = format_enforcement(EnforcementMode.AUDIT)
        assert "AUDIT" in result
        assert result.startswith("🟢")


class TestFormatValidationStatus:
    """Test format_validation_status function."""

    def test_passed_status(self):
        """Test passed validation status."""
        result = format_validation_status(ValidationStatus.PASSED)
        assert result == "✅"

    def test_failed_status(self):
        """Test failed validation status."""
        result = format_validation_status(ValidationStatus.FAILED)
        assert result == "❌"

    def test_skipped_status(self):
        """Test skipped validation status."""
        result = format_validation_status(ValidationStatus.SKIPPED)
        assert result == "⏭️"

    def test_error_status(self):
        """Test error validation status."""
        result = format_validation_status(ValidationStatus.ERROR)
        assert result == "💥"


class TestFormatSourceLevel:
    """Test format_source_level function."""

    def test_roadmap_level(self):
        """Test roadmap source level format."""
        result = format_source_level('roadmap')
        assert 'roadmap' in result
        assert '🗺️' in result

    def test_track_level(self):
        """Test track source level format."""
        result = format_source_level('track')
        assert 'track' in result
        assert '🛤️' in result

    def test_sprint_level(self):
        """Test sprint source level format."""
        result = format_source_level('sprint')
        assert 'sprint' in result
        assert '🏃' in result

    def test_unknown_level(self):
        """Test unknown source level format."""
        result = format_source_level('unknown')
        assert 'unknown' in result
        assert '❓' in result


class TestFormatStandardsSummary:
    """Test format_standards_summary function."""

    def test_no_standards(self):
        """Test summary with no standards."""
        result = format_standards_summary([])
        assert result == "No standards"

    def test_single_blocking_standard(self):
        """Test summary with single blocking standard."""
        standard = MagicMock()
        standard.enforcement = EnforcementMode.BLOCKING

        result = format_standards_summary([standard])

        assert "1 standards" in result
        assert "blocking" in result

    def test_mixed_enforcement_standards(self):
        """Test summary with mixed enforcement modes."""
        blocking = MagicMock()
        blocking.enforcement = EnforcementMode.BLOCKING

        warning = MagicMock()
        warning.enforcement = EnforcementMode.WARNING

        audit = MagicMock()
        audit.enforcement = EnforcementMode.AUDIT

        result = format_standards_summary([blocking, warning, audit])

        assert "3 standards" in result
        assert "blocking" in result
        assert "warning" in result
        assert "audit" in result

    def test_compact_format(self):
        """Test compact summary format."""
        standard = MagicMock()
        standard.enforcement = EnforcementMode.BLOCKING

        compact = format_standards_summary([standard], compact=True)
        full = format_standards_summary([standard], compact=False)

        # Compact uses parentheses, full uses colon
        assert "(" in compact
        assert ":" in full


class TestFormatStandardsCompliance:
    """Test format_standards_compliance function."""

    def test_no_standards(self):
        """Test compliance with no standards."""
        result = format_standards_compliance(0, 0)
        assert result == "No standards"

    def test_all_passing(self):
        """Test 100% compliance."""
        result = format_standards_compliance(10, 10)
        assert "✅" in result
        assert "10/10" in result
        assert "100%" in result

    def test_with_blocking_failures(self):
        """Test compliance with blocking failures."""
        result = format_standards_compliance(7, 10, blocking_failures=2)
        assert "❌" in result
        assert "7/10" in result
        assert "blocking failures" in result

    def test_with_warnings_only(self):
        """Test compliance with warnings but no blockers."""
        result = format_standards_compliance(8, 10, warnings=2)
        assert "⚠️" in result
        assert "8/10" in result
        assert "warnings" in result

    def test_with_both_failures_and_warnings(self):
        """Test compliance with both failures and warnings."""
        result = format_standards_compliance(6, 10, blocking_failures=2, warnings=2)
        assert "❌" in result  # Blockers take precedence
        assert "blocking failures" in result
        assert "warnings" in result

    def test_percentage_calculation(self):
        """Test percentage is calculated correctly."""
        result = format_standards_compliance(3, 4)
        assert "75%" in result


class TestGetStandardsForItem:
    """Test get_standards_for_item function."""

    @patch('vibey.cli.roadmap_lib.standards_formatter.StandardsResolver')
    def test_get_standards_for_task(self, mock_resolver_cls):
        """Test getting standards for a task."""
        mock_resolver = MagicMock()
        mock_resolver.resolve_for_task.return_value = []
        mock_resolver_cls.return_value = mock_resolver

        result = get_standards_for_item(Path("/test"), "sprint-1-task-001")

        mock_resolver.resolve_for_task.assert_called_once_with("sprint-1-task-001")

    @patch('vibey.cli.roadmap_lib.standards_formatter.StandardsResolver')
    def test_get_standards_for_sprint(self, mock_resolver_cls):
        """Test getting standards for a sprint."""
        mock_resolver = MagicMock()
        mock_resolver.resolve_for_sprint.return_value = []
        mock_resolver_cls.return_value = mock_resolver

        result = get_standards_for_item(Path("/test"), "sprint-1")

        mock_resolver.resolve_for_sprint.assert_called_once_with("sprint-1")

    @patch('vibey.cli.roadmap_lib.standards_formatter.StandardsResolver')
    def test_get_standards_for_track(self, mock_resolver_cls):
        """Test getting standards for a track."""
        mock_resolver = MagicMock()
        mock_resolver.resolve_for_track.return_value = []
        mock_resolver_cls.return_value = mock_resolver

        result = get_standards_for_item(Path("/test"), "backend")

        mock_resolver.resolve_for_track.assert_called_once_with("backend")

    @patch('vibey.cli.roadmap_lib.standards_formatter.StandardsResolver')
    def test_get_standards_handles_exception(self, mock_resolver_cls):
        """Test that exceptions return empty list."""
        mock_resolver_cls.side_effect = Exception("Resolver error")

        result = get_standards_for_item(Path("/test"), "task-001")

        assert result == []


class TestGetStandardsComplianceData:
    """Test get_standards_compliance_data function."""

    @patch('vibey.cli.roadmap_lib.standards_formatter.get_standards_for_item')
    def test_empty_standards(self, mock_get):
        """Test compliance data with no standards."""
        mock_get.return_value = []

        result = get_standards_compliance_data(Path("/test"), "task-001")

        assert result['total'] == 0
        assert result['blocking_count'] == 0
        assert result['warning_count'] == 0
        assert result['audit_count'] == 0
        assert result['standards'] == []

    @patch('vibey.cli.roadmap_lib.standards_formatter.get_standards_for_item')
    def test_with_plain_standards(self, mock_get):
        """Test compliance data with plain Standard objects."""
        # Create mock standard
        standard = MagicMock()
        standard.id = "std-001"
        standard.name = "Test Standard"
        standard.type = MagicMock()
        standard.type.value = "quality"
        standard.enforcement = EnforcementMode.BLOCKING
        standard.has_overrides.return_value = False

        mock_get.return_value = [standard]

        result = get_standards_compliance_data(Path("/test"), "task-001")

        assert result['total'] == 1
        assert result['blocking_count'] == 1
        assert len(result['standards']) == 1
        assert result['standards'][0]['id'] == "std-001"

    @patch('vibey.cli.roadmap_lib.standards_formatter.get_standards_for_item')
    def test_counts_by_enforcement(self, mock_get):
        """Test correct counting by enforcement mode."""
        blocking1 = MagicMock()
        blocking1.enforcement = EnforcementMode.BLOCKING
        blocking1.id = "b1"
        blocking1.name = "Blocking 1"
        blocking1.type = MagicMock(value="quality")
        blocking1.has_overrides.return_value = False

        blocking2 = MagicMock()
        blocking2.enforcement = EnforcementMode.BLOCKING
        blocking2.id = "b2"
        blocking2.name = "Blocking 2"
        blocking2.type = MagicMock(value="quality")
        blocking2.has_overrides.return_value = False

        warning = MagicMock()
        warning.enforcement = EnforcementMode.WARNING
        warning.id = "w1"
        warning.name = "Warning"
        warning.type = MagicMock(value="quality")
        warning.has_overrides.return_value = False

        mock_get.return_value = [blocking1, blocking2, warning]

        result = get_standards_compliance_data(Path("/test"), "item-001")

        assert result['total'] == 3
        assert result['blocking_count'] == 2
        assert result['warning_count'] == 1
        assert result['audit_count'] == 0


class TestIntegration:
    """Integration tests for standards formatter."""

    def test_enforcement_modes_all_covered(self):
        """Test all enforcement modes have formatting."""
        for mode in EnforcementMode:
            result = format_enforcement(mode)
            assert len(result) > 0
            # Should contain an emoji
            assert any(c for c in result if ord(c) > 127)

    def test_validation_statuses_all_covered(self):
        """Test all validation statuses have formatting."""
        for status in ValidationStatus:
            result = format_validation_status(status)
            assert len(result) > 0

    def test_source_levels_all_covered(self):
        """Test all standard source levels have formatting."""
        for level in ['roadmap', 'track', 'sprint']:
            result = format_source_level(level)
            assert level in result

    def test_compliance_string_is_informative(self):
        """Test compliance strings contain useful information."""
        result = format_standards_compliance(
            passed=8,
            total=10,
            blocking_failures=1,
            warnings=1
        )

        # Should contain counts
        assert "8/10" in result
        # Should contain percentage
        assert "80%" in result
        # Should indicate failures
        assert "blocking" in result.lower()

    def test_summary_with_multiple_standards(self):
        """Test summary correctly aggregates multiple standards."""
        standards = []
        for _ in range(3):
            s = MagicMock()
            s.enforcement = EnforcementMode.BLOCKING
            standards.append(s)
        for _ in range(2):
            s = MagicMock()
            s.enforcement = EnforcementMode.WARNING
            standards.append(s)

        result = format_standards_summary(standards)

        assert "5 standards" in result
        assert "3 blocking" in result
        assert "2 warning" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
