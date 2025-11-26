"""
CRUD operations for roadmap entities.

This subpackage provides create, read, update, delete operations
for all roadmap entities:

- roadmap: Roadmap operations
- track: Track operations
- sprint: Sprint operations
- task: Task operations
- relationships: Blocking, dependency, junction table, and quality gate operations
"""

from .roadmap import (
    create_roadmap,
    get_roadmap,
    update_roadmap,
    delete_roadmap,
    list_roadmaps,
    roadmap_exists,
    count_roadmaps,
)

from .track import (
    create_track,
    get_track,
    update_track,
    delete_track,
    list_tracks_by_roadmap,
    track_exists,
    count_tracks,
)

from .sprint import (
    create_sprint,
    get_sprint,
    update_sprint,
    delete_sprint,
    list_sprints_by_track,
    list_sprints_by_roadmap,
    sprint_exists,
    count_sprints,
)

from .task import (
    create_task,
    get_task,
    update_task,
    delete_task,
    list_tasks_by_sprint,
    list_tasks_by_track,
    list_tasks_by_roadmap,
    task_exists,
    count_tasks,
    get_blocked_tasks,
)

from .relationships import (
    # Blocking relationships
    add_blocker,
    remove_blocker,
    get_blockers,
    get_blocked_by,
    is_blocked,
    # Soft dependencies
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    # Deliverables junction
    create_deliverable,
    link_deliverable,
    unlink_deliverable,
    get_deliverables,
    # Commits junction
    create_commit,
    get_commit_by_hash,
    link_commit,
    unlink_commit,
    get_commits,
    # Quality gates
    add_quality_gate,
    update_quality_gate,
    remove_quality_gate,
    list_quality_gates,
    get_blocking_gates,
    # Dependency chain queries
    get_dependency_chain,
    get_blocking_chain,
    detect_circular_dependencies,
    detect_circular_blockers,
)

__all__ = [
    # Roadmap
    "create_roadmap",
    "get_roadmap",
    "update_roadmap",
    "delete_roadmap",
    "list_roadmaps",
    "roadmap_exists",
    "count_roadmaps",
    # Track
    "create_track",
    "get_track",
    "update_track",
    "delete_track",
    "list_tracks_by_roadmap",
    "track_exists",
    "count_tracks",
    # Sprint
    "create_sprint",
    "get_sprint",
    "update_sprint",
    "delete_sprint",
    "list_sprints_by_track",
    "list_sprints_by_roadmap",
    "sprint_exists",
    "count_sprints",
    # Task
    "create_task",
    "get_task",
    "update_task",
    "delete_task",
    "list_tasks_by_sprint",
    "list_tasks_by_track",
    "list_tasks_by_roadmap",
    "task_exists",
    "count_tasks",
    "get_blocked_tasks",
    # Blocking relationships
    "add_blocker",
    "remove_blocker",
    "get_blockers",
    "get_blocked_by",
    "is_blocked",
    # Soft dependencies
    "add_dependency",
    "remove_dependency",
    "get_dependencies",
    "get_dependents",
    # Deliverables junction
    "create_deliverable",
    "link_deliverable",
    "unlink_deliverable",
    "get_deliverables",
    # Commits junction
    "create_commit",
    "get_commit_by_hash",
    "link_commit",
    "unlink_commit",
    "get_commits",
    # Quality gates
    "add_quality_gate",
    "update_quality_gate",
    "remove_quality_gate",
    "list_quality_gates",
    "get_blocking_gates",
    # Dependency chain queries
    "get_dependency_chain",
    "get_blocking_chain",
    "detect_circular_dependencies",
    "detect_circular_blockers",
]
