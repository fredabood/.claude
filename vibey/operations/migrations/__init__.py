"""
Migration operations for Vibey roadmap system.

This module provides migration functions for different data structure transitions:
- Legacy sprint state to roadmap system
- Flat structure to hierarchical structure
- Embedded tasks to separate task files
"""

from .to_roadmap import migrate_to_roadmap
from .to_hierarchical import migrate_to_hierarchical
from .embedded_tasks import migrate_embedded_tasks

__all__ = [
    'migrate_to_roadmap',
    'migrate_to_hierarchical',
    'migrate_embedded_tasks',
]
