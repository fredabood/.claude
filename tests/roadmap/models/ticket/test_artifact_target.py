"""
Tests for ArtifactTarget criterion target.

Tests cover:
- Basic creation and properties
- All three verification modes (EXISTS, NOT_STALE, HASH_UNCHANGED)
- Refresh from artifact registry
- Status descriptions
- Hash capture functionality
"""

import pytest
from datetime import datetime, timezone
from typing import Optional

from vibey.roadmap.models.ticket.targets import ArtifactTarget, create_target
from vibey.roadmap.models.ticket.artifact import Artifact, ArtifactProvenance
from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactType,
    ArtifactVerification,
    ProvenanceType,
)
from vibey.roadmap.models.ticket.enums import CriterionTargetType
from vibey.roadmap.models.ticket.support import RefreshContext


# =============================================================================
# TEST FIXTURES
# =============================================================================


class MockArtifact:
    """Mock artifact for testing."""

    def __init__(
        self,
        exists: bool = True,
        content_hash: Optional[str] = None,
        is_stale: bool = False,
    ):
        self.exists = exists
        self.content_hash = content_hash
        self.is_stale = is_stale


class MockArtifactRegistry:
    """Mock registry for testing."""

    def __init__(self):
        self._artifacts = {}

    def add(self, artifact_id: str, artifact: MockArtifact) -> None:
        self._artifacts[artifact_id] = artifact

    def get(self, artifact_id: str) -> Optional[MockArtifact]:
        return self._artifacts.get(artifact_id)


class MockRefreshContext:
    """Mock context with artifact registry."""

    def __init__(self, registry: MockArtifactRegistry):
        self.artifact_registry = registry


@pytest.fixture
def registry():
    """Create a mock registry."""
    return MockArtifactRegistry()


@pytest.fixture
def context(registry):
    """Create a mock context with registry."""
    return MockRefreshContext(registry)


# =============================================================================
# BASIC CREATION TESTS
# =============================================================================


class TestArtifactTargetCreation:
    """Tests for ArtifactTarget creation."""

    def test_minimal_creation(self):
        """Test creating with just artifact_id."""
        target = ArtifactTarget(artifact_id="art-001")
        assert target.artifact_id == "art-001"
        assert target.verification == ArtifactVerification.EXISTS
        assert target.type == CriterionTargetType.ARTIFACT

    def test_with_verification_mode(self):
        """Test creating with specific verification mode."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
        )
        assert target.verification == ArtifactVerification.NOT_STALE

    def test_is_automatic(self):
        """Test that is_automatic returns True."""
        target = ArtifactTarget(artifact_id="art-001")
        assert target.is_automatic is True

    def test_default_cached_state(self):
        """Test default cached state values."""
        target = ArtifactTarget(artifact_id="art-001")
        assert target.artifact_exists is False
        assert target.artifact_hash is None
        assert target.artifact_is_stale is False
        assert target.last_checked is None


# =============================================================================
# EXISTS VERIFICATION MODE TESTS
# =============================================================================


class TestExistsVerification:
    """Tests for EXISTS verification mode."""

    def test_is_satisfied_when_exists(self):
        """Test is_satisfied returns True when artifact exists."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.EXISTS,
            artifact_exists=True,
        )
        assert target.is_satisfied() is True

    def test_is_satisfied_when_not_exists(self):
        """Test is_satisfied returns False when artifact doesn't exist."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.EXISTS,
            artifact_exists=False,
        )
        assert target.is_satisfied() is False

    def test_status_description_exists(self):
        """Test status description when exists."""
        target = ArtifactTarget(
            artifact_id="art-001",
            artifact_exists=True,
        )
        desc = target.get_status_description()
        assert "art-001" in desc
        assert "exists" in desc.lower()

    def test_status_description_not_exists(self):
        """Test status description when doesn't exist."""
        target = ArtifactTarget(
            artifact_id="art-001",
            artifact_exists=False,
        )
        desc = target.get_status_description()
        assert "art-001" in desc
        assert "not exist" in desc.lower() or "does not exist" in desc.lower()


# =============================================================================
# NOT_STALE VERIFICATION MODE TESTS
# =============================================================================


class TestNotStaleVerification:
    """Tests for NOT_STALE verification mode."""

    def test_is_satisfied_exists_and_current(self):
        """Test is_satisfied when exists and not stale."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
            artifact_exists=True,
            artifact_is_stale=False,
        )
        assert target.is_satisfied() is True

    def test_is_satisfied_exists_but_stale(self):
        """Test is_satisfied returns False when stale."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
            artifact_exists=True,
            artifact_is_stale=True,
        )
        assert target.is_satisfied() is False

    def test_is_satisfied_not_exists(self):
        """Test is_satisfied returns False when doesn't exist."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
            artifact_exists=False,
            artifact_is_stale=False,
        )
        assert target.is_satisfied() is False

    def test_status_description_current(self):
        """Test status description when current."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
            artifact_exists=True,
            artifact_is_stale=False,
        )
        desc = target.get_status_description()
        assert "art-001" in desc
        assert "current" in desc.lower() or "not stale" in desc.lower() or "exists and is current" in desc.lower()

    def test_status_description_stale(self):
        """Test status description when stale."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
            artifact_exists=True,
            artifact_is_stale=True,
        )
        desc = target.get_status_description()
        assert "art-001" in desc
        assert "stale" in desc.lower()


# =============================================================================
# HASH_UNCHANGED VERIFICATION MODE TESTS
# =============================================================================


class TestHashUnchangedVerification:
    """Tests for HASH_UNCHANGED verification mode."""

    def test_is_satisfied_hash_matches(self):
        """Test is_satisfied when hash matches expected."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=True,
            artifact_hash="abc123",
            expected_hash="abc123",
        )
        assert target.is_satisfied() is True

    def test_is_satisfied_hash_different(self):
        """Test is_satisfied when hash differs from expected."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=True,
            artifact_hash="abc123",
            expected_hash="def456",
        )
        assert target.is_satisfied() is False

    def test_is_satisfied_no_expected_hash(self):
        """Test is_satisfied when no expected hash set."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=True,
            artifact_hash="abc123",
            expected_hash=None,
        )
        # Satisfied if exists and no expected hash
        assert target.is_satisfied() is True

    def test_is_satisfied_not_exists(self):
        """Test is_satisfied returns False when doesn't exist."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=False,
            expected_hash="abc123",
        )
        assert target.is_satisfied() is False

    def test_capture_expected_hash(self):
        """Test capture_expected_hash method."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_hash="current_hash",
        )
        target.capture_expected_hash()
        assert target.expected_hash == "current_hash"

    def test_status_description_unchanged(self):
        """Test status description when hash unchanged."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=True,
            artifact_hash="abc123",
            expected_hash="abc123",
        )
        desc = target.get_status_description()
        assert "art-001" in desc
        assert "unchanged" in desc.lower()

    def test_status_description_changed(self):
        """Test status description when hash changed."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=True,
            artifact_hash="abc123",
            expected_hash="def456",
        )
        desc = target.get_status_description()
        assert "art-001" in desc
        assert "changed" in desc.lower()


# =============================================================================
# REFRESH TESTS
# =============================================================================


class TestArtifactTargetRefresh:
    """Tests for refresh method."""

    def test_refresh_with_existing_artifact(self, registry, context):
        """Test refresh updates cached state from artifact."""
        artifact = MockArtifact(
            exists=True,
            content_hash="hash123",
            is_stale=False,
        )
        registry.add("art-001", artifact)

        target = ArtifactTarget(artifact_id="art-001")
        target.refresh(context)

        assert target.artifact_exists is True
        assert target.artifact_hash == "hash123"
        assert target.artifact_is_stale is False
        assert target.last_checked is not None

    def test_refresh_with_missing_artifact(self, registry, context):
        """Test refresh when artifact not in registry."""
        target = ArtifactTarget(artifact_id="art-missing")
        target.refresh(context)

        assert target.artifact_exists is False
        assert target.artifact_hash is None
        assert target.artifact_is_stale is False
        assert target.last_checked is not None

    def test_refresh_with_stale_artifact(self, registry, context):
        """Test refresh with stale artifact."""
        artifact = MockArtifact(
            exists=True,
            content_hash="hash123",
            is_stale=True,
        )
        registry.add("art-001", artifact)

        target = ArtifactTarget(artifact_id="art-001")
        target.refresh(context)

        assert target.artifact_exists is True
        assert target.artifact_is_stale is True

    def test_refresh_without_context(self):
        """Test refresh does nothing without context."""
        target = ArtifactTarget(artifact_id="art-001")
        target.refresh(None)

        assert target.artifact_exists is False
        assert target.last_checked is None

    def test_refresh_without_registry(self):
        """Test refresh does nothing without registry in context."""

        class EmptyContext:
            pass

        target = ArtifactTarget(artifact_id="art-001")
        target.refresh(EmptyContext())

        assert target.artifact_exists is False
        assert target.last_checked is None


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestCreateTargetFactory:
    """Tests for create_target factory function."""

    def test_create_artifact_target(self):
        """Test creating ArtifactTarget via factory."""
        target = create_target(
            CriterionTargetType.ARTIFACT,
            {"artifact_id": "art-001"},
        )
        assert isinstance(target, ArtifactTarget)
        assert target.artifact_id == "art-001"

    def test_create_with_verification(self):
        """Test creating with verification mode."""
        target = create_target(
            CriterionTargetType.ARTIFACT,
            {
                "artifact_id": "art-001",
                "verification": "not_stale",
            },
        )
        assert target.verification == ArtifactVerification.NOT_STALE


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================


class TestArtifactTargetSerialization:
    """Tests for serialization/deserialization."""

    def test_to_dict(self):
        """Test serialization to dict."""
        target = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.NOT_STALE,
            artifact_exists=True,
            artifact_hash="hash123",
        )
        data = target.model_dump()
        assert data["artifact_id"] == "art-001"
        assert data["verification"] == "not_stale"
        assert data["artifact_exists"] is True
        assert data["artifact_hash"] == "hash123"
        assert data["type"] == "artifact"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "type": "artifact",
            "artifact_id": "art-001",
            "verification": "exists",
            "artifact_exists": True,
        }
        target = ArtifactTarget.model_validate(data)
        assert target.artifact_id == "art-001"
        assert target.verification == ArtifactVerification.EXISTS

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = ArtifactTarget(
            artifact_id="art-001",
            verification=ArtifactVerification.HASH_UNCHANGED,
            artifact_exists=True,
            artifact_hash="hash123",
            expected_hash="hash123",
        )
        data = original.model_dump()
        restored = ArtifactTarget.model_validate(data)

        assert restored.artifact_id == original.artifact_id
        assert restored.verification == original.verification
        assert restored.artifact_hash == original.artifact_hash
        assert restored.expected_hash == original.expected_hash
