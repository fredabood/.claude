"""
Git operations for Implementation Mode.

This submodule provides git-related services for the implementation loop,
including branch management, git requirements validation, commit linking,
and context dumping.

Components:
- TicketBranchManager: Manages git branches tied to tickets
- GitRequirementsEnforcer: Validates and enforces git repository state
- TicketCommitLinker: Links commits to tickets with metadata tracking
- CommitContextDumper: Dumps context state at commit time for audit trail

Usage:
    from vibey.services.implementation.git import (
        TicketBranchManager,
        GitRequirementsEnforcer,
        TicketCommitLinker,
        CommitContextDumper,
        CommitType,
    )

    # Branch management
    manager = TicketBranchManager(repo_root=Path("."), config=config)
    branch_name = manager.create_ticket_branch(ticket)
    manager.checkout_ticket_branch(ticket)
    result = manager.merge_to_main(ticket, strategy=MergeStrategy.SQUASH)
    if result.success:
        manager.cleanup_branch(ticket)

    # Git requirements enforcement
    enforcer = GitRequirementsEnforcer(config, repo_root=Path("."))
    result = enforcer.validate_preconditions()
    if not result.passed:
        for issue in result.issues:
            print(f"{issue.severity.value}: {issue.message}")

    # Commit linking
    linker = TicketCommitLinker(repo_root=Path("."))
    commit_hash = linker.create_linked_commit(
        ticket=task,
        message="Implement feature X",
        commit_type=CommitType.FEAT,
    )

    # Context dumping
    dumper = CommitContextDumper(repo_root=Path("."))
    context_path = dumper.dump_commit_context(
        ticket_id="01ABC123",
        commit_sha="abc1234",
    )
"""

from vibey.services.implementation.git.branch_manager import (
    BranchError,
    BranchConflictError,
    BranchNotFoundError,
    BranchStatus,
    DEFAULT_BRANCH_PREFIX,
    MergeResult,
    MergeStrategy,
    NotAGitRepositoryError,
    TicketBranchManager,
)
from vibey.services.implementation.git.commit_linker import (
    CommitRef,
    CommitType,
    TicketCommitLinker,
)
from vibey.services.implementation.git.context_dumper import (
    CommitContext,
    CommitContextDumper,
)
from vibey.services.implementation.git.requirements import (
    DEFAULT_MAIN_BRANCHES,
    DEFAULT_STASH_MESSAGE_PREFIX,
    EnforcementResult,
    GitIssue,
    GitIssueType,
    GitOperationError,
    GitRequirementsEnforcer,
    GitRequirementsError,
    IssueSeverity,
    RemediationResult,
    RequirementLevel,
    SyncStatus,
    ValidationResult,
    is_git_clean,
    validate_git_preconditions,
)

__all__ = [
    # Branch Manager
    "BranchConflictError",
    "BranchError",
    "BranchNotFoundError",
    "BranchStatus",
    "DEFAULT_BRANCH_PREFIX",
    "MergeResult",
    "MergeStrategy",
    "NotAGitRepositoryError",
    "TicketBranchManager",
    # Commit Linker
    "CommitRef",
    "CommitType",
    "TicketCommitLinker",
    # Context Dumper
    "CommitContext",
    "CommitContextDumper",
    # Requirements Enforcer
    "DEFAULT_MAIN_BRANCHES",
    "DEFAULT_STASH_MESSAGE_PREFIX",
    "EnforcementResult",
    "GitIssue",
    "GitIssueType",
    "GitOperationError",
    "GitRequirementsEnforcer",
    "GitRequirementsError",
    "IssueSeverity",
    "RemediationResult",
    "RequirementLevel",
    "SyncStatus",
    "ValidationResult",
    "is_git_clean",
    "validate_git_preconditions",
]
