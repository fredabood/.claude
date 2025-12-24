"""
Agent spawner for parallel task execution.

This module provides the AgentSpawner class for spawning and managing
multiple Claude Code agent processes in parallel. It enables concurrent
task execution with proper lifecycle management.

Key Features:
- Spawn multiple Claude Code agents concurrently
- Support for git branch isolation per agent
- Process timeout and cancellation handling
- Output buffering per agent for logging/debugging
- Configurable concurrency limits

Usage:
    from vibey.services.implementation import AgentSpawner, ImplementConfig
    from pathlib import Path

    config = ImplementConfig(max_tasks=5)
    spawner = AgentSpawner(config)

    # Spawn agents for a parallel group
    agents = await spawner.spawn_agents(group)

    # Wait for all to complete
    results = await spawner.wait_for_all(agents, timeout=600)

    # Or cancel if needed
    await spawner.cancel_all(agents)

Design Reference:
- Implementation Mode Track Sprint 3
- Task: Implement AgentSpawner for parallel execution
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ulid import ULID

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.config import ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class AgentStatus(Enum):
    """Status of an agent process."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class TaskContext:
    """
    Context provided to each spawned agent.

    Contains all information needed for a Claude Code agent to execute
    a task, including prompts, working directory, and environment.

    Attributes:
        task: The HierarchicalTicket to execute
        system_prompt: System prompt for the agent
        task_prompt: The main task/user prompt
        working_directory: Directory to run the agent in
        environment: Additional environment variables
        timeout_seconds: Optional timeout for this specific task
    """

    task: "HierarchicalTicket"
    system_prompt: str
    task_prompt: str
    working_directory: Path
    environment: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: Optional[int] = None


@dataclass
class ExecutionResult:
    """
    Result from agent execution.

    Simplified result type for spawner operations.
    Can be converted to/from the full ExecutionResult in result.py.
    """

    task_id: str
    success: bool
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    branch: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class ParallelGroup:
    """
    A group of tasks that can be executed in parallel.

    Tasks in a parallel group have no dependencies on each other
    and can safely run concurrently.

    Attributes:
        tasks: List of tasks to execute in parallel
        group_id: Optional identifier for this group
        max_concurrent: Optional override for max concurrent agents
    """

    tasks: List["HierarchicalTicket"]
    group_id: Optional[str] = None
    max_concurrent: Optional[int] = None


@dataclass
class AgentProcess:
    """
    Represents a running agent process.

    Tracks the lifecycle of a spawned Claude Code agent including
    its process, output, and status.

    Attributes:
        agent_id: Unique identifier for this agent (ULID)
        task_id: ID of the task being executed
        process: The asyncio subprocess (None if not yet spawned)
        started_at: When the process was started
        completed_at: When the process completed
        branch: Git branch name if using branch isolation
        status: Current status of the agent
        output_buffer: Lines of output collected from the process
        return_code: Process exit code when completed
    """

    agent_id: str
    task_id: str
    process: Optional[asyncio.subprocess.Process] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    branch: Optional[str] = None
    status: AgentStatus = AgentStatus.PENDING
    output_buffer: List[str] = field(default_factory=list)
    return_code: Optional[int] = None

    async def wait(self) -> ExecutionResult:
        """
        Wait for process completion and return result.

        Returns:
            ExecutionResult with process outcome

        Raises:
            RuntimeError: If process was not started
        """
        if self.process is None:
            raise RuntimeError(f"Agent {self.agent_id} was not started")

        # Wait for the process to complete
        await self.process.wait()
        self.completed_at = datetime.now(timezone.utc)
        self.return_code = self.process.returncode

        # Determine status based on return code
        if self.return_code == 0:
            self.status = AgentStatus.COMPLETED
            success = True
            error_message = None
        else:
            self.status = AgentStatus.FAILED
            success = False
            error_message = f"Process exited with code {self.return_code}"

        return ExecutionResult(
            task_id=self.task_id,
            success=success,
            return_code=self.return_code,
            stdout=self.get_output(),
            stderr="",  # Stderr is merged into output_buffer
            error_message=error_message,
            started_at=self.started_at,
            completed_at=self.completed_at,
            branch=self.branch,
        )

    async def cancel(self) -> None:
        """
        Send cancel signal to agent.

        Attempts graceful termination first, then force kills if needed.
        """
        if self.process is None:
            return

        if self.process.returncode is not None:
            # Process already finished
            return

        logger.info(f"Cancelling agent {self.agent_id} (task {self.task_id})")
        self.status = AgentStatus.CANCELLED

        try:
            # Try graceful termination first
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if termination didn't work
                logger.warning(
                    f"Agent {self.agent_id} didn't terminate gracefully, killing"
                )
                self.process.kill()
                await self.process.wait()
        except ProcessLookupError:
            # Process already exited
            pass

        self.completed_at = datetime.now(timezone.utc)
        self.return_code = self.process.returncode

    def get_output(self) -> str:
        """
        Get current output buffer as a single string.

        Returns:
            All captured output lines joined with newlines
        """
        return "\n".join(self.output_buffer)

    def append_output(self, line: str) -> None:
        """
        Append a line to the output buffer.

        Args:
            line: Output line to append
        """
        self.output_buffer.append(line)


# =============================================================================
# AGENT SPAWNER
# =============================================================================


class AgentSpawner:
    """
    Spawns and manages parallel agent processes.

    This class handles the lifecycle of multiple Claude Code agent
    processes running in parallel, including spawning, monitoring,
    and cleanup.

    Attributes:
        config: ImplementConfig with execution parameters
        max_concurrent: Maximum number of concurrent agents
        active_agents: Dictionary of currently active agents by ID
        use_branch_isolation: Whether to create separate git branches

    Example:
        >>> config = ImplementConfig(max_tasks=10)
        >>> spawner = AgentSpawner(config)
        >>> agents = await spawner.spawn_agents(group)
        >>> results = await spawner.wait_for_all(agents)
    """

    # Claude Code CLI binary name
    AGENT_BINARY = "claude"

    # Default settings
    DEFAULT_MAX_CONCURRENT = 3
    DEFAULT_TIMEOUT = 600  # 10 minutes

    def __init__(
        self,
        config: "ImplementConfig",
        use_branch_isolation: bool = False,
        working_directory: Optional[Path] = None,
    ):
        """
        Initialize the spawner.

        Args:
            config: ImplementConfig with execution parameters
            use_branch_isolation: Create separate git branch per agent
            working_directory: Base working directory for agents
        """
        self.config = config
        self.max_concurrent = getattr(
            config, "max_concurrent_agents", self.DEFAULT_MAX_CONCURRENT
        )
        self.active_agents: Dict[str, AgentProcess] = {}
        self.use_branch_isolation = use_branch_isolation
        self.working_directory = working_directory or Path.cwd()

        # Verify Claude CLI is available
        self._verify_agent_binary()

    def _verify_agent_binary(self) -> None:
        """Verify the Claude Code CLI binary is available."""
        binary_path = shutil.which(self.AGENT_BINARY)
        if binary_path is None:
            logger.warning(
                f"Claude Code CLI '{self.AGENT_BINARY}' not found in PATH. "
                "Agent spawning will fail."
            )
        else:
            logger.debug(f"Found Claude Code CLI at: {binary_path}")

    # =========================================================================
    # SPAWNING
    # =========================================================================

    async def spawn_agents(
        self,
        group: ParallelGroup,
    ) -> List[AgentProcess]:
        """
        Spawn agents for all tasks in parallel group.

        Respects max_concurrent limit using a semaphore to throttle
        how many agents run simultaneously.

        Args:
            group: ParallelGroup containing tasks to execute

        Returns:
            List of AgentProcess objects for each spawned agent
        """
        if not group.tasks:
            return []

        # Determine concurrency limit
        max_concurrent = group.max_concurrent or self.max_concurrent
        semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"Spawning agents for {len(group.tasks)} tasks "
            f"(max concurrent: {max_concurrent})"
        )

        async def spawn_with_semaphore(task: "HierarchicalTicket") -> AgentProcess:
            async with semaphore:
                context = self._build_context(task)
                return await self.spawn_agent(task, context)

        # Spawn all agents (semaphore will limit concurrency)
        agents = await asyncio.gather(
            *[spawn_with_semaphore(task) for task in group.tasks],
            return_exceptions=True,
        )

        # Filter out any exceptions and log them
        valid_agents: List[AgentProcess] = []
        for i, result in enumerate(agents):
            if isinstance(result, Exception):
                task = group.tasks[i]
                logger.error(f"Failed to spawn agent for task {task.id}: {result}")
            else:
                valid_agents.append(result)

        return valid_agents

    async def spawn_agent(
        self,
        task: "HierarchicalTicket",
        context: TaskContext,
    ) -> AgentProcess:
        """
        Spawn single Claude Code agent for task.

        Uses: claude --print --dangerously-skip-permissions ...

        Args:
            task: The HierarchicalTicket to execute
            context: TaskContext with execution parameters

        Returns:
            AgentProcess representing the spawned agent

        Raises:
            FileNotFoundError: If Claude CLI not found
            RuntimeError: If branch creation fails
        """
        # Generate unique agent ID
        agent_id = str(ULID())

        # Create agent process object
        agent = AgentProcess(
            agent_id=agent_id,
            task_id=task.id,
            status=AgentStatus.PENDING,
        )

        logger.info(f"Spawning agent {agent_id} for task {task.id}: {task.name}")

        # Optional branch isolation
        branch_name: Optional[str] = None
        if self.use_branch_isolation:
            branch_name = f"implement/{task.id}"
            await self._create_branch(branch_name, context.working_directory)
            agent.branch = branch_name

        # Build command arguments
        cmd = self._build_command(context)

        # Build environment
        env = os.environ.copy()
        env.update(context.environment)

        try:
            # Spawn the subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
                cwd=context.working_directory,
                env=env,
            )

            agent.process = process
            agent.started_at = datetime.now(timezone.utc)
            agent.status = AgentStatus.RUNNING

            # Register as active
            self.active_agents[agent_id] = agent

            # Start output reader task
            asyncio.create_task(self._read_output(agent))

            logger.debug(
                f"Agent {agent_id} started (PID: {process.pid}) "
                f"in {context.working_directory}"
            )

            return agent

        except FileNotFoundError:
            agent.status = AgentStatus.FAILED
            raise FileNotFoundError(
                f"Claude Code CLI '{self.AGENT_BINARY}' not found in PATH"
            )
        except Exception as e:
            agent.status = AgentStatus.FAILED
            raise RuntimeError(f"Failed to spawn agent: {e}") from e

    def _build_command(self, context: TaskContext) -> List[str]:
        """
        Build the Claude CLI command.

        Args:
            context: TaskContext with prompts

        Returns:
            List of command arguments
        """
        cmd = [
            self.AGENT_BINARY,
            "--print",  # Print output to stdout
            "--dangerously-skip-permissions",  # Skip permission prompts
        ]

        # Add system prompt
        if context.system_prompt:
            cmd.extend(["--system-prompt", context.system_prompt])

        # Add model from config if available
        if hasattr(self.config, "agent") and hasattr(self.config.agent, "model"):
            cmd.extend(["--model", self.config.agent.model])

        # Add max turns if configured
        if hasattr(self.config, "agent") and hasattr(self.config.agent, "max_turns"):
            cmd.extend(["--max-turns", str(self.config.agent.max_turns)])

        # Add the task prompt as the user message
        cmd.append(context.task_prompt)

        return cmd

    def _build_context(self, task: "HierarchicalTicket") -> TaskContext:
        """
        Build execution context for a task.

        Args:
            task: The task to build context for

        Returns:
            TaskContext with execution parameters
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(task)

        # Build task prompt
        task_prompt = self._build_task_prompt(task)

        # Determine timeout
        timeout = getattr(self.config, "timeout_per_task", self.DEFAULT_TIMEOUT)

        return TaskContext(
            task=task,
            system_prompt=system_prompt,
            task_prompt=task_prompt,
            working_directory=self.working_directory,
            timeout_seconds=timeout,
        )

    def _build_system_prompt(self, task: "HierarchicalTicket") -> str:
        """Build system prompt for the agent."""
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

        return "\n".join(lines)

    def _build_task_prompt(self, task: "HierarchicalTicket") -> str:
        """Build the task prompt for the agent."""
        lines = [f"Execute task: {task.name}"]

        if task.description:
            lines.append("")
            lines.append("Description:")
            lines.append(task.description)

        # Add acceptance criteria
        if task.criteria:
            lines.append("")
            lines.append("Acceptance Criteria:")
            for i, criterion in enumerate(task.criteria, 1):
                lines.append(f"{i}. {criterion.description}")

        return "\n".join(lines)

    async def _create_branch(self, branch_name: str, working_dir: Path) -> None:
        """
        Create and checkout a git branch for isolation.

        Args:
            branch_name: Name for the new branch
            working_dir: Working directory with git repo

        Raises:
            RuntimeError: If git operation fails
        """
        logger.debug(f"Creating branch: {branch_name}")

        try:
            # Create and checkout the branch
            process = await asyncio.create_subprocess_exec(
                "git",
                "checkout",
                "-b",
                branch_name,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Branch might already exist, try checking out
                process = await asyncio.create_subprocess_exec(
                    "git",
                    "checkout",
                    branch_name,
                    cwd=working_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.wait()

                if process.returncode != 0:
                    raise RuntimeError(
                        f"Failed to create/checkout branch {branch_name}: "
                        f"{stderr.decode()}"
                    )

            logger.debug(f"Branch {branch_name} ready")

        except FileNotFoundError:
            raise RuntimeError("git command not found")

    async def _read_output(self, agent: AgentProcess) -> None:
        """
        Read and buffer output from agent process.

        Runs as a background task, reading lines from the process
        stdout and storing them in the agent's output buffer.

        Args:
            agent: AgentProcess to read output from
        """
        if agent.process is None or agent.process.stdout is None:
            return

        try:
            while True:
                line = await agent.process.stdout.readline()
                if not line:
                    break

                decoded = line.decode("utf-8", errors="replace").rstrip()
                agent.append_output(decoded)

                # Log if configured
                if hasattr(self.config, "agent") and getattr(
                    self.config.agent, "print_output", False
                ):
                    logger.debug(f"[{agent.agent_id[:8]}] {decoded}")

        except Exception as e:
            logger.warning(f"Error reading output from agent {agent.agent_id}: {e}")

    # =========================================================================
    # WAITING AND CANCELLATION
    # =========================================================================

    async def wait_for_all(
        self,
        agents: List[AgentProcess],
        timeout: Optional[int] = None,
    ) -> List[ExecutionResult]:
        """
        Wait for all agents to complete.

        Args:
            agents: List of AgentProcess objects to wait for
            timeout: Optional timeout in seconds for all agents

        Returns:
            List of ExecutionResult objects, one per agent
        """
        if not agents:
            return []

        timeout = timeout or self.DEFAULT_TIMEOUT

        logger.info(f"Waiting for {len(agents)} agents (timeout: {timeout}s)")

        async def wait_single(agent: AgentProcess) -> ExecutionResult:
            """Wait for a single agent with timeout handling."""
            try:
                return await asyncio.wait_for(
                    agent.wait(),
                    timeout=agent.started_at
                    and timeout
                    or timeout,  # Use task-specific or global timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Agent {agent.agent_id} timed out")
                agent.status = AgentStatus.TIMEOUT
                await agent.cancel()
                return ExecutionResult(
                    task_id=agent.task_id,
                    success=False,
                    error_message=f"Agent timed out after {timeout} seconds",
                    started_at=agent.started_at,
                    completed_at=datetime.now(timezone.utc),
                    branch=agent.branch,
                )
            except asyncio.CancelledError:
                logger.info(f"Wait for agent {agent.agent_id} was cancelled")
                await agent.cancel()
                return ExecutionResult(
                    task_id=agent.task_id,
                    success=False,
                    error_message="Agent was cancelled",
                    started_at=agent.started_at,
                    completed_at=datetime.now(timezone.utc),
                    branch=agent.branch,
                )

        # Wait for all agents concurrently
        results = await asyncio.gather(
            *[wait_single(agent) for agent in agents],
            return_exceptions=True,
        )

        # Process results
        final_results: List[ExecutionResult] = []
        for i, result in enumerate(results):
            agent = agents[i]

            if isinstance(result, Exception):
                logger.error(f"Agent {agent.agent_id} raised exception: {result}")
                final_results.append(
                    ExecutionResult(
                        task_id=agent.task_id,
                        success=False,
                        error_message=str(result),
                        started_at=agent.started_at,
                        completed_at=datetime.now(timezone.utc),
                        branch=agent.branch,
                    )
                )
            else:
                final_results.append(result)

            # Remove from active agents
            if agent.agent_id in self.active_agents:
                del self.active_agents[agent.agent_id]

        return final_results

    async def cancel_all(self, agents: List[AgentProcess]) -> None:
        """
        Cancel all running agents.

        Args:
            agents: List of AgentProcess objects to cancel
        """
        if not agents:
            return

        running = [a for a in agents if a.status == AgentStatus.RUNNING]
        if not running:
            return

        logger.info(f"Cancelling {len(running)} running agents")

        # Cancel all agents concurrently
        await asyncio.gather(
            *[agent.cancel() for agent in running],
            return_exceptions=True,
        )

        # Remove from active agents
        for agent in agents:
            if agent.agent_id in self.active_agents:
                del self.active_agents[agent.agent_id]

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """
        Get status of specific agent.

        Args:
            agent_id: The agent ID to look up

        Returns:
            AgentStatus of the agent, or PENDING if not found
        """
        agent = self.active_agents.get(agent_id)
        if agent is None:
            return AgentStatus.PENDING
        return agent.status

    def get_active_count(self) -> int:
        """
        Get count of currently running agents.

        Returns:
            Number of agents with RUNNING status
        """
        return sum(
            1 for a in self.active_agents.values() if a.status == AgentStatus.RUNNING
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AgentStatus",
    # Data classes
    "TaskContext",
    "ExecutionResult",
    "ParallelGroup",
    "AgentProcess",
    # Main class
    "AgentSpawner",
]
