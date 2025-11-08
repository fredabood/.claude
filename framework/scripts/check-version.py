#!/usr/bin/env python3
"""
Vibey Framework Version Checker

Checks if the deployed framework version matches the available version
and provides upgrade information if needed.

Usage:
    python3 check-version.py [--deployed-marker PATH] [--framework-source PATH]
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple

# Framework version (updated with each release)
FRAMEWORK_VERSION = "1.2.0"
VERSION_DATE = "2024-11-05"


def read_deployed_version(marker_file: Path) -> Optional[Tuple[str, str]]:
    """
    Read version from deployed .vibey/ai-reference.md marker file.

    Returns:
        Tuple of (version, deployed_date) or None if not found
    """
    if not marker_file.exists():
        return None

    try:
        with open(marker_file, 'r') as f:
            content = f.read()
            lines = content.splitlines()

        version = None
        deployed_date = None

        for line in lines:
            line = line.strip()
            # Format: **Framework Version:** 2.0
            if line.startswith("**Framework Version:**"):
                version = line.split("**Framework Version:**")[1].strip()
            # Format: **Deployed:** ...
            elif line.startswith("**Deployed:**"):
                deployed_date = line.split("**Deployed:**")[1].strip()

        return (version, deployed_date) if version else None
    except Exception as e:
        print(f"Error reading marker file: {e}", file=sys.stderr)
        return None


def get_available_version() -> str:
    """Get the available framework version."""
    return FRAMEWORK_VERSION


def compare_versions(deployed: str, available: str) -> int:
    """
    Compare two semantic versions.

    Returns:
        -1 if deployed < available (upgrade needed)
         0 if deployed == available (up to date)
         1 if deployed > available (shouldn't happen)
    """
    try:
        # Parse versions (handle both "2.0" and "1.2.0" formats)
        deployed_parts = [int(x) for x in deployed.split('.')]
        available_parts = [int(x) for x in available.split('.')]

        # Pad to same length
        max_len = max(len(deployed_parts), len(available_parts))
        deployed_parts += [0] * (max_len - len(deployed_parts))
        available_parts += [0] * (max_len - len(available_parts))

        # Compare
        for d, a in zip(deployed_parts, available_parts):
            if d < a:
                return -1
            elif d > a:
                return 1

        return 0
    except (ValueError, AttributeError):
        # If parsing fails, assume versions don't match
        return -1 if deployed != available else 0


def format_upgrade_message(deployed_version: str, available_version: str, deployed_date: str) -> str:
    """Format a message about available upgrades."""
    return f"""
╔══════════════════════════════════════════════════════════════╗
║                 VIBEY FRAMEWORK UPDATE AVAILABLE              ║
╚══════════════════════════════════════════════════════════════╝

Current Version:   {deployed_version} (deployed {deployed_date})
Latest Version:    {available_version} (released {VERSION_DATE})

An update to the Vibey framework is available!

To upgrade:
1. Pull the latest framework code
2. Run: /vibey (select Framework Management)
3. Choose "Upgrade Framework"

Or manually:
1. git pull (in framework repository)
2. Re-deploy: cp -r framework/* .claude/
3. Regenerate marker: Run /vibey to update .vibey/ai-reference.md

Changes in {available_version}:
- 100% Claude Code compatibility (all bash prompts replaced)
- Critical scripts added (generate-config, update-config)
- Sprint state management improvements
- Enhanced deployment pre-flight checks
- Bug fixes and performance improvements

═════════════════════════════════════════════════════════════════
"""


def check_version(marker_file: Path, verbose: bool = False) -> int:
    """
    Check framework version and report status.

    Returns:
        0 if up to date
        1 if upgrade available
        2 if error
    """
    # Read deployed version
    deployed_info = read_deployed_version(marker_file)

    if not deployed_info:
        print("⚠️  Framework version unknown (marker file not found or invalid)")
        print(f"   Expected: {marker_file}")
        print(f"   Available version: {FRAMEWORK_VERSION}")
        return 2

    deployed_version, deployed_date = deployed_info
    available_version = get_available_version()

    # Compare versions
    comparison = compare_versions(deployed_version, available_version)

    if comparison < 0:
        # Upgrade available
        print(format_upgrade_message(deployed_version, available_version, deployed_date))
        return 1
    elif comparison == 0:
        # Up to date
        if verbose:
            print(f"✓ Vibey framework is up to date (v{available_version})")
        return 0
    else:
        # Deployed version is newer (shouldn't happen)
        print(f"⚠️  Deployed version ({deployed_version}) is newer than available ({available_version})")
        print("   This shouldn't happen - you may be on a development branch")
        return 2


def main():
    parser = argparse.ArgumentParser(
        description="Check Vibey framework version and upgrade status"
    )
    parser.add_argument(
        '--deployed-marker',
        type=Path,
        default=None,  # Will auto-detect
        help='Path to marker file (default: .vibey/ai-reference.md)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output (show message even when up to date)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (exit code only, no output except errors)'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show available framework version and exit'
    )

    args = parser.parse_args()

    if args.version:
        print(f"Vibey Framework v{FRAMEWORK_VERSION} ({VERSION_DATE})")
        return 0

    # Auto-detect marker file if not specified
    if args.deployed_marker is None:
        args.deployed_marker = Path('.vibey/ai-reference.md')

    # Check if .vibey/ directory exists first
    vibey_dir = Path('.vibey')
    if not vibey_dir.exists():
        print("❌ No .vibey/ directory found")
        print("   Vibey may not be deployed. Run /vibey to initialize.")
        return 1

    if not args.deployed_marker.exists():
        print("⚠️  .vibey/ exists but ai-reference.md is missing")
        print(f"   Expected: {args.deployed_marker}")
        print()
        print("   Run /vibey to regenerate the AI reference file.")
        return 1

    # Check version
    if args.quiet:
        # Suppress all output except errors
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = check_version(args.deployed_marker, args.verbose)
        finally:
            sys.stdout = old_stdout
        return result
    else:
        return check_version(args.deployed_marker, args.verbose)


if __name__ == '__main__':
    sys.exit(main())
