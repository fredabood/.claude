"""
Tests for Artifact entity.

Tests cover:
- ArtifactProvenance creation and factory methods
- Artifact entity creation and properties
- Staleness detection
- Content hash computation
- File existence verification
- Registry binding
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from vibey.roadmap.models.ticket.artifact import (
    Artifact,
    ArtifactProvenance,
    ArtifactRegistry,
)
from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactType,
    ProvenanceType,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


class MockArtifactRegistry:
    """Mock registry for testing."""

    def __init__(self):
        self._artifacts: Dict[str, Artifact] = {}
        self._criteria_refs: Dict[str, List[str]] = {}

    def add(self, artifact: Artifact) -> None:
        self._artifacts[artifact.id] = artifact

    def set_criteria_refs(self, artifact_id: str, criteria_ids: List[str]) -> None:
        self._criteria_refs[artifact_id] = criteria_ids

    def get(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)

    def get_referencing_criteria(self, artifact_id: str) -> List[str]:
        return self._criteria_refs.get(artifact_id, [])


@pytest.fixture
def registry():
    """Create a mock registry."""
    return MockArtifactRegistry()


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        file1 = Path(tmpdir) / "file1.py"
        file1.write_text("# Python file 1")

        file2 = Path(tmpdir) / "file2.py"
        file2.write_text("# Python file 2")

        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()

        file3 = Path(tmpdir) / "subdir" / "file3.py"
        file3.write_text("# Python file 3")

        yield tmpdir


def create_artifact(
    id: str = "art-001",
    name: str = "Test Artifact",
    paths: Optional[List[str]] = None,
    artifact_type: ArtifactType = ArtifactType.CODE,
    provenance_type: ProvenanceType = ProvenanceType.TICKET_CREATED,
) -> Artifact:
    """Helper to create artifacts for testing."""
    return Artifact(
        id=id,
        name=name,
        paths=paths or ["src/main.py"],
        artifact_type=artifact_type,
        provenance=ArtifactProvenance(provenance_type=provenance_type),
    )


# =============================================================================
# ARTIFACT PROVENANCE TESTS
# =============================================================================


class TestArtifactProvenance:
    """Tests for ArtifactProvenance class."""

    def test_basic_creation(self):
        """Test basic provenance creation."""
        prov = ArtifactProvenance(provenance_type=ProvenanceType.TICKET_CREATED)
        assert prov.provenance_type == ProvenanceType.TICKET_CREATED

    def test_ticket_created_factory(self):
        """Test ticket_created factory method."""
        prov = ArtifactProvenance.ticket_created(
            ticket_id="task-001",
            criterion_id="crit-001",
        )
        assert prov.provenance_type == ProvenanceType.TICKET_CREATED
        assert prov.created_by_ticket_id == "task-001"
        assert prov.created_by_criterion_id == "crit-001"

    def test_pre_existing_factory(self):
        """Test pre_existing factory method."""
        prov = ArtifactProvenance.pre_existing(discovered_by="manual")
        assert prov.provenance_type == ProvenanceType.PRE_EXISTING
        assert prov.discovered_by == "manual"
        assert prov.discovered_at is not None

    def test_pre_existing_default_discoverer(self):
        """Test pre_existing with default discoverer."""
        prov = ArtifactProvenance.pre_existing()
        assert prov.discovered_by == "filesystem_scan"

    def test_generated_factory(self):
        """Test generated factory method."""
        prov = ArtifactProvenance.generated(
            generator_type="sphinx",
            source_artifact_ids=["art-001", "art-002"],
            generator_config={"theme": "alabaster"},
        )
        assert prov.provenance_type == ProvenanceType.GENERATED
        assert prov.generator_type == "sphinx"
        assert prov.source_artifact_ids == ["art-001", "art-002"]
        assert prov.generator_config == {"theme": "alabaster"}

    def test_external_factory(self):
        """Test external factory method."""
        prov = ArtifactProvenance.external(
            source="https://example.com/package",
            version="1.0.0",
        )
        assert prov.provenance_type == ProvenanceType.EXTERNAL
        assert prov.external_source == "https://example.com/package"
        assert prov.external_version == "1.0.0"

    def test_framework_factory(self):
        """Test framework factory method."""
        prov = ArtifactProvenance.framework(component_type="agent")
        assert prov.provenance_type == ProvenanceType.FRAMEWORK
        assert prov.framework_component_type == "agent"


# =============================================================================
# ARTIFACT CREATION TESTS
# =============================================================================


class TestArtifactCreation:
    """Tests for Artifact creation."""

    def test_minimal_artifact(self):
        """Test minimal artifact creation."""
        artifact = create_artifact()
        assert artifact.id == "art-001"
        assert artifact.name == "Test Artifact"
        assert artifact.paths == ["src/main.py"]
        assert artifact.artifact_type == ArtifactType.CODE
        assert artifact.exists is True
        assert artifact.is_stale is False

    def test_artifact_with_all_fields(self):
        """Test artifact with all fields."""
        now = datetime.now(timezone.utc)
        artifact = Artifact(
            id="art-002",
            name="Complete Artifact",
            description="A fully specified artifact",
            paths=["src/main.py", "src/utils.py"],
            content_hash="abc123",
            last_verified=now,
            artifact_type=ArtifactType.DOCUMENTATION,
            artifact_subtype="readme",
            provenance=ArtifactProvenance.pre_existing(),
            documents_artifact_id="art-001",
            depends_on_artifact_ids=["art-003", "art-004"],
            exists=True,
            is_stale=False,
            created_at=now,
            updated_at=now,
        )
        assert artifact.description == "A fully specified artifact"
        assert len(artifact.paths) == 2
        assert artifact.content_hash == "abc123"
        assert artifact.artifact_subtype == "readme"
        assert artifact.documents_artifact_id == "art-001"
        assert len(artifact.depends_on_artifact_ids) == 2


# =============================================================================
# COMPUTED PROPERTIES TESTS
# =============================================================================


class TestArtifactComputedProperties:
    """Tests for Artifact computed properties."""

    def test_is_documentation_true(self):
        """Test is_documentation when artifact documents another."""
        artifact = create_artifact()
        artifact.documents_artifact_id = "art-other"
        assert artifact.is_documentation is True

    def test_is_documentation_false(self):
        """Test is_documentation when artifact doesn't document another."""
        artifact = create_artifact()
        assert artifact.is_documentation is False

    def test_is_orphan_without_registry(self):
        """Test is_orphan returns False without registry."""
        artifact = create_artifact()
        assert artifact.is_orphan is False

    def test_is_orphan_with_registry_no_refs(self, registry):
        """Test is_orphan returns True when no criteria reference artifact."""
        artifact = create_artifact()
        registry.add(artifact)
        artifact.bind_registry(registry)
        assert artifact.is_orphan is True

    def test_is_orphan_with_registry_has_refs(self, registry):
        """Test is_orphan returns False when criteria reference artifact."""
        artifact = create_artifact()
        registry.add(artifact)
        registry.set_criteria_refs("art-001", ["crit-001", "crit-002"])
        artifact.bind_registry(registry)
        assert artifact.is_orphan is False

    def test_referencing_criteria_without_registry(self):
        """Test referencing_criteria returns empty list without registry."""
        artifact = create_artifact()
        assert artifact.referencing_criteria == []

    def test_referencing_criteria_with_registry(self, registry):
        """Test referencing_criteria returns correct IDs."""
        artifact = create_artifact()
        registry.add(artifact)
        registry.set_criteria_refs("art-001", ["crit-001", "crit-002"])
        artifact.bind_registry(registry)
        assert artifact.referencing_criteria == ["crit-001", "crit-002"]


# =============================================================================
# CONTENT HASH TESTS
# =============================================================================


class TestArtifactContentHash:
    """Tests for content hash computation."""

    def test_compute_content_hash(self, temp_dir):
        """Test computing content hash for existing files."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[str(Path(temp_dir) / "file1.py")],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        hash1 = artifact.compute_content_hash()
        assert len(hash1) == 64  # SHA256 hex digest length

    def test_compute_content_hash_deterministic(self, temp_dir):
        """Test that content hash is deterministic."""
        paths = [
            str(Path(temp_dir) / "file1.py"),
            str(Path(temp_dir) / "file2.py"),
        ]
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=paths,
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        hash1 = artifact.compute_content_hash()
        hash2 = artifact.compute_content_hash()
        assert hash1 == hash2

    def test_compute_content_hash_order_independent(self, temp_dir):
        """Test that path order doesn't affect hash."""
        paths_forward = [
            str(Path(temp_dir) / "file1.py"),
            str(Path(temp_dir) / "file2.py"),
        ]
        paths_reverse = [
            str(Path(temp_dir) / "file2.py"),
            str(Path(temp_dir) / "file1.py"),
        ]
        artifact1 = Artifact(
            id="art-001",
            name="Test",
            paths=paths_forward,
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        artifact2 = Artifact(
            id="art-002",
            name="Test",
            paths=paths_reverse,
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        assert artifact1.compute_content_hash() == artifact2.compute_content_hash()

    def test_compute_content_hash_missing_file(self):
        """Test that missing file raises error."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=["nonexistent/file.py"],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        with pytest.raises(FileNotFoundError):
            artifact.compute_content_hash()

    def test_refresh_content_hash(self, temp_dir):
        """Test refreshing content hash."""
        path = str(Path(temp_dir) / "file1.py")
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[path],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )

        # First refresh
        changed = artifact.refresh_content_hash()
        assert changed is True  # First time is always a change
        assert artifact.content_hash is not None
        assert artifact.last_verified is not None
        assert artifact.exists is True

        # Second refresh (no change)
        old_hash = artifact.content_hash
        changed = artifact.refresh_content_hash()
        assert changed is False
        assert artifact.content_hash == old_hash

    def test_refresh_content_hash_file_deleted(self, temp_dir):
        """Test refresh when file is deleted."""
        path = Path(temp_dir) / "temp_file.py"
        path.write_text("# Temporary file")

        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[str(path)],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )

        # First refresh
        artifact.refresh_content_hash()
        assert artifact.exists is True

        # Delete file
        path.unlink()

        # Refresh again
        changed = artifact.refresh_content_hash()
        assert changed is True
        assert artifact.exists is False

    def test_compute_hash_with_base_path(self, temp_dir):
        """Test computing hash with base_path."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=["file1.py"],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        hash_val = artifact.compute_content_hash(base_path=Path(temp_dir))
        assert len(hash_val) == 64


# =============================================================================
# FILE EXISTENCE TESTS
# =============================================================================


class TestArtifactFileExistence:
    """Tests for file existence verification."""

    def test_verify_exists_all_exist(self, temp_dir):
        """Test verify_exists when all files exist."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[
                str(Path(temp_dir) / "file1.py"),
                str(Path(temp_dir) / "file2.py"),
            ],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        result = artifact.verify_exists()
        assert result is True
        assert artifact.exists is True
        assert artifact.last_verified is not None

    def test_verify_exists_some_missing(self, temp_dir):
        """Test verify_exists when some files are missing."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[
                str(Path(temp_dir) / "file1.py"),
                str(Path(temp_dir) / "nonexistent.py"),
            ],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        result = artifact.verify_exists()
        assert result is False
        assert artifact.exists is False

    def test_verify_exists_with_base_path(self, temp_dir):
        """Test verify_exists with base_path."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=["file1.py", "file2.py"],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        result = artifact.verify_exists(base_path=Path(temp_dir))
        assert result is True

    def test_get_missing_paths_none(self, temp_dir):
        """Test get_missing_paths when all exist."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[str(Path(temp_dir) / "file1.py")],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        missing = artifact.get_missing_paths()
        assert missing == []

    def test_get_missing_paths_some(self, temp_dir):
        """Test get_missing_paths with missing files."""
        artifact = Artifact(
            id="art-001",
            name="Test",
            paths=[
                str(Path(temp_dir) / "file1.py"),
                "nonexistent.py",
                str(Path(temp_dir) / "also_missing.py"),
            ],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
        )
        missing = artifact.get_missing_paths()
        assert len(missing) == 2
        assert "nonexistent.py" in missing


# =============================================================================
# STALENESS DETECTION TESTS
# =============================================================================


class TestArtifactStaleness:
    """Tests for staleness detection."""

    def test_check_staleness_not_documentation(self, registry):
        """Test check_staleness returns False for non-documentation."""
        artifact = create_artifact()
        registry.add(artifact)
        result = artifact.check_staleness(registry)
        assert result is False

    def test_check_staleness_source_missing(self, registry):
        """Test check_staleness returns True when source is missing."""
        doc_artifact = Artifact(
            id="doc-001",
            name="Documentation",
            paths=["docs/README.md"],
            artifact_type=ArtifactType.DOCUMENTATION,
            provenance=ArtifactProvenance.pre_existing(),
            documents_artifact_id="art-001",  # This doesn't exist in registry
        )
        result = doc_artifact.check_staleness(registry)
        assert result is True
        assert doc_artifact.is_stale is True

    def test_check_staleness_hash_changed(self, registry):
        """Test check_staleness returns True when source hash changed."""
        # Create source artifact with hash
        source = Artifact(
            id="art-001",
            name="Source",
            paths=["src/main.py"],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
            content_hash="new_hash_value",
        )
        registry.add(source)

        # Create doc with different stored hash
        doc = Artifact(
            id="doc-001",
            name="Documentation",
            paths=["docs/README.md"],
            artifact_type=ArtifactType.DOCUMENTATION,
            provenance=ArtifactProvenance.pre_existing(),
            documents_artifact_id="art-001",
        )
        object.__setattr__(doc, "_documented_source_hash", "old_hash_value")

        result = doc.check_staleness(registry)
        assert result is True
        assert doc.is_stale is True

    def test_check_staleness_hash_unchanged(self, registry):
        """Test check_staleness returns False when source hash unchanged."""
        source = Artifact(
            id="art-001",
            name="Source",
            paths=["src/main.py"],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
            content_hash="same_hash",
        )
        registry.add(source)

        doc = Artifact(
            id="doc-001",
            name="Documentation",
            paths=["docs/README.md"],
            artifact_type=ArtifactType.DOCUMENTATION,
            provenance=ArtifactProvenance.pre_existing(),
            documents_artifact_id="art-001",
        )
        object.__setattr__(doc, "_documented_source_hash", "same_hash")

        result = doc.check_staleness(registry)
        assert result is False
        assert doc.is_stale is False

    def test_mark_updated(self, registry):
        """Test mark_updated captures source hash."""
        source = Artifact(
            id="art-001",
            name="Source",
            paths=["src/main.py"],
            artifact_type=ArtifactType.CODE,
            provenance=ArtifactProvenance.pre_existing(),
            content_hash="current_hash",
        )
        registry.add(source)

        doc = Artifact(
            id="doc-001",
            name="Documentation",
            paths=["docs/README.md"],
            artifact_type=ArtifactType.DOCUMENTATION,
            provenance=ArtifactProvenance.pre_existing(),
            documents_artifact_id="art-001",
            is_stale=True,
        )

        doc.mark_updated(registry)

        assert doc.is_stale is False
        assert doc._documented_source_hash == "current_hash"


# =============================================================================
# REGISTRY BINDING TESTS
# =============================================================================


class TestArtifactRegistryBinding:
    """Tests for registry binding."""

    def test_bind_registry(self, registry):
        """Test binding a registry."""
        artifact = create_artifact()
        artifact.bind_registry(registry)
        assert artifact._registry is registry

    def test_bind_registry_enables_computed_properties(self, registry):
        """Test that binding enables computed properties."""
        artifact = create_artifact()
        registry.add(artifact)
        registry.set_criteria_refs("art-001", ["crit-001"])

        # Before binding
        assert artifact.referencing_criteria == []

        # After binding
        artifact.bind_registry(registry)
        assert artifact.referencing_criteria == ["crit-001"]


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================


class TestArtifactSerialization:
    """Tests for JSON/YAML serialization."""

    def test_to_dict(self):
        """Test artifact serialization to dict."""
        artifact = create_artifact()
        data = artifact.model_dump()
        assert data["id"] == "art-001"
        assert data["name"] == "Test Artifact"
        assert data["paths"] == ["src/main.py"]
        assert data["artifact_type"] == "code"

    def test_from_dict(self):
        """Test artifact deserialization from dict."""
        data = {
            "id": "art-001",
            "name": "Test",
            "paths": ["src/main.py"],
            "artifact_type": "code",
            "provenance": {"provenance_type": "ticket_created"},
        }
        artifact = Artifact.model_validate(data)
        assert artifact.id == "art-001"
        assert artifact.artifact_type == ArtifactType.CODE

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = create_artifact()
        data = original.model_dump()
        restored = Artifact.model_validate(data)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.paths == original.paths
        assert restored.artifact_type == original.artifact_type
