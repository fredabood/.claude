"""
Gemini platform adapter for Vibey.

This module provides zero-drift export of Vibey agents and workflows
to Gemini Code Assist's extension format.

Key Components:
- GeminiAdapter: Main adapter class
- GeminiContextGenerator: Generates GEMINI.md from agent frontmatter
- GeminiCommandGenerator: Generates TOML commands from workflow frontmatter
- GeminiExtensionGenerator: Creates extension manifest and settings
"""

from .adapter import GeminiAdapter
from .context_generator import GeminiContextGenerator
from .command_generator import GeminiCommandGenerator
from .extension_generator import GeminiExtensionGenerator

__all__ = [
    'GeminiAdapter',
    'GeminiContextGenerator',
    'GeminiCommandGenerator',
    'GeminiExtensionGenerator',
]
