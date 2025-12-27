"""
Submodule configuration loader.

This module provides functions for loading and saving submodule integration
configuration from .vibey/config/submodules.yaml.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: Config lives in PARENT repo only. Submodules have no knowledge
of being submodules.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from vibey.roadmap.models.cross_repo import (
    PushMode,
    SubmoduleConfig,
)
from vibey.roadmap.models.submodule import (
    DetectionSource,
    SubmoduleReference,
    SyncStatus,
)


def get_submodule_config_path(repo_path: Optional[Path] = None) -> Path:
    """
    Get the path to submodules.yaml config file.

    Args:
        repo_path: Repository root path. Defaults to cwd.

    Returns:
        Path to .vibey/config/submodules.yaml
    """
    if repo_path is None:
        repo_path = Path.cwd()
    return Path(repo_path) / ".vibey" / "config" / "submodules.yaml"


def load_submodule_config(repo_path: Optional[Path] = None) -> SubmoduleConfig:
    """
    Load submodule configuration from .vibey/config/submodules.yaml.

    Args:
        repo_path: Repository root path. Defaults to cwd.

    Returns:
        SubmoduleConfig loaded from file, or default config if file doesn't exist.
    """
    config_path = get_submodule_config_path(repo_path)

    if not config_path.exists():
        return get_default_config()

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        return _parse_config_data(data)
    except Exception as e:
        # Return default config on parse errors
        return get_default_config()


def save_submodule_config(
    config: SubmoduleConfig,
    repo_path: Optional[Path] = None,
) -> Path:
    """
    Save submodule configuration to .vibey/config/submodules.yaml.

    Args:
        config: SubmoduleConfig to save.
        repo_path: Repository root path. Defaults to cwd.

    Returns:
        Path to saved config file.
    """
    config_path = get_submodule_config_path(repo_path)

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert config to YAML-serializable dict
    data = _config_to_dict(config)

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return config_path


def get_default_config() -> SubmoduleConfig:
    """
    Get default submodule configuration.

    Returns:
        Default SubmoduleConfig with no submodules registered.
    """
    return SubmoduleConfig(
        submodules=[],
        default_push_mode=PushMode.LINKED,
        aggregate_on_status=True,
        stale_threshold_minutes=60,
    )


def _parse_config_data(data: dict) -> SubmoduleConfig:
    """
    Parse YAML data into SubmoduleConfig.

    Args:
        data: Parsed YAML data.

    Returns:
        SubmoduleConfig instance.
    """
    # Parse default push mode
    default_push_mode = PushMode.LINKED
    if "default_push_mode" in data:
        try:
            default_push_mode = PushMode(data["default_push_mode"])
        except ValueError:
            pass

    # Parse submodules list
    submodules = []
    for sub_data in data.get("submodules", []):
        submodule = _parse_submodule_reference(sub_data)
        if submodule:
            submodules.append(submodule)

    return SubmoduleConfig(
        submodules=submodules,
        default_push_mode=default_push_mode,
        aggregate_on_status=data.get("aggregate_on_status", True),
        stale_threshold_minutes=data.get("stale_threshold_minutes", 60),
    )


def _parse_submodule_reference(data: dict) -> Optional[SubmoduleReference]:
    """
    Parse YAML data into SubmoduleReference.

    Args:
        data: Submodule entry data.

    Returns:
        SubmoduleReference or None if invalid.
    """
    if not data.get("path"):
        return None

    # Parse detection source
    detection_source = DetectionSource.GITMODULES
    if "detection_source" in data:
        try:
            detection_source = DetectionSource(data["detection_source"])
        except ValueError:
            pass

    # Parse sync status
    sync_status = SyncStatus.NEVER_SYNCED
    if "sync_status" in data:
        try:
            sync_status = SyncStatus(data["sync_status"])
        except ValueError:
            pass

    # Parse last_synced datetime
    last_synced = None
    if "last_synced" in data and data["last_synced"]:
        if isinstance(data["last_synced"], datetime):
            last_synced = data["last_synced"]
        elif isinstance(data["last_synced"], str):
            try:
                last_synced = datetime.fromisoformat(data["last_synced"].replace("Z", "+00:00"))
            except ValueError:
                pass

    return SubmoduleReference(
        path=data["path"],
        roadmap_id=data.get("roadmap_id"),
        aggregate=data.get("aggregate", True),
        track_filter=data.get("track_filter", []),
        detection_source=detection_source,
        last_synced=last_synced,
        sync_status=sync_status,
    )


def _config_to_dict(config: SubmoduleConfig) -> dict:
    """
    Convert SubmoduleConfig to YAML-serializable dict.

    Args:
        config: SubmoduleConfig to convert.

    Returns:
        Dictionary ready for YAML serialization.
    """
    return {
        "default_push_mode": config.default_push_mode.value,
        "aggregate_on_status": config.aggregate_on_status,
        "stale_threshold_minutes": config.stale_threshold_minutes,
        "submodules": [
            _submodule_reference_to_dict(sub) for sub in config.submodules
        ],
    }


def _submodule_reference_to_dict(ref: SubmoduleReference) -> dict:
    """
    Convert SubmoduleReference to YAML-serializable dict.

    Args:
        ref: SubmoduleReference to convert.

    Returns:
        Dictionary ready for YAML serialization.
    """
    result = {
        "path": ref.path,
        "aggregate": ref.aggregate,
    }

    if ref.roadmap_id:
        result["roadmap_id"] = ref.roadmap_id

    if ref.track_filter:
        result["track_filter"] = ref.track_filter

    if ref.detection_source != DetectionSource.GITMODULES:
        result["detection_source"] = ref.detection_source.value

    if ref.sync_status != SyncStatus.NEVER_SYNCED:
        result["sync_status"] = ref.sync_status.value

    if ref.last_synced:
        result["last_synced"] = ref.last_synced.isoformat()

    return result


__all__ = [
    "load_submodule_config",
    "save_submodule_config",
    "get_submodule_config_path",
    "get_default_config",
]
