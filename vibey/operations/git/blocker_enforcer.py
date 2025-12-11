"""
Blocker enforcement for git operations.

This module provides:
- Roadmap blocker checking in git workflows
- Pre-commit hook integration for blocked items
- PR merge blocking for blocked tasks
- Blocker status visualization
- Enforcement mode configuration (advisory, blocking, audit)
"""

import subprocess
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


class EnforcementMode(Enum):
    """Enforcement mode for blocker checking."""
    OFF = "off"           # No blocker checking
    ADVISORY = "advisory"  # Show warnings only
    BLOCKING = "blocking"  # Prevent operations on blocked items
    AUDIT = "audit"        # Log attempts, don't block


@dataclass
class BlockerInfo:
    """Information about a single blocker."""
    blocker_id: str          # ID of the blocking item
    blocker_type: str        # 'task', 'sprint', 'track'
    blocker_name: str        # Human-readable name
    blocker_status: str      # Current status of the blocker
    required_status: str     # Status required to unblock
    blocking_since: Optional[datetime] = None


@dataclass
class BlockedItem:
    """An item that is blocked from operations."""
    item_id: str             # ID of the blocked item
    item_type: str           # 'task', 'sprint', 'track'
    item_name: str           # Human-readable name
    blockers: List[BlockerInfo] = field(default_factory=list)
    file_path: Optional[str] = None


@dataclass
class BlockerViolation:
    """A blocker violation detected during git operation."""
    item_id: str
    item_type: str
    operation: str           # 'commit', 'pr_create', 'pr_merge', 'branch_create'
    blockers: List[BlockerInfo]
    severity: str            # 'error', 'warning'
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EnforcementResult:
    """Result of blocker enforcement check."""
    allowed: bool
    mode: EnforcementMode
    violations: List[BlockerViolation]
    warnings: List[str]
    audit_log: Optional[str] = None


@dataclass
class BlockerStatus:
    """Overall blocker status for display."""
    blocked_tasks: List[BlockedItem]
    blocked_sprints: List[BlockedItem]
    blocked_tracks: List[BlockedItem]
    total_blocked: int
    checked_at: datetime


class BlockerEnforcer:
    """
    Enforce roadmap blockers in git operations.

    Prevents work on blocked items by checking blocker status
    during commits, PR creation, and merges.
    """

    def __init__(self, repo_path: str = ".", mode: EnforcementMode = EnforcementMode.ADVISORY):
        self.repo_path = Path(repo_path)
        self.roadmap_root = self.repo_path / ".vibey" / "roadmap"
        self.mode = mode
        self.audit_log_path = self.repo_path / ".vibey" / "audit" / "blocker_enforcement.log"

    def _run_git(self, args: List[str], check: bool = True) -> Tuple[bool, str, str]:
        """
        Run a git command and return (success, stdout, stderr).
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return False, e.stdout, e.stderr

    def _load_yaml_file(self, file_path: Path) -> Optional[dict]:
        """Load and parse a YAML file."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception:
            pass
        return None

    def _get_task_blockers(self, task_path: Path) -> List[BlockerInfo]:
        """
        Get blockers for a task from its task.yaml file.
        """
        data = self._load_yaml_file(task_path)
        if not data or 'task' not in data:
            return []

        task = data['task']
        blockers = []

        # Check blocked_by field
        for blocker in task.get('blocked_by', []):
            if isinstance(blocker, str):
                # Simple string blocker (task ID)
                blockers.append(BlockerInfo(
                    blocker_id=blocker,
                    blocker_type='task',
                    blocker_name=blocker,
                    blocker_status='unknown',
                    required_status='completed'
                ))
            elif isinstance(blocker, dict):
                # Structured blocker
                blockers.append(BlockerInfo(
                    blocker_id=blocker.get('dependency_id', blocker.get('target_id', '')),
                    blocker_type=blocker.get('dependency_type', 'task'),
                    blocker_name=blocker.get('dependency_id', blocker.get('target_id', '')),
                    blocker_status=blocker.get('current_status', 'unknown'),
                    required_status=blocker.get('required_status', 'completed'),
                    blocking_since=self._parse_datetime(blocker.get('blocking_since'))
                ))

        return blockers

    def _get_sprint_blockers(self, sprint_path: Path) -> List[BlockerInfo]:
        """
        Get blockers for a sprint from its sprint.yaml file.
        """
        data = self._load_yaml_file(sprint_path)
        if not data or 'sprint' not in data:
            return []

        sprint = data['sprint']
        blockers = []

        for blocker in sprint.get('blocked_by', []):
            if isinstance(blocker, str):
                blockers.append(BlockerInfo(
                    blocker_id=blocker,
                    blocker_type='sprint',
                    blocker_name=blocker,
                    blocker_status='unknown',
                    required_status='completed'
                ))
            elif isinstance(blocker, dict):
                blockers.append(BlockerInfo(
                    blocker_id=blocker.get('dependency_id', ''),
                    blocker_type=blocker.get('dependency_type', 'sprint'),
                    blocker_name=blocker.get('dependency_id', ''),
                    blocker_status=blocker.get('current_status', 'unknown'),
                    required_status=blocker.get('required_status', 'completed'),
                    blocking_since=self._parse_datetime(blocker.get('blocking_since'))
                ))

        return blockers

    def _get_track_blockers(self, track_path: Path) -> List[BlockerInfo]:
        """
        Get blockers for a track from its track.yaml file.
        """
        data = self._load_yaml_file(track_path)
        if not data or 'track' not in data:
            return []

        track = data['track']
        blockers = []

        for blocker in track.get('blocked_by', []):
            if isinstance(blocker, str):
                blockers.append(BlockerInfo(
                    blocker_id=blocker,
                    blocker_type='track',
                    blocker_name=blocker,
                    blocker_status='unknown',
                    required_status='completed'
                ))
            elif isinstance(blocker, dict):
                blockers.append(BlockerInfo(
                    blocker_id=blocker.get('dependency_id', ''),
                    blocker_type=blocker.get('dependency_type', 'track'),
                    blocker_name=blocker.get('dependency_id', ''),
                    blocker_status=blocker.get('current_status', 'unknown'),
                    required_status=blocker.get('required_status', 'completed'),
                    blocking_since=self._parse_datetime(blocker.get('blocking_since'))
                ))

        return blockers

    def _parse_datetime(self, value) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except Exception:
            return None

    def _is_blocker_resolved(self, blocker: BlockerInfo) -> bool:
        """
        Check if a blocker has been resolved.

        Looks up the actual status of the blocking item and compares
        to the required status.
        """
        # Find the blocking item
        item_path = self._find_item_path(blocker.blocker_id, blocker.blocker_type)
        if not item_path:
            # Can't find blocker - assume unresolved for safety
            return False

        data = self._load_yaml_file(item_path)
        if not data:
            return False

        # Get current status
        if blocker.blocker_type == 'task' and 'task' in data:
            current_status = data['task'].get('status', 'not_started')
        elif blocker.blocker_type == 'sprint' and 'sprint' in data:
            current_status = data['sprint'].get('status', 'not_started')
        elif blocker.blocker_type == 'track' and 'track' in data:
            current_status = data['track'].get('status', 'not_started')
        else:
            return False

        # Check if required status is met
        return current_status == blocker.required_status

    def _find_item_path(self, item_id: str, item_type: str) -> Optional[Path]:
        """
        Find the YAML file path for an item by ID.

        Uses flat structure:
        - tasks/{task_id}.yaml
        - sprints/{sprint_id}.yaml
        - tracks/{track_id}.yaml
        """
        if item_type == 'task':
            task_file = self.roadmap_root / "tasks" / f"{item_id}.yaml"
            if task_file.exists():
                return task_file
        elif item_type == 'sprint':
            sprint_file = self.roadmap_root / "sprints" / f"{item_id}.yaml"
            if sprint_file.exists():
                return sprint_file
        elif item_type == 'track':
            track_file = self.roadmap_root / "tracks" / f"{item_id}.yaml"
            if track_file.exists():
                return track_file

        return None

    def _extract_task_ids_from_commit_msg(self, commit_msg: str) -> Set[str]:
        """
        Extract task IDs referenced in a commit message.

        Looks for patterns like:
        - Task: task-id
        - [task-id]
        - Completes task-id
        - Fixes task-id
        """
        import re

        task_ids = set()

        # Pattern: Task: task-id or task-id (at start of line)
        task_patterns = [
            r'Task:\s*(\S+-task-\d+)',
            r'\[(\S+-task-\d+)\]',
            r'(?:Completes?|Fixes?|Closes?)\s+(\S+-task-\d+)',
            r'^\s*(\S+-task-\d+)',
        ]

        for pattern in task_patterns:
            matches = re.findall(pattern, commit_msg, re.MULTILINE | re.IGNORECASE)
            task_ids.update(matches)

        return task_ids

    def _extract_task_ids_from_staged_files(self) -> Set[str]:
        """
        Extract task IDs from staged roadmap files.

        Returns task IDs for any task.yaml files that are staged.
        """
        task_ids = set()

        success, stdout, _ = self._run_git(['diff', '--cached', '--name-only'], check=False)
        if not success:
            return task_ids

        for line in stdout.strip().split('\n'):
            if not line:
                continue

            path = Path(line)

            # Check if it's a task.yaml file
            if path.name == 'task.yaml' and '.vibey/roadmap' in str(path):
                # Extract task ID from path
                # .vibey/roadmap/track/sprint/task-id/task.yaml
                parts = path.parts
                if len(parts) >= 5:
                    task_id = parts[-2]  # task-id directory name
                    task_ids.add(task_id)

        return task_ids

    def check_commit(self, commit_msg: str = "") -> EnforcementResult:
        """
        Check if a commit is allowed based on blocker status.

        Called during pre-commit hook to prevent commits that
        work on blocked items.

        Args:
            commit_msg: Commit message (may be empty for pre-commit)

        Returns:
            EnforcementResult with allowed status and violations
        """
        if self.mode == EnforcementMode.OFF:
            return EnforcementResult(
                allowed=True,
                mode=self.mode,
                violations=[],
                warnings=[]
            )

        violations = []
        warnings = []

        # Get task IDs from commit message and staged files
        task_ids = self._extract_task_ids_from_commit_msg(commit_msg)
        task_ids.update(self._extract_task_ids_from_staged_files())

        # Check each task for blockers
        for task_id in task_ids:
            task_path = self._find_item_path(task_id, 'task')
            if not task_path:
                continue

            blockers = self._get_task_blockers(task_path)
            unresolved = [b for b in blockers if not self._is_blocker_resolved(b)]

            if unresolved:
                violation = BlockerViolation(
                    item_id=task_id,
                    item_type='task',
                    operation='commit',
                    blockers=unresolved,
                    severity='error' if self.mode == EnforcementMode.BLOCKING else 'warning',
                    message=self._format_violation_message(task_id, unresolved)
                )
                violations.append(violation)

        # Determine if allowed
        if self.mode == EnforcementMode.BLOCKING:
            allowed = len(violations) == 0
        else:
            allowed = True
            warnings = [v.message for v in violations]

        # Log for audit mode
        audit_log = None
        if self.mode == EnforcementMode.AUDIT and violations:
            audit_log = self._log_audit(violations, 'commit')

        return EnforcementResult(
            allowed=allowed,
            mode=self.mode,
            violations=violations,
            warnings=warnings,
            audit_log=audit_log
        )

    def check_pr_create(self, branch_name: str, task_ids: Optional[List[str]] = None) -> EnforcementResult:
        """
        Check if PR creation is allowed for the given branch.

        Args:
            branch_name: Name of the PR branch
            task_ids: Optional list of task IDs associated with PR

        Returns:
            EnforcementResult
        """
        if self.mode == EnforcementMode.OFF:
            return EnforcementResult(
                allowed=True,
                mode=self.mode,
                violations=[],
                warnings=[]
            )

        violations = []
        warnings = []

        # Extract task IDs from branch name if not provided
        if task_ids is None:
            task_ids = list(self._extract_task_ids_from_commit_msg(branch_name))

        for task_id in task_ids:
            task_path = self._find_item_path(task_id, 'task')
            if not task_path:
                continue

            blockers = self._get_task_blockers(task_path)
            unresolved = [b for b in blockers if not self._is_blocker_resolved(b)]

            if unresolved:
                violation = BlockerViolation(
                    item_id=task_id,
                    item_type='task',
                    operation='pr_create',
                    blockers=unresolved,
                    severity='error' if self.mode == EnforcementMode.BLOCKING else 'warning',
                    message=self._format_violation_message(task_id, unresolved)
                )
                violations.append(violation)

        allowed = len(violations) == 0 if self.mode == EnforcementMode.BLOCKING else True

        if self.mode == EnforcementMode.AUDIT and violations:
            self._log_audit(violations, 'pr_create')

        return EnforcementResult(
            allowed=allowed,
            mode=self.mode,
            violations=violations,
            warnings=[v.message for v in violations] if self.mode != EnforcementMode.BLOCKING else []
        )

    def check_pr_merge(self, pr_branch: str, target_branch: str = 'main') -> EnforcementResult:
        """
        Check if PR merge is allowed based on blocker status.

        Args:
            pr_branch: PR source branch
            target_branch: Target branch for merge

        Returns:
            EnforcementResult
        """
        if self.mode == EnforcementMode.OFF:
            return EnforcementResult(
                allowed=True,
                mode=self.mode,
                violations=[],
                warnings=[]
            )

        violations = []

        # Get task IDs from branch name and commits
        task_ids = self._extract_task_ids_from_commit_msg(pr_branch)

        # Also check commits in the PR
        success, stdout, _ = self._run_git(
            ['log', f'{target_branch}..{pr_branch}', '--format=%s'],
            check=False
        )
        if success:
            for line in stdout.strip().split('\n'):
                task_ids.update(self._extract_task_ids_from_commit_msg(line))

        for task_id in task_ids:
            task_path = self._find_item_path(task_id, 'task')
            if not task_path:
                continue

            blockers = self._get_task_blockers(task_path)
            unresolved = [b for b in blockers if not self._is_blocker_resolved(b)]

            if unresolved:
                violation = BlockerViolation(
                    item_id=task_id,
                    item_type='task',
                    operation='pr_merge',
                    blockers=unresolved,
                    severity='error' if self.mode == EnforcementMode.BLOCKING else 'warning',
                    message=self._format_violation_message(task_id, unresolved)
                )
                violations.append(violation)

        allowed = len(violations) == 0 if self.mode == EnforcementMode.BLOCKING else True

        if self.mode == EnforcementMode.AUDIT and violations:
            self._log_audit(violations, 'pr_merge')

        return EnforcementResult(
            allowed=allowed,
            mode=self.mode,
            violations=violations,
            warnings=[v.message for v in violations] if self.mode != EnforcementMode.BLOCKING else []
        )

    def get_blocker_status(self) -> BlockerStatus:
        """
        Get overall blocker status for the roadmap.

        Returns:
            BlockerStatus with all blocked items
        """
        blocked_tasks = []
        blocked_sprints = []
        blocked_tracks = []

        # Find all task.yaml files
        for task_file in self.roadmap_root.glob("**/task.yaml"):
            data = self._load_yaml_file(task_file)
            if not data or 'task' not in data:
                continue

            task = data['task']
            task_id = task.get('id', '')

            # Check if blocked
            if task.get('blocked', False):
                blockers = self._get_task_blockers(task_file)
                blocked_tasks.append(BlockedItem(
                    item_id=task_id,
                    item_type='task',
                    item_name=task.get('title', task.get('name', task_id)),
                    blockers=blockers,
                    file_path=str(task_file)
                ))

        # Find all sprint.yaml files
        for sprint_file in self.roadmap_root.glob("**/sprint.yaml"):
            data = self._load_yaml_file(sprint_file)
            if not data or 'sprint' not in data:
                continue

            sprint = data['sprint']
            sprint_id = sprint.get('id', '')

            if sprint.get('blocked', False):
                blockers = self._get_sprint_blockers(sprint_file)
                blocked_sprints.append(BlockedItem(
                    item_id=sprint_id,
                    item_type='sprint',
                    item_name=sprint.get('name', sprint_id),
                    blockers=blockers,
                    file_path=str(sprint_file)
                ))

        # Find all track.yaml files
        for track_file in self.roadmap_root.glob("*/track.yaml"):
            data = self._load_yaml_file(track_file)
            if not data or 'track' not in data:
                continue

            track = data['track']
            track_id = track.get('id', '')

            if track.get('blocked', False):
                blockers = self._get_track_blockers(track_file)
                blocked_tracks.append(BlockedItem(
                    item_id=track_id,
                    item_type='track',
                    item_name=track.get('name', track_id),
                    blockers=blockers,
                    file_path=str(track_file)
                ))

        return BlockerStatus(
            blocked_tasks=blocked_tasks,
            blocked_sprints=blocked_sprints,
            blocked_tracks=blocked_tracks,
            total_blocked=len(blocked_tasks) + len(blocked_sprints) + len(blocked_tracks),
            checked_at=datetime.now(timezone.utc)
        )

    def _format_violation_message(self, item_id: str, blockers: List[BlockerInfo]) -> str:
        """Format a human-readable violation message."""
        blocker_strs = [
            f"  - {b.blocker_id} ({b.blocker_type}, needs: {b.required_status})"
            for b in blockers
        ]
        return f"Task {item_id} is blocked by:\n" + "\n".join(blocker_strs)

    def _log_audit(self, violations: List[BlockerViolation], operation: str) -> str:
        """
        Log violations to audit file.

        Returns:
            Path to audit log
        """
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Blocker Enforcement Audit\n")
                f.write(f"Operation: {operation}\n")
                f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"Mode: {self.mode.value}\n")
                f.write(f"Violations: {len(violations)}\n")
                for v in violations:
                    f.write(f"\n  Item: {v.item_id} ({v.item_type})\n")
                    f.write(f"  Blockers:\n")
                    for b in v.blockers:
                        f.write(f"    - {b.blocker_id}: {b.blocker_status} (needs {b.required_status})\n")
                f.write(f"{'='*80}\n")

            return str(self.audit_log_path)
        except Exception:
            return ""


# Convenience functions

def check_commit_blockers(commit_msg: str = "", repo_path: str = ".",
                         mode: EnforcementMode = EnforcementMode.ADVISORY) -> EnforcementResult:
    """
    Check if a commit is allowed based on blocker status.

    Args:
        commit_msg: Commit message
        repo_path: Path to repository
        mode: Enforcement mode

    Returns:
        EnforcementResult
    """
    enforcer = BlockerEnforcer(repo_path, mode)
    return enforcer.check_commit(commit_msg)


def get_blocker_status(repo_path: str = ".") -> BlockerStatus:
    """
    Get overall blocker status for the roadmap.

    Args:
        repo_path: Path to repository

    Returns:
        BlockerStatus
    """
    enforcer = BlockerEnforcer(repo_path)
    return enforcer.get_blocker_status()


def format_blocker_status(status: BlockerStatus) -> str:
    """
    Format blocker status for display.

    Args:
        status: BlockerStatus to format

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Blocker Status Report")
    lines.append(f"Checked at: {status.checked_at.isoformat()}")
    lines.append("=" * 60)
    lines.append("")

    if status.total_blocked == 0:
        lines.append("✅ No blocked items found")
    else:
        lines.append(f"⚠️  {status.total_blocked} blocked item(s) found")
        lines.append("")

        if status.blocked_tracks:
            lines.append("🔴 Blocked Tracks:")
            for item in status.blocked_tracks:
                lines.append(f"  - {item.item_id}: {item.item_name}")
                for b in item.blockers:
                    lines.append(f"      Blocked by: {b.blocker_id} (needs {b.required_status})")
            lines.append("")

        if status.blocked_sprints:
            lines.append("🟠 Blocked Sprints:")
            for item in status.blocked_sprints:
                lines.append(f"  - {item.item_id}: {item.item_name}")
                for b in item.blockers:
                    lines.append(f"      Blocked by: {b.blocker_id} (needs {b.required_status})")
            lines.append("")

        if status.blocked_tasks:
            lines.append("🟡 Blocked Tasks:")
            for item in status.blocked_tasks:
                lines.append(f"  - {item.item_id}: {item.item_name}")
                for b in item.blockers:
                    lines.append(f"      Blocked by: {b.blocker_id} (needs {b.required_status})")

    return "\n".join(lines)
