"""
Discover commands.

Provides project discovery, analysis, and version tracking functionality.
"""

from vibey.cli.formatters import format_success, format_error


def discover_run_cmd(
    output_format: str = "yaml",
    save: bool = True,
    project_root: str = ".",
) -> int:
    """Run project discovery and analyze the codebase."""
    from datetime import datetime, timezone
    from pathlib import Path
    import subprocess

    from vibey.operations.discovery import (
        DiscoveryOutput,
        DiscoveryMetadata,
        ProjectInfo,
        StructureInfo,
        DependenciesInfo,
        ProjectType,
        to_yaml,
        to_json,
        DiscoveryVersionManager,
    )

    root = Path(project_root).resolve()

    if not root.exists():
        print(format_error(f"Project root not found: {root}"))
        return 1

    print(f"🔍 Running discovery on: {root}")

    # Gather git info
    git_commit = None
    git_branch = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=root
        )
        if result.returncode == 0:
            git_commit = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=root
        )
        if result.returncode == 0:
            git_branch = result.stdout.strip()
    except Exception:
        pass

    # Create basic discovery output
    # In a full implementation, this would run actual analyzers
    metadata = DiscoveryMetadata(
        discovered_at=datetime.now(timezone.utc),
        project_root=str(root),
        git_commit=git_commit,
        git_branch=git_branch,
    )

    # Detect project name
    project_name = root.name

    # Create minimal project info (actual discovery would analyze files)
    project = ProjectInfo(
        name=project_name,
        type=ProjectType.UNKNOWN,
    )

    discovery = DiscoveryOutput(
        metadata=metadata,
        project=project,
        structure=StructureInfo(),
        dependencies=DependenciesInfo(),
    )

    # Save if requested
    if save:
        discovery_dir = root / ".vibey" / "discovery"
        manager = DiscoveryVersionManager(discovery_dir=discovery_dir)
        saved_path, diff = manager.save(discovery)
        print(format_success(f"Discovery saved to: {saved_path}"))
        if diff and diff.has_significant_changes:
            print(f"📊 Changes: {diff.summary}")

    # Output in requested format
    if output_format == "yaml":
        print("\n" + to_yaml(discovery))
    elif output_format == "json":
        print("\n" + to_json(discovery))
    else:  # text
        print(f"\n📋 Project: {discovery.project.name}")
        print(f"   Type: {discovery.project.type.value}")
        print(f"   Git: {git_branch or 'N/A'} @ {(git_commit or 'N/A')[:8]}")
        print(f"   Discovered: {discovery.metadata.discovered_at.isoformat()}")

    return 0


def discover_show_cmd(
    output_format: str = "text",
    section: str = "all",
) -> int:
    """Show current discovery output."""
    from pathlib import Path

    from vibey.operations.discovery import (
        DiscoveryVersionManager,
        to_yaml,
        to_json,
    )

    discovery_dir = Path.cwd() / ".vibey" / "discovery"
    manager = DiscoveryVersionManager(discovery_dir=discovery_dir)

    discovery = manager.load_current()
    if not discovery:
        print(format_error("No discovery found. Run 'vibey discover run' first."))
        return 1

    # Filter to section if requested
    if section != "all":
        data = discovery.model_dump(exclude_none=True)
        if section not in data:
            print(format_error(f"Unknown section: {section}"))
            return 1
        data = {section: data[section]}

        if output_format == "yaml":
            import yaml
            print(yaml.dump(data, default_flow_style=False))
        elif output_format == "json":
            import json
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"📋 {section.title()}:")
            for k, v in data[section].items():
                print(f"   {k}: {v}")
        return 0

    # Full output
    if output_format == "yaml":
        print(to_yaml(discovery))
    elif output_format == "json":
        print(to_json(discovery))
    else:  # text
        print(f"📋 Project: {discovery.project.name}")
        print(f"   Type: {discovery.project.type.value}")
        print(f"   Confidence: {discovery.project.type_confidence}%")

        if discovery.project.languages:
            langs = ", ".join(f"{l.name} ({l.percentage}%)"
                            for l in discovery.project.languages)
            print(f"   Languages: {langs}")

        if discovery.project.frameworks:
            fws = ", ".join(f.name for f in discovery.project.frameworks)
            print(f"   Frameworks: {fws}")

        print(f"\n📁 Structure:")
        print(f"   Files: {discovery.structure.total_files}")
        print(f"   Lines: {discovery.structure.total_lines}")

        if discovery.structure.architecture_pattern:
            print(f"   Pattern: {discovery.structure.architecture_pattern.value}")

        print(f"\n📦 Dependencies:")
        print(f"   Runtime: {len(discovery.dependencies.runtime)}")
        print(f"   Development: {len(discovery.dependencies.development)}")
        if discovery.dependencies.vulnerable_count > 0:
            print(f"   ⚠️ Vulnerabilities: {discovery.dependencies.vulnerable_count}")

        print(f"\n⏰ Discovered: {discovery.metadata.discovered_at.isoformat()}")
        if discovery.metadata.git_branch:
            print(f"   Git: {discovery.metadata.git_branch} @ {discovery.metadata.git_commit[:8] if discovery.metadata.git_commit else 'N/A'}")

    return 0


def discover_status_cmd(max_age_hours: int = 24) -> int:
    """Check if current discovery is stale."""
    from pathlib import Path

    from vibey.operations.discovery import DiscoveryVersionManager

    discovery_dir = Path.cwd() / ".vibey" / "discovery"
    manager = DiscoveryVersionManager(discovery_dir=discovery_dir)

    is_stale, reason = manager.is_stale(max_age_hours=max_age_hours)

    if is_stale:
        print(f"⚠️  Discovery is STALE: {reason}")
        print("   Run 'vibey discover refresh' to update.")
        return 1
    else:
        print(f"✅ Discovery is current: {reason}")
        return 0


def discover_history_cmd(limit: int = 10) -> int:
    """List discovery version history."""
    from pathlib import Path

    from vibey.operations.discovery import DiscoveryVersionManager

    discovery_dir = Path.cwd() / ".vibey" / "discovery"
    manager = DiscoveryVersionManager(discovery_dir=discovery_dir)

    versions = manager.list_versions(limit=limit)

    if not versions:
        print("No discovery history found.")
        return 0

    print(f"📜 Discovery History ({len(versions)} versions)")
    print("=" * 60)

    for v in versions:
        marker = " 📌 CURRENT" if v.is_current else ""
        time_str = v.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        git_info = f" ({v.git_branch})" if v.git_branch else ""
        print(f"  {time_str}{git_info}{marker}")

    return 0


def discover_diff_cmd(
    from_version: str = None,
    to_version: str = "current",
) -> int:
    """Compare two discovery versions."""
    from pathlib import Path

    from vibey.operations.discovery import DiscoveryVersionManager

    discovery_dir = Path.cwd() / ".vibey" / "discovery"
    manager = DiscoveryVersionManager(discovery_dir=discovery_dir)

    diff = manager.get_diff(from_version=from_version, to_version=to_version)

    if not diff:
        print(format_error("Could not compute diff. Check version identifiers."))
        return 1

    print(f"📊 Discovery Diff")
    print(f"   From: {diff.from_version}")
    print(f"   To:   {diff.to_version}")
    print("=" * 60)

    if not diff.has_significant_changes:
        print("No significant changes detected.")
        return 0

    print(f"\n📋 Summary: {diff.summary}")

    if diff.project_changes:
        print("\n🏗️  Project Changes:")
        for k, v in diff.project_changes.items():
            print(f"   {k}: {v}")

    if diff.structure_changes:
        print("\n📁 Structure Changes:")
        for k, v in diff.structure_changes.items():
            print(f"   {k}: {v}")

    if diff.dependencies_changes:
        print("\n📦 Dependency Changes:")
        for k, v in diff.dependencies_changes.items():
            print(f"   {k}: {v}")

    return 0


def discover_refresh_cmd(force: bool = False) -> int:
    """Refresh discovery if stale."""
    from pathlib import Path

    from vibey.operations.discovery import DiscoveryVersionManager

    discovery_dir = Path.cwd() / ".vibey" / "discovery"
    manager = DiscoveryVersionManager(discovery_dir=discovery_dir)

    if not force:
        is_stale, reason = manager.is_stale()
        if not is_stale:
            print(f"✅ Discovery is current: {reason}")
            print("   Use --force to refresh anyway.")
            return 0

    # Run discovery
    return discover_run_cmd(output_format="text", save=True, project_root=".")
