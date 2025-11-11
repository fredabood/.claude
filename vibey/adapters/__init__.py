"""
Platform adapters for Vibey Framework.

This module provides the adapter pattern for deploying Vibey to different
AI coding assistant platforms. Each platform (Claude Code, Goose, Cursor, etc.)
has its own adapter that transforms the .vibey/ source of truth into the
platform-specific deployment format.

Architecture:
- Source of Truth: .vibey/ directory (platform-agnostic)
- Adapters: Transform .vibey/ → platform deployment
- Deployments: .claude/, .goose/, etc. (generated, disposable)

Example:
    from vibey.adapters import ClaudeCodeAdapter

    adapter = ClaudeCodeAdapter()
    adapter.deploy(source_dir=".vibey", target_dir=".claude")
"""

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from vibey.adapters.claude_code import ClaudeCodeAdapter
from vibey.adapters.goose import GooseAdapter

__all__ = [
    'PlatformAdapter',
    'DeploymentResult',
    'ClaudeCodeAdapter',
    'GooseAdapter',
]
