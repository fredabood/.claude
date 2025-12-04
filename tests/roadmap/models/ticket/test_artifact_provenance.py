"""
Tests for ArtifactProvenance class.

Tests cover:
- Factory methods for each provenance type
- Validation of type-specific fields
- Serialization/deserialization
"""

import pytest
from datetime import datetime, timezone

from vibey.roadmap.models.ticket.artifact import ArtifactProvenance
from vibey.roadmap.models.ticket.artifact_enums import ProvenanceType


# =============================================================================
# TICKET_CREATED PROVENANCE TESTS
# =============================================================================


class TestTicketCreatedProvenance:
    """Tests for TICKET_CREATED provenance type."""

    def test_factory_minimal(self):
        """Test creating ticket provenance with minimal args."""
        provenance = ArtifactProvenance.ticket_created(ticket_id="task-001")

        assert provenance.provenance_type == ProvenanceType.TICKET_CREATED
        assert provenance.created_by_ticket_id == "task-001"
        assert provenance.created_by_criterion_id is None

    def test_factory_with_criterion(self):
        """Test creating ticket provenance with criterion."""
        provenance = ArtifactProvenance.ticket_created(
            ticket_id="task-001",
            criterion_id="crit-deliverable-1",
        )

        assert provenance.provenance_type == ProvenanceType.TICKET_CREATED
        assert provenance.created_by_ticket_id == "task-001"
        assert provenance.created_by_criterion_id == "crit-deliverable-1"

    def test_other_fields_none(self):
        """Test that non-relevant fields are None."""
        provenance = ArtifactProvenance.ticket_created(ticket_id="task-001")

        assert provenance.discovered_at is None
        assert provenance.discovered_by is None
        assert provenance.generator_type is None
        assert provenance.external_source is None
        assert provenance.framework_component_type is None


# =============================================================================
# PRE_EXISTING PROVENANCE TESTS
# =============================================================================


class TestPreExistingProvenance:
    """Tests for PRE_EXISTING provenance type."""

    def test_factory_defaults(self):
        """Test creating pre-existing provenance with defaults."""
        provenance = ArtifactProvenance.pre_existing()

        assert provenance.provenance_type == ProvenanceType.PRE_EXISTING
        assert provenance.discovered_by == "filesystem_scan"
        assert provenance.discovered_at is not None
        assert isinstance(provenance.discovered_at, datetime)

    def test_factory_custom_discoverer(self):
        """Test creating pre-existing provenance with custom discoverer."""
        provenance = ArtifactProvenance.pre_existing(discovered_by="user-import")

        assert provenance.provenance_type == ProvenanceType.PRE_EXISTING
        assert provenance.discovered_by == "user-import"

    def test_discovered_at_has_timezone(self):
        """Test that discovered_at has timezone info."""
        provenance = ArtifactProvenance.pre_existing()

        assert provenance.discovered_at.tzinfo is not None

    def test_other_fields_none(self):
        """Test that non-relevant fields are None."""
        provenance = ArtifactProvenance.pre_existing()

        assert provenance.created_by_ticket_id is None
        assert provenance.generator_type is None
        assert provenance.external_source is None
        assert provenance.framework_component_type is None


# =============================================================================
# GENERATED PROVENANCE TESTS
# =============================================================================


class TestGeneratedProvenance:
    """Tests for GENERATED provenance type."""

    def test_factory_minimal(self):
        """Test creating generated provenance with minimal args."""
        provenance = ArtifactProvenance.generated(generator_type="sphinx")

        assert provenance.provenance_type == ProvenanceType.GENERATED
        assert provenance.generator_type == "sphinx"
        assert provenance.source_artifact_ids == []
        assert provenance.generator_config is None

    def test_factory_with_sources(self):
        """Test creating generated provenance with source artifacts."""
        provenance = ArtifactProvenance.generated(
            generator_type="pdoc",
            source_artifact_ids=["art-code-1", "art-code-2"],
        )

        assert provenance.generator_type == "pdoc"
        assert provenance.source_artifact_ids == ["art-code-1", "art-code-2"]

    def test_factory_with_config(self):
        """Test creating generated provenance with config."""
        config = {"output_format": "html", "theme": "readthedocs"}
        provenance = ArtifactProvenance.generated(
            generator_type="mkdocs",
            generator_config=config,
        )

        assert provenance.generator_type == "mkdocs"
        assert provenance.generator_config == config

    def test_factory_full(self):
        """Test creating generated provenance with all fields."""
        config = {"output_dir": "docs/api"}
        provenance = ArtifactProvenance.generated(
            generator_type="typedoc",
            source_artifact_ids=["art-ts-models"],
            generator_config=config,
        )

        assert provenance.provenance_type == ProvenanceType.GENERATED
        assert provenance.generator_type == "typedoc"
        assert provenance.source_artifact_ids == ["art-ts-models"]
        assert provenance.generator_config == config

    def test_other_fields_none(self):
        """Test that non-relevant fields are None."""
        provenance = ArtifactProvenance.generated(generator_type="sphinx")

        assert provenance.created_by_ticket_id is None
        assert provenance.discovered_at is None
        assert provenance.external_source is None
        assert provenance.framework_component_type is None


# =============================================================================
# EXTERNAL PROVENANCE TESTS
# =============================================================================


class TestExternalProvenance:
    """Tests for EXTERNAL provenance type."""

    def test_factory_minimal(self):
        """Test creating external provenance with minimal args."""
        provenance = ArtifactProvenance.external(source="https://example.com/lib.js")

        assert provenance.provenance_type == ProvenanceType.EXTERNAL
        assert provenance.external_source == "https://example.com/lib.js"
        assert provenance.external_version is None

    def test_factory_with_version(self):
        """Test creating external provenance with version."""
        provenance = ArtifactProvenance.external(
            source="npm:lodash",
            version="4.17.21",
        )

        assert provenance.external_source == "npm:lodash"
        assert provenance.external_version == "4.17.21"

    def test_various_source_formats(self):
        """Test various external source formats."""
        # URL
        prov1 = ArtifactProvenance.external(source="https://cdn.example.com/file.js")
        assert prov1.external_source == "https://cdn.example.com/file.js"

        # Package reference
        prov2 = ArtifactProvenance.external(source="pip:requests")
        assert prov2.external_source == "pip:requests"

        # Git reference
        prov3 = ArtifactProvenance.external(source="git:github.com/user/repo")
        assert prov3.external_source == "git:github.com/user/repo"

    def test_other_fields_none(self):
        """Test that non-relevant fields are None."""
        provenance = ArtifactProvenance.external(source="https://example.com")

        assert provenance.created_by_ticket_id is None
        assert provenance.discovered_at is None
        assert provenance.generator_type is None
        assert provenance.framework_component_type is None


# =============================================================================
# FRAMEWORK PROVENANCE TESTS
# =============================================================================


class TestFrameworkProvenance:
    """Tests for FRAMEWORK provenance type."""

    def test_factory_agent(self):
        """Test creating framework provenance for agent."""
        provenance = ArtifactProvenance.framework(component_type="agent")

        assert provenance.provenance_type == ProvenanceType.FRAMEWORK
        assert provenance.framework_component_type == "agent"

    def test_factory_workflow(self):
        """Test creating framework provenance for workflow."""
        provenance = ArtifactProvenance.framework(component_type="workflow")

        assert provenance.framework_component_type == "workflow"

    def test_factory_template(self):
        """Test creating framework provenance for template."""
        provenance = ArtifactProvenance.framework(component_type="template")

        assert provenance.framework_component_type == "template"

    def test_other_fields_none(self):
        """Test that non-relevant fields are None."""
        provenance = ArtifactProvenance.framework(component_type="agent")

        assert provenance.created_by_ticket_id is None
        assert provenance.discovered_at is None
        assert provenance.generator_type is None
        assert provenance.external_source is None


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================


class TestProvenanceSerialization:
    """Tests for provenance serialization/deserialization."""

    def test_ticket_created_round_trip(self):
        """Test serialization round-trip for TICKET_CREATED."""
        original = ArtifactProvenance.ticket_created(
            ticket_id="task-001",
            criterion_id="crit-001",
        )

        data = original.model_dump()
        restored = ArtifactProvenance.model_validate(data)

        assert restored.provenance_type == original.provenance_type
        assert restored.created_by_ticket_id == original.created_by_ticket_id
        assert restored.created_by_criterion_id == original.created_by_criterion_id

    def test_pre_existing_round_trip(self):
        """Test serialization round-trip for PRE_EXISTING."""
        original = ArtifactProvenance.pre_existing(discovered_by="user-scan")

        data = original.model_dump()
        restored = ArtifactProvenance.model_validate(data)

        assert restored.provenance_type == original.provenance_type
        assert restored.discovered_by == original.discovered_by

    def test_generated_round_trip(self):
        """Test serialization round-trip for GENERATED."""
        config = {"theme": "dark"}
        original = ArtifactProvenance.generated(
            generator_type="sphinx",
            source_artifact_ids=["art-1", "art-2"],
            generator_config=config,
        )

        data = original.model_dump()
        restored = ArtifactProvenance.model_validate(data)

        assert restored.provenance_type == original.provenance_type
        assert restored.generator_type == original.generator_type
        assert restored.source_artifact_ids == original.source_artifact_ids
        assert restored.generator_config == original.generator_config

    def test_external_round_trip(self):
        """Test serialization round-trip for EXTERNAL."""
        original = ArtifactProvenance.external(
            source="npm:lodash",
            version="4.17.21",
        )

        data = original.model_dump()
        restored = ArtifactProvenance.model_validate(data)

        assert restored.provenance_type == original.provenance_type
        assert restored.external_source == original.external_source
        assert restored.external_version == original.external_version

    def test_framework_round_trip(self):
        """Test serialization round-trip for FRAMEWORK."""
        original = ArtifactProvenance.framework(component_type="workflow")

        data = original.model_dump()
        restored = ArtifactProvenance.model_validate(data)

        assert restored.provenance_type == original.provenance_type
        assert restored.framework_component_type == original.framework_component_type

    def test_json_mode(self):
        """Test JSON serialization mode."""
        original = ArtifactProvenance.ticket_created(ticket_id="task-001")

        json_data = original.model_dump(mode="json")

        assert isinstance(json_data, dict)
        assert json_data["provenance_type"] == "ticket_created"
        assert json_data["created_by_ticket_id"] == "task-001"


# =============================================================================
# DIRECT CONSTRUCTION TESTS
# =============================================================================


class TestProvenanceDirectConstruction:
    """Tests for direct provenance construction."""

    def test_construct_directly(self):
        """Test constructing provenance directly without factory."""
        provenance = ArtifactProvenance(
            provenance_type=ProvenanceType.TICKET_CREATED,
            created_by_ticket_id="task-002",
        )

        assert provenance.provenance_type == ProvenanceType.TICKET_CREATED
        assert provenance.created_by_ticket_id == "task-002"

    def test_construct_with_mixed_fields(self):
        """Test that mixed fields are allowed (model doesn't enforce type-specific constraints)."""
        # This is technically valid even though it's semantically wrong
        # The model allows flexibility for edge cases
        provenance = ArtifactProvenance(
            provenance_type=ProvenanceType.TICKET_CREATED,
            created_by_ticket_id="task-001",
            external_source="should-not-be-here",  # Semantically wrong but allowed
        )

        assert provenance.created_by_ticket_id == "task-001"
        assert provenance.external_source == "should-not-be-here"

    def test_construct_from_dict(self):
        """Test constructing from dictionary."""
        data = {
            "provenance_type": "generated",
            "generator_type": "sphinx",
            "source_artifact_ids": ["art-1"],
        }
        provenance = ArtifactProvenance.model_validate(data)

        assert provenance.provenance_type == ProvenanceType.GENERATED
        assert provenance.generator_type == "sphinx"
