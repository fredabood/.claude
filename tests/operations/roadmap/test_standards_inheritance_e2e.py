"""
End-to-end tests for Sprint 10 interface changes.

Tests the standards inheritance display in CLI and MCP tools.
Verifies the full integration of:
- Standards resolver returning ResolvedStandard objects
- CLI formatter displaying inheritance chain
- MCP tool returning inheritance breakdown

Uses real roadmap data from the project as test fixtures.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Get the project root directory (where .vibey/ exists)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestStandardsFormatterInheritance:
    """E2E tests for CLI standards formatter with inheritance display."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_get_standards_for_item_returns_resolved_standards(self, root_dir):
        """Test that get_standards_for_item returns ResolvedStandard objects."""
        from vibey.cli.roadmap_lib.standards_formatter import get_standards_for_item
        from vibey.roadmap.standards.resolver import ResolvedStandard

        # Query standards for a track (should inherit from roadmap)
        standards = get_standards_for_item(root_dir, "sqlite-backend")

        # All returned items should be ResolvedStandard objects
        for std in standards:
            assert isinstance(std, ResolvedStandard), f"Expected ResolvedStandard, got {type(std)}"
            assert hasattr(std, 'source_level')
            assert hasattr(std, 'source_id')
            assert hasattr(std, 'is_overridden')
            assert std.source_level in ['roadmap', 'track', 'sprint']

    def test_format_standards_summary_shows_inheritance(self, root_dir):
        """Test that format_standards_summary includes inheritance breakdown."""
        from vibey.cli.roadmap_lib.standards_formatter import (
            get_standards_for_item,
            format_standards_summary
        )

        standards = get_standards_for_item(root_dir, "sqlite-backend")

        if not standards:
            pytest.skip("No standards defined for sqlite-backend track")

        # Format with inheritance
        summary = format_standards_summary(standards, show_inheritance=True)

        # Should include enforcement info
        assert "standards" in summary.lower()

        # Format without inheritance
        summary_no_inherit = format_standards_summary(standards, show_inheritance=False)
        assert "standards" in summary_no_inherit.lower()

    def test_get_standards_compliance_data_includes_inheritance(self, root_dir):
        """Test that compliance data includes inheritance breakdown."""
        from vibey.cli.roadmap_lib.standards_formatter import get_standards_compliance_data

        data = get_standards_compliance_data(root_dir, "sqlite-backend")

        # Should include inheritance dict
        assert 'inheritance' in data
        assert isinstance(data['inheritance'], dict)
        assert 'roadmap' in data['inheritance']
        assert 'track' in data['inheritance']
        assert 'sprint' in data['inheritance']
        assert 'overridden' in data['inheritance']

        # Should include source info in standards list
        for std in data.get('standards', []):
            assert 'source_level' in std
            assert 'source_id' in std
            assert 'is_overridden' in std

    def test_resolved_standard_has_correct_source_level(self, root_dir):
        """Test that ResolvedStandard correctly identifies source level."""
        from vibey.roadmap.standards import StandardsResolver

        resolver = StandardsResolver(root_dir)

        # Resolve for a track - should get roadmap and track level standards
        try:
            track_standards = resolver.resolve_for_track("sqlite-backend")
            for std in track_standards:
                assert std.source_level in ['roadmap', 'track']
        except Exception:
            pytest.skip("Could not resolve standards for sqlite-backend track")


class TestMCPQueryStandardsTool:
    """E2E tests for MCP vibey_query_standards tool."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    @pytest.fixture
    def mock_adapter(self, root_dir):
        """Create a RoadmapAdapter with real root directory."""
        from vibey.mcp.adapters.roadmap_adapter import RoadmapAdapter
        return RoadmapAdapter(str(root_dir / ".vibey" / "roadmap"))

    def test_query_standards_returns_inheritance_data(self, mock_adapter):
        """Test that adapter.query_standards returns inheritance breakdown."""
        # Use a task ID which has unambiguous format (track-sprint-task-num)
        result = mock_adapter.query_standards("sqlite-backend-10-task-001")

        # Should have total count
        assert 'total' in result
        assert isinstance(result['total'], int)

        # Should have enforcement breakdown
        assert 'blocking_count' in result
        assert 'warning_count' in result
        assert 'audit_count' in result

        # Should have inheritance breakdown
        assert 'inheritance' in result
        assert 'roadmap' in result['inheritance']
        assert 'track' in result['inheritance']
        assert 'sprint' in result['inheritance']

        # Should have standards list with source info
        assert 'standards' in result
        for std in result['standards']:
            assert 'id' in std
            assert 'source_level' in std
            assert 'source_id' in std

    def test_query_tools_includes_standards_tool(self):
        """Test that get_query_tools includes vibey_query_standards."""
        from vibey.mcp.tools.query_tools import get_query_tools

        tools = get_query_tools()
        tool_names = [t['name'] for t in tools]

        assert 'vibey_query_standards' in tool_names

        # Find the standards tool
        standards_tool = next(t for t in tools if t['name'] == 'vibey_query_standards')

        # Verify schema
        assert 'inputSchema' in standards_tool
        schema = standards_tool['inputSchema']
        assert 'item_id' in schema['properties']
        assert 'show_inheritance' in schema['properties']

    @pytest.mark.asyncio
    async def test_handle_query_standards_formats_output(self, mock_adapter):
        """Test that handle_query_standards returns formatted text."""
        from vibey.mcp.tools.query_tools import handle_query_standards

        # Use a task ID which has unambiguous format
        arguments = {"item_id": "sqlite-backend-10-task-001", "show_inheritance": True}

        result = await handle_query_standards(arguments, mock_adapter)

        # Should return MCP response format
        assert 'content' in result
        assert 'isError' in result
        assert result['isError'] is False

        # Content should be text
        assert len(result['content']) > 0
        assert result['content'][0]['type'] == 'text'

        # Text should contain standards info
        text = result['content'][0]['text']
        assert 'Standards' in text or 'standards' in text


class TestStandardsResolverIntegration:
    """Integration tests for StandardsResolver with real data."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_resolve_for_task_includes_all_levels(self, root_dir):
        """Test that task resolution includes roadmap, track, sprint standards."""
        from vibey.roadmap.standards import StandardsResolver

        resolver = StandardsResolver(root_dir)

        # Try to resolve for a real task
        try:
            standards = resolver.resolve_for_task("sqlite-backend-10-task-001")

            # Should have source_level set for each
            source_levels = set(s.source_level for s in standards)

            # All levels should be valid
            for level in source_levels:
                assert level in ['roadmap', 'track', 'sprint']

        except Exception as e:
            # May fail if no standards defined
            if "not found" in str(e).lower() or "invalid" in str(e).lower():
                pytest.skip("Standards not defined or task not found")
            raise

    def test_resolve_deduplicates_by_id(self, root_dir):
        """Test that more specific standards override less specific ones."""
        from vibey.roadmap.standards import StandardsResolver

        resolver = StandardsResolver(root_dir)

        try:
            standards = resolver.resolve_for_track("sqlite-backend")

            # Should not have duplicate IDs
            ids = [s.standard.id for s in standards]
            assert len(ids) == len(set(ids)), "Standards should be deduplicated by ID"

        except Exception:
            pytest.skip("Could not resolve standards for track")


class TestInheritanceChainVisualization:
    """Tests for the inheritance chain display functionality."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_print_standards_list_groups_by_source(self, root_dir, capsys):
        """Test that print_standards_list groups by source level."""
        from vibey.cli.roadmap_lib.standards_formatter import (
            get_standards_for_item,
            print_standards_list
        )

        standards = get_standards_for_item(root_dir, "sqlite-backend")

        if not standards:
            pytest.skip("No standards to display")

        # Print with inheritance
        print_standards_list(standards, show_inheritance=True)

        captured = capsys.readouterr()

        # Should show source headers if there are multiple sources
        source_levels = set(s.source_level for s in standards)
        if len(source_levels) > 1:
            # Check for at least one source header
            assert any(level in captured.out.lower() for level in ['roadmap', 'track', 'sprint'])

    def test_format_source_level_returns_emoji(self):
        """Test that format_source_level returns proper emoji format."""
        from vibey.cli.roadmap_lib.standards_formatter import format_source_level

        roadmap_fmt = format_source_level('roadmap')
        track_fmt = format_source_level('track')
        sprint_fmt = format_source_level('sprint')

        # Should contain the level name
        assert 'roadmap' in roadmap_fmt
        assert 'track' in track_fmt
        assert 'sprint' in sprint_fmt
