"""
Tests for CI integration module.
"""

import pytest
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path

from vibey.operations.git.ci_integration import (
    CIPlatform,
    GateResult,
    GateMapping,
    GateCheckResult,
    CIStatusReport,
    CIConfig,
    CIIntegration,
    check_ci_gates,
    format_ci_output,
    get_pr_gate_section,
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository with quality gates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create roadmap structure
        roadmap_root = repo / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        # Create roadmap.yaml with quality gates
        roadmap_yaml = {
            'roadmap': {
                'id': 'test-roadmap',
                'name': 'Test Roadmap',
                'quality_gates': [
                    {
                        'name': 'Test Coverage',
                        'threshold': 80,
                        'blocking': True,
                        'status': 'not_run',
                        'score': None
                    },
                    {
                        'name': 'Test Pass Rate',
                        'threshold': 100,
                        'blocking': True,
                        'status': 'not_run',
                        'score': 95
                    },
                    {
                        'name': 'Documentation',
                        'threshold': 90,
                        'blocking': False,
                        'status': 'not_run',
                        'score': 85
                    }
                ]
            }
        }
        with open(repo / ".vibey" / "roadmap.yaml", 'w') as f:
            yaml.dump(roadmap_yaml, f)

        # Create track with gates
        track_dir = roadmap_root / "test-track"
        track_dir.mkdir()

        track_yaml = {
            'track': {
                'id': 'test-track',
                'name': 'Test Track',
                'status': 'in_progress',
                'quality_gates': [
                    {
                        'name': 'Integration Tests',
                        'threshold': 90,
                        'blocking': True,
                        'status': 'passed',
                        'score': 95
                    }
                ]
            }
        }
        with open(track_dir / "track.yaml", 'w') as f:
            yaml.dump(track_yaml, f)

        # Create sprint with gates
        sprint_dir = track_dir / "test-sprint-1"
        sprint_dir.mkdir()

        sprint_yaml = {
            'sprint': {
                'id': 'test-sprint-1',
                'name': 'Test Sprint',
                'status': 'in_progress',
                'quality_gates': [
                    {
                        'name': 'Sprint Coverage',
                        'threshold': 85,
                        'blocking': True,
                        'status': 'not_run',
                        'score': 90
                    }
                ]
            }
        }
        with open(sprint_dir / "sprint.yaml", 'w') as f:
            yaml.dump(sprint_yaml, f)

        # Initialize git
        import subprocess
        subprocess.run(['git', 'init'], cwd=repo, capture_output=True)
        subprocess.run(['git', 'add', '.'], cwd=repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Initial'],
            cwd=repo,
            capture_output=True,
            env={'GIT_AUTHOR_NAME': 'Test', 'GIT_AUTHOR_EMAIL': 'test@test.com',
                 'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 'test@test.com'}
        )

        yield repo


class TestCIPlatform:
    """Tests for CIPlatform enum."""

    def test_platform_values(self):
        """Test CI platform values."""
        assert CIPlatform.GITHUB_ACTIONS.value == "github_actions"
        assert CIPlatform.GITLAB_CI.value == "gitlab_ci"
        assert CIPlatform.JENKINS.value == "jenkins"
        assert CIPlatform.GENERIC.value == "generic"


class TestGateResult:
    """Tests for GateResult enum."""

    def test_result_values(self):
        """Test gate result values."""
        assert GateResult.PASSED.value == "passed"
        assert GateResult.FAILED.value == "failed"
        assert GateResult.SKIPPED.value == "skipped"
        assert GateResult.PENDING.value == "pending"


class TestGateMapping:
    """Tests for GateMapping dataclass."""

    def test_gate_mapping_creation(self):
        """Test creating a gate mapping."""
        mapping = GateMapping(
            gate_name="Test Coverage",
            ci_job_name="test",
            threshold=80.0,
            required=True
        )

        assert mapping.gate_name == "Test Coverage"
        assert mapping.ci_job_name == "test"
        assert mapping.threshold == 80.0
        assert mapping.required

    def test_gate_mapping_with_override(self):
        """Test gate mapping with threshold override."""
        mapping = GateMapping(
            gate_name="Test Coverage",
            ci_job_name="test",
            threshold=80.0,
            threshold_override={'main': 90.0, 'develop': 75.0}
        )

        assert mapping.threshold_override['main'] == 90.0


class TestCIStatusReport:
    """Tests for CIStatusReport dataclass."""

    def test_report_passed(self):
        """Test a passing report."""
        report = CIStatusReport(
            platform=CIPlatform.GITHUB_ACTIONS,
            branch="main",
            commit_sha="abc123",
            gates=[
                GateCheckResult(
                    gate_name="Test",
                    result=GateResult.PASSED,
                    score=95.0,
                    threshold=80.0,
                    message="Passed"
                )
            ],
            overall_result=GateResult.PASSED,
            blocking_gates=[]
        )

        assert report.passed
        assert len(report.failed_gates) == 0

    def test_report_failed(self):
        """Test a failing report."""
        report = CIStatusReport(
            platform=CIPlatform.GITHUB_ACTIONS,
            branch="main",
            commit_sha="abc123",
            gates=[
                GateCheckResult(
                    gate_name="Test",
                    result=GateResult.FAILED,
                    score=70.0,
                    threshold=80.0,
                    message="Failed"
                )
            ],
            overall_result=GateResult.FAILED,
            blocking_gates=["Test"]
        )

        assert not report.passed
        assert len(report.failed_gates) == 1


class TestCIIntegration:
    """Tests for CIIntegration class."""

    def test_init(self, temp_repo):
        """Test initialization."""
        ci = CIIntegration(str(temp_repo))
        assert ci.repo_path == temp_repo

    def test_detect_platform_generic(self, temp_repo):
        """Test platform detection without CI environment."""
        ci = CIIntegration(str(temp_repo))
        platform = ci._detect_platform()
        assert platform == CIPlatform.GENERIC

    def test_load_quality_gates_from_roadmap(self, temp_repo):
        """Test loading gates from main roadmap."""
        ci = CIIntegration(str(temp_repo))
        gates = ci._load_quality_gates()

        assert len(gates) == 3
        gate_names = [g['name'] for g in gates]
        assert 'Test Coverage' in gate_names

    def test_load_quality_gates_from_track(self, temp_repo):
        """Test loading gates from track."""
        ci = CIIntegration(str(temp_repo))
        gates = ci._load_quality_gates(track_id='test-track')

        assert len(gates) == 1
        assert gates[0]['name'] == 'Integration Tests'

    def test_load_quality_gates_from_sprint(self, temp_repo):
        """Test loading gates from sprint."""
        ci = CIIntegration(str(temp_repo))
        gates = ci._load_quality_gates(sprint_id='test-sprint-1')

        assert len(gates) == 1
        assert gates[0]['name'] == 'Sprint Coverage'

    def test_check_gates(self, temp_repo):
        """Test checking gates."""
        ci = CIIntegration(str(temp_repo))
        report = ci.check_gates()

        assert report.branch is not None
        assert len(report.gates) == 3  # From roadmap

    def test_check_gates_with_ci_results(self, temp_repo):
        """Test checking gates with CI results."""
        ci = CIIntegration(str(temp_repo))
        report = ci.check_gates(ci_results={
            'Test Coverage': 85.0,
            'Test Pass Rate': 100.0,
            'Documentation': 95.0
        })

        # Test Coverage should pass (85 >= 80)
        coverage_gate = next(g for g in report.gates if g.gate_name == 'Test Coverage')
        assert coverage_gate.result == GateResult.PASSED

    def test_format_github_annotations(self, temp_repo):
        """Test GitHub Actions annotation formatting."""
        ci = CIIntegration(str(temp_repo))
        report = ci.check_gates(ci_results={
            'Test Coverage': 85.0,
            'Test Pass Rate': 100.0,
            'Documentation': 95.0
        })

        output = ci.format_github_annotations(report)
        assert "::" in output  # GitHub annotation syntax

    def test_format_gitlab_ci_output(self, temp_repo):
        """Test GitLab CI output formatting."""
        ci = CIIntegration(str(temp_repo))
        report = ci.check_gates()

        output = ci.format_gitlab_ci_output(report)
        assert "Quality Gate Report" in output
        assert "Branch:" in output

    def test_format_json_output(self, temp_repo):
        """Test JSON output formatting."""
        ci = CIIntegration(str(temp_repo))
        report = ci.check_gates()

        output = ci.format_json_output(report)
        import json
        data = json.loads(output)
        assert 'gates' in data
        assert 'overall_result' in data

    def test_generate_pr_description_section(self, temp_repo):
        """Test PR description generation."""
        ci = CIIntegration(str(temp_repo))
        report = ci.check_gates()

        section = ci.generate_pr_description_section(report)
        assert "## Quality Gates" in section
        assert "| Gate |" in section

    def test_should_block_merge_passed(self, temp_repo):
        """Test merge blocking when gates pass."""
        ci = CIIntegration(str(temp_repo))
        report = CIStatusReport(
            platform=CIPlatform.GENERIC,
            branch="main",
            commit_sha="abc",
            gates=[],
            overall_result=GateResult.PASSED,
            blocking_gates=[]
        )

        should_block, reason = ci.should_block_merge(report)
        assert not should_block

    def test_should_block_merge_failed(self, temp_repo):
        """Test merge blocking when gates fail."""
        ci = CIIntegration(str(temp_repo))
        report = CIStatusReport(
            platform=CIPlatform.GENERIC,
            branch="main",
            commit_sha="abc",
            gates=[],
            overall_result=GateResult.FAILED,
            blocking_gates=["Test Coverage"]
        )

        should_block, reason = ci.should_block_merge(report)
        assert should_block
        assert "Test Coverage" in reason


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_check_ci_gates(self, temp_repo):
        """Test check_ci_gates convenience function."""
        report = check_ci_gates(repo_path=str(temp_repo))

        assert isinstance(report, CIStatusReport)
        assert report.branch is not None

    def test_format_ci_output_auto(self, temp_repo):
        """Test format_ci_output with auto detection."""
        report = check_ci_gates(repo_path=str(temp_repo))
        output = format_ci_output(report, format_type="auto")

        assert len(output) > 0

    def test_format_ci_output_json(self, temp_repo):
        """Test format_ci_output with JSON format."""
        report = check_ci_gates(repo_path=str(temp_repo))
        output = format_ci_output(report, format_type="json")

        import json
        data = json.loads(output)
        assert 'gates' in data

    def test_get_pr_gate_section(self, temp_repo):
        """Test get_pr_gate_section convenience function."""
        section = get_pr_gate_section(repo_path=str(temp_repo))

        assert "## Quality Gates" in section
