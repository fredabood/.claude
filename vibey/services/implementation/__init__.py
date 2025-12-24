"""
Implementation Mode Services - Autonomous task execution loop.

This module provides the core services for the autonomous implementation mode,
which allows AI agents to work through a queue of tasks with minimal human
intervention.

Core Components:
- ImplementationLoop: Main execution loop for autonomous task processing
- TaskSelector: Find the next executable task based on status, dependencies, and priority
- TaskExecutor: Protocol for task execution implementations
- LoopState: Mutable state tracking for execution sessions
- LoopStatus: Enum for execution status (RUNNING, PAUSED, STOPPED, COMPLETED)
- TaskResult: Individual task execution result tracking
- LoopResult: Summary result from an execution loop session
- ImplementConfig: Configuration for the implementation loop
- ExecutionResult: Result from executing a single task

Usage:
    from vibey.services.implementation import (
        ImplementationLoop,
        TaskSelector,
        ImplementConfig,
        TaskExecutor,
        ExecutionResult,
        LoopState,
        LoopStatus,
    )
    from pathlib import Path

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
            return ExecutionResult(success=True, tokens_input=1000, tokens_output=500)

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

from vibey.services.implementation.loop import (
    ExecutionResult,
    ImplementConfig,
    ImplementationLoop,
    LoopResult,
    TaskExecutor,
    run_implementation_loop,
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
    # Executor protocol
    "TaskExecutor",
    "ExecutionResult",
    # Results
    "LoopResult",
    # Task selection
    "TaskSelector",
    # State management
    "LoopState",
    "LoopStatus",
    "TaskResult",
]
