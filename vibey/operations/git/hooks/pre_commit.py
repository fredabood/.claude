"""
Pre-commit Hook Implementation

Validates roadmap YAML files before allowing commits.

Task: git-integration-2-task-001
Status: In Progress
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import yaml


@dataclass
class ValidationIssue:
    """A validation issue found during pre-commit checks."""
    severity: str  # "error", "warning", "info"
    rule: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "rule": self.rule,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "suggestion": self.suggestion,
        }


@dataclass
class HookConfig:
    """Pre-commit hook configuration."""
    mode: str = "advisory"  # off|advisory|blocking|audit
    audit_log: Optional[str] = None

    # Rule configurations
    yaml_integrity: Dict = None
    task_status: Dict = None
    cli_usage: Dict = None

    def __post_init__(self):
        """Set defaults for rule configs."""
        if self.yaml_integrity is None:
            self.yaml_integrity = {"enabled": True, "mode": "blocking"}
        if self.task_status is None:
            self.task_status = {"enabled": True, "mode": None}
        if self.cli_usage is None:
            self.cli_usage = {"enabled": False, "mode": None}


class PreCommitHook:
    """
    Pre-commit hook for Vibey roadmap validation.

    Validates YAML syntax, roadmap consistency, and enforces
    configured rules based on enforcement mode.
    """

    # Terminal colors
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, repo_path: str = "."):
        """
        Initialize pre-commit hook.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = self._load_config()
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

            return HookConfig(
                mode=enforcement.get("mode", "advisory"),
                audit_log=audit.get("file") if audit.get("enabled") else None,
                yaml_integrity=rules.get("yaml_integrity", {}),
                task_status=rules.get("task_status", {}),
                cli_usage=rules.get("cli_usage", {}),
            )
        except Exception as e:
            # If config is broken, use defaults
            print(f"Warning: Could not load config: {e}")
            return HookConfig()

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _get_staged_files(self, pattern: str = "*") -> List[str]:
        """
        Get list of staged files matching pattern.

        Args:
            pattern: Glob pattern to filter files

        Returns:
            List of file paths relative to repo root
        """
        result = self._run_git("diff", "--cached", "--name-only", "--diff-filter=ACM")
        if result.returncode != 0:
            return []

        files = [f for f in result.stdout.strip().split("\n") if f]

        # Filter by pattern
        if pattern != "*":
            from fnmatch import fnmatch
            files = [f for f in files if fnmatch(f, pattern)]

        return files

    def _validate_yaml_syntax(self, file_path: str) -> bool:
        """
        Validate YAML syntax for a file.

        Args:
            file_path: Path to YAML file

        Returns:
            True if valid, False otherwise
        """
        full_path = self.repo_path / file_path

        try:
            with open(full_path) as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            line_num = line.line + 1 if line else None

            self.issues.append(ValidationIssue(
                severity="error",
                rule="yaml_integrity",
                message=f"Invalid YAML syntax: {e.problem}" if hasattr(e, "problem") else "Invalid YAML syntax",
                file=file_path,
                line=line_num,
                suggestion="Fix YAML syntax errors before committing",
            ))
            return False
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity="error",
                rule="yaml_integrity",
                message=f"Could not read file: {e}",
                file=file_path,
                suggestion="Ensure file exists and is readable",
            ))
            return False

    def _validate_roadmap_files(self) -> bool:
        """
        Validate all staged roadmap YAML files.

        Returns:
            True if all valid, False if any invalid
        """
        # Get staged .yaml files in .vibey/roadmap/
        staged_files = self._get_staged_files()
        roadmap_files = [
            f for f in staged_files
            if f.startswith(".vibey/roadmap/") and f.endswith(".yaml")
        ]

        if not roadmap_files:
            # No roadmap files staged, nothing to validate
            return True

        all_valid = True
        for file in roadmap_files:
            if not self._validate_yaml_syntax(file):
                all_valid = False

        return all_valid

    def _check_cli_usage(self) -> None:
        """Check if CLI should have been used instead of manual edits."""
        if not self.config.cli_usage.get("enabled", False):
            return

        # Get staged roadmap YAML files
        staged_files = self._get_staged_files()
        roadmap_files = [
            f for f in staged_files
            if f.startswith(".vibey/roadmap/") and (
                f.endswith("/sprint.yaml") or
                f.endswith("/track.yaml")
            )
        ]

        for file in roadmap_files:
            # Get the diff to see what changed
            result = self._run_git("diff", "--cached", file)
            if result.returncode == 0:
                diff = result.stdout

                # Check for common manual edit patterns
                if "status:" in diff or "progress:" in diff or "completed:" in diff:
                    # Extract file type
                    if file.endswith("sprint.yaml"):
                        item_type = "sprint"
                        item_id = file.split("/")[-2]
                    elif file.endswith("track.yaml"):
                        item_type = "track"
                        item_id = file.split("/")[-2]
                    else:
                        continue

                    self.issues.append(ValidationIssue(
                        severity="warning",
                        rule="cli_usage",
                        message=f"Manual YAML edit detected: {file}",
                        file=file,
                        suggestion=f"Consider using CLI: vibey roadmap update {item_type} {item_id} ...",
                    ))

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

        if issue.file:
            location = f"{issue.file}"
            if issue.line:
                location += f":{issue.line}"
            lines.append(f"    {self.BLUE}{location}{self.RESET}")

        if issue.suggestion:
            lines.append(f"    {self.GREEN}Suggestion:{self.RESET} {issue.suggestion}")

        return "\n".join(lines)

    def _write_audit_log(self) -> None:
        """Write validation results to audit log."""
        if not self.config.audit_log:
            return

        audit_path = self.repo_path / self.config.audit_log
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import json
            from datetime import datetime, timezone

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hook": "pre-commit",
                "mode": self.config.mode,
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
        Run pre-commit validation.

        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        # Check if hook is disabled
        if self.config.mode == "off":
            return 0

        # Run validations
        self._validate_roadmap_files()
        self._check_cli_usage()

        # Determine outcome
        should_block = self._should_block(self.issues)

        # Write audit log if configured
        if self.config.mode == "audit" or self.config.audit_log:
            self._write_audit_log()

        # Display results
        if not self.issues:
            if self.config.mode != "audit":
                print(f"\n{self.GREEN}[vibey] Pre-commit:{self.RESET} ✓ All checks passed\n")
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


def main() -> int:
    """Main entry point for pre-commit hook."""
    try:
        hook = PreCommitHook()
        return hook.run()
    except Exception as e:
        print(f"Error running pre-commit hook: {e}", file=sys.stderr)
        # Don't block on hook errors (fail open)
        return 0


if __name__ == "__main__":
    sys.exit(main())
