"""
Commit-Msg Hook Implementation

Validates commit message format and checks task references.

Task: git-integration-2-task-002
Status: In Progress
"""

import sys
from pathlib import Path
from typing import List, Optional
import yaml

from vibey.operations.git.commit_parser import CommitParser
from vibey.operations.git.hooks.pre_commit import ValidationIssue, HookConfig


class CommitMsgHook:
    """
    Commit-msg hook for Vibey roadmap integration.

    Validates commit messages and checks that referenced tasks
    exist in the roadmap.
    """

    # Terminal colors
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, commit_msg_file: str, repo_path: str = "."):
        """
        Initialize commit-msg hook.

        Args:
            commit_msg_file: Path to commit message file (.git/COMMIT_EDITMSG)
            repo_path: Path to git repository root
        """
        self.commit_msg_file = Path(commit_msg_file)
        self.repo_path = Path(repo_path).resolve()
        self.config = self._load_config()
        self.parser = CommitParser()
        self.issues: List[ValidationIssue] = []

    def _load_config(self) -> HookConfig:
        """Load hook configuration from .vibey/config/git.yaml."""
        config_path = self.repo_path / ".vibey" / "config" / "git.yaml"

        # Default config
        if not config_path.exists():
            return HookConfig()

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            git_config = data.get("git", {})
            enforcement = git_config.get("enforcement", {})
            rules = enforcement.get("rules", {})
            audit = enforcement.get("audit", {})

            config = HookConfig(
                mode=enforcement.get("mode", "advisory"),
                audit_log=audit.get("file") if audit.get("enabled") else None,
            )

            # Add task_reference rule config
            if not hasattr(config, "task_reference"):
                config.task_reference = rules.get("task_reference", {})

            return config
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return HookConfig()

    def _read_commit_message(self) -> str:
        """
        Read the commit message from file.

        Returns:
            Commit message text
        """
        try:
            with open(self.commit_msg_file) as f:
                # Skip comment lines
                lines = []
                for line in f:
                    if not line.startswith("#"):
                        lines.append(line)
                return "".join(lines).strip()
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity="error",
                rule="commit_msg",
                message=f"Could not read commit message: {e}",
                suggestion="Ensure commit message file exists",
            ))
            return ""

    def _load_roadmap_tasks(self) -> set:
        """
        Load all task IDs from roadmap YAML files.

        Returns:
            Set of task IDs
        """
        task_ids = set()
        roadmap_dir = self.repo_path / ".vibey" / "roadmap"

        if not roadmap_dir.exists():
            return task_ids

        # Find all sprint.yaml files
        for sprint_file in roadmap_dir.rglob("sprint.yaml"):
            try:
                with open(sprint_file) as f:
                    data = yaml.safe_load(f)

                sprint = data.get("sprint", {})
                tasks = sprint.get("tasks", [])

                for task in tasks:
                    if "id" in task:
                        task_ids.add(task["id"])
            except Exception:
                # Skip files that can't be parsed
                continue

        return task_ids

    def _validate_commit_format(self, message: str) -> None:
        """
        Validate commit message format.

        Args:
            message: Commit message text
        """
        # Parse the commit message
        parsed = self.parser.parse(message)

        # Check for parse errors
        if parsed.parse_errors:
            for error in parsed.parse_errors:
                self.issues.append(ValidationIssue(
                    severity="warning",
                    rule="commit_format",
                    message=error,
                    suggestion="Follow conventional commit format: type(scope): description",
                ))

        # Check for task references (if required by config)
        task_ref_config = getattr(self.config, "task_reference", {})
        require_ref = task_ref_config.get("require_valid_id", False)

        if require_ref and not parsed.has_task_reference:
            # Determine severity based on mode
            mode = task_ref_config.get("mode") or self.config.mode
            severity = "error" if mode == "blocking" else "warning"

            self.issues.append(ValidationIssue(
                severity=severity,
                rule="task_reference",
                message="Commit does not reference a task",
                suggestion="Use format: type(task-id): description OR add 'Task: task-id' footer",
            ))

    def _validate_task_exists(self, message: str) -> None:
        """
        Validate that referenced tasks exist in roadmap.

        Args:
            message: Commit message text
        """
        # Parse task references
        parsed = self.parser.parse(message)

        if not parsed.has_task_reference:
            return

        # Load known task IDs
        known_tasks = self._load_roadmap_tasks()

        # Check each referenced task
        for task_ref in parsed.tasks:
            if task_ref.task_id not in known_tasks:
                # Try to find similar task IDs
                suggestions = self._find_similar_tasks(task_ref.task_id, known_tasks)

                suggestion_text = "Task not found in roadmap"
                if suggestions:
                    suggestion_text += f". Did you mean: {', '.join(suggestions[:3])}?"

                self.issues.append(ValidationIssue(
                    severity="warning",
                    rule="task_reference",
                    message=f"Task '{task_ref.task_id}' not found in roadmap",
                    suggestion=suggestion_text,
                ))

    def _verify_completion_claims(self, message: str) -> None:
        """
        Verify that claimed completions meet all criteria.

        When a commit message includes "Completes: task-id" or similar,
        this method verifies that the task meets all completion criteria
        using the unified ticket model's can_transition_to() validation.

        Args:
            message: Commit message text

        Reference: Sprint 6 design - func_verify_completion_claims.py
        """
        if not self.config.completion_verification.get("enabled", True):
            return

        # Parse task references
        parsed = self.parser.parse(message)

        if not parsed.has_task_reference:
            return

        # Import ticket loading and status types
        try:
            from vibey.operations.roadmap.query import load_task_ticket
            from vibey.roadmap.models.ticket import TicketStatus
            from vibey.operations.git.commit_parser_schema import TaskStatus
        except ImportError:
            # Ticket models not available, skip verification
            return

        # Find tasks claimed as completed
        completion_claims = [
            task_ref for task_ref in parsed.tasks
            if task_ref.status == TaskStatus.COMPLETED
        ]

        if not completion_claims:
            return

        # Verify each completion claim
        for task_ref in completion_claims:
            task_id = task_ref.task_id

            try:
                # Load the task ticket
                ticket = load_task_ticket(self.repo_path, task_id)

                if ticket is None:
                    self.issues.append(ValidationIssue(
                        severity="warning",
                        rule="completion_verification",
                        message=f"Cannot verify completion for '{task_id}': task not found",
                        suggestion="Ensure task ID is correct",
                    ))
                    continue

                # Check if can transition to completed
                can_complete, blockers = ticket.can_transition_to(TicketStatus.COMPLETED)

                if not can_complete and blockers:
                    # Determine severity based on mode
                    mode = self._get_rule_mode("completion_verification")
                    severity = "error" if mode == "blocking" else "warning"

                    # Format blockers for display
                    blocker_text = "; ".join(blockers[:3])
                    if len(blockers) > 3:
                        blocker_text += f" (+{len(blockers) - 3} more)"

                    self.issues.append(ValidationIssue(
                        severity=severity,
                        rule="completion_verification",
                        message=f"Cannot complete '{task_id}': {blocker_text}",
                        suggestion="Resolve blocking criteria before claiming completion",
                    ))

            except Exception as e:
                # If we can't load the ticket, add a warning but don't block
                self.issues.append(ValidationIssue(
                    severity="warning",
                    rule="completion_verification",
                    message=f"Could not verify completion for '{task_id}': {str(e)[:50]}",
                ))

    def _find_similar_tasks(self, task_id: str, known_tasks: set) -> List[str]:
        """
        Find similar task IDs using simple string matching.

        Args:
            task_id: Task ID to find matches for
            known_tasks: Set of known task IDs

        Returns:
            List of similar task IDs
        """
        # Simple prefix matching
        similar = []
        task_lower = task_id.lower()

        for known in known_tasks:
            known_lower = known.lower()
            # Check if they share a common prefix
            if (task_lower.startswith(known_lower[:5]) or
                known_lower.startswith(task_lower[:5])):
                similar.append(known)

        return sorted(similar)[:5]

    def _get_rule_mode(self, rule_name: str) -> str:
        """
        Get effective enforcement mode for a rule.

        Args:
            rule_name: Name of the rule

        Returns:
            Effective mode (off|advisory|blocking|audit)
        """
        rule_config = getattr(self.config, rule_name, {})

        # Check if rule is enabled
        if not rule_config.get("enabled", True):
            return "off"

        # Get rule-specific mode, or fall back to global mode
        return rule_config.get("mode") or self.config.mode

    def _should_block(self, issues: List[ValidationIssue]) -> bool:
        """
        Determine if any issues should block the commit.

        Args:
            issues: List of validation issues

        Returns:
            True if commit should be blocked
        """
        for issue in issues:
            rule_mode = self._get_rule_mode(issue.rule)

            # Blocking mode and error severity = block
            if rule_mode == "blocking" and issue.severity == "error":
                return True

        return False

    def _format_issue(self, issue: ValidationIssue) -> str:
        """
        Format a validation issue for display.

        Args:
            issue: Validation issue

        Returns:
            Formatted message
        """
        symbol = {
            "error": f"{self.RED}✗{self.RESET}",
            "warning": f"{self.YELLOW}⚠{self.RESET}",
            "info": f"{self.BLUE}ℹ{self.RESET}",
        }.get(issue.severity, "•")

        lines = [f"  {symbol} {issue.message}"]

        if issue.suggestion:
            lines.append(f"    {self.GREEN}Suggestion:{self.RESET} {issue.suggestion}")

        return "\n".join(lines)

    def _write_audit_log(self, message: str) -> None:
        """
        Write validation results to audit log.

        Args:
            message: Commit message that was validated
        """
        if not self.config.audit_log:
            return

        audit_path = self.repo_path / self.config.audit_log
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import json
            from datetime import datetime, timezone

            # Parse commit to extract task references
            parsed = self.parser.parse(message)
            task_refs = [t.task_id for t in parsed.tasks]

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hook": "commit-msg",
                "mode": self.config.mode,
                "task_references": task_refs,
                "has_task_reference": parsed.has_task_reference,
                "issues_count": len(self.issues),
                "issues": [issue.to_dict() for issue in self.issues],
            }

            # Append to log file
            with open(audit_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Warning: Could not write audit log: {e}")

    def run(self) -> int:
        """
        Run commit-msg validation.

        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        # Check if hook is disabled
        if self.config.mode == "off":
            return 0

        # Read commit message
        message = self._read_commit_message()
        if not message:
            # Empty message or read error
            return 0 if not self.issues else 1

        # Run validations
        self._validate_commit_format(message)
        self._validate_task_exists(message)
        self._verify_completion_claims(message)

        # Determine outcome
        should_block = self._should_block(self.issues)

        # Write audit log if configured
        if self.config.mode == "audit" or self.config.audit_log:
            self._write_audit_log(message)

        # Display results
        if not self.issues:
            if self.config.mode != "audit":
                # Parse and show task references if found
                parsed = self.parser.parse(message)
                if parsed.has_task_reference:
                    tasks = ", ".join([t.task_id for t in parsed.tasks])
                    print(f"\n{self.GREEN}[vibey] Commit-msg:{self.RESET} ✓ Task references: {tasks}\n")
            return 0

        # Show mode header
        mode_display = {
            "advisory": f"{self.YELLOW}Advisory{self.RESET}",
            "blocking": f"{self.RED}Blocking{self.RESET}",
            "audit": f"{self.BLUE}Audit{self.RESET}",
        }.get(self.config.mode, self.config.mode)

        print(f"\n{self.BOLD}[vibey] {mode_display}:{self.RESET}")

        # Display issues
        for issue in self.issues:
            print(self._format_issue(issue))

        # Display action taken
        print()
        if should_block:
            print(f"{self.RED}Commit blocked.{self.RESET} Use --no-verify to override.\n")
            return 1
        else:
            action = "Logged to audit" if self.config.mode == "audit" else "Proceeding with commit"
            print(f"{action}... {self.GREEN}✓{self.RESET}\n")
            return 0


def main(args: List[str] = None) -> int:
    """
    Main entry point for commit-msg hook.

    Args:
        args: Command line arguments (first arg should be commit message file)

    Returns:
        Exit code
    """
    if args is None:
        args = sys.argv[1:]

    if not args:
        print("Error: No commit message file specified", file=sys.stderr)
        return 1

    commit_msg_file = args[0]

    try:
        hook = CommitMsgHook(commit_msg_file)
        return hook.run()
    except Exception as e:
        print(f"Error running commit-msg hook: {e}", file=sys.stderr)
        # Don't block on hook errors (fail open)
        return 0


if __name__ == "__main__":
    sys.exit(main())
