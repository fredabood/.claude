"""
Unified deploy commands.

These commands deploy Vibey configurations to various AI platforms.
"""

from pathlib import Path
from typing import Optional

from vibey.unified import (
    unified_command,
    param,
    ParamType,
    CommandResult,
)


@unified_command(
    name="deploy_list",
    description="List available deployment platforms",
    cli_group="deploy",
    cli_name="list",
    mcp_name="vibey_deploy_list",
    mcp_category="deploy",
)
def deploy_list(root_dir: Optional[Path] = None) -> CommandResult:
    """List available deployment platforms."""
    from vibey.adapters.registry import ADAPTER_REGISTRY

    try:
        platforms = ADAPTER_REGISTRY.list_adapters()
        lines = [
            "Available Platforms:",
            "=" * 40,
        ]
        for p in platforms:
            lines.append(f"  - {p['name']}: {p['description']}")
        return CommandResult.ok(
            data=platforms,
            message="\n".join(lines)
        )
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="deploy_run",
    description="Deploy configuration to a platform",
    cli_group="deploy",
    cli_name="run",
    mcp_name="vibey_deploy",
    mcp_category="deploy",
)
@param(
    "platform",
    type=ParamType.STRING,
    required=True,
    help="Target platform (e.g., claude-code, cursor, copilot)",
    cli_short="-p",
)
@param(
    "dry_run",
    type=ParamType.BOOLEAN,
    required=False,
    default=False,
    help="Show what would be deployed without making changes",
    cli_is_flag=True,
)
@param(
    "force",
    type=ParamType.BOOLEAN,
    required=False,
    default=False,
    help="Overwrite existing configuration",
    cli_short="-f",
    cli_is_flag=True,
)
def deploy_run(
    platform: str,
    dry_run: bool = False,
    force: bool = False,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """Deploy configuration to a platform."""
    from vibey.adapters.registry import ADAPTER_REGISTRY

    root_dir = root_dir or Path.cwd()

    try:
        adapter = ADAPTER_REGISTRY.get_adapter(platform)
        if not adapter:
            available = ", ".join(a['name'] for a in ADAPTER_REGISTRY.list_adapters())
            return CommandResult.fail(
                error=f"Unknown platform: {platform}. Available: {available}"
            )

        if dry_run:
            preview = adapter.preview_deploy(root_dir)
            return CommandResult.ok(
                data=preview,
                message=f"Dry run for {platform}:\n" + "\n".join(f"  - {f}" for f in preview.get('files', []))
            )

        result = adapter.deploy(root_dir, force=force)
        return CommandResult.ok(
            data=result,
            message=f"Deployed to {platform}: {result.get('files_written', 0)} files written"
        )
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="deploy_status",
    description="Check deployment status for a platform",
    cli_group="deploy",
    cli_name="status",
    mcp_name="vibey_deploy_status",
    mcp_category="deploy",
)
@param(
    "platform",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Target platform (checks all if not specified)",
    cli_short="-p",
)
def deploy_status(
    platform: Optional[str] = None,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """Check deployment status for platforms."""
    from vibey.adapters.registry import ADAPTER_REGISTRY

    root_dir = root_dir or Path.cwd()

    try:
        if platform:
            adapter = ADAPTER_REGISTRY.get_adapter(platform)
            if not adapter:
                return CommandResult.fail(error=f"Unknown platform: {platform}")
            status = adapter.check_status(root_dir)
            return CommandResult.ok(
                data=status,
                message=f"{platform}: {'Deployed' if status.get('deployed') else 'Not deployed'}"
            )
        else:
            # Check all platforms
            results = {}
            lines = ["Deployment Status:", "=" * 40]
            for p in ADAPTER_REGISTRY.list_adapters():
                adapter = ADAPTER_REGISTRY.get_adapter(p['name'])
                status = adapter.check_status(root_dir) if adapter else {'deployed': False}
                results[p['name']] = status
                icon = "✅" if status.get('deployed') else "❌"
                lines.append(f"  {icon} {p['name']}")
            return CommandResult.ok(data=results, message="\n".join(lines))
    except Exception as e:
        return CommandResult.fail(error=str(e))
