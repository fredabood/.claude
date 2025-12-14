"""Discovery versioning for tracking changes over time.

This module provides versioned storage for discovery outputs,
enabling change tracking, diffing, and correlation with project evolution.

Storage Structure:
    .vibey/discovery/
    ├── current.yaml           # Latest discovery
    ├── history/
    │   ├── 2025-12-12T10-00-00.yaml
    │   └── 2025-12-11T15-30-00.yaml
    └── diffs/
        └── 2025-12-12T10-00-00.diff.yaml
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schema import DiscoveryOutput
from .serializers import DiscoverySerializer


@dataclass
class DiscoveryVersion:
    """Information about a discovery version."""

    timestamp: datetime
    filepath: Path
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    is_current: bool = False


@dataclass
class DiscoveryDiff:
    """Differences between two discovery outputs."""

    from_version: str
    to_version: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Changes by section
    project_changes: Dict[str, Any] = field(default_factory=dict)
    structure_changes: Dict[str, Any] = field(default_factory=dict)
    dependencies_changes: Dict[str, Any] = field(default_factory=dict)
    patterns_changes: Dict[str, Any] = field(default_factory=dict)
    conventions_changes: Dict[str, Any] = field(default_factory=dict)
    quality_changes: Dict[str, Any] = field(default_factory=dict)

    # Summary
    has_significant_changes: bool = False
    summary: str = ""


class DiscoveryVersionManager:
    """Manages versioned discovery outputs.

    Provides:
    - Storage of discovery history
    - Diff capability between versions
    - Retention policy enforcement
    - History queries
    """

    def __init__(
        self,
        discovery_dir: Optional[Path] = None,
        max_history: int = 10,
        keep_milestones: bool = True,
    ):
        """Initialize the version manager.

        Args:
            discovery_dir: Base directory for discovery storage.
                           Defaults to .vibey/discovery/
            max_history: Maximum number of history entries to keep
            keep_milestones: Whether to keep milestone discoveries
        """
        self.discovery_dir = discovery_dir or Path(".vibey/discovery")
        self.current_file = self.discovery_dir / "current.yaml"
        self.history_dir = self.discovery_dir / "history"
        self.diffs_dir = self.discovery_dir / "diffs"
        self.max_history = max_history
        self.keep_milestones = keep_milestones

    def _ensure_dirs(self) -> None:
        """Ensure all required directories exist."""
        self.discovery_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.diffs_dir.mkdir(parents=True, exist_ok=True)

    def _timestamp_to_filename(self, ts: datetime) -> str:
        """Convert timestamp to filename-safe string."""
        return ts.strftime("%Y-%m-%dT%H-%M-%S")

    def _filename_to_timestamp(self, filename: str) -> datetime:
        """Convert filename back to timestamp."""
        # Remove .yaml extension if present
        name = filename.replace(".yaml", "").replace(".diff", "")
        return datetime.strptime(name, "%Y-%m-%dT%H-%M-%S").replace(
            tzinfo=timezone.utc
        )

    def save(
        self,
        discovery: DiscoveryOutput,
        create_diff: bool = True,
    ) -> Tuple[Path, Optional[DiscoveryDiff]]:
        """Save a discovery output with versioning.

        Args:
            discovery: The discovery output to save
            create_diff: Whether to create a diff from previous

        Returns:
            Tuple of (path to saved file, diff if created)
        """
        self._ensure_dirs()

        # Get previous discovery for diff
        previous = None
        diff = None
        if create_diff and self.current_file.exists():
            try:
                previous = self.load_current()
            except Exception:
                pass  # No previous or invalid

        # Move current to history if it exists
        if self.current_file.exists():
            try:
                current = self.load_current()
                timestamp = current.metadata.discovered_at
                history_file = (
                    self.history_dir / f"{self._timestamp_to_filename(timestamp)}.yaml"
                )
                shutil.copy2(self.current_file, history_file)
            except Exception:
                # If we can't read current, just overwrite
                pass

        # Save new current
        DiscoverySerializer.save_yaml(discovery, self.current_file)

        # Create diff if requested and we have previous
        if create_diff and previous:
            diff = self.create_diff(previous, discovery)
            if diff.has_significant_changes:
                diff_file = (
                    self.diffs_dir
                    / f"{self._timestamp_to_filename(discovery.metadata.discovered_at)}.diff.yaml"
                )
                self._save_diff(diff, diff_file)

        # Enforce retention policy
        self._enforce_retention()

        return self.current_file, diff

    def _save_diff(self, diff: DiscoveryDiff, path: Path) -> None:
        """Save a diff to file."""
        import yaml

        data = {
            "from_version": diff.from_version,
            "to_version": diff.to_version,
            "timestamp": diff.timestamp.isoformat(),
            "has_significant_changes": diff.has_significant_changes,
            "summary": diff.summary,
            "changes": {
                "project": diff.project_changes,
                "structure": diff.structure_changes,
                "dependencies": diff.dependencies_changes,
                "patterns": diff.patterns_changes,
                "conventions": diff.conventions_changes,
                "quality": diff.quality_changes,
            },
        }
        path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def load_current(self) -> Optional[DiscoveryOutput]:
        """Load the current discovery output.

        Returns:
            Current discovery output or None if not found
        """
        if not self.current_file.exists():
            return None
        return DiscoverySerializer.load_yaml(self.current_file)

    def load_version(self, version: str) -> Optional[DiscoveryOutput]:
        """Load a specific version from history.

        Args:
            version: Version identifier (timestamp string or 'current')

        Returns:
            Discovery output or None if not found
        """
        if version == "current":
            return self.load_current()

        # Try to find in history
        history_file = self.history_dir / f"{version}.yaml"
        if history_file.exists():
            return DiscoverySerializer.load_yaml(history_file)

        # Try with .yaml extension added
        if not version.endswith(".yaml"):
            history_file = self.history_dir / f"{version}.yaml"
            if history_file.exists():
                return DiscoverySerializer.load_yaml(history_file)

        return None

    def list_versions(self, limit: Optional[int] = None) -> List[DiscoveryVersion]:
        """List available discovery versions.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of versions, newest first
        """
        versions = []

        # Add current if exists
        if self.current_file.exists():
            try:
                current = self.load_current()
                if current:
                    versions.append(
                        DiscoveryVersion(
                            timestamp=current.metadata.discovered_at,
                            filepath=self.current_file,
                            git_commit=current.metadata.git_commit,
                            git_branch=current.metadata.git_branch,
                            is_current=True,
                        )
                    )
            except Exception:
                pass

        # Add history versions
        if self.history_dir.exists():
            for filepath in sorted(
                self.history_dir.glob("*.yaml"), reverse=True
            ):
                try:
                    ts = self._filename_to_timestamp(filepath.stem)
                    versions.append(
                        DiscoveryVersion(
                            timestamp=ts,
                            filepath=filepath,
                            is_current=False,
                        )
                    )
                except Exception:
                    continue

        # Apply limit
        if limit:
            versions = versions[:limit]

        return versions

    def create_diff(
        self,
        from_discovery: DiscoveryOutput,
        to_discovery: DiscoveryOutput,
    ) -> DiscoveryDiff:
        """Create a diff between two discovery outputs.

        Args:
            from_discovery: Earlier discovery output
            to_discovery: Later discovery output

        Returns:
            DiscoveryDiff with changes
        """
        diff = DiscoveryDiff(
            from_version=from_discovery.metadata.discovered_at.isoformat(),
            to_version=to_discovery.metadata.discovered_at.isoformat(),
        )

        # Compare project info
        diff.project_changes = self._diff_project(
            from_discovery.project, to_discovery.project
        )

        # Compare structure
        diff.structure_changes = self._diff_structure(
            from_discovery.structure, to_discovery.structure
        )

        # Compare dependencies
        diff.dependencies_changes = self._diff_dependencies(
            from_discovery.dependencies, to_discovery.dependencies
        )

        # Compare patterns
        diff.patterns_changes = self._diff_section(
            from_discovery.patterns, to_discovery.patterns, "patterns"
        )

        # Compare conventions
        diff.conventions_changes = self._diff_section(
            from_discovery.conventions, to_discovery.conventions, "conventions"
        )

        # Compare quality
        diff.quality_changes = self._diff_section(
            from_discovery.quality, to_discovery.quality, "quality"
        )

        # Determine significance
        diff.has_significant_changes = self._is_significant(diff)
        diff.summary = self._generate_summary(diff)

        return diff

    def _diff_project(self, from_proj: Any, to_proj: Any) -> Dict[str, Any]:
        """Compare project info."""
        changes = {}

        if from_proj.type != to_proj.type:
            changes["type"] = {"from": from_proj.type.value, "to": to_proj.type.value}

        # Compare languages
        from_langs = {l.name for l in from_proj.languages}
        to_langs = {l.name for l in to_proj.languages}
        added_langs = to_langs - from_langs
        removed_langs = from_langs - to_langs
        if added_langs or removed_langs:
            changes["languages"] = {
                "added": list(added_langs),
                "removed": list(removed_langs),
            }

        # Compare frameworks
        from_fw = {f.name for f in from_proj.frameworks}
        to_fw = {f.name for f in to_proj.frameworks}
        added_fw = to_fw - from_fw
        removed_fw = from_fw - to_fw
        if added_fw or removed_fw:
            changes["frameworks"] = {
                "added": list(added_fw),
                "removed": list(removed_fw),
            }

        return changes

    def _diff_structure(self, from_struct: Any, to_struct: Any) -> Dict[str, Any]:
        """Compare structure info."""
        changes = {}

        # File/line count changes
        file_diff = to_struct.total_files - from_struct.total_files
        line_diff = to_struct.total_lines - from_struct.total_lines

        if abs(file_diff) > 0:
            changes["files"] = {
                "from": from_struct.total_files,
                "to": to_struct.total_files,
                "change": file_diff,
            }

        if abs(line_diff) > 50:  # Only report significant line changes
            changes["lines"] = {
                "from": from_struct.total_lines,
                "to": to_struct.total_lines,
                "change": line_diff,
            }

        # Compare directories
        from_dirs = {d.path for d in from_struct.directories}
        to_dirs = {d.path for d in to_struct.directories}
        added_dirs = to_dirs - from_dirs
        removed_dirs = from_dirs - to_dirs
        if added_dirs or removed_dirs:
            changes["directories"] = {
                "added": list(added_dirs),
                "removed": list(removed_dirs),
            }

        # Compare entry points
        from_ep = set(from_struct.entry_points)
        to_ep = set(to_struct.entry_points)
        if from_ep != to_ep:
            changes["entry_points"] = {
                "added": list(to_ep - from_ep),
                "removed": list(from_ep - to_ep),
            }

        return changes

    def _diff_dependencies(self, from_deps: Any, to_deps: Any) -> Dict[str, Any]:
        """Compare dependencies."""
        changes = {}

        # Runtime dependencies
        from_rt = {d.name for d in from_deps.runtime}
        to_rt = {d.name for d in to_deps.runtime}
        added_rt = to_rt - from_rt
        removed_rt = from_rt - to_rt
        if added_rt or removed_rt:
            changes["runtime"] = {
                "added": list(added_rt),
                "removed": list(removed_rt),
            }

        # Dev dependencies
        from_dev = {d.name for d in from_deps.development}
        to_dev = {d.name for d in to_deps.development}
        added_dev = to_dev - from_dev
        removed_dev = from_dev - to_dev
        if added_dev or removed_dev:
            changes["development"] = {
                "added": list(added_dev),
                "removed": list(removed_dev),
            }

        # Vulnerability changes
        if from_deps.vulnerable_count != to_deps.vulnerable_count:
            changes["vulnerabilities"] = {
                "from": from_deps.vulnerable_count,
                "to": to_deps.vulnerable_count,
            }

        return changes

    def _diff_section(
        self, from_section: Any, to_section: Any, name: str
    ) -> Dict[str, Any]:
        """Generic section diff."""
        changes = {}

        # Handle None cases
        from_data = from_section.model_dump() if from_section else {}
        to_data = to_section.model_dump() if to_section else {}

        if from_data != to_data:
            changes["modified"] = True
            # For simplicity, just note it changed
            # A more sophisticated diff could be implemented

        return changes

    def _is_significant(self, diff: DiscoveryDiff) -> bool:
        """Determine if diff has significant changes."""
        # Significant if:
        # - Project type changed
        # - Languages or frameworks changed
        # - Significant file/line count changes
        # - Dependencies changed
        # - Vulnerabilities changed

        if diff.project_changes.get("type"):
            return True

        if diff.project_changes.get("languages"):
            return True

        if diff.project_changes.get("frameworks"):
            return True

        if diff.structure_changes.get("files"):
            file_change = abs(diff.structure_changes["files"].get("change", 0))
            if file_change >= 5:
                return True

        if diff.dependencies_changes.get("runtime"):
            return True

        if diff.dependencies_changes.get("vulnerabilities"):
            return True

        return False

    def _generate_summary(self, diff: DiscoveryDiff) -> str:
        """Generate human-readable summary of changes."""
        parts = []

        if diff.project_changes.get("type"):
            parts.append(
                f"Project type: {diff.project_changes['type']['from']} → {diff.project_changes['type']['to']}"
            )

        if diff.project_changes.get("frameworks"):
            fw = diff.project_changes["frameworks"]
            if fw.get("added"):
                parts.append(f"Added frameworks: {', '.join(fw['added'])}")
            if fw.get("removed"):
                parts.append(f"Removed frameworks: {', '.join(fw['removed'])}")

        if diff.structure_changes.get("files"):
            change = diff.structure_changes["files"]["change"]
            sign = "+" if change > 0 else ""
            parts.append(f"Files: {sign}{change}")

        if diff.dependencies_changes.get("runtime"):
            deps = diff.dependencies_changes["runtime"]
            if deps.get("added"):
                parts.append(f"New deps: {', '.join(deps['added'][:3])}")
            if deps.get("removed"):
                parts.append(f"Removed deps: {', '.join(deps['removed'][:3])}")

        if diff.dependencies_changes.get("vulnerabilities"):
            vuln = diff.dependencies_changes["vulnerabilities"]
            parts.append(f"Vulnerabilities: {vuln['from']} → {vuln['to']}")

        return "; ".join(parts) if parts else "No significant changes"

    def _enforce_retention(self) -> None:
        """Enforce retention policy on history."""
        if not self.history_dir.exists():
            return

        history_files = sorted(self.history_dir.glob("*.yaml"), reverse=True)

        if len(history_files) <= self.max_history:
            return

        # Remove oldest files beyond retention limit
        for filepath in history_files[self.max_history :]:
            try:
                os.remove(filepath)
                # Also remove corresponding diff if exists
                diff_file = (
                    self.diffs_dir / f"{filepath.stem}.diff.yaml"
                )
                if diff_file.exists():
                    os.remove(diff_file)
            except Exception:
                pass

    def get_diff(
        self,
        from_version: Optional[str] = None,
        to_version: str = "current",
    ) -> Optional[DiscoveryDiff]:
        """Get or compute diff between versions.

        Args:
            from_version: Earlier version (defaults to previous)
            to_version: Later version (defaults to current)

        Returns:
            DiscoveryDiff or None if versions not found
        """
        # Load to_version
        to_discovery = self.load_version(to_version)
        if not to_discovery:
            return None

        # If no from_version, use previous in history
        if not from_version:
            versions = self.list_versions()
            if len(versions) < 2:
                return None
            from_version = self._timestamp_to_filename(versions[1].timestamp)

        # Load from_version
        from_discovery = self.load_version(from_version)
        if not from_discovery:
            return None

        return self.create_diff(from_discovery, to_discovery)

    def is_stale(
        self,
        max_age_hours: int = 24,
        check_git: bool = True,
    ) -> Tuple[bool, str]:
        """Check if current discovery is stale.

        Args:
            max_age_hours: Maximum age before considered stale
            check_git: Whether to check git commit

        Returns:
            Tuple of (is_stale, reason)
        """
        current = self.load_current()
        if not current:
            return True, "No discovery exists"

        # Check age
        age = datetime.now(timezone.utc) - current.metadata.discovered_at
        if age.total_seconds() > max_age_hours * 3600:
            return True, f"Discovery is {age.days} days old"

        # Check git commit if requested
        if check_git and current.metadata.git_commit:
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=current.metadata.project_root,
                )
                if result.returncode == 0:
                    current_commit = result.stdout.strip()
                    if current_commit != current.metadata.git_commit:
                        return True, "Git commit has changed"
            except Exception:
                pass

        return False, "Discovery is current"


# Convenience function
def get_version_manager(
    discovery_dir: Optional[Path] = None,
) -> DiscoveryVersionManager:
    """Get a configured version manager instance."""
    return DiscoveryVersionManager(discovery_dir=discovery_dir)
