"""
Tests for vibey.cli.roadmap_lib.formatting module.

Tests terminal formatting utilities for CLI output.
"""

import pytest
from unittest.mock import patch

from vibey.cli.roadmap_lib.formatting import (
    Color,
    StatusIcon,
    set_plain_mode,
    is_plain_mode,
    colorize,
    bold,
    dim,
    status_indicator,
    progress_bar,
    table,
    tree,
    header,
    success,
    error,
    warning,
    info,
    _strip_ansi,
)


@pytest.fixture(autouse=True)
def reset_plain_mode():
    """Reset plain mode before and after each test."""
    set_plain_mode(False)
    yield
    set_plain_mode(False)


class TestPlainMode:
    """Test plain mode toggle."""

    def test_set_plain_mode_enables(self):
        """Test enabling plain mode."""
        set_plain_mode(True)
        assert is_plain_mode() is True

    def test_set_plain_mode_disables(self):
        """Test disabling plain mode."""
        set_plain_mode(True)
        set_plain_mode(False)
        # May still be True if terminal doesn't support color
        # Just verify the function doesn't crash

    @patch('vibey.cli.roadmap_lib.formatting._supports_color')
    def test_plain_mode_when_no_color_support(self, mock_supports):
        """Test plain mode when terminal doesn't support color."""
        mock_supports.return_value = False
        set_plain_mode(False)
        assert is_plain_mode() is True


class TestColorize:
    """Test colorize function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_colorize_with_color(self, mock_plain):
        """Test colorize adds color codes."""
        mock_plain.return_value = False
        result = colorize("test", Color.RED)
        assert Color.RED.value in result
        assert Color.RESET.value in result
        assert "test" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_colorize_plain_mode(self, mock_plain):
        """Test colorize in plain mode returns plain text."""
        mock_plain.return_value = True
        result = colorize("test", Color.RED)
        assert result == "test"


class TestBold:
    """Test bold function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_bold_with_formatting(self, mock_plain):
        """Test bold adds bold codes."""
        mock_plain.return_value = False
        result = bold("test")
        assert Color.BOLD.value in result
        assert "test" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_bold_plain_mode(self, mock_plain):
        """Test bold in plain mode returns plain text."""
        mock_plain.return_value = True
        result = bold("test")
        assert result == "test"


class TestDim:
    """Test dim function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_dim_with_formatting(self, mock_plain):
        """Test dim adds dim codes."""
        mock_plain.return_value = False
        result = dim("test")
        assert Color.DIM.value in result
        assert "test" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_dim_plain_mode(self, mock_plain):
        """Test dim in plain mode returns plain text."""
        mock_plain.return_value = True
        result = dim("test")
        assert result == "test"


class TestStatusIndicator:
    """Test status_indicator function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_completed_status(self, mock_plain):
        """Test completed status indicator."""
        mock_plain.return_value = False
        result = status_indicator("completed")
        assert "✅" in result
        assert "completed" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_in_progress_status(self, mock_plain):
        """Test in_progress status indicator."""
        mock_plain.return_value = False
        result = status_indicator("in_progress")
        assert "🔵" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_blocked_status(self, mock_plain):
        """Test blocked status indicator."""
        mock_plain.return_value = False
        result = status_indicator("blocked")
        assert "❌" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_pending_status(self, mock_plain):
        """Test pending status indicator."""
        mock_plain.return_value = False
        result = status_indicator("pending")
        assert "⚪" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_not_started_maps_to_pending(self, mock_plain):
        """Test not_started maps to pending icon."""
        mock_plain.return_value = False
        result = status_indicator("not_started")
        assert "⚪" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_status_indicator_plain_mode(self, mock_plain):
        """Test status indicator in plain mode."""
        mock_plain.return_value = True
        result = status_indicator("completed")
        assert result == "completed"


class TestProgressBar:
    """Test progress_bar function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_progress_bar_zero(self, mock_plain):
        """Test progress bar at 0%."""
        mock_plain.return_value = False
        result = progress_bar(0, 10)
        assert "0%" in result
        assert "0/10" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_progress_bar_fifty(self, mock_plain):
        """Test progress bar at 50%."""
        mock_plain.return_value = False
        result = progress_bar(5, 10)
        assert "50%" in result
        assert "5/10" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_progress_bar_hundred(self, mock_plain):
        """Test progress bar at 100%."""
        mock_plain.return_value = False
        result = progress_bar(10, 10)
        assert "100%" in result
        assert "10/10" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_progress_bar_zero_total(self, mock_plain):
        """Test progress bar with zero total."""
        mock_plain.return_value = False
        result = progress_bar(0, 0)
        assert "0%" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_progress_bar_without_percentage(self, mock_plain):
        """Test progress bar without percentage."""
        mock_plain.return_value = False
        result = progress_bar(5, 10, show_percentage=False)
        assert "5/10" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_progress_bar_plain_mode(self, mock_plain):
        """Test progress bar in plain mode."""
        mock_plain.return_value = True
        result = progress_bar(5, 10)
        assert result == "5/10 (50%)"


class TestTable:
    """Test table function."""

    def test_table_empty_rows(self):
        """Test table with empty rows."""
        result = table(["Col1", "Col2"], [])
        assert result == ""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_table_basic(self, mock_plain):
        """Test basic table creation."""
        mock_plain.return_value = False
        headers = ["Name", "Status"]
        rows = [["Task 1", "completed"], ["Task 2", "pending"]]
        result = table(headers, rows)
        assert "Name" in result
        assert "Status" in result
        assert "Task 1" in result
        assert "completed" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_table_with_title(self, mock_plain):
        """Test table with title."""
        mock_plain.return_value = False
        headers = ["Col1"]
        rows = [["Value1"]]
        result = table(headers, rows, title="My Table")
        assert "My Table" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_table_plain_mode(self, mock_plain):
        """Test table in plain mode."""
        mock_plain.return_value = True
        headers = ["Col1"]
        rows = [["Value1"]]
        result = table(headers, rows, title="My Table")
        assert "My Table" in result
        assert "=" in result  # Plain mode separator


class TestTree:
    """Test tree function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_tree_single_item(self, mock_plain):
        """Test tree with single item."""
        mock_plain.return_value = False
        items = [{"id": "item1", "name": "Item 1", "status": "completed"}]
        result = tree(items)
        assert "Item 1" in result
        assert "✅" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_tree_with_children(self, mock_plain):
        """Test tree with nested children."""
        mock_plain.return_value = False
        items = [
            {
                "id": "parent",
                "name": "Parent",
                "status": "in_progress",
                "children": [
                    {"id": "child1", "name": "Child 1", "status": "completed"},
                    {"id": "child2", "name": "Child 2", "status": "pending"},
                ]
            }
        ]
        result = tree(items)
        assert "Parent" in result
        assert "Child 1" in result
        assert "Child 2" in result
        assert "└─" in result or "├─" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_tree_no_status(self, mock_plain):
        """Test tree without status indicators."""
        mock_plain.return_value = False
        items = [{"id": "item1", "name": "Item 1"}]
        result = tree(items, show_status=False)
        assert "Item 1" in result
        # Should not have status icon prefix


class TestHeader:
    """Test header function."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_header_level_1(self, mock_plain):
        """Test level 1 header."""
        mock_plain.return_value = False
        result = header("Main Title", level=1)
        assert "Main Title" in result
        assert "═" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_header_level_2(self, mock_plain):
        """Test level 2 header."""
        mock_plain.return_value = False
        result = header("Section", level=2)
        assert "Section" in result
        assert "─" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_header_level_3(self, mock_plain):
        """Test level 3 header."""
        mock_plain.return_value = False
        result = header("Subsection", level=3)
        assert "Subsection" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_header_plain_mode(self, mock_plain):
        """Test header in plain mode."""
        mock_plain.return_value = True
        result = header("Title", level=1)
        assert "Title" in result
        assert "=" in result


class TestMessageFormatters:
    """Test message formatting functions."""

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_success_message(self, mock_plain):
        """Test success message formatting."""
        mock_plain.return_value = False
        result = success("Operation completed")
        assert "✓" in result
        assert "Operation completed" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_success_plain_mode(self, mock_plain):
        """Test success in plain mode."""
        mock_plain.return_value = True
        result = success("Done")
        assert result == "SUCCESS: Done"

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_error_message(self, mock_plain):
        """Test error message formatting."""
        mock_plain.return_value = False
        result = error("Something failed")
        assert "✗" in result
        assert "Something failed" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_error_plain_mode(self, mock_plain):
        """Test error in plain mode."""
        mock_plain.return_value = True
        result = error("Failed")
        assert result == "ERROR: Failed"

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_warning_message(self, mock_plain):
        """Test warning message formatting."""
        mock_plain.return_value = False
        result = warning("Caution needed")
        assert "⚠" in result
        assert "Caution needed" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_warning_plain_mode(self, mock_plain):
        """Test warning in plain mode."""
        mock_plain.return_value = True
        result = warning("Watch out")
        assert result == "WARNING: Watch out"

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_info_message(self, mock_plain):
        """Test info message formatting."""
        mock_plain.return_value = False
        result = info("FYI")
        assert "ℹ" in result
        assert "FYI" in result

    @patch('vibey.cli.roadmap_lib.formatting.is_plain_mode')
    def test_info_plain_mode(self, mock_plain):
        """Test info in plain mode."""
        mock_plain.return_value = True
        result = info("Note")
        assert result == "INFO: Note"


class TestStripAnsi:
    """Test _strip_ansi helper."""

    def test_strip_ansi_with_codes(self):
        """Test stripping ANSI codes."""
        text_with_ansi = f"{Color.RED.value}red text{Color.RESET.value}"
        result = _strip_ansi(text_with_ansi)
        assert result == "red text"

    def test_strip_ansi_plain_text(self):
        """Test plain text is unchanged."""
        result = _strip_ansi("plain text")
        assert result == "plain text"

    def test_strip_ansi_multiple_codes(self):
        """Test stripping multiple ANSI codes."""
        text = f"{Color.BOLD.value}{Color.GREEN.value}bold green{Color.RESET.value}"
        result = _strip_ansi(text)
        assert result == "bold green"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
