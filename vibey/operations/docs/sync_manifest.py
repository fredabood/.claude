"""
Sync Manifest Tracking System

Tracks synchronized files with checksums, timestamps, and source→target mappings.
Enables incremental sync by detecting which files have changed since last sync.

Manifest Format (.vibey/roadmap/.sync-manifest.json):
{
    "version": "1.0",
    "last_sync": "2025-11-09T19:30:00Z",
    "files": {
        "track.md": {
            "source_path": ".vibey/roadmap/documentation-system/track.md",
            "target_path": "docs/roadmap/documentation-system/track.md",
            "checksum": "abc123...",
            "synced_at": "2025-11-09T19:30:00Z",
            "file_size": 1234
        }
    },
    "sync_history": [
        {
            "timestamp": "2025-11-09T19:30:00Z",
            "files_copied": 10,
            "files_skipped": 5,
            "duration_seconds": 0.5
        }
    ]
}
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class FileSyncRecord:
    """Record of a synchronized file."""
    source_path: str
    target_path: str
    checksum: str
    synced_at: str  # ISO 8601 timestamp
    file_size: int

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'FileSyncRecord':
        """Create from dictionary."""
        return FileSyncRecord(**data)


@dataclass
class SyncHistoryEntry:
    """Entry in sync history."""
    timestamp: str  # ISO 8601
    files_copied: int
    files_skipped: int
    files_deleted: int
    duration_seconds: float
    errors: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'SyncHistoryEntry':
        """Create from dictionary."""
        return SyncHistoryEntry(**data)


class SyncManifest:
    """
    Sync manifest for tracking synchronized files.

    Stores checksums, timestamps, and mappings for incremental sync.
    """

    MANIFEST_VERSION = "1.0"

    def __init__(self, manifest_path: str = ".vibey/roadmap/.sync-manifest.json"):
        """
        Initialize sync manifest.

        Args:
            manifest_path: Path to manifest file
        """
        self.manifest_path = Path(manifest_path)
        self.version = self.MANIFEST_VERSION
        self.last_sync: Optional[str] = None
        self.files: Dict[str, FileSyncRecord] = {}
        self.sync_history: List[SyncHistoryEntry] = []

        # Load existing manifest if it exists
        if self.manifest_path.exists():
            self.load()

    def load(self):
        """Load manifest from disk."""
        try:
            with open(self.manifest_path, 'r') as f:
                data = json.load(f)

            self.version = data.get('version', self.MANIFEST_VERSION)
            self.last_sync = data.get('last_sync')

            # Load file records
            self.files = {}
            for key, file_data in data.get('files', {}).items():
                self.files[key] = FileSyncRecord.from_dict(file_data)

            # Load sync history
            self.sync_history = []
            for entry_data in data.get('sync_history', []):
                self.sync_history.append(SyncHistoryEntry.from_dict(entry_data))

        except Exception as e:
            print(f"Warning: Failed to load sync manifest: {e}")
            # Continue with empty manifest

    def save(self):
        """Save manifest to disk (atomically)."""
        # Create parent directory if it doesn't exist
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data
        data = {
            'version': self.version,
            'last_sync': self.last_sync,
            'files': {
                key: record.to_dict()
                for key, record in self.files.items()
            },
            'sync_history': [
                entry.to_dict()
                for entry in self.sync_history
            ]
        }

        # Write atomically (write to temp file, then rename)
        temp_path = self.manifest_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            temp_path.replace(self.manifest_path)

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def record_file_sync(
        self,
        source_path: Path,
        target_path: Path,
        source_root: Path,
        target_root: Path
    ):
        """
        Record a file synchronization.

        Args:
            source_path: Absolute source file path
            target_path: Absolute target file path
            source_root: Source root directory
            target_root: Target root directory
        """
        # Calculate relative path for key
        relative_path = str(source_path.relative_to(source_root))

        # Calculate checksum
        checksum = self._calculate_checksum(source_path)

        # Get file size
        file_size = source_path.stat().st_size

        # Create record
        record = FileSyncRecord(
            source_path=str(source_path.relative_to(source_root.parent)),
            target_path=str(target_path.relative_to(target_root.parent)),
            checksum=checksum,
            synced_at=datetime.now(timezone.utc).isoformat(),
            file_size=file_size
        )

        self.files[relative_path] = record

    def record_sync_operation(
        self,
        files_copied: int,
        files_skipped: int,
        files_deleted: int,
        duration_seconds: float,
        errors: int = 0
    ):
        """
        Record a complete sync operation in history.

        Args:
            files_copied: Number of files copied
            files_skipped: Number of files skipped
            files_deleted: Number of files deleted
            duration_seconds: Duration of sync
            errors: Number of errors encountered
        """
        entry = SyncHistoryEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            files_copied=files_copied,
            files_skipped=files_skipped,
            files_deleted=files_deleted,
            duration_seconds=duration_seconds,
            errors=errors
        )

        self.sync_history.append(entry)

        # Keep only last 50 entries
        if len(self.sync_history) > 50:
            self.sync_history = self.sync_history[-50:]

        # Update last sync timestamp
        self.last_sync = entry.timestamp

    def is_file_changed(self, source_path: Path, source_root: Path) -> bool:
        """
        Check if a file has changed since last sync.

        Args:
            source_path: Absolute source file path
            source_root: Source root directory

        Returns:
            True if file has changed or is new
        """
        relative_path = str(source_path.relative_to(source_root))

        # If file not in manifest, it's new
        if relative_path not in self.files:
            return True

        # Compare checksums
        current_checksum = self._calculate_checksum(source_path)
        recorded_checksum = self.files[relative_path].checksum

        return current_checksum != recorded_checksum

    def remove_file(self, relative_path: str):
        """
        Remove a file from the manifest.

        Args:
            relative_path: Relative path of file to remove
        """
        if relative_path in self.files:
            del self.files[relative_path]

    def get_file_record(self, relative_path: str) -> Optional[FileSyncRecord]:
        """
        Get sync record for a file.

        Args:
            relative_path: Relative path of file

        Returns:
            FileSyncRecord or None if not found
        """
        return self.files.get(relative_path)

    def get_recent_history(self, limit: int = 10) -> List[SyncHistoryEntry]:
        """
        Get recent sync history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent sync history entries (newest first)
        """
        return list(reversed(self.sync_history[-limit:]))

    def get_total_synced_files(self) -> int:
        """Get total number of files currently tracked."""
        return len(self.files)

    def get_total_synced_size(self) -> int:
        """Get total size of all synced files in bytes."""
        return sum(record.file_size for record in self.files.values())

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

    def print_summary(self):
        """Print summary of manifest state."""
        print(f"Sync Manifest Summary")
        print(f"=" * 60)
        print(f"Version: {self.version}")
        print(f"Last sync: {self.last_sync or 'Never'}")
        print(f"Total files tracked: {self.get_total_synced_files()}")
        print(f"Total size: {self.get_total_synced_size():,} bytes")
        print()

        if self.sync_history:
            print("Recent Sync History:")
            for entry in self.get_recent_history(5):
                print(f"  {entry.timestamp}")
                print(f"    Copied: {entry.files_copied}, Skipped: {entry.files_skipped}, "
                      f"Deleted: {entry.files_deleted}")
                print(f"    Duration: {entry.duration_seconds:.2f}s, Errors: {entry.errors}")
                print()
