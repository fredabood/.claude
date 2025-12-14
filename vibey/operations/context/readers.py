"""Context readers for loading context with caching.

This module provides reader classes for loading context from the filesystem
with in-memory caching to improve performance for frequently accessed items.

Readers:
    - ContextReader: Base reader with caching
    - SessionContextReader: Read session context
    - TaskContextReader: Read task context
    - DecisionContextReader: Read decision records
    - SprintContextReader: Read sprint context
    - ContextLoader: Unified loader with cache management
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

import yaml

from .writers import (
    SessionContext,
    TaskContext,
    DecisionContext,
    SprintContext,
    SessionContextWriter,
    TaskContextWriter,
    DecisionContextWriter,
    SprintContextWriter,
)


T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Entry in the context cache."""

    value: T
    timestamp: float
    hit_count: int = 0


class ContextCache(Generic[T]):
    """In-memory cache for context objects.

    Features:
    - TTL-based expiration
    - LRU eviction when max size reached
    - Manual invalidation
    - Cache statistics
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
        max_size: int = 100,
    ):
        """Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default 5 minutes)
            max_size: Maximum number of entries (default 100)
        """
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def get(self, key: str) -> Optional[T]:
        """Get value from cache if present and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not present/expired
        """
        entry = self._cache.get(key)
        if entry is None:
            self._stats["misses"] += 1
            return None

        # Check TTL
        if time.time() - entry.timestamp > self.ttl:
            del self._cache[key]
            self._stats["misses"] += 1
            return None

        entry.hit_count += 1
        self._stats["hits"] += 1
        return entry.value

    def set(self, key: str, value: T) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict if at max size
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
        )

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry existed and was removed
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all entries with keys starting with prefix.

        Args:
            prefix: Key prefix to match

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]
        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with lowest hit count and oldest timestamp
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hit_count, self._cache[k].timestamp),
        )
        del self._cache[lru_key]
        self._stats["evictions"] += 1

    @property
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate": (
                self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                if (self._stats["hits"] + self._stats["misses"]) > 0
                else 0.0
            ),
        }


class ContextReader(ABC, Generic[T]):
    """Abstract base class for context readers.

    Provides common functionality for reading context with caching.
    Delegates actual file reading to the corresponding writer class.
    """

    def __init__(
        self,
        context_dir: Optional[Path] = None,
        cache: Optional[ContextCache[T]] = None,
    ):
        """Initialize the reader.

        Args:
            context_dir: Base context directory
            cache: Optional shared cache instance
        """
        self.context_dir = context_dir or Path(".vibey/context")
        self.cache = cache or ContextCache[T]()

    @abstractmethod
    def _get_writer(self) -> Any:
        """Get the corresponding writer instance."""
        pass

    @abstractmethod
    def _get_cache_prefix(self) -> str:
        """Get cache key prefix for this reader type."""
        pass

    def _cache_key(self, context_id: str) -> str:
        """Generate cache key for a context ID."""
        return f"{self._get_cache_prefix()}:{context_id}"

    def read(self, context_id: str, use_cache: bool = True) -> Optional[T]:
        """Read context by ID.

        Args:
            context_id: Context ID to read
            use_cache: Whether to use cache (default True)

        Returns:
            Context object or None if not found
        """
        if use_cache:
            cached = self.cache.get(self._cache_key(context_id))
            if cached is not None:
                return cached

        # Read from writer
        writer = self._get_writer()
        context = writer.read(context_id)

        if context is not None and use_cache:
            self.cache.set(self._cache_key(context_id), context)

        return context

    def read_current(self) -> Optional[T]:
        """Read the current/active context.

        Returns:
            Current context or None if none active
        """
        writer = self._get_writer()
        current_ids = writer.list_current()
        if current_ids:
            return self.read(current_ids[0])
        return None

    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[T]:
        """List contexts matching filters.

        Args:
            filters: Optional filters to apply
            limit: Maximum number to return

        Returns:
            List of matching contexts
        """
        writer = self._get_writer()
        ids = writer.list_current()[:limit]

        contexts = []
        for context_id in ids:
            context = self.read(context_id)
            if context is not None:
                if filters is None or self._matches_filters(context, filters):
                    contexts.append(context)

        return contexts

    def _matches_filters(self, context: T, filters: Dict[str, Any]) -> bool:
        """Check if context matches filters.

        Override in subclasses for type-specific filtering.
        """
        return True

    def invalidate(self, context_id: str) -> None:
        """Invalidate cache for a context ID."""
        self.cache.invalidate(self._cache_key(context_id))


class SessionContextReader(ContextReader[SessionContext]):
    """Reader for session context."""

    def _get_writer(self) -> SessionContextWriter:
        return SessionContextWriter(self.context_dir)

    def _get_cache_prefix(self) -> str:
        return "session"

    def _matches_filters(
        self,
        context: SessionContext,
        filters: Dict[str, Any],
    ) -> bool:
        """Filter sessions by status, type, agent, etc."""
        if "status" in filters and context.status != filters["status"]:
            return False
        if "type" in filters and context.type != filters["type"]:
            return False
        if "agent" in filters and context.agent != filters["agent"]:
            return False
        if "user" in filters and context.user != filters["user"]:
            return False
        return True

    def get_active_session(self) -> Optional[SessionContext]:
        """Get the currently active session.

        Returns:
            Active session or None
        """
        sessions = self.list(filters={"status": "active"}, limit=1)
        return sessions[0] if sessions else None


class TaskContextReader(ContextReader[TaskContext]):
    """Reader for task context."""

    def _get_writer(self) -> TaskContextWriter:
        return TaskContextWriter(self.context_dir)

    def _get_cache_prefix(self) -> str:
        return "task"

    def _matches_filters(
        self,
        context: TaskContext,
        filters: Dict[str, Any],
    ) -> bool:
        """Filter tasks by sprint, track, etc."""
        if "sprint_id" in filters and context.sprint_id != filters["sprint_id"]:
            return False
        if "track_id" in filters and context.track_id != filters["track_id"]:
            return False
        return True

    def get_tasks_for_sprint(self, sprint_id: str) -> List[TaskContext]:
        """Get all task contexts for a sprint.

        Args:
            sprint_id: Sprint ID to filter by

        Returns:
            List of task contexts
        """
        return self.list(filters={"sprint_id": sprint_id})


class DecisionContextReader(ContextReader[DecisionContext]):
    """Reader for decision records."""

    def _get_writer(self) -> DecisionContextWriter:
        return DecisionContextWriter(self.context_dir)

    def _get_cache_prefix(self) -> str:
        return "decision"

    def _matches_filters(
        self,
        context: DecisionContext,
        filters: Dict[str, Any],
    ) -> bool:
        """Filter decisions by status, date range, etc."""
        if "status" in filters and context.status != filters["status"]:
            return False
        if "date_from" in filters:
            if context.date < filters["date_from"]:
                return False
        if "date_to" in filters:
            if context.date > filters["date_to"]:
                return False
        return True

    def get_recent_decisions(self, limit: int = 10) -> List[DecisionContext]:
        """Get most recent decisions.

        Args:
            limit: Maximum number to return

        Returns:
            List of recent decisions
        """
        return self.list(limit=limit)


class SprintContextReader(ContextReader[SprintContext]):
    """Reader for sprint context."""

    def _get_writer(self) -> SprintContextWriter:
        return SprintContextWriter(self.context_dir)

    def _get_cache_prefix(self) -> str:
        return "sprint"

    def read_plan(self, sprint_slug: str) -> Optional[str]:
        """Read sprint plan markdown content.

        Args:
            sprint_slug: Sprint slug

        Returns:
            Plan content or None
        """
        plan_path = self.context_dir / "sprints" / sprint_slug / "SPRINT_PLAN.md"
        if plan_path.exists():
            return plan_path.read_text()
        return None

    def list_artifacts(self, sprint_slug: str) -> List[Dict[str, Any]]:
        """List artifacts in a sprint's context.

        Args:
            sprint_slug: Sprint slug

        Returns:
            List of artifact info dicts
        """
        sprint_dir = self.context_dir / "sprints" / sprint_slug
        if not sprint_dir.exists():
            return []

        artifacts = []
        for f in sprint_dir.iterdir():
            if f.is_file():
                artifacts.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime,
                        tz=timezone.utc,
                    ).isoformat(),
                })
        return artifacts


@dataclass
class AgentContext:
    """Aggregated context for AI agent work."""

    task: Optional[TaskContext] = None
    sprint: Optional[SprintContext] = None
    sprint_plan: Optional[str] = None
    recent_sessions: List[SessionContext] = field(default_factory=list)
    recent_decisions: List[DecisionContext] = field(default_factory=list)
    discovery: Optional[Dict[str, Any]] = None

    def format_for_claude(self) -> str:
        """Format context for inclusion in Claude prompts.

        Returns:
            Formatted markdown context
        """
        sections = []

        if self.task:
            sections.append(f"## Current Task\n")
            sections.append(f"**{self.task.title}**")
            if self.task.description:
                sections.append(f"\n{self.task.description}")
            sections.append(f"\n- Task ID: `{self.task.task_id}`")
            sections.append(f"- Sprint: `{self.task.sprint_id}`")
            if self.task.notes:
                sections.append(f"\n### Notes\n{self.task.notes}")

        if self.sprint_plan:
            sections.append(f"\n## Sprint Plan\n")
            # Include first 1000 chars of plan
            plan_preview = self.sprint_plan[:1000]
            if len(self.sprint_plan) > 1000:
                plan_preview += "\n...(truncated)"
            sections.append(plan_preview)

        if self.recent_sessions:
            sections.append(f"\n## Recent Sessions ({len(self.recent_sessions)})\n")
            for session in self.recent_sessions[:3]:
                sections.append(f"- `{session.id}`: {session.type} ({session.status})")
                if session.goals:
                    sections.append(f"  Goals: {', '.join(session.goals[:3])}")

        if self.recent_decisions:
            sections.append(f"\n## Recent Decisions ({len(self.recent_decisions)})\n")
            for decision in self.recent_decisions[:5]:
                sections.append(f"- **{decision.title}** ({decision.status})")

        if self.discovery:
            sections.append(f"\n## Project Discovery\n")
            if "project" in self.discovery:
                proj = self.discovery["project"]
                sections.append(f"- Type: {proj.get('type', 'unknown')}")
                sections.append(f"- Languages: {', '.join(proj.get('languages', []))}")

        return "\n".join(sections)


class ContextLoader:
    """Unified context loader with shared caching.

    Provides a single interface for loading all context types
    with efficient caching across readers.
    """

    def __init__(
        self,
        context_dir: Optional[Path] = None,
        cache_ttl: int = 300,
    ):
        """Initialize the loader.

        Args:
            context_dir: Base context directory
            cache_ttl: Cache TTL in seconds
        """
        self.context_dir = context_dir or Path(".vibey/context")

        # Shared caches for each type
        self._session_cache = ContextCache[SessionContext](ttl_seconds=cache_ttl)
        self._task_cache = ContextCache[TaskContext](ttl_seconds=cache_ttl)
        self._decision_cache = ContextCache[DecisionContext](ttl_seconds=cache_ttl)
        self._sprint_cache = ContextCache[SprintContext](ttl_seconds=cache_ttl)

        # Initialize readers with shared caches
        self.sessions = SessionContextReader(self.context_dir, self._session_cache)
        self.tasks = TaskContextReader(self.context_dir, self._task_cache)
        self.decisions = DecisionContextReader(self.context_dir, self._decision_cache)
        self.sprints = SprintContextReader(self.context_dir, self._sprint_cache)

    def load(
        self,
        context_type: str,
        context_id: str,
    ) -> Optional[Union[SessionContext, TaskContext, DecisionContext, SprintContext]]:
        """Load context by type and ID.

        Args:
            context_type: One of 'session', 'task', 'decision', 'sprint'
            context_id: Context ID

        Returns:
            Context object or None
        """
        readers = {
            "session": self.sessions,
            "task": self.tasks,
            "decision": self.decisions,
            "sprint": self.sprints,
        }

        reader = readers.get(context_type)
        if reader is None:
            return None

        return reader.read(context_id)

    def load_for_task(self, task_id: str) -> AgentContext:
        """Load all relevant context for working on a task.

        Args:
            task_id: Task ID to load context for

        Returns:
            AgentContext with aggregated context
        """
        task = self.tasks.read(task_id)

        agent_context = AgentContext(
            task=task,
            recent_sessions=self.sessions.list(limit=3),
            recent_decisions=self.decisions.get_recent_decisions(limit=10),
        )

        # Load sprint context if task has sprint
        if task and task.sprint_id:
            # Try to find sprint slug from sprint directory
            sprints_dir = self.context_dir / "sprints"
            if sprints_dir.exists():
                for sprint_dir in sprints_dir.iterdir():
                    if sprint_dir.is_dir():
                        agent_context.sprint_plan = self.sprints.read_plan(sprint_dir.name)
                        if agent_context.sprint_plan:
                            break

        # Load discovery if available
        discovery_path = self.context_dir.parent / "discovery" / "current.yaml"
        if discovery_path.exists():
            try:
                with open(discovery_path) as f:
                    agent_context.discovery = yaml.safe_load(f)
            except Exception:
                pass

        return agent_context

    def load_for_session(self, session_id: Optional[str] = None) -> AgentContext:
        """Load context for a session.

        Args:
            session_id: Optional session ID. If None, uses active session.

        Returns:
            AgentContext with session-relevant context
        """
        if session_id:
            session = self.sessions.read(session_id)
        else:
            session = self.sessions.get_active_session()

        agent_context = AgentContext(
            recent_sessions=[session] if session else [],
            recent_decisions=self.decisions.get_recent_decisions(limit=10),
        )

        # If session has tasks, load the first one
        if session and session.tasks_worked:
            first_task = session.tasks_worked[0]
            task_id = first_task.get("id")
            if task_id:
                agent_context.task = self.tasks.read(task_id)

        return agent_context

    def invalidate_all(self) -> None:
        """Clear all caches."""
        self._session_cache.clear()
        self._task_cache.clear()
        self._decision_cache.clear()
        self._sprint_cache.clear()

    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get cache statistics for all readers.

        Returns:
            Dict of stats by context type
        """
        return {
            "session": self._session_cache.stats,
            "task": self._task_cache.stats,
            "decision": self._decision_cache.stats,
            "sprint": self._sprint_cache.stats,
        }


# Module-level convenience function
_loader: Optional[ContextLoader] = None


def get_context_loader(context_dir: Optional[Path] = None) -> ContextLoader:
    """Get or create the global context loader.

    Args:
        context_dir: Optional context directory path

    Returns:
        ContextLoader instance
    """
    global _loader
    if _loader is None or context_dir is not None:
        _loader = ContextLoader(context_dir)
    return _loader
