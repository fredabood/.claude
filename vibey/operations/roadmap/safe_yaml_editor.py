"""
Safe YAML Editor Module

Provides safe YAML editing with automatic validation, backups, and rollback
to prevent data corruption during bulk status corrections.

Author: Vibey Framework
Created: 2025-11-21
Sprint: roadmap-integrity-fixes-1
Task: roadmap-integrity-fixes-1-task-003
"""

import hashlib
import json
import re
import shutil
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Add an error message."""
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


@dataclass
class EditResult:
    """Result of an edit operation."""
    success: bool
    file_path: str
    backup_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    changes_made: Dict[str, Any] = field(default_factory=dict)
    checksum_before: Optional[str] = None
    checksum_after: Optional[str] = None


@dataclass
class BulkEditResult:
    """Result of a bulk edit operation."""
    success: bool
    files_changed: int = 0
    files_failed: int = 0
    total_files: int = 0
    results: List[EditResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    checkpoint_path: Optional[str] = None


@dataclass
class ChangeLogEntry:
    """Entry in the change log."""
    timestamp: str
    file: str
    operation: str
    field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    success: bool = True
    validation_passed: bool = True
    error: Optional[str] = None


# ============================================================================
# Safe YAML Editor Class
# ============================================================================

class SafeYAMLEditor:
    """
    Safe YAML editing with automatic validation and backups.

    Features:
    - Automatic backups before edits
    - Schema and business logic validation
    - Transaction semantics for bulk edits (all-or-nothing)
    - Dry-run mode
    - Change logging
    - Automatic rollback on failures
    """

    def __init__(
        self,
        auto_backup: bool = True,
        validate: bool = True,
        backup_dir: Optional[Path] = None,
        max_backups: int = 50
    ):
        """
        Initialize safe YAML editor.

        Args:
            auto_backup: Create backups before edits
            validate: Validate YAML before and after edits
            backup_dir: Directory for backups (default: .vibey/safe-edit-backups)
            max_backups: Maximum number of backups to keep
        """
        self.auto_backup = auto_backup
        self.validate = validate
        self.max_backups = max_backups
        self.changes_log: List[ChangeLogEntry] = []

        # Set backup directory
        if backup_dir:
            self.backup_dir = backup_dir
        else:
            self.backup_dir = Path.cwd() / ".vibey" / "safe-edit-backups"

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # Single File Operations
    # ========================================================================

    def edit_file(
        self,
        file_path: Union[str, Path],
        modifications: Dict[str, Any],
        dry_run: bool = False
    ) -> EditResult:
        """
        Safely edit a single YAML file with validation.

        Args:
            file_path: Path to YAML file
            modifications: Dictionary of field paths to new values
                          e.g., {"status": "completed", "task.priority": "high"}
            dry_run: If True, validate but don't actually modify

        Returns:
            EditResult with success status and details
        """
        file_path = Path(file_path)
        result = EditResult(success=False, file_path=str(file_path))

        # Check file exists
        if not file_path.exists():
            result.errors.append(f"File not found: {file_path}")
            return result

        try:
            # Calculate checksum before
            result.checksum_before = self._calculate_checksum(file_path)

            # Create backup
            if self.auto_backup and not dry_run:
                backup_path = self._create_backup(file_path, modifications)
                result.backup_path = str(backup_path)

            # Load YAML
            with open(file_path) as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            # Validate current structure
            if self.validate:
                validation = self._validate_yaml_structure(data, file_path)
                if not validation.valid:
                    result.errors.extend(validation.errors)
                    result.errors.append("Pre-edit validation failed")
                    return result
                result.warnings.extend(validation.warnings)

            # Apply modifications
            original_data = data.copy() if isinstance(data, dict) else data
            for field_path, new_value in modifications.items():
                old_value = self._apply_modification(data, field_path, new_value)
                result.changes_made[field_path] = {
                    "old": old_value,
                    "new": new_value
                }

            # Validate modified structure
            if self.validate:
                validation = self._validate_yaml_structure(data, file_path)
                if not validation.valid:
                    result.errors.extend(validation.errors)
                    result.errors.append("Post-edit validation failed")
                    return result
                result.warnings.extend(validation.warnings)

            # Write to file (if not dry-run)
            if not dry_run:
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

                # Calculate checksum after
                result.checksum_after = self._calculate_checksum(file_path)

                # Log change
                self._log_change(
                    file_path=file_path,
                    operation="edit_file",
                    modifications=modifications,
                    success=True
                )

            result.success = True
            return result

        except yaml.YAMLError as e:
            result.errors.append(f"YAML parse error: {e}")
            self._log_change(
                file_path=file_path,
                operation="edit_file",
                modifications=modifications,
                success=False,
                error=str(e)
            )
            return result
        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            self._log_change(
                file_path=file_path,
                operation="edit_file",
                modifications=modifications,
                success=False,
                error=str(e)
            )
            return result

    def bulk_edit(
        self,
        file_pattern: str,
        modifications: Dict[str, Any],
        dry_run: bool = False,
        root_dir: Optional[Path] = None
    ) -> BulkEditResult:
        """
        Safely edit multiple YAML files with transaction semantics.

        If any file fails validation or edit, ALL changes are rolled back.

        Args:
            file_pattern: Glob pattern for files (e.g., ".vibey/roadmap/*/task.yaml")
            modifications: Dictionary of field paths to new values
            dry_run: If True, validate but don't actually modify
            root_dir: Root directory for glob (default: current directory)

        Returns:
            BulkEditResult with transaction status
        """
        if root_dir is None:
            root_dir = Path.cwd()

        result = BulkEditResult(success=False)

        # Find all matching files
        matching_files = list(root_dir.glob(file_pattern))
        result.total_files = len(matching_files)

        if result.total_files == 0:
            result.errors.append(f"No files match pattern: {file_pattern}")
            return result

        # Create checkpoint backup (for rollback)
        checkpoint_path = None
        if not dry_run:
            checkpoint_path = self._create_checkpoint(matching_files, root_dir=root_dir)
            result.checkpoint_path = str(checkpoint_path)

        # Edit each file
        all_succeeded = True
        for file_path in matching_files:
            edit_result = self.edit_file(file_path, modifications, dry_run=dry_run)
            result.results.append(edit_result)

            if edit_result.success:
                result.files_changed += 1
            else:
                result.files_failed += 1
                all_succeeded = False
                result.errors.extend([f"{file_path}: {err}" for err in edit_result.errors])

        # Transaction semantics: rollback if any failed
        if not all_succeeded and not dry_run:
            print(f"  ⚠️  {result.files_failed} files failed validation, rolling back all changes...")
            rollback_success = self._rollback_from_checkpoint(checkpoint_path, matching_files, root_dir=root_dir)

            if rollback_success:
                result.rollback_performed = True
                result.files_changed = 0
                print(f"  ✅ Rollback successful - all files restored")
            else:
                result.errors.append("Rollback failed - some files may be in inconsistent state")
                print(f"  ❌ Rollback failed")

        result.success = all_succeeded
        return result

    def rollback_last_edit(self) -> bool:
        """
        Rollback the most recent edit operation.

        Returns:
            True if rollback successful
        """
        # Find most recent backup
        backups = sorted(self.backup_dir.glob("backup_*"), reverse=True)

        if not backups:
            print("No backups found to rollback")
            return False

        most_recent = backups[0]

        # Find the original file path from metadata
        metadata_file = most_recent / "metadata.json"
        if not metadata_file.exists():
            print(f"Backup metadata not found: {metadata_file}")
            return False

        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            original_file = Path(metadata["original_file"])
            backup_file = most_recent / "original.yaml"

            # Restore the original file
            if backup_file.exists():
                shutil.copy2(backup_file, original_file)
                print(f"✅ Rolled back: {original_file}")
                print(f"   From backup: {most_recent}")
                return True
            else:
                print(f"❌ Backup file not found: {backup_file}")
                return False

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    # ========================================================================
    # Validation Methods
    # ========================================================================

    def validate_yaml_file(self, file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate YAML syntax and schema.

        Performs three levels of validation:
        1. Syntax validation (parseable YAML)
        2. Schema validation (required fields, types, enums)
        3. Business logic validation (ID matching, references, consistency)

        Args:
            file_path: Path to YAML file

        Returns:
            ValidationResult with errors and warnings
        """
        file_path = Path(file_path)
        result = ValidationResult(valid=True)

        if not file_path.exists():
            result.add_error(f"File not found: {file_path}")
            return result

        try:
            # Load YAML
            with open(file_path) as f:
                data = yaml.safe_load(f)

            if data is None:
                result.add_error("Empty YAML file")
                return result

            # Validate structure
            validation = self._validate_yaml_structure(data, file_path)
            result.valid = validation.valid
            result.errors = validation.errors
            result.warnings = validation.warnings

            return result

        except yaml.YAMLError as e:
            result.add_error(f"YAML syntax error: {e}")
            return result
        except Exception as e:
            result.add_error(f"Validation error: {e}")
            return result

    def _validate_yaml_structure(self, data: Dict[str, Any], file_path: Path) -> ValidationResult:
        """Internal validation of YAML structure."""
        result = ValidationResult(valid=True)

        # Determine file type from path
        if file_path.name == "task.yaml":
            self._validate_task_yaml(data, file_path, result)
        elif file_path.name == "sprint.yaml":
            self._validate_sprint_yaml(data, file_path, result)
        elif file_path.name == "track.yaml":
            self._validate_track_yaml(data, file_path, result)
        else:
            # Generic validation for other YAML files
            result.add_warning(f"Unknown YAML file type: {file_path.name}")

        return result

    def _validate_task_yaml(self, data: Dict[str, Any], file_path: Path, result: ValidationResult):
        """Validate task.yaml structure."""
        # Check for 'task' root key
        if 'task' not in data:
            result.add_error("Missing 'task' root key")
            return

        task = data['task']

        # Required fields
        required_fields = ['id', 'sprint_id', 'track_id', 'status', 'title', 'description']
        for field in required_fields:
            if field not in task:
                result.add_error(f"Missing required field: task.{field}")

        # Validate status enum
        if 'status' in task:
            valid_statuses = ['not_started', 'in_progress', 'completed', 'blocked', 'cancelled']
            if task['status'] not in valid_statuses:
                result.add_error(f"Invalid status: {task['status']} (must be one of {valid_statuses})")

        # Validate task ID matches directory
        if 'id' in task:
            expected_id = file_path.parent.name
            if task['id'] != expected_id:
                result.add_error(f"Task ID mismatch: {task['id']} != {expected_id}")

        # Validate sprint ID matches parent directory
        if 'sprint_id' in task:
            expected_sprint = file_path.parent.parent.name
            if not task['sprint_id'].startswith(expected_sprint):
                result.add_warning(f"Sprint ID may not match directory: {task['sprint_id']} vs {expected_sprint}")

        # Validate completion logic
        if task.get('status') == 'completed':
            if not task.get('completed'):
                result.add_error("Task marked completed but 'completed' timestamp missing")
        else:
            if task.get('completed'):
                result.add_warning(f"Task has completion date but status is '{task.get('status')}'")

        # Validate dates
        for date_field in ['created', 'started', 'completed']:
            if date_field in task and task[date_field]:
                if not self._validate_iso8601_date(task[date_field]):
                    result.add_error(f"Invalid date format for '{date_field}': {task[date_field]}")

    def _validate_sprint_yaml(self, data: Dict[str, Any], file_path: Path, result: ValidationResult):
        """Validate sprint.yaml structure."""
        # Check for 'sprint' root key
        if 'sprint' not in data:
            result.add_error("Missing 'sprint' root key")
            return

        sprint = data['sprint']

        # Required fields
        required_fields = ['id', 'track_id', 'status', 'name']
        for field in required_fields:
            if field not in sprint:
                result.add_error(f"Missing required field: sprint.{field}")

        # Validate status enum
        if 'status' in sprint:
            valid_statuses = ['not_started', 'in_progress', 'completion_gate_check', 'completed']
            if sprint['status'] not in valid_statuses:
                result.add_error(f"Invalid status: {sprint['status']} (must be one of {valid_statuses})")

        # Validate progress counters
        if 'progress' in sprint:
            progress = sprint['progress']
            if 'tasks_completed' in progress and 'tasks_total' in progress:
                if progress['tasks_completed'] > progress['tasks_total']:
                    result.add_error(f"Invalid progress: completed ({progress['tasks_completed']}) > total ({progress['tasks_total']})")

    def _validate_track_yaml(self, data: Dict[str, Any], file_path: Path, result: ValidationResult):
        """Validate track.yaml structure."""
        # Check for 'track' root key
        if 'track' not in data:
            result.add_error("Missing 'track' root key")
            return

        track = data['track']

        # Required fields
        required_fields = ['id', 'status', 'name']
        for field in required_fields:
            if field not in track:
                result.add_error(f"Missing required field: track.{field}")

        # Validate status enum
        if 'status' in track:
            valid_statuses = ['not_started', 'in_progress', 'blocked', 'completed']
            if track['status'] not in valid_statuses:
                result.add_error(f"Invalid status: {track['status']} (must be one of {valid_statuses})")

        # Validate progress counters
        if 'progress' in track:
            progress = track['progress']
            if 'sprints_completed' in progress and 'sprints_total' in progress:
                if progress['sprints_completed'] > progress['sprints_total']:
                    result.add_error(f"Invalid progress: completed ({progress['sprints_completed']}) > total ({progress['sprints_total']})")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _apply_modification(self, data: Dict[str, Any], field_path: str, new_value: Any) -> Any:
        """
        Apply a modification to nested dictionary using dot notation.

        Args:
            data: Dictionary to modify
            field_path: Dot-separated path (e.g., "task.status")
            new_value: New value to set

        Returns:
            Old value (or None if field didn't exist)
        """
        keys = field_path.split('.')
        current = data

        # Navigate to parent of target field
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Get old value and set new value
        final_key = keys[-1]
        old_value = current.get(final_key)
        current[final_key] = new_value

        return old_value

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _create_backup(self, file_path: Path, modifications: Dict[str, Any]) -> Path:
        """Create a backup of a file before editing."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_subdir = self.backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir(parents=True, exist_ok=True)

        # Copy original file
        backup_file = backup_subdir / "original.yaml"
        shutil.copy2(file_path, backup_file)

        # Save metadata
        metadata = {
            "original_file": str(file_path),
            "backup_timestamp": datetime.now(timezone.utc).isoformat(),
            "modification_intent": f"Modify: {', '.join(modifications.keys())}",
            "backup_path": str(backup_subdir),
            "checksum_before": self._calculate_checksum(file_path)
        }

        metadata_file = backup_subdir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Cleanup old backups
        self._cleanup_old_backups()

        return backup_subdir

    def _create_checkpoint(self, files: List[Path], root_dir: Optional[Path] = None) -> Path:
        """Create a checkpoint backup for multiple files."""
        if root_dir is None:
            root_dir = Path.cwd()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        checkpoint_dir = self.backup_dir / f"checkpoint_{timestamp}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files
        for file_path in files:
            # Preserve directory structure relative to root_dir
            try:
                rel_path = file_path.relative_to(root_dir)
            except ValueError:
                # If file is not under root_dir, use absolute path
                rel_path = Path(file_path.name)
            backup_file = checkpoint_dir / rel_path
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_file)

        # Save checkpoint metadata
        metadata = {
            "checkpoint_timestamp": datetime.now(timezone.utc).isoformat(),
            "files_count": len(files),
            "files": [str(f) for f in files]
        }

        metadata_file = checkpoint_dir / "checkpoint_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return checkpoint_dir

    def _rollback_from_checkpoint(self, checkpoint_path: Path, files: List[Path], root_dir: Optional[Path] = None) -> bool:
        """Rollback files from a checkpoint."""
        if not checkpoint_path or not checkpoint_path.exists():
            return False

        if root_dir is None:
            root_dir = Path.cwd()

        try:
            for file_path in files:
                try:
                    rel_path = file_path.relative_to(root_dir)
                except ValueError:
                    rel_path = Path(file_path.name)

                backup_file = checkpoint_path / rel_path

                if backup_file.exists():
                    shutil.copy2(backup_file, file_path)
                else:
                    print(f"  ⚠️  Backup not found for {file_path}")

            return True
        except Exception as e:
            print(f"  ❌ Rollback error: {e}")
            return False

    def _cleanup_old_backups(self):
        """Remove old backups beyond max_backups limit."""
        backups = sorted(self.backup_dir.glob("backup_*"))

        if len(backups) > self.max_backups:
            for old_backup in backups[:-self.max_backups]:
                shutil.rmtree(old_backup)

    def _log_change(
        self,
        file_path: Path,
        operation: str,
        modifications: Dict[str, Any],
        success: bool,
        error: Optional[str] = None
    ):
        """Log a change to the changes log."""
        for field, new_value in modifications.items():
            entry = ChangeLogEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                file=str(file_path),
                operation=operation,
                field=field,
                new_value=new_value,
                success=success,
                validation_passed=success,
                error=error
            )
            self.changes_log.append(entry)

    def _validate_iso8601_date(self, date_str: Any) -> bool:
        """Validate ISO 8601 date format."""
        if not isinstance(date_str, str):
            return False

        # Try parsing as ISO 8601
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False

    # ========================================================================
    # Dry-Run Operations
    # ========================================================================

    def dry_run_edit(
        self,
        file_path: Union[str, Path],
        modifications: Dict[str, Any]
    ) -> EditResult:
        """
        Preview changes without applying them.

        Args:
            file_path: Path to YAML file
            modifications: Dictionary of field paths to new values

        Returns:
            EditResult showing what would change
        """
        return self.edit_file(file_path, modifications, dry_run=True)

    def dry_run_bulk_edit(
        self,
        file_pattern: str,
        modifications: Dict[str, Any],
        root_dir: Optional[Path] = None
    ) -> BulkEditResult:
        """
        Preview bulk changes without applying them.

        Args:
            file_pattern: Glob pattern for files
            modifications: Dictionary of field paths to new values
            root_dir: Root directory for glob

        Returns:
            BulkEditResult showing what would change
        """
        return self.bulk_edit(file_pattern, modifications, dry_run=True, root_dir=root_dir)

    # ========================================================================
    # Change Log Operations
    # ========================================================================

    def export_change_log(self, output_path: Union[str, Path]) -> bool:
        """
        Export change log to YAML file.

        Args:
            output_path: Path to output file

        Returns:
            True if export successful
        """
        try:
            log_data = {
                "change_log": [
                    {
                        "timestamp": entry.timestamp,
                        "file": entry.file,
                        "operation": entry.operation,
                        "field": entry.field,
                        "old_value": entry.old_value,
                        "new_value": entry.new_value,
                        "success": entry.success,
                        "validation_passed": entry.validation_passed,
                        "error": entry.error
                    }
                    for entry in self.changes_log
                ]
            }

            with open(output_path, 'w') as f:
                yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)

            return True
        except Exception as e:
            print(f"Error exporting change log: {e}")
            return False

    def clear_change_log(self):
        """Clear the change log."""
        self.changes_log = []
