"""
Migration operations for Vibey roadmap system.

Note: Legacy migration functions (migrate_to_roadmap, migrate_to_hierarchical) have been
removed as we now use the flat ULID-based structure per ADR-0002. The roadmap system
has been fully migrated to use:
- .vibey/roadmap/tracks/{ulid}.yaml
- .vibey/roadmap/sprints/{ulid}.yaml
- .vibey/roadmap/tasks/{ulid}.yaml

The embedded_tasks migration is also deprecated as all tasks are now standalone files.
"""

from .embedded_tasks import migrate_embedded_tasks

__all__ = [
    "migrate_embedded_tasks",
]
