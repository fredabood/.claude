"""
Documentation Generation Module

Provides documentation generation from Vibey configuration.

Usage:
    from framework.docs import DocumentationGenerator

    generator = DocumentationGenerator()
    generator.generate_all()

Created: 2025-11-09
Sprint: core-framework-2, Task 8
"""

from .generator import DocumentationGenerator

__all__ = ['DocumentationGenerator']
