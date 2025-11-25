"""
Tests for merge ordering module.
"""

import pytest
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path

from vibey.operations.git.merge_ordering import (
    DependencyLevel,
    MergeRecommendation,
    DependencyNode,
    DependencyEdge,
    MergeOrderItem,
    DependencyCheckResult,
    MergeOrderReport,
    MergeOrderAnalyzer,
    get_merge_order,
    check_branch_dependencies,
    format_merge_order_report,
    format_dependency_check_result,
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository with dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create roadmap structure
        roadmap_root = repo / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        # Create track A (no dependencies)
        track_a = roadmap_root / "track-a"
        track_a.mkdir()
        with open(track_a / "track.yaml", 'w') as f:
            yaml.dump({
                'track': {
                    'id': 'track-a',
                    'name': 'Track A',
                    'status': 'completed',
                    'depends_on': [],
                    'blocked_by': []
                }
            }, f)

        # Create track B (depends on track A)
        track_b = roadmap_root / "track-b"
        track_b.mkdir()
        with open(track_b / "track.yaml", 'w') as f:
            yaml.dump({
                'track': {
                    'id': 'track-b',
                    'name': 'Track B',
                    'status': 'in_progress',
                    'depends_on': ['track-a'],
                    'blocked_by': []
                }
            }, f)

        # Create sprint 1 in track B
        sprint_1 = track_b / "track-b-sprint-1"
        sprint_1.mkdir()
        with open(sprint_1 / "sprint.yaml", 'w') as f:
            yaml.dump({
                'sprint': {
                    'id': 'track-b-sprint-1',
                    'name': 'Sprint 1',
                    'status': 'completed',
                    'dependencies': [],
                    'blocked_by': []
                }
            }, f)

        # Create sprint 2 (depends on sprint 1)
        sprint_2 = track_b / "track-b-sprint-2"
        sprint_2.mkdir()
        with open(sprint_2 / "sprint.yaml", 'w') as f:
            yaml.dump({
                'sprint': {
                    'id': 'track-b-sprint-2',
                    'name': 'Sprint 2',
                    'status': 'in_progress',
                    'dependencies': ['track-b-sprint-1'],
                    'blocked_by': []
                }
            }, f)

        # Create task 1 in sprint 2
        task_1 = sprint_2 / "track-b-sprint-2-task-001"
        task_1.mkdir()
        with open(task_1 / "task.yaml", 'w') as f:
            yaml.dump({
                'task': {
                    'id': 'track-b-sprint-2-task-001',
                    'name': 'Task 1',
                    'status': 'completed',
                    'dependencies': [],
                    'blocked_by': []
                }
            }, f)

        # Create task 2 (depends on task 1)
        task_2 = sprint_2 / "track-b-sprint-2-task-002"
        task_2.mkdir()
        with open(task_2 / "task.yaml", 'w') as f:
            yaml.dump({
                'task': {
                    'id': 'track-b-sprint-2-task-002',
                    'name': 'Task 2',
                    'status': 'not_started',
                    'dependencies': ['track-b-sprint-2-task-001'],
                    'blocked_by': []
                }
            }, f)

        # Create task 3 (depends on task 2 - not completed)
        task_3 = sprint_2 / "track-b-sprint-2-task-003"
        task_3.mkdir()
        with open(task_3 / "task.yaml", 'w') as f:
            yaml.dump({
                'task': {
                    'id': 'track-b-sprint-2-task-003',
                    'name': 'Task 3',
                    'status': 'not_started',
                    'dependencies': ['track-b-sprint-2-task-002'],
                    'blocked_by': []
                }
            }, f)

        # Initialize git
        import subprocess
        subprocess.run(['git', 'init'], cwd=repo, capture_output=True)
        subprocess.run(['git', 'add', '.'], cwd=repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Initial'],
            cwd=repo,
            capture_output=True,
            env={'GIT_AUTHOR_NAME': 'Test', 'GIT_AUTHOR_EMAIL': 'test@test.com',
                 'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 'test@test.com'}
        )

        # Create branches for tasks
        subprocess.run(['git', 'branch', 'feature/track-b-sprint-2-task-002'], cwd=repo, capture_output=True)
        subprocess.run(['git', 'branch', 'feature/track-b-sprint-2-task-003'], cwd=repo, capture_output=True)

        yield repo


class TestDependencyLevel:
    """Tests for DependencyLevel enum."""

    def test_level_values(self):
        """Test dependency level values."""
        assert DependencyLevel.TRACK.value == "track"
        assert DependencyLevel.SPRINT.value == "sprint"
        assert DependencyLevel.TASK.value == "task"


class TestMergeRecommendation:
    """Tests for MergeRecommendation enum."""

    def test_recommendation_values(self):
        """Test recommendation values."""
        assert MergeRecommendation.SAFE.value == "safe"
        assert MergeRecommendation.WARNING.value == "warning"
        assert MergeRecommendation.BLOCKED.value == "blocked"
        assert MergeRecommendation.OVERRIDE.value == "override"


class TestDependencyNode:
    """Tests for DependencyNode dataclass."""

    def test_node_creation(self):
        """Test creating a dependency node."""
        node = DependencyNode(
            id='task-001',
            level=DependencyLevel.TASK,
            name='Task 1',
            status='not_started',
            depends_on=['task-000'],
            blocks=['task-002']
        )

        assert node.id == 'task-001'
        assert node.level == DependencyLevel.TASK
        assert len(node.depends_on) == 1


class TestMergeOrderAnalyzer:
    """Tests for MergeOrderAnalyzer class."""

    def test_init(self, temp_repo):
        """Test initialization."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        assert analyzer.repo_path == temp_repo

    def test_build_dependency_graph(self, temp_repo):
        """Test building dependency graph."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        analyzer._build_dependency_graph()

        # Should have tracks, sprints, and tasks
        assert 'track-a' in analyzer._dependency_graph
        assert 'track-b' in analyzer._dependency_graph
        assert 'track-b-sprint-1' in analyzer._dependency_graph
        assert 'track-b-sprint-2-task-001' in analyzer._dependency_graph

    def test_extract_item_id_from_branch(self, temp_repo):
        """Test extracting item ID from branch name."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))

        # Task branch
        result = analyzer._extract_item_id_from_branch('feature/track-b-sprint-2-task-002')
        assert result is not None
        item_id, level = result
        assert item_id == 'track-b-sprint-2-task-002'
        assert level == DependencyLevel.TASK

        # Track branch
        result = analyzer._extract_item_id_from_branch('track/my-track')
        assert result is not None
        item_id, level = result
        assert item_id == 'my-track'
        assert level == DependencyLevel.TRACK

    def test_is_dependency_satisfied(self, temp_repo):
        """Test checking if dependency is satisfied."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        analyzer._build_dependency_graph()

        # track-a is completed
        assert analyzer._is_dependency_satisfied('track-a')

        # task-002 is not completed
        assert not analyzer._is_dependency_satisfied('track-b-sprint-2-task-002')

    def test_topological_sort(self, temp_repo):
        """Test topological sorting."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        analyzer._build_dependency_graph()

        order = analyzer._topological_sort()

        # Dependencies should come before dependents
        # track-a should come before track-b
        if 'track-a' in order and 'track-b' in order:
            assert order.index('track-a') < order.index('track-b')

    def test_get_merge_order(self, temp_repo):
        """Test getting merge order."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        report = analyzer.get_merge_order()

        assert isinstance(report, MergeOrderReport)
        assert report.generated_at is not None

    def test_check_branch_dependencies_satisfied(self, temp_repo):
        """Test checking satisfied dependencies."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))

        # Task 2 depends on task 1 which is completed
        result = analyzer.check_branch_dependencies('feature/track-b-sprint-2-task-002')

        assert result.item_id == 'track-b-sprint-2-task-002'
        assert result.can_merge  # task-001 is completed

    def test_check_branch_dependencies_unsatisfied(self, temp_repo):
        """Test checking unsatisfied dependencies."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))

        # Task 3 depends on task 2 which is NOT completed
        result = analyzer.check_branch_dependencies('feature/track-b-sprint-2-task-003')

        assert result.item_id == 'track-b-sprint-2-task-003'
        assert not result.can_merge
        assert 'track-b-sprint-2-task-002' in result.unsatisfied_dependencies

    def test_check_branch_dependencies_override(self, temp_repo):
        """Test dependency check with override."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))

        result = analyzer.check_branch_dependencies(
            'feature/track-b-sprint-2-task-003',
            allow_override=True
        )

        assert result.can_merge  # Override allows merge
        assert result.recommendation == MergeRecommendation.OVERRIDE

    def test_check_unknown_branch(self, temp_repo):
        """Test checking branch not in roadmap."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))

        result = analyzer.check_branch_dependencies('feature/random-branch')

        assert result.can_merge
        assert result.recommendation == MergeRecommendation.SAFE

    def test_format_merge_order(self, temp_repo):
        """Test formatting merge order report."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        report = analyzer.get_merge_order()

        output = analyzer.format_merge_order(report)

        assert "Recommended Merge Order" in output

    def test_format_dependency_check(self, temp_repo):
        """Test formatting dependency check result."""
        analyzer = MergeOrderAnalyzer(str(temp_repo))
        result = analyzer.check_branch_dependencies('feature/track-b-sprint-2-task-002')

        output = analyzer.format_dependency_check(result)

        assert "Dependency Check:" in output
        assert "track-b-sprint-2-task-002" in output


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_merge_order(self, temp_repo):
        """Test get_merge_order convenience function."""
        report = get_merge_order(str(temp_repo))

        assert isinstance(report, MergeOrderReport)

    def test_check_branch_dependencies(self, temp_repo):
        """Test check_branch_dependencies convenience function."""
        result = check_branch_dependencies(
            'feature/track-b-sprint-2-task-002',
            str(temp_repo)
        )

        assert isinstance(result, DependencyCheckResult)

    def test_format_merge_order_report(self, temp_repo):
        """Test format_merge_order_report convenience function."""
        report = get_merge_order(str(temp_repo))
        output = format_merge_order_report(report)

        assert len(output) > 0

    def test_format_dependency_check_result(self, temp_repo):
        """Test format_dependency_check_result convenience function."""
        result = check_branch_dependencies(
            'feature/track-b-sprint-2-task-002',
            str(temp_repo)
        )
        output = format_dependency_check_result(result)

        assert len(output) > 0


class TestMergeOrderItem:
    """Tests for MergeOrderItem dataclass."""

    def test_item_creation(self):
        """Test creating a merge order item."""
        item = MergeOrderItem(
            item_id='task-001',
            level=DependencyLevel.TASK,
            name='Test Task',
            order=1,
            branch_name='feature/task-001',
            dependencies_satisfied=True
        )

        assert item.item_id == 'task-001'
        assert item.order == 1
        assert item.dependencies_satisfied


class TestDependencyCheckResult:
    """Tests for DependencyCheckResult dataclass."""

    def test_result_creation(self):
        """Test creating a dependency check result."""
        result = DependencyCheckResult(
            branch_name='feature/task-001',
            item_id='task-001',
            level=DependencyLevel.TASK,
            recommendation=MergeRecommendation.SAFE,
            satisfied_dependencies=['task-000'],
            unsatisfied_dependencies=[],
            message='All good',
            can_merge=True
        )

        assert result.branch_name == 'feature/task-001'
        assert result.can_merge
        assert len(result.satisfied_dependencies) == 1
