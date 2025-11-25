"""
Git integration operations for Vibey roadmap system.

This package provides:
- Commit message parsing and task correlation
- Git log analysis and sprint velocity calculations
- State reconstruction from git history
- Tag-based milestone tracking
"""

from vibey.operations.git.commit_parser_schema import (
    CommitFormat,
    TaskStatus,
    TaskReference,
    SprintReference,
    TrackReference,
    CommitMessageParts,
    ParsedCommit,
    ParserConfig,
    RegexPatterns,
    CommitParserInterface,
    ParseResult,
    STATUS_KEYWORDS,
)

from vibey.operations.git.commit_parser import (
    CommitParser,
    analyze_batch,
)

from vibey.operations.git.log_analyzer import (
    CommitInfo,
    BranchInfo,
    TagInfo,
    AnalysisResult,
    GitLogAnalyzer,
    analyze_repository,
)

from vibey.operations.git.velocity_calculator import (
    TaskMetrics,
    SprintVelocity,
    VelocityTrend,
    VelocityCalculator,
    quick_sprint_velocity,
)

from vibey.operations.git.tag_parser import (
    TagType,
    ParsedTag,
    TagParser,
    get_sprint_commits_with_tags,
    get_task_commits_with_tags,
)

from vibey.operations.git.state_reconstructor import (
    StateSnapshot,
    StateChange,
    ProgressPoint,
    StateReconstructor,
    get_state_at_ref,
)

from vibey.operations.git.hooks import (
    PreCommitHook,
    CommitMsgHook,
    ValidationIssue,
    HookConfig,
)

from vibey.operations.git.status_updater import (
    StatusUpdate,
    UpdateResult,
    TaskStatusUpdater,
    update_from_commit,
    update_from_recent_commits,
)

from vibey.operations.git.branch_linker import (
    BranchType,
    BranchInfo,
    BranchLinkInfo,
    BranchLinker,
    create_task_branch,
)

from vibey.operations.git.pr_generator import (
    TaskInfo,
    PRDescriptionGenerator,
    generate_pr_description,
)

from vibey.operations.git.sprint_tagger import (
    SprintTag,
    SprintTagger,
    create_sprint_start_tag,
    create_sprint_end_tag,
    list_all_sprint_tags,
)

from vibey.operations.git.git_sync import (
    TaskStateChange,
    SprintStateChange,
    SyncResult,
    GitPrimarySync,
    sync_from_git,
)

from vibey.operations.git.mode_detector import (
    SourceOfTruthMode,
    ModeDetectionResult,
    StrategyValidation,
    ModeDetector,
    detect_source_of_truth_mode,
    validate_git_strategy,
    get_mode_configuration,
)

from vibey.operations.git.error_handler import (
    BackupInfo,
    RepairResult,
    RollbackResult,
    TransactionalUpdate,
    ErrorHandler,
    validate_roadmap,
    repair_roadmap,
    rollback_roadmap,
)

from vibey.operations.git.tag_repair import (
    DanglingTag,
    TagRepairResult,
    RepairSummary,
    TagRepairer,
    find_dangling_tags,
    repair_all_tags,
    move_tag,
)

from vibey.operations.git.merge_checker import (
    TaskStatusChange,
    TaskConflict,
    ConflictResolution,
    MergeCheckResult,
    MergeChecker,
    check_merge,
)

from vibey.operations.git.blocker_enforcer import (
    EnforcementMode,
    BlockerInfo,
    BlockedItem,
    BlockerViolation,
    EnforcementResult,
    BlockerStatus,
    BlockerEnforcer,
    check_commit_blockers,
    get_blocker_status,
    format_blocker_status,
)

__all__ = [
    # Schema types
    "CommitFormat",
    "TaskStatus",
    "TaskReference",
    "SprintReference",
    "TrackReference",
    "CommitMessageParts",
    "ParsedCommit",
    "ParserConfig",
    "RegexPatterns",
    "CommitParserInterface",
    "ParseResult",
    "STATUS_KEYWORDS",
    # Parser implementation
    "CommitParser",
    "analyze_batch",
    # Log analyzer
    "CommitInfo",
    "BranchInfo",
    "TagInfo",
    "AnalysisResult",
    "GitLogAnalyzer",
    "analyze_repository",
    # Velocity calculator
    "TaskMetrics",
    "SprintVelocity",
    "VelocityTrend",
    "VelocityCalculator",
    "quick_sprint_velocity",
    # Tag parser
    "TagType",
    "ParsedTag",
    "TagParser",
    "get_sprint_commits_with_tags",
    "get_task_commits_with_tags",
    # State reconstructor
    "StateSnapshot",
    "StateChange",
    "ProgressPoint",
    "StateReconstructor",
    "get_state_at_ref",
    # Hooks
    "PreCommitHook",
    "CommitMsgHook",
    "ValidationIssue",
    "HookConfig",
    # Status updater
    "StatusUpdate",
    "UpdateResult",
    "TaskStatusUpdater",
    "update_from_commit",
    "update_from_recent_commits",
    # Branch linker
    "BranchType",
    "BranchInfo",
    "BranchLinkInfo",
    "BranchLinker",
    "create_task_branch",
    # PR generator
    "TaskInfo",
    "PRDescriptionGenerator",
    "generate_pr_description",
    # Sprint tagger
    "SprintTag",
    "SprintTagger",
    "create_sprint_start_tag",
    "create_sprint_end_tag",
    "list_all_sprint_tags",
    # Git sync
    "TaskStateChange",
    "SprintStateChange",
    "SyncResult",
    "GitPrimarySync",
    "sync_from_git",
    # Mode detection
    "SourceOfTruthMode",
    "ModeDetectionResult",
    "StrategyValidation",
    "ModeDetector",
    "detect_source_of_truth_mode",
    "validate_git_strategy",
    "get_mode_configuration",
    # Error handling
    "BackupInfo",
    "RepairResult",
    "RollbackResult",
    "TransactionalUpdate",
    "ErrorHandler",
    "validate_roadmap",
    "repair_roadmap",
    "rollback_roadmap",
    # Tag repair
    "DanglingTag",
    "TagRepairResult",
    "RepairSummary",
    "TagRepairer",
    "find_dangling_tags",
    "repair_all_tags",
    "move_tag",
    # Merge checker
    "TaskStatusChange",
    "TaskConflict",
    "ConflictResolution",
    "MergeCheckResult",
    "MergeChecker",
    "check_merge",
    # Blocker enforcer
    "EnforcementMode",
    "BlockerInfo",
    "BlockedItem",
    "BlockerViolation",
    "EnforcementResult",
    "BlockerStatus",
    "BlockerEnforcer",
    "check_commit_blockers",
    "get_blocker_status",
    "format_blocker_status",
]
