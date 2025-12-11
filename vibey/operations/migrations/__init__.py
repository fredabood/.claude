"""
Migration operations for Vibey roadmap system.

This module provides migration functions for different data structure transitions:
- Legacy sprint state to roadmap system
- Embedded tasks to separate task files

Note: migrate_to_hierarchical was removed as we now use flat ULID-based structure.
"""

from .to_roadmap import migrate_to_roadmap
from .embedded_tasks import migrate_embedded_tasks

__all__ = [
    'migrate_to_roadmap',
    'migrate_embedded_tasks',
]
