"""
Tests for vibey.cli.roadmap_lib.agents module.

Tests agent routing and recommendation utilities for roadmap.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from collections import defaultdict

from vibey.roadmap.models import TaskStatus
from vibey.cli.roadmap_lib.agents import (
    AGENT_CAPABILITIES,
    AgentRouter,
    recommend_agent,
    get_workload,
    recommend_tasks,
    enhance_sprint_with_agent_recommendations,
    plan_sprint_agents,
    detect_parallel_tasks,
    get_task_execution_order,
)


class TestAgentCapabilities:
    """Test agent capabilities definition."""

    def test_web_developer_capabilities(self):
        """Test web developer agent capabilities."""
        caps = AGENT_CAPABILITIES["web-developer"]
        assert "api" in caps["keywords"]
        assert "development" in caps["task_types"]
        assert "web development" in caps["specialties"]

    def test_security_auditor_capabilities(self):
        """Test security auditor agent capabilities."""
        caps = AGENT_CAPABILITIES["security-auditor"]
        assert "security" in caps["keywords"]
        assert "completion_gate" in caps["task_types"]

    def test_all_agents_have_required_keys(self):
        """Test all agents have required keys."""
        for agent_name, caps in AGENT_CAPABILITIES.items():
            assert "keywords" in caps, f"{agent_name} missing keywords"
            assert "task_types" in caps, f"{agent_name} missing task_types"
            assert "specialties" in caps, f"{agent_name} missing specialties"


class TestAgentRouterInit:
    """Test AgentRouter initialization."""

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_init_default_root(self, mock_fs):
        """Test initialization with default root."""
        router = AgentRouter()
        mock_fs.assert_called_once_with(None)

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_init_custom_root(self, mock_fs):
        """Test initialization with custom root."""
        custom_path = Path("/custom/path")
        router = AgentRouter(root_dir=custom_path)
        mock_fs.assert_called_once_with(custom_path)

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_init_sets_capabilities(self, mock_fs):
        """Test initialization sets agent capabilities."""
        router = AgentRouter()
        assert router.agent_capabilities == AGENT_CAPABILITIES


class TestRecommendAgentForTask:
    """Test agent recommendation for tasks."""

    @pytest.fixture
    def router(self):
        """Create AgentRouter instance."""
        with patch('vibey.cli.roadmap_lib.agents.FileSystemManager'):
            return AgentRouter()

    def test_recommend_web_development_task(self, router):
        """Test recommendation for web development task."""
        task = MagicMock()
        task.title = "Build REST API endpoint"
        task.description = "Create API endpoint for user authentication"
        task.task_type = "development"

        recommendations = router.recommend_agent_for_task(task)

        # Should recommend web-developer
        agent_names = [r[0] for r in recommendations]
        assert "web-developer" in agent_names

    def test_recommend_security_task(self, router):
        """Test recommendation for security task."""
        task = MagicMock()
        task.title = "Security audit"
        task.description = "Check for SQL injection vulnerabilities"
        task.task_type = "completion_gate"

        recommendations = router.recommend_agent_for_task(task)

        agent_names = [r[0] for r in recommendations]
        assert "security-auditor" in agent_names

    def test_recommend_ml_task(self, router):
        """Test recommendation for ML task."""
        task = MagicMock()
        task.title = "Train model"
        task.description = "Train neural network for image classification"
        task.task_type = "development"

        recommendations = router.recommend_agent_for_task(task)

        agent_names = [r[0] for r in recommendations]
        assert "ml-engineer" in agent_names

    def test_recommendations_sorted_by_confidence(self, router):
        """Test recommendations are sorted by confidence."""
        task = MagicMock()
        task.title = "API security test"
        task.description = "Test API endpoints for security vulnerabilities"
        task.task_type = "completion_gate"

        recommendations = router.recommend_agent_for_task(task)

        # Should be sorted descending
        scores = [r[1] for r in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_no_recommendations_for_unrelated_task(self, router):
        """Test no recommendations for unrelated task."""
        task = MagicMock()
        task.title = "Random task"
        task.description = "Something unrelated"
        task.task_type = "unknown_type"

        recommendations = router.recommend_agent_for_task(task)

        # May return empty or low confidence results
        assert isinstance(recommendations, list)


class TestAutoAssignTask:
    """Test automatic task assignment."""

    @pytest.fixture
    def router(self):
        """Create AgentRouter instance."""
        with patch('vibey.cli.roadmap_lib.agents.FileSystemManager'):
            return AgentRouter()

    def test_auto_assign_high_confidence(self, router):
        """Test auto-assignment with high confidence."""
        task = MagicMock()
        task.title = "Create API endpoint"
        task.description = "Build REST API with authentication"
        task.task_type = "development"

        result = router.auto_assign_task(task, min_confidence=0.3)

        # Should return an agent
        assert result is not None

    def test_auto_assign_low_confidence(self, router):
        """Test no auto-assignment with low confidence."""
        task = MagicMock()
        task.title = "Generic task"
        task.description = "Something generic"
        task.task_type = "unknown"

        result = router.auto_assign_task(task, min_confidence=0.9)

        # Should return None (confidence too low)
        assert result is None


class TestGetAgentWorkload:
    """Test agent workload calculation."""

    @pytest.fixture
    def router(self):
        """Create AgentRouter with mocked filesystem."""
        with patch('vibey.cli.roadmap_lib.agents.FileSystemManager') as mock_fs:
            mock_fs_instance = MagicMock()
            mock_fs.return_value = mock_fs_instance
            r = AgentRouter()
            r.fs = mock_fs_instance
            return r

    def test_workload_roadmap_not_found(self, router):
        """Test workload when roadmap doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        router.fs.get_roadmap_path.return_value = mock_path

        workload = router.get_agent_workload()

        assert workload == {}

    @patch('vibey.cli.roadmap_lib.agents.load_roadmap')
    def test_workload_empty_roadmap(self, mock_load, router):
        """Test workload with empty roadmap."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        router.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.tracks = []
        mock_load.return_value = mock_roadmap

        workload = router.get_agent_workload()

        assert workload == {}


class TestRecommendNextTask:
    """Test next task recommendation."""

    @pytest.fixture
    def router(self):
        """Create AgentRouter with mocked filesystem."""
        with patch('vibey.cli.roadmap_lib.agents.FileSystemManager') as mock_fs:
            mock_fs_instance = MagicMock()
            mock_fs.return_value = mock_fs_instance
            r = AgentRouter()
            r.fs = mock_fs_instance
            return r

    def test_recommend_roadmap_not_found(self, router):
        """Test recommendations when roadmap doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        router.fs.get_roadmap_path.return_value = mock_path

        recommendations = router.recommend_next_task()

        assert recommendations == []

    @patch('vibey.cli.roadmap_lib.agents.load_roadmap')
    def test_recommend_empty_roadmap(self, mock_load, router):
        """Test recommendations with empty roadmap."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        router.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_roadmap.tracks = []
        mock_load.return_value = mock_roadmap

        recommendations = router.recommend_next_task()

        assert recommendations == []


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_recommend_agent_function(self, mock_fs):
        """Test recommend_agent convenience function."""
        task = MagicMock()
        task.title = "API development"
        task.description = "Build REST endpoint"
        task.task_type = "development"

        recommendations = recommend_agent(task)

        assert isinstance(recommendations, list)

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_get_workload_function(self, mock_fs):
        """Test get_workload convenience function."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        workload = get_workload()

        assert isinstance(workload, dict)

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_recommend_tasks_function(self, mock_fs):
        """Test recommend_tasks convenience function."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        tasks = recommend_tasks()

        assert isinstance(tasks, list)


class TestEnhanceSprintWithAgentRecommendations:
    """Test sprint enhancement with agent recommendations."""

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_enhance_sprint_not_found(self, mock_fs):
        """Test enhancement when sprint not found."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_tasks_path.return_value = mock_path

        result = enhance_sprint_with_agent_recommendations("sprint-001")

        assert result["sprint_id"] == "sprint-001"
        assert result["total_tasks"] == 0
        assert result["recommendations"] == []

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.agents.load_tasks')
    def test_enhance_sprint_with_tasks(self, mock_load_tasks, mock_fs):
        """Test enhancement with tasks."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_tasks_path.return_value = mock_path

        # Create mock tasks
        task1 = MagicMock()
        task1.id = "task-001"
        task1.title = "Build API"
        task1.description = "Create REST endpoint"
        task1.task_type = "development"
        task1.assigned_agent = None

        mock_load_tasks.return_value = [task1]

        result = enhance_sprint_with_agent_recommendations("sprint-001")

        assert result["sprint_id"] == "sprint-001"
        assert result["total_tasks"] == 1
        assert len(result["recommendations"]) == 1


class TestPlanSprintAgents:
    """Test sprint agent planning."""

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.agents.load_tasks')
    @patch('vibey.cli.roadmap_lib.agents.load_roadmap')
    def test_plan_sprint_no_tasks(self, mock_load_roadmap, mock_load_tasks, mock_fs):
        """Test planning when no tasks exist."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_tasks_path = MagicMock()
        mock_tasks_path.exists.return_value = False
        mock_fs_instance.get_tasks_path.return_value = mock_tasks_path

        # Mock roadmap path for workload check
        mock_roadmap_path = MagicMock()
        mock_roadmap_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_roadmap_path

        result = plan_sprint_agents("sprint-001")

        assert result["sprint_id"] == "sprint-001"
        assert result["assignments"] == {}


class TestDetectParallelTasks:
    """Test parallel task detection."""

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_detect_parallel_no_tasks(self, mock_fs):
        """Test detection when no tasks exist."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_tasks_path.return_value = mock_path

        result = detect_parallel_tasks("sprint-001")

        assert result["sprint_id"] == "sprint-001"
        assert result["total_tasks"] == 0
        assert result["parallel_groups"] == []
        assert result["sequential_chains"] == []
        assert result["independent_tasks"] == []
        assert result["blocking_tasks"] == []

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.agents.load_tasks')
    def test_detect_parallel_independent_tasks(self, mock_load_tasks, mock_fs):
        """Test detection with independent tasks."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_tasks_path.return_value = mock_path

        # Create mock independent tasks
        task1 = MagicMock()
        task1.id = "task-001"
        task1.title = "Task 1"
        task1.status = TaskStatus.NOT_STARTED
        task1.blocked_by = []
        task1.blocks = []

        task2 = MagicMock()
        task2.id = "task-002"
        task2.title = "Task 2"
        task2.status = TaskStatus.NOT_STARTED
        task2.blocked_by = []
        task2.blocks = []

        mock_load_tasks.return_value = [task1, task2]

        result = detect_parallel_tasks("sprint-001")

        assert result["total_tasks"] == 2
        assert len(result["independent_tasks"]) == 2


class TestGetTaskExecutionOrder:
    """Test task execution order calculation."""

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    def test_execution_order_no_tasks(self, mock_fs):
        """Test execution order when no tasks exist."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_tasks_path.return_value = mock_path

        phases = get_task_execution_order("sprint-001")

        assert phases == []

    @patch('vibey.cli.roadmap_lib.agents.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.agents.load_tasks')
    def test_execution_order_independent_tasks(self, mock_load_tasks, mock_fs):
        """Test execution order with independent tasks."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_tasks_path.return_value = mock_path

        # Create mock independent tasks
        task1 = MagicMock()
        task1.id = "task-001"
        task1.title = "Task 1"
        task1.status = TaskStatus.NOT_STARTED
        task1.blocked_by = []
        task1.blocks = []

        task2 = MagicMock()
        task2.id = "task-002"
        task2.title = "Task 2"
        task2.status = TaskStatus.NOT_STARTED
        task2.blocked_by = []
        task2.blocks = []

        mock_load_tasks.return_value = [task1, task2]

        phases = get_task_execution_order("sprint-001")

        # All independent tasks should be in phase 1
        assert len(phases) >= 1
        assert "task-001" in phases[0]
        assert "task-002" in phases[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
