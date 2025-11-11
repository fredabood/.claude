"""
Agent routing and recommendation utilities for roadmap.

Handles intelligent agent assignment based on task characteristics.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import sys

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

from vibey.roadmap.models import Task, TaskStatus
from vibey.roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from .filesystem import FileSystemManager


# Agent capabilities mapping
AGENT_CAPABILITIES = {
    "web-developer": {
        "keywords": ["api", "endpoint", "route", "controller", "middleware", "auth", "backend", "frontend", "react", "vue", "angular"],
        "task_types": ["development"],
        "specialties": ["web development", "API design", "full-stack"],
    },
    "ml-engineer": {
        "keywords": ["model", "training", "dataset", "inference", "ml", "ai", "neural", "pytorch", "tensorflow"],
        "task_types": ["development"],
        "specialties": ["machine learning", "data science", "model training"],
    },
    "security-auditor": {
        "keywords": ["security", "vulnerability", "auth", "encryption", "xss", "sql injection", "csrf"],
        "task_types": ["completion_gate", "production_gate"],
        "specialties": ["security auditing", "penetration testing"],
    },
    "test-engineer": {
        "keywords": ["test", "unit test", "integration test", "e2e", "coverage", "qa"],
        "task_types": ["completion_gate", "production_gate"],
        "specialties": ["testing", "quality assurance"],
    },
    "docs-writer": {
        "keywords": ["documentation", "docs", "readme", "guide", "tutorial", "api docs"],
        "task_types": ["completion_gate"],
        "specialties": ["technical writing", "documentation"],
    },
    "performance-optimizer": {
        "keywords": ["performance", "optimization", "latency", "throughput", "caching", "profiling"],
        "task_types": ["production_gate"],
        "specialties": ["performance optimization", "profiling"],
    },
    "devops-engineer": {
        "keywords": ["deployment", "ci/cd", "docker", "kubernetes", "infrastructure", "pipeline"],
        "task_types": ["production_gate"],
        "specialties": ["DevOps", "infrastructure", "deployment"],
    },
    "observability-engineer": {
        "keywords": ["logging", "monitoring", "metrics", "tracing", "observability", "alerting"],
        "task_types": ["production_gate"],
        "specialties": ["observability", "monitoring", "logging"],
    },
}


class AgentRouter:
    """Routes tasks to appropriate agents."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize agent router.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.fs = FileSystemManager(root_dir)
        self.agent_capabilities = AGENT_CAPABILITIES

    def recommend_agent_for_task(self, task: Task) -> List[Tuple[str, float]]:
        """
        Recommend agents for a task with confidence scores.

        Args:
            task: Task object

        Returns:
            List of (agent_name, confidence_score) tuples, sorted by confidence
        """
        scores = {}

        task_text = (task.name + " " + task.description).lower()
        task_type = task.task_type

        for agent_name, capabilities in self.agent_capabilities.items():
            score = 0.0

            # Check task type match
            if task_type in capabilities["task_types"]:
                score += 0.5

            # Check keyword matches
            keyword_matches = sum(
                1 for keyword in capabilities["keywords"]
                if keyword in task_text
            )
            if keyword_matches > 0:
                # Scale keyword score (max 0.5)
                score += min(0.5, keyword_matches * 0.1)

            scores[agent_name] = score

        # Sort by score (descending)
        recommendations = sorted(
            [(agent, score) for agent, score in scores.items() if score > 0],
            key=lambda x: x[1],
            reverse=True
        )

        return recommendations

    def auto_assign_task(self, task: Task, min_confidence: float = 0.3) -> Optional[str]:
        """
        Automatically assign a task to an agent if confidence is high enough.

        Args:
            task: Task object
            min_confidence: Minimum confidence score required for auto-assignment

        Returns:
            Agent name if assigned, None otherwise
        """
        recommendations = self.recommend_agent_for_task(task)

        if recommendations and recommendations[0][1] >= min_confidence:
            return recommendations[0][0]

        return None

    def get_agent_workload(self) -> Dict[str, Dict[str, Any]]:
        """
        Get workload for each agent.

        Returns:
            Dictionary mapping agent name to workload statistics
        """
        workload = defaultdict(lambda: {
            "total_tasks": 0,
            "in_progress": 0,
            "not_started": 0,
            "completed": 0,
            "tasks": [],
        })

        roadmap_path = self.fs.get_roadmap_path()
        if not roadmap_path.exists():
            return dict(workload)

        roadmap = load_roadmap(roadmap_path)

        # Iterate through all tasks
        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if not track_path.exists():
                continue

            track = load_track(track_path)

            for sprint_summary in track.sprints:
                tasks_path = self.fs.get_tasks_path(sprint_summary.id)
                if not tasks_path.exists():
                    continue

                tasks = load_tasks(tasks_path)

                for task in tasks:
                    if task.assigned_agent:
                        agent = task.assigned_agent
                        workload[agent]["total_tasks"] += 1
                        workload[agent]["tasks"].append({
                            "id": task.id,
                            "name": task.name,
                            "status": task.status.value,
                            "sprint_id": sprint_summary.id,
                            "track_id": track.id,
                        })

                        # Update status counts
                        if task.status == TaskStatus.IN_PROGRESS:
                            workload[agent]["in_progress"] += 1
                        elif task.status == TaskStatus.NOT_STARTED:
                            workload[agent]["not_started"] += 1
                        elif task.status == TaskStatus.COMPLETED:
                            workload[agent]["completed"] += 1

        return dict(workload)

    def recommend_next_task(
        self,
        agent: Optional[str] = None,
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend next tasks to work on.

        Args:
            agent: Optional agent name to get recommendations for
            max_recommendations: Maximum number of recommendations

        Returns:
            List of task recommendations with metadata
        """
        recommendations = []
        roadmap_path = self.fs.get_roadmap_path()

        if not roadmap_path.exists():
            return recommendations

        roadmap = load_roadmap(roadmap_path)

        # Iterate through all tasks
        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if not track_path.exists():
                continue

            track = load_track(track_path)

            for sprint_summary in track.sprints:
                # Skip if sprint not started
                sprint_path = self.fs.get_sprint_path(sprint_summary.id)
                if not sprint_path.exists():
                    continue

                sprint = load_sprint(sprint_path)
                if sprint.status not in [TaskStatus.IN_PROGRESS, "in_progress"]:
                    continue

                tasks_path = self.fs.get_tasks_path(sprint_summary.id)
                if not tasks_path.exists():
                    continue

                tasks = load_tasks(tasks_path)

                for task in tasks:
                    # Skip if not available
                    if task.status != TaskStatus.NOT_STARTED:
                        continue

                    # Skip quality gates (require dev tasks first)
                    if task.is_quality_gate():
                        continue

                    # Check if task is blocked
                    if task.blocked:
                        continue

                    # Get agent recommendations
                    agent_recommendations = self.recommend_agent_for_task(task)

                    # Filter by agent if specified
                    if agent:
                        agent_match = next(
                            (a for a, s in agent_recommendations if a == agent),
                            None
                        )
                        if not agent_match:
                            continue

                    # Calculate priority score
                    priority_score = 0.0

                    # Higher priority for tasks in active sprints
                    if sprint.status == "in_progress":
                        priority_score += 1.0

                    # Higher priority if agent is already assigned
                    if task.assigned_agent == agent:
                        priority_score += 2.0

                    # Add agent confidence if available
                    if agent_recommendations:
                        priority_score += agent_recommendations[0][1]

                    recommendations.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "sprint_id": sprint_summary.id,
                        "sprint_name": sprint.name,
                        "track_id": track.id,
                        "track_name": track.name,
                        "priority_score": priority_score,
                        "recommended_agents": agent_recommendations[:3],
                        "assigned_agent": task.assigned_agent,
                    })

        # Sort by priority score
        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)

        return recommendations[:max_recommendations]


def recommend_agent(task: Task, root_dir: Optional[Path] = None) -> List[Tuple[str, float]]:
    """
    Recommend agents for a task (convenience function).

    Args:
        task: Task object
        root_dir: Root directory

    Returns:
        List of (agent_name, confidence_score) tuples
    """
    router = AgentRouter(root_dir)
    return router.recommend_agent_for_task(task)


def get_workload(root_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get agent workload (convenience function).

    Args:
        root_dir: Root directory

    Returns:
        Dictionary of agent workloads
    """
    router = AgentRouter(root_dir)
    return router.get_agent_workload()


def recommend_tasks(
    agent: Optional[str] = None,
    max_recommendations: int = 5,
    root_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Recommend next tasks (convenience function).

    Args:
        agent: Optional agent name
        max_recommendations: Maximum number of recommendations
        root_dir: Root directory

    Returns:
        List of task recommendations
    """
    router = AgentRouter(root_dir)
    return router.recommend_next_task(agent, max_recommendations)
