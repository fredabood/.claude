"""
Platform Adapters Module

Provides platform-specific deployment adapters for Claude Code, Goose, Cursor, etc.

Usage:
    from framework.platform_adapters import ClaudeAdapter

    adapter = ClaudeAdapter()
    adapter.deploy()

Created: 2025-11-09
Sprint: core-framework-2, Task 5
"""

from .base import PlatformAdapter
from .claude_adapter import ClaudeAdapter
from .registry import AdapterRegistry

__all__ = ['PlatformAdapter', 'ClaudeAdapter', 'AdapterRegistry']
