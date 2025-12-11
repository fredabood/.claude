"""
Quality gate CI/CD integration.

This module provides:
- Quality gate status reporting for CI systems
- GitHub Actions integration (check annotations)
- GitLab CI integration (job results)
- Gate-based merge blocking
- Auto-update gate scores from CI results
"""

import json
import os
import subprocess
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class CIPlatform(Enum):
    """Supported CI platforms."""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    GENERIC = "generic"


class GateResult(Enum):
    """Quality gate check result."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class GateMapping:
    """Mapping between a quality gate and CI job."""
    gate_name: str
    ci_job_name: str
    threshold: float
    required: bool = True
    threshold_override: Optional[Dict[str, float]] = None  # branch -> threshold


@dataclass
class GateCheckResult:
    """Result of a single gate check."""
    gate_name: str
    result: GateResult
    score: Optional[float]
    threshold: float
    message: str
    ci_job: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class CIStatusReport:
    """Overall CI status report for quality gates."""
    platform: CIPlatform
    branch: str
    commit_sha: str
    gates: List[GateCheckResult]
    overall_result: GateResult
    blocking_gates: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def passed(self) -> bool:
        return self.overall_result == GateResult.PASSED

    @property
    def failed_gates(self) -> List[GateCheckResult]:
        return [g for g in self.gates if g.result == GateResult.FAILED]


@dataclass
class CIConfig:
    """CI integration configuration."""
    platform: CIPlatform
    gate_mappings: List[GateMapping]
    block_merge_on_failure: bool = True
    auto_update_scores: bool = True
    annotation_level: str = "warning"  # 'error', 'warning', 'notice'


class CIIntegration:
    """
    Quality gate integration with CI/CD systems.

    Provides gate status reporting, CI platform integration,
    and merge blocking based on gate results.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.roadmap_root = self.repo_path / ".vibey" / "roadmap"
        self.config_path = self.repo_path / ".vibey" / "config" / "ci-integration.yaml"
        self._config: Optional[CIConfig] = None

    def _run_git(self, args: List[str], check: bool = True) -> Tuple[bool, str, str]:
        """Run a git command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return False, e.stdout, e.stderr

    def _detect_platform(self) -> CIPlatform:
        """Auto-detect CI platform from environment."""
        if os.environ.get('GITHUB_ACTIONS'):
            return CIPlatform.GITHUB_ACTIONS
        elif os.environ.get('GITLAB_CI'):
            return CIPlatform.GITLAB_CI
        elif os.environ.get('JENKINS_URL'):
            return CIPlatform.JENKINS
        return CIPlatform.GENERIC

    def _get_current_branch(self) -> str:
        """Get current git branch name."""
        success, stdout, _ = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'], check=False)
        if success:
            return stdout.strip()
        return 'unknown'

    def _get_current_commit(self) -> str:
        """Get current git commit SHA."""
        success, stdout, _ = self._run_git(['rev-parse', 'HEAD'], check=False)
        if success:
            return stdout.strip()[:8]
        return 'unknown'

    def _load_config(self) -> CIConfig:
        """Load CI integration configuration."""
        if self._config:
            return self._config

        # Default configuration
        default_mappings = [
            GateMapping(
                gate_name="Test Coverage",
                ci_job_name="test",
                threshold=80.0,
                required=True
            ),
            GateMapping(
                gate_name="Test Pass Rate",
                ci_job_name="test",
                threshold=100.0,
                required=True
            ),
            GateMapping(
                gate_name="Documentation",
                ci_job_name="docs",
                threshold=90.0,
                required=False
            ),
        ]

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)

                if data and 'ci_integration' in data:
                    ci_data = data['ci_integration']
                    mappings = []
                    for m in ci_data.get('gate_mappings', []):
                        mappings.append(GateMapping(
                            gate_name=m['gate_name'],
                            ci_job_name=m['ci_job_name'],
                            threshold=m.get('threshold', 80.0),
                            required=m.get('required', True),
                            threshold_override=m.get('threshold_override')
                        ))

                    self._config = CIConfig(
                        platform=CIPlatform(ci_data.get('platform', 'generic')),
                        gate_mappings=mappings or default_mappings,
                        block_merge_on_failure=ci_data.get('block_merge_on_failure', True),
                        auto_update_scores=ci_data.get('auto_update_scores', True),
                        annotation_level=ci_data.get('annotation_level', 'warning')
                    )
                    return self._config
            except Exception:
                pass

        # Return default config
        self._config = CIConfig(
            platform=self._detect_platform(),
            gate_mappings=default_mappings,
            block_merge_on_failure=True,
            auto_update_scores=True,
            annotation_level='warning'
        )
        return self._config

    def _load_quality_gates(self, sprint_id: Optional[str] = None,
                           track_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load quality gates from roadmap files.

        Args:
            sprint_id: Optional sprint to get gates from
            track_id: Optional track to get gates from

        Returns:
            List of quality gate dictionaries
        """
        gates = []

        # If sprint specified, load sprint gates from flat structure
        if sprint_id:
            sprint_path = self.roadmap_root / "sprints" / f"{sprint_id}.yaml"
            if sprint_path.exists():
                with open(sprint_path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'sprint' in data:
                        gates.extend(data['sprint'].get('quality_gates', []))

        # If track specified, load track gates from flat structure
        if track_id:
            track_path = self.roadmap_root / "tracks" / f"{track_id}.yaml"
            if track_path.exists():
                with open(track_path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'track' in data:
                        gates.extend(data['track'].get('quality_gates', []))

        # If no specific item, load from main roadmap
        if not sprint_id and not track_id:
            roadmap_path = self.roadmap_root.parent / "roadmap.yaml"
            if roadmap_path.exists():
                with open(roadmap_path, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'roadmap' in data:
                        gates.extend(data['roadmap'].get('quality_gates', []))

        return gates

    def _get_threshold_for_branch(self, mapping: GateMapping, branch: str) -> float:
        """Get threshold for a specific branch, with override support."""
        if mapping.threshold_override and branch in mapping.threshold_override:
            return mapping.threshold_override[branch]
        return mapping.threshold

    def check_gates(self, sprint_id: Optional[str] = None,
                   track_id: Optional[str] = None,
                   ci_results: Optional[Dict[str, float]] = None) -> CIStatusReport:
        """
        Check quality gates and generate CI status report.

        Args:
            sprint_id: Optional sprint to check gates for
            track_id: Optional track to check gates for
            ci_results: Optional dict mapping gate names to scores from CI

        Returns:
            CIStatusReport with gate check results
        """
        config = self._load_config()
        branch = self._get_current_branch()
        commit = self._get_current_commit()

        # Load quality gates from roadmap
        gates = self._load_quality_gates(sprint_id, track_id)

        gate_results = []
        blocking_gates = []

        for gate in gates:
            gate_name = gate.get('name', 'Unknown')
            threshold = gate.get('threshold', 80.0)
            is_blocking = gate.get('blocking', True)
            current_score = gate.get('score')

            # Check if we have CI results for this gate
            if ci_results and gate_name in ci_results:
                current_score = ci_results[gate_name]

            # Find mapping for this gate
            mapping = None
            for m in config.gate_mappings:
                if m.gate_name.lower() == gate_name.lower():
                    mapping = m
                    threshold = self._get_threshold_for_branch(m, branch)
                    break

            # Determine result
            if current_score is None:
                result = GateResult.PENDING
                message = f"Gate '{gate_name}' has no score yet"
            elif current_score >= threshold:
                result = GateResult.PASSED
                message = f"Gate '{gate_name}' passed: {current_score:.1f}% >= {threshold:.1f}%"
            else:
                result = GateResult.FAILED
                message = f"Gate '{gate_name}' failed: {current_score:.1f}% < {threshold:.1f}%"
                if is_blocking:
                    blocking_gates.append(gate_name)

            gate_results.append(GateCheckResult(
                gate_name=gate_name,
                result=result,
                score=current_score,
                threshold=threshold,
                message=message,
                ci_job=mapping.ci_job_name if mapping else None,
                details={'blocking': is_blocking}
            ))

        # Determine overall result
        if blocking_gates:
            overall_result = GateResult.FAILED
        elif any(g.result == GateResult.PENDING for g in gate_results):
            overall_result = GateResult.PENDING
        elif all(g.result == GateResult.PASSED for g in gate_results):
            overall_result = GateResult.PASSED
        else:
            overall_result = GateResult.PASSED  # Non-blocking failures don't fail overall

        return CIStatusReport(
            platform=config.platform,
            branch=branch,
            commit_sha=commit,
            gates=gate_results,
            overall_result=overall_result,
            blocking_gates=blocking_gates
        )

    def format_github_annotations(self, report: CIStatusReport) -> str:
        """
        Format gate results as GitHub Actions annotations.

        Args:
            report: CI status report

        Returns:
            String with GitHub Actions annotation commands
        """
        lines = []

        for gate in report.gates:
            if gate.result == GateResult.FAILED:
                level = "error" if gate.details and gate.details.get('blocking') else "warning"
                lines.append(f"::{level}::{gate.message}")
            elif gate.result == GateResult.PASSED:
                lines.append(f"::notice::{gate.message}")

        # Summary
        if report.passed:
            lines.append("::notice::All quality gates passed!")
        else:
            lines.append(f"::error::Quality gates failed: {', '.join(report.blocking_gates)}")

        return "\n".join(lines)

    def format_gitlab_ci_output(self, report: CIStatusReport) -> str:
        """
        Format gate results for GitLab CI.

        Args:
            report: CI status report

        Returns:
            String formatted for GitLab CI output
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Quality Gate Report")
        lines.append("=" * 60)
        lines.append(f"Branch: {report.branch}")
        lines.append(f"Commit: {report.commit_sha}")
        lines.append(f"Timestamp: {report.timestamp.isoformat()}")
        lines.append("")

        for gate in report.gates:
            status_icon = {
                GateResult.PASSED: "✅",
                GateResult.FAILED: "❌",
                GateResult.PENDING: "⏳",
                GateResult.SKIPPED: "⏭️"
            }.get(gate.result, "❓")

            lines.append(f"{status_icon} {gate.gate_name}")
            if gate.score is not None:
                lines.append(f"   Score: {gate.score:.1f}% (threshold: {gate.threshold:.1f}%)")
            lines.append(f"   {gate.message}")
            lines.append("")

        lines.append("=" * 60)
        if report.passed:
            lines.append("✅ All quality gates PASSED")
        else:
            lines.append(f"❌ Quality gates FAILED: {', '.join(report.blocking_gates)}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def format_json_output(self, report: CIStatusReport) -> str:
        """
        Format gate results as JSON for programmatic consumption.

        Args:
            report: CI status report

        Returns:
            JSON string
        """
        return json.dumps({
            "platform": report.platform.value,
            "branch": report.branch,
            "commit_sha": report.commit_sha,
            "timestamp": report.timestamp.isoformat(),
            "overall_result": report.overall_result.value,
            "passed": report.passed,
            "blocking_gates": report.blocking_gates,
            "gates": [
                {
                    "name": g.gate_name,
                    "result": g.result.value,
                    "score": g.score,
                    "threshold": g.threshold,
                    "message": g.message,
                    "ci_job": g.ci_job,
                    "blocking": g.details.get('blocking', False) if g.details else False
                }
                for g in report.gates
            ]
        }, indent=2)

    def generate_pr_description_section(self, report: CIStatusReport) -> str:
        """
        Generate quality gate section for PR description.

        Args:
            report: CI status report

        Returns:
            Markdown formatted string for PR description
        """
        lines = []
        lines.append("## Quality Gates")
        lines.append("")

        if report.passed:
            lines.append("✅ **All gates passed**")
        else:
            lines.append(f"❌ **{len(report.blocking_gates)} gate(s) failed**")

        lines.append("")
        lines.append("| Gate | Status | Score | Threshold |")
        lines.append("|------|--------|-------|-----------|")

        for gate in report.gates:
            status_icon = {
                GateResult.PASSED: "✅",
                GateResult.FAILED: "❌",
                GateResult.PENDING: "⏳",
                GateResult.SKIPPED: "⏭️"
            }.get(gate.result, "❓")

            score_str = f"{gate.score:.1f}%" if gate.score is not None else "N/A"
            lines.append(f"| {gate.gate_name} | {status_icon} | {score_str} | {gate.threshold:.1f}% |")

        return "\n".join(lines)

    def update_gate_scores(self, gate_scores: Dict[str, float],
                          sprint_id: Optional[str] = None,
                          track_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Update quality gate scores from CI results.

        Args:
            gate_scores: Dict mapping gate names to scores
            sprint_id: Optional sprint to update
            track_id: Optional track to update

        Returns:
            (success, error) tuple
        """
        try:
            # Find the file to update
            if sprint_id:
                file_path = self.roadmap_root / "sprints" / f"{sprint_id}.yaml"
                key = 'sprint'
            elif track_id:
                file_path = self.roadmap_root / "tracks" / f"{track_id}.yaml"
                key = 'track'
            else:
                return False, "Must specify sprint_id or track_id"

            if not file_path or not file_path.exists():
                return False, f"File not found for {sprint_id or track_id}"

            # Load and update
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            if not data or key not in data:
                return False, f"Invalid file format"

            gates = data[key].get('quality_gates', [])
            updated = False

            for gate in gates:
                gate_name = gate.get('name', '')
                if gate_name in gate_scores:
                    gate['score'] = gate_scores[gate_name]
                    gate['status'] = 'passed' if gate_scores[gate_name] >= gate.get('threshold', 80) else 'failed'
                    updated = True

            if updated:
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return True, None

        except Exception as e:
            return False, str(e)

    def should_block_merge(self, report: CIStatusReport) -> Tuple[bool, str]:
        """
        Determine if merge should be blocked based on gate results.

        Args:
            report: CI status report

        Returns:
            (should_block, reason) tuple
        """
        config = self._load_config()

        if not config.block_merge_on_failure:
            return False, "Merge blocking disabled"

        if report.blocking_gates:
            return True, f"Blocked by failed gates: {', '.join(report.blocking_gates)}"

        return False, "All required gates passed"


# Convenience functions

def check_ci_gates(sprint_id: Optional[str] = None,
                  track_id: Optional[str] = None,
                  repo_path: str = ".") -> CIStatusReport:
    """
    Check quality gates and return CI status report.

    Args:
        sprint_id: Optional sprint to check
        track_id: Optional track to check
        repo_path: Path to repository

    Returns:
        CIStatusReport
    """
    ci = CIIntegration(repo_path)
    return ci.check_gates(sprint_id, track_id)


def format_ci_output(report: CIStatusReport,
                    format_type: str = "auto") -> str:
    """
    Format CI report for output.

    Args:
        report: CI status report
        format_type: 'github', 'gitlab', 'json', or 'auto'

    Returns:
        Formatted string
    """
    ci = CIIntegration()

    if format_type == "auto":
        format_type = {
            CIPlatform.GITHUB_ACTIONS: "github",
            CIPlatform.GITLAB_CI: "gitlab",
        }.get(report.platform, "gitlab")

    if format_type == "github":
        return ci.format_github_annotations(report)
    elif format_type == "json":
        return ci.format_json_output(report)
    else:
        return ci.format_gitlab_ci_output(report)


def get_pr_gate_section(sprint_id: Optional[str] = None,
                       track_id: Optional[str] = None,
                       repo_path: str = ".") -> str:
    """
    Get quality gate section for PR description.

    Args:
        sprint_id: Optional sprint
        track_id: Optional track
        repo_path: Path to repository

    Returns:
        Markdown formatted string
    """
    ci = CIIntegration(repo_path)
    report = ci.check_gates(sprint_id, track_id)
    return ci.generate_pr_description_section(report)
