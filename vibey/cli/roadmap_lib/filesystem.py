"""
File system management utilities for roadmap state.

Uses flat ULID-based directory structure per ADR-0002:

DIRECTORY STRUCTURE:
   .vibey/roadmap/tracks/{ulid}.yaml
   .vibey/roadmap/sprints/{ulid}.yaml
   .vibey/roadmap/tasks/{ulid}.yaml
   .vibey/roadmap/artifacts/{ulid}.yaml
   .vibey/roadmap/context/{scope}/{slug}/

Note: Hierarchical/nested directory support was removed per ADR-0002.
Legacy nested structures (track/sprint/task directories) are no longer supported.
"""

from pathlib import Path
from typing import Optional, Dict


class FileSystemManager:
    """Manages roadmap file system structure (flat ULID-based only)."""

    VIBEY_DIR = ".vibey"
    ROADMAP_DIR = "roadmap"
    ROADMAP_FILE = "roadmap.yaml"

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.vibey_dir = self.root_dir / self.VIBEY_DIR
        self.roadmap_root = self.vibey_dir / self.ROADMAP_DIR
        self.config_root = self.vibey_dir / "config"
        self.activity_log_dir = self.roadmap_root / "activity_log"
        self.structure_format = "flat"
        self._id_to_slug_cache: Dict[str, str] = {}
        self._id_mappings: Optional[Dict[str, Dict[str, str]]] = None

    def ensure_structure(self):
        self.vibey_dir.mkdir(parents=True, exist_ok=True)
        self.roadmap_root.mkdir(parents=True, exist_ok=True)
        self.config_root.mkdir(parents=True, exist_ok=True)
        self.tracks_dir.mkdir(exist_ok=True)
        self.sprints_dir.mkdir(exist_ok=True)
        self.tasks_dir.mkdir(exist_ok=True)
        self.activity_log_dir.mkdir(parents=True, exist_ok=True)

    def ensure_activity_log_dir(self) -> Path:
        self.activity_log_dir.mkdir(parents=True, exist_ok=True)
        return self.activity_log_dir

    def get_activity_log_path(self, year: int, month: int) -> Path:
        filename = f"{year}-{month:02d}.jsonl"
        return self.activity_log_dir / filename

    def get_current_activity_log_path(self) -> Path:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return self.get_activity_log_path(now.year, now.month)

    def _load_id_mappings(self):
        if self._id_mappings is not None:
            return
        self._id_mappings = {"tracks": {}, "sprints": {}, "tasks": {}, "artifacts": {}}
        for entity_type in ["tracks", "sprints", "tasks", "artifacts"]:
            id_file = self.roadmap_root / entity_type / ".id"
            if not id_file.exists():
                continue
            with open(id_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        slug, ulid = line.split("=", 1)
                        self._id_mappings[entity_type][slug.strip()] = ulid.strip()
                        self._id_mappings[entity_type][ulid.strip()] = slug.strip()

    def _resolve_id_in_flat_structure(self, entity_id: str, entity_type: str) -> str:
        self._load_id_mappings()
        if len(entity_id) == 26 and entity_id.replace("_", "").replace("-", "").isalnum():
            return entity_id
        mappings = self._id_mappings.get(entity_type, {})
        ulid = mappings.get(entity_id)
        return ulid if ulid else entity_id

    def _resolve_slug_from_ulid(self, ulid: str, entity_type: str) -> Optional[str]:
        self._load_id_mappings()
        return self._id_mappings.get(entity_type, {}).get(ulid)

    @property
    def tracks_dir(self) -> Path:
        return self.roadmap_root / "tracks"

    @property
    def sprints_dir(self) -> Path:
        return self.roadmap_root / "sprints"

    @property
    def tasks_dir(self) -> Path:
        return self.roadmap_root / "tasks"

    @property
    def context_dir(self) -> Path:
        return self.roadmap_root / "context"

    def get_roadmap_path(self) -> Path:
        return self.roadmap_root / self.ROADMAP_FILE

    def get_entity_path(self, entity_id: str, entity_type: str) -> Path:
        if entity_type == "track":
            return self.get_track_path(entity_id)
        elif entity_type == "sprint":
            return self.get_sprint_path(entity_id)
        elif entity_type == "task":
            return self.get_task_path(entity_id)
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")

    def entity_exists(self, entity_id: str, entity_type: str) -> bool:
        try:
            return self.get_entity_path(entity_id, entity_type).exists()
        except (ValueError, FileNotFoundError):
            return False

    def detect_entity_type(self, entity_id: str) -> Optional[str]:
        if (self.tasks_dir / f"{entity_id}.yaml").exists():
            return "task"
        if (self.sprints_dir / f"{entity_id}.yaml").exists():
            return "sprint"
        if (self.tracks_dir / f"{entity_id}.yaml").exists():
            return "track"
        return None

    def get_track_path(self, track_id: str) -> Path:
        ulid = self._resolve_id_in_flat_structure(track_id, "tracks")
        return self.roadmap_root / "tracks" / f"{ulid}.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        ulid = self._resolve_id_in_flat_structure(sprint_id, "sprints")
        return self.roadmap_root / "sprints" / f"{ulid}.yaml"

    def get_tasks_path(self, sprint_id: str) -> Path:
        return self.roadmap_root / "tasks"

    def get_task_path(self, task_id: str) -> Path:
        ulid = self._resolve_id_in_flat_structure(task_id, "tasks")
        return self.roadmap_root / "tasks" / f"{ulid}.yaml"

    def roadmap_exists(self) -> bool:
        return self.get_roadmap_path().exists()

    def track_exists(self, track_id: str) -> bool:
        try:
            return self.get_track_path(track_id).exists()
        except (ValueError, FileNotFoundError):
            return False

    def sprint_exists(self, sprint_id: str) -> bool:
        try:
            return self.get_sprint_path(sprint_id).exists()
        except (ValueError, FileNotFoundError):
            return False

    def tasks_exist(self, sprint_id: str) -> bool:
        tasks_dir = self.get_tasks_path(sprint_id)
        if not tasks_dir.exists():
            return False
        return any(f.suffix == ".yaml" for f in tasks_dir.iterdir() if f.is_file())

    def list_tracks(self) -> list[str]:
        tracks_dir = self.roadmap_root / "tracks"
        if not tracks_dir.exists():
            return []
        return [f.stem for f in tracks_dir.glob("*.yaml")]

    def list_sprints(self) -> list[str]:
        sprints_dir = self.roadmap_root / "sprints"
        if not sprints_dir.exists():
            return []
        return [f.stem for f in sprints_dir.glob("*.yaml")]

    def list_sprint_tasks(self) -> list[str]:
        return self.list_sprints()

    @property
    def submodules_config_path(self) -> Path:
        """Path to .vibey/config/submodules.yaml (submodule registry)."""
        return self.config_root / "submodules.yaml"

    @property
    def linked_tasks_config_path(self) -> Path:
        """Path to .vibey/config/linked_tasks.yaml (task link tracking)."""
        return self.config_root / "linked_tasks.yaml"

    def ensure_submodules_config(self) -> Path:
        """Ensure submodules.yaml exists with default template if missing.

        Per SUBMODULE_ISOLATION_AND_PUSHDOWN.md: All cross-repo data lives
        in PARENT only. Submodules have NO additional directories for
        submodule integration.

        Returns:
            Path to the submodules config file.
        """
        self.config_root.mkdir(parents=True, exist_ok=True)
        if not self.submodules_config_path.exists():
            template = {
                "submodules": [],
                "default_push_mode": "linked",
                "aggregate_on_status": True,
            }
            save_yaml(self.submodules_config_path, template)
        return self.submodules_config_path

    def submodules_config_exists(self) -> bool:
        """Check if submodules.yaml exists."""
        return self.submodules_config_path.exists()

    def linked_tasks_config_exists(self) -> bool:
        """Check if linked_tasks.yaml exists."""
        return self.linked_tasks_config_path.exists()


def find_roadmap_root(start_path: Optional[Path] = None) -> Optional[Path]:
    current = Path(start_path) if start_path else Path.cwd()
    while True:
        vibey_dir = current / ".vibey"
        if (vibey_dir / "roadmap" / "roadmap.yaml").exists():
            return current
        if (vibey_dir / "roadmap.yaml").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def ensure_roadmap_structure(root_dir: Optional[Path] = None):
    fs = FileSystemManager(root_dir)
    fs.ensure_structure()


def get_file_system_manager(root_dir: Optional[Path] = None) -> FileSystemManager:
    return FileSystemManager(root_dir)


def load_yaml(file_path: Path) -> dict:
    import yaml
    if not file_path.exists():
        return {}
    with open(file_path, "r") as f:
        return yaml.safe_load(f) or {}


def save_yaml(file_path: Path, data: dict) -> None:
    import yaml
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
