"""
Deployment commands.

Commands for deploying the framework to various platforms.
"""

from pathlib import Path


def deploy_cmd(platform: str, clean: bool = False) -> int:
    """Deploy framework to platform."""
    from vibey.operations.deployment import deploy_framework

    return deploy_framework(
        platform=platform,
        clean=clean,
        project_root=Path.cwd()
    )
