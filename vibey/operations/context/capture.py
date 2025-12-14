"""Context capture for CLI command execution.

This module provides infrastructure for capturing command execution context
and storing it for later retrieval by AI agents.

The captured context includes:
- Command name and arguments
- Execution timestamp and duration
- Input/output data
- Related entity IDs (tasks, sprints, tracks)
- Success/failure status

Usage:
    from vibey.operations.context.capture import CommandContextCapture

    capture = CommandContextCapture()
    capture.start_capture("roadmap start", {"task_id": "01KC..."})

    # ... execute command ...

    capture.end_capture(
        status="success",
        outputs={"new_status": "in_progress"},
        changes=[{"field": "status", "old": "not_started", "new": "in_progress"}],
    )
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class CommandContext:
    """Captured context from a CLI command execution."""

    command: str
    timestamp: str
    duration_ms: int = 0
    status: str = "pending"  # pending | success | error

    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    changes: List[Dict[str, Any]] = field(default_factory=list)

    related: Dict[str, str] = field(default_factory=dict)  # task_id, sprint_id, etc.
    error: Optional[str] = None

    session_id: Optional[str] = None


class CommandContextCapture:
    """Captures context from CLI command execution.

    Usage:
        capture = CommandContextCapture(context_dir)

        # Option 1: Manual start/end
        capture.start_capture("vibey roadmap start", {"task_id": "01KC..."})
        # ... execute command ...
        capture.end_capture(status="success", outputs={...})

        # Option 2: Context manager
        with capture.capture("vibey roadmap start", {"task_id": "01KC..."}):
            # ... execute command ...
            capture.set_outputs({...})
    """

    def __init__(self, context_dir: Optional[Path] = None):
        """Initialize the capture.

        Args:
            context_dir: Base context directory. Defaults to .vibey/context/
        """
        self.context_dir = context_dir or Path(".vibey/context")
        self.commands_dir = self.context_dir / "commands"
        self._current: Optional[CommandContext] = None
        self._start_time: Optional[float] = None

    def _ensure_dirs(self) -> None:
        """Ensure directories exist."""
        self.commands_dir.mkdir(parents=True, exist_ok=True)

    def start_capture(
        self,
        command: str,
        inputs: Optional[Dict[str, Any]] = None,
        related: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Start capturing command context.

        Args:
            command: The command being executed
            inputs: Input arguments/options
            related: Related entity IDs (task_id, sprint_id, etc.)
            session_id: Optional session ID to link
        """
        self._start_time = time.time()
        self._current = CommandContext(
            command=command,
            timestamp=datetime.now(timezone.utc).isoformat(),
            inputs=inputs or {},
            related=related or {},
            session_id=session_id,
        )

    def end_capture(
        self,
        status: str = "success",
        outputs: Optional[Dict[str, Any]] = None,
        changes: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
    ) -> Optional[Path]:
        """End capture and save context.

        Args:
            status: Command execution status
            outputs: Command outputs
            changes: List of changes made
            error: Error message if failed

        Returns:
            Path to saved context file, or None if no capture in progress
        """
        if self._current is None or self._start_time is None:
            return None

        # Calculate duration
        duration_ms = int((time.time() - self._start_time) * 1000)

        # Update context
        self._current.duration_ms = duration_ms
        self._current.status = status
        self._current.outputs = outputs or {}
        self._current.changes = changes or []
        self._current.error = error

        # Save context
        filepath = self._save_context(self._current)

        # Reset state
        self._current = None
        self._start_time = None

        return filepath

    def set_outputs(self, outputs: Dict[str, Any]) -> None:
        """Set outputs during capture (for use with context manager)."""
        if self._current:
            self._current.outputs = outputs

    def add_change(self, field: str, old: Any, new: Any) -> None:
        """Add a change record during capture."""
        if self._current:
            self._current.changes.append({
                "field": field,
                "old": old,
                "new": new,
            })

    def set_related(self, key: str, value: str) -> None:
        """Set a related entity ID during capture."""
        if self._current:
            self._current.related[key] = value

    def _save_context(self, context: CommandContext) -> Path:
        """Save context to file.

        Returns:
            Path to saved file
        """
        self._ensure_dirs()

        # Generate filename from timestamp
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"cmd_{ts}.yaml"
        filepath = self.commands_dir / filename

        data = {"command_context": asdict(context)}
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def capture(
        self,
        command: str,
        inputs: Optional[Dict[str, Any]] = None,
        related: Optional[Dict[str, str]] = None,
    ):
        """Context manager for capturing command context.

        Usage:
            with capture.capture("vibey roadmap start", {"task_id": "01KC..."}):
                # ... execute command ...
                capture.set_outputs({"status": "started"})
        """
        return _CaptureContextManager(self, command, inputs, related)


class _CaptureContextManager:
    """Context manager for command capture."""

    def __init__(
        self,
        capture: CommandContextCapture,
        command: str,
        inputs: Optional[Dict[str, Any]],
        related: Optional[Dict[str, str]],
    ):
        self.capture = capture
        self.command = command
        self.inputs = inputs
        self.related = related
        self._error: Optional[str] = None

    def __enter__(self):
        self.capture.start_capture(
            self.command,
            inputs=self.inputs,
            related=self.related,
        )
        return self.capture

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.capture.end_capture(
                status="error",
                error=str(exc_val),
            )
        else:
            self.capture.end_capture(status="success")
        return False


def capture_command_context(
    command: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    changes: List[Dict[str, Any]],
    related: Dict[str, str],
    status: str = "success",
    error: Optional[str] = None,
    context_dir: Optional[Path] = None,
) -> Optional[Path]:
    """One-shot function to capture and save command context.

    Args:
        command: Command executed
        inputs: Input arguments
        outputs: Output data
        changes: Changes made
        related: Related entity IDs
        status: Execution status
        error: Error message if any
        context_dir: Context directory

    Returns:
        Path to saved context file
    """
    capture = CommandContextCapture(context_dir)
    capture.start_capture(command, inputs, related)
    return capture.end_capture(
        status=status,
        outputs=outputs,
        changes=changes,
        error=error,
    )


def get_recent_command_contexts(
    limit: int = 20,
    context_dir: Optional[Path] = None,
) -> List[CommandContext]:
    """Get recent command contexts.

    Args:
        limit: Maximum number to return
        context_dir: Context directory

    Returns:
        List of CommandContext objects, most recent first
    """
    context_dir = context_dir or Path(".vibey/context")
    commands_dir = context_dir / "commands"

    if not commands_dir.exists():
        return []

    # Get all command files, sorted by modification time
    files = sorted(
        commands_dir.glob("cmd_*.yaml"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:limit]

    contexts = []
    for f in files:
        try:
            with open(f) as fp:
                data = yaml.safe_load(fp)
            ctx_data = data.get("command_context", {})
            contexts.append(CommandContext(**{
                k: v for k, v in ctx_data.items()
                if k in CommandContext.__dataclass_fields__
            }))
        except Exception:
            continue

    return contexts
