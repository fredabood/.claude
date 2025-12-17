"""
Unified docs commands.

These commands generate and manage documentation.
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
    name="docs_generate_cli",
    description="Generate CLI reference documentation",
    cli_group="docs",
    cli_name="generate-cli",
    mcp_name="vibey_docs_generate_cli",
    mcp_category="docs",
)
@param(
    "output",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Output file path (default: docs/reference/CLI_REFERENCE.md)",
    cli_short="-o",
)
def docs_generate_cli(
    output: Optional[str] = None,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """Generate CLI reference documentation."""
    from vibey.operations.docs.cli_reference_generator import generate_cli_reference

    root_dir = root_dir or Path.cwd()
    output_path = Path(output) if output else root_dir / "docs/reference/CLI_REFERENCE.md"

    try:
        result = generate_cli_reference(root_dir, output_path)
        return CommandResult.ok(
            data=result,
            message=f"CLI reference generated: {output_path} ({result.get('command_count', 0)} commands)"
        )
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="docs_generate_mcp",
    description="Generate MCP reference documentation",
    cli_group="docs",
    cli_name="generate-mcp",
    mcp_name="vibey_docs_generate_mcp",
    mcp_category="docs",
)
@param(
    "output",
    type=ParamType.STRING,
    required=False,
    default=None,
    help="Output file path (default: docs/reference/MCP_REFERENCE.md)",
    cli_short="-o",
)
def docs_generate_mcp(
    output: Optional[str] = None,
    root_dir: Optional[Path] = None,
) -> CommandResult:
    """Generate MCP reference documentation."""
    from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference

    root_dir = root_dir or Path.cwd()
    output_path = Path(output) if output else root_dir / "docs/reference/MCP_REFERENCE.md"

    try:
        result = generate_mcp_reference(root_dir, output_path)
        return CommandResult.ok(
            data=result,
            message=f"MCP reference generated: {output_path} ({result.get('tool_count', 0)} tools)"
        )
    except Exception as e:
        return CommandResult.fail(error=str(e))


@unified_command(
    name="docs_check_drift",
    description="Check for documentation drift",
    cli_group="docs",
    cli_name="check-drift",
    mcp_name="vibey_docs_check_drift",
    mcp_category="docs",
)
def docs_check_drift(root_dir: Optional[Path] = None) -> CommandResult:
    """Check for documentation drift (outdated docs)."""
    from vibey.operations.docs.drift_checker import check_documentation_drift

    root_dir = root_dir or Path.cwd()

    try:
        result = check_documentation_drift(root_dir)
        if result.get("drift_detected", False):
            drift_items = result.get("drift_items", [])
            return CommandResult.fail(
                error=f"Documentation drift detected: {len(drift_items)} items need updating\n" +
                      "\n".join(f"  - {item}" for item in drift_items[:5])
            )
        return CommandResult.ok(
            data=result,
            message="No documentation drift detected - docs are up to date"
        )
    except Exception as e:
        return CommandResult.fail(error=str(e))
