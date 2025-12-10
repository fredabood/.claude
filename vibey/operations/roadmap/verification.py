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


@dataclass
class CommitVerificationResult:
    """Result of verifying a single commit."""
    commit_hash: str
    verified: bool
    roadmap_files: List[str]
    unverified_files: List[str]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "commit_hash": self.commit_hash,
            "verified": self.verified,
            "roadmap_files": self.roadmap_files,
            "unverified_files": self.unverified_files,
            "error": self.error,
        }


class CommitRangeVerifier:
    """
    Verifies roadmap changes across a range of commits.

    Used by CI/CD pipelines to ensure all commits have
    valid activity log entries for roadmap changes.

    Task: git-integration-5-task-011
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

    def _run_git(self, *args: str):
        """Run a git command."""
        import subprocess
        cmd = ["git", "-C", str(self.root_dir)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _get_hash_index(self) -> dict:
        """Get or build hash index for fast lookups."""
        if self._hash_index is None:
            self._hash_index = self.reader.build_hash_index()
        return self._hash_index

    def _get_commits_in_range(self, commit_range: str) -> List[str]:
        """
        Get list of commits in range.

        Args:
            commit_range: Git revision range (e.g., main..HEAD)

        Returns:
            List of commit hashes
        """
        result = self._run_git("log", "--format=%H", commit_range)

        if result.returncode != 0:
            return []

        commits = [c for c in result.stdout.strip().split("\n") if c]
        return commits

    def _get_roadmap_files_in_commit(self, commit_hash: str) -> List[str]:
        """
        Get roadmap YAML files modified in a commit.

        Args:
            commit_hash: Git commit hash

        Returns:
            List of file paths
        """
        result = self._run_git(
            "diff-tree", "--no-commit-id", "--name-only", "-r",
            commit_hash,
        )

        if result.returncode != 0:
            return []

        files = []
        for f in result.stdout.strip().split("\n"):
            if f and f.startswith(".vibey/roadmap/") and f.endswith(".yaml"):
                files.append(f)

        return files

    def _get_file_hash_at_commit(self, commit_hash: str, file_path: str) -> Optional[str]:
        """
        Get SHA256 hash of file content at a specific commit.

        Args:
            commit_hash: Git commit hash
            file_path: Path to file

        Returns:
            SHA256 hash of file content, or None if file doesn't exist
        """
        result = self._run_git("show", f"{commit_hash}:{file_path}")

        if result.returncode != 0:
            return None

        import hashlib
        content = result.stdout.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def verify_commit(self, commit_hash: str) -> CommitVerificationResult:
        """
        Verify a single commit has activity log entries for roadmap changes.

        Args:
            commit_hash: Git commit hash

        Returns:
            CommitVerificationResult
        """
        roadmap_files = self._get_roadmap_files_in_commit(commit_hash)

        if not roadmap_files:
            return CommitVerificationResult(
                commit_hash=commit_hash,
                verified=True,
                roadmap_files=[],
                unverified_files=[],
            )

        hash_index = self._get_hash_index()
        unverified_files = []

        for file_path in roadmap_files:
            file_hash = self._get_file_hash_at_commit(commit_hash, file_path)

            if file_hash is None:
                # File was deleted - this is allowed
                continue

            if file_hash not in hash_index:
                unverified_files.append(file_path)

        return CommitVerificationResult(
            commit_hash=commit_hash,
            verified=len(unverified_files) == 0,
            roadmap_files=roadmap_files,
            unverified_files=unverified_files,
        )

    def verify_range(self, commit_range: str) -> List[CommitVerificationResult]:
        """
        Verify all commits in a range.

        Args:
            commit_range: Git revision range (e.g., main..HEAD)

        Returns:
            List of CommitVerificationResult
        """
        commits = self._get_commits_in_range(commit_range)
        results = []

        for commit_hash in commits:
            result = self.verify_commit(commit_hash)
            results.append(result)

        return results


def verify_commits(
    root_dir: Path,
    commit_range: str,
    json_output: bool = False,
) -> int:
    """
    Verify roadmap changes in a commit range.

    CLI wrapper for CommitRangeVerifier.

    Args:
        root_dir: Project root directory
        commit_range: Git revision range
        json_output: Output JSON instead of human-readable

    Returns:
        Exit code: 0=all verified, 1=some unverified, 2=error
    """
    try:
        verifier = CommitRangeVerifier(root_dir)
        results = verifier.verify_range(commit_range)
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"❌ Error: {e}")
        return 2

    if not results:
        if json_output:
            print(json.dumps({"commits": [], "all_verified": True}, indent=2))
        else:
            print("No commits found in range")
        return 0

    # Check for failures
    failed = [r for r in results if not r.verified]
    all_verified = len(failed) == 0

    if json_output:
        output = {
            "commit_range": commit_range,
            "total_commits": len(results),
            "verified_commits": len(results) - len(failed),
            "failed_commits": len(failed),
            "all_verified": all_verified,
            "commits": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Verifying commits: {commit_range}")
        print(f"{'='*60}\n")

        for result in results:
            if result.verified:
                if result.roadmap_files:
                    print(f"✅ {result.commit_hash[:8]} - {len(result.roadmap_files)} files verified")
                # Skip commits with no roadmap files
            else:
                print(f"❌ {result.commit_hash[:8]} - {len(result.unverified_files)} unverified files:")
                for f in result.unverified_files:
                    print(f"     - {f}")

        print()
        if all_verified:
            verified_count = sum(1 for r in results if r.roadmap_files)
            print(f"✅ All {verified_count} commits with roadmap changes verified")
        else:
            print(f"❌ {len(failed)} commits have unverified roadmap changes")
            print("\nTo fix: Use 'vibey roadmap' CLI commands to make changes")
        print()

    return 0 if all_verified else 1
