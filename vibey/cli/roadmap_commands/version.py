"""
'roadmap version' command - Manage roadmap versioning.
"""

import sys
from pathlib import Path

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.serialization import load_roadmap
from filesystem import FileSystemManager, find_roadmap_root
from versioning import VersionManager


def handle_version(args):
    """Handle 'roadmap version' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)
    roadmap_path = fs.get_roadmap_path()

    if not roadmap_path.exists():
        print("❌ Roadmap not found")
        sys.exit(1)

    roadmap = load_roadmap(roadmap_path)
    version_mgr = VersionManager(root_dir)

    # Show current version
    if args.show:
        print(f"Current version: {roadmap.version}")
        print(f"Bump strategy: {roadmap.version_strategy.bump_on}")
        print(f"Bump type: {roadmap.version_strategy.bump_type}")
        sys.exit(0)

    # Bump version
    if args.bump:
        bump_type = args.type or roadmap.version_strategy.bump_type

        try:
            old_version, new_version = version_mgr.bump_roadmap_version(
                bump_type=bump_type,
                message=args.message
            )

            print(f"✅ Version bumped: {old_version} → {new_version}")

            if args.tag:
                # Create git tag if requested
                import subprocess
                tag_name = f"v{new_version}"
                result = subprocess.run(
                    ["git", "tag", "-a", tag_name, "-m", f"Release {new_version}"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(f"✅ Git tag created: {tag_name}")
                else:
                    print(f"⚠️  Failed to create git tag: {result.stderr}")

        except Exception as e:
            print(f"❌ Failed to bump version: {e}")
            sys.exit(1)
