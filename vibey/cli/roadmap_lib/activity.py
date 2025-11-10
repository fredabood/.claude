"""
Activity logging utilities for roadmap state.

Handles activity log entries in the roadmap.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

from framework.roadmap.models import Roadmap, ActivityType
from framework.roadmap.serialization import load_roadmap, save_roadmap
from .filesystem import FileSystemManager


class ActivityLogger:
    """Logs activities to roadmap activity log."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize activity logger.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.fs = FileSystemManager(root_dir)

    def log_activity(
        self,
        activity_type: ActivityType,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an activity to the roadmap.

        Args:
            activity_type: Type of activity
            description: Human-readable description
            context: Optional context dictionary

        Returns:
            True if logged successfully, False otherwise
        """
        try:
            # Load roadmap
            roadmap_path = self.fs.get_roadmap_path()
            if not roadmap_path.exists():
                print(f"❌ Roadmap not found at {roadmap_path}")
                return False

            roadmap = load_roadmap(roadmap_path)

            # Add activity
            roadmap.add_activity(activity_type, description, context)

            # Save roadmap
            save_roadmap(roadmap, roadmap_path)

            return True

        except Exception as e:
            print(f"❌ Failed to log activity: {e}")
            return False


def log_activity(
    activity_type: ActivityType,
    description: str,
    context: Optional[Dict[str, Any]] = None,
    root_dir: Optional[Path] = None
) -> bool:
    """
    Log an activity to the roadmap (convenience function).

    Args:
        activity_type: Type of activity
        description: Human-readable description
        context: Optional context dictionary
        root_dir: Root directory (defaults to current working directory)

    Returns:
        True if logged successfully, False otherwise
    """
    logger = ActivityLogger(root_dir)
    return logger.log_activity(activity_type, description, context)
