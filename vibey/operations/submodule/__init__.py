"""
Submodule operations module.

Provides functionality for detecting, discovering, and managing
git submodules that have vibey roadmaps.
"""

from vibey.operations.submodule.discovery import SubmoduleDiscovery
from vibey.operations.submodule.pull import ProgressAggregator
from vibey.operations.submodule.push import TaskDefinition, TaskPusher

__all__ = ["SubmoduleDiscovery", "TaskPusher", "TaskDefinition", "ProgressAggregator"]
