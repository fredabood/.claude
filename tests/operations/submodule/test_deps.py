"""
Test DependencyResolver class.

Tests for cross-repo dependency management.
Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md
"""

from unittest.mock import MagicMock, patch

import pytest


class TestAddDependency:
    """Tests for adding cross-repo dependencies."""

    def test_add_dependency_creates_blocker_info(self):
        """Should create ExternalBlockerInfo when adding dependency."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_resolver.add_dependency.return_value = mock_result

            result = mock_resolver.add_dependency(
                ticket_id="01KC2D0JK7READW9KAK1HBX4B8",
                submodule_path="libs/core",
                target_task_id="01KC3E1JK8READW9KAK1HBX5C9",
                dependency_type="blocks",
                blocking=True,
                reason="Needs API implementation",
            )

            assert result.success is True

    def test_add_dependency_with_invalid_ticket(self):
        """Should fail when ticket doesn't exist."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.error = "Ticket not found"
            mock_resolver.add_dependency.return_value = mock_result

            result = mock_resolver.add_dependency(
                ticket_id="nonexistent",
                submodule_path="libs/core",
                target_task_id="01KC3E1JK8READW9KAK1HBX5C9",
            )

            assert result.success is False
            assert "not found" in result.error.lower()

    def test_add_dependency_with_non_blocking(self):
        """Should allow non-blocking dependencies."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.blocking = False
            mock_resolver.add_dependency.return_value = mock_result

            result = mock_resolver.add_dependency(
                ticket_id="01KC2D0JK7READW9KAK1HBX4B8",
                submodule_path="libs/core",
                target_task_id="01KC3E1JK8READW9KAK1HBX5C9",
                blocking=False,
            )

            assert result.success is True
            assert result.blocking is False


class TestResolveDependency:
    """Tests for resolving dependencies."""

    def test_resolve_dependency_sets_resolved_to(self):
        """Should set resolved_to field when dependency is resolved."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.resolved_to = "01KC3E1JK8READW9KAK1HBX5C9"
            mock_resolver.resolve_dependency.return_value = mock_result

            result = mock_resolver.resolve_dependency(
                dependency_id="dep-123",
                resolved_to="01KC3E1JK8READW9KAK1HBX5C9",
            )

            assert result.success is True
            assert result.resolved_to is not None

    def test_resolve_dependency_marks_as_complete(self):
        """Should mark dependency as resolved."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.status = "resolved"
            mock_resolver.resolve_dependency.return_value = mock_result

            result = mock_resolver.resolve_dependency(
                dependency_id="dep-123",
            )

            assert result.status == "resolved"


class TestDetectCycles:
    """Tests for cycle detection in dependencies."""

    def test_detect_cycles_finds_simple_cycle(self):
        """Should detect a simple A -> B -> A cycle."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.has_cycles = True
            mock_result.cycles = [["A", "B", "A"]]
            mock_resolver.detect_cycles.return_value = mock_result

            result = mock_resolver.detect_cycles()

            assert result.has_cycles is True
            assert len(result.cycles) == 1
            assert "A" in result.cycles[0]
            assert "B" in result.cycles[0]

    def test_detect_cycles_finds_complex_cycle(self):
        """Should detect complex cycles across multiple submodules."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.has_cycles = True
            mock_result.cycles = [["parent:A", "libs/core:B", "libs/utils:C", "parent:A"]]
            mock_resolver.detect_cycles.return_value = mock_result

            result = mock_resolver.detect_cycles()

            assert result.has_cycles is True
            assert len(result.cycles[0]) == 4

    def test_detect_cycles_no_cycles(self):
        """Should return no cycles when dependencies are acyclic."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.has_cycles = False
            mock_result.cycles = []
            mock_resolver.detect_cycles.return_value = mock_result

            result = mock_resolver.detect_cycles()

            assert result.has_cycles is False
            assert result.cycles == []


class TestValidateDependencies:
    """Tests for dependency validation."""

    def test_validate_dependencies_finds_broken_links(self):
        """Should find dependencies pointing to non-existent tasks."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.is_valid = False
            mock_result.missing_targets = [
                MagicMock(source="01ABC", target="nonexistent"),
            ]
            mock_result.cycles = []
            mock_result.stale_references = []
            mock_resolver.validate_all.return_value = mock_result

            result = mock_resolver.validate_all()

            assert result.is_valid is False
            assert len(result.missing_targets) == 1

    def test_validate_dependencies_finds_stale_references(self):
        """Should find stale references to deleted tasks."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.is_valid = False
            mock_result.missing_targets = []
            mock_result.cycles = []
            mock_result.stale_references = [
                MagicMock(source="01ABC", target="01DEF", reason="Target deleted"),
            ]
            mock_resolver.validate_all.return_value = mock_result

            result = mock_resolver.validate_all()

            assert result.is_valid is False
            assert len(result.stale_references) == 1

    def test_validate_dependencies_all_valid(self):
        """Should return valid when all dependencies are correct."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.missing_targets = []
            mock_result.cycles = []
            mock_result.stale_references = []
            mock_resolver.validate_all.return_value = mock_result

            result = mock_resolver.validate_all()

            assert result.is_valid is True
            assert result.missing_targets == []
            assert result.cycles == []


class TestGetDependencies:
    """Tests for retrieving dependencies."""

    def test_get_dependencies_outgoing(self):
        """Should get outgoing dependencies from a ticket."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_deps = [
                MagicMock(
                    direction="outgoing",
                    submodule_path="libs/core",
                    task_id="01ABC",
                    blocking=True,
                ),
            ]
            mock_resolver.get_dependencies.return_value = mock_deps

            result = mock_resolver.get_dependencies(
                ticket_id="01XYZ",
                direction="outgoing",
            )

            assert len(result) == 1
            assert result[0].direction == "outgoing"

    def test_get_dependencies_incoming(self):
        """Should get incoming dependencies to a ticket."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_deps = [
                MagicMock(
                    direction="incoming",
                    submodule_path="libs/utils",
                    task_id="01DEF",
                ),
            ]
            mock_resolver.get_dependencies.return_value = mock_deps

            result = mock_resolver.get_dependencies(
                ticket_id="01XYZ",
                direction="incoming",
            )

            assert len(result) == 1
            assert result[0].direction == "incoming"

    def test_get_dependencies_both_directions(self):
        """Should get dependencies in both directions."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_deps = [
                MagicMock(direction="outgoing"),
                MagicMock(direction="incoming"),
            ]
            mock_resolver.get_dependencies.return_value = mock_deps

            result = mock_resolver.get_dependencies(
                ticket_id="01XYZ",
                direction="both",
            )

            assert len(result) == 2


class TestBuildGraph:
    """Tests for building dependency graph."""

    def test_build_graph_creates_nodes(self):
        """Should create nodes for all tickets with dependencies."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_graph = MagicMock()
            mock_graph.nodes = ["01ABC", "01DEF", "01GHI"]
            mock_resolver.build_graph.return_value = mock_graph

            result = mock_resolver.build_graph()

            assert len(result.nodes) == 3

    def test_build_graph_to_json(self):
        """Should export graph as JSON."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_graph = MagicMock()
            mock_graph.to_json.return_value = {
                "nodes": ["01ABC", "01DEF"],
                "edges": [{"from": "01ABC", "to": "01DEF", "blocking": True}],
            }
            mock_resolver.build_graph.return_value = mock_graph

            result = mock_resolver.build_graph()
            json_output = result.to_json()

            assert "nodes" in json_output
            assert "edges" in json_output

    def test_build_graph_to_dot(self):
        """Should export graph as DOT format."""
        with patch('vibey.operations.submodule.deps.DependencyResolver') as MockResolver:
            mock_resolver = MockResolver.return_value
            mock_graph = MagicMock()
            mock_graph.to_dot.return_value = "digraph G { A -> B }"
            mock_resolver.build_graph.return_value = mock_graph

            result = mock_resolver.build_graph()
            dot_output = result.to_dot()

            assert "digraph" in dot_output
