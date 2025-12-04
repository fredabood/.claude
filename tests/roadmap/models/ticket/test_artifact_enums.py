"""
Tests for artifact system enums.

Tests cover:
- ArtifactType enum and properties
- ProvenanceType enum and properties
- ArtifactVerification enum and properties
- ContextArtifactSubtype enum and properties
- DocumentationSubtype enum and properties
- DocumentationHealth enum and properties
"""

import pytest

from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactType,
    ProvenanceType,
    ArtifactVerification,
    ContextArtifactSubtype,
    DocumentationSubtype,
    DocumentationHealth,
)


# =============================================================================
# ARTIFACT TYPE TESTS
# =============================================================================


class TestArtifactType:
    """Tests for ArtifactType enum."""

    def test_all_values_defined(self):
        """Test that all expected values exist."""
        assert ArtifactType.CODE.value == "code"
        assert ArtifactType.TEST.value == "test"
        assert ArtifactType.CONFIG.value == "config"
        assert ArtifactType.DOCUMENTATION.value == "documentation"
        assert ArtifactType.CONTEXT.value == "context"
        assert ArtifactType.AGENT.value == "agent"
        assert ArtifactType.WORKFLOW.value == "workflow"
        assert ArtifactType.TEMPLATE.value == "template"
        assert ArtifactType.DATA.value == "data"
        assert ArtifactType.ASSET.value == "asset"
        assert ArtifactType.SCHEMA.value == "schema"
        assert ArtifactType.OTHER.value == "other"

    def test_is_documentation_type_true(self):
        """Test is_documentation_type for documentation types."""
        assert ArtifactType.DOCUMENTATION.is_documentation_type is True
        assert ArtifactType.CONTEXT.is_documentation_type is True

    def test_is_documentation_type_false(self):
        """Test is_documentation_type for non-documentation types."""
        assert ArtifactType.CODE.is_documentation_type is False
        assert ArtifactType.TEST.is_documentation_type is False
        assert ArtifactType.AGENT.is_documentation_type is False

    def test_is_code_type_true(self):
        """Test is_code_type for code types."""
        assert ArtifactType.CODE.is_code_type is True
        assert ArtifactType.TEST.is_code_type is True
        assert ArtifactType.CONFIG.is_code_type is True

    def test_is_code_type_false(self):
        """Test is_code_type for non-code types."""
        assert ArtifactType.DOCUMENTATION.is_code_type is False
        assert ArtifactType.AGENT.is_code_type is False
        assert ArtifactType.ASSET.is_code_type is False

    def test_is_framework_type_true(self):
        """Test is_framework_type for framework types."""
        assert ArtifactType.AGENT.is_framework_type is True
        assert ArtifactType.WORKFLOW.is_framework_type is True
        assert ArtifactType.TEMPLATE.is_framework_type is True

    def test_is_framework_type_false(self):
        """Test is_framework_type for non-framework types."""
        assert ArtifactType.CODE.is_framework_type is False
        assert ArtifactType.DOCUMENTATION.is_framework_type is False
        assert ArtifactType.DATA.is_framework_type is False


class TestArtifactTypeFromExtension:
    """Tests for ArtifactType.from_extension method."""

    def test_python_file(self):
        """Test .py extension maps to CODE."""
        assert ArtifactType.from_extension(".py") == ArtifactType.CODE
        assert ArtifactType.from_extension("py") == ArtifactType.CODE

    def test_javascript_file(self):
        """Test .js extension maps to CODE."""
        assert ArtifactType.from_extension(".js") == ArtifactType.CODE

    def test_typescript_file(self):
        """Test .ts extension maps to CODE."""
        assert ArtifactType.from_extension(".ts") == ArtifactType.CODE
        assert ArtifactType.from_extension(".tsx") == ArtifactType.CODE

    def test_yaml_file(self):
        """Test .yaml extension maps to CONFIG."""
        assert ArtifactType.from_extension(".yaml") == ArtifactType.CONFIG
        assert ArtifactType.from_extension(".yml") == ArtifactType.CONFIG

    def test_json_file(self):
        """Test .json extension maps to CONFIG."""
        assert ArtifactType.from_extension(".json") == ArtifactType.CONFIG

    def test_markdown_file(self):
        """Test .md extension maps to DOCUMENTATION."""
        assert ArtifactType.from_extension(".md") == ArtifactType.DOCUMENTATION
        assert ArtifactType.from_extension(".rst") == ArtifactType.DOCUMENTATION

    def test_image_file(self):
        """Test image extensions map to ASSET."""
        assert ArtifactType.from_extension(".png") == ArtifactType.ASSET
        assert ArtifactType.from_extension(".jpg") == ArtifactType.ASSET
        assert ArtifactType.from_extension(".svg") == ArtifactType.ASSET

    def test_schema_file(self):
        """Test schema extensions map to SCHEMA."""
        assert ArtifactType.from_extension(".graphql") == ArtifactType.SCHEMA
        assert ArtifactType.from_extension(".proto") == ArtifactType.SCHEMA

    def test_data_file(self):
        """Test data extensions map to DATA."""
        assert ArtifactType.from_extension(".csv") == ArtifactType.DATA
        assert ArtifactType.from_extension(".sqlite") == ArtifactType.DATA

    def test_unknown_extension(self):
        """Test unknown extension maps to OTHER."""
        assert ArtifactType.from_extension(".xyz") == ArtifactType.OTHER
        assert ArtifactType.from_extension("unknown") == ArtifactType.OTHER

    def test_case_insensitive(self):
        """Test extension matching is case-insensitive."""
        assert ArtifactType.from_extension(".PY") == ArtifactType.CODE
        assert ArtifactType.from_extension(".MD") == ArtifactType.DOCUMENTATION


# =============================================================================
# PROVENANCE TYPE TESTS
# =============================================================================


class TestProvenanceType:
    """Tests for ProvenanceType enum."""

    def test_all_values_defined(self):
        """Test that all expected values exist."""
        assert ProvenanceType.TICKET_CREATED.value == "ticket_created"
        assert ProvenanceType.PRE_EXISTING.value == "pre_existing"
        assert ProvenanceType.GENERATED.value == "generated"
        assert ProvenanceType.EXTERNAL.value == "external"
        assert ProvenanceType.FRAMEWORK.value == "framework"

    def test_is_tracked_true(self):
        """Test is_tracked for ticket-created artifacts."""
        assert ProvenanceType.TICKET_CREATED.is_tracked is True

    def test_is_tracked_false(self):
        """Test is_tracked for non-ticket-created artifacts."""
        assert ProvenanceType.PRE_EXISTING.is_tracked is False
        assert ProvenanceType.GENERATED.is_tracked is False
        assert ProvenanceType.EXTERNAL.is_tracked is False
        assert ProvenanceType.FRAMEWORK.is_tracked is False

    def test_is_auto_generated_true(self):
        """Test is_auto_generated for generated artifacts."""
        assert ProvenanceType.GENERATED.is_auto_generated is True

    def test_is_auto_generated_false(self):
        """Test is_auto_generated for non-generated artifacts."""
        assert ProvenanceType.TICKET_CREATED.is_auto_generated is False
        assert ProvenanceType.PRE_EXISTING.is_auto_generated is False


# =============================================================================
# ARTIFACT VERIFICATION TESTS
# =============================================================================


class TestArtifactVerification:
    """Tests for ArtifactVerification enum."""

    def test_all_values_defined(self):
        """Test that all expected values exist."""
        assert ArtifactVerification.EXISTS.value == "exists"
        assert ArtifactVerification.NOT_STALE.value == "not_stale"
        assert ArtifactVerification.HASH_UNCHANGED.value == "hash_unchanged"

    def test_default(self):
        """Test default verification mode."""
        assert ArtifactVerification.default() == ArtifactVerification.EXISTS

    def test_checks_staleness_true(self):
        """Test checks_staleness for staleness-aware modes."""
        assert ArtifactVerification.NOT_STALE.checks_staleness is True

    def test_checks_staleness_false(self):
        """Test checks_staleness for non-staleness-aware modes."""
        assert ArtifactVerification.EXISTS.checks_staleness is False
        assert ArtifactVerification.HASH_UNCHANGED.checks_staleness is False

    def test_is_content_aware_true(self):
        """Test is_content_aware for content-aware modes."""
        assert ArtifactVerification.NOT_STALE.is_content_aware is True
        assert ArtifactVerification.HASH_UNCHANGED.is_content_aware is True

    def test_is_content_aware_false(self):
        """Test is_content_aware for non-content-aware modes."""
        assert ArtifactVerification.EXISTS.is_content_aware is False


# =============================================================================
# CONTEXT ARTIFACT SUBTYPE TESTS
# =============================================================================


class TestContextArtifactSubtype:
    """Tests for ContextArtifactSubtype enum."""

    def test_all_values_defined(self):
        """Test that all expected values exist."""
        assert ContextArtifactSubtype.PLANNING_DOC.value == "planning_doc"
        assert ContextArtifactSubtype.IMPLEMENTATION_NOTES.value == "impl_notes"
        assert ContextArtifactSubtype.DECISION_RECORD.value == "decision_record"
        assert ContextArtifactSubtype.AUDIT_REPORT.value == "audit_report"
        assert ContextArtifactSubtype.RETROSPECTIVE.value == "retrospective"

    def test_is_pre_work_true(self):
        """Test is_pre_work for pre-work context."""
        assert ContextArtifactSubtype.PLANNING_DOC.is_pre_work is True
        assert ContextArtifactSubtype.DECISION_RECORD.is_pre_work is True

    def test_is_pre_work_false(self):
        """Test is_pre_work for non-pre-work context."""
        assert ContextArtifactSubtype.IMPLEMENTATION_NOTES.is_pre_work is False
        assert ContextArtifactSubtype.AUDIT_REPORT.is_pre_work is False
        assert ContextArtifactSubtype.RETROSPECTIVE.is_pre_work is False

    def test_is_during_work_true(self):
        """Test is_during_work for during-work context."""
        assert ContextArtifactSubtype.IMPLEMENTATION_NOTES.is_during_work is True

    def test_is_during_work_false(self):
        """Test is_during_work for non-during-work context."""
        assert ContextArtifactSubtype.PLANNING_DOC.is_during_work is False
        assert ContextArtifactSubtype.RETROSPECTIVE.is_during_work is False

    def test_is_post_work_true(self):
        """Test is_post_work for post-work context."""
        assert ContextArtifactSubtype.AUDIT_REPORT.is_post_work is True
        assert ContextArtifactSubtype.RETROSPECTIVE.is_post_work is True

    def test_is_post_work_false(self):
        """Test is_post_work for non-post-work context."""
        assert ContextArtifactSubtype.PLANNING_DOC.is_post_work is False
        assert ContextArtifactSubtype.IMPLEMENTATION_NOTES.is_post_work is False


# =============================================================================
# DOCUMENTATION SUBTYPE TESTS
# =============================================================================


class TestDocumentationSubtype:
    """Tests for DocumentationSubtype enum."""

    def test_all_values_defined(self):
        """Test that all expected values exist."""
        assert DocumentationSubtype.README.value == "readme"
        assert DocumentationSubtype.API_REFERENCE.value == "api_reference"
        assert DocumentationSubtype.USER_GUIDE.value == "user_guide"
        assert DocumentationSubtype.ARCHITECTURE.value == "architecture"
        assert DocumentationSubtype.CHANGELOG.value == "changelog"
        assert DocumentationSubtype.TUTORIAL.value == "tutorial"

    def test_is_reference_true(self):
        """Test is_reference for reference documentation."""
        assert DocumentationSubtype.README.is_reference is True
        assert DocumentationSubtype.API_REFERENCE.is_reference is True

    def test_is_reference_false(self):
        """Test is_reference for non-reference documentation."""
        assert DocumentationSubtype.USER_GUIDE.is_reference is False
        assert DocumentationSubtype.TUTORIAL.is_reference is False
        assert DocumentationSubtype.CHANGELOG.is_reference is False

    def test_is_guide_true(self):
        """Test is_guide for guide documentation."""
        assert DocumentationSubtype.USER_GUIDE.is_guide is True
        assert DocumentationSubtype.TUTORIAL.is_guide is True

    def test_is_guide_false(self):
        """Test is_guide for non-guide documentation."""
        assert DocumentationSubtype.README.is_guide is False
        assert DocumentationSubtype.API_REFERENCE.is_guide is False
        assert DocumentationSubtype.ARCHITECTURE.is_guide is False


# =============================================================================
# DOCUMENTATION HEALTH TESTS
# =============================================================================


class TestDocumentationHealth:
    """Tests for DocumentationHealth enum."""

    def test_all_values_defined(self):
        """Test that all expected values exist."""
        assert DocumentationHealth.HEALTHY.value == "healthy"
        assert DocumentationHealth.DEGRADED.value == "degraded"
        assert DocumentationHealth.CRITICAL.value == "critical"

    def test_is_healthy_true(self):
        """Test is_healthy for healthy status."""
        assert DocumentationHealth.HEALTHY.is_healthy is True

    def test_is_healthy_false(self):
        """Test is_healthy for non-healthy status."""
        assert DocumentationHealth.DEGRADED.is_healthy is False
        assert DocumentationHealth.CRITICAL.is_healthy is False

    def test_is_blocking_true(self):
        """Test is_blocking for blocking status."""
        assert DocumentationHealth.CRITICAL.is_blocking is True

    def test_is_blocking_false(self):
        """Test is_blocking for non-blocking status."""
        assert DocumentationHealth.HEALTHY.is_blocking is False
        assert DocumentationHealth.DEGRADED.is_blocking is False


class TestDocumentationHealthFromStaleCount:
    """Tests for DocumentationHealth.from_stale_count method."""

    def test_no_stale_docs_is_healthy(self):
        """Test zero stale docs returns HEALTHY."""
        assert DocumentationHealth.from_stale_count(0, 0) == DocumentationHealth.HEALTHY

    def test_stale_non_blocking_is_degraded(self):
        """Test stale but non-blocking returns DEGRADED."""
        assert DocumentationHealth.from_stale_count(5, 0) == DocumentationHealth.DEGRADED
        assert DocumentationHealth.from_stale_count(1, 0) == DocumentationHealth.DEGRADED

    def test_blocking_stale_is_critical(self):
        """Test blocking stale docs returns CRITICAL."""
        assert DocumentationHealth.from_stale_count(5, 1) == DocumentationHealth.CRITICAL
        assert DocumentationHealth.from_stale_count(1, 1) == DocumentationHealth.CRITICAL
        assert DocumentationHealth.from_stale_count(0, 1) == DocumentationHealth.CRITICAL


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================


class TestEnumSerialization:
    """Tests for JSON/YAML serialization compatibility."""

    def test_artifact_type_to_string(self):
        """Test ArtifactType serializes to string."""
        assert str(ArtifactType.CODE) == "ArtifactType.CODE"
        assert ArtifactType.CODE.value == "code"

    def test_artifact_type_from_string(self):
        """Test ArtifactType deserializes from string."""
        assert ArtifactType("code") == ArtifactType.CODE
        assert ArtifactType("documentation") == ArtifactType.DOCUMENTATION

    def test_provenance_type_to_string(self):
        """Test ProvenanceType serializes to string."""
        assert ProvenanceType.TICKET_CREATED.value == "ticket_created"

    def test_provenance_type_from_string(self):
        """Test ProvenanceType deserializes from string."""
        assert ProvenanceType("ticket_created") == ProvenanceType.TICKET_CREATED

    def test_all_enums_are_str_enum(self):
        """Test all enums inherit from str for serialization."""
        assert isinstance(ArtifactType.CODE, str)
        assert isinstance(ProvenanceType.TICKET_CREATED, str)
        assert isinstance(ArtifactVerification.EXISTS, str)
        assert isinstance(ContextArtifactSubtype.PLANNING_DOC, str)
        assert isinstance(DocumentationSubtype.README, str)
        assert isinstance(DocumentationHealth.HEALTHY, str)
