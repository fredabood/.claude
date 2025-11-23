"""
Platform adapters for Vibey Framework.

This module provides the adapter pattern for deploying Vibey to different
AI coding assistant platforms. Each platform (Claude Code, Goose, Cursor, etc.)
has its own adapter that transforms the .vibey/ source of truth into the
platform-specific deployment format.

Architecture:
- Source of Truth: .vibey/ directory (platform-agnostic)
- Adapters: Transform .vibey/ → platform deployment
- Deployments: .claude/, .goose/, .gemini/, etc. (generated, disposable)

Zero-Drift Guarantee:
All platform adapters generate artifacts from frontmatter metadata.
No manual conversion required - tools, commands, and context files
are automatically derived from the source markdown files.

Example:
    from vibey.adapters import ClaudeCodeAdapter, GeminiAdapter

    # Deploy to Claude Code
    adapter = ClaudeCodeAdapter()
    adapter.deploy(source_dir=".vibey", target_dir=".claude")

    # Export to Gemini extension
    gemini = GeminiAdapter(Path("/path/to/vibey"))
    result = gemini.export(Path("./dist/vibey-gemini-extension"))
"""

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from vibey.adapters.claude_code import ClaudeCodeAdapter
from vibey.adapters.goose import GooseAdapter
from vibey.adapters.aider import AiderAdapter
from vibey.adapters.gemini import GeminiAdapter
from vibey.adapters.continuedev import ContinueAdapter
from vibey.adapters.windsurf import WindsurfAdapter
from vibey.adapters.vscode import VSCodeAdapter
from vibey.adapters.cursor import CursorAdapter
from vibey.adapters.copilot import CopilotAdapter
from vibey.adapters.jetbrains import JetBrainsAdapter
from vibey.adapters.amazonq import AmazonQAdapter
from vibey.adapters.replit import ReplitAdapter
from vibey.adapters.cody import CodyAdapter

__all__ = [
    'PlatformAdapter',
    'DeploymentResult',
    'ClaudeCodeAdapter',
    'GooseAdapter',
    'AiderAdapter',
    'GeminiAdapter',
    'ContinueAdapter',
    'WindsurfAdapter',
    'VSCodeAdapter',
    'CursorAdapter',
    'CopilotAdapter',
    'JetBrainsAdapter',
    'AmazonQAdapter',
    'ReplitAdapter',
    'CodyAdapter',
]
