"""
Markdown migration for roadmap documentation fields.

Migrates documentation-like fields from YAML to markdown files:
- version_strategy → VERSIONING_POLICY.md
- version_history → CHANGELOG.md
- metadata.notes → NOTES.md (per-entity)

This provides better formatting, diffability, and human readability
while keeping YAML files clean with just structured data.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


# ==============================================================================
# Templates
# ==============================================================================

VERSIONING_POLICY_TEMPLATE = """# Versioning Policy

This document describes the versioning strategy for the roadmap.

## Semantic Versioning Rules

| Version Component | Trigger |
|-------------------|---------|
| **Major** | {major_on} |
| **Minor** | {minor_on} |
| **Patch** | {patch_on} |

## Current Version

{version}

## Automation

Version bumps are triggered by:
- `vibey roadmap version --bump major` - Manual major bump
- `vibey roadmap version --bump minor` - Manual minor bump
- `vibey roadmap version --bump patch` - Manual patch bump

Auto-bump may be enabled based on the triggers defined above.
"""

CHANGELOG_TEMPLATE = """# Changelog

All notable changes to this roadmap are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{entries}
"""

CHANGELOG_ENTRY_TEMPLATE = """## [{version}] - {date}

### Changes
{changes}

### Summary
{summary}
"""

NOTES_TEMPLATE = """# Implementation Notes

{content}
"""


# ==============================================================================
# Migration Functions
# ==============================================================================

def migrate_version_strategy(
    legacy_data: Dict[str, Any],
    roadmap_dir: Path,
    dry_run: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Migrate version_strategy to VERSIONING_POLICY.md.

    Args:
        legacy_data: Dict containing version_strategy field
        roadmap_dir: Path to roadmap directory
        dry_run: If True, only report what would happen

    Returns:
        Tuple of (migrated: bool, file_path: Optional[str])
    """
    vs = legacy_data.get('version_strategy')
    if not vs:
        return False, None

    policy_file = roadmap_dir / 'VERSIONING_POLICY.md'

    if policy_file.exists() and not dry_run:
        logger.debug(f"VERSIONING_POLICY.md already exists at {policy_file}")
        return False, None

    # Extract version strategy fields
    major_on = vs.get('major_on', 'roadmap_milestone')
    minor_on = vs.get('minor_on', 'track_completion')
    patch_on = vs.get('patch_on', 'sprint_production_ready')

    # Handle enum values if present
    if hasattr(major_on, 'value'):
        major_on = major_on.value
    if hasattr(minor_on, 'value'):
        minor_on = minor_on.value
    if hasattr(patch_on, 'value'):
        patch_on = patch_on.value

    # Format trigger descriptions
    trigger_map = {
        'roadmap_milestone': 'Roadmap milestone completion',
        'track_completion': 'Track completion',
        'sprint_production_ready': 'Sprint marked production ready',
        'sprint_completion': 'Sprint completion',
        'manual': 'Manual version bump only',
    }

    major_desc = trigger_map.get(major_on, major_on)
    minor_desc = trigger_map.get(minor_on, minor_on)
    patch_desc = trigger_map.get(patch_on, patch_on)

    # Get current version
    version = legacy_data.get('version', '0.1.0')

    content = VERSIONING_POLICY_TEMPLATE.format(
        major_on=major_desc,
        minor_on=minor_desc,
        patch_on=patch_desc,
        version=version,
    )

    if dry_run:
        logger.info(f"Would create {policy_file}")
        return True, str(policy_file)

    policy_file.write_text(content)
    logger.info(f"Migrated version_strategy to {policy_file}")
    return True, str(policy_file)


def migrate_version_history(
    legacy_data: Dict[str, Any],
    repo_root: Path,
    dry_run: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Migrate version_history to CHANGELOG.md.

    Args:
        legacy_data: Dict containing version_history field
        repo_root: Path to repository root
        dry_run: If True, only report what would happen

    Returns:
        Tuple of (migrated: bool, file_path: Optional[str])
    """
    vh = legacy_data.get('version_history', [])
    if not vh:
        return False, None

    changelog_file = repo_root / 'CHANGELOG.md'

    if changelog_file.exists() and not dry_run:
        logger.debug(f"CHANGELOG.md already exists at {changelog_file}")
        return False, None

    # Format entries
    entries_content = []
    for entry in vh:
        version = entry.get('version', 'Unknown')
        date_val = entry.get('date', entry.get('released_at', ''))

        # Format date
        if hasattr(date_val, 'strftime'):
            date_str = date_val.strftime('%Y-%m-%d')
        elif date_val:
            date_str = str(date_val)[:10]  # Take first 10 chars (YYYY-MM-DD)
        else:
            date_str = 'Unreleased'

        changes = entry.get('changes', [])
        if isinstance(changes, list):
            changes_str = '\n'.join(f'- {c}' for c in changes)
        else:
            changes_str = f'- {changes}'

        summary = entry.get('summary', entry.get('description', ''))

        entry_content = CHANGELOG_ENTRY_TEMPLATE.format(
            version=version,
            date=date_str,
            changes=changes_str or '- No changes recorded',
            summary=summary or 'No summary provided.',
        )
        entries_content.append(entry_content)

    content = CHANGELOG_TEMPLATE.format(
        entries='\n'.join(entries_content) if entries_content else '## [Unreleased]\n\nNo releases yet.'
    )

    if dry_run:
        logger.info(f"Would create {changelog_file}")
        return True, str(changelog_file)

    changelog_file.write_text(content)
    logger.info(f"Migrated version_history to {changelog_file}")
    return True, str(changelog_file)


def migrate_metadata_notes(
    legacy_data: Dict[str, Any],
    entity_dir: Path,
    dry_run: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Migrate metadata.notes to NOTES.md.

    Args:
        legacy_data: Dict containing metadata.notes field
        entity_dir: Path to entity directory (track/sprint/task)
        dry_run: If True, only report what would happen

    Returns:
        Tuple of (migrated: bool, file_path: Optional[str])
    """
    metadata = legacy_data.get('metadata', {})
    if not isinstance(metadata, dict):
        return False, None

    notes = metadata.get('notes')
    if not notes:
        return False, None

    notes_file = entity_dir / 'NOTES.md'

    if notes_file.exists() and not dry_run:
        logger.debug(f"NOTES.md already exists at {notes_file}")
        return False, None

    # Handle string notes
    if isinstance(notes, str):
        content = NOTES_TEMPLATE.format(content=notes.strip())
    else:
        # Assume it's a dict or complex object, convert to string
        content = NOTES_TEMPLATE.format(content=str(notes))

    if dry_run:
        logger.info(f"Would create {notes_file}")
        return True, str(notes_file)

    notes_file.write_text(content)
    logger.info(f"Migrated metadata.notes to {notes_file}")
    return True, str(notes_file)


def merge_metadata_description(
    legacy_data: Dict[str, Any],
) -> Optional[str]:
    """
    Merge metadata.purpose and metadata.description into a single description.

    Args:
        legacy_data: Dict containing metadata.purpose and/or metadata.description

    Returns:
        Merged description string or None
    """
    metadata = legacy_data.get('metadata', {})
    if not isinstance(metadata, dict):
        return None

    purpose = metadata.get('purpose')
    description = metadata.get('description')

    # Prefer existing description, fall back to purpose
    if description:
        return description
    elif purpose:
        return purpose
    else:
        return None


# ==============================================================================
# Batch Migration
# ==============================================================================

class MigrationResult:
    """Result of a migration operation."""

    def __init__(self):
        self.migrated_files: List[str] = []
        self.skipped_files: List[str] = []
        self.errors: List[Tuple[str, str]] = []

    @property
    def total_migrated(self) -> int:
        return len(self.migrated_files)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped_files)

    @property
    def total_errors(self) -> int:
        return len(self.errors)

    def add_migrated(self, file_path: str) -> None:
        self.migrated_files.append(file_path)

    def add_skipped(self, file_path: str) -> None:
        self.skipped_files.append(file_path)

    def add_error(self, file_path: str, error: str) -> None:
        self.errors.append((file_path, error))


def migrate_roadmap_docs(
    roadmap_dir: Path,
    repo_root: Optional[Path] = None,
    dry_run: bool = False,
    verbose: bool = False
) -> MigrationResult:
    """
    Migrate all documentation fields from YAML to markdown.

    Scans all YAML files in the roadmap directory and:
    - Migrates version_strategy to VERSIONING_POLICY.md
    - Migrates version_history to CHANGELOG.md
    - Migrates metadata.notes to NOTES.md files

    Args:
        roadmap_dir: Path to roadmap directory (.vibey/roadmap)
        repo_root: Path to repository root (default: roadmap_dir parent's parent)
        dry_run: If True, only report what would happen
        verbose: If True, log detailed progress

    Returns:
        MigrationResult with details of migrated/skipped files
    """
    import yaml

    result = MigrationResult()

    if repo_root is None:
        repo_root = roadmap_dir.parent.parent

    # Find roadmap.yaml and migrate roadmap-level fields
    roadmap_file = roadmap_dir / 'roadmap.yaml'
    if roadmap_file.exists():
        try:
            with open(roadmap_file, 'r') as f:
                data = yaml.safe_load(f)

            if data and 'roadmap' in data:
                roadmap_data = data['roadmap']

                # Migrate version_strategy
                migrated, path = migrate_version_strategy(
                    roadmap_data, roadmap_dir, dry_run
                )
                if migrated and path:
                    result.add_migrated(path)
                elif not migrated and roadmap_data.get('version_strategy'):
                    result.add_skipped(str(roadmap_dir / 'VERSIONING_POLICY.md'))

                # Migrate version_history
                migrated, path = migrate_version_history(
                    roadmap_data, repo_root, dry_run
                )
                if migrated and path:
                    result.add_migrated(path)
                elif not migrated and roadmap_data.get('version_history'):
                    result.add_skipped(str(repo_root / 'CHANGELOG.md'))

        except Exception as e:
            result.add_error(str(roadmap_file), str(e))

    # Find all track.yaml files
    track_files = list(roadmap_dir.glob('*/track.yaml'))
    for track_file in track_files:
        try:
            with open(track_file, 'r') as f:
                data = yaml.safe_load(f)

            if data and 'track' in data:
                track_data = data['track']
                track_dir = track_file.parent

                # Migrate metadata.notes
                migrated, path = migrate_metadata_notes(
                    track_data, track_dir, dry_run
                )
                if migrated and path:
                    result.add_migrated(path)
                elif not migrated and track_data.get('metadata', {}).get('notes'):
                    result.add_skipped(str(track_dir / 'NOTES.md'))

        except Exception as e:
            result.add_error(str(track_file), str(e))

    # Find all sprint.yaml files
    sprint_files = list(roadmap_dir.glob('*/*/sprint.yaml'))
    for sprint_file in sprint_files:
        try:
            with open(sprint_file, 'r') as f:
                data = yaml.safe_load(f)

            if data and 'sprint' in data:
                sprint_data = data['sprint']
                sprint_dir = sprint_file.parent

                # Migrate metadata.notes (sprint.metadata.notes is rarely used but check)
                migrated, path = migrate_metadata_notes(
                    sprint_data, sprint_dir, dry_run
                )
                if migrated and path:
                    result.add_migrated(path)

        except Exception as e:
            result.add_error(str(sprint_file), str(e))

    # Find all task.yaml files
    task_files = list(roadmap_dir.glob('*/*/*/task.yaml'))
    for task_file in task_files:
        try:
            with open(task_file, 'r') as f:
                data = yaml.safe_load(f)

            if data and 'task' in data:
                task_data = data['task']
                task_dir = task_file.parent

                # Migrate metadata.notes
                migrated, path = migrate_metadata_notes(
                    task_data, task_dir, dry_run
                )
                if migrated and path:
                    result.add_migrated(path)

        except Exception as e:
            result.add_error(str(task_file), str(e))

    return result


# ==============================================================================
# CLI Helper Functions
# ==============================================================================

def format_migration_report(result: MigrationResult, verbose: bool = False) -> str:
    """Format migration result for CLI output."""
    lines = []

    lines.append("\nMigration Summary")
    lines.append("=" * 50)
    lines.append(f"Files migrated: {result.total_migrated}")
    lines.append(f"Files skipped:  {result.total_skipped}")
    lines.append(f"Errors:         {result.total_errors}")

    if verbose and result.migrated_files:
        lines.append("\nMigrated Files:")
        for f in result.migrated_files:
            lines.append(f"  + {f}")

    if verbose and result.skipped_files:
        lines.append("\nSkipped Files (already exist):")
        for f in result.skipped_files:
            lines.append(f"  - {f}")

    if result.errors:
        lines.append("\nErrors:")
        for file_path, error in result.errors:
            lines.append(f"  ! {file_path}: {error}")

    return '\n'.join(lines)
