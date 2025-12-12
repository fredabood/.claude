"""
Pre-push Hook Implementation

Verifies all commits being pushed have valid activity log entries
for any roadmap file changes.

Task: git-integration-5-task-006
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import yaml


@dataclass
class CommitVerification:
    """Result of verifying a single commit."""
    commit_hash: str
    verified: bool
    roadmap_files: List[str]
    unverified_files: List[str]
    error: Optional[str] = None


@dataclass
class PushRef:
    """A ref being pushed."""
    local_ref: str
    local_sha: str
    remote_ref: str
    remote_sha: str


class PrePushHook:
    """
    Pre-push hook for Vibey roadmap verification.

    Verifies all commits being pushed have valid activity log entries
    for any roadmap file modifications.
    """

    # Terminal colors
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Zero SHA indicates new branch or deleted ref
    ZERO_SHA = "0" * 40

    def __init__(self, repo_path: str = "."):
        """
        Initialize pre-push hook.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load hook configuration from .vibey/config/git.yaml."""
        config_path = self.repo_path / ".vibey" / "config" / "git.yaml"

        if not config_path.exists():
            return {"mode": "advisory"}

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            git_config = data.get("git", {})
            enforcement = git_config.get("enforcement", {})
            return {
                "mode": enforcement.get("mode", "advisory"),
                "pre_push": enforcement.get("pre_push", {}),
            }
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {"mode": "advisory"}

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _parse_stdin(self, stdin_data: str) -> List[PushRef]:
        """
        Parse refs from pre-push hook stdin.

        Format: <local ref> <local sha1> <remote ref> <remote sha1>

        Args:
            stdin_data: Raw stdin data

        Returns:
            List of PushRef objects
        """
        refs = []
        for line in stdin_data.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                refs.append(PushRef(
                    local_ref=parts[0],
                    local_sha=parts[1],
                    remote_ref=parts[2],
                    remote_sha=parts[3],
                ))
        return refs

    def _get_commits_in_range(self, base_sha: str, head_sha: str) -> List[str]:
        """
        Get list of commits in range.

        Args:
            base_sha: Starting commit (exclusive)
            head_sha: Ending commit (inclusive)

        Returns:
            List of commit hashes
        """
        if base_sha == self.ZERO_SHA:
            # New branch - get all commits reachable from head
            # that aren't in any other remote-tracking branch
            result = self._run_git(
                "log", "--format=%H",
                head_sha,
                "--not", "--remotes",
            )
        else:
            # Existing branch - get commits in range
            result = self._run_git(
                "log", "--format=%H",
                f"{base_sha}..{head_sha}",
            )

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

    def _verify_commit(self, commit_hash: str) -> CommitVerification:
        """
        Verify a single commit has activity log entries for roadmap changes.

        Args:
            commit_hash: Git commit hash

        Returns:
            CommitVerification result
        """
        roadmap_files = self._get_roadmap_files_in_commit(commit_hash)

        if not roadmap_files:
            return CommitVerification(
                commit_hash=commit_hash,
                verified=True,
                roadmap_files=[],
                unverified_files=[],
            )

        # Import verification module
        try:
            from vibey.operations.roadmap.verification import ChangeVerifier
            from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader
            from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        except ImportError as e:
            return CommitVerification(
                commit_hash=commit_hash,
                verified=False,
                roadmap_files=roadmap_files,
                unverified_files=roadmap_files,
                error=f"Verification module not available: {e}",
            )

        # Build hash index for fast lookups
        fs = FileSystemManager(self.repo_path)
        reader = ActivityLogReader(fs.roadmap_root / "activity_log")
        hash_index = reader.build_hash_index()

        unverified_files = []
        for file_path in roadmap_files:
            # Get the file's hash at this commit
            file_hash = self._get_file_hash_at_commit(commit_hash, file_path)

            if file_hash is None:
                # File was deleted - allow this
                continue

            # Check if hash is in activity log
            if file_hash not in hash_index:
                unverified_files.append(file_path)

        return CommitVerification(
            commit_hash=commit_hash,
            verified=len(unverified_files) == 0,
            roadmap_files=roadmap_files,
            unverified_files=unverified_files,
        )

    def _verify_push_refs(self, refs: List[PushRef]) -> List[CommitVerification]:
        """
        Verify all commits being pushed.

        Args:
            refs: List of push refs

        Returns:
            List of verification results
        """
        results = []

        for ref in refs:
            # Skip deleted refs
            if ref.local_sha == self.ZERO_SHA:
                continue

            commits = self._get_commits_in_range(ref.remote_sha, ref.local_sha)

            for commit_hash in commits:
                result = self._verify_commit(commit_hash)
                results.append(result)

        return results

    def _format_results(self, results: List[CommitVerification]) -> str:
        """Format verification results for display."""
        lines = []

        for result in results:
            if result.error:
                lines.append(
                    f"  {self.YELLOW}⚠{self.RESET} {result.commit_hash[:8]}: "
                    f"{result.error}"
                )
            elif not result.verified:
                lines.append(
                    f"  {self.RED}✗{self.RESET} {result.commit_hash[:8]}: "
                    f"Unverified files:"
                )
                for f in result.unverified_files:
                    lines.append(f"      - {f}")

        return "\n".join(lines)

    def run(self, stdin_data: str = "") -> int:
        """
        Run pre-push verification.

        Args:
            stdin_data: Data from stdin (push refs)

        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        # Check if hook is disabled
        if self.config.get("mode") == "off":
            return 0

        # Session tracking: Warn about active session (advisory only)
        try:
            from vibey.operations.roadmap.hooks.session_hooks import (
                on_pre_push,
                print_active_session_warning,
            )
            session_info = on_pre_push(self.repo_path)
            if session_info:
                print_active_session_warning(session_info)
        except ImportError:
            pass  # Session hooks not available
        except Exception as e:
            # Don't fail push for session tracking errors
            print(f"Warning: Session check error: {e}", file=sys.stderr)

        # Parse refs from stdin
        if not stdin_data:
            stdin_data = sys.stdin.read()

        refs = self._parse_stdin(stdin_data)

        if not refs:
            return 0

        # Verify all commits
        results = self._verify_push_refs(refs)

        # Check for failures
        failed = [r for r in results if not r.verified]

        if not failed:
            print(f"\n{self.GREEN}[vibey] Pre-push:{self.RESET} ✓ All commits verified\n")
            return 0

        # Determine if we should block
        mode = self.config.get("mode", "advisory")
        should_block = mode == "blocking"

        # Display results
        mode_display = {
            "advisory": f"{self.YELLOW}Advisory{self.RESET}",
            "blocking": f"{self.RED}Blocking{self.RESET}",
            "audit": f"{self.BLUE}Audit{self.RESET}",
        }.get(mode, mode)

        print(f"\n{self.BOLD}[vibey] Pre-push {mode_display}:{self.RESET}")
        print(self._format_results(failed))

        print()
        if should_block:
            print(
                f"{self.RED}Push blocked.{self.RESET} "
                f"Use 'vibey roadmap' CLI to make changes.\n"
            )
            print(
                f"To force push: git push --no-verify"
            )
            print()
            return 1
        else:
            print(
                f"{self.YELLOW}Warning:{self.RESET} Some commits contain unverified "
                f"roadmap changes.\n"
            )
            return 0


def main() -> int:
    """Main entry point for pre-push hook."""
    try:
        hook = PrePushHook()
        return hook.run()
    except Exception as e:
        print(f"Error running pre-push hook: {e}", file=sys.stderr)
        # Don't block on hook errors (fail open)
        return 0


if __name__ == "__main__":
    sys.exit(main())
