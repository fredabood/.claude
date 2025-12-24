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

from vibey.services.implementation.context import (
    TaskContext,
    TaskContextBuilder,
)
from vibey.services.implementation.executor import (
    ClaudeTaskExecutor,
)
from vibey.services.implementation.loop import (
    ImplementConfig,
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
from vibey.services.implementation.state import (
    LoopState,
    LoopStatus,
    TaskResult,
)

__all__ = [
    # Main loop
    "ImplementationLoop",
    "run_implementation_loop",
    # Configuration
    "ImplementConfig",
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
]
