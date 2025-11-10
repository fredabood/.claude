#!/usr/bin/env python3
"""
Test terminal formatting utilities.

Demonstrates all formatting features: colors, progress bars, tables, trees.
"""

import sys
from pathlib import Path

# Add roadmap-lib to path
test_dir = Path(__file__).parent
scripts_dir = test_dir.parent
roadmap_lib_dir = scripts_dir / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_dir))

from formatting import (
    status_indicator, progress_bar, table, tree,
    header, success, error, warning, info,
    colorize, bold, dim, Color, set_plain_mode
)


def test_status_indicators():
    """Test status indicators."""
    print(header("Status Indicators", level=1))

    statuses = ['completed', 'in_progress', 'pending', 'blocked', 'planning']
    for status in statuses:
        print(f"  {status_indicator(status)}")

    print()


def test_progress_bars():
    """Test progress bars."""
    print(header("Progress Bars", level=1))

    test_cases = [
        (0, 10, "0% - Empty"),
        (2, 10, "20% - Low"),
        (5, 10, "50% - Half"),
        (8, 10, "80% - High"),
        (10, 10, "100% - Complete"),
    ]

    for current, total, label in test_cases:
        bar = progress_bar(current, total)
        print(f"  {label:20} {bar}")

    print()


def test_tables():
    """Test table formatting."""
    print(header("Table Formatting", level=1))

    headers = ["Task ID", "Status", "Duration", "Progress"]
    rows = [
        ["task-001", status_indicator("completed"), "4h", progress_bar(4, 4, width=15, show_percentage=False)],
        ["task-002", status_indicator("in_progress"), "3h", progress_bar(2, 3, width=15, show_percentage=False)],
        ["task-003", status_indicator("pending"), "3h", progress_bar(0, 3, width=15, show_percentage=False)],
        ["task-004", status_indicator("blocked"), "2h", progress_bar(0, 2, width=15, show_percentage=False)],
    ]

    print(table(headers, rows, title="Sprint Tasks"))
    print()


def test_tree_view():
    """Test tree view."""
    print(header("Tree View (Dependencies)", level=1))

    items = [
        {
            'id': 'track-001',
            'name': 'Core Framework',
            'status': 'in_progress',
            'children': [
                {
                    'id': 'sprint-001',
                    'name': 'Foundation',
                    'status': 'completed',
                    'children': [
                        {'id': 'task-001', 'name': 'Setup', 'status': 'completed'},
                        {'id': 'task-002', 'name': 'Config', 'status': 'completed'},
                    ]
                },
                {
                    'id': 'sprint-002',
                    'name': 'Polish',
                    'status': 'in_progress',
                    'children': [
                        {'id': 'task-003', 'name': 'Caching', 'status': 'completed'},
                        {'id': 'task-004', 'name': 'Formatting', 'status': 'in_progress'},
                        {'id': 'task-005', 'name': 'Docs', 'status': 'pending'},
                    ]
                },
            ]
        }
    ]

    print(tree(items))
    print()


def test_messages():
    """Test message formatting."""
    print(header("Messages", level=1))

    print(f"  {success('Operation completed successfully')}")
    print(f"  {info('Loading configuration...')}")
    print(f"  {warning('Cache is stale, rebuilding...')}")
    print(f"  {error('Task not found: task-999')}")
    print()


def test_colors():
    """Test color formatting."""
    print(header("Colors and Styles", level=1))

    print(f"  {colorize('Red text', Color.RED)}")
    print(f"  {colorize('Green text', Color.GREEN)}")
    print(f"  {colorize('Yellow text', Color.YELLOW)}")
    print(f"  {colorize('Blue text', Color.BLUE)}")
    print(f"  {colorize('Cyan text', Color.CYAN)}")
    print(f"  {colorize('Magenta text', Color.MAGENTA)}")
    print(f"  {bold('Bold text')}")
    print(f"  {dim('Dimmed text')}")
    print()


def test_plain_mode():
    """Test plain mode (no colors)."""
    print("\n" + "="*70)
    print("PLAIN MODE (--plain flag)")
    print("="*70 + "\n")

    set_plain_mode(True)

    print("Status:", status_indicator("completed"))
    print("Progress:", progress_bar(7, 10))
    print("Success:", success("Task completed"))
    print("Error:", error("Task failed"))

    print("\n" + "="*70)
    print("Table in plain mode:")
    print("="*70 + "\n")

    headers = ["ID", "Status", "Progress"]
    rows = [
        ["task-001", status_indicator("completed"), progress_bar(10, 10, width=20)],
        ["task-002", status_indicator("in_progress"), progress_bar(5, 10, width=20)],
    ]
    print(table(headers, rows))

    set_plain_mode(False)


def main():
    """Run all formatting tests."""
    print("\n" + "="*70)
    print("Terminal Formatting Test Suite")
    print("="*70 + "\n")

    test_status_indicators()
    test_progress_bars()
    test_tables()
    test_tree_view()
    test_messages()
    test_colors()
    test_plain_mode()

    print("\n" + "="*70)
    print("✅ All formatting features demonstrated!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
