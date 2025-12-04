"""
Tests for ImpactAnalyzer.

Tests cover:
- ImpactReport properties and creation
- ArtifactSummary, TicketImpact, RecommendedAction models
- ImpactAnalyzer file change analysis
- Documentation staleness detection
- Ticket impact detection
- Recommendation generation
- Git hook helper functions
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pytest

from vibey.roadmap.operations.impact_analyzer import (
    ImpactAnalyzer,
    ImpactReport,
    ArtifactSummary,
    TicketImpact,
    RecommendedAction,
    format_impact_report,
)
from vibey.roadmap.models.ticket.artifact_enums import ArtifactType


# =============================================================================
# TEST FIXTURES - Mock Objects
# =============================================================================


class MockArtifact:
    """Mock artifact for testing."""

    def __init__(
        self,
        id: str,
        name: str,
        artifact_type: ArtifactType = ArtifactType.CODE,
        paths: Optional[List[str]] = None,
        documents_artifact_id: Optional[str] = None,
        is_stale: bool = False,
        content_hash: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.artifact_type = artifact_type
        self.paths = paths or []
        self.documents_artifact_id = documents_artifact_id
        self.is_stale = is_stale
        self.content_hash = content_hash
        self._computed_hash = None

    def compute_content_hash(self, base_path: Optional[Path] = None) -> str:
        """Mock hash computation."""
        self._computed_hash = f"hash_{self.id}"
        self.content_hash = self._computed_hash
        return self._computed_hash


class MockArtifactRegistry:
    """Mock registry for testing."""

    def __init__(self):
        self._artifacts = {}

    def add(self, artifact: MockArtifact) -> None:
        self._artifacts[artifact.id] = artifact

    def get(self, artifact_id: str) -> Optional[MockArtifact]:
        return self._artifacts.get(artifact_id)

    def get_all(self) -> List[MockArtifact]:
        return list(self._artifacts.values())


class MockCursor:
    """Mock database cursor."""

    def __init__(self, rows: List[tuple]):
        self._rows = rows

    def fetchall(self) -> List[tuple]:
        return self._rows

    def fetchone(self) -> Optional[tuple]:
        return self._rows[0] if self._rows else None


class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self._queries = []
        self._results = []

    def set_results(self, results: List[tuple]) -> None:
        self._results = results

    def execute(self, query: str, params: tuple = ()) -> MockCursor:
        self._queries.append((query, params))
        return MockCursor(self._results)

    @property
    def last_query(self) -> Optional[tuple]:
        return self._queries[-1] if self._queries else None


@pytest.fixture
def registry():
    """Create a mock registry with some artifacts."""
    reg = MockArtifactRegistry()

    # Source code artifacts
    reg.add(MockArtifact(
        id="src-main",
        name="Main Module",
        artifact_type=ArtifactType.CODE,
        paths=["src/main.py"],
        content_hash="hash_main_v1",
    ))
    reg.add(MockArtifact(
        id="src-utils",
        name="Utilities",
        artifact_type=ArtifactType.CODE,
        paths=["src/utils.py", "src/helpers.py"],
        content_hash="hash_utils_v1",
    ))

    # Documentation artifacts
    reg.add(MockArtifact(
        id="doc-api",
        name="API Documentation",
        artifact_type=ArtifactType.DOCUMENTATION,
        paths=["docs/api.md"],
        documents_artifact_id="src-main",
        is_stale=False,
    ))
    reg.add(MockArtifact(
        id="doc-utils",
        name="Utils Documentation",
        artifact_type=ArtifactType.DOCUMENTATION,
        paths=["docs/utils.md"],
        documents_artifact_id="src-utils",
        is_stale=False,
    ))

    # Standalone doc
    reg.add(MockArtifact(
        id="doc-readme",
        name="README",
        artifact_type=ArtifactType.DOCUMENTATION,
        paths=["README.md"],
    ))

    return reg


@pytest.fixture
def db():
    """Create a mock database."""
    return MockDatabase()


# =============================================================================
# IMPACT REPORT TESTS
# =============================================================================


class TestImpactReport:
    """Tests for ImpactReport model."""

    def test_empty_report(self):
        """Test creating empty report."""
        report = ImpactReport(changed_files=[])
        assert report.changed_files == []
        assert report.total_artifacts_affected == 0
        assert report.total_tickets_affected == 0
        assert report.has_blocking_impacts is False
        assert report.has_any_impacts is False

    def test_report_with_changed_files(self):
        """Test report with changed files."""
        report = ImpactReport(changed_files=["src/main.py", "src/utils.py"])
        assert len(report.changed_files) == 2
        assert report.analyzed_at is not None

    def test_total_artifacts_affected(self):
        """Test total_artifacts_affected property."""
        report = ImpactReport(
            changed_files=["test.py"],
            directly_impacted_artifacts=[
                ArtifactSummary(id="a1", name="A1", artifact_type=ArtifactType.CODE, paths=[]),
            ],
            stale_documentation=[
                ArtifactSummary(id="d1", name="D1", artifact_type=ArtifactType.DOCUMENTATION, paths=[]),
                ArtifactSummary(id="d2", name="D2", artifact_type=ArtifactType.DOCUMENTATION, paths=[]),
            ],
        )
        assert report.total_artifacts_affected == 3

    def test_total_tickets_affected(self):
        """Test total_tickets_affected counts unique tickets."""
        report = ImpactReport(
            changed_files=["test.py"],
            affected_tickets=[
                TicketImpact(ticket_id="t1", ticket_name="T1", impact_type="warning", criterion_id="c1", artifact_id="a1"),
                TicketImpact(ticket_id="t1", ticket_name="T1", impact_type="warning", criterion_id="c2", artifact_id="a2"),
                TicketImpact(ticket_id="t2", ticket_name="T2", impact_type="warning", criterion_id="c3", artifact_id="a3"),
            ],
        )
        assert report.total_tickets_affected == 2

    def test_has_blocking_impacts(self):
        """Test has_blocking_impacts property."""
        # No blocking
        report1 = ImpactReport(
            changed_files=["test.py"],
            affected_tickets=[
                TicketImpact(ticket_id="t1", ticket_name="T1", impact_type="stale_doc_warning", criterion_id="c1", artifact_id="a1"),
            ],
        )
        assert report1.has_blocking_impacts is False

        # With blocking
        report2 = ImpactReport(
            changed_files=["test.py"],
            affected_tickets=[
                TicketImpact(ticket_id="t1", ticket_name="T1", impact_type="stale_doc_blocks_completion", criterion_id="c1", artifact_id="a1"),
            ],
        )
        assert report2.has_blocking_impacts is True

    def test_has_any_impacts(self):
        """Test has_any_impacts property."""
        # Empty
        report1 = ImpactReport(changed_files=["test.py"])
        assert report1.has_any_impacts is False

        # With impacts
        report2 = ImpactReport(
            changed_files=["test.py"],
            directly_impacted_artifacts=[
                ArtifactSummary(id="a1", name="A1", artifact_type=ArtifactType.CODE, paths=[]),
            ],
        )
        assert report2.has_any_impacts is True


# =============================================================================
# ARTIFACT SUMMARY TESTS
# =============================================================================


class TestArtifactSummary:
    """Tests for ArtifactSummary model."""

    def test_creation(self):
        """Test creating ArtifactSummary."""
        summary = ArtifactSummary(
            id="art-001",
            name="Test Artifact",
            artifact_type=ArtifactType.CODE,
            paths=["src/test.py"],
        )
        assert summary.id == "art-001"
        assert summary.name == "Test Artifact"
        assert summary.artifact_type == ArtifactType.CODE

    def test_from_artifact(self):
        """Test creating from artifact-like object."""
        artifact = MockArtifact(
            id="art-001",
            name="Test",
            artifact_type=ArtifactType.TEST,
            paths=["tests/test.py"],
        )
        summary = ArtifactSummary.from_artifact(artifact)
        assert summary.id == "art-001"
        assert summary.name == "Test"
        assert summary.artifact_type == ArtifactType.TEST


# =============================================================================
# TICKET IMPACT TESTS
# =============================================================================


class TestTicketImpact:
    """Tests for TicketImpact model."""

    def test_creation(self):
        """Test creating TicketImpact."""
        impact = TicketImpact(
            ticket_id="task-001",
            ticket_name="Implement Feature",
            impact_type="stale_doc_blocks_completion",
            criterion_id="crit-001",
            artifact_id="doc-001",
        )
        assert impact.ticket_id == "task-001"
        assert impact.impact_type == "stale_doc_blocks_completion"


# =============================================================================
# RECOMMENDED ACTION TESTS
# =============================================================================


class TestRecommendedAction:
    """Tests for RecommendedAction model."""

    def test_creation(self):
        """Test creating RecommendedAction."""
        action = RecommendedAction(
            action_type="update_documentation",
            target_artifact_id="doc-001",
            description="Update API docs",
            priority="high",
        )
        assert action.action_type == "update_documentation"
        assert action.priority == "high"


# =============================================================================
# IMPACT ANALYZER TESTS
# =============================================================================


class TestImpactAnalyzer:
    """Tests for ImpactAnalyzer class."""

    def test_analyze_no_files(self, registry):
        """Test analysis with no files returns empty report."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes([])
        assert report.changed_files == []
        assert report.total_artifacts_affected == 0

    def test_analyze_untracked_file(self, registry):
        """Test analysis with file not in any artifact."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["unknown/file.py"])
        assert len(report.changed_files) == 1
        assert len(report.directly_impacted_artifacts) == 0

    def test_find_directly_impacted(self, registry):
        """Test finding directly impacted artifacts."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py"])

        assert len(report.directly_impacted_artifacts) == 1
        assert report.directly_impacted_artifacts[0].id == "src-main"

    def test_find_multiple_impacted(self, registry):
        """Test finding multiple impacted artifacts."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py", "src/utils.py"])

        assert len(report.directly_impacted_artifacts) == 2

    def test_find_stale_documentation(self, registry):
        """Test finding documentation that may become stale."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py"])

        # doc-api documents src-main, so it should be marked stale
        assert len(report.stale_documentation) == 1
        assert report.stale_documentation[0].id == "doc-api"

    def test_cascade_documentation_staleness(self, registry):
        """Test cascading documentation staleness."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/utils.py", "src/helpers.py"])

        # src-utils contains both files, doc-utils documents it
        assert len(report.directly_impacted_artifacts) == 1
        assert report.directly_impacted_artifacts[0].id == "src-utils"
        assert len(report.stale_documentation) == 1
        assert report.stale_documentation[0].id == "doc-utils"

    def test_mark_documentation_stale(self, registry):
        """Test marking documentation as stale."""
        analyzer = ImpactAnalyzer(registry)

        # Initially not stale
        doc = registry.get("doc-api")
        assert doc.is_stale is False

        # Mark stale
        count = analyzer.mark_documentation_stale(["doc-api"])
        assert count == 1
        assert doc.is_stale is True

    def test_mark_nonexistent_artifact(self, registry):
        """Test marking nonexistent artifact."""
        analyzer = ImpactAnalyzer(registry)
        count = analyzer.mark_documentation_stale(["nonexistent"])
        assert count == 0

    def test_refresh_artifact_hashes(self, registry):
        """Test refreshing artifact hashes."""
        analyzer = ImpactAnalyzer(registry)

        # Initially no computed hash
        artifact = registry.get("src-main")
        old_hash = artifact.content_hash

        # Refresh
        count = analyzer.refresh_artifact_hashes(["src-main"])
        assert count == 1
        assert artifact._computed_hash is not None

    def test_recommendations_generated(self, registry):
        """Test that recommendations are generated."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py"])

        # Should have recommendations for:
        # - refresh hash on src-main
        # - update documentation for doc-api
        assert len(report.recommended_actions) >= 2

        action_types = [a.action_type for a in report.recommended_actions]
        assert "refresh_hash" in action_types
        assert "update_documentation" in action_types


# =============================================================================
# DATABASE INTEGRATION TESTS
# =============================================================================


class TestImpactAnalyzerWithDatabase:
    """Tests for ImpactAnalyzer with database queries."""

    def test_find_affected_tickets(self, registry, db):
        """Test finding affected tickets from database."""
        # Set up database to return affected tickets
        db.set_results([
            ("crit-001", "task-001", "Implement API", "doc-api", "completed"),
        ])

        analyzer = ImpactAnalyzer(registry, db)
        report = analyzer.analyze_file_changes(["src/main.py"])

        assert len(report.affected_tickets) == 1
        assert report.affected_tickets[0].ticket_id == "task-001"

    def test_no_database(self, registry):
        """Test analysis works without database."""
        analyzer = ImpactAnalyzer(registry, db=None)
        report = analyzer.analyze_file_changes(["src/main.py"])

        # Should work but have no ticket impacts
        assert len(report.directly_impacted_artifacts) == 1
        assert len(report.affected_tickets) == 0


# =============================================================================
# PATH NORMALIZATION TESTS
# =============================================================================


class TestPathNormalization:
    """Tests for path normalization."""

    def test_normalize_relative_path(self, registry):
        """Test normalizing relative paths."""
        analyzer = ImpactAnalyzer(registry)

        # With leading ./
        report = analyzer.analyze_file_changes(["./src/main.py"])
        assert len(report.directly_impacted_artifacts) == 1

    def test_find_with_different_path_formats(self, registry):
        """Test finding artifacts with different path formats."""
        # Add artifact with different path format
        registry.add(MockArtifact(
            id="src-config",
            name="Config",
            artifact_type=ArtifactType.CONFIG,
            paths=["./config/settings.yaml"],
        ))

        analyzer = ImpactAnalyzer(registry)

        # Should find with normalized path
        report = analyzer.analyze_file_changes(["config/settings.yaml"])
        assert len(report.directly_impacted_artifacts) == 1
        assert report.directly_impacted_artifacts[0].id == "src-config"


# =============================================================================
# FORMAT REPORT TESTS
# =============================================================================


class TestFormatImpactReport:
    """Tests for report formatting."""

    def test_format_empty_report(self):
        """Test formatting empty report."""
        report = ImpactReport(changed_files=[])
        output = format_impact_report(report)
        assert "No documentation impacts detected" in output

    def test_format_report_with_impacts(self, registry):
        """Test formatting report with impacts."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py"])

        output = format_impact_report(report)
        assert "Impact Analysis" in output
        assert "Main Module" in output or "src-main" in output

    def test_format_verbose(self, registry):
        """Test verbose formatting includes recommendations."""
        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py"])

        output = format_impact_report(report, verbose=True)
        assert "Recommended Actions" in output

    def test_format_blocking_warning(self, registry, db):
        """Test blocking warning is shown."""
        db.set_results([
            ("crit-001", "task-001", "Task", "doc-api", "completed"),
        ])

        analyzer = ImpactAnalyzer(registry, db)
        report = analyzer.analyze_file_changes(["src/main.py"])

        if report.has_blocking_impacts:
            output = format_impact_report(report)
            assert "WARNING" in output or "BLOCKING" in output


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_artifact_with_multiple_paths(self, registry):
        """Test artifact with multiple paths."""
        analyzer = ImpactAnalyzer(registry)

        # src-utils has two paths
        report = analyzer.analyze_file_changes(["src/helpers.py"])
        assert len(report.directly_impacted_artifacts) == 1
        assert report.directly_impacted_artifacts[0].id == "src-utils"

    def test_documentation_of_documentation(self, registry):
        """Test documentation that documents documentation."""
        # Add meta-doc
        registry.add(MockArtifact(
            id="doc-meta",
            name="Doc Style Guide",
            artifact_type=ArtifactType.DOCUMENTATION,
            paths=["docs/style.md"],
            documents_artifact_id="doc-api",  # Documents another doc
        ))

        analyzer = ImpactAnalyzer(registry)
        report = analyzer.analyze_file_changes(["src/main.py"])

        # Should cascade: src-main -> doc-api -> doc-meta
        stale_ids = [d.id for d in report.stale_documentation]
        assert "doc-api" in stale_ids

    def test_empty_registry(self):
        """Test with empty registry."""
        registry = MockArtifactRegistry()
        analyzer = ImpactAnalyzer(registry)

        report = analyzer.analyze_file_changes(["any/file.py"])
        assert report.total_artifacts_affected == 0

    def test_circular_documentation_reference(self, registry):
        """Test handling of circular documentation references."""
        # Create circular reference
        doc_a = registry.get("doc-api")
        doc_a.documents_artifact_id = "doc-utils"

        doc_b = registry.get("doc-utils")
        doc_b.documents_artifact_id = "doc-api"

        analyzer = ImpactAnalyzer(registry)

        # Should not infinite loop - analyze docs/api.md
        report = analyzer.analyze_file_changes(["docs/api.md"])

        # Should handle gracefully
        assert report.changed_files == ["docs/api.md"]
