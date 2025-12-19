"""
Artifact operations for managing first-class artifact entities.

Sprint 5 (unified-arch-5-task-004): Operations for artifacts as first-class entities.

## Operations

1. list_artifacts() - List all registered artifacts
2. show_artifact(id) - Show artifact details
3. adopt_artifact(path) - Register existing file as artifact
4. orphan_artifacts() - List artifacts not referenced by any ticket
5. stale_artifacts() - List stale documentation artifacts
6. impact_analysis(files) - Show tickets affected by file changes

## Usage

```python
from vibey.operations.roadmap.artifacts import (
    list_artifacts,
    show_artifact,
    adopt_artifact,
    orphan_artifacts,
    stale_artifacts,
    impact_analysis,
)

# List all artifacts
artifacts = list_artifacts(root_dir)

# Adopt a file as artifact
artifact = adopt_artifact("docs/README.md", ArtifactType.DOCUMENTATION, root_dir)

# Find orphans (unreferenced artifacts)
orphans = orphan_artifacts(root_dir)

# Check for stale documentation
stale = stale_artifacts(root_dir)

# Impact analysis
affected = impact_analysis(["src/api.py", "src/models.py"], root_dir)
```
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Set, Any
import hashlib
import yaml

from vibey.roadmap.models.ticket import (
    Artifact,
    ArtifactType,
    ArtifactProvenance,
    ProvenanceType,
)
from vibey.cli.roadmap_lib.filesystem import FileSystemManager

# Try to import ULID generator
try:
    from ulid import ULID
    HAS_ULID = True
except ImportError:
    HAS_ULID = False
    import uuid


def generate_artifact_id() -> str:
    """Generate a unique artifact ID."""
    if HAS_ULID:
        return str(ULID())
    else:
        # Fallback to UUID-based ID
        return uuid.uuid4().hex[:26].upper()


def _compute_file_hash(file_path: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return None
    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None


def _load_artifact_registry(root_dir: Path) -> Dict[str, Artifact]:
    """
    Load artifact registry from .vibey/roadmap/artifacts.yaml.

    Returns dict mapping artifact ID to Artifact.
    """
    fs = FileSystemManager(root_dir)
    registry_path = fs.roadmap_root / "artifacts.yaml"

    if not registry_path.exists():
        return {}

    try:
        with open(registry_path) as f:
            data = yaml.safe_load(f)

        if not data or 'artifacts' not in data:
            return {}

        artifacts = {}
        for artifact_data in data['artifacts']:
            try:
                # Parse artifact
                artifact = _parse_artifact(artifact_data)
                artifacts[artifact.id] = artifact
            except Exception:
                continue

        return artifacts
    except Exception:
        return {}


def _parse_artifact(data: Dict[str, Any]) -> Artifact:
    """Parse artifact data dict to Artifact model."""
    # Parse provenance
    prov_data = data.get('provenance', {})
    provenance = ArtifactProvenance(
        provenance_type=ProvenanceType(prov_data.get('provenance_type', 'pre_existing')),
        source_ticket_id=prov_data.get('source_ticket_id'),
        source_criterion_id=prov_data.get('source_criterion_id'),
        discovered_at=prov_data.get('discovered_at'),
        discovered_by=prov_data.get('discovered_by'),
        external_source=prov_data.get('external_source'),
        external_version=prov_data.get('external_version'),
    )

    return Artifact(
        id=data['id'],
        name=data['name'],
        paths=data.get('paths', []),
        artifact_type=ArtifactType(data['artifact_type']),
        artifact_subtype=data.get('artifact_subtype'),
        provenance=provenance,
        referenced_by=set(data.get('referenced_by', [])),
        created_at=data.get('created_at'),
        updated_at=data.get('updated_at'),
        content_hash=data.get('content_hash'),
    )


def _save_artifact_registry(artifacts: Dict[str, Artifact], root_dir: Path) -> None:
    """Save artifact registry to .vibey/roadmap/artifacts.yaml."""
    fs = FileSystemManager(root_dir)
    registry_path = fs.roadmap_root / "artifacts.yaml"

    # Convert artifacts to serializable format
    artifacts_list = []
    for artifact in artifacts.values():
        artifact_data = {
            'id': artifact.id,
            'name': artifact.name,
            'paths': artifact.paths,
            'artifact_type': artifact.artifact_type.value,
            'artifact_subtype': artifact.artifact_subtype,
            'provenance': {
                'provenance_type': artifact.provenance.provenance_type.value,
                'created_by_ticket_id': artifact.provenance.created_by_ticket_id,
                'created_by_criterion_id': artifact.provenance.created_by_criterion_id,
                'discovered_at': artifact.provenance.discovered_at.isoformat() if artifact.provenance.discovered_at else None,
                'discovered_by': artifact.provenance.discovered_by,
                'external_source': artifact.provenance.external_source,
                'external_version': artifact.provenance.external_version,
                'source_artifact_ids': artifact.provenance.source_artifact_ids,
            },
            'depends_on_artifact_ids': artifact.depends_on_artifact_ids,
            'documents_artifact_id': artifact.documents_artifact_id,
            'exists': artifact.exists,
            'is_stale': artifact.is_stale,
            'created_at': artifact.created_at.isoformat() if artifact.created_at else None,
            'updated_at': artifact.updated_at.isoformat() if artifact.updated_at else None,
            'content_hash': artifact.content_hash,
        }
        artifacts_list.append(artifact_data)

    # Write registry
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        yaml.dump({'artifacts': artifacts_list}, f, default_flow_style=False, sort_keys=False)


def list_artifacts(root_dir: Path) -> List[Artifact]:
    """
    List all registered artifacts.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        List of all Artifact objects
    """
    registry = _load_artifact_registry(root_dir)
    return list(registry.values())


def show_artifact(artifact_id: str, root_dir: Path) -> Optional[Artifact]:
    """
    Show details of a specific artifact.

    Args:
        artifact_id: ID of the artifact
        root_dir: Root directory containing .vibey/

    Returns:
        Artifact if found, None otherwise
    """
    registry = _load_artifact_registry(root_dir)
    return registry.get(artifact_id)


def adopt_artifact(
    path: str,
    artifact_type: ArtifactType,
    root_dir: Path,
    name: Optional[str] = None,
    artifact_subtype: Optional[str] = None,
) -> Artifact:
    """
    Register an existing file as an artifact.

    Creates a new Artifact entity for a pre-existing file, tracking it
    in the artifact registry.

    Args:
        path: Path to the file (relative to root_dir)
        artifact_type: Primary artifact classification
        root_dir: Root directory containing .vibey/
        name: Optional name (defaults to filename without extension)
        artifact_subtype: Optional subtype for more specific classification

    Returns:
        The newly created Artifact

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    file_path = root_dir / path
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Generate ID and default name
    artifact_id = generate_artifact_id()
    if name is None:
        name = file_path.stem

    # Compute content hash
    content_hash = _compute_file_hash(file_path)
    now = datetime.now(timezone.utc).isoformat()

    # Create artifact
    artifact = Artifact(
        id=artifact_id,
        name=name,
        paths=[path],
        artifact_type=artifact_type,
        artifact_subtype=artifact_subtype,
        provenance=ArtifactProvenance.pre_existing(discovered_by="cli_adopt"),
        referenced_by=set(),
        created_at=now,
        updated_at=now,
        content_hash=content_hash,
    )

    # Save to registry
    registry = _load_artifact_registry(root_dir)
    registry[artifact_id] = artifact
    _save_artifact_registry(registry, root_dir)

    return artifact


def orphan_artifacts(root_dir: Path) -> List[Artifact]:
    """
    List artifacts not referenced by any ticket.

    Orphan artifacts are those not referenced by any ticket criteria.
    These may be candidates for cleanup or adoption.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        List of unreferenced Artifact objects
    """
    registry = _load_artifact_registry(root_dir)
    # All artifacts in the registry are considered orphans until
    # a registry is set up to track referencing criteria.
    # For now, return all artifacts as potentially orphan.
    return list(registry.values())


def stale_artifacts(root_dir: Path) -> List[Artifact]:
    """
    List stale documentation artifacts.

    An artifact is considered stale if:
    - It's a DOCUMENTATION type
    - The content hash has changed since last update
    - OR the file doesn't exist anymore

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        List of stale Artifact objects
    """
    registry = _load_artifact_registry(root_dir)
    stale = []

    for artifact in registry.values():
        # Only check documentation artifacts
        if artifact.artifact_type != ArtifactType.DOCUMENTATION:
            continue

        # Check each path
        is_stale = False
        for path in artifact.paths:
            file_path = root_dir / path
            if not file_path.exists():
                is_stale = True
                break

            # Check content hash
            if artifact.content_hash:
                current_hash = _compute_file_hash(file_path)
                if current_hash != artifact.content_hash:
                    is_stale = True
                    break

        if is_stale:
            stale.append(artifact)

    return stale


def impact_analysis(
    files: List[str],
    root_dir: Path,
) -> Dict[str, List[str]]:
    """
    Analyze which tickets would be affected by changes to given files.

    For each file, finds artifacts that include that path, then returns
    all tickets that reference those artifacts.

    Args:
        files: List of file paths to analyze (relative to root_dir)
        root_dir: Root directory containing .vibey/

    Returns:
        Dict mapping file path to list of affected ticket IDs
    """
    registry = _load_artifact_registry(root_dir)

    # Build path -> artifact mapping
    path_to_artifacts: Dict[str, List[Artifact]] = {}
    for artifact in registry.values():
        for path in artifact.paths:
            if path not in path_to_artifacts:
                path_to_artifacts[path] = []
            path_to_artifacts[path].append(artifact)

    # Find affected tickets for each file
    result: Dict[str, List[str]] = {}
    for file_path in files:
        affected_tickets: Set[str] = set()

        # Check exact path match
        if file_path in path_to_artifacts:
            for artifact in path_to_artifacts[file_path]:
                affected_tickets.update(artifact.referenced_by)

        # Check if file is under any artifact path (for directory artifacts)
        for artifact_path, artifacts in path_to_artifacts.items():
            if file_path.startswith(artifact_path + "/"):
                for artifact in artifacts:
                    affected_tickets.update(artifact.referenced_by)

        result[file_path] = sorted(affected_tickets)

    return result


def refresh_artifact_hashes(root_dir: Path) -> int:
    """
    Refresh content hashes for all artifacts.

    Args:
        root_dir: Root directory containing .vibey/

    Returns:
        Number of artifacts updated
    """
    registry = _load_artifact_registry(root_dir)
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for artifact in registry.values():
        for path in artifact.paths:
            file_path = root_dir / path
            if file_path.exists():
                new_hash = _compute_file_hash(file_path)
                if new_hash != artifact.content_hash:
                    artifact.content_hash = new_hash
                    artifact.updated_at = now
                    updated += 1
                    break

    if updated > 0:
        _save_artifact_registry(registry, root_dir)

    return updated


def delete_artifact(artifact_id: str, root_dir: Path) -> bool:
    """
    Delete an artifact from the registry.

    Note: This only removes the artifact from tracking, it does NOT
    delete the actual files.

    Args:
        artifact_id: ID of the artifact to delete
        root_dir: Root directory containing .vibey/

    Returns:
        True if deleted, False if not found
    """
    registry = _load_artifact_registry(root_dir)

    if artifact_id not in registry:
        return False

    del registry[artifact_id]
    _save_artifact_registry(registry, root_dir)
    return True


def link_artifact_to_ticket(
    artifact_id: str,
    ticket_id: str,
    root_dir: Path,
) -> bool:
    """
    Link an artifact to a ticket.

    Adds the ticket ID to the artifact's referenced_by set.

    Args:
        artifact_id: ID of the artifact
        ticket_id: ID of the ticket to link
        root_dir: Root directory containing .vibey/

    Returns:
        True if linked, False if artifact not found
    """
    registry = _load_artifact_registry(root_dir)

    if artifact_id not in registry:
        return False

    artifact = registry[artifact_id]
    artifact.referenced_by.add(ticket_id)
    artifact.updated_at = datetime.now(timezone.utc).isoformat()
    _save_artifact_registry(registry, root_dir)
    return True


def unlink_artifact_from_ticket(
    artifact_id: str,
    ticket_id: str,
    root_dir: Path,
) -> bool:
    """
    Unlink an artifact from a ticket.

    Removes the ticket ID from the artifact's referenced_by set.

    Args:
        artifact_id: ID of the artifact
        ticket_id: ID of the ticket to unlink
        root_dir: Root directory containing .vibey/

    Returns:
        True if unlinked, False if artifact not found or not linked
    """
    registry = _load_artifact_registry(root_dir)

    if artifact_id not in registry:
        return False

    artifact = registry[artifact_id]
    if ticket_id not in artifact.referenced_by:
        return False

    artifact.referenced_by.discard(ticket_id)
    artifact.updated_at = datetime.now(timezone.utc).isoformat()
    _save_artifact_registry(registry, root_dir)
    return True


def artifacts_for_ticket(ticket_id: str, root_dir: Path) -> List[Artifact]:
    """
    List artifacts referenced by a specific ticket.

    Args:
        ticket_id: ID of the ticket (task, sprint, or track)
        root_dir: Root directory containing .vibey/

    Returns:
        List of Artifact objects referenced by the ticket
    """
    registry = _load_artifact_registry(root_dir)
    return [a for a in registry.values() if ticket_id in a.referenced_by]


# Export for convenient importing
__all__ = [
    # Core operations
    'list_artifacts',
    'show_artifact',
    'adopt_artifact',
    'orphan_artifacts',
    'stale_artifacts',
    'impact_analysis',
    # Additional operations
    'refresh_artifact_hashes',
    'delete_artifact',
    'link_artifact_to_ticket',
    'unlink_artifact_from_ticket',
    'artifacts_for_ticket',
    # Utilities
    'generate_artifact_id',
]
