"""
Test helpers for roadmap CLI tests.

Provides utilities to create hierarchical roadmap structures for testing.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


class HierarchicalRoadmapBuilder:
    """Builds hierarchical roadmap structures for testing."""

    def __init__(self, root_dir: Path):
        """
        Initialize builder with root directory.

        Args:
            root_dir: Root directory for the test roadmap
        """
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.roadmap_root = self.vibey_dir / "roadmap"

    def create_structure(self):
        """Create basic directory structure."""
        self.vibey_dir.mkdir(parents=True, exist_ok=True)
        self.roadmap_root.mkdir(parents=True, exist_ok=True)

    def create_roadmap_file(
        self,
        roadmap_id: str = "test-roadmap",
        name: str = "Test Roadmap",
        version: str = "1.0.0",
        tracks: Optional[List[Dict[str, Any]]] = None,
    ) -> Path:
        """
        Create main roadmap.yaml file with all required fields for model loading.

        Args:
            roadmap_id: Roadmap ID
            name: Roadmap name
            version: Version string
            tracks: List of track dicts (with id, name keys)

        Returns:
            Path to roadmap.yaml
        """
        from datetime import datetime, timezone

        tracks_list = tracks or []

        roadmap_data = {
            "roadmap": {
                # Required fields
                "id": roadmap_id,
                "name": name,
                "version": version,
                "status": "not_started",
                "blocked": False,
                "created": datetime.now(timezone.utc).isoformat(),

                # Version strategy (optional with defaults)
                "version_strategy": {
                    "major_on": "roadmap_milestone",
                    "minor_on": "track_completion",
                    "patch_on": "sprint_production_ready"
                },

                # Progress (required)
                "progress": {
                    "tracks_total": len(tracks_list),
                    "tracks_completed": 0,
                    "sprints_total": 0,
                    "sprints_completed": 0,
                    "tasks_total": 0,
                    "tasks_completed": 0,
                    "completion_percent": 0,
                },

                # Tracks (TrackSummary format)
                "tracks": [
                    {
                        "id": t["id"],
                        "name": t.get("name", t["id"]),
                        "status": t.get("status", "not_started"),
                        "priority": t.get("priority", "medium"),
                    }
                    for t in tracks_list
                ],

                # Activity log (required, can be empty)
                "activity_log": [],

                # Metadata (optional with defaults)
                "metadata": {
                    "created_by": "test",
                    "framework_version": "2.5.0",
                    "schema_version": "2.1",
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },

                # Optional fields
                "dependencies": [],
                "blocked_by": [],
                "version_history": [],
                "deployed_platforms": [],
            }
        }

        roadmap_file = self.vibey_dir / "roadmap.yaml"
        with open(roadmap_file, 'w') as f:
            yaml.dump(roadmap_data, f, default_flow_style=False, sort_keys=False)

        return roadmap_file

    def create_track(
        self,
        track_slug: str,
        track_id: str,
        name: str,
        status: str = "not_started",
        priority: str = "medium",
        dependencies: Optional[List[str]] = None,
        sprints: Optional[List[str]] = None,
    ) -> Path:
        """
        Create track in hierarchical structure.

        Args:
            track_slug: Track directory slug (e.g., "user-management")
            track_id: Track ID (e.g., "user-management")
            name: Track name
            status: Track status
            priority: Priority level
            dependencies: List of track IDs this depends on
            sprints: List of sprint IDs

        Returns:
            Path to track directory
        """
        from datetime import datetime, timezone

        track_dir = self.roadmap_root / track_slug
        track_dir.mkdir(parents=True, exist_ok=True)

        # Create context directory
        (track_dir / "context").mkdir(exist_ok=True)

        # Create track.yaml with all required fields
        track_data = {
            "track": {
                # Identity
                "id": track_id,
                "name": name,
                "roadmap_id": "test-roadmap",

                # Status
                "status": status,
                "blocked": False,
                "priority": priority,

                # Timing
                "created": datetime.now(timezone.utc).isoformat(),

                # Progress (with completion_percent)
                "progress": {
                    "sprints_total": len(sprints) if sprints else 0,
                    "sprints_completed": 0,
                    "tasks_total": 0,
                    "tasks_completed": 0,
                    "completion_percent": 0,
                },

                # Sprints (empty list - will be populated by create_sprint)
                "sprints": [],

                # Dependencies
                "dependencies": dependencies or [],
                "blocks": [],
                "blocked_by": [],

                # NEW: Cached dependency tracking
                "depends_on": [],
                "depended_on_by": [],

                # Quality gates
                "quality_gates": [],

                # Assigned agents
                "assigned_agents": [],

                # Metadata
                "metadata": {
                    "created_by": "test",
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },

                # Optional fields with defaults
                "deliverables": [],
                "strategic_value": [],
                "commits": [],
            }
        }

        track_file = track_dir / "track.yaml"
        with open(track_file, 'w') as f:
            yaml.dump(track_data, f, default_flow_style=False, sort_keys=False)

        # Create .id file
        id_file = track_dir / ".id"
        with open(id_file, 'w') as f:
            f.write(track_id)

        return track_dir

    def create_sprint(
        self,
        track_slug: str,
        sprint_slug: str,
        sprint_id: str,
        name: str,
        track_id: str,
        status: str = "not_started",
        tasks: Optional[List[str]] = None,
        quality_gates: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Create sprint in hierarchical structure.

        Args:
            track_slug: Parent track slug
            sprint_slug: Sprint directory slug
            sprint_id: Sprint ID
            name: Sprint name
            track_id: Parent track ID
            status: Sprint status
            tasks: List of task IDs
            quality_gates: Quality gate configuration

        Returns:
            Path to sprint directory
        """
        from datetime import datetime, timezone

        sprint_dir = self.roadmap_root / track_slug / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Create context directory
        (sprint_dir / "context").mkdir(exist_ok=True)

        # Create sprint.yaml with all required fields
        sprint_data = {
            "sprint": {
                # Identity
                "id": sprint_id,
                "name": name,
                "track_id": track_id,
                "roadmap_id": "test-roadmap",

                # Status
                "status": status,
                "blocked": False,

                # Timing
                "created": datetime.now(timezone.utc).isoformat(),

                # Progress (SprintProgress requires all task type breakdowns)
                "progress": {
                    "development_tasks_total": len(tasks) if tasks else 0,
                    "development_tasks_completed": 0,
                    "completion_gate_tasks_total": 0,
                    "completion_gate_tasks_completed": 0,
                    "production_gate_tasks_total": 0,
                    "production_gate_tasks_completed": 0,
                    "tasks_total": len(tasks) if tasks else 0,
                    "tasks_completed": 0,
                    "completion_percent": 0,
                },

                # Tasks (empty list - will be populated by create_task)
                "tasks": [],

                # Dependencies
                "development_gates": [],
                "blocks": [],
                "blocked_by": [],

                # NEW: Cached dependency tracking
                "depends_on": [],
                "depended_on_by": [],

                # Metadata
                "metadata": {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },

                # Optional fields with defaults
                "deliverables": [],
                "commits": [],
            }
        }

        sprint_file = sprint_dir / "sprint.yaml"
        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False)

        # Create .id file
        id_file = sprint_dir / ".id"
        with open(id_file, 'w') as f:
            f.write(sprint_id)

        return sprint_dir

    def create_task(
        self,
        track_slug: str,
        sprint_slug: str,
        task_slug: str,
        task_id: str,
        name: str,
        sprint_id: str,
        status: str = "not_started",
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        files_to_modify: Optional[List[str]] = None,
        quality_requirements: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Path:
        """
        Create task in hierarchical structure.

        Args:
            track_slug: Parent track slug
            sprint_slug: Parent sprint slug
            task_slug: Task directory slug
            task_id: Task ID
            name: Task name
            sprint_id: Parent sprint ID
            status: Task status
            description: Task description
            assigned_to: Assigned developer
            files_to_modify: List of files to modify
            dependencies: List of task IDs this depends on

        Returns:
            Path to task directory
        """
        from datetime import datetime, timezone

        task_dir = self.roadmap_root / track_slug / sprint_slug / task_slug
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create context directory
        (task_dir / "context").mkdir(exist_ok=True)

        # Extract track_id from sprint_id (format: track-sprint)
        track_id = sprint_id.rsplit('-', 1)[0] if '-' in sprint_id else "unknown-track"

        # Create task.yaml with all required fields
        task_data = {
            "task": {
                # Identity
                "id": task_id,
                "sprint_id": sprint_id,
                "track_id": track_id,
                "roadmap_id": "test-roadmap",

                # Task Type (default to development)
                "task_type": "development",

                # Description
                "title": name,
                "description": description or "",

                # Status
                "status": status,
                "blocked": False,

                # Timing
                "created": datetime.now(timezone.utc).isoformat(),

                # Assignment
                "assigned_agent": assigned_to or "test-agent",
                "priority": "medium",

                # Complexity & Size
                "estimated_tokens": 5000,
                "complexity": "medium",

                # Dependencies and blockers
                "dependencies": dependencies or [],
                "blocks": [],
                "blocked_by": [],

                # NEW: Cached dependency tracking
                "depends_on": [],
                "depended_on_by": [],

                # Metadata
                "metadata": {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },

                # Optional fields with defaults
                "deliverables": [],
                "commits": [],
                "files_to_modify": files_to_modify or [],
                "quality_requirements": quality_requirements or [],
            }
        }

        task_file = task_dir / "task.yaml"
        with open(task_file, 'w') as f:
            yaml.dump(task_data, f, default_flow_style=False, sort_keys=False)

        # Create .id file
        id_file = task_dir / ".id"
        with open(id_file, 'w') as f:
            f.write(task_id)

        return task_dir

    def add_sprint_to_track(self, track_slug: str, sprint_id: str, sprint_name: str, sprint_status: str = "not_started") -> None:
        """Add a sprint summary to track's sprints array."""
        from datetime import datetime, timezone

        track_file = self.roadmap_root / track_slug / "track.yaml"
        with open(track_file, 'r') as f:
            data = yaml.safe_load(f)

        # Add sprint summary
        sprint_summary = {
            "id": sprint_id,
            "name": sprint_name,
            "status": sprint_status,
        }
        data['track']['sprints'].append(sprint_summary)
        data['track']['progress']['sprints_total'] = len(data['track']['sprints'])

        with open(track_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def add_task_to_sprint(self, track_slug: str, sprint_slug: str, task_id: str, task_title: str, task_status: str = "not_started") -> None:
        """Add a task summary to sprint's tasks array."""
        from datetime import datetime, timezone

        sprint_file = self.roadmap_root / track_slug / sprint_slug / "sprint.yaml"
        with open(sprint_file, 'r') as f:
            data = yaml.safe_load(f)

        # Add task summary
        task_summary = {
            "id": task_id,
            "title": task_title,
            "status": task_status,
            "task_type": "development",
        }
        data['sprint']['tasks'].append(task_summary)

        # Update progress counts
        data['sprint']['progress']['development_tasks_total'] = len([t for t in data['sprint']['tasks'] if t['task_type'] == 'development'])
        data['sprint']['progress']['tasks_total'] = len(data['sprint']['tasks'])

        with open(sprint_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def create_sample_roadmap(root_dir: Path) -> Path:
    """
    Create a complete sample roadmap for testing.

    Creates a realistic roadmap structure with:
    - 3 tracks
    - 5 sprints
    - Multiple tasks per sprint
    - Dependencies between tracks

    Args:
        root_dir: Root directory for the test roadmap

    Returns:
        Path to the root directory
    """
    builder = HierarchicalRoadmapBuilder(root_dir)
    builder.create_structure()

    # Create main roadmap file
    builder.create_roadmap_file(
        roadmap_id="test-roadmap",
        name="Test Project Roadmap",
        version="1.0.0",
        tracks=[
            {"id": "user-management", "slug": "user-management"},
            {"id": "payment-integration", "slug": "payment-integration"},
            {"id": "performance", "slug": "performance"},
        ]
    )

    # Track 1: User Management
    builder.create_track(
        track_slug="user-management",
        track_id="user-management",
        name="User Management System",
        status="not_started",
        priority="high",
    )

    # Sprint 1-1: Authentication (ID must start with track ID)
    builder.create_sprint(
        track_slug="user-management",
        sprint_slug="user-management-1-auth",
        sprint_id="user-management-1-auth",
        name="Authentication",
        track_id="user-management",
        status="not_started",
    )
    builder.add_sprint_to_track("user-management", "user-management-1-auth", "Authentication")

    # Tasks for Sprint 1-1 (IDs must start with sprint ID)
    builder.create_task(
        track_slug="user-management",
        sprint_slug="user-management-1-auth",
        task_slug="user-management-1-auth-task-001",
        task_id="user-management-1-auth-task-001",
        name="User registration API",
        sprint_id="user-management-1-auth",
        description="Build REST API endpoint for user registration",
        files_to_modify=["src/api/auth.py", "tests/test_auth.py"],
        quality_requirements=["Unit tests with >80% coverage", "Input validation", "Security audit"]
    )
    builder.add_task_to_sprint("user-management", "user-management-1-auth", "user-management-1-auth-task-001", "User registration API")

    builder.create_task(
        track_slug="user-management",
        sprint_slug="user-management-1-auth",
        task_slug="user-management-1-auth-task-002",
        task_id="user-management-1-auth-task-002",
        name="Login endpoint",
        sprint_id="user-management-1-auth",
        description="Implement login with JWT tokens"
    )
    builder.add_task_to_sprint("user-management", "user-management-1-auth", "user-management-1-auth-task-002", "Login endpoint")

    builder.create_task(
        track_slug="user-management",
        sprint_slug="user-management-1-auth",
        task_slug="user-management-1-auth-task-003",
        task_id="user-management-1-auth-task-003",
        name="Password reset flow",
        sprint_id="user-management-1-auth"
    )
    builder.add_task_to_sprint("user-management", "user-management-1-auth", "user-management-1-auth-task-003", "Password reset flow")

    builder.create_task(
        track_slug="user-management",
        sprint_slug="user-management-1-auth",
        task_slug="user-management-1-auth-task-004",
        task_id="user-management-1-auth-task-004",
        name="Email verification",
        sprint_id="user-management-1-auth"
    )
    builder.add_task_to_sprint("user-management", "user-management-1-auth", "user-management-1-auth-task-004", "Email verification")

    # Sprint 1-2: User Profiles
    builder.create_sprint(
        track_slug="user-management",
        sprint_slug="user-management-2-profiles",
        sprint_id="user-management-2-profiles",
        name="User Profiles",
        track_id="user-management",
        status="not_started",
    )
    builder.add_sprint_to_track("user-management", "user-management-2-profiles", "User Profiles")

    # Track 2: Payment Integration
    builder.create_track(
        track_slug="payment-integration",
        track_id="payment-integration",
        name="Payment Integration",
        status="not_started",
        priority="high",
        dependencies=["user-management"],
    )

    builder.create_sprint(
        track_slug="payment-integration",
        sprint_slug="payment-integration-1-setup",
        sprint_id="payment-integration-1-setup",
        name="Payment Setup",
        track_id="payment-integration",
        status="not_started",
    )
    builder.add_sprint_to_track("payment-integration", "payment-integration-1-setup", "Payment Setup")

    # Track 3: Performance
    builder.create_track(
        track_slug="performance",
        track_id="performance",
        name="Performance Optimization",
        status="not_started",
        priority="medium",
    )

    builder.create_sprint(
        track_slug="performance",
        sprint_slug="performance-1-frontend",
        sprint_id="performance-1-frontend",
        name="Frontend Optimization",
        track_id="performance",
        status="not_started",
    )
    builder.add_sprint_to_track("performance", "performance-1-frontend", "Frontend Optimization")

    builder.create_sprint(
        track_slug="performance",
        sprint_slug="performance-2-backend",
        sprint_id="performance-2-backend",
        name="Backend Optimization",
        track_id="performance",
        status="not_started",
    )
    builder.add_sprint_to_track("performance", "performance-2-backend", "Backend Optimization")

    return root_dir
