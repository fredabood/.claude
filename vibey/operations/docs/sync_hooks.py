"""
Automatic Sync Triggers

Hooks into roadmap state change events to automatically trigger documentation
synchronization based on configuration.

Trigger Events:
- Task completion
- Sprint completion
- Track completion
- Context file addition

Configuration (in project.yaml):
documentation:
  sync:
    enabled: true
    auto_sync_on:
      - task_complete
      - sprint_complete
      - track_complete
      - context_add
"""

import sys
from pathlib import Path
from typing import List, Optional

# Add framework to path if needed
framework_root = Path(__file__).parent.parent
if str(framework_root.parent) not in sys.path:
    sys.path.insert(0, str(framework_root.parent))

from vibey.operations.docs.sync_engine import SyncEngine, SyncConfig


class SyncTrigger:
    """
    Automatic synchronization trigger.

    Hooks into roadmap state changes and triggers sync based on configuration.
    """

    def __init__(
        self,
        enabled: bool = True,
        auto_sync_on: Optional[List[str]] = None,
        source_dir: str = ".vibey/roadmap",
        target_dir: str = "docs/roadmap",
        verbose: bool = False
    ):
        """
        Initialize sync trigger.

        Args:
            enabled: Whether automatic sync is enabled
            auto_sync_on: List of events that trigger sync
            source_dir: Source directory for sync
            target_dir: Target directory for sync
            verbose: Print sync results
        """
        self.enabled = enabled
        self.auto_sync_on = auto_sync_on or [
            "task_complete",
            "sprint_complete",
            "track_complete"
        ]
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.verbose = verbose

        # Create sync engine
        self.config = SyncConfig(
            source_dir=source_dir,
            target_dir=target_dir
        )
        self.engine = SyncEngine(self.config)

    def should_trigger(self, event: str) -> bool:
        """
        Check if event should trigger sync.

        Args:
            event: Event name (task_complete, sprint_complete, etc.)

        Returns:
            True if sync should be triggered
        """
        return self.enabled and event in self.auto_sync_on

    def trigger_sync(self, event: str, object_id: Optional[str] = None) -> bool:
        """
        Trigger automatic synchronization.

        Args:
            event: Event that triggered sync
            object_id: ID of object that triggered event (optional)

        Returns:
            True if sync succeeded, False otherwise
        """
        if not self.should_trigger(event):
            return True  # Not an error, just not configured to sync

        try:
            if self.verbose:
                print(f"🔄 Auto-sync triggered by: {event}")
                if object_id:
                    print(f"   Object: {object_id}")

            # Perform sync
            result = self.engine.sync(dry_run=False)

            if self.verbose:
                if result.files_copied:
                    print(f"   ✓ Synced {len(result.files_copied)} file(s)")
                if result.errors:
                    print(f"   ⚠️  {len(result.errors)} error(s)")

            return result.success

        except Exception as e:
            if self.verbose:
                print(f"   ❌ Sync failed: {e}")
            # Don't propagate error - sync failure shouldn't block state changes
            return False

    def on_task_complete(self, task_id: str) -> bool:
        """
        Trigger sync on task completion.

        Args:
            task_id: ID of completed task

        Returns:
            True if sync succeeded
        """
        return self.trigger_sync("task_complete", task_id)

    def on_sprint_complete(self, sprint_id: str) -> bool:
        """
        Trigger sync on sprint completion.

        Args:
            sprint_id: ID of completed sprint

        Returns:
            True if sync succeeded
        """
        return self.trigger_sync("sprint_complete", sprint_id)

    def on_track_complete(self, track_id: str) -> bool:
        """
        Trigger sync on track completion.

        Args:
            track_id: ID of completed track

        Returns:
            True if sync succeeded
        """
        return self.trigger_sync("track_complete", track_id)

    def on_context_add(self, object_id: str, context_file: str) -> bool:
        """
        Trigger sync on context file addition.

        Args:
            object_id: ID of object context was added to
            context_file: Path to context file

        Returns:
            True if sync succeeded
        """
        return self.trigger_sync("context_add", f"{object_id}:{context_file}")


# Global trigger instance (lazy-loaded)
_trigger_instance: Optional[SyncTrigger] = None


def get_sync_trigger(
    enabled: bool = True,
    auto_sync_on: Optional[List[str]] = None,
    verbose: bool = False
) -> SyncTrigger:
    """
    Get global sync trigger instance.

    Args:
        enabled: Whether automatic sync is enabled
        auto_sync_on: List of events that trigger sync
        verbose: Print sync results

    Returns:
        SyncTrigger instance
    """
    global _trigger_instance

    if _trigger_instance is None:
        _trigger_instance = SyncTrigger(
            enabled=enabled,
            auto_sync_on=auto_sync_on,
            verbose=verbose
        )

    return _trigger_instance


# Convenience functions for direct use
def trigger_on_task_complete(task_id: str, enabled: bool = True, verbose: bool = False) -> bool:
    """Trigger sync on task completion."""
    trigger = get_sync_trigger(enabled=enabled, verbose=verbose)
    return trigger.on_task_complete(task_id)


def trigger_on_sprint_complete(sprint_id: str, enabled: bool = True, verbose: bool = False) -> bool:
    """Trigger sync on sprint completion."""
    trigger = get_sync_trigger(enabled=enabled, verbose=verbose)
    return trigger.on_sprint_complete(sprint_id)


def trigger_on_track_complete(track_id: str, enabled: bool = True, verbose: bool = False) -> bool:
    """Trigger sync on track completion."""
    trigger = get_sync_trigger(enabled=enabled, verbose=verbose)
    return trigger.on_track_complete(track_id)


def trigger_on_context_add(object_id: str, context_file: str, enabled: bool = True, verbose: bool = False) -> bool:
    """Trigger sync on context file addition."""
    trigger = get_sync_trigger(enabled=enabled, verbose=verbose)
    return trigger.on_context_add(object_id, context_file)
