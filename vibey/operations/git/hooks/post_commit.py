"""
Post-Commit Hook Implementation

Clears the CLI change tracker after successful commits and detects
if pre-commit hook was bypassed for roadmap file changes.

Tasks: git-integration-4-task-005, git-integration-5-task-007
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class BypassDetector:
    """
    Detects when pre-commit hook was bypassed for roadmap changes.

    Compares roadmap files in the latest commit against activity log
    to detect if changes were made without CLI.

    Task: git-integration-5-task-007
    """

    def __init__(self, repo_path: Path):
        """
        Initialize bypass detector.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        self.audit_log_path = self.repo_path / ".vibey" / "audit" / "bypass.log"

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _get_head_commit_hash(self) -> Optional[str]:
        """Get the hash of the HEAD commit."""
        result = self._run_git("rev-parse", "HEAD")
        if result.returncode != 0:
            return None
        return result.stdout.strip()

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

    def _check_activity_log_for_hash(self, file_hash: str) -> bool:
        """
        Check if a file hash exists in the activity log.

        Args:
            file_hash: SHA256 hash to search for

        Returns:
            True if hash found in activity log
        """
        try:
            from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader
            from vibey.cli.roadmap_lib.filesystem import FileSystemManager

            fs = FileSystemManager(self.repo_path)
            reader = ActivityLogReader(fs.roadmap_root / "activity_log")
            hash_index = reader.build_hash_index()

            return file_hash in hash_index
        except ImportError:
            # If verification module not available, assume no bypass
            return True

    def detect_bypass(self) -> List[dict]:
        """
        Detect if pre-commit was bypassed for the latest commit.

        Returns:
            List of bypass events (empty if no bypass detected)
        """
        commit_hash = self._get_head_commit_hash()
        if not commit_hash:
            return []

        roadmap_files = self._get_roadmap_files_in_commit(commit_hash)
        if not roadmap_files:
            return []

        bypass_events = []

        for file_path in roadmap_files:
            file_hash = self._get_file_hash_at_commit(commit_hash, file_path)

            if file_hash is None:
                # File was deleted - this is allowed
                continue

            if not self._check_activity_log_for_hash(file_hash):
                bypass_events.append({
                    "type": "pre_commit_bypass",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "commit_hash": commit_hash,
                    "file_path": file_path,
                    "file_hash": file_hash,
                    "detection_source": "post_commit_hook",
                })

        return bypass_events

    def log_bypass_events(self, events: List[dict]) -> None:
        """
        Log bypass events to audit log.

        Args:
            events: List of bypass event dictionaries
        """
        if not events:
            return

        # Ensure audit directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to log file (JSONL format)
        with open(self.audit_log_path, "a") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

    def report_bypass(self, events: List[dict]) -> None:
        """
        Report bypass events to console with actionable guidance.

        Args:
            events: List of bypass event dictionaries
        """
        if not events:
            return

        # Colors
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        print()
        print(f"{BOLD}{YELLOW}[vibey] Pre-commit bypass detected!{RESET}")
        print()
        print(f"  The following roadmap files were modified without using the CLI:")
        for event in events:
            print(f"    - {event['file_path']}")
        print()
        print(f"  {RED}This has been logged to:{RESET} {self.audit_log_path}")
        print()
        print(f"  {BOLD}How to avoid this warning:{RESET}")
        print(f"  Use the vibey CLI to modify roadmap files:")
        print()
        print(f"    {CYAN}vibey roadmap start <task-slug>{RESET}    - Start a task")
        print(f"    {CYAN}vibey roadmap complete <task-slug>{RESET} - Complete a task")
        print(f"    {CYAN}vibey roadmap update task <id> --status <status>{RESET}")
        print()
        print(f"  Or verify changes manually:")
        print(f"    {CYAN}vibey roadmap verify <file>{RESET}        - Verify a file")
        print()
        print(f"  Documentation: docs/guides/ROADMAP_CLI_REFERENCE.md")
        print()


def detect_and_log_bypass(repo_path: Path) -> int:
    """
    Detect and log any pre-commit bypass for the latest commit.

    Args:
        repo_path: Path to repository root

    Returns:
        Number of bypass events detected
    """
    detector = BypassDetector(repo_path)
    events = detector.detect_bypass()

    if events:
        detector.log_bypass_events(events)
        detector.report_bypass(events)

    return len(events)


def get_head_commit_info(repo_path: Path) -> tuple:
    """Get commit SHA and message for HEAD."""
    try:
        # Get commit SHA
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return None, None
        commit_sha = result.stdout.strip()

        # Get commit message
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "-1", "--format=%s"],
            capture_output=True, text=True
        )
        message = result.stdout.strip() if result.returncode == 0 else ""

        return commit_sha, message
    except Exception:
        return None, None


def main() -> int:
    """Clear CLI changes tracker after successful commit and detect bypass."""
    try:
        # Get repo root
        repo_path = Path.cwd()

        # Check if we're in a Vibey project
        if not (repo_path / ".vibey").exists():
            return 0

        # Clear CLI changes tracker
        try:
            from vibey.operations.git.cli_change_tracker import clear_cli_changes
            clear_cli_changes(repo_path)
        except ImportError:
            pass  # Tracker not available

        # Detect bypass
        detect_and_log_bypass(repo_path)

        # Session tracking: Associate commit with active session
        try:
            from vibey.operations.roadmap.hooks.session_hooks import on_post_commit
            commit_sha, message = get_head_commit_info(repo_path)
            if commit_sha:
                on_post_commit(repo_path, commit_sha, message)
        except ImportError:
            pass  # Session hooks not available
        except Exception as e:
            # Don't fail commit for session tracking errors
            print(f"Warning: Session tracking error: {e}", file=sys.stderr)

        return 0

    except Exception as e:
        # Don't fail on errors in post-commit
        print(f"Warning: Post-commit hook error: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
