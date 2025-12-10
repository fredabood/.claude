"""
Verification module for roadmap integrity.

Verifies that roadmap file changes have corresponding activity log entries.
Used by git hooks and CI to enforce CLI-only modifications.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import json

from vibey.operations.roadmap.jsonl_activity_log import (
    ActivityLogReader,
    CommandActivityEvent,
    compute_file_hash,
)
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


@dataclass
class VerificationResult:
    """Result of verifying a single file."""
    file_path: Path
    verified: bool
    current_hash: str
    matching_event: Optional[CommandActivityEvent] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        result = {
            "file_path": str(self.file_path),
            "verified": self.verified,
            "current_hash": self.current_hash,
        }
        if self.matching_event:
            result["event"] = {
                "id": self.matching_event.id,
                "timestamp": self.matching_event.timestamp,
                "command": self.matching_event.command,
                "object_type": self.matching_event.object_type,
                "object_id": self.matching_event.object_id,
            }
        if self.error:
            result["error"] = self.error
        return result


class ChangeVerifier:
    """
    Verifies roadmap file changes against the activity log.

    Looks up files by their SHA256 hash in the activity log.
    A file is "verified" if its current hash matches a file_hash_after
    in the activity log.
    """

    def __init__(self, root_dir: Path):
        """
        Initialize verifier.

        Args:
            root_dir: Project root directory
        """
        self.root_dir = Path(root_dir)
        self.fs = FileSystemManager(root_dir)
        self.reader = ActivityLogReader(self.fs.roadmap_root / "activity_log")
        self._hash_index: Optional[dict] = None

    def _get_hash_index(self) -> dict:
        """Get or build hash index for fast lookups."""
        if self._hash_index is None:
            self._hash_index = self.reader.build_hash_index()
        return self._hash_index

    def verify_file(self, file_path: Path, use_index: bool = False) -> VerificationResult:
        """
        Verify a single roadmap file.

        Args:
            file_path: Path to file (absolute or relative to root_dir)
            use_index: Use pre-built index for faster lookups

        Returns:
            VerificationResult with verification status
        """
        # Resolve to absolute path
        if not file_path.is_absolute():
            full_path = self.root_dir / file_path
        else:
            full_path = file_path

        # Check file exists
        if not full_path.exists():
            return VerificationResult(
                file_path=file_path,
                verified=False,
                current_hash="",
                error=f"File not found: {file_path}",
            )

        # Compute current hash
        try:
            current_hash = compute_file_hash(full_path)
        except Exception as e:
            return VerificationResult(
                file_path=file_path,
                verified=False,
                current_hash="",
                error=f"Failed to compute hash: {e}",
            )

        # Look up in activity log
        if use_index:
            index = self._get_hash_index()
            event = index.get(current_hash)
        else:
            event = self.reader.find_by_hash(current_hash)

        return VerificationResult(
            file_path=file_path,
            verified=event is not None,
            current_hash=current_hash,
            matching_event=event,
        )

    def verify_files(self, file_paths: List[Path]) -> List[VerificationResult]:
        """
        Verify multiple files efficiently.

        Uses pre-built hash index for batch verification.

        Args:
            file_paths: List of file paths to verify

        Returns:
            List of VerificationResult objects
        """
        results = []
        for file_path in file_paths:
            result = self.verify_file(file_path, use_index=True)
            results.append(result)
        return results

    def verify_staged_files(self) -> List[VerificationResult]:
        """
        Verify all staged roadmap YAML files.

        Used by pre-commit hook.

        Returns:
            List of VerificationResult for staged files
        """
        import subprocess

        # Get staged files
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            staged_files = result.stdout.strip().split('\n')
        except subprocess.CalledProcessError as e:
            return []

        # Filter to roadmap YAML files
        roadmap_files = []
        for f in staged_files:
            if f and '.vibey/roadmap' in f and f.endswith('.yaml'):
                roadmap_files.append(Path(f))

        return self.verify_files(roadmap_files)


def verify_change(
    root_dir: Path,
    file_path: Path,
    json_output: bool = False,
) -> int:
    """
    Verify a roadmap file change.

    CLI wrapper for ChangeVerifier.verify_file().

    Args:
        root_dir: Project root directory
        file_path: Path to file to verify
        json_output: Output JSON instead of human-readable

    Returns:
        Exit code: 0=verified, 1=unverified, 2=error
    """
    verifier = ChangeVerifier(root_dir)
    result = verifier.verify_file(file_path)

    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.error:
            print(f"❌ Error: {result.error}")
            return 2
        elif result.verified:
            print(f"✅ Verified: {file_path}")
            if result.matching_event:
                print(f"   Command: {result.matching_event.command}")
                print(f"   Time: {result.matching_event.timestamp}")
        else:
            print(f"❌ Unverified: {file_path}")
            print(f"   Hash: {result.current_hash}")
            print("   No matching activity log entry found")

    if result.error:
        return 2
    return 0 if result.verified else 1
