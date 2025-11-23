#!/usr/bin/env python3
"""
Vibey Docs Command

Generate project documentation from .vibey/config/ files.

Usage:
    python3 framework/scripts/docs.py generate
    python3 framework/scripts/docs.py generate --overwrite
    python3 framework/scripts/docs.py generate --output custom-docs/

Created: 2025-11-09
Sprint: core-framework-2, Task 8
"""

import sys
import argparse
from pathlib import Path

# Add framework to path
framework_dir = Path(__file__).parent.parent
sys.path.insert(0, str(framework_dir.parent))

from vibey.operations.docs import DocumentationGenerator


def print_banner():
    """Print Vibey docs banner."""
    print("=" * 60)
    print("📚 Vibey Docs - Documentation Generator")
    print("=" * 60)
    print()


def generate_docs(
    vibey_dir: Path = None,
    output_dir: Path = None,
    overwrite: bool = False
) -> int:
    """
    Generate documentation.

    Args:
        vibey_dir: Path to .vibey directory (auto-detected if None)
        output_dir: Path to output directory (default: docs/)
        overwrite: Overwrite existing files

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print_banner()

    try:
        # Initialize generator
        print("🔍 Loading configuration...")
        generator = DocumentationGenerator(vibey_dir=vibey_dir, output_dir=output_dir)

        print(f"   .vibey directory: {generator.vibey_dir}")
        print(f"   Output directory: {generator.output_dir}")
        print()

        # Show loaded configuration
        project_name = generator.project_config.get('project', {}).get('name', 'Unknown')
        print(f"📦 Project: {project_name}")
        print(f"   Agents: {len(generator.agents)}")
        print(f"   Workflows: {len(generator.workflows)}")
        print()

        # Generate documentation
        print("📝 Generating documentation...\n")
        generated_files = generator.generate_all(overwrite=overwrite)

        if not generated_files:
            print("ℹ️  No files generated (all documentation already exists)")
            print("   Use --overwrite to regenerate existing files")
            print()
        else:
            print()
            print(f"✅ Generated {len(generated_files)} file(s):")
            for file_path in generated_files:
                rel_path = file_path.relative_to(generator.project_root)
                print(f"   ✓ {rel_path}")
            print()

        # Show summary
        print("=" * 60)
        print("✅ Documentation generation complete!")
        print()
        print(f"📁 Documentation location: {generator.output_dir}")
        print()
        print("Generated documentation:")
        print("  - README.md - Project overview and quick start")
        print("  - ARCHITECTURE.md - System architecture")
        print("  - AGENTS.md - Agent reference")
        print("  - WORKFLOWS.md - Workflow reference")
        print("  - CONFIGURATION.md - Configuration reference")
        print()
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}\n")
        print("Make sure you're in a Vibey-managed project (with .vibey/ directory).")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate project documentation from Vibey configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate
  %(prog)s generate --overwrite
  %(prog)s generate --output custom-docs/
  %(prog)s generate --vibey-dir /path/to/.vibey
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate documentation from configuration'
    )

    generate_parser.add_argument(
        '--vibey-dir',
        type=Path,
        default=None,
        help='Path to .vibey directory (auto-detected if not provided)'
    )

    generate_parser.add_argument(
        '--output',
        '-o',
        type=Path,
        default=None,
        help='Output directory (default: docs/)'
    )

    generate_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing documentation files'
    )

    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        print("\n❌ Error: command is required")
        print("\nAvailable commands:")
        print("  generate    Generate documentation from configuration")
        return 1

    # Generate documentation
    if args.command == 'generate':
        return generate_docs(
            vibey_dir=args.vibey_dir,
            output_dir=args.output,
            overwrite=args.overwrite
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
