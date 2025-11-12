"""
Roadmap operations module.

This module provides high-level operations for roadmap initialization, querying,
and updating. These operations are used by the CLI commands and can also be
imported directly for programmatic use.
"""

from .init import init_roadmap
from .query import (
    query_roadmap_summary,
    query_track_details,
    query_sprint_details,
    query_task_details,
    query_blockers,
    query_dependencies,
)
from .update import (
    complete_task,
    start_task,
    assign_task,
    start_sprint,
    complete_sprint,
    refresh_progress,
    recalculate_all,
)
from .context import (
    ContextLoader,
    get_task_context,
)
from .summarize import (
    SummaryGenerator,
    summarize_sprint,
    summarize_task,
    summarize_all_completed,
)
from .add_commit import (
    add_commit_to_task,
    get_commit_info,
    get_current_commit,
)
from .validate import (
    RoadmapValidator,
    validate_roadmap,
)
from .standards_enforcement import (
    EnforcementResult,
    enforce_standards,
    print_enforcement_results,
    get_failure_summary,
)

__all__ = [
    # Initialization
    "init_roadmap",
    # Query operations
    "query_roadmap_summary",
    "query_track_details",
    "query_sprint_details",
    "query_task_details",
    "query_blockers",
    "query_dependencies",
    # Update operations
    "complete_task",
    "start_task",
    "assign_task",
    "start_sprint",
    "complete_sprint",
    "refresh_progress",
    "recalculate_all",
    # Context operations
    "ContextLoader",
    "get_task_context",
    # Summary operations
    "SummaryGenerator",
    "summarize_sprint",
    "summarize_task",
    "summarize_all_completed",
    # Commit operations
    "add_commit_to_task",
    "get_commit_info",
    "get_current_commit",
    # Validation operations
    "RoadmapValidator",
    "validate_roadmap",
    # Standards enforcement
    "EnforcementResult",
    "enforce_standards",
    "print_enforcement_results",
    "get_failure_summary",
]
