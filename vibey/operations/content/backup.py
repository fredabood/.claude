"""
Content Backup System.

Handles creating backups before modifications and restoring from backups.
Backups are stored in .vibey/backups/ with timestamps.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ContentBackup:
    """
    Manage content backups.

    Creates timestamped backups in .vibey/backups/ before
    any modification, and supports restoring from backups.
    """

    BACKUP_DIR_NAME = ".vibey/backups/content"
    TRASH_DIR_NAME = ".vibey/trash"

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize backup manager.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.backup_dir = self.project_root / self.BACKUP_DIR_NAME
        self.trash_dir = self.project_root / self.TRASH_DIR_NAME

    def create_backup(self, filepath: Path, operation: str = "modify") -> Optional[Path]:
        """
        Create a backup of a file before modification.

        Args:
            filepath: Path to file to backup
            operation: Type of operation (modify, delete, etc.)

        Returns:
            Path to backup file, or None if backup failed
        """
        if not filepath.exists():
            logger.debug(f"No backup needed - file doesn't exist: {filepath}")
            return None

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = filepath.relative_to(filepath.parent.parent.parent) if len(filepath.parts) > 3 else filepath.name
        safe_name = str(relative_path).replace("/", "_").replace("\\", "_")
        backup_name = f"{timestamp}_{operation}_{safe_name}"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(filepath, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def move_to_trash(self, filepath: Path) -> Optional[Path]:
        """
        Move a file to trash instead of deleting.

        Args:
            filepath: Path to file to trash

        Returns:
            Path in trash, or None if move failed
        """
        if not filepath.exists():
            logger.warning(f"Cannot trash - file doesn't exist: {filepath}")
            return None

        # Ensure trash directory exists
        self.trash_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped trash filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trash_name = f"{timestamp}_{filepath.name}"
        trash_path = self.trash_dir / trash_name

        try:
            shutil.move(str(filepath), str(trash_path))
            logger.info(f"Moved to trash: {trash_path}")
            return trash_path
        except Exception as e:
            logger.error(f"Failed to move to trash: {e}")
            return None

    def list_backups(self, filename_pattern: Optional[str] = None) -> List[Path]:
        """
        List available backups.

        Args:
            filename_pattern: Optional pattern to filter backups

        Returns:
            List of backup file paths, sorted by date (newest first)
        """
        if not self.backup_dir.exists():
            return []

        backups = list(self.backup_dir.glob("*"))

        if filename_pattern:
            backups = [b for b in backups if filename_pattern in b.name]

        # Sort by modification time, newest first
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        return backups

    def list_trash(self) -> List[Path]:
        """
        List files in trash.

        Returns:
            List of trashed file paths, sorted by date (newest first)
        """
        if not self.trash_dir.exists():
            return []

        trashed = list(self.trash_dir.glob("*"))
        trashed.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        return trashed

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a file from backup.

        Args:
            backup_path: Path to backup file
            target_path: Path to restore to

        Returns:
            True if restore succeeded
        """
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False

        try:
            # Backup current file if it exists
            if target_path.exists():
                self.create_backup(target_path, operation="pre-restore")

            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Restore
            shutil.copy2(backup_path, target_path)
            logger.info(f"Restored {backup_path} to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def restore_from_trash(self, trash_path: Path, target_path: Path) -> bool:
        """
        Restore a file from trash.

        Args:
            trash_path: Path to trashed file
            target_path: Path to restore to

        Returns:
            True if restore succeeded
        """
        if not trash_path.exists():
            logger.error(f"Trashed file not found: {trash_path}")
            return False

        try:
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Move back from trash
            shutil.move(str(trash_path), str(target_path))
            logger.info(f"Restored {trash_path} to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore from trash: {e}")
            return False

    def cleanup_old_backups(self, keep_count: int = 50) -> int:
        """
        Clean up old backups, keeping the most recent ones.

        Args:
            keep_count: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        to_delete = backups[keep_count:]

        deleted = 0
        for backup in to_delete:
            try:
                backup.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete old backup {backup}: {e}")

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old backups")

        return deleted

    def cleanup_old_trash(self, keep_count: int = 20) -> int:
        """
        Clean up old trash, keeping the most recent ones.

        Args:
            keep_count: Number of trashed files to keep

        Returns:
            Number of files permanently deleted
        """
        trashed = self.list_trash()
        to_delete = trashed[keep_count:]

        deleted = 0
        for path in to_delete:
            try:
                path.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete from trash {path}: {e}")

        if deleted > 0:
            logger.info(f"Permanently deleted {deleted} items from trash")

        return deleted


# Module-level convenience instance
_default_backup: Optional[ContentBackup] = None


def get_backup_manager(project_root: Optional[Path] = None) -> ContentBackup:
    """Get a backup manager instance."""
    global _default_backup
    if _default_backup is None or project_root is not None:
        _default_backup = ContentBackup(project_root)
    return _default_backup
