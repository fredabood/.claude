"""
Submodule detection and discovery.

Implements automatic detection of git submodules with Vibey roadmaps.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: All cross-repo coordination data lives in PARENT repo only.
Submodules have NO knowledge of parent repos.
"""

import configparser
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from vibey.roadmap.models.submodule import (
    DetectionSource,
    SubmoduleReference,
    SyncStatus,
)


@dataclass
class GitmoduleEntry:
    """Raw entry from .gitmodules file."""

    name: str
    path: str
    url: str


@dataclass
class SubmoduleValidation:
    """Result of submodule validation."""

    path: str
    exists: bool
    is_initialized: bool
    has_content: bool
    error: Optional[str] = None


@dataclass
class VibeyRoadmapCheck:
    """Result of checking for vibey roadmap in a submodule."""

    path: str
    has_roadmap: bool
    roadmap_id: Optional[str] = None
    error: Optional[str] = None


class SubmoduleDiscovery:
    """
    Detects and discovers git submodules with Vibey roadmaps.

    This class provides methods for:
    - Parsing .gitmodules file
    - Validating submodule initialization
    - Detecting vibey roadmaps in submodules
    - Building SubmoduleReference registry
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize SubmoduleDiscovery.

        Args:
            repo_root: Path to repository root. Defaults to current directory.
        """
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.vibey_dir = self.repo_root / ".vibey"
        self.config_dir = self.vibey_dir / "config"
        self.submodules_config = self.config_dir / "submodules.yaml"

    def parse_gitmodules(self) -> list[GitmoduleEntry]:
        """
        Parse .gitmodules file using configparser.

        Returns:
            List of raw submodule entries with name, path, and url.
        """
        gitmodules_path = self.repo_root / ".gitmodules"
        if not gitmodules_path.exists():
            return []

        entries = []
        config = configparser.ConfigParser()

        try:
            config.read(str(gitmodules_path))

            for section in config.sections():
                if section.startswith('submodule "') and section.endswith('"'):
                    name = section[11:-1]  # Extract name from 'submodule "name"'
                    path = config.get(section, "path", fallback="")
                    url = config.get(section, "url", fallback="")

                    if path:
                        entries.append(GitmoduleEntry(name=name, path=path, url=url))
        except Exception as e:
            # Log error but continue - may be malformed file
            print(f"Warning: Error parsing .gitmodules: {e}")

        return entries

    def validate_submodule(self, path: str) -> SubmoduleValidation:
        """
        Validate that a submodule is initialized and has content.

        Args:
            path: Relative path to submodule directory.

        Returns:
            SubmoduleValidation with status information.
        """
        submodule_path = self.repo_root / path

        # Check if directory exists
        if not submodule_path.exists():
            return SubmoduleValidation(
                path=path,
                exists=False,
                is_initialized=False,
                has_content=False,
                error="Directory does not exist",
            )

        # Check if directory has content
        has_content = any(submodule_path.iterdir())
        if not has_content:
            return SubmoduleValidation(
                path=path,
                exists=True,
                is_initialized=False,
                has_content=False,
                error="Directory is empty (submodule not initialized)",
            )

        # Run git submodule status to check initialization
        try:
            result = subprocess.run(
                ["git", "submodule", "status", path],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse status output
            # Format: [+- ]<sha1> <path> (<description>)
            # Leading '-' means not initialized, '+' means different commit
            output = result.stdout.strip()
            is_initialized = bool(output) and not output.startswith("-")

            return SubmoduleValidation(
                path=path,
                exists=True,
                is_initialized=is_initialized,
                has_content=has_content,
            )
        except subprocess.TimeoutExpired:
            return SubmoduleValidation(
                path=path,
                exists=True,
                is_initialized=False,
                has_content=has_content,
                error="Timeout checking submodule status",
            )
        except Exception as e:
            return SubmoduleValidation(
                path=path,
                exists=True,
                is_initialized=False,
                has_content=has_content,
                error=str(e),
            )

    def has_vibey_roadmap(self, path: str) -> VibeyRoadmapCheck:
        """
        Check if a submodule has a Vibey roadmap.

        Args:
            path: Relative path to submodule directory.

        Returns:
            VibeyRoadmapCheck with roadmap presence and ID if found.
        """
        submodule_path = self.repo_root / path
        vibey_roadmap_dir = submodule_path / ".vibey" / "roadmap"
        roadmap_yaml = vibey_roadmap_dir / "roadmap.yaml"

        # Also check legacy location
        legacy_roadmap_yaml = submodule_path / ".vibey" / "roadmap.yaml"

        # Check if roadmap directory exists
        if not vibey_roadmap_dir.exists():
            return VibeyRoadmapCheck(
                path=path,
                has_roadmap=False,
            )

        # Try to read roadmap_id from roadmap.yaml
        roadmap_file = roadmap_yaml if roadmap_yaml.exists() else (
            legacy_roadmap_yaml if legacy_roadmap_yaml.exists() else None
        )

        if not roadmap_file:
            # Has .vibey/roadmap/ directory but no roadmap.yaml
            return VibeyRoadmapCheck(
                path=path,
                has_roadmap=True,
                roadmap_id=None,
            )

        try:
            with open(roadmap_file) as f:
                data = yaml.safe_load(f)

            roadmap_id = None
            if isinstance(data, dict):
                # Handle wrapped format: roadmap: { id: ... }
                if "roadmap" in data and isinstance(data["roadmap"], dict):
                    roadmap_id = data["roadmap"].get("id")
                # Handle flat format: id: ...
                elif "id" in data:
                    roadmap_id = data["id"]

            return VibeyRoadmapCheck(
                path=path,
                has_roadmap=True,
                roadmap_id=roadmap_id,
            )
        except Exception as e:
            return VibeyRoadmapCheck(
                path=path,
                has_roadmap=True,
                roadmap_id=None,
                error=f"Error reading roadmap.yaml: {e}",
            )

    def discover(self, write_registry: bool = True) -> list[SubmoduleReference]:
        """
        Discover all submodules with vibey roadmaps.

        This is the main discovery method that:
        1. Parses .gitmodules
        2. Validates each submodule
        3. Checks for vibey roadmaps
        4. Builds SubmoduleReference list
        5. Optionally writes to .vibey/config/submodules.yaml

        Args:
            write_registry: If True, write discovered submodules to config file.

        Returns:
            List of SubmoduleReference objects for valid submodules with roadmaps.
        """
        discovered = []

        # Parse .gitmodules
        entries = self.parse_gitmodules()

        for entry in entries:
            # Validate submodule
            validation = self.validate_submodule(entry.path)
            if not validation.is_initialized:
                continue

            # Check for vibey roadmap
            roadmap_check = self.has_vibey_roadmap(entry.path)
            if not roadmap_check.has_roadmap:
                continue

            # Build SubmoduleReference
            ref = SubmoduleReference(
                path=entry.path,
                roadmap_id=roadmap_check.roadmap_id,
                aggregate=True,
                track_filter=[],
                detection_source=DetectionSource.GITMODULES,
                last_synced=None,
                sync_status=SyncStatus.NEVER_SYNCED,
            )
            discovered.append(ref)

        # Write to registry if requested
        if write_registry and discovered:
            self._write_registry(discovered)

        return discovered

    def get_vibey_submodules(self) -> list[SubmoduleReference]:
        """
        Get currently registered submodules from config file.

        Returns:
            List of SubmoduleReference objects from .vibey/config/submodules.yaml.
        """
        if not self.submodules_config.exists():
            return []

        try:
            with open(self.submodules_config) as f:
                data = yaml.safe_load(f) or {}

            submodules_data = data.get("submodules", [])
            references = []

            for item in submodules_data:
                if not isinstance(item, dict):
                    continue

                ref = SubmoduleReference(
                    path=item.get("path", ""),
                    roadmap_id=item.get("roadmap_id"),
                    aggregate=item.get("aggregate", True),
                    track_filter=item.get("track_filter", []),
                    detection_source=DetectionSource(
                        item.get("detection_source", "gitmodules")
                    ),
                    last_synced=self._parse_datetime(item.get("last_synced")),
                    sync_status=SyncStatus(
                        item.get("sync_status", "never_synced")
                    ),
                )
                references.append(ref)

            return references
        except Exception as e:
            print(f"Warning: Error reading submodules config: {e}")
            return []

    def refresh(self, path: str) -> Optional[SubmoduleReference]:
        """
        Refresh a single submodule's information.

        Re-validates the submodule and updates its entry in the registry.

        Args:
            path: Relative path to submodule.

        Returns:
            Updated SubmoduleReference if valid, None otherwise.
        """
        # Validate submodule
        validation = self.validate_submodule(path)
        if not validation.is_initialized:
            return None

        # Check for vibey roadmap
        roadmap_check = self.has_vibey_roadmap(path)
        if not roadmap_check.has_roadmap:
            return None

        # Load existing references
        existing = self.get_vibey_submodules()

        # Find or create reference
        ref = None
        for existing_ref in existing:
            if existing_ref.path == path:
                ref = existing_ref
                break

        if ref:
            # Update existing
            ref.roadmap_id = roadmap_check.roadmap_id
            ref.last_synced = datetime.now(timezone.utc)
            ref.sync_status = SyncStatus.SYNCED
        else:
            # Create new
            ref = SubmoduleReference(
                path=path,
                roadmap_id=roadmap_check.roadmap_id,
                aggregate=True,
                track_filter=[],
                detection_source=DetectionSource.MANUAL,
                last_synced=datetime.now(timezone.utc),
                sync_status=SyncStatus.SYNCED,
            )
            existing.append(ref)

        # Write updated registry
        self._write_registry(existing)

        return ref

    def _write_registry(self, references: list[SubmoduleReference]) -> None:
        """
        Write submodule references to config file.

        Args:
            references: List of SubmoduleReference objects to write.
        """
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing config to preserve other settings
        existing_data = {}
        if self.submodules_config.exists():
            try:
                with open(self.submodules_config) as f:
                    existing_data = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Build submodules list
        submodules_list = []
        for ref in references:
            item = {
                "path": ref.path,
                "roadmap_id": ref.roadmap_id,
                "aggregate": ref.aggregate,
                "track_filter": ref.track_filter,
                "detection_source": ref.detection_source.value,
                "last_synced": (
                    ref.last_synced.isoformat() if ref.last_synced else None
                ),
                "sync_status": ref.sync_status.value,
            }
            submodules_list.append(item)

        # Update data
        existing_data["submodules"] = submodules_list

        # Ensure default settings exist
        if "default_push_mode" not in existing_data:
            existing_data["default_push_mode"] = "linked"
        if "aggregate_on_status" not in existing_data:
            existing_data["aggregate_on_status"] = True

        # Write file
        with open(self.submodules_config, "w") as f:
            yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse ISO format datetime string."""
        if not value:
            return None
        try:
            # Handle 'Z' suffix
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except Exception:
            return None
