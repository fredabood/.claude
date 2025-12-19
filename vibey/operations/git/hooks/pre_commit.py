"""
Unified Pre-commit Hook Implementation with Triangle Validation

Validates roadmap YAML files and commit-ticket-artifact relationships
before allowing commits.

The hook executes in four phases:
1. Collect Data - Parse commit message, resolve staged files to artifacts
2. Triangle Validation - Check consistency across Ticket-Commit-Artifact
3. Completion Verification - Verify Completes: claims can be satisfied
4. Persist Relationships - Prepare relationship records (persisted post-commit)

Task: 01KCMNDFWS0C2N2FJJBZRR3FC8
Track: Context System V2
Sprint: Sprint 2: Context Implementation
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml


# =============================================================================
# CONFIGURATION MODELS
# =============================================================================


class ArtifactConsistencyMode(str, Enum):
    """Mode for artifact consistency checks."""

    OFF = "off"  # Check skipped entirely
    WARN = "warn"  # Show issues, commit proceeds
    PROMPT = "prompt"  # Show issues, ask user for resolution
    STRICT = "strict"  # Block commit until resolved


class CompletionVerificationMode(str, Enum):
    """Mode for completion verification."""

    OFF = "off"  # Skip verification
    WARN = "warn"  # Show warnings only
    STRICT = "strict"  # Block if criteria unmet


class Resolution(str, Enum):
    """User resolution options for discrepancies."""

    UPDATE_ASSOCIATIONS = "update_associations"  # Add artifacts to ticket
    UPDATE_MESSAGE = "update_message"  # Re-edit commit message
    ADD_REFERENCE = "add_reference"  # Add Task: reference
    PROCEED = "proceed"  # Override, commit as-is
    CANCEL = "cancel"  # Abort commit


@dataclass
class ArtifactConsistencyConfig:
    """Configuration for artifact consistency checks."""

    mode: ArtifactConsistencyMode = ArtifactConsistencyMode.PROMPT
    on_staged_not_associated: str = "prompt"  # ignore | warn | prompt | block
    on_associated_not_staged: str = "ignore"  # ignore | warn
    on_no_task_ref: str = "warn"  # ignore | warn | prompt | block


@dataclass
class CompletionVerificationConfig:
    """Configuration for completion verification."""

    mode: CompletionVerificationMode = CompletionVerificationMode.STRICT
    block_on_unmet_criteria: bool = True
    show_criteria_progress: bool = True


@dataclass
class TemplateConfig:
    """Configuration for commit message template."""

    auto_install: bool = True
    path: str = ".gitmessage"
    configure_git: bool = True


@dataclass
class OutputConfig:
    """Configuration for output formatting."""

    use_colors: bool = True
    show_artifact_paths: bool = True
    verbosity: str = "normal"  # quiet | normal | verbose


@dataclass
class PreCommitHookConfig:
    """Complete pre-commit hook configuration."""

    enabled: bool = True
    artifact_consistency: ArtifactConsistencyConfig = field(
        default_factory=ArtifactConsistencyConfig
    )
    completion_verification: CompletionVerificationConfig = field(
        default_factory=CompletionVerificationConfig
    )
    template: TemplateConfig = field(default_factory=TemplateConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    # Legacy config fields for backward compatibility
    mode: str = "advisory"  # off|advisory|blocking|audit
    audit_log: Optional[str] = None
    yaml_integrity: Dict = field(default_factory=lambda: {"enabled": True, "mode": "blocking"})
    task_status: Dict = field(default_factory=lambda: {"enabled": True, "mode": None})
    cli_usage: Dict = field(default_factory=lambda: {"enabled": False, "mode": None})

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "PreCommitHookConfig":
        """
        Load configuration from YAML file.

        Checks both new git_hooks.yaml and legacy git.yaml for config.
        """
        if config_path is None:
            # Try new config path first
            new_path = Path(".vibey/config/git_hooks.yaml")
            legacy_path = Path(".vibey/config/git.yaml")

            if new_path.exists():
                config_path = new_path
            elif legacy_path.exists():
                config_path = legacy_path
            else:
                return cls()  # Default configuration

        if not config_path.exists():
            return cls()

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            # Check for new-style config (git_hooks.yaml)
            if "pre_commit" in data:
                return cls._from_new_config(data["pre_commit"])

            # Check for legacy config (git.yaml)
            if "git" in data:
                return cls._from_legacy_config(data["git"])

            return cls()

        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return cls()

    @classmethod
    def _from_new_config(cls, pre_commit_data: Dict) -> "PreCommitHookConfig":
        """Load from new-style git_hooks.yaml configuration."""
        artifact_config = pre_commit_data.get("artifact_consistency", {})
        completion_config = pre_commit_data.get("completion_verification", {})
        template_config = pre_commit_data.get("template", {})
        output_config = pre_commit_data.get("output", {})

        return cls(
            enabled=pre_commit_data.get("enabled", True),
            artifact_consistency=ArtifactConsistencyConfig(
                mode=ArtifactConsistencyMode(artifact_config.get("mode", "prompt")),
                on_staged_not_associated=artifact_config.get("on_mismatch", {}).get(
                    "staged_not_in_associations", "prompt"
                ),
                on_associated_not_staged=artifact_config.get("on_mismatch", {}).get(
                    "associations_not_in_staged", "ignore"
                ),
                on_no_task_ref=artifact_config.get("on_mismatch", {}).get(
                    "no_task_ref", "warn"
                ),
            ),
            completion_verification=CompletionVerificationConfig(
                mode=CompletionVerificationMode(completion_config.get("mode", "strict")),
                block_on_unmet_criteria=completion_config.get("block_on_unmet_criteria", True),
                show_criteria_progress=completion_config.get("show_criteria_progress", True),
            ),
            template=TemplateConfig(
                auto_install=template_config.get("auto_install", True),
                path=template_config.get("path", ".gitmessage"),
                configure_git=template_config.get("configure_git", True),
            ),
            output=OutputConfig(
                use_colors=output_config.get("use_colors", True),
                show_artifact_paths=output_config.get("show_artifact_paths", True),
                verbosity=output_config.get("verbosity", "normal"),
            ),
        )

    @classmethod
    def _from_legacy_config(cls, git_data: Dict) -> "PreCommitHookConfig":
        """Load from legacy git.yaml configuration."""
        enforcement = git_data.get("enforcement", {})
        rules = enforcement.get("rules", {})
        audit = enforcement.get("audit", {})

        config = cls(
            mode=enforcement.get("mode", "advisory"),
            audit_log=audit.get("file") if audit.get("enabled") else None,
            yaml_integrity=rules.get("yaml_integrity", {"enabled": True, "mode": "blocking"}),
            task_status=rules.get("task_status", {"enabled": True, "mode": None}),
            cli_usage=rules.get("cli_usage", {"enabled": False, "mode": None}),
        )

        # Map legacy mode to new configs
        if config.mode == "blocking":
            config.artifact_consistency.mode = ArtifactConsistencyMode.STRICT
            config.completion_verification.mode = CompletionVerificationMode.STRICT
        elif config.mode == "off":
            config.artifact_consistency.mode = ArtifactConsistencyMode.OFF
            config.completion_verification.mode = CompletionVerificationMode.OFF

        return config


# =============================================================================
# VALIDATION ISSUE MODEL
# =============================================================================


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


# =============================================================================
# PHASE 1: COLLECT DATA MODELS
# =============================================================================


@dataclass
class CommitData:
    """Data collected in Phase 1."""

    commit_sha: str = ""
    commit_message: str = ""
    staged_files: List[str] = field(default_factory=list)

    # Parsed references
    task_refs: List[str] = field(default_factory=list)  # From "Task:" lines
    completion_claims: List[str] = field(default_factory=list)  # From "Completes:" lines

    # Resolved to artifacts
    staged_artifacts: Dict[str, str] = field(default_factory=dict)  # path -> artifact_id

    @property
    def all_referenced_tickets(self) -> Set[str]:
        """Get all tickets referenced in the commit message."""
        return set(self.task_refs + self.completion_claims)


# =============================================================================
# PHASE 2: TRIANGLE VALIDATION MODELS
# =============================================================================


@dataclass
class TriangleValidationResult:
    """Result of triangle validation for one ticket."""

    ticket_id: str

    # Set operations
    overlap: Set[str] = field(default_factory=set)  # A intersection B
    staged_only: Set[str] = field(default_factory=set)  # A - B (in commit but not ticket)
    ticket_only: Set[str] = field(default_factory=set)  # B - A (in ticket but not commit)

    # Validation status
    is_valid: bool = True
    requires_resolution: bool = False
    suggested_action: Optional[str] = None

    @property
    def has_issues(self) -> bool:
        """Check if there are any discrepancies."""
        return len(self.staged_only) > 0 or len(self.ticket_only) > 0


# =============================================================================
# PHASE 3: COMPLETION VERIFICATION MODELS
# =============================================================================


@dataclass
class CompletionVerificationResult:
    """Result of completion verification for one ticket."""

    ticket_id: str
    can_complete: bool = True
    blocking_reasons: List[str] = field(default_factory=list)
    unmet_criteria: List[str] = field(default_factory=list)


# =============================================================================
# PHASE 4: PENDING RELATIONSHIPS MODEL
# =============================================================================


@dataclass
class PendingRelationships:
    """Relationships to persist after successful commit."""

    ticket_commit_links: List[Dict] = field(default_factory=list)
    commit_artifact_changes: List[Dict] = field(default_factory=list)
    ticket_artifact_associations: List[Dict] = field(default_factory=list)


# =============================================================================
# HOOK RESULT MODEL
# =============================================================================


@dataclass
class HookResult:
    """Result of pre-commit hook execution."""

    blocked: bool = False
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    pending_relationships: Optional[PendingRelationships] = None
    user_resolutions: Dict[str, Resolution] = field(default_factory=dict)


# =============================================================================
# LEGACY HOOK CONFIG (for backward compatibility)
# =============================================================================


@dataclass
class HookConfig:
    """Pre-commit hook configuration (legacy)."""

    mode: str = "advisory"  # off|advisory|blocking|audit
    audit_log: Optional[str] = None

    # Rule configurations
    yaml_integrity: Dict = None
    task_status: Dict = None
    cli_usage: Dict = None
    completion_verification: Dict = None

    def __post_init__(self):
        """Set defaults for rule configs."""
        if self.yaml_integrity is None:
            self.yaml_integrity = {"enabled": True, "mode": "blocking"}
        if self.task_status is None:
            self.task_status = {"enabled": True, "mode": None}
        if self.cli_usage is None:
            self.cli_usage = {"enabled": False, "mode": None}
        if self.completion_verification is None:
            self.completion_verification = {"enabled": True, "mode": "blocking"}


# =============================================================================
# UNIFIED PRE-COMMIT HOOK
# =============================================================================


class UnifiedPreCommitHook:
    """
    Unified Pre-commit Hook with Triangle Validation.

    Validates commit message task references and artifact consistency
    across the Ticket-Commit-Artifact triangle.

    Four-Phase Execution:
    1. Collect Data - Parse commit message, resolve staged files
    2. Triangle Validation - Check consistency across relationships
    3. Completion Verification - Verify Completes: claims
    4. Persist Relationships - Prepare records for post-commit
    """

    # Terminal colors
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # ULID validation pattern (26 characters, Crockford base32)
    ULID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$", re.IGNORECASE)

    def __init__(self, repo_path: str = ".", config: Optional[PreCommitHookConfig] = None):
        """
        Initialize unified pre-commit hook.

        Args:
            repo_path: Path to git repository root
            config: Hook configuration (loads from file if not provided)
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = config or PreCommitHookConfig.load(self.repo_path / ".vibey" / "config" / "git_hooks.yaml")
        self.issues: List[ValidationIssue] = []

        # Artifact registry cache
        self._artifact_cache: Dict[str, str] = {}  # path -> artifact_id

    # =========================================================================
    # GIT OPERATIONS
    # =========================================================================

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        result = self._run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
        if result.returncode != 0:
            return []
        return [f for f in result.stdout.strip().split("\n") if f]

    def _get_staged_file_status(self) -> Dict[str, str]:
        """Get staged files with their change type (A/C/M/R/D)."""
        result = self._run_git("diff", "--cached", "--name-status")
        if result.returncode != 0:
            return {}

        status_map = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0][0]  # First char is status
                    file_path = parts[-1]  # Last is current path (for renames)
                    status_map[file_path] = status
        return status_map

    def _get_commit_message(self) -> str:
        """Get the commit message from COMMIT_EDITMSG."""
        msg_path = self.repo_path / ".git" / "COMMIT_EDITMSG"
        if msg_path.exists():
            return msg_path.read_text()
        return ""

    def _get_current_sha(self) -> str:
        """Get current HEAD SHA (empty string if no commits)."""
        result = self._run_git("rev-parse", "HEAD")
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    def _get_line_stats(self, file_path: str) -> Tuple[int, int]:
        """Get lines added/removed for a staged file."""
        result = self._run_git("diff", "--cached", "--numstat", file_path)
        if result.returncode != 0:
            return (0, 0)

        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    try:
                        added = int(parts[0]) if parts[0] != "-" else 0
                        removed = int(parts[1]) if parts[1] != "-" else 0
                        return (added, removed)
                    except ValueError:
                        pass
        return (0, 0)

    # =========================================================================
    # PHASE 1: COLLECT DATA
    # =========================================================================

    def phase_1_collect_data(self) -> CommitData:
        """
        Phase 1: Collect all data needed for validation.

        Parses commit message for Task:/Completes: markers and
        resolves staged files to artifact IDs.
        """
        commit_message = self._get_commit_message()
        staged_files = self._get_staged_files()
        commit_sha = self._get_current_sha()

        # Parse task references from message
        task_refs, completion_claims = self._parse_commit_message(commit_message)

        # Resolve staged files to artifacts
        staged_artifacts = self._resolve_to_artifacts(staged_files)

        return CommitData(
            commit_sha=commit_sha,
            commit_message=commit_message,
            staged_files=staged_files,
            task_refs=task_refs,
            completion_claims=completion_claims,
            staged_artifacts=staged_artifacts,
        )

    def _parse_commit_message(self, message: str) -> Tuple[List[str], List[str]]:
        """
        Parse task references from commit message.

        Supports:
        - Task: <id> or Task: <id1>, <id2>
        - Completes: <id> or Completes: <id1>, <id2>

        Returns:
            Tuple of (task_refs, completion_claims)
        """
        task_refs = []
        completion_claims = []

        for line in message.split("\n"):
            line = line.strip()

            # Skip comments
            if line.startswith("#"):
                continue

            # Parse Task: lines
            task_match = re.match(r"^Task:\s*(.+)$", line, re.IGNORECASE)
            if task_match:
                ids = [id.strip() for id in task_match.group(1).split(",")]
                task_refs.extend(self._validate_ticket_ids(ids))
                continue

            # Parse Completes: lines
            completes_match = re.match(r"^Completes:\s*(.+)$", line, re.IGNORECASE)
            if completes_match:
                ids = [id.strip() for id in completes_match.group(1).split(",")]
                completion_claims.extend(self._validate_ticket_ids(ids))
                continue

        return task_refs, completion_claims

    def _validate_ticket_ids(self, ids: List[str]) -> List[str]:
        """Validate and return only valid ticket IDs (ULIDs)."""
        valid_ids = []
        for ticket_id in ids:
            if self.ULID_PATTERN.match(ticket_id):
                valid_ids.append(ticket_id)
            elif ticket_id:  # Non-empty but invalid
                self.issues.append(ValidationIssue(
                    severity="warning",
                    rule="task_reference",
                    message=f"Invalid ticket ID format: '{ticket_id}'",
                    suggestion="Ticket IDs should be 26-character ULIDs",
                ))
        return valid_ids

    def _resolve_to_artifacts(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Resolve file paths to artifact IDs.

        Creates artifacts for files that don't have one yet.
        """
        artifacts = {}

        try:
            from vibey.roadmap.database.artifacts import get_or_create_artifact_id
            for path in file_paths:
                artifact_id = get_or_create_artifact_id(self.repo_path, path)
                if artifact_id:
                    artifacts[path] = artifact_id
        except ImportError:
            # Artifact registry not available - use path-based IDs
            for path in file_paths:
                # Create a deterministic pseudo-ID from path
                artifacts[path] = f"path:{path}"

        return artifacts

    # =========================================================================
    # PHASE 2: TRIANGLE VALIDATION
    # =========================================================================

    def phase_2_triangle_validation(
        self, commit_data: CommitData
    ) -> List[TriangleValidationResult]:
        """
        Phase 2: Validate triangle consistency for each referenced ticket.

        For each Task: reference, compare:
        - A = Artifacts in staged files
        - B = Artifacts associated with ticket

        Checks:
        1. A intersection B - Files in both (expected, good)
        2. A - B - Staged NOT in ticket associations (prompt to add)
        3. B - A - Ticket associations NOT in staged (info only)
        """
        results = []

        if self.config.artifact_consistency.mode == ArtifactConsistencyMode.OFF:
            return results

        staged_artifacts = set(commit_data.staged_artifacts.values())

        for ticket_id in commit_data.task_refs:
            # Get artifacts associated with this ticket
            ticket_artifacts = self._get_ticket_artifacts(ticket_id)

            # Set operations
            overlap = staged_artifacts & ticket_artifacts
            staged_only = staged_artifacts - ticket_artifacts
            ticket_only = ticket_artifacts - staged_artifacts

            # Determine if resolution needed
            requires_resolution = False
            suggested_action = None

            if staged_only and self.config.artifact_consistency.on_staged_not_associated != "ignore":
                requires_resolution = True
                suggested_action = f"Add {len(staged_only)} artifact(s) to ticket associations"

            result = TriangleValidationResult(
                ticket_id=ticket_id,
                overlap=overlap,
                staged_only=staged_only,
                ticket_only=ticket_only,
                is_valid=not requires_resolution or self.config.artifact_consistency.mode == ArtifactConsistencyMode.WARN,
                requires_resolution=requires_resolution,
                suggested_action=suggested_action,
            )
            results.append(result)

            # Add warnings/info for discrepancies
            if staged_only:
                severity = self._get_severity_for_mode(
                    self.config.artifact_consistency.on_staged_not_associated
                )
                self.issues.append(ValidationIssue(
                    severity=severity,
                    rule="artifact_consistency",
                    message=f"Ticket {ticket_id[:8]}...: {len(staged_only)} staged file(s) not associated",
                    suggestion=suggested_action,
                ))

            if ticket_only and self.config.artifact_consistency.on_associated_not_staged == "warn":
                self.issues.append(ValidationIssue(
                    severity="info",
                    rule="artifact_consistency",
                    message=f"Ticket {ticket_id[:8]}...: {len(ticket_only)} associated file(s) not in commit",
                ))

        # Check for files matching OTHER tasks (not referenced)
        if commit_data.staged_artifacts and self.config.artifact_consistency.on_no_task_ref != "ignore":
            for artifact_id in commit_data.staged_artifacts.values():
                other_tickets = self._find_tickets_for_artifact(artifact_id)
                unreferenced = other_tickets - commit_data.all_referenced_tickets

                if unreferenced:
                    severity = self._get_severity_for_mode(
                        self.config.artifact_consistency.on_no_task_ref
                    )
                    self.issues.append(ValidationIssue(
                        severity=severity,
                        rule="artifact_consistency",
                        message=f"Staged file associated with unreferenced ticket(s): {', '.join(list(unreferenced)[:3])}",
                        suggestion=f"Consider adding Task: {list(unreferenced)[0]} to commit message",
                    ))

        return results

    def _get_ticket_artifacts(self, ticket_id: str) -> Set[str]:
        """Get artifact IDs associated with a ticket."""
        try:
            from vibey.roadmap.database.relationships import get_ticket_artifact_associations
            associations = get_ticket_artifact_associations(self.repo_path, ticket_id)
            return {a.artifact_id for a in associations}
        except ImportError:
            return set()

    def _find_tickets_for_artifact(self, artifact_id: str) -> Set[str]:
        """Find tickets that have this artifact associated."""
        try:
            from vibey.roadmap.database.relationships import find_tickets_for_artifact
            return set(find_tickets_for_artifact(self.repo_path, artifact_id))
        except ImportError:
            return set()

    def _get_severity_for_mode(self, mode: str) -> str:
        """Map mode to severity level."""
        return {
            "ignore": "info",
            "warn": "warning",
            "prompt": "warning",
            "block": "error",
        }.get(mode, "warning")

    # =========================================================================
    # PHASE 3: COMPLETION VERIFICATION
    # =========================================================================

    def phase_3_completion_verification(
        self, commit_data: CommitData
    ) -> List[CompletionVerificationResult]:
        """
        Phase 3: Verify completion claims can be satisfied.

        For each Completes: reference, load ticket and check
        if it can transition to COMPLETED status.
        """
        results = []

        if self.config.completion_verification.mode == CompletionVerificationMode.OFF:
            return results

        for ticket_id in commit_data.completion_claims:
            result = self._verify_ticket_completion(ticket_id)
            results.append(result)

            if not result.can_complete:
                severity = (
                    "error"
                    if self.config.completion_verification.mode == CompletionVerificationMode.STRICT
                    else "warning"
                )

                self.issues.append(ValidationIssue(
                    severity=severity,
                    rule="completion_verification",
                    message=f"Cannot complete ticket {ticket_id[:8]}...: {result.blocking_reasons[0] if result.blocking_reasons else 'Unknown reason'}",
                    suggestion="Resolve blocking criteria before claiming completion",
                ))

                if self.config.completion_verification.show_criteria_progress:
                    for criterion in result.unmet_criteria[:3]:
                        self.issues.append(ValidationIssue(
                            severity="info",
                            rule="completion_verification",
                            message=f"  - Unmet: {criterion}",
                        ))

        return results

    def _verify_ticket_completion(self, ticket_id: str) -> CompletionVerificationResult:
        """Verify if a ticket can be marked complete."""
        try:
            from vibey.operations.roadmap.query import load_task_ticket
            from vibey.roadmap.models.ticket import TicketStatus

            ticket = load_task_ticket(self.repo_path, ticket_id)
            if ticket is None:
                return CompletionVerificationResult(
                    ticket_id=ticket_id,
                    can_complete=False,
                    blocking_reasons=[f"Ticket {ticket_id} not found"],
                )

            can_complete, blockers = ticket.can_transition_to(TicketStatus.COMPLETED)

            unmet_criteria = []
            if not can_complete:
                unmet_criteria = [
                    c.description
                    for c in ticket.criteria
                    if c.blocks_transition_to == TicketStatus.COMPLETED and not c.is_met
                ]

            return CompletionVerificationResult(
                ticket_id=ticket_id,
                can_complete=can_complete,
                blocking_reasons=blockers,
                unmet_criteria=unmet_criteria,
            )

        except ImportError:
            # Ticket system not available
            return CompletionVerificationResult(
                ticket_id=ticket_id,
                can_complete=True,  # Allow if we can't verify
                blocking_reasons=[],
            )
        except Exception as e:
            return CompletionVerificationResult(
                ticket_id=ticket_id,
                can_complete=False,
                blocking_reasons=[str(e)],
            )

    # =========================================================================
    # PHASE 4: BUILD PENDING RELATIONSHIPS
    # =========================================================================

    def phase_4_build_pending_relationships(
        self,
        commit_data: CommitData,
        triangle_results: List[TriangleValidationResult],
        user_resolutions: Dict[str, Resolution],
    ) -> PendingRelationships:
        """
        Phase 4: Build pending relationships for post-commit persistence.

        Creates:
        - TicketCommitLink for each Task:/Completes: reference
        - CommitArtifactChange for each staged file
        - TicketArtifactAssociation for user-approved additions
        """
        pending = PendingRelationships()
        now = datetime.now(timezone.utc).isoformat()
        file_status = self._get_staged_file_status()

        # Build TicketCommitLink for Task: references
        for ticket_id in commit_data.task_refs:
            pending.ticket_commit_links.append({
                "ticket_id": ticket_id,
                "commit_sha": commit_data.commit_sha,
                "reference_type": "task_reference",
                "link_source": "pre_commit_hook",
                "linked_at": now,
            })

        # Build TicketCommitLink for Completes: references
        for ticket_id in commit_data.completion_claims:
            pending.ticket_commit_links.append({
                "ticket_id": ticket_id,
                "commit_sha": commit_data.commit_sha,
                "reference_type": "completion_claim",
                "link_source": "pre_commit_hook",
                "linked_at": now,
            })

        # Build CommitArtifactChange for each staged file
        for path, artifact_id in commit_data.staged_artifacts.items():
            status = file_status.get(path, "M")
            change_type = {
                "A": "added",
                "M": "modified",
                "D": "deleted",
                "R": "renamed",
            }.get(status, "modified")

            lines_added, lines_removed = self._get_line_stats(path)

            pending.commit_artifact_changes.append({
                "commit_sha": commit_data.commit_sha,
                "artifact_id": artifact_id,
                "change_type": change_type,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "recorded_at": now,
            })

        # Build TicketArtifactAssociation for user-approved additions
        for result in triangle_results:
            resolution = user_resolutions.get(result.ticket_id)
            if resolution == Resolution.UPDATE_ASSOCIATIONS:
                for artifact_id in result.staged_only:
                    pending.ticket_artifact_associations.append({
                        "ticket_id": result.ticket_id,
                        "artifact_id": artifact_id,
                        "association_source": "commit_bootstrap",
                        "added_at": now,
                        "added_by": "pre_commit_hook",
                    })

        return pending

    # =========================================================================
    # INTERACTIVE RESOLUTION
    # =========================================================================

    def prompt_for_resolutions(
        self, results: List[TriangleValidationResult]
    ) -> Dict[str, Resolution]:
        """
        Prompt user for resolution of triangle validation issues.

        Only called in 'prompt' mode when there are issues requiring resolution.
        """
        resolutions = {}

        for result in results:
            if not result.requires_resolution:
                continue

            print(f"\n{self.BOLD}Ticket: {result.ticket_id}{self.RESET}")
            print(f"  Staged files not in ticket associations: {len(result.staged_only)}")

            if self.config.output.show_artifact_paths:
                for artifact_id in list(result.staged_only)[:5]:
                    print(f"    - {artifact_id}")
                if len(result.staged_only) > 5:
                    print(f"    ... and {len(result.staged_only) - 5} more")

            print("\n  Resolution options:")
            print(f"  {self.CYAN}1{self.RESET}. Add files to ticket associations")
            print(f"  {self.CYAN}2{self.RESET}. Proceed without updating (override)")
            print(f"  {self.CYAN}3{self.RESET}. Cancel commit")

            try:
                choice = input(f"\n  Select option [1-3]: ").strip()

                if choice == "1":
                    resolutions[result.ticket_id] = Resolution.UPDATE_ASSOCIATIONS
                elif choice == "2":
                    resolutions[result.ticket_id] = Resolution.PROCEED
                elif choice == "3":
                    resolutions[result.ticket_id] = Resolution.CANCEL
                else:
                    # Default to proceed
                    resolutions[result.ticket_id] = Resolution.PROCEED
            except (EOFError, KeyboardInterrupt):
                resolutions[result.ticket_id] = Resolution.CANCEL

        return resolutions

    # =========================================================================
    # MAIN RUN METHOD
    # =========================================================================

    def run(self) -> HookResult:
        """
        Run the unified pre-commit hook.

        Executes all four phases and returns the result.
        """
        result = HookResult()

        # Check if hook is disabled
        if not self.config.enabled:
            return result

        # Phase 1: Collect Data
        commit_data = self.phase_1_collect_data()

        # Phase 2: Triangle Validation
        triangle_results = self.phase_2_triangle_validation(commit_data)

        # Handle validation issues based on mode
        user_resolutions = {}
        if self.config.artifact_consistency.mode == ArtifactConsistencyMode.PROMPT:
            needs_resolution = [r for r in triangle_results if r.requires_resolution]
            if needs_resolution:
                user_resolutions = self.prompt_for_resolutions(needs_resolution)

                # Check if user cancelled
                if Resolution.CANCEL in user_resolutions.values():
                    result.blocked = True
                    result.reasons.append("User cancelled commit")
                    return result

        elif self.config.artifact_consistency.mode == ArtifactConsistencyMode.STRICT:
            if any(r.has_issues for r in triangle_results):
                result.blocked = True
                result.reasons.append("Artifact consistency check failed in strict mode")

        # Phase 3: Completion Verification
        completion_results = self.phase_3_completion_verification(commit_data)

        if self.config.completion_verification.mode == CompletionVerificationMode.STRICT:
            failed = [r for r in completion_results if not r.can_complete]
            if failed:
                result.blocked = True
                for r in failed:
                    result.reasons.extend(r.blocking_reasons)

        # Phase 4: Build Pending Relationships (for post-commit)
        if not result.blocked:
            result.pending_relationships = self.phase_4_build_pending_relationships(
                commit_data, triangle_results, user_resolutions
            )

        # Collect warnings
        for issue in self.issues:
            if issue.severity == "warning":
                result.warnings.append(issue.message)

        result.user_resolutions = user_resolutions
        return result


# =============================================================================
# LEGACY PRE-COMMIT HOOK (for backward compatibility)
# =============================================================================


class PreCommitHook:
    """
    Pre-commit hook for Vibey roadmap validation.

    Validates YAML syntax, roadmap consistency, and enforces
    configured rules based on enforcement mode.

    NOTE: This is the legacy hook. New code should use UnifiedPreCommitHook.
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

        # Create unified hook for new features
        unified_config = PreCommitHookConfig.load(self.repo_path / ".vibey" / "config" / "git_hooks.yaml")
        self.unified_hook = UnifiedPreCommitHook(repo_path, unified_config)

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

        try:
            from vibey.operations.git.yaml_analyzer import YAMLChangeAnalyzer

            # Determine if we're in blocking mode for CLI usage
            cli_mode = self.config.cli_usage.get("mode") or self.config.mode
            blocking_mode = cli_mode == "blocking"

            analyzer = YAMLChangeAnalyzer(str(self.repo_path))
            results = analyzer.analyze_staged_changes(blocking_mode=blocking_mode)

            for result in results:
                # Determine severity based on mode and whether it should block
                if result.should_block and blocking_mode:
                    severity = "error"
                else:
                    severity = "warning"

                # Build suggestion string from all suggestions
                if result.suggestions:
                    # Take the highest priority suggestion
                    best_suggestion = sorted(
                        result.suggestions,
                        key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.priority, 2)
                    )[0]
                    suggestion_text = best_suggestion.command
                else:
                    suggestion_text = None

                # Build change description
                changed_fields = ", ".join(set(c.field_name for c in result.changes))

                self.issues.append(ValidationIssue(
                    severity=severity,
                    rule="cli_usage",
                    message=f"Manual YAML edit detected: {result.file_path}\n      Modified: {changed_fields}",
                    file=result.file_path,
                    suggestion=f"Use: {suggestion_text}" if suggestion_text else None,
                ))

        except ImportError:
            # Fallback to basic detection if yaml_analyzer not available
            self._check_cli_usage_basic()

    def _check_cli_usage_basic(self) -> None:
        """Basic CLI usage check (fallback when yaml_analyzer unavailable)."""
        staged_files = self._get_staged_files()
        roadmap_files = [
            f for f in staged_files
            if f.startswith(".vibey/roadmap/") and (
                f.endswith("/sprint.yaml") or
                f.endswith("/track.yaml") or
                f.endswith("/task.yaml")
            )
        ]

        for file in roadmap_files:
            result = self._run_git("diff", "--cached", file)
            if result.returncode == 0:
                diff = result.stdout

                if "status:" in diff or "progress:" in diff or "completed:" in diff:
                    if file.endswith("sprint.yaml"):
                        item_type = "sprint"
                        item_id = file.split("/")[-2]
                    elif file.endswith("track.yaml"):
                        item_type = "track"
                        item_id = file.split("/")[-2]
                    elif file.endswith("task.yaml"):
                        item_type = "task"
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

    def _verify_activity_log(self) -> None:
        """
        Verify staged roadmap files have matching activity log entries.

        Uses V2 command-level activity log to verify that changes were made
        through the CLI, not by direct YAML edits.
        """
        try:
            from vibey.operations.roadmap.verification import ChangeVerifier
        except ImportError:
            # Verification module not available, skip
            return

        staged_files = self._get_staged_files()
        roadmap_files = [
            f for f in staged_files
            if f.startswith(".vibey/roadmap/") and f.endswith(".yaml")
        ]

        if not roadmap_files:
            return

        verifier = ChangeVerifier(self.repo_path)
        failures = []

        for file in roadmap_files:
            file_path = Path(file)
            result = verifier.verify_file(file_path)
            if not result.verified:
                failures.append((file, result))

        if failures:
            # Determine severity based on mode
            mode = self._get_rule_mode("cli_usage")  # Use cli_usage mode for verification
            severity = "error" if mode == "blocking" else "warning"

            for file, result in failures:
                self.issues.append(ValidationIssue(
                    severity=severity,
                    rule="activity_log_verification",
                    message=f"No activity log entry for: {file}",
                    file=file,
                    suggestion="Use 'vibey roadmap' CLI commands to make changes",
                ))

    def _check_completion_verification(self) -> None:
        """
        Verify that items being marked as completed meet all completion criteria.

        Uses the unified ticket model's can_transition_to() validation to ensure
        that tasks, sprints, and tracks meet their completion requirements before
        allowing the commit.
        """
        if not self.config.completion_verification.get("enabled", True):
            return

        try:
            from vibey.operations.roadmap.query import (
                load_task_ticket,
                load_sprint_ticket,
                load_track_ticket,
            )
            from vibey.roadmap.models.ticket import TicketStatus
        except ImportError:
            # Ticket models not available, skip verification
            return

        staged_files = self._get_staged_files()

        for file in staged_files:
            if not file.startswith(".vibey/roadmap/") or not file.endswith(".yaml"):
                continue

            # Check if this file contains a status change to "completed"
            result = self._run_git("diff", "--cached", file)
            if result.returncode != 0:
                continue

            diff = result.stdout

            # Look for status being changed to completed
            if "+  status: completed" not in diff and "+status: completed" not in diff:
                continue

            # Determine item type and ID
            if file.endswith("/task.yaml"):
                item_type = "task"
                item_id = file.split("/")[-2]
            elif file.endswith("/sprint.yaml"):
                item_type = "sprint"
                item_id = file.split("/")[-2]
            elif file.endswith("/track.yaml"):
                item_type = "track"
                item_id = file.split("/")[-2]
            else:
                continue

            # Load the ticket and check if it can be completed
            try:
                if item_type == "task":
                    ticket = load_task_ticket(self.repo_path, item_id)
                elif item_type == "sprint":
                    ticket = load_sprint_ticket(self.repo_path, item_id)
                elif item_type == "track":
                    ticket = load_track_ticket(self.repo_path, item_id)
                else:
                    continue

                # Check if can transition to completed
                can_complete, blockers = ticket.can_transition_to(TicketStatus.COMPLETED)

                if not can_complete and blockers:
                    # Determine severity based on mode
                    mode = self._get_rule_mode("completion_verification")
                    severity = "error" if mode == "blocking" else "warning"

                    self.issues.append(ValidationIssue(
                        severity=severity,
                        rule="completion_verification",
                        message=f"Cannot complete {item_type} '{item_id}': {', '.join(blockers[:3])}",
                        file=file,
                        suggestion=f"Resolve blockers before marking as completed",
                    ))

            except Exception as e:
                # If we can't load the ticket, add a warning but don't block
                self.issues.append(ValidationIssue(
                    severity="warning",
                    rule="completion_verification",
                    message=f"Could not verify completion criteria for {item_id}: {str(e)[:50]}",
                    file=file,
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
            "error": f"{self.RED}x{self.RESET}",
            "warning": f"{self.YELLOW}!{self.RESET}",
            "info": f"{self.BLUE}i{self.RESET}",
        }.get(issue.severity, "-")

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

    def _sync_database_to_yaml(self) -> bool:
        """
        Sync SQLite database to YAML if database has uncommitted changes.

        Returns:
            True if sync succeeded or wasn't needed, False if sync failed
        """
        try:
            from vibey.roadmap.database.connection import database_exists, get_db_path
            from vibey.roadmap.serialization.backend import SyncManager

            db_path = get_db_path(self.repo_path)

            # Check if database exists
            if not database_exists(db_path=db_path):
                return True  # No database, nothing to sync

            roadmap_dir = self.repo_path / ".vibey" / "roadmap"
            sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

            # Check if database is dirty
            if not sync.is_db_dirty():
                return True  # Database is clean, nothing to sync

            # Database has uncommitted changes - dump to YAML
            print(f"{self.YELLOW}[vibey]{self.RESET} Database has uncommitted changes, syncing to YAML...")

            try:
                sync.dump()

                # Get list of modified YAML files
                modified_files = self._get_modified_yaml_files()

                if modified_files:
                    # Stage the modified YAML files
                    for f in modified_files:
                        self._run_git("add", f)
                    print(f"{self.GREEN}[vibey]{self.RESET} Synced and staged {len(modified_files)} YAML files")

                return True

            except Exception as e:
                self.issues.append(ValidationIssue(
                    severity="error",
                    rule="db_sync",
                    message=f"Failed to sync database to YAML: {e}",
                    suggestion="Run 'vibey roadmap db dump' manually or use --no-verify to skip",
                ))
                return False

        except ImportError:
            # SQLite backend not available, skip sync
            return True

    def _get_modified_yaml_files(self) -> List[str]:
        """Get list of modified YAML files in .vibey/roadmap/."""
        result = self._run_git("status", "--porcelain", ".vibey/roadmap/")
        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.strip().split("\n"):
            if line and len(line) > 3:
                status = line[:2]
                file_path = line[3:]
                if file_path.endswith(".yaml") and status.strip():
                    files.append(file_path)

        return files

    def _save_pending_relationships(self, pending: PendingRelationships) -> None:
        """Save pending relationships for post-commit hook to process."""
        pending_path = self.repo_path / ".vibey" / ".pending_relationships.json"
        try:
            with open(pending_path, "w") as f:
                json.dump({
                    "ticket_commit_links": pending.ticket_commit_links,
                    "commit_artifact_changes": pending.commit_artifact_changes,
                    "ticket_artifact_associations": pending.ticket_artifact_associations,
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save pending relationships: {e}")

    def run(self) -> int:
        """
        Run pre-commit validation.

        Returns:
            Exit code: 0 for success, non-zero for failure
        """
        # Check if hook is disabled
        if self.config.mode == "off":
            return 0

        # Sync database to YAML if needed
        self._sync_database_to_yaml()

        # Run legacy validations
        self._validate_roadmap_files()
        self._verify_activity_log()
        self._check_cli_usage()
        self._check_completion_verification()

        # Run unified hook (triangle validation)
        unified_result = self.unified_hook.run()

        # Merge unified hook issues into our issues
        self.issues.extend(self.unified_hook.issues)

        # Save pending relationships for post-commit
        if unified_result.pending_relationships:
            self._save_pending_relationships(unified_result.pending_relationships)

        # Determine outcome
        should_block = self._should_block(self.issues) or unified_result.blocked

        # Write audit log if configured
        if self.config.mode == "audit" or self.config.audit_log:
            self._write_audit_log()

        # Display results
        if not self.issues:
            if self.config.mode != "audit":
                print(f"\n{self.GREEN}[vibey] Pre-commit:{self.RESET} All checks passed\n")
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
            print(f"{action}... {self.GREEN}OK{self.RESET}\n")
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
