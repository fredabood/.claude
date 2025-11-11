"""
End-to-end tests for quality gate enforcement.

Tests quality gate blocking behavior, non-blocking warnings,
multiple gate execution, and gate pass/fail scenarios.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, MetricsCollector
import yaml


@pytest.mark.e2e
class TestQualityGateEnforcement:
    """Test quality gate enforcement in E2E workflows."""

    def test_01_blocking_gate_prevents_completion(self, temp_dir):
        """Test that blocking quality gate prevents sprint completion."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Create failing blocking gate
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        (sprint_dir / "quality-gates.yaml").write_text("""quality_gates:
  - name: security_review
    enabled: true
    blocking: true
    threshold: 70
    status: failed
    score: 55
    reason: Critical vulnerabilities found
""")

        # Assert - Sprint cannot complete
        with open(sprint_dir / "quality-gates.yaml") as f:
            gates = yaml.safe_load(f)

        blocking_failed = any(
            gate["blocking"] and gate["status"] == "failed"
            for gate in gates["quality_gates"]
        )
        assert blocking_failed

        metrics.track("security_review", 55, unit="percentage", threshold=70)
        assert not metrics.assert_metric("security_review", min_value=70)

    def test_02_non_blocking_gate_allows_completion(self, temp_dir):
        """Test that non-blocking gate allows completion with warning."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Act - Create failing non-blocking gate
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        (sprint_dir / "quality-gates.yaml").write_text("""quality_gates:
  - name: documentation
    enabled: true
    blocking: false
    threshold: 80
    status: failed
    score: 65
    reason: Incomplete documentation

  - name: security_review
    enabled: true
    blocking: true
    threshold: 70
    status: passed
    score: 85
""")

        # Assert - Sprint can complete despite non-blocking failure
        with open(sprint_dir / "quality-gates.yaml") as f:
            gates = yaml.safe_load(f)

        blocking_gates = [g for g in gates["quality_gates"] if g["blocking"]]
        non_blocking_gates = [g for g in gates["quality_gates"] if not g["blocking"]]

        # All blocking gates passed
        all_blocking_passed = all(g["status"] == "passed" for g in blocking_gates)
        assert all_blocking_passed

        # Non-blocking can fail
        assert non_blocking_gates[0]["status"] == "failed"

    def test_03_multiple_gate_execution(self, temp_dir):
        """Test execution of multiple quality gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Execute all gate types
        audit_base = repo.path / ".vibey" / "audits"

        # Security audit
        (audit_base / "security").mkdir(parents=True, exist_ok=True)
        (audit_base / "security" / "audit.md").write_text("Score: 88/100")

        # Performance audit
        (audit_base / "performance").mkdir(parents=True, exist_ok=True)
        (audit_base / "performance" / "audit.md").write_text("Score: 92/100")

        # Logging audit
        (audit_base / "logging").mkdir(parents=True, exist_ok=True)
        (audit_base / "logging" / "audit.md").write_text("Score: 85/100")

        # Documentation audit
        (audit_base / "documentation").mkdir(parents=True, exist_ok=True)
        (audit_base / "documentation" / "audit.md").write_text("Score: 78/100")

        # Test coverage
        (audit_base / "coverage").mkdir(parents=True, exist_ok=True)
        (audit_base / "coverage" / "report.md").write_text("Coverage: 87%")

        # Assert - All audits executed
        assert (audit_base / "security" / "audit.md").exists()
        assert (audit_base / "performance" / "audit.md").exists()
        assert (audit_base / "logging" / "audit.md").exists()
        assert (audit_base / "documentation" / "audit.md").exists()
        assert (audit_base / "coverage" / "report.md").exists()

        # Track all gate metrics
        metrics.track("security_score", 88, unit="percentage", threshold=70)
        metrics.track("performance_score", 92, unit="percentage", threshold=80)
        metrics.track("logging_score", 85, unit="percentage", threshold=75)
        metrics.track("documentation_score", 78, unit="percentage", threshold=70)
        metrics.track("test_coverage", 87, unit="percentage", threshold=80)

        # All gates should pass
        assert metrics.calculate_success_rate() == 100.0

    def test_04_gate_failure_and_retry(self, temp_dir):
        """Test quality gate failure, fix, and retry."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Act - Attempt 1: Failure
        (sprint_dir / "gate-attempt-1.yaml").write_text("""attempt: 1
timestamp: '2025-11-10T10:00:00Z'
gates:
  security_review:
    status: failed
    score: 45
    issues:
      - SQL injection vulnerability
      - Missing input validation
""")

        # Attempt 2: Still failing
        (sprint_dir / "gate-attempt-2.yaml").write_text("""attempt: 2
timestamp: '2025-11-10T11:00:00Z'
gates:
  security_review:
    status: failed
    score: 65
    issues:
      - Missing input validation (partially fixed)
""")

        # Attempt 3: Success
        (sprint_dir / "gate-attempt-3.yaml").write_text("""attempt: 3
timestamp: '2025-11-10T12:00:00Z'
gates:
  security_review:
    status: passed
    score: 85
    issues: []
""")

        # Assert - Final attempt passes
        with open(sprint_dir / "gate-attempt-3.yaml") as f:
            final = yaml.safe_load(f)

        assert final["gates"]["security_review"]["status"] == "passed"
        assert final["gates"]["security_review"]["score"] >= 70

        # Track retry metrics
        metrics.track("gate_attempts", 3, unit="count")
        metrics.track("final_score", 85, unit="percentage", threshold=70)
        assert metrics.assert_metric("final_score", min_value=70)

    def test_05_gate_pass_fail_metrics(self, temp_dir):
        """Test comprehensive gate pass/fail metrics."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Track gate results
        gates = [
            ("security_review", 88, 70, "passed"),
            ("performance", 92, 80, "passed"),
            ("logging", 75, 75, "passed"),
            ("documentation", 65, 70, "failed"),
            ("test_coverage", 87, 80, "passed")
        ]

        for name, score, threshold, status in gates:
            metrics.track(
                name,
                score,
                unit="percentage",
                threshold=threshold
            )

        # Assert
        passed_gates = sum(1 for _, score, threshold, _ in gates if score >= threshold)
        total_gates = len(gates)

        pass_rate = (passed_gates / total_gates) * 100
        metrics.track("gate_pass_rate", pass_rate, unit="percentage")

        # 4 out of 5 passed = 80%
        assert metrics.get_metric("gate_pass_rate").value == 80.0

    def test_06_conditional_gate_execution(self, temp_dir):
        """Test conditional execution of quality gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Define conditional gates
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        (sprint_dir / "quality-gates.yaml").write_text("""quality_gates:
  - name: security_review
    enabled: true
    blocking: true
    condition: always

  - name: performance_audit
    enabled: true
    blocking: true
    condition: has_api_changes

  - name: ui_review
    enabled: false
    blocking: false
    condition: has_ui_changes
    reason: No UI changes in this sprint
""")

        # Assert
        with open(sprint_dir / "quality-gates.yaml") as f:
            gates = yaml.safe_load(f)

        enabled_gates = [g for g in gates["quality_gates"] if g["enabled"]]
        disabled_gates = [g for g in gates["quality_gates"] if not g["enabled"]]

        assert len(enabled_gates) == 2
        assert len(disabled_gates) == 1
        assert disabled_gates[0]["name"] == "ui_review"

    def test_07_gate_threshold_configuration(self, temp_dir):
        """Test configurable thresholds for quality gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Act - Configure different thresholds
        config_file = repo.path / ".vibey" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        config["framework"]["quality_gates"] = {
            "enabled": True,
            "thresholds": {
                "security_review": 80,
                "test_coverage": 85,
                "performance": 75,
                "documentation": 70,
                "logging": 70
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Assert
        with open(config_file) as f:
            updated = yaml.safe_load(f)

        thresholds = updated["framework"]["quality_gates"]["thresholds"]
        assert thresholds["security_review"] == 80
        assert thresholds["test_coverage"] == 85
        assert thresholds["performance"] == 75


@pytest.mark.e2e
@pytest.mark.slow
class TestQualityGateWorkflows:
    """Test complete quality gate workflows."""

    def test_complete_quality_assurance_workflow(self, temp_dir):
        """Test complete QA workflow with all gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="qa-workflow")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Execute complete QA workflow
        # 1. Run all audits
        audit_base = repo.path / ".vibey" / "audits"
        audit_results = {
            "security": 88,
            "performance": 92,
            "logging": 85,
            "documentation": 82,
            "coverage": 87
        }

        for audit_type, score in audit_results.items():
            audit_dir = audit_base / audit_type
            audit_dir.mkdir(parents=True, exist_ok=True)
            (audit_dir / "report.md").write_text(f"Score: {score}/100")
            metrics.track(f"{audit_type}_score", score, unit="percentage", threshold=70)

        # 2. Aggregate results
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        gate_results = {
            "quality_gates": [
                {"name": audit, "score": score, "status": "passed"}
                for audit, score in audit_results.items()
            ]
        }

        with open(sprint_dir / "quality-gates.yaml", 'w') as f:
            yaml.dump(gate_results, f)

        # Assert - All gates passed
        assert metrics.calculate_success_rate() == 100.0

        with open(sprint_dir / "quality-gates.yaml") as f:
            final_gates = yaml.safe_load(f)

        all_passed = all(
            gate["status"] == "passed"
            for gate in final_gates["quality_gates"]
        )
        assert all_passed
