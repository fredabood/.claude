"""
Error handling and recovery for git integration.

This module provides:
- Transaction-like updates with automatic rollback
- Corruption detection and validation
- Manual recovery commands
- State validation and repair
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml


@dataclass
class BackupInfo:
    """Information about a roadmap backup."""
    backup_path: Path
    original_path: Path
    timestamp: datetime
    operation: str
    git_sha: Optional[str] = None


@dataclass
class ValidationIssue:
    """An issue found during validation."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'yaml', 'git', 'consistency'
    file_path: Optional[str]
    issue: str
    suggestion: Optional[str] = None


@dataclass
class RepairResult:
    """Result of a repair operation."""
    success: bool
    issues_found: int
    issues_fixed: int
    issues_remaining: int
    fixes_applied: List[str]
    errors: List[str]


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    commit_sha: str
    files_restored: List[str]
    error: Optional[str] = None


class TransactionalUpdate:
    """
    Context manager for transaction-like roadmap updates.

    Usage:
        with TransactionalUpdate(roadmap_root, "task status update") as txn:
            txn.modify_file(task_file, updated_data)
            # If any exception occurs, changes are rolled back
            txn.commit()  # Explicitly commit changes
    """

    def __init__(self, roadmap_root: Path, operation: str):
        self.roadmap_root = Path(roadmap_root)
        self.operation = operation
        self.backup_dir: Optional[Path] = None
        self.backups: List[BackupInfo] = []
        self.committed = False

    def __enter__(self) -> 'TransactionalUpdate':
        """Start transaction by creating backup directory."""
        self.backup_dir = Path(tempfile.mkdtemp(prefix="vibey_backup_"))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup: rollback if not committed, remove backups if committed."""
        if exc_type is not None or not self.committed:
            # Exception occurred or commit() was never called - rollback
            self._rollback()
        else:
            # Success - remove backups
            self._cleanup_backups()

    def backup_file(self, file_path: Path) -> BackupInfo:
        """Create backup of a file before modification."""
        if not self.backup_dir:
            raise RuntimeError("Transaction not started")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create backup with same relative structure
        rel_path = file_path.relative_to(self.roadmap_root)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(file_path, backup_path)

        backup = BackupInfo(
            backup_path=backup_path,
            original_path=file_path,
            timestamp=datetime.now(timezone.utc),
            operation=self.operation
        )
        self.backups.append(backup)
        return backup

    def modify_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Modify a YAML file with backup."""
        file_path = Path(file_path)

        # Backup before modification
        self.backup_file(file_path)

        # Write new data
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def commit(self) -> None:
        """Mark transaction as successful."""
        self.committed = True

    def _rollback(self) -> None:
        """Restore all backed up files."""
        for backup in reversed(self.backups):
            if backup.backup_path.exists():
                shutil.copy2(backup.backup_path, backup.original_path)

    def _cleanup_backups(self) -> None:
        """Remove backup directory."""
        if self.backup_dir and self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)


class ErrorHandler:
    """
    Error handling and recovery for git integration.

    Provides:
    - YAML validation and corruption detection
    - Git-roadmap consistency checking
    - Automatic repair of common issues
    - Manual rollback to previous git commits
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.roadmap_root = self.repo_path / ".vibey" / "roadmap"

    def validate_roadmap(self, fix: bool = False) -> Tuple[List[ValidationIssue], Optional[str]]:
        """
        Validate roadmap YAML files and git state consistency.

        Args:
            fix: If True, attempt to fix issues automatically

        Returns:
            (issues, error) tuple
        """
        issues: List[ValidationIssue] = []

        if not self.roadmap_root.exists():
            return issues, "Roadmap directory not found"

        # 1. Validate YAML syntax and schema
        yaml_issues = self._validate_yaml_files()
        issues.extend(yaml_issues)

        # 2. Validate task/sprint references
        ref_issues = self._validate_references()
        issues.extend(ref_issues)

        # 3. Validate git state consistency
        git_issues = self._validate_git_consistency()
        issues.extend(git_issues)

        # 4. Check for orphaned files
        orphan_issues = self._check_orphaned_files()
        issues.extend(orphan_issues)

        return issues, None

    def _validate_yaml_files(self) -> List[ValidationIssue]:
        """Validate YAML syntax in all roadmap files."""
        issues = []

        for yaml_file in self.roadmap_root.rglob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                issues.append(ValidationIssue(
                    severity='error',
                    category='yaml',
                    file_path=str(yaml_file.relative_to(self.roadmap_root)),
                    issue=f"YAML syntax error: {e}",
                    suggestion="Fix YAML syntax or restore from git history"
                ))
            except Exception as e:
                issues.append(ValidationIssue(
                    severity='error',
                    category='yaml',
                    file_path=str(yaml_file.relative_to(self.roadmap_root)),
                    issue=f"Error reading file: {e}",
                    suggestion="Check file permissions and content"
                ))

        return issues

    def _validate_references(self) -> List[ValidationIssue]:
        """Validate task and sprint ID references using flat structure."""
        issues = []

        # Load all IDs from flat structure directories
        track_ids = set()
        sprint_ids = set()
        task_ids = set()

        tracks_dir = self.roadmap_root / "tracks"
        sprints_dir = self.roadmap_root / "sprints"
        tasks_dir = self.roadmap_root / "tasks"

        # Collect track IDs from flat tracks/ directory
        if tracks_dir.exists():
            for track_file in tracks_dir.glob("*.yaml"):
                if track_file.name.startswith('.'):
                    continue
                try:
                    with open(track_file) as f:
                        track_data = yaml.safe_load(f)
                        if track_data and 'track' in track_data:
                            track_ids.add(track_data['track'].get('id'))
                except Exception:
                    pass

        # Collect sprint IDs from flat sprints/ directory
        if sprints_dir.exists():
            for sprint_file in sprints_dir.glob("*.yaml"):
                if sprint_file.name.startswith('.'):
                    continue
                try:
                    with open(sprint_file) as f:
                        sprint_data = yaml.safe_load(f)
                        if sprint_data and 'sprint' in sprint_data:
                            sprint_ids.add(sprint_data['sprint'].get('id'))
                except Exception:
                    pass

        # Collect task IDs from flat tasks/ directory
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                try:
                    with open(task_file) as f:
                        task_data = yaml.safe_load(f)
                        if task_data and 'task' in task_data:
                            task_ids.add(task_data['task'].get('id'))
                except Exception:
                    pass

        # Validate references in track files
        if tracks_dir.exists():
            for track_file in tracks_dir.glob("*.yaml"):
                if track_file.name.startswith('.'):
                    continue
                try:
                    with open(track_file) as f:
                        track_data = yaml.safe_load(f)

                    if not track_data or 'track' not in track_data:
                        continue

                    track = track_data['track']

                    # Check sprint references
                    for sprint_ref in track.get('sprints', []):
                        sprint_id = sprint_ref.get('id')
                        if sprint_id and sprint_id not in sprint_ids:
                            issues.append(ValidationIssue(
                                severity='error',
                                category='consistency',
                                file_path=f"tracks/{track_file.name}",
                                issue=f"Track references non-existent sprint: {sprint_id}",
                                suggestion=f"Create sprint file sprints/{sprint_id}.yaml"
                            ))

                    # Check dependency references
                    dependencies = track.get('dependencies', [])
                    if dependencies and isinstance(dependencies, list):
                        for dep in dependencies:
                            if not isinstance(dep, str):
                                continue
                            if dep not in track_ids:
                                issues.append(ValidationIssue(
                                    severity='warning',
                                    category='consistency',
                                    file_path=f"tracks/{track_file.name}",
                                    issue=f"Track dependency not found: {dep}",
                                    suggestion="Remove invalid dependency or create missing track"
                                ))

                except Exception as e:
                    issues.append(ValidationIssue(
                        severity='error',
                        category='yaml',
                        file_path=f"tracks/{track_file.name}",
                        issue=f"Error validating references: {e}",
                        suggestion="Check YAML syntax and structure"
                    ))

        return issues

    def _validate_git_consistency(self) -> List[ValidationIssue]:
        """Validate consistency between git state and roadmap."""
        issues = []

        # Check if we're in a git repo
        try:
            subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            issues.append(ValidationIssue(
                severity='info',
                category='git',
                file_path=None,
                issue="Not a git repository",
                suggestion="Initialize git repo or use YAML-only mode"
            ))
            return issues

        # Check for uncommitted changes in roadmap
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain', '.vibey/roadmap'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                issues.append(ValidationIssue(
                    severity='warning',
                    category='git',
                    file_path=None,
                    issue="Uncommitted changes in roadmap files",
                    suggestion="Commit changes to preserve history"
                ))
        except subprocess.CalledProcessError:
            pass

        return issues

    def _check_orphaned_files(self) -> List[ValidationIssue]:
        """Check for orphaned sprints/tasks without valid parent references."""
        issues = []

        tracks_dir = self.roadmap_root / "tracks"
        sprints_dir = self.roadmap_root / "sprints"
        tasks_dir = self.roadmap_root / "tasks"

        # Collect valid track and sprint IDs
        track_ids = set()
        sprint_ids = set()

        if tracks_dir.exists():
            for track_file in tracks_dir.glob("*.yaml"):
                if track_file.name.startswith('.'):
                    continue
                try:
                    with open(track_file) as f:
                        data = yaml.safe_load(f)
                        if data and 'track' in data:
                            track_ids.add(data['track'].get('id'))
                except Exception:
                    pass

        if sprints_dir.exists():
            for sprint_file in sprints_dir.glob("*.yaml"):
                if sprint_file.name.startswith('.'):
                    continue
                try:
                    with open(sprint_file) as f:
                        data = yaml.safe_load(f)
                        if data and 'sprint' in data:
                            sprint_ids.add(data['sprint'].get('id'))
                            # Check sprint references valid track
                            track_id = data['sprint'].get('track_id')
                            if track_id and track_id not in track_ids:
                                issues.append(ValidationIssue(
                                    severity='warning',
                                    category='consistency',
                                    file_path=f"sprints/{sprint_file.name}",
                                    issue=f"Sprint references non-existent track: {track_id}",
                                    suggestion="Fix track_id or remove orphaned sprint"
                                ))
                except Exception:
                    pass

        # Check tasks reference valid sprints
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                try:
                    with open(task_file) as f:
                        data = yaml.safe_load(f)
                        if data and 'task' in data:
                            sprint_id = data['task'].get('sprint_id')
                            if sprint_id and sprint_id not in sprint_ids:
                                issues.append(ValidationIssue(
                                    severity='warning',
                                    category='consistency',
                                    file_path=f"tasks/{task_file.name}",
                                    issue=f"Task references non-existent sprint: {sprint_id}",
                                    suggestion="Fix sprint_id or remove orphaned task"
                                ))
                except Exception:
                    pass

        # Check for legacy hierarchical ULID directories (should not exist)
        for item in self.roadmap_root.iterdir():
            if item.is_dir() and item.name.startswith('01K'):
                issues.append(ValidationIssue(
                    severity='warning',
                    category='consistency',
                    file_path=item.name,
                    issue=f"Legacy hierarchical ULID directory found: {item.name}",
                    suggestion="Delete legacy directory or run migration"
                ))

        return issues

    def repair(self, dry_run: bool = False) -> Tuple[RepairResult, Optional[str]]:
        """
        Attempt to repair common roadmap issues.

        Args:
            dry_run: If True, only report what would be fixed

        Returns:
            (result, error) tuple
        """
        # First validate to find issues
        issues, error = self.validate_roadmap(fix=False)
        if error:
            return RepairResult(
                success=False,
                issues_found=0,
                issues_fixed=0,
                issues_remaining=0,
                fixes_applied=[],
                errors=[error]
            ), error

        fixes_applied = []
        errors = []

        # Only attempt to fix certain types of issues
        fixable_issues = [i for i in issues if i.severity != 'info']

        if dry_run:
            # Just report what would be fixed
            potential_fixes = []
            for issue in fixable_issues:
                if issue.category == 'yaml':
                    potential_fixes.append(f"Would restore {issue.file_path} from git")
                elif issue.category == 'consistency':
                    potential_fixes.append(f"Would fix consistency issue in {issue.file_path}")

            return RepairResult(
                success=True,
                issues_found=len(issues),
                issues_fixed=0,
                issues_remaining=len(fixable_issues),
                fixes_applied=potential_fixes,
                errors=[]
            ), None

        # Attempt actual repairs
        for issue in fixable_issues:
            try:
                if issue.category == 'yaml' and issue.file_path:
                    # Try to restore from git
                    file_path = self.roadmap_root / issue.file_path
                    self._restore_from_git(file_path)
                    fixes_applied.append(f"Restored {issue.file_path} from git")
            except Exception as e:
                errors.append(f"Failed to fix {issue.file_path}: {e}")

        # Re-validate to count remaining issues
        remaining_issues, _ = self.validate_roadmap(fix=False)

        return RepairResult(
            success=len(errors) == 0,
            issues_found=len(issues),
            issues_fixed=len(fixes_applied),
            issues_remaining=len([i for i in remaining_issues if i.severity != 'info']),
            fixes_applied=fixes_applied,
            errors=errors
        ), None

    def _restore_from_git(self, file_path: Path) -> None:
        """Restore a file from git HEAD."""
        rel_path = file_path.relative_to(self.repo_path)
        subprocess.run(
            ['git', 'checkout', 'HEAD', '--', str(rel_path)],
            cwd=self.repo_path,
            check=True
        )

    def rollback(self, commit_sha: str, files: Optional[List[str]] = None) -> Tuple[RollbackResult, Optional[str]]:
        """
        Restore roadmap state from a specific git commit.

        Args:
            commit_sha: Git commit SHA to restore from
            files: Optional list of specific files to restore (relative to roadmap root)

        Returns:
            (result, error) tuple
        """
        # Validate commit exists
        try:
            subprocess.run(
                ['git', 'rev-parse', commit_sha],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            return RollbackResult(
                success=False,
                commit_sha=commit_sha,
                files_restored=[],
                error=f"Commit not found: {commit_sha}"
            ), f"Commit not found: {commit_sha}"

        files_restored = []

        try:
            if files:
                # Restore specific files
                for file in files:
                    file_path = f".vibey/roadmap/{file}"
                    subprocess.run(
                        ['git', 'checkout', commit_sha, '--', file_path],
                        cwd=self.repo_path,
                        check=True
                    )
                    files_restored.append(file)
            else:
                # Restore entire roadmap directory
                subprocess.run(
                    ['git', 'checkout', commit_sha, '--', '.vibey/roadmap'],
                    cwd=self.repo_path,
                    check=True
                )
                files_restored.append('.vibey/roadmap/*')

            return RollbackResult(
                success=True,
                commit_sha=commit_sha,
                files_restored=files_restored,
                error=None
            ), None

        except subprocess.CalledProcessError as e:
            return RollbackResult(
                success=False,
                commit_sha=commit_sha,
                files_restored=files_restored,
                error=f"Git checkout failed: {e}"
            ), f"Git checkout failed: {e}"


def validate_roadmap(repo_path: str = ".", fix: bool = False) -> Tuple[List[ValidationIssue], Optional[str]]:
    """
    Convenience function to validate roadmap.

    Args:
        repo_path: Path to repository root
        fix: Attempt to fix issues automatically

    Returns:
        (issues, error) tuple
    """
    handler = ErrorHandler(repo_path)
    return handler.validate_roadmap(fix=fix)


def repair_roadmap(repo_path: str = ".", dry_run: bool = False) -> Tuple[RepairResult, Optional[str]]:
    """
    Convenience function to repair roadmap issues.

    Args:
        repo_path: Path to repository root
        dry_run: If True, only report what would be fixed

    Returns:
        (result, error) tuple
    """
    handler = ErrorHandler(repo_path)
    return handler.repair(dry_run=dry_run)


def rollback_roadmap(commit_sha: str, repo_path: str = ".", files: Optional[List[str]] = None) -> Tuple[RollbackResult, Optional[str]]:
    """
    Convenience function to rollback roadmap to a commit.

    Args:
        commit_sha: Git commit SHA to restore from
        repo_path: Path to repository root
        files: Optional list of specific files to restore

    Returns:
        (result, error) tuple
    """
    handler = ErrorHandler(repo_path)
    return handler.rollback(commit_sha, files)
