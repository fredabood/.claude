"""
Branch-to-Task Linking System

Links Git branches to roadmap tasks/sprints/tracks.

Task: git-integration-2-task-005
"""

import yaml
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class BranchType(Enum):
    """Type of branch."""
    TASK = "task"
    SPRINT = "sprint"
    TRACK = "track"
    OTHER = "other"


@dataclass
class BranchInfo:
    """Information about a Git branch."""
    name: str
    branch_type: BranchType
    item_id: Optional[str]
    current: bool
    exists: bool
    merged: bool = False
    merge_commit: Optional[str] = None


@dataclass
class BranchLinkInfo:
    """Information about a branch-task link."""
    task_id: str
    branch_name: str
    created: Optional[str]
    merged: Optional[bool]
    merge_commit: Optional[str]
    current: bool
    exists: bool


class BranchLinker:
    """
    Link Git branches to roadmap tasks/sprints/tracks.

    Supports branch naming conventions:
    - task/<task-id>
    - sprint/<sprint-id>
    - track/<track-id>
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize branch linker.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.roadmap_dir = self.repo_path / ".vibey" / "roadmap"

    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def parse_branch_name(self, branch_name: str) -> Tuple[BranchType, Optional[str]]:
        """
        Parse branch name to extract type and item ID.

        Args:
            branch_name: Branch name (e.g., "task/git-integration-2-task-001")

        Returns:
            Tuple of (branch_type, item_id)
        """
        if "/" not in branch_name:
            return BranchType.OTHER, None

        parts = branch_name.split("/", 1)
        prefix = parts[0].lower()
        item_id = parts[1] if len(parts) > 1 else None

        if prefix == "task":
            return BranchType.TASK, item_id
        elif prefix == "sprint":
            return BranchType.SPRINT, item_id
        elif prefix == "track":
            return BranchType.TRACK, item_id
        else:
            return BranchType.OTHER, None

    def get_current_branch(self) -> Optional[str]:
        """
        Get the current branch name.

        Returns:
            Current branch name, or None if not on a branch
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            return branch if branch != "HEAD" else None
        except subprocess.CalledProcessError:
            return None

    def get_all_branches(self, include_remote: bool = False) -> List[str]:
        """
        Get all branch names.

        Args:
            include_remote: Include remote branches

        Returns:
            List of branch names
        """
        try:
            cmd = ["git", "branch"]
            if include_remote:
                cmd.append("-a")

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            branches = []
            for line in result.stdout.splitlines():
                # Remove leading * and whitespace
                branch = line.strip().lstrip("* ")
                if branch and not branch.startswith("remotes/origin/HEAD"):
                    # Clean up remote branch names
                    if branch.startswith("remotes/origin/"):
                        branch = branch.replace("remotes/origin/", "")
                    branches.append(branch)

            return branches

        except subprocess.CalledProcessError:
            return []

    def branch_exists(self, branch_name: str) -> bool:
        """
        Check if a branch exists.

        Args:
            branch_name: Branch name

        Returns:
            True if branch exists
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def is_branch_merged(self, branch_name: str, target_branch: str = "main") -> bool:
        """
        Check if a branch has been merged.

        Args:
            branch_name: Branch to check
            target_branch: Target branch (default: main)

        Returns:
            True if merged
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--merged", target_branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            merged_branches = [b.strip().lstrip("* ") for b in result.stdout.splitlines()]
            return branch_name in merged_branches

        except subprocess.CalledProcessError:
            return False

    def create_branch(self, branch_name: str, start_point: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Create a new branch.

        Args:
            branch_name: Name of branch to create
            start_point: Starting point (branch/commit), defaults to HEAD

        Returns:
            Tuple of (success, error_message)
        """
        try:
            cmd = ["git", "checkout", "-b", branch_name]
            if start_point:
                cmd.append(start_point)

            subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            return True, None

        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

    def find_task_file(self, task_id: str) -> Optional[Path]:
        """
        Find the YAML file for a specific task.

        First checks standalone task files (tasks/*.yaml), then falls back
        to searching legacy sprint files with embedded tasks.

        Args:
            task_id: Task ID to search for

        Returns:
            Path to task.yaml file (standalone) or sprint.yaml (legacy), or None
        """
        if not self.roadmap_dir.exists():
            return None

        # First: Check for standalone task file (flat structure)
        tasks_dir = self.roadmap_dir / "tasks"
        if tasks_dir.exists():
            # Direct lookup for ULID-based task IDs
            task_file = tasks_dir / f"{task_id}.yaml"
            if task_file.exists():
                return task_file

            # Search all task files for slug-based IDs
            for task_file in tasks_dir.glob("*.yaml"):
                try:
                    with open(task_file) as f:
                        data = yaml.safe_load(f)
                    task_data = data.get("task", {})
                    if task_data.get("id") == task_id or task_data.get("slug") == task_id:
                        return task_file
                except Exception:
                    continue

        # Fallback: Search legacy sprint.yaml files with embedded tasks (DEPRECATED)
        for sprint_file in self.roadmap_dir.rglob("sprint.yaml"):
            try:
                with open(sprint_file) as f:
                    data = yaml.safe_load(f)

                sprint = data.get("sprint", {})
                tasks = sprint.get("tasks", [])

                for task in tasks:
                    if task.get("id") == task_id:
                        return sprint_file

            except Exception:
                continue

        return None

    def link_branch_to_task(
        self,
        task_id: str,
        branch_name: str,
        dry_run: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Link a branch to a task in roadmap YAML.

        Handles both standalone task files (task: {}) and legacy sprint files
        with embedded tasks (sprint: {tasks: []}).

        Args:
            task_id: Task ID
            branch_name: Branch name
            dry_run: If True, don't actually write changes

        Returns:
            Tuple of (success, error_message)
        """
        # Find task file
        task_file = self.find_task_file(task_id)

        if not task_file:
            return False, f"Task {task_id} not found in roadmap"

        try:
            with open(task_file) as f:
                data = yaml.safe_load(f)

            # Determine file format: standalone task vs legacy sprint
            task = None
            if "task" in data:
                # Standalone task file format
                task = data["task"]
            elif "sprint" in data:
                # Legacy sprint file with embedded tasks
                sprint = data.get("sprint", {})
                tasks = sprint.get("tasks", [])
                for t in tasks:
                    if t.get("id") == task_id:
                        task = t
                        break

            if not task:
                return False, f"Task {task_id} not found in file"

            # Initialize branch metadata
            if "branch" not in task:
                task["branch"] = {}

            # Check if branch is merged
            is_merged = self.is_branch_merged(branch_name)
            merge_commit = None

            if is_merged:
                # Get merge commit
                try:
                    result = subprocess.run(
                        ["git", "log", "--merges", "--oneline", "--grep", branch_name, "-1"],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        merge_commit = result.stdout.split()[0]
                except subprocess.CalledProcessError:
                    pass

            # Update branch info
            task["branch"]["name"] = branch_name
            task["branch"]["created"] = task["branch"].get("created") or datetime.now(timezone.utc).isoformat()
            task["branch"]["merged"] = is_merged

            if merge_commit:
                task["branch"]["merge_commit"] = merge_commit

            # Write changes
            if not dry_run:
                with open(task_file, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return True, None

        except Exception as e:
            return False, str(e)

    def unlink_branch_from_task(
        self,
        task_id: str,
        dry_run: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Unlink a branch from a task.

        Handles both standalone task files (task: {}) and legacy sprint files
        with embedded tasks (sprint: {tasks: []}).

        Args:
            task_id: Task ID
            dry_run: If True, don't actually write changes

        Returns:
            Tuple of (success, error_message)
        """
        # Find task file
        task_file = self.find_task_file(task_id)

        if not task_file:
            return False, f"Task {task_id} not found in roadmap"

        try:
            with open(task_file) as f:
                data = yaml.safe_load(f)

            # Determine file format: standalone task vs legacy sprint
            task = None
            if "task" in data:
                # Standalone task file format
                task = data["task"]
            elif "sprint" in data:
                # Legacy sprint file with embedded tasks
                sprint = data.get("sprint", {})
                tasks = sprint.get("tasks", [])
                for t in tasks:
                    if t.get("id") == task_id:
                        task = t
                        break

            if not task:
                return False, f"Task {task_id} not found in file"

            # Remove branch metadata
            if "branch" in task:
                del task["branch"]

            # Write changes
            if not dry_run:
                with open(task_file, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return True, None

        except Exception as e:
            return False, str(e)

    def get_task_branch(self, task_id: str) -> Optional[BranchLinkInfo]:
        """
        Get branch information for a task.

        Handles both standalone task files (task: {}) and legacy sprint files
        with embedded tasks (sprint: {tasks: []}).

        Args:
            task_id: Task ID

        Returns:
            BranchLinkInfo or None
        """
        task_file = self.find_task_file(task_id)

        if not task_file:
            return None

        try:
            with open(task_file) as f:
                data = yaml.safe_load(f)

            # Determine file format: standalone task vs legacy sprint
            task = None
            if "task" in data:
                # Standalone task file format
                task = data["task"]
            elif "sprint" in data:
                # Legacy sprint file with embedded tasks
                sprint = data.get("sprint", {})
                tasks = sprint.get("tasks", [])
                for t in tasks:
                    if t.get("id") == task_id:
                        task = t
                        break

            if not task:
                return None

            branch_info = task.get("branch")

            if not branch_info:
                return None

            branch_name = branch_info.get("name")

            if not branch_name:
                return None

            current_branch = self.get_current_branch()
            exists = self.branch_exists(branch_name)

            return BranchLinkInfo(
                task_id=task_id,
                branch_name=branch_name,
                created=branch_info.get("created"),
                merged=branch_info.get("merged"),
                merge_commit=branch_info.get("merge_commit"),
                current=(branch_name == current_branch),
                exists=exists
            )

        except Exception:
            pass

        return None

    def get_all_branch_links(self) -> List[BranchLinkInfo]:
        """
        Get all branch-task links.

        Scans both standalone task files (tasks/*.yaml) and legacy sprint files
        with embedded tasks.

        Returns:
            List of BranchLinkInfo
        """
        links = []

        if not self.roadmap_dir.exists():
            return links

        current_branch = self.get_current_branch()

        # First: Scan standalone task files (primary source)
        tasks_dir = self.roadmap_dir / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                try:
                    with open(task_file) as f:
                        data = yaml.safe_load(f)

                    task = data.get("task", {})
                    branch_info = task.get("branch")

                    if branch_info and branch_info.get("name"):
                        branch_name = branch_info["name"]
                        exists = self.branch_exists(branch_name)

                        links.append(BranchLinkInfo(
                            task_id=task["id"],
                            branch_name=branch_name,
                            created=branch_info.get("created"),
                            merged=branch_info.get("merged"),
                            merge_commit=branch_info.get("merge_commit"),
                            current=(branch_name == current_branch),
                            exists=exists
                        ))

                except Exception:
                    continue

        # Second: Also scan legacy sprint.yaml files with embedded tasks (DEPRECATED)
        for sprint_file in self.roadmap_dir.rglob("sprint.yaml"):
            try:
                with open(sprint_file) as f:
                    data = yaml.safe_load(f)

                sprint = data.get("sprint", {})
                tasks = sprint.get("tasks", [])

                for task in tasks:
                    branch_info = task.get("branch")

                    if branch_info and branch_info.get("name"):
                        branch_name = branch_info["name"]
                        exists = self.branch_exists(branch_name)

                        links.append(BranchLinkInfo(
                            task_id=task["id"],
                            branch_name=branch_name,
                            created=branch_info.get("created"),
                            merged=branch_info.get("merged"),
                            merge_commit=branch_info.get("merge_commit"),
                            current=(branch_name == current_branch),
                            exists=exists
                        ))

            except Exception:
                continue

        return links

    def suggest_branch_name(self, task_id: str) -> str:
        """
        Suggest a branch name for a task.

        Args:
            task_id: Task ID

        Returns:
            Suggested branch name
        """
        # Default format: task/<task-id>
        return f"task/{task_id}"


def create_task_branch(
    task_id: str,
    repo_path: str = ".",
    start_point: Optional[str] = None,
    link: bool = True,
    dry_run: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Convenience function to create a branch for a task.

    Args:
        task_id: Task ID
        repo_path: Repository path
        start_point: Starting point for branch
        link: If True, link branch to task in YAML
        dry_run: If True, don't actually create branch

    Returns:
        Tuple of (success, branch_name, error_message)
    """
    linker = BranchLinker(repo_path)

    branch_name = linker.suggest_branch_name(task_id)

    if not dry_run:
        success, error = linker.create_branch(branch_name, start_point)

        if not success:
            return False, branch_name, error

        if link:
            success, error = linker.link_branch_to_task(task_id, branch_name)

            if not success:
                return False, branch_name, f"Branch created but linking failed: {error}"

    return True, branch_name, None
