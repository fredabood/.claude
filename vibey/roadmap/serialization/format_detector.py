"""YAML format version detection for roadmap files.

Detects whether YAML files use legacy v2 format or current v3 format.
This is used to identify files that need migration or cleanup.
"""
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional
import yaml


class YAMLFormat(Enum):
    """YAML format versions for roadmap files."""
    V2_LEGACY = "v2_legacy"      # Uses parent_ref, name, created_at
    V3_CURRENT = "v3_current"    # Uses sprint_id, title, created
    UNKNOWN = "unknown"


# V2 legacy field markers
V2_TASK_MARKERS = {"parent_ref", "name", "created_at", "started_at", "completed_at", "updated_at", "ticket_type"}
V2_SPRINT_MARKERS = {"parent_ref", "name", "created_at"}
V2_TRACK_MARKERS = {"name", "created_at"}

# V3 current field markers
V3_TASK_MARKERS = {"sprint_id", "title", "created", "task_type"}
V3_SPRINT_MARKERS = {"track_id", "name", "created"}
V3_TRACK_MARKERS = {"name", "created", "roadmap_id"}


def detect_task_format(yaml_path: Path) -> YAMLFormat:
    """Detect the format version of a task YAML file.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        YAMLFormat enum indicating v2_legacy, v3_current, or unknown
    """
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return YAMLFormat.UNKNOWN

    if not data:
        return YAMLFormat.UNKNOWN

    task = data.get("task", {})
    if not task:
        return YAMLFormat.UNKNOWN

    task_keys = set(task.keys())

    # Check for explicit format_version field
    if task.get("format_version") == "v2":
        return YAMLFormat.V2_LEGACY

    # Check for v2 legacy markers (these shouldn't exist in v3)
    v2_markers_found = task_keys & V2_TASK_MARKERS
    if v2_markers_found:
        # If we find any v2 markers like parent_ref, created_at, etc.
        return YAMLFormat.V2_LEGACY

    # Check for v3 current markers
    v3_markers_found = task_keys & V3_TASK_MARKERS
    if v3_markers_found:
        return YAMLFormat.V3_CURRENT

    return YAMLFormat.UNKNOWN


def detect_sprint_format(yaml_path: Path) -> YAMLFormat:
    """Detect the format version of a sprint YAML file."""
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return YAMLFormat.UNKNOWN

    if not data:
        return YAMLFormat.UNKNOWN

    sprint = data.get("sprint", {})
    if not sprint:
        return YAMLFormat.UNKNOWN

    sprint_keys = set(sprint.keys())

    # Check for v2 legacy markers
    if "parent_ref" in sprint_keys or "created_at" in sprint_keys:
        return YAMLFormat.V2_LEGACY

    # Check for v3 current markers
    if "track_id" in sprint_keys and "created" in sprint_keys:
        return YAMLFormat.V3_CURRENT

    return YAMLFormat.UNKNOWN


def detect_track_format(yaml_path: Path) -> YAMLFormat:
    """Detect the format version of a track YAML file."""
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return YAMLFormat.UNKNOWN

    if not data:
        return YAMLFormat.UNKNOWN

    track = data.get("track", {})
    if not track:
        return YAMLFormat.UNKNOWN

    track_keys = set(track.keys())

    # Check for v2 legacy markers
    if "created_at" in track_keys:
        return YAMLFormat.V2_LEGACY

    # Check for v3 current markers
    if "created" in track_keys and "roadmap_id" in track_keys:
        return YAMLFormat.V3_CURRENT

    return YAMLFormat.UNKNOWN


def scan_for_legacy_files(roadmap_dir: Path) -> List[Tuple[Path, str, YAMLFormat]]:
    """Scan roadmap directory for legacy format files.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        List of (file_path, entity_type, format_version) tuples for legacy files
    """
    legacy_files = []

    # Scan tasks
    tasks_dir = roadmap_dir / "tasks"
    if tasks_dir.exists():
        for yaml_file in sorted(tasks_dir.glob("*.yaml")):
            format_version = detect_task_format(yaml_file)
            if format_version == YAMLFormat.V2_LEGACY:
                legacy_files.append((yaml_file, "task", format_version))

    # Scan sprints
    sprints_dir = roadmap_dir / "sprints"
    if sprints_dir.exists():
        for yaml_file in sorted(sprints_dir.glob("*.yaml")):
            format_version = detect_sprint_format(yaml_file)
            if format_version == YAMLFormat.V2_LEGACY:
                legacy_files.append((yaml_file, "sprint", format_version))

    # Scan tracks
    tracks_dir = roadmap_dir / "tracks"
    if tracks_dir.exists():
        for yaml_file in sorted(tracks_dir.glob("*.yaml")):
            format_version = detect_track_format(yaml_file)
            if format_version == YAMLFormat.V2_LEGACY:
                legacy_files.append((yaml_file, "track", format_version))

    return legacy_files


def get_legacy_file_details(yaml_path: Path) -> Optional[dict]:
    """Get details about a legacy format file for reporting.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        Dictionary with legacy field details, or None if not legacy
    """
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return None

    if not data:
        return None

    # Determine entity type
    entity_type = None
    entity_data = None
    for key in ["task", "sprint", "track"]:
        if key in data:
            entity_type = key
            entity_data = data[key]
            break

    if not entity_data:
        return None

    entity_keys = set(entity_data.keys())

    # Find legacy fields
    legacy_fields = []
    if "parent_ref" in entity_keys:
        legacy_fields.append(("parent_ref", entity_data.get("parent_ref"), "should be sprint_id/track_id"))
    if "name" in entity_keys and entity_type == "task":
        legacy_fields.append(("name", entity_data.get("name"), "should be title"))
    if "created_at" in entity_keys:
        legacy_fields.append(("created_at", entity_data.get("created_at"), "should be created"))
    if "started_at" in entity_keys:
        legacy_fields.append(("started_at", entity_data.get("started_at"), "should be started"))
    if "completed_at" in entity_keys:
        legacy_fields.append(("completed_at", entity_data.get("completed_at"), "should be completed"))
    if "updated_at" in entity_keys:
        legacy_fields.append(("updated_at", entity_data.get("updated_at"), "not used in v3"))
    if "ticket_type" in entity_keys:
        legacy_fields.append(("ticket_type", entity_data.get("ticket_type"), "should be task_type"))
    if "format_version" in entity_keys:
        legacy_fields.append(("format_version", entity_data.get("format_version"), "v2 format marker"))

    if not legacy_fields:
        return None

    return {
        "file": yaml_path.name,
        "entity_type": entity_type,
        "id": entity_data.get("id"),
        "legacy_fields": legacy_fields,
    }
