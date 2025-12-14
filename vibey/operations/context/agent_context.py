"""Agent context loading for AI-assisted development.

This module provides automatic context loading for AI agents working on tasks.
It aggregates relevant context from multiple sources:
- Current task context
- Sprint context and planning documents
- Recent session history
- Recent decisions
- Project discovery output

Usage:
    from vibey.operations.context.agent_context import AgentContextLoader

    loader = AgentContextLoader()

    # Load context for a specific task
    context = loader.load_for_task("01KC...")
    prompt_context = context.format_for_claude()

    # Load context for current session
    context = loader.load_for_session()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .readers import (
    ContextLoader,
    AgentContext,
    SessionContextReader,
    TaskContextReader,
    DecisionContextReader,
    SprintContextReader,
)
from .writers import SessionContext, TaskContext, DecisionContext, SprintContext


@dataclass
class EnhancedAgentContext(AgentContext):
    """Extended agent context with additional fields for AI work.

    Extends the base AgentContext with:
    - Command history from recent context captures
    - Files recently modified
    - Blockers and dependencies
    - Recommended next actions
    """

    command_history: List[Dict[str, Any]] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def format_for_claude(self) -> str:
        """Format context for inclusion in Claude prompts.

        Returns comprehensive markdown-formatted context.
        """
        sections = []

        # Header
        sections.append("# Agent Context")
        sections.append(f"*Generated: {datetime.now(timezone.utc).isoformat()}*")
        sections.append("")

        # Current Task
        if self.task:
            sections.append("## Current Task")
            sections.append(f"**{self.task.title}**")
            sections.append("")
            if self.task.description:
                sections.append(f"{self.task.description}")
                sections.append("")
            sections.append(f"- Task ID: `{self.task.task_id}`")
            sections.append(f"- Sprint: `{self.task.sprint_id}`")
            sections.append(f"- Track: `{self.task.track_id}`")

            if self.task.notes:
                sections.append("")
                sections.append("### Notes")
                sections.append(self.task.notes)

            if self.task.decisions:
                sections.append("")
                sections.append("### Decisions Made")
                for decision in self.task.decisions:
                    sections.append(f"- {decision}")

        # Sprint Plan
        if self.sprint_plan:
            sections.append("")
            sections.append("## Sprint Plan")
            # Truncate if too long
            plan_preview = self.sprint_plan
            if len(plan_preview) > 2000:
                plan_preview = plan_preview[:2000] + "\n\n...(truncated, see full plan in sprint context)"
            sections.append(plan_preview)

        # Blockers
        if self.blockers:
            sections.append("")
            sections.append("## Blockers")
            for blocker in self.blockers:
                sections.append(f"- **{blocker.get('type', 'Unknown')}**: {blocker.get('description', '')}")

        # Dependencies
        if self.dependencies:
            sections.append("")
            sections.append("## Dependencies")
            for dep in self.dependencies:
                sections.append(f"- {dep}")

        # Recent Sessions
        if self.recent_sessions:
            sections.append("")
            sections.append(f"## Recent Sessions ({len(self.recent_sessions)})")
            for session in self.recent_sessions[:3]:
                sections.append(f"- `{session.id}`: {session.type} ({session.status})")
                if session.goals:
                    goals_str = ", ".join(session.goals[:3])
                    if len(session.goals) > 3:
                        goals_str += f" (+{len(session.goals) - 3} more)"
                    sections.append(f"  Goals: {goals_str}")

        # Recent Decisions
        if self.recent_decisions:
            sections.append("")
            sections.append(f"## Recent Decisions ({len(self.recent_decisions)})")
            for decision in self.recent_decisions[:5]:
                sections.append(f"- **{decision.title}** ({decision.status}) - {decision.date}")

        # Command History
        if self.command_history:
            sections.append("")
            sections.append(f"## Recent Commands ({len(self.command_history)})")
            for cmd in self.command_history[:10]:
                status_icon = "+" if cmd.get("status") == "success" else "x"
                sections.append(f"- [{status_icon}] `{cmd.get('command', 'unknown')}` ({cmd.get('duration_ms', 0)}ms)")

        # Files Modified
        if self.files_modified:
            sections.append("")
            sections.append(f"## Files Modified ({len(self.files_modified)})")
            for f in self.files_modified[:20]:
                sections.append(f"- `{f}`")
            if len(self.files_modified) > 20:
                sections.append(f"- ... and {len(self.files_modified) - 20} more")

        # Project Discovery
        if self.discovery:
            sections.append("")
            sections.append("## Project Discovery")
            if "project" in self.discovery:
                proj = self.discovery["project"]
                sections.append(f"- **Type**: {proj.get('type', 'unknown')}")
                if proj.get("languages"):
                    sections.append(f"- **Languages**: {', '.join(proj.get('languages', []))}")
                if proj.get("frameworks"):
                    sections.append(f"- **Frameworks**: {', '.join(proj.get('frameworks', []))}")

        # Recommendations
        if self.recommendations:
            sections.append("")
            sections.append("## Recommendations")
            for rec in self.recommendations:
                sections.append(f"- {rec}")

        return "\n".join(sections)

    def format_compact(self) -> str:
        """Format context in a compact form for smaller prompts.

        Returns:
            Compact markdown context (under 1000 chars)
        """
        parts = []

        if self.task:
            parts.append(f"**Task**: {self.task.title} (`{self.task.task_id}`)")

        if self.blockers:
            parts.append(f"**Blockers**: {len(self.blockers)}")

        if self.recent_sessions:
            parts.append(f"**Sessions**: {len(self.recent_sessions)} recent")

        if self.recent_decisions:
            parts.append(f"**Decisions**: {len(self.recent_decisions)} recent")

        return " | ".join(parts)


class AgentContextLoader:
    """Loads relevant context for AI agent work.

    This class aggregates context from multiple sources and provides
    it in formats suitable for AI agent consumption.
    """

    def __init__(self, context_dir: Optional[Path] = None):
        """Initialize the agent context loader.

        Args:
            context_dir: Base context directory. Defaults to .vibey/context/
        """
        self.context_dir = context_dir or Path(".vibey/context")
        self._loader = ContextLoader(self.context_dir)

    def load_for_task(self, task_id: str) -> EnhancedAgentContext:
        """Load all relevant context for working on a task.

        Args:
            task_id: Task ID to load context for

        Returns:
            EnhancedAgentContext with aggregated context
        """
        task = self._loader.tasks.read(task_id)

        context = EnhancedAgentContext(
            task=task,
            recent_sessions=self._loader.sessions.list(limit=5),
            recent_decisions=self._loader.decisions.get_recent_decisions(limit=10),
        )

        # Load sprint plan if task has sprint
        if task:
            # Try to find sprint context
            context.sprint_plan = self._load_sprint_plan_for_task(task)

            # Get files modified from task context
            context.files_modified = [
                f.get("path", "") for f in task.files_modified
            ]

            # Get blockers from task
            context.blockers = task.blockers_encountered

        # Load discovery
        context.discovery = self._load_discovery()

        # Load command history
        context.command_history = self._load_command_history(limit=10)

        # Generate recommendations
        context.recommendations = self._generate_recommendations(context)

        return context

    def load_for_session(self, session_id: Optional[str] = None) -> EnhancedAgentContext:
        """Load context for a session.

        Args:
            session_id: Optional session ID. If None, uses active session.

        Returns:
            EnhancedAgentContext with session-relevant context
        """
        if session_id:
            session = self._loader.sessions.read(session_id)
        else:
            session = self._loader.sessions.get_active_session()

        context = EnhancedAgentContext(
            recent_sessions=[session] if session else [],
            recent_decisions=self._loader.decisions.get_recent_decisions(limit=10),
        )

        # If session has tasks, load the first one
        if session and session.tasks_worked:
            first_task = session.tasks_worked[0]
            task_id = first_task.get("id")
            if task_id:
                context.task = self._loader.tasks.read(task_id)

        # Load discovery
        context.discovery = self._load_discovery()

        # Load command history
        context.command_history = self._load_command_history(limit=10)

        return context

    def load_current(self) -> EnhancedAgentContext:
        """Load context for the current working state.

        Attempts to load context based on:
        1. Active session if one exists
        2. Most recent task context
        3. General project context

        Returns:
            EnhancedAgentContext with best available context
        """
        # Try active session first
        active_session = self._loader.sessions.get_active_session()
        if active_session:
            return self.load_for_session(active_session.id)

        # Try most recent task
        recent_tasks = self._loader.tasks.list(limit=1)
        if recent_tasks:
            return self.load_for_task(recent_tasks[0].task_id)

        # Return general context
        return EnhancedAgentContext(
            recent_sessions=self._loader.sessions.list(limit=5),
            recent_decisions=self._loader.decisions.get_recent_decisions(limit=10),
            discovery=self._load_discovery(),
            command_history=self._load_command_history(limit=10),
        )

    def _load_sprint_plan_for_task(self, task: TaskContext) -> Optional[str]:
        """Load sprint plan for a task.

        Searches for sprint plan in both old and new context locations.
        """
        # Try new context location
        sprints_dir = self.context_dir / "sprints"
        if sprints_dir.exists():
            for sprint_dir in sprints_dir.iterdir():
                if sprint_dir.is_dir():
                    plan_path = sprint_dir / "SPRINT_PLAN.md"
                    if plan_path.exists():
                        return plan_path.read_text()

        # Try old roadmap context location
        old_context_dir = Path(".vibey/roadmap/context/sprints")
        if old_context_dir.exists():
            for sprint_dir in old_context_dir.iterdir():
                if sprint_dir.is_dir():
                    plan_path = sprint_dir / "SPRINT_PLAN.md"
                    if plan_path.exists():
                        return plan_path.read_text()

        return None

    def _load_discovery(self) -> Optional[Dict[str, Any]]:
        """Load current discovery output."""
        # Try new context location
        discovery_path = self.context_dir / "discovery" / "current.yaml"
        if discovery_path.exists():
            try:
                with open(discovery_path) as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        # Try old location
        old_discovery_path = Path(".vibey/discovery/current.yaml")
        if old_discovery_path.exists():
            try:
                with open(old_discovery_path) as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        return None

    def _load_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Load recent command context."""
        from .capture import get_recent_command_contexts

        contexts = get_recent_command_contexts(limit=limit, context_dir=self.context_dir)
        return [
            {
                "command": ctx.command,
                "timestamp": ctx.timestamp,
                "duration_ms": ctx.duration_ms,
                "status": ctx.status,
                "inputs": ctx.inputs,
                "outputs": ctx.outputs,
            }
            for ctx in contexts
        ]

    def _generate_recommendations(self, context: EnhancedAgentContext) -> List[str]:
        """Generate recommendations based on context.

        Args:
            context: Current context

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check for blockers
        if context.blockers:
            recommendations.append("Resolve blockers before proceeding")

        # Check discovery age
        if context.discovery:
            # If discovery exists but has no content, suggest running discovery
            if not context.discovery.get("project"):
                recommendations.append("Run 'vibey discover run' to analyze project")

        # Check for missing context
        if not context.task:
            recommendations.append("Start a task with 'vibey roadmap start <task-id>'")

        if not context.recent_sessions:
            recommendations.append("Context will improve as you use vibey")

        if not context.sprint_plan:
            recommendations.append("Add sprint plan to context for better guidance")

        return recommendations


# Module-level convenience functions

_agent_loader: Optional[AgentContextLoader] = None


def get_agent_context_loader(context_dir: Optional[Path] = None) -> AgentContextLoader:
    """Get or create the global agent context loader.

    Args:
        context_dir: Optional context directory path

    Returns:
        AgentContextLoader instance
    """
    global _agent_loader
    if _agent_loader is None or context_dir is not None:
        _agent_loader = AgentContextLoader(context_dir)
    return _agent_loader


def load_agent_context(task_id: Optional[str] = None) -> EnhancedAgentContext:
    """Convenience function to load agent context.

    Args:
        task_id: Optional task ID. If None, loads current context.

    Returns:
        EnhancedAgentContext
    """
    loader = get_agent_context_loader()
    if task_id:
        return loader.load_for_task(task_id)
    return loader.load_current()


def format_context_for_prompt(task_id: Optional[str] = None, compact: bool = False) -> str:
    """Format agent context for inclusion in prompts.

    Args:
        task_id: Optional task ID
        compact: If True, return compact format

    Returns:
        Formatted context string
    """
    context = load_agent_context(task_id)
    if compact:
        return context.format_compact()
    return context.format_for_claude()
