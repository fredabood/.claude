#!/usr/bin/env python3
"""
Vibey Deploy Command

Deploy Vibey framework to target platform from .vibey/ configuration.

Usage:
    python3 framework/scripts/deploy.py --platform claude-code
    python3 framework/scripts/deploy.py --platform goose
    python3 framework/scripts/deploy.py --list-platforms
    python3 framework/scripts/deploy.py --platform claude-code --no-backup
    python3 framework/scripts/deploy.py --platform claude-code --no-clean

Created: 2025-11-09
Sprint: core-framework-2, Task 7
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add framework to path
framework_dir = Path(__file__).parent.parent
sys.path.insert(0, str(framework_dir.parent))

from framework.platform_adapters.registry import AdapterRegistry


def print_banner():
    """Print Vibey deploy banner."""
    print("=" * 60)
    print("🚀 Vibey Deploy - Platform Deployment Generator")
    print("=" * 60)
    print()


def list_platforms():
    """List all available platforms."""
    print_banner()

    platforms = AdapterRegistry.list_platforms()

    if not platforms:
        print("❌ No platforms registered.")
        print("\nPlease ensure platform adapters are installed.")
        return 1

    print(f"Available Platforms ({len(platforms)}):\n")

    for platform in platforms:
        try:
            info = AdapterRegistry.get_adapter_info(platform)
            print(f"  📦 {platform}")
            print(f"     Class: {info['class_name']}")
            print(f"     Deployment Dir: {info['deployment_dir']}")
            print(f"     Instructions File: {info['instructions_file']}")
            print()
        except Exception as e:
            print(f"  ⚠️  {platform}: Error getting info - {e}")
            print()

    print("=" * 60)
    return 0


def deploy_to_platform(
    platform: str,
    vibey_dir: Optional[Path] = None,
    clean: bool = True,
    backup: bool = True,
    validate: bool = True
) -> int:
    """
    Deploy to specified platform.

    Args:
        platform: Platform identifier (e.g., 'claude-code')
        vibey_dir: Path to .vibey directory (auto-detected if None)
        clean: Delete existing deployment before generating
        backup: Backup existing deployment
        validate: Validate configuration before deployment

    Returns:
        Exit code (0 = success, 1 = error)
    """
    print_banner()

    # Check if platform is registered
    if not AdapterRegistry.is_registered(platform):
        available = ', '.join(AdapterRegistry.list_platforms())
        print(f"❌ Platform '{platform}' not registered.\n")
        print(f"Available platforms: {available}\n")
        print("Use --list-platforms to see all available platforms.")
        print("=" * 60)
        return 1

    # Get adapter
    print(f"📦 Platform: {platform}")
    print()

    try:
        adapter = AdapterRegistry.get_adapter(platform, vibey_dir=vibey_dir)
        print(f"✅ Adapter loaded: {type(adapter).__name__}")
        print(f"   Deployment Directory: {adapter.get_deployment_dir()}")
        print(f"   Instructions File: {adapter.get_instructions_filename()}")
        print()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}\n")
        print("Make sure you're in a Vibey-managed project (with .vibey/ directory).")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"❌ Error loading adapter: {e}")
        print("=" * 60)
        return 1

    # Validate configuration
    if validate:
        print("🔍 Validating configuration...")
        if not adapter.validate_config():
            print("❌ Configuration validation failed.")
            print("\nPlease check your .vibey/config/ files:")
            print("  - .vibey/config/project.yaml")
            print("  - .vibey/config/framework.yaml")
            print("  - .vibey/config/agents/*.yaml")
            print("  - .vibey/config/workflows/*.yaml")
            print("\n" + "=" * 60)
            return 1
        print("✅ Configuration valid")
        print()

    # Show deployment options
    print("⚙️  Deployment Options:")
    print(f"   Clean: {'Yes' if clean else 'No'} (delete existing deployment)")
    print(f"   Backup: {'Yes' if backup else 'No'} (backup before overwrite)")
    print(f"   Validate: {'Yes' if validate else 'No'} (validate configs)")
    print()

    # Confirm deployment
    deployment_dir = adapter.get_deployment_dir()
    if deployment_dir.exists():
        print(f"⚠️  Existing deployment found at: {deployment_dir}")
        if clean:
            print("   This deployment will be deleted and regenerated.")
        elif backup:
            print("   This deployment will be backed up and overwritten.")
        else:
            print("   This deployment will be overwritten (no backup).")
        print()

    # Deploy
    try:
        print("🚀 Starting deployment...\n")
        adapter.deploy(clean=clean, validate=validate, backup=backup)
        print()
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        return 1

    # Success
    print("=" * 60)
    print(f"✅ Deployment complete!")
    print()
    print(f"📁 Deployment location: {deployment_dir}")
    print(f"📄 Instructions file: {deployment_dir / adapter.get_instructions_filename()}")

    # Show next steps
    print()
    print("Next steps:")
    if platform == 'claude-code':
        print("  1. Open this project in Claude Code")
        print("  2. Claude will automatically load CLAUDE.md")
        print("  3. Start using Vibey agents and workflows!")
    elif platform == 'goose':
        print("  1. Open this project in Goose")
        print("  2. Goose will automatically load .goose/README.md")
        print("  3. Start using Vibey recipes and extensions!")
    elif platform == 'cursor':
        print("  1. Open this project in Cursor")
        print("  2. Cursor will automatically load .cursorrules")
        print("  3. Start using Vibey agents!")
    else:
        print(f"  1. Open this project in {platform}")
        print("  2. Follow platform-specific instructions")

    print()
    print("=" * 60)
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Deploy Vibey framework to target platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --platform claude-code
  %(prog)s --platform goose --no-backup
  %(prog)s --list-platforms
  %(prog)s --platform claude-code --vibey-dir /path/to/.vibey
        """
    )

    parser.add_argument(
        '--platform',
        '-p',
        type=str,
        help='Target platform (e.g., claude-code, goose, cursor)'
    )

    parser.add_argument(
        '--list-platforms',
        '-l',
        action='store_true',
        help='List all available platforms'
    )

    parser.add_argument(
        '--vibey-dir',
        type=Path,
        default=None,
        help='Path to .vibey directory (auto-detected if not provided)'
    )

    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Do not delete existing deployment (default: clean)'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not backup existing deployment (default: backup)'
    )

    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip configuration validation (default: validate)'
    )

    args = parser.parse_args()

    # List platforms
    if args.list_platforms:
        return list_platforms()

    # Deploy to platform
    if not args.platform:
        parser.print_help()
        print("\n❌ Error: --platform is required (or use --list-platforms)")
        return 1

    return deploy_to_platform(
        platform=args.platform,
        vibey_dir=args.vibey_dir,
        clean=not args.no_clean,
        backup=not args.no_backup,
        validate=not args.no_validate
    )


if __name__ == "__main__":
    sys.exit(main())
