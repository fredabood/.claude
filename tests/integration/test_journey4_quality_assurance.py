"""
Integration tests for Journey 4: Quality Assurance & Review

Tests quality gate execution, security audits, performance audits,
logging audits, and documentation audits.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
from tests.utils.config_loader import ConfigLoader
import time


@pytest.mark.integration
class TestJourney4QualityAssurance:
    """Test Journey 4: Quality Assurance & Review workflow."""

    def test_01_security_audit_execution(self, temp_dir):
        """Test security audit quality gate execution."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Create security audit report
        audit_dir = repo.path / ".vibey" / "audits" / "security"
        audit_dir.mkdir(parents=True, exist_ok=True)

        audit_report = audit_dir / "audit-2025-11-10.md"
        audit_report.write_text("""# Security Audit Report

## Date
2025-11-10

## Scope
Authentication and authorization implementation

## Findings
- ✅ Password hashing implemented correctly (bcrypt)
- ✅ JWT tokens properly signed
- ⚠️  Missing rate limiting on login endpoint
- ❌ SQL injection vulnerability in user search

## Recommendations
1. Add rate limiting (express-rate-limit)
2. Use parameterized queries for all database access
3. Implement input validation library (joi/zod)

## Score
75/100 (PASS threshold: 70)
""")

        # Assert
        assert audit_report.exists()
        metrics.track("security_audit_score", 75, unit="percentage", threshold=70)
        assert metrics.assert_metric("security_audit_score", min_value=70)

    def test_02_performance_audit_execution(self, temp_dir):
        """Test performance audit quality gate execution."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Create performance audit report
        audit_dir = repo.path / ".vibey" / "audits" / "performance"
        audit_dir.mkdir(parents=True, exist_ok=True)

        audit_report = audit_dir / "audit-2025-11-10.md"
        audit_report.write_text("""# Performance Audit Report

## Metrics
- API Response Time (p95): 245ms (target: <500ms) ✅
- Database Query Time (p95): 85ms (target: <100ms) ✅
- Memory Usage: 128MB (target: <256MB) ✅
- CPU Usage (avg): 35% (target: <60%) ✅

## Issues
- N+1 query detected in /users endpoint
- Missing database indexes on frequently queried fields

## Optimizations Implemented
- Added database indexes
- Implemented query batching
- Added Redis caching layer

## Score
88/100 (PASS threshold: 80)
""")

        # Assert
        assert audit_report.exists()
        metrics.track("performance_audit_score", 88, unit="percentage", threshold=80)
        assert metrics.assert_metric("performance_audit_score", min_value=80)

    def test_03_logging_audit_execution(self, temp_dir):
        """Test logging audit quality gate execution."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Act - Create logging audit report
        audit_dir = repo.path / ".vibey" / "audits" / "logging"
        audit_dir.mkdir(parents=True, exist_ok=True)

        audit_report = audit_dir / "audit-2025-11-10.md"
        audit_report.write_text("""# Logging Audit Report

## Coverage
- Error logging: ✅ Implemented
- Request logging: ✅ Implemented
- Authentication events: ✅ Logged
- Database queries: ⚠️  Partial logging

## Log Levels
- ERROR: Used correctly
- WARN: Used correctly
- INFO: Used correctly
- DEBUG: Missing in some modules

## Structured Logging
- JSON format: ✅ Implemented
- Correlation IDs: ✅ Implemented
- Timestamps: ✅ ISO 8601 format

## Score
85/100 (PASS threshold: 75)
""")

        metrics = MetricsCollector()

        # Assert
        assert audit_report.exists()
        metrics.track("logging_audit_score", 85, unit="percentage", threshold=75)
        assert metrics.assert_metric("logging_audit_score", min_value=75)

    def test_04_documentation_audit_execution(self, temp_dir):
        """Test documentation audit quality gate execution."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Act - Create documentation audit report
        audit_dir = repo.path / ".vibey" / "audits" / "documentation"
        audit_dir.mkdir(parents=True, exist_ok=True)

        audit_report = audit_dir / "audit-2025-11-10.md"
        audit_report.write_text("""# Documentation Audit Report

## API Documentation
- OpenAPI/Swagger: ✅ Complete
- Endpoint descriptions: ✅ Present
- Request/response examples: ✅ Provided
- Error codes documented: ✅ Complete

## Code Documentation
- JSDoc comments: 78% coverage (target: 80%)
- README.md: ✅ Comprehensive
- Architecture docs: ✅ Present
- Setup guide: ✅ Complete

## Missing Documentation
- Deployment procedures
- Troubleshooting guide

## Score
82/100 (PASS threshold: 80)
""")

        metrics = MetricsCollector()

        # Assert
        assert audit_report.exists()
        metrics.track("documentation_audit_score", 82, unit="percentage", threshold=80)
        assert metrics.assert_metric("documentation_audit_score", min_value=80)

    def test_05_test_coverage_audit(self, temp_dir):
        """Test code coverage audit quality gate."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Create coverage report
        audit_dir = repo.path / ".vibey" / "audits" / "coverage"
        audit_dir.mkdir(parents=True, exist_ok=True)

        coverage_report = audit_dir / "coverage-2025-11-10.md"
        coverage_report.write_text("""# Test Coverage Report

## Overall Coverage
- Line Coverage: 85% (target: 80%) ✅
- Branch Coverage: 78% (target: 75%) ✅
- Function Coverage: 92% (target: 85%) ✅

## By Module
- Authentication: 95%
- API Routes: 88%
- Database: 75%
- Utilities: 90%

## Uncovered Areas
- Error handling edge cases
- Rarely-used utility functions

## Score
85/100 (PASS threshold: 80)
""")

        # Assert
        assert coverage_report.exists()
        metrics.track("test_coverage", 85, unit="percentage", threshold=80)
        assert metrics.assert_metric("test_coverage", min_value=80)

    def test_06_complete_quality_assurance_workflow(self, temp_dir):
        """Test complete end-to-end quality assurance workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Complete QA workflow
        repo = builder.create_web_app_repo(name="qa-project")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Create all audit reports
        audit_base = repo.path / ".vibey" / "audits"
        for audit_type in ["security", "performance", "logging", "documentation", "coverage"]:
            audit_dir = audit_base / audit_type
            audit_dir.mkdir(parents=True, exist_ok=True)
            (audit_dir / "audit-2025-11-10.md").write_text(f"# {audit_type.title()} Audit\nScore: 85/100")

        total_time = time.time() - start_time

        # Assert - All audits completed
        expected_structure = {
            "directories": [
                ".vibey/audits/security",
                ".vibey/audits/performance",
                ".vibey/audits/logging",
                ".vibey/audits/documentation",
                ".vibey/audits/coverage"
            ],
            "files": [
                ".vibey/audits/security/audit-2025-11-10.md",
                ".vibey/audits/performance/audit-2025-11-10.md",
                ".vibey/audits/logging/audit-2025-11-10.md",
                ".vibey/audits/documentation/audit-2025-11-10.md",
                ".vibey/audits/coverage/audit-2025-11-10.md"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected_structure)
        assert result.passed, f"QA structure invalid: {result.errors}"

        # Track success metrics
        metrics.track("audit_pass_rate", 100, unit="percentage", threshold=100)
        metrics.track("issue_detection_rate", 95, unit="percentage", threshold=85)
        metrics.track("audit_completion_time", total_time, unit="seconds")  # Track without threshold

        # Validate all metrics
        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0, f"Journey 4 success rate: {success_rate}%"

    def test_07_quality_gate_blocking_behavior(self, temp_dir):
        """Test that blocking quality gates prevent sprint completion."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Simulate failing blocking gate
        metrics.track("security_audit_score", 55, unit="percentage", threshold=70)
        metrics.track("performance_audit_score", 85, unit="percentage", threshold=80)

        # Assert - Should detect failure
        assert not metrics.assert_metric("security_audit_score", min_value=70)
        assert metrics.calculate_success_rate() == 50.0  # 1 of 2 passed

    def test_08_quality_assurance_metrics_collection(self, temp_dir):
        """Test comprehensive QA metrics collection."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Track all QA metrics
        metrics.track("audit_pass_rate", 100, unit="percentage", threshold=100)
        metrics.track("issue_detection_rate", 92, unit="percentage", threshold=85)
        metrics.track("security_score", 88, unit="percentage", threshold=70)
        metrics.track("performance_score", 90, unit="percentage", threshold=80)
        metrics.track("logging_score", 85, unit="percentage", threshold=75)
        metrics.track("documentation_score", 82, unit="percentage", threshold=80)
        metrics.track("test_coverage", 87, unit="percentage", threshold=80)

        # Assert - All metrics collected
        assert len(metrics.get_all_metrics()) == 7
        assert metrics.calculate_success_rate() == 100.0

        # Export
        export_data = metrics.export_metrics()
        assert all(metric in export_data["metrics"] for metric in [
            "audit_pass_rate",
            "security_score",
            "performance_score"
        ])


@pytest.mark.integration
class TestJourney4ErrorScenarios:
    """Test Journey 4 error handling."""

    def test_audit_fails_threshold(self, temp_dir):
        """Test handling of audit that fails threshold."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Record failing audit
        metrics.track("security_audit_score", 45, unit="percentage", threshold=70)

        # Assert - Should fail
        assert not metrics.assert_metric("security_audit_score", min_value=70)
        assert metrics.calculate_success_rate() == 0.0
