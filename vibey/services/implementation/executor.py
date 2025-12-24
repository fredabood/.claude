"""
TaskExecutor - Execute tasks via Claude Code agent subprocess.

This module provides the concrete implementation of the TaskExecutor protocol
for running tasks through the Claude Code CLI agent.

Key Features:
- Spawns Claude Code agent as subprocess
- Streams output for real-time monitoring
- Handles timeouts and cancellation
- Parses token usage from agent output
- Graceful error handling

Usage:
    from vibey.services.implementation import ClaudeTaskExecutor
    from vibey.services.implementation.loop import ImplementConfig
    from pathlib import Path

    config = ImplementConfig(max_tasks=5)
    executor = ClaudeTaskExecutor(config, roadmap_root=Path(".vibey/roadmap"))

    result = await executor.execute(task)
    print(f"Success: {result.success}")
    print(f"Tokens: {result.tokens_input} input, {result.tokens_output} output")

Agent Invocation:
    claude --print --dangerously-skip-permissions \\
        --system-prompt "..." \\
        "Execute task: {task_description}"

Design Reference:
- Implementation Mode Track Sprint 2
- Task N5: TaskExecutor implementation
"""

import asyncio
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.services.implementation.context import TaskContext, TaskContextBuilder
from vibey.services.implementation.loop import ExecutionResult, ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# TASK EXECUTOR
# =============================================================================


class ClaudeTaskExecutor:
    """
    Execute tasks via Claude Code agent subprocess.

    This is the concrete implementation of the TaskExecutor protocol
    that spawns the Claude Code CLI to execute tasks.

    Attributes:
        config: ImplementConfig with execution parameters
        context_builder: TaskContextBuilder for assembling execution context
        agent_binary: Path to the Claude Code CLI binary
        default_timeout: Default timeout in seconds

    Example:
        >>> config = ImplementConfig(max_tasks=10)
        >>> executor = ClaudeTaskExecutor(config, Path(".vibey/roadmap"))
        >>> result = await executor.execute(task)
        >>> if result.success:
        ...     print(f"Task completed with {len(result.commits)} commits")
    """

    # Agent binary name
    AGENT_BINARY = "claude"

    # Default timeout (10 minutes)
    DEFAULT_TIMEOUT = 600

    # Regex patterns for parsing output
    TOKEN_PATTERN = re.compile(
        r"(?:tokens?|usage)[:\s]*"
        r"(?:input[:\s]*)?(\d+)[,\s]*"
        r"(?:output[:\s]*)?(\d+)",
        re.IGNORECASE,
    )
    COMMIT_PATTERN = re.compile(r"\b([a-f0-9]{7,40})\b")
    ERROR_PATTERNS = [
        re.compile(r"error[:\s]+(.+)", re.IGNORECASE),
        re.compile(r"failed[:\s]+(.+)", re.IGNORECASE),
        re.compile(r"exception[:\s]+(.+)", re.IGNORECASE),
    ]

    def __init__(
        self,
        config: ImplementConfig,
        roadmap_root: Optional[Path] = None,
        working_directory: Optional[Path] = None,
    ):
        """
        Initialize the executor.

        Args:
            config: ImplementConfig with execution parameters
            roadmap_root: Path to .vibey/roadmap directory for context building
            working_directory: Optional working directory override for agent execution
        """
        self.config = config
        self.working_directory = working_directory

        # Initialize context builder if roadmap root provided
        if roadmap_root is not None:
            self.context_builder: Optional[TaskContextBuilder] = TaskContextBuilder(
                roadmap_root
            )
        else:
            self.context_builder = None

        self._verify_agent_binary()

    def _verify_agent_binary(self) -> None:
        """Verify the Claude Code CLI binary is available."""
        binary_path = shutil.which(self.AGENT_BINARY)
        if binary_path is None:
            logger.warning(
                f"Claude Code CLI '{self.AGENT_BINARY}' not found in PATH. "
                "Task execution will fail."
            )
        else:
            logger.debug(f"Found Claude Code CLI at: {binary_path}")

    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================

    async def execute(self, task: HierarchicalTicket) -> ExecutionResult:
        """
        Execute a task via Claude Code agent subprocess.

        Steps:
        1. Prepare agent command with context
        2. Spawn subprocess with proper environment
        3. Stream output for monitoring
        4. Wait for completion or timeout
        5. Parse result and return ExecutionResult

        Args:
            task: The HierarchicalTicket to execute

        Returns:
            ExecutionResult with success status and resource usage
        """
        # Build context from task
        context = self._build_context(task)

        logger.info(f"Executing task {task.id}: {task.name}")

        try:
            # Spawn the agent subprocess
            process = await self.spawn_agent(context)

            # Determine timeout
            timeout = context.max_tokens if context.max_tokens else self.DEFAULT_TIMEOUT

            # Stream and capture output
            output = await self.stream_output(process, timeout)

            # Wait for process to complete
            returncode = process.returncode
            if returncode is None:
                # Process didn't complete - likely killed
                returncode = -1

            # Parse the result
            result = self.parse_result(output, returncode)

            logger.info(
                f"Task {task.id} {'completed' if result.success else 'failed'} "
                f"(exit={returncode}, tokens={result.tokens_input}+{result.tokens_output})"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Task {task.id} timed out after {self.DEFAULT_TIMEOUT}s")
            return ExecutionResult(
                success=False,
                error_message=f"Task execution timed out after {self.DEFAULT_TIMEOUT} seconds",
            )

        except asyncio.CancelledError:
            logger.info(f"Task {task.id} was cancelled")
            raise  # Re-raise to allow proper cancellation handling

        except FileNotFoundError:
            logger.error(f"Claude Code CLI '{self.AGENT_BINARY}' not found")
            return ExecutionResult(
                success=False,
                error_message=f"Claude Code CLI '{self.AGENT_BINARY}' not found in PATH",
            )

        except Exception as e:
            logger.exception(f"Task {task.id} failed with error: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
            )

    def _build_context(self, task: HierarchicalTicket) -> TaskContext:
        """
        Build execution context for a task.

        Uses TaskContextBuilder if available, otherwise creates a basic context.

        Args:
            task: The task to build context for

        Returns:
            TaskContext with execution context
        """
        if self.context_builder is not None:
            return self.context_builder.build_context(task)

        # Fallback: create minimal context if no builder configured
        return TaskContext(
            task=task,
            system_prompt=self._build_fallback_system_prompt(task),
            task_description=task.description or task.name,
            acceptance_criteria=[c.description for c in task.criteria],
            relevant_files=[],
            parent_context=None,
            max_tokens=None,
        )

    def _build_fallback_system_prompt(self, task: HierarchicalTicket) -> str:
        """Build a basic system prompt when no context builder is available."""
        lines = [
            "You are an autonomous coding agent executing a development task.",
            "Follow the task instructions precisely.",
            "Make incremental commits for significant changes.",
            "Report any blockers or issues clearly.",
            "",
            f"Task ID: {task.id}",
            f"Task Name: {task.name}",
        ]

        if task.parent_ref:
            lines.append(f"Parent ID: {task.parent_ref}")

        if task.description:
            lines.append("")
            lines.append("Description:")
            lines.append(task.description)

        return "\n".join(lines)

    # =========================================================================
    # SUBPROCESS MANAGEMENT
    # =========================================================================

    async def spawn_agent(self, context: TaskContext) -> asyncio.subprocess.Process:
        """
        Spawn Claude Code agent with task prompt.

        Args:
            context: TaskContext with execution parameters

        Returns:
            The spawned subprocess

        Raises:
            FileNotFoundError: If claude binary not found
        """
        # Build command arguments
        cmd = [
            self.AGENT_BINARY,
            "--print",  # Print output to stdout
            "--dangerously-skip-permissions",  # Skip permission prompts
        ]

        # Add system prompt
        if context.system_prompt:
            cmd.extend(["--system-prompt", context.system_prompt])

        # Add the user prompt (task description)
        cmd.append(context.task_description)

        # Build environment
        env = os.environ.copy()

        # Determine working directory
        cwd = self.working_directory
        if cwd is None:
            cwd = Path.cwd()

        logger.debug(f"Spawning agent: {' '.join(cmd[:3])}... (in {cwd})")

        # Spawn the subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        return process

    async def stream_output(
        self,
        process: asyncio.subprocess.Process,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ) -> str:
        """
        Stream and capture agent output.

        Args:
            process: The running subprocess
            timeout_seconds: Maximum time to wait

        Returns:
            Complete output as a string

        Raises:
            asyncio.TimeoutError: If process doesn't complete in time
        """
        output_lines: List[str] = []

        async def read_stream(
            stream: Optional[asyncio.StreamReader],
            prefix: str = "",
        ) -> None:
            """Read from a stream and log lines."""
            if stream is None:
                return

            while True:
                line = await stream.readline()
                if not line:
                    break

                decoded = line.decode("utf-8", errors="replace").rstrip()
                output_lines.append(decoded)

                # Log output in real-time
                if prefix:
                    logger.debug(f"{prefix}: {decoded}")
                else:
                    logger.debug(decoded)

        try:
            # Create tasks for reading stdout and stderr
            stdout_task = asyncio.create_task(read_stream(process.stdout, "AGENT"))
            stderr_task = asyncio.create_task(read_stream(process.stderr, "AGENT-ERR"))

            # Wait for both streams with timeout
            await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task),
                timeout=timeout_seconds,
            )

            # Wait for process to finish
            await asyncio.wait_for(
                process.wait(),
                timeout=10,  # Extra time for process cleanup
            )

        except asyncio.TimeoutError:
            # Kill the process on timeout
            logger.warning("Process timed out, terminating...")
            process.terminate()

            # Give it a moment to terminate gracefully
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                # Force kill if still running
                logger.warning("Process didn't terminate, killing...")
                process.kill()
                await process.wait()

            raise

        except asyncio.CancelledError:
            # Kill the process on cancellation
            logger.info("Task cancelled, terminating process...")
            process.terminate()

            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

            raise

        return "\n".join(output_lines)

    # =========================================================================
    # RESULT PARSING
    # =========================================================================

    def parse_result(self, output: str, returncode: int) -> ExecutionResult:
        """
        Parse agent output to determine success/failure.

        Args:
            output: Complete agent output
            returncode: Process exit code

        Returns:
            ExecutionResult with parsed information
        """
        # Determine success based on return code
        success = returncode == 0

        # Parse token usage
        tokens_input, tokens_output = self._parse_tokens(output)

        # Parse commits
        commits = self._parse_commits(output)

        # Extract error message if failed
        error_message = None
        if not success:
            error_message = self._extract_error(output, returncode)

        # Build metadata
        metadata: Dict[str, Any] = {
            "returncode": returncode,
            "output_length": len(output),
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        }

        return ExecutionResult(
            success=success,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            commits=commits,
            error_message=error_message,
            metadata=metadata,
        )

    def _parse_tokens(self, output: str) -> Tuple[int, int]:
        """
        Extract token usage from output.

        Looks for patterns like:
        - "tokens: 1000, 500"
        - "input: 1000, output: 500"
        - "Token usage: input 1000, output 500"

        Args:
            output: Agent output text

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        # Try to find token usage pattern
        match = self.TOKEN_PATTERN.search(output)
        if match:
            try:
                input_tokens = int(match.group(1))
                output_tokens = int(match.group(2))
                return input_tokens, output_tokens
            except (ValueError, IndexError):
                pass

        # Default to 0 if not found
        return 0, 0

    def _parse_commits(self, output: str) -> List[str]:
        """
        Extract git commit SHAs from output.

        Looks for patterns that look like commit hashes (7-40 hex chars).
        Filters to only include likely commit references.

        Args:
            output: Agent output text

        Returns:
            List of commit SHAs
        """
        commits: List[str] = []

        # Look for lines that mention commits
        commit_keywords = ["commit", "committed", "sha", "hash"]

        for line in output.split("\n"):
            line_lower = line.lower()

            # Only parse lines that seem to mention commits
            if any(keyword in line_lower for keyword in commit_keywords):
                matches = self.COMMIT_PATTERN.findall(line)
                for match in matches:
                    # Filter out common false positives
                    if len(match) >= 7 and match not in commits:
                        commits.append(match)

        return commits

    def _extract_error(self, output: str, returncode: int) -> str:
        """
        Extract error message from output.

        Args:
            output: Agent output text
            returncode: Process exit code

        Returns:
            Error message string
        """
        # Look for explicit error messages
        for pattern in self.ERROR_PATTERNS:
            match = pattern.search(output)
            if match:
                return match.group(1).strip()

        # Check last few lines for error context
        lines = output.strip().split("\n")
        if lines:
            # Take last non-empty line as error context
            for line in reversed(lines):
                line = line.strip()
                if line:
                    return f"Process exited with code {returncode}: {line[:200]}"

        return f"Process exited with code {returncode}"


# =============================================================================
# EXPORTS
# =============================================================================

# Export ClaudeTaskExecutor as TaskExecutor for convenience
TaskExecutor = ClaudeTaskExecutor

__all__ = [
    "TaskExecutor",
    "ClaudeTaskExecutor",
]
