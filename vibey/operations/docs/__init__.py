"""
Documentation Generation Module

Provides documentation generation from Vibey configuration.

Usage:
    from vibey.operations.docs import DocumentationGenerator, generate_docs

    generator = DocumentationGenerator()
    generator.generate_all()

    # Or use the convenience function:
    generate_docs()

Created: 2025-11-09
Sprint: core-framework-2, Task 8
"""

from .generator import DocumentationGenerator
from .operations import generate_docs, get_doc_files, check_docs_exist, validate_vibey_dir

__all__ = [
    'DocumentationGenerator',
    'generate_docs',
    'get_doc_files',
    'check_docs_exist',
    'validate_vibey_dir',
]
