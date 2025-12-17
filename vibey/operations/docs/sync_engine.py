"""
Documentation Synchronization Engine

Synchronizes documentation from .vibey/roadmap/ to docs/roadmap/ based on
configuration rules. Supports incremental sync with change detection.

Key Features:
- Syncs markdown files from source to target
- Respects include/exclude patterns (glob-based)
- Incremental sync (only changed files)
- Checksum-based change detection
- Preserves directory structure
"""

import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import fnmatch

from .sync_manifest import SyncManifest


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    files_copied: List[str]
    files_skipped: List[str]
    files_deleted: List[str]
    errors: List[Tuple[str, str]]  # (file, error_message)
    duration_seconds: float

    @property
    def success(self) -> bool:
        """Check if sync completed without errors."""
        return len(self.errors) == 0

    @property
    def total_files(self) -> int:
        """Total files processed."""
        return len(self.files_copied) + len(self.files_skipped)


@dataclass
class SyncConfig:
    """Configuration for synchronization."""
    enabled: bool = True
    source_dir: str = ".vibey/roadmap"
    target_dir: str = "docs/roadmap"
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    delete_orphaned: bool = False  # Delete files in target not in source

    def __post_init__(self):
        """Set default patterns if not provided."""
        if self.include_patterns is None:
            self.include_patterns = ["**/*.md"]  # Only markdown files
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "**/*.yaml",
                "**/*.json",
                "**/.id",
                "**/context/**",  # Skip context directories for now
            ]


class SyncEngine:
    """
    Documentation synchronization engine.

    Copies markdown documentation from .vibey/roadmap/ to docs/roadmap/
    with incremental sync based on checksums.
    """

    def __init__(self, config: Optional[SyncConfig] = None, manifest_path: Optional[str] = None):
        """
        Initialize sync engine.

        Args:
            config: Synchronization configuration (uses defaults if None)
            manifest_path: Path to sync manifest (defaults to .vibey/roadmap/.sync-manifest.json)
        """
        self.config = config or SyncConfig()
        self.source_root = Path(self.config.source_dir)
        self.target_root = Path(self.config.target_dir)
        self.manifest = SyncManifest(manifest_path or f"{self.config.source_dir}/.sync-manifest.json")

    def sync(self, dry_run: bool = False) -> SyncResult:
        """
        Synchronize documentation from source to target.

        Args:
            dry_run: If True, show what would be synced without actually copying

        Returns:
            SyncResult with details of synchronization
        """
        start_time = datetime.now(timezone.utc)

        files_copied = []
        files_skipped = []
        files_deleted = []
        errors = []

        try:
            # Ensure source exists
            if not self.source_root.exists():
                errors.append((str(self.source_root), "Source directory does not exist"))
                return SyncResult(
                    files_copied=files_copied,
                    files_skipped=files_skipped,
                    files_deleted=files_deleted,
                    errors=errors,
                    duration_seconds=0.0
                )

            # Create target directory if it doesn't exist
            if not dry_run:
                self.target_root.mkdir(parents=True, exist_ok=True)

            # Find all files matching include patterns
            source_files = self._find_source_files()

            # Sync each file
            for source_file in source_files:
                try:
                    target_file = self._get_target_path(source_file)

                    # Check if file needs to be copied (using manifest)
                    if self.manifest.is_file_changed(source_file, self.source_root):
                        if not dry_run:
                            # Create target directory
                            target_file.parent.mkdir(parents=True, exist_ok=True)

                            # Copy file
                            shutil.copy2(source_file, target_file)

                            # Record in manifest
                            self.manifest.record_file_sync(
                                source_file, target_file,
                                self.source_root, self.target_root
                            )

                        files_copied.append(str(source_file.relative_to(self.source_root)))
                    else:
                        files_skipped.append(str(source_file.relative_to(self.source_root)))

                except Exception as e:
                    errors.append((str(source_file), str(e)))

            # Handle orphaned files (files in target but not in source)
            if self.config.delete_orphaned:
                orphaned = self._find_orphaned_files(source_files)
                for orphaned_file in orphaned:
                    try:
                        if not dry_run:
                            orphaned_file.unlink()
                        files_deleted.append(str(orphaned_file.relative_to(self.target_root)))
                    except Exception as e:
                        errors.append((str(orphaned_file), str(e)))

            # Record sync operation in manifest and save
            if not dry_run:
                self.manifest.record_sync_operation(
                    files_copied=len(files_copied),
                    files_skipped=len(files_skipped),
                    files_deleted=len(files_deleted),
                    duration_seconds=0.0,  # Will be updated below
                    errors=len(errors)
                )
                self.manifest.save()

        except Exception as e:
            errors.append(("sync_operation", str(e)))

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Update duration in manifest if not dry run
        if not dry_run and self.manifest.sync_history:
            self.manifest.sync_history[-1].duration_seconds = duration
            self.manifest.save()

        return SyncResult(
            files_copied=files_copied,
            files_skipped=files_skipped,
            files_deleted=files_deleted,
            errors=errors,
            duration_seconds=duration
        )

    def _find_source_files(self) -> List[Path]:
        """
        Find all source files matching include patterns and not matching exclude patterns.

        Returns:
            List of source file paths
        """
        matching_files = []

        # Find all files matching include patterns
        for pattern in self.config.include_patterns:
            for file in self.source_root.glob(pattern):
                if file.is_file():
                    # Check if file matches any exclude pattern
                    relative_path = str(file.relative_to(self.source_root))
                    excluded = False

                    for exclude_pattern in self.config.exclude_patterns:
                        if fnmatch.fnmatch(relative_path, exclude_pattern) or \
                           fnmatch.fnmatch(file.name, exclude_pattern):
                            excluded = True
                            break

                    if not excluded and file not in matching_files:
                        matching_files.append(file)

        return sorted(matching_files)

    def _get_target_path(self, source_file: Path) -> Path:
        """
        Get target path for a source file.

        Args:
            source_file: Source file path

        Returns:
            Target file path
        """
        relative_path = source_file.relative_to(self.source_root)
        return self.target_root / relative_path

    def _needs_sync(self, source_file: Path, target_file: Path) -> bool:
        """
        Check if a file needs to be synchronized.

        Args:
            source_file: Source file path
            target_file: Target file path

        Returns:
            True if file needs to be synchronized
        """
        # If target doesn't exist, need to sync
        if not target_file.exists():
            return True

        # Compare checksums
        source_checksum = self._calculate_checksum(source_file)
        target_checksum = self._calculate_checksum(target_file)

        return source_checksum != target_checksum

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA-256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal checksum string
        """
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _find_orphaned_files(self, source_files: List[Path]) -> List[Path]:
        """
        Find files in target that don't exist in source.

        Args:
            source_files: List of source files

        Returns:
            List of orphaned target files
        """
        if not self.target_root.exists():
            return []

        # Get set of expected target paths
        expected_targets = {self._get_target_path(sf) for sf in source_files}

        # Find all target files
        orphaned = []
        for target_file in self.target_root.rglob("*"):
            if target_file.is_file() and target_file not in expected_targets:
                # Only consider files that match our include patterns
                relative_path = str(target_file.relative_to(self.target_root))
                for pattern in self.config.include_patterns:
                    if fnmatch.fnmatch(relative_path, pattern):
                        orphaned.append(target_file)
                        break

        return orphaned

    def get_sync_preview(self) -> Dict:
        """
        Get preview of what would be synchronized.

        Returns:
            Dictionary with preview information
        """
        source_files = self._find_source_files()

        to_copy = []
        to_skip = []
        to_delete = []

        for source_file in source_files:
            target_file = self._get_target_path(source_file)
            if self._needs_sync(source_file, target_file):
                to_copy.append(str(source_file.relative_to(self.source_root)))
            else:
                to_skip.append(str(source_file.relative_to(self.source_root)))

        if self.config.delete_orphaned:
            orphaned = self._find_orphaned_files(source_files)
            to_delete = [str(f.relative_to(self.target_root)) for f in orphaned]

        return {
            "files_to_copy": to_copy,
            "files_to_skip": to_skip,
            "files_to_delete": to_delete,
            "total_files": len(source_files)
        }
