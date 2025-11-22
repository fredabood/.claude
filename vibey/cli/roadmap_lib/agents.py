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

        task_text = (task.title + " " + task.description).lower()
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
                            "name": task.title,
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
                        "task_name": task.title,
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


# ============================================================================
# Sprint Planning Integration (Task 004)
# ============================================================================

def enhance_sprint_with_agent_recommendations(
    sprint_id: str,
    auto_assign: bool = False,
    min_confidence: float = 0.5,
    root_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Enhance a sprint's tasks with agent recommendations.

    Integrates with sprint planning workflow by analyzing all tasks in a sprint
    and providing agent recommendations for each.

    Args:
        sprint_id: Sprint ID to enhance
        auto_assign: If True, auto-assign agents when confidence >= min_confidence
        min_confidence: Minimum confidence for auto-assignment
        root_dir: Root directory

    Returns:
        Dictionary with:
        - sprint_id: Sprint ID
        - total_tasks: Number of tasks analyzed
        - recommendations: List of task recommendations
        - auto_assigned: Number of tasks auto-assigned (if auto_assign=True)
        - unassigned: Number of tasks without confident recommendations
    """
    router = AgentRouter(root_dir)
    fs = router.fs

    result = {
        "sprint_id": sprint_id,
        "total_tasks": 0,
        "recommendations": [],
        "auto_assigned": 0,
        "unassigned": 0,
    }

    # Load sprint tasks
    tasks_path = fs.get_tasks_path(sprint_id)
    if not tasks_path.exists():
        return result

    tasks = load_tasks(tasks_path)
    result["total_tasks"] = len(tasks)

    for task in tasks:
        recommendations = router.recommend_agent_for_task(task)

        task_rec = {
            "task_id": task.id,
            "task_title": task.title,
            "current_agent": task.assigned_agent,
            "recommendations": recommendations[:3],  # Top 3
            "auto_assigned_to": None,
        }

        if recommendations:
            best_agent, confidence = recommendations[0]

            if auto_assign and confidence >= min_confidence and not task.assigned_agent:
                task_rec["auto_assigned_to"] = best_agent
                result["auto_assigned"] += 1
        else:
            result["unassigned"] += 1

        result["recommendations"].append(task_rec)

    return result


def plan_sprint_agents(
    sprint_id: str,
    balance_workload: bool = True,
    root_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Plan agent assignments for a sprint considering workload balance.

    Used during sprint planning to distribute work across agents.

    Args:
        sprint_id: Sprint ID
        balance_workload: If True, consider current agent workloads
        root_dir: Root directory

    Returns:
        Dictionary with planned assignments and workload distribution
    """
    router = AgentRouter(root_dir)

    # Get current workloads if balancing
    workloads = router.get_agent_workload() if balance_workload else {}

    # Enhance sprint with recommendations
    recommendations = enhance_sprint_with_agent_recommendations(
        sprint_id,
        auto_assign=False,
        root_dir=root_dir
    )

    # Plan assignments considering workload
    assignments = {}
    planned_additions = defaultdict(int)

    for task_rec in recommendations["recommendations"]:
        task_id = task_rec["task_id"]
        recs = task_rec["recommendations"]

        if not recs:
            assignments[task_id] = {"agent": None, "reason": "No suitable agent found"}
            continue

        if balance_workload:
            # Score agents considering current workload
            best_agent = None
            best_score = -1

            for agent, confidence in recs:
                current_load = workloads.get(agent, {}).get("in_progress", 0)
                planned_load = planned_additions[agent]
                total_load = current_load + planned_load

                # Adjusted score: confidence minus load penalty
                adjusted_score = confidence - (total_load * 0.1)

                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_agent = agent

            if best_agent:
                assignments[task_id] = {
                    "agent": best_agent,
                    "confidence": next(c for a, c in recs if a == best_agent),
                    "reason": "Best fit considering workload balance"
                }
                planned_additions[best_agent] += 1
        else:
            # Just use the best recommendation
            best_agent, confidence = recs[0]
            assignments[task_id] = {
                "agent": best_agent,
                "confidence": confidence,
                "reason": "Highest confidence match"
            }

    return {
        "sprint_id": sprint_id,
        "assignments": assignments,
        "workload_distribution": dict(planned_additions),
        "total_planned": len([a for a in assignments.values() if a.get("agent")]),
    }


# ============================================================================
# Parallel Task Detection (Task 007)
# ============================================================================

def detect_parallel_tasks(
    sprint_id: str,
    root_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Detect tasks that can be executed in parallel.

    Analyzes task dependencies within a sprint to identify independent tasks
    that can be worked on simultaneously.

    Args:
        sprint_id: Sprint ID to analyze
        root_dir: Root directory

    Returns:
        Dictionary with:
        - sprint_id: Sprint ID
        - parallel_groups: List of task groups that can run in parallel
        - sequential_chains: List of task chains that must run sequentially
        - independent_tasks: Tasks with no dependencies
        - blocking_tasks: Tasks that block other tasks
    """
    fs = FileSystemManager(root_dir)
    tasks_path = fs.get_tasks_path(sprint_id)

    result = {
        "sprint_id": sprint_id,
        "parallel_groups": [],
        "sequential_chains": [],
        "independent_tasks": [],
        "blocking_tasks": [],
        "total_tasks": 0,
    }

    if not tasks_path.exists():
        return result

    tasks = load_tasks(tasks_path)
    result["total_tasks"] = len(tasks)

    # Build dependency graph
    task_map = {task.id: task for task in tasks}
    blocks = defaultdict(set)  # task_id -> set of tasks it blocks
    blocked_by = defaultdict(set)  # task_id -> set of tasks blocking it

    for task in tasks:
        # Check blocked_by relationships
        if hasattr(task, 'blocked_by') and task.blocked_by:
            for blocker_id in task.blocked_by:
                if blocker_id in task_map:
                    blocked_by[task.id].add(blocker_id)
                    blocks[blocker_id].add(task.id)

        # Check blocks relationships
        if hasattr(task, 'blocks') and task.blocks:
            for blocked_id in task.blocks:
                if blocked_id in task_map:
                    blocks[task.id].add(blocked_id)
                    blocked_by[blocked_id].add(task.id)

    # Identify independent tasks (no blockers, not blocking anyone)
    for task in tasks:
        if task.id not in blocks and task.id not in blocked_by:
            result["independent_tasks"].append({
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            })

    # Identify blocking tasks
    for task_id, blocked_tasks in blocks.items():
        if blocked_tasks:
            task = task_map[task_id]
            result["blocking_tasks"].append({
                "task_id": task_id,
                "title": task.title,
                "blocks": list(blocked_tasks),
                "blocks_count": len(blocked_tasks),
            })

    # Build parallel groups (tasks that can run together)
    # Tasks are parallel if they don't depend on each other
    remaining_tasks = set(task.id for task in tasks)
    visited = set()

    # First, handle sequential chains
    def build_chain(start_id: str, chain: List[str]) -> List[str]:
        """Build a sequential chain starting from a task."""
        chain.append(start_id)
        for blocked_id in blocks.get(start_id, []):
            if blocked_id not in visited:
                visited.add(blocked_id)
                build_chain(blocked_id, chain)
        return chain

    # Find chain starters (tasks that are blocked but block others)
    chain_starters = [
        tid for tid in remaining_tasks
        if tid in blocks and tid not in blocked_by
    ]

    for starter in chain_starters:
        if starter not in visited:
            visited.add(starter)
            chain = build_chain(starter, [])
            if len(chain) > 1:
                result["sequential_chains"].append({
                    "chain": chain,
                    "length": len(chain),
                    "tasks": [
                        {"task_id": tid, "title": task_map[tid].title}
                        for tid in chain
                    ]
                })

    # Remaining tasks without dependencies form parallel groups
    parallel_candidates = [
        tid for tid in remaining_tasks
        if tid not in visited and tid not in blocked_by
    ]

    if parallel_candidates:
        result["parallel_groups"].append({
            "group_id": "parallel-1",
            "tasks": [
                {"task_id": tid, "title": task_map[tid].title}
                for tid in parallel_candidates
            ],
            "count": len(parallel_candidates),
        })

    return result


def get_task_execution_order(
    sprint_id: str,
    root_dir: Optional[Path] = None
) -> List[List[str]]:
    """
    Get optimal task execution order for a sprint.

    Returns tasks grouped by execution phase - tasks in the same phase
    can be executed in parallel.

    Args:
        sprint_id: Sprint ID
        root_dir: Root directory

    Returns:
        List of phases, each phase is a list of task IDs that can run in parallel
    """
    parallel_info = detect_parallel_tasks(sprint_id, root_dir)

    phases = []

    # Phase 1: Independent tasks and chain starters
    phase1 = [t["task_id"] for t in parallel_info["independent_tasks"]]
    for chain in parallel_info["sequential_chains"]:
        if chain["chain"]:
            phase1.append(chain["chain"][0])

    if phase1:
        phases.append(phase1)

    # Subsequent phases from sequential chains
    max_chain_length = max(
        (len(chain["chain"]) for chain in parallel_info["sequential_chains"]),
        default=0
    )

    for i in range(1, max_chain_length):
        phase = []
        for chain in parallel_info["sequential_chains"]:
            if i < len(chain["chain"]):
                phase.append(chain["chain"][i])
        if phase:
            phases.append(phase)

    return phases
