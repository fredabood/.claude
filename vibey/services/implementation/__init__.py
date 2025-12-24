"""
Implementation Mode Services - Autonomous task execution loop.

This module provides the core services for the autonomous implementation mode,
which allows AI agents to work through a queue of tasks with minimal human
intervention.

Core Components:
- ImplementationLoop: Main execution loop for autonomous task processing
- TaskSelector: Find the next executable task based on status, dependencies, and priority
- TaskExecutor: Protocol for task execution implementations
- TaskContextBuilder: Assemble execution context for task implementation
- TaskContext: Complete execution context dataclass
- LoopState: Mutable state tracking for execution sessions
- LoopStatus: Enum for execution status (RUNNING, PAUSED, STOPPED, COMPLETED)
- TaskResult: Individual task execution result tracking
- LoopResult: Summary result from an execution loop session
- ImplementConfig: Configuration for the implementation loop
- ExecutionResult: Detailed result from executing a single task
- ExecutionStatus: Enum for task execution status (SUCCESS, FAILURE, BLOCKED, etc.)
- ExecutionLogger: Structured JSONL logging for execution events
- ExecutionEventType: Event type constants for logging
- ProgressDisplay: Rich terminal output for real-time progress tracking
- ErrorRecovery: Error classification and retry logic
- RecoveryAction: Enum for recovery actions (RETRY, SKIP, STOP, WAIT)
- ErrorSeverity: Enum for error classification (TRANSIENT, PERMANENT)
- BlockedTask: Record of a task blocked due to errors
- TokenBudget: Token budget tracking and enforcement
- BudgetCheck: Enum for budget check results (ALLOWED, WARNING, EXCEEDED)
- CheckpointManager: Git checkpoint creation and rollback support
- Checkpoint: Record of a git checkpoint
- ApprovalGate: Human approval gates for high-risk tasks
- ApprovalResult: Enum for approval decisions (APPROVED, SKIPPED, QUIT, TIMEOUT)
- IntentionalRegressionHandler: Manage acknowledged regressions for deprecation/sunset
- RegressionAcknowledgment: Record of an acknowledged intentional regression
- RegressionReason: Enum for regression reasons (DEPRECATION, SUNSET, BREAKING_CHANGE, etc.)
- SnapshotManager: Capture and manage pre-task criterion state snapshots
- CriterionSnapshot: Collection of criterion states for a task
- CriterionState: State of a single criterion at snapshot time
- CriterionStatus: Enum for criterion evaluation status (MET, NOT_MET, SKIPPED, ERROR)
- CriterionType: Enum for criterion target type classification

Usage:
    from vibey.services.implementation import (
        ImplementationLoop,
        TaskSelector,
        ImplementConfig,
        TaskExecutor,
        ExecutionResult,
        ExecutionStatus,
        LoopState,
        LoopStatus,
    )
    from pathlib import Path
    from datetime import datetime, timezone

    # Configure the loop
    config = ImplementConfig(
        max_tasks=10,
        max_tokens=100000,
        state_path=Path(".vibey/implementation/state.yaml"),
    )

    # Create components
    selector = TaskSelector(roadmap_root=Path(".vibey/roadmap"))

    # Implement TaskExecutor protocol
    class MyExecutor:
        async def execute(self, task) -> ExecutionResult:
            # Execute the task...
            return ExecutionResult(
                task_id=task.id,
                status=ExecutionStatus.SUCCESS,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                tokens_input=1000,
                tokens_output=500,
            )

    executor = MyExecutor()

    # Run the loop
    loop = ImplementationLoop(selector, executor, config)
    result = await loop.run()

    print(f"Completed: {result.tasks_completed}/{result.tasks_attempted}")

    # Or use the convenience function
    from vibey.services.implementation import run_implementation_loop

    result = await run_implementation_loop(
        roadmap_root=Path(".vibey/roadmap"),
        executor=executor,
        config=config,
    )
"""

from vibey.services.implementation.config import (
    ImplementConfig,
    RetryConfig,
    SelectionConfig,
    AgentConfig,
    load_implement_config,
    get_default_config_path,
)
from vibey.services.implementation.context import (
    TaskContext,
    TaskContextBuilder,
)
from vibey.services.implementation.executor import (
    ClaudeTaskExecutor,
)
from vibey.services.implementation.loop import (
    ImplementationLoop,
    LoopResult,
    TaskExecutor,
    run_implementation_loop,
)
from vibey.services.implementation.result import (
    ExecutionResult,
    ExecutionStatus,
)
from vibey.services.implementation.selector import TaskSelector
from vibey.services.implementation.logging import (
    ExecutionLogger,
    ExecutionEventType,
)
from vibey.services.implementation.state import (
    LoopState,
    LoopStatus,
    TaskResult,
)
from vibey.services.implementation.display import ProgressDisplay
from vibey.services.implementation.recovery import (
    BlockedTask,
    ErrorRecovery,
    ErrorSeverity,
    RecoveryAction,
)
from vibey.services.implementation.budget import (
    BudgetCheck,
    TokenBudget,
)
from vibey.services.implementation.checkpoint import (
    Checkpoint,
    CheckpointError,
    CheckpointManager,
    CheckpointNotFoundError,
    GitOperationError,
    NotAGitRepositoryError,
    create_task_checkpoint,
    rollback_task_checkpoint,
    CHECKPOINT_TAG_PREFIX,
    DEFAULT_KEEP_CHECKPOINTS,
)
from vibey.services.implementation.approval import (
    ApprovalGate,
    ApprovalResult,
)
from vibey.services.implementation.acknowledgment import (
    IntentionalRegressionHandler,
    RegressionAcknowledgment,
    RegressionReason,
    DEFAULT_ACKNOWLEDGMENT_EXPIRY_DAYS,
    DEFAULT_STORAGE_PATH as DEFAULT_ACKNOWLEDGMENT_STORAGE_PATH,
)
from vibey.services.implementation.snapshot import (
    CriterionSnapshot,
    CriterionState,
    CriterionStatus,
    CriterionType,
    SnapshotManager,
)
from vibey.services.implementation.dependency_graph import (
    CriterionDependencyGraph,
    CriterionRef,
)
from vibey.services.implementation.regression import (
    Regression,
    RegressionConfig,
    RegressionCriterionState,
    RegressionDetector,
    RegressionPolicy,
    RegressionReport,
    RegressionSnapshot,
)

__all__ = [
    # Main loop
    "ImplementationLoop",
    "run_implementation_loop",
    # Configuration
    "ImplementConfig",
    "RetryConfig",
    "SelectionConfig",
    "AgentConfig",
    "load_implement_config",
    "get_default_config_path",
    # Executor protocol and implementations
    "TaskExecutor",
    "ClaudeTaskExecutor",
    # Context building
    "TaskContext",
    "TaskContextBuilder",
    # Execution results
    "ExecutionResult",
    "ExecutionStatus",
    # Loop results
    "LoopResult",
    # Task selection
    "TaskSelector",
    # State management
    "LoopState",
    "LoopStatus",
    "TaskResult",
    # Logging
    "ExecutionLogger",
    "ExecutionEventType",
    # Display
    "ProgressDisplay",
    # Error recovery
    "ErrorRecovery",
    "RecoveryAction",
    "ErrorSeverity",
    "BlockedTask",
    # Budget enforcement
    "BudgetCheck",
    "TokenBudget",
    # Checkpoint management
    "Checkpoint",
    "CheckpointError",
    "CheckpointManager",
    "CheckpointNotFoundError",
    "GitOperationError",
    "NotAGitRepositoryError",
    "create_task_checkpoint",
    "rollback_task_checkpoint",
    "CHECKPOINT_TAG_PREFIX",
    "DEFAULT_KEEP_CHECKPOINTS",
    # Approval gates
    "ApprovalGate",
    "ApprovalResult",
    # Intentional regression handling
    "IntentionalRegressionHandler",
    "RegressionAcknowledgment",
    "RegressionReason",
    "DEFAULT_ACKNOWLEDGMENT_EXPIRY_DAYS",
    "DEFAULT_ACKNOWLEDGMENT_STORAGE_PATH",
    # Criterion snapshots
    "CriterionSnapshot",
    "CriterionState",
    "CriterionStatus",
    "CriterionType",
    "SnapshotManager",
    # Dependency graph
    "CriterionDependencyGraph",
    "CriterionRef",
    # Regression detection
    "Regression",
    "RegressionConfig",
    "RegressionCriterionState",
    "RegressionDetector",
    "RegressionPolicy",
    "RegressionReport",
    "RegressionSnapshot",
]
