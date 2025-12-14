"""
Tests for vibey.cli.roadmap_lib.dependencies module.

Tests dependency resolution and circular dependency detection.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from vibey.cli.roadmap_lib.dependencies import (
    DependencyNode,
    DependencyResolver,
    resolve_dependencies,
    detect_circular_dependencies,
)


class TestDependencyNode:
    """Test DependencyNode dataclass."""

    def test_create_node(self):
        """Test creating a dependency node."""
        node = DependencyNode(
            id="task-001",
            type="task",
            depends_on=["task-000"]
        )
        assert node.id == "task-001"
        assert node.type == "task"
        assert node.depends_on == ["task-000"]

    def test_node_empty_dependencies(self):
        """Test node with no dependencies."""
        node = DependencyNode(
            id="track-1",
            type="track",
            depends_on=[]
        )
        assert len(node.depends_on) == 0

    def test_node_multiple_dependencies(self):
        """Test node with multiple dependencies."""
        node = DependencyNode(
            id="sprint-1",
            type="sprint",
            depends_on=["dep-1", "dep-2", "dep-3"]
        )
        assert len(node.depends_on) == 3


class TestDependencyResolverBasics:
    """Test DependencyResolver basic operations."""

    def test_init_creates_empty_graph(self):
        """Test initialization creates empty dependency graph."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()
            assert resolver.dependency_graph == {}

    def test_get_dependencies_nonexistent(self):
        """Test getting dependencies for nonexistent node."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()
            result = resolver.get_dependencies("nonexistent")
            assert result == []

    def test_get_dependents_empty_graph(self):
        """Test getting dependents from empty graph."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()
            result = resolver.get_dependents("any-id")
            assert result == []

    def test_get_transitive_dependencies_nonexistent(self):
        """Test transitive dependencies for nonexistent node."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()
            result = resolver.get_transitive_dependencies("nonexistent")
            assert result == set()


class TestDependencyResolverWithGraph:
    """Test DependencyResolver with pre-built graph."""

    @pytest.fixture
    def resolver_with_graph(self):
        """Create resolver with test dependency graph."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()

            # Build test graph:
            # A -> B -> C
            # D -> B
            resolver.dependency_graph = {
                "A": DependencyNode(id="A", type="task", depends_on=["B"]),
                "B": DependencyNode(id="B", type="task", depends_on=["C"]),
                "C": DependencyNode(id="C", type="task", depends_on=[]),
                "D": DependencyNode(id="D", type="task", depends_on=["B"]),
            }
            return resolver

    def test_get_dependencies(self, resolver_with_graph):
        """Test getting direct dependencies."""
        deps = resolver_with_graph.get_dependencies("A")
        assert deps == ["B"]

    def test_get_dependencies_multiple(self, resolver_with_graph):
        """Test node with no dependencies."""
        deps = resolver_with_graph.get_dependencies("C")
        assert deps == []

    def test_get_dependents(self, resolver_with_graph):
        """Test getting dependents."""
        dependents = resolver_with_graph.get_dependents("B")
        assert set(dependents) == {"A", "D"}

    def test_get_dependents_leaf_node(self, resolver_with_graph):
        """Test getting dependents of leaf node."""
        dependents = resolver_with_graph.get_dependents("C")
        assert dependents == ["B"]

    def test_get_dependents_root_node(self, resolver_with_graph):
        """Test getting dependents of root node (no dependents)."""
        dependents = resolver_with_graph.get_dependents("A")
        assert dependents == []

    def test_get_transitive_dependencies(self, resolver_with_graph):
        """Test getting transitive dependencies."""
        trans_deps = resolver_with_graph.get_transitive_dependencies("A")
        assert trans_deps == {"B", "C"}

    def test_get_transitive_dependencies_direct_only(self, resolver_with_graph):
        """Test transitive dependencies with only direct deps."""
        trans_deps = resolver_with_graph.get_transitive_dependencies("B")
        assert trans_deps == {"C"}

    def test_get_transitive_dependencies_none(self, resolver_with_graph):
        """Test transitive dependencies for leaf node."""
        trans_deps = resolver_with_graph.get_transitive_dependencies("C")
        assert trans_deps == set()


class TestCircularDependencyDetection:
    """Test circular dependency detection."""

    def test_no_circular_dependencies(self):
        """Test detection with no circular dependencies."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()

            # Linear chain: A -> B -> C
            resolver.dependency_graph = {
                "A": DependencyNode(id="A", type="task", depends_on=["B"]),
                "B": DependencyNode(id="B", type="task", depends_on=["C"]),
                "C": DependencyNode(id="C", type="task", depends_on=[]),
            }

            cycles = resolver.detect_circular_dependencies()
            assert cycles == []

    def test_simple_circular_dependency(self):
        """Test detection of simple circular dependency."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()

            # Cycle: A -> B -> A
            resolver.dependency_graph = {
                "A": DependencyNode(id="A", type="task", depends_on=["B"]),
                "B": DependencyNode(id="B", type="task", depends_on=["A"]),
            }

            cycles = resolver.detect_circular_dependencies()
            assert len(cycles) >= 1
            # At least one cycle should contain A and B
            found_cycle = False
            for cycle in cycles:
                if "A" in cycle and "B" in cycle:
                    found_cycle = True
                    break
            assert found_cycle

    def test_self_referential_dependency(self):
        """Test detection of self-referential dependency."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()

            # Self-reference: A -> A
            resolver.dependency_graph = {
                "A": DependencyNode(id="A", type="task", depends_on=["A"]),
            }

            cycles = resolver.detect_circular_dependencies()
            assert len(cycles) >= 1

    def test_longer_cycle(self):
        """Test detection of longer circular dependency."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()

            # Cycle: A -> B -> C -> A
            resolver.dependency_graph = {
                "A": DependencyNode(id="A", type="task", depends_on=["B"]),
                "B": DependencyNode(id="B", type="task", depends_on=["C"]),
                "C": DependencyNode(id="C", type="task", depends_on=["A"]),
            }

            cycles = resolver.detect_circular_dependencies()
            assert len(cycles) >= 1

    def test_multiple_independent_components(self):
        """Test graph with multiple independent components."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()

            # Two independent chains, no cycles
            resolver.dependency_graph = {
                "A": DependencyNode(id="A", type="task", depends_on=["B"]),
                "B": DependencyNode(id="B", type="task", depends_on=[]),
                "C": DependencyNode(id="C", type="task", depends_on=["D"]),
                "D": DependencyNode(id="D", type="task", depends_on=[]),
            }

            cycles = resolver.detect_circular_dependencies()
            assert cycles == []

    def test_empty_graph_no_cycles(self):
        """Test empty graph has no cycles."""
        with patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager'):
            resolver = DependencyResolver()
            resolver.dependency_graph = {}

            cycles = resolver.detect_circular_dependencies()
            assert cycles == []


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager')
    def test_resolve_dependencies_returns_resolver(self, mock_fs):
        """Test resolve_dependencies returns DependencyResolver."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        # Mock the path to not exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        resolver = resolve_dependencies()

        assert isinstance(resolver, DependencyResolver)

    @patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager')
    def test_detect_circular_dependencies_returns_list(self, mock_fs):
        """Test detect_circular_dependencies returns list."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        # Mock the path to not exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        cycles = detect_circular_dependencies()

        assert isinstance(cycles, list)


class TestBuildDependencyGraph:
    """Test building dependency graph from roadmap."""

    @patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager')
    def test_build_graph_no_roadmap(self, mock_fs):
        """Test building graph when roadmap doesn't exist."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        # Roadmap path doesn't exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        resolver = DependencyResolver()
        graph = resolver.build_dependency_graph()

        assert graph == {}

    @patch('vibey.cli.roadmap_lib.dependencies.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.dependencies.load_roadmap')
    def test_build_graph_with_roadmap(self, mock_load_roadmap, mock_fs):
        """Test building graph with roadmap."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        # Roadmap path exists
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        # Mock roadmap with no tracks
        mock_roadmap = MagicMock()
        mock_roadmap.id = "test-roadmap"
        mock_roadmap.tracks = []
        mock_load_roadmap.return_value = mock_roadmap

        resolver = DependencyResolver()
        graph = resolver.build_dependency_graph()

        assert "test-roadmap" in graph
        assert graph["test-roadmap"].type == "roadmap"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
