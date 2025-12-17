"""
Documentation commands.

Commands for generating documentation.
"""

from pathlib import Path


def docs_generate_cmd(overwrite: bool = False) -> int:
    """Generate documentation."""
    from vibey.operations.docs import generate_docs

    return generate_docs(
        vibey_dir=Path.cwd() / ".vibey",  # This expects .vibey/ path
        overwrite=overwrite,
        quiet=False
    )
