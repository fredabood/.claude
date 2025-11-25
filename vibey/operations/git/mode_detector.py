"""
Source-of-truth mode detection and strategy enforcement.

This module determines which mode is active (yaml-only, hybrid, git-primary)
and validates that strategy requirements are met.

MODE DETECTION LOGIC:
1. Check if Git repo exists → yaml-only if not
2. Check strategy.enforce → hybrid if false
3. Check allow_git_primary + requirements → git if all true
4. Default: hybrid

MODES:
- yaml-only: YAML files are source of truth, no git integration
- hybrid: YAML primary, git provides supplementary data
- git-primary: Git is source of truth, YAML derived from git
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import yaml


class SourceOfTruthMode(Enum):
    """Source of truth modes for roadmap management."""
    YAML_ONLY = "yaml-only"
    HYBRID = "hybrid"
    GIT_PRIMARY = "git-primary"


@dataclass
class ModeDetectionResult:
    """Result of mode detection."""
    mode: SourceOfTruthMode
    reason: str
    requirements_met: Dict[str, bool]
    warnings: List[str]


@dataclass
class StrategyValidation:
    """Result of strategy validation."""
    valid: bool
    mode: SourceOfTruthMode
    violations: List[str]
    warnings: List[str]
    requirements: Dict[str, Any]


class ModeDetector:
    """
    Detect source-of-truth mode and validate strategy requirements.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize mode detector.

        Args:
            repo_path: Path to repository (default: current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.git_dir = self.repo_path / ".git"
        self.config_dir = self.repo_path / ".vibey" / "config"
        self.git_config_file = self.config_dir / "git.yaml"

    def _run_git(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=True,
            text=True
        )

    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        return self.git_dir.exists() and self.git_dir.is_dir()

    def _load_git_config(self) -> Optional[Dict[str, Any]]:
        """
        Load git configuration from .vibey/config/git.yaml.

        Returns:
            Config dict, or None if not found
        """
        if not self.git_config_file.exists():
            return None

        try:
            with open(self.git_config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _check_git_primary_requirements(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, bool]]:
        """
        Check if git-primary mode requirements are met.

        Args:
            config: Git configuration dict

        Returns:
            (all_met, requirements_dict)
        """
        requirements = {}

        # Check if git-primary is allowed
        strategy = config.get('strategy', {})
        allow_git_primary = strategy.get('allow_git_primary', False)
        requirements['allow_git_primary'] = allow_git_primary

        if not allow_git_primary:
            return False, requirements

        # Check for required branches
        required_branches = strategy.get('required_branches', [])
        if required_branches:
            for branch in required_branches:
                result = self._run_git("rev-parse", "--verify", branch, check=False)
                branch_exists = result.returncode == 0
                requirements[f'branch:{branch}'] = branch_exists
                if not branch_exists:
                    return False, requirements

        # Check for required tags pattern
        required_tags = strategy.get('required_tags', [])
        if required_tags:
            # Get all tags
            result = self._run_git("tag", "-l", check=False)
            all_tags = result.stdout.splitlines() if result.returncode == 0 else []

            for tag_pattern in required_tags:
                # Simple pattern matching (e.g., "sprint/*/start")
                matching_tags = [t for t in all_tags if tag_pattern.replace('*', '') in t]
                has_matching = len(matching_tags) > 0
                requirements[f'tag_pattern:{tag_pattern}'] = has_matching
                if not has_matching:
                    return False, requirements

        # All requirements met
        return True, requirements

    def detect_mode(self) -> ModeDetectionResult:
        """
        Detect current source-of-truth mode.

        Returns:
            ModeDetectionResult with mode and reasoning
        """
        warnings = []
        requirements = {}

        # Step 1: Check if git repo exists
        if not self._is_git_repo():
            return ModeDetectionResult(
                mode=SourceOfTruthMode.YAML_ONLY,
                reason="Not a git repository",
                requirements_met=requirements,
                warnings=warnings
            )

        requirements['git_repo'] = True

        # Step 2: Load config
        config = self._load_git_config()
        if not config:
            warnings.append("Git config not found at .vibey/config/git.yaml, using defaults")
            return ModeDetectionResult(
                mode=SourceOfTruthMode.HYBRID,
                reason="Default mode (no git.yaml config found)",
                requirements_met=requirements,
                warnings=warnings
            )

        # Step 3: Check strategy.enforce
        strategy = config.get('strategy', {})
        enforce = strategy.get('enforce', True)
        requirements['strategy.enforce'] = enforce

        if not enforce:
            return ModeDetectionResult(
                mode=SourceOfTruthMode.HYBRID,
                reason="strategy.enforce is false",
                requirements_met=requirements,
                warnings=warnings
            )

        # Step 4: Check git-primary requirements
        git_primary_met, git_reqs = self._check_git_primary_requirements(config)
        requirements.update(git_reqs)

        if git_primary_met:
            return ModeDetectionResult(
                mode=SourceOfTruthMode.GIT_PRIMARY,
                reason="All git-primary requirements met",
                requirements_met=requirements,
                warnings=warnings
            )

        # Step 5: Default to hybrid
        return ModeDetectionResult(
            mode=SourceOfTruthMode.HYBRID,
            reason="Git repo exists and strategy enforced, but git-primary requirements not met",
            requirements_met=requirements,
            warnings=warnings
        )

    def validate_strategy(self) -> StrategyValidation:
        """
        Validate strategy requirements for current mode.

        Returns:
            StrategyValidation with violations and warnings
        """
        violations = []
        warnings = []

        # Detect mode
        detection = self.detect_mode()
        mode = detection.mode

        # Load config
        config = self._load_git_config()
        if not config:
            if mode != SourceOfTruthMode.YAML_ONLY:
                warnings.append("No git.yaml config found, cannot validate strategy")
            return StrategyValidation(
                valid=True,
                mode=mode,
                violations=violations,
                warnings=warnings,
                requirements={}
            )

        strategy = config.get('strategy', {})

        # Validate branch naming conventions
        branch_conventions = strategy.get('branch_naming', {})
        if branch_conventions:
            task_pattern = branch_conventions.get('task_pattern', 'task/<task-id>')
            sprint_pattern = branch_conventions.get('sprint_pattern', 'sprint/<sprint-id>')
            track_pattern = branch_conventions.get('track_pattern', 'track/<track-id>')

            # Get all branches
            result = self._run_git("branch", "-a", check=False)
            if result.returncode == 0:
                branches = [b.strip().replace('* ', '') for b in result.stdout.splitlines()]

                # Check if any task/sprint/track branches follow convention
                # This is informational, not a hard requirement
                task_branches = [b for b in branches if b.startswith('task/')]
                sprint_branches = [b for b in branches if b.startswith('sprint/')]
                track_branches = [b for b in branches if b.startswith('track/')]

                if task_branches or sprint_branches or track_branches:
                    # Branches exist, conventions are being used
                    pass
                else:
                    if mode == SourceOfTruthMode.GIT_PRIMARY:
                        warnings.append("No branches following naming conventions found")

        # Validate required branches exist
        required_branches = strategy.get('required_branches', [])
        for branch in required_branches:
            result = self._run_git("rev-parse", "--verify", branch, check=False)
            if result.returncode != 0:
                violations.append(f"Required branch '{branch}' does not exist")

        # Validate required tags exist
        required_tags = strategy.get('required_tags', [])
        if required_tags:
            result = self._run_git("tag", "-l", check=False)
            all_tags = result.stdout.splitlines() if result.returncode == 0 else []

            for tag_pattern in required_tags:
                matching_tags = [t for t in all_tags if tag_pattern.replace('*', '') in t]
                if not matching_tags:
                    violations.append(f"No tags matching pattern '{tag_pattern}' found")

        # Validate merge targets
        merge_rules = strategy.get('merge_targets', {})
        if merge_rules:
            hierarchical = merge_rules.get('hierarchical', False)
            if hierarchical:
                # Task branches must merge to sprint branches
                # Sprint branches must merge to track branches
                # Track branches must merge to main
                pass  # Implementation would check actual merge targets

        return StrategyValidation(
            valid=len(violations) == 0,
            mode=mode,
            violations=violations,
            warnings=warnings,
            requirements=detection.requirements_met
        )

    def get_mode_config(self) -> Dict[str, Any]:
        """
        Get configuration for current mode.

        Returns:
            Mode-specific configuration
        """
        detection = self.detect_mode()
        config = self._load_git_config()

        if not config:
            config = {}

        return {
            'mode': detection.mode.value,
            'reason': detection.reason,
            'warnings': detection.warnings,
            'requirements': detection.requirements_met,
            'strategy': config.get('strategy', {}),
            'enforcement': config.get('enforcement', {}),
        }

    def should_enforce_hooks(self) -> bool:
        """
        Check if git hooks should be enforced based on mode.

        Returns:
            True if hooks should be enforced
        """
        detection = self.detect_mode()

        # YAML-only mode: no hooks needed
        if detection.mode == SourceOfTruthMode.YAML_ONLY:
            return False

        # Check enforcement config
        config = self._load_git_config()
        if config:
            enforcement = config.get('enforcement', {})
            mode_setting = enforcement.get('mode', 'advisory')

            # Off mode: don't enforce
            if mode_setting == 'off':
                return False

        # Hybrid and git-primary: enforce hooks
        return True

    def get_enforcement_mode(self) -> str:
        """
        Get enforcement mode for hooks (off, advisory, blocking, audit).

        Returns:
            Enforcement mode string
        """
        config = self._load_git_config()
        if not config:
            return 'advisory'

        enforcement = config.get('enforcement', {})
        return enforcement.get('mode', 'advisory')


def detect_source_of_truth_mode(repo_path: Optional[str] = None) -> SourceOfTruthMode:
    """
    Convenience function to detect source-of-truth mode.

    Args:
        repo_path: Path to repository

    Returns:
        SourceOfTruthMode enum
    """
    detector = ModeDetector(repo_path)
    result = detector.detect_mode()
    return result.mode


def validate_git_strategy(repo_path: Optional[str] = None) -> StrategyValidation:
    """
    Convenience function to validate git strategy.

    Args:
        repo_path: Path to repository

    Returns:
        StrategyValidation result
    """
    detector = ModeDetector(repo_path)
    return detector.validate_strategy()


def get_mode_configuration(repo_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get mode configuration.

    Args:
        repo_path: Path to repository

    Returns:
        Mode configuration dict
    """
    detector = ModeDetector(repo_path)
    return detector.get_mode_config()
