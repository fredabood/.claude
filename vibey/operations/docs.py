"""
Documentation generation operations module.

This module handles Vibey project documentation generation from configuration files.
Extracted from CLI to provide reusable documentation generation logic.
"""

from pathlib import Path
from typing import Optional, List

from framework.docs.generator import DocumentationGenerator


def generate_docs(
    vibey_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    quiet: bool = False
) -> int:
    """
    Generate documentation from Vibey configuration.

    Args:
        vibey_dir: Path to .vibey directory (auto-detected if None)
        output_dir: Path to output directory (default: docs/)
        overwrite: Overwrite existing files
        quiet: Suppress output (only show errors)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    def print_msg(msg: str, force: bool = False) -> None:
        """Print message unless in quiet mode."""
        if not quiet or force:
            print(msg)

    try:
        # Initialize generator
        print_msg("🔍 Loading configuration...")
        generator = DocumentationGenerator(vibey_dir=vibey_dir, output_dir=output_dir)

        print_msg(f"   .vibey directory: {generator.vibey_dir}")
        print_msg(f"   Output directory: {generator.output_dir}")
        print_msg("")

        # Show loaded configuration
        project_name = generator.project_config.get('project', {}).get('name', 'Unknown')
        print_msg(f"📦 Project: {project_name}")
        print_msg(f"   Agents: {len(generator.agents)}")
        print_msg(f"   Workflows: {len(generator.workflows)}")
        print_msg("")

        # Generate documentation
        print_msg("📝 Generating documentation...\n")
        generated_files = generator.generate_all(overwrite=overwrite)

        if not generated_files:
            print_msg("ℹ️  No files generated (all documentation already exists)")
            print_msg("   Use --overwrite to regenerate existing files")
            print_msg("")
        else:
            print_msg("")
            print_msg(f"✅ Generated {len(generated_files)} file(s):")
            for file_path in generated_files:
                rel_path = file_path.relative_to(generator.project_root)
                print_msg(f"   ✓ {rel_path}")
            print_msg("")

        # Show summary
        if not quiet:
            print_msg("=" * 60)
            print_msg("✅ Documentation generation complete!")
            print_msg("")
            print_msg(f"📁 Documentation location: {generator.output_dir}")
            print_msg("")
            print_msg("Generated documentation:")
            print_msg("  - README.md - Project overview and quick start")
            print_msg("  - ARCHITECTURE.md - System architecture")
            print_msg("  - AGENTS.md - Agent reference")
            print_msg("  - WORKFLOWS.md - Workflow reference")
            print_msg("  - CONFIGURATION.md - Configuration reference")
            print_msg("")
            print_msg("=" * 60)

        return 0

    except FileNotFoundError as e:
        print_msg(f"❌ Error: {e}\n", force=True)
        print_msg("Make sure you're in a Vibey-managed project (with .vibey/ directory).", force=True)
        print_msg("=" * 60, force=True)
        return 1
    except Exception as e:
        print_msg(f"❌ Error generating documentation: {e}", force=True)
        if not quiet:
            import traceback
            traceback.print_exc()
        print_msg("\n" + "=" * 60, force=True)
        return 1


def get_doc_files(output_dir: Optional[Path] = None) -> List[Path]:
    """
    Get list of expected documentation files.

    Args:
        output_dir: Output directory (default: docs/)

    Returns:
        List of expected documentation file paths
    """
    if output_dir is None:
        output_dir = Path.cwd() / "docs"

    return [
        output_dir / "README.md",
        output_dir / "ARCHITECTURE.md",
        output_dir / "AGENTS.md",
        output_dir / "WORKFLOWS.md",
        output_dir / "CONFIGURATION.md",
    ]


def check_docs_exist(output_dir: Optional[Path] = None) -> bool:
    """
    Check if documentation files already exist.

    Args:
        output_dir: Output directory (default: docs/)

    Returns:
        True if all documentation files exist, False otherwise
    """
    doc_files = get_doc_files(output_dir)
    return all(f.exists() for f in doc_files)


def validate_vibey_dir(vibey_dir: Optional[Path] = None) -> bool:
    """
    Validate that a .vibey directory exists and has required files.

    Args:
        vibey_dir: Path to .vibey directory (auto-detected if None)

    Returns:
        True if valid, False otherwise
    """
    if vibey_dir is None:
        vibey_dir = Path.cwd() / ".vibey"

    if not vibey_dir.exists():
        return False

    # Check for config directory
    config_dir = vibey_dir / "config"
    if not config_dir.exists():
        return False

    # Check for required config files
    required_files = [
        config_dir / "project.yaml",
        config_dir / "framework.yaml",
    ]

    return all(f.exists() for f in required_files)
