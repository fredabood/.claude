"""
Git strategy preset adoption module.

Provides commands for adopting Git workflow strategy presets:
- trunk-based: No branches, commits on main
- feature-branch: Branch per task, PR-based
- gitflow: Track branches, sprint branches optional
- hierarchical: Full track/sprint/task hierarchy
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class StrategyPreset(Enum):
    """Available Git workflow strategy presets."""
    TRUNK_BASED = "trunk-based"
    FEATURE_BRANCH = "feature-branch"
    GITFLOW = "gitflow"
    HIERARCHICAL = "hierarchical"


class EnforcementLevel(Enum):
    """Enforcement level for strategy requirements."""
    OFF = "off"
    ADVISORY = "advisory"
    BLOCKING = "blocking"


@dataclass
class BranchRequirement:
    """Branch naming requirement for a strategy."""
    pattern: str
    description: str
    required: bool = True
    examples: List[str] = field(default_factory=list)


@dataclass
class StrategyRequirement:
    """A requirement for a Git strategy."""
    name: str
    description: str
    check_type: str  # 'branch_exists', 'branch_pattern', 'no_direct_commits', etc.
    check_config: Dict[str, Any] = field(default_factory=dict)
    required: bool = True
    auto_fixable: bool = False


@dataclass
class StrategyConfig:
    """Complete configuration for a Git strategy preset."""
    name: str
    preset: StrategyPreset
    description: str
    use_case: str
    enforcement: EnforcementLevel
    branch_patterns: Dict[str, BranchRequirement] = field(default_factory=dict)
    requirements: List[StrategyRequirement] = field(default_factory=list)
    hooks_enabled: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of strategy validation."""
    passed: bool
    requirement_name: str
    message: str
    auto_fix_available: bool = False
    fix_command: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for a strategy."""
    strategy: str
    passed: bool
    results: List[ValidationResult] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    fixable_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AdoptionResult:
    """Result of strategy adoption."""
    success: bool
    strategy: str
    config_updated: bool
    message: str
    validation_report: Optional[ValidationReport] = None
    suggested_fixes: List[str] = field(default_factory=list)


# Predefined strategy configurations
STRATEGY_PRESETS: Dict[StrategyPreset, StrategyConfig] = {
    StrategyPreset.TRUNK_BASED: StrategyConfig(
        name="Trunk-Based Development",
        preset=StrategyPreset.TRUNK_BASED,
        description="All commits go directly to main branch. No feature branches. Fast integration.",
        use_case="Small teams, continuous deployment, rapid iteration",
        enforcement=EnforcementLevel.ADVISORY,
        branch_patterns={
            'main': BranchRequirement(
                pattern=r'^main$|^master$',
                description="Main/master branch only",
                examples=['main', 'master']
            )
        },
        requirements=[
            StrategyRequirement(
                name="Main branch exists",
                description="Repository must have a main or master branch",
                check_type="branch_exists",
                check_config={'branches': ['main', 'master']}
            ),
            StrategyRequirement(
                name="No long-lived feature branches",
                description="Feature branches should be short-lived (< 1 day)",
                check_type="branch_age",
                check_config={'max_age_days': 1},
                required=False
            )
        ],
        hooks_enabled=['commit-msg']
    ),

    StrategyPreset.FEATURE_BRANCH: StrategyConfig(
        name="Feature Branch Workflow",
        preset=StrategyPreset.FEATURE_BRANCH,
        description="One branch per task/feature. PRs for code review. Most common workflow.",
        use_case="Most teams, code review required, moderate deployment frequency",
        enforcement=EnforcementLevel.ADVISORY,
        branch_patterns={
            'main': BranchRequirement(
                pattern=r'^main$|^master$',
                description="Main branch for production code",
                examples=['main']
            ),
            'feature': BranchRequirement(
                pattern=r'^feature/[\w-]+-task-\d+$|^feature/[\w-]+$',
                description="Feature branches for tasks",
                examples=['feature/git-integration-3-task-007', 'feature/add-login']
            ),
            'bugfix': BranchRequirement(
                pattern=r'^bugfix/[\w-]+$|^fix/[\w-]+$',
                description="Bug fix branches",
                required=False,
                examples=['bugfix/fix-login-error', 'fix/typo']
            )
        },
        requirements=[
            StrategyRequirement(
                name="Main branch exists",
                description="Repository must have a main branch",
                check_type="branch_exists",
                check_config={'branches': ['main', 'master']}
            ),
            StrategyRequirement(
                name="Feature branches follow naming",
                description="Feature branches should match pattern",
                check_type="branch_pattern",
                check_config={'pattern': r'^feature/'},
                required=False
            ),
            StrategyRequirement(
                name="No direct main commits",
                description="Main branch should only receive merge commits",
                check_type="protected_branch",
                check_config={'branch': 'main'},
                required=False
            )
        ],
        hooks_enabled=['pre-commit', 'commit-msg']
    ),

    StrategyPreset.GITFLOW: StrategyConfig(
        name="GitFlow Workflow",
        preset=StrategyPreset.GITFLOW,
        description="Structured workflow with develop, release, and hotfix branches. Good for releases.",
        use_case="Teams with scheduled releases, need for hotfixes, larger projects",
        enforcement=EnforcementLevel.BLOCKING,
        branch_patterns={
            'main': BranchRequirement(
                pattern=r'^main$|^master$',
                description="Production branch",
                examples=['main']
            ),
            'develop': BranchRequirement(
                pattern=r'^develop$|^dev$',
                description="Development integration branch",
                examples=['develop']
            ),
            'feature': BranchRequirement(
                pattern=r'^feature/[\w-]+$',
                description="Feature development branches",
                examples=['feature/new-feature', 'feature/git-integration']
            ),
            'release': BranchRequirement(
                pattern=r'^release/v?\d+\.\d+(\.\d+)?$',
                description="Release preparation branches",
                required=False,
                examples=['release/v1.0.0', 'release/1.2']
            ),
            'hotfix': BranchRequirement(
                pattern=r'^hotfix/[\w-]+$',
                description="Production hotfix branches",
                required=False,
                examples=['hotfix/critical-bug']
            )
        },
        requirements=[
            StrategyRequirement(
                name="Main branch exists",
                description="Repository must have a main branch",
                check_type="branch_exists",
                check_config={'branches': ['main', 'master']}
            ),
            StrategyRequirement(
                name="Develop branch exists",
                description="Repository must have a develop branch",
                check_type="branch_exists",
                check_config={'branches': ['develop', 'dev']},
                auto_fixable=True
            ),
            StrategyRequirement(
                name="Feature branches from develop",
                description="Feature branches should be created from develop",
                check_type="branch_base",
                check_config={'pattern': r'^feature/', 'base': 'develop'},
                required=False
            )
        ],
        hooks_enabled=['pre-commit', 'commit-msg', 'pre-push']
    ),

    StrategyPreset.HIERARCHICAL: StrategyConfig(
        name="Hierarchical Branch Workflow",
        preset=StrategyPreset.HIERARCHICAL,
        description="Full track/sprint/task branch hierarchy. Maximum traceability.",
        use_case="Enterprise teams, strict audit requirements, complex multi-track projects",
        enforcement=EnforcementLevel.BLOCKING,
        branch_patterns={
            'main': BranchRequirement(
                pattern=r'^main$|^master$',
                description="Production branch",
                examples=['main']
            ),
            'track': BranchRequirement(
                pattern=r'^track/[\w-]+$',
                description="Track-level integration branches",
                examples=['track/git-integration', 'track/user-auth']
            ),
            'sprint': BranchRequirement(
                pattern=r'^sprint/[\w-]+-\d+$',
                description="Sprint-level branches",
                required=False,
                examples=['sprint/git-integration-3']
            ),
            'task': BranchRequirement(
                pattern=r'^feature/[\w-]+-task-\d+$',
                description="Task-level feature branches",
                examples=['feature/git-integration-3-task-007']
            )
        },
        requirements=[
            StrategyRequirement(
                name="Main branch exists",
                description="Repository must have a main branch",
                check_type="branch_exists",
                check_config={'branches': ['main', 'master']}
            ),
            StrategyRequirement(
                name="Track branches for active tracks",
                description="Each active track should have a track branch",
                check_type="track_branches",
                check_config={},
                required=False
            ),
            StrategyRequirement(
                name="Task branches follow naming",
                description="Task branches must include task ID",
                check_type="branch_pattern",
                check_config={'pattern': r'-task-\d+'}
            )
        ],
        hooks_enabled=['pre-commit', 'commit-msg', 'pre-push']
    )
}


class StrategyAdoption:
    """
    Manages Git strategy preset adoption.

    Handles listing, adopting, validating, and showing strategy configurations.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize strategy adoption manager."""
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.config_dir = self.repo_path / ".vibey" / "config"
        self.git_config_file = self.config_dir / "git.yaml"

    def list_presets(self) -> List[StrategyConfig]:
        """List all available strategy presets."""
        return list(STRATEGY_PRESETS.values())

    def get_preset(self, preset_name: str) -> Optional[StrategyConfig]:
        """Get a specific preset by name."""
        try:
            preset = StrategyPreset(preset_name)
            return STRATEGY_PRESETS.get(preset)
        except ValueError:
            return None

    def get_current_strategy(self) -> Optional[str]:
        """Get the currently configured strategy."""
        if not self.git_config_file.exists():
            return None

        try:
            import yaml
            with open(self.git_config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('git', {}).get('strategy', {}).get('preset')
        except Exception:
            return None

    def show_current(self) -> Dict[str, Any]:
        """Show current strategy configuration."""
        current = self.get_current_strategy()
        if not current:
            return {
                'configured': False,
                'message': 'No strategy configured. Run "vibey git strategy adopt <preset>" to configure.'
            }

        preset = self.get_preset(current)
        if not preset:
            return {
                'configured': True,
                'preset': current,
                'message': f'Unknown preset: {current}'
            }

        # Load custom config if present
        config = self._load_config()
        strategy_config = config.get('git', {}).get('strategy', {})

        return {
            'configured': True,
            'preset': current,
            'name': preset.name,
            'description': preset.description,
            'enforcement': strategy_config.get('enforcement', preset.enforcement.value),
            'hooks_enabled': strategy_config.get('hooks_enabled', preset.hooks_enabled),
            'customizations': strategy_config.get('customizations', {})
        }

    def validate_strategy(self, preset_name: Optional[str] = None) -> ValidationReport:
        """Validate current state against strategy requirements."""
        if preset_name:
            preset = self.get_preset(preset_name)
        else:
            current = self.get_current_strategy()
            preset = self.get_preset(current) if current else None

        if not preset:
            return ValidationReport(
                strategy='unknown',
                passed=False,
                results=[ValidationResult(
                    passed=False,
                    requirement_name='Strategy configured',
                    message='No strategy configured or invalid preset'
                )]
            )

        results = []
        for req in preset.requirements:
            result = self._check_requirement(req)
            results.append(result)

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)
        fixable_count = sum(1 for r in results if not r.passed and r.auto_fix_available)

        # Strategy passes if all required checks pass
        required_passed = all(r.passed for r in results if results)

        return ValidationReport(
            strategy=preset.preset.value,
            passed=required_passed,
            results=results,
            passed_count=passed_count,
            failed_count=failed_count,
            fixable_count=fixable_count
        )

    def adopt(
        self,
        preset_name: str,
        enforcement: Optional[str] = None,
        customize: bool = False,
        dry_run: bool = False
    ) -> AdoptionResult:
        """
        Adopt a strategy preset.

        Args:
            preset_name: Name of the preset to adopt
            enforcement: Override enforcement level
            customize: Enable interactive customization
            dry_run: Show what would be done without making changes

        Returns:
            AdoptionResult with success status and details
        """
        preset = self.get_preset(preset_name)
        if not preset:
            return AdoptionResult(
                success=False,
                strategy=preset_name,
                config_updated=False,
                message=f'Unknown preset: {preset_name}. Available: {", ".join(p.value for p in StrategyPreset)}'
            )

        # Build configuration
        config = {
            'git': {
                'strategy': {
                    'preset': preset_name,
                    'enforcement': enforcement if enforcement else preset.enforcement.value,
                    'hooks_enabled': preset.hooks_enabled,
                    'branch_patterns': {
                        name: {
                            'pattern': req.pattern,
                            'description': req.description,
                            'required': req.required,
                            'examples': req.examples
                        }
                        for name, req in preset.branch_patterns.items()
                    }
                }
            }
        }

        if dry_run:
            return AdoptionResult(
                success=True,
                strategy=preset_name,
                config_updated=False,
                message=f'[DRY RUN] Would adopt {preset.name} ({preset_name})',
                suggested_fixes=self._get_suggested_fixes(preset)
            )

        # Write configuration
        try:
            self._save_config(config)
        except Exception as e:
            return AdoptionResult(
                success=False,
                strategy=preset_name,
                config_updated=False,
                message=f'Failed to save configuration: {e}'
            )

        # Validate current state
        validation = self.validate_strategy(preset_name)

        # Get suggested fixes for failures
        suggested_fixes = []
        for result in validation.results:
            if not result.passed and result.fix_command:
                suggested_fixes.append(result.fix_command)

        return AdoptionResult(
            success=True,
            strategy=preset_name,
            config_updated=True,
            message=f'Successfully adopted {preset.name} ({preset_name})',
            validation_report=validation,
            suggested_fixes=suggested_fixes
        )

    def _check_requirement(self, req: StrategyRequirement) -> ValidationResult:
        """Check a single strategy requirement."""
        try:
            if req.check_type == 'branch_exists':
                return self._check_branch_exists(req)
            elif req.check_type == 'branch_pattern':
                return self._check_branch_pattern(req)
            elif req.check_type == 'protected_branch':
                return self._check_protected_branch(req)
            elif req.check_type == 'branch_age':
                return self._check_branch_age(req)
            elif req.check_type == 'track_branches':
                return self._check_track_branches(req)
            elif req.check_type == 'branch_base':
                return self._check_branch_base(req)
            else:
                return ValidationResult(
                    passed=True,
                    requirement_name=req.name,
                    message=f'Unknown check type: {req.check_type}'
                )
        except Exception as e:
            return ValidationResult(
                passed=False,
                requirement_name=req.name,
                message=f'Check failed: {e}'
            )

    def _check_branch_exists(self, req: StrategyRequirement) -> ValidationResult:
        """Check if required branches exist."""
        branches = req.check_config.get('branches', [])
        existing = self._get_local_branches()

        for branch in branches:
            if branch in existing:
                return ValidationResult(
                    passed=True,
                    requirement_name=req.name,
                    message=f'Branch "{branch}" exists'
                )

        return ValidationResult(
            passed=False,
            requirement_name=req.name,
            message=f'None of required branches exist: {", ".join(branches)}',
            auto_fix_available=req.auto_fixable,
            fix_command=f'git checkout -b {branches[0]}' if req.auto_fixable else None
        )

    def _check_branch_pattern(self, req: StrategyRequirement) -> ValidationResult:
        """Check if branches match required pattern."""
        import re
        pattern = req.check_config.get('pattern', '')
        existing = self._get_local_branches()

        # Find branches that should match but don't
        matches = [b for b in existing if re.search(pattern, b)]

        if matches:
            return ValidationResult(
                passed=True,
                requirement_name=req.name,
                message=f'{len(matches)} branches match pattern'
            )

        return ValidationResult(
            passed=False,
            requirement_name=req.name,
            message=f'No branches match pattern: {pattern}'
        )

    def _check_protected_branch(self, req: StrategyRequirement) -> ValidationResult:
        """Check if branch protection is in place (advisory only)."""
        # This is informational - actual protection is at GitHub/GitLab level
        return ValidationResult(
            passed=True,
            requirement_name=req.name,
            message='Branch protection check is advisory - configure at repository hosting level'
        )

    def _check_branch_age(self, req: StrategyRequirement) -> ValidationResult:
        """Check that feature branches are not too old."""
        max_age = req.check_config.get('max_age_days', 7)

        # Get feature branches with age
        try:
            result = subprocess.run(
                ['git', 'for-each-ref', '--sort=-committerdate',
                 '--format=%(refname:short) %(committerdate:relative)',
                 'refs/heads/feature/*'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0 or not result.stdout.strip():
                return ValidationResult(
                    passed=True,
                    requirement_name=req.name,
                    message='No feature branches to check'
                )

            # Check ages (simplified - actual implementation would parse dates)
            branches = result.stdout.strip().split('\n')
            old_branches = [b for b in branches if 'days' in b or 'weeks' in b or 'months' in b]

            if old_branches:
                return ValidationResult(
                    passed=False,
                    requirement_name=req.name,
                    message=f'{len(old_branches)} feature branches may be older than {max_age} days'
                )

            return ValidationResult(
                passed=True,
                requirement_name=req.name,
                message='All feature branches are recent'
            )
        except Exception as e:
            return ValidationResult(
                passed=True,
                requirement_name=req.name,
                message=f'Could not check branch age: {e}'
            )

    def _check_track_branches(self, req: StrategyRequirement) -> ValidationResult:
        """Check that active tracks have corresponding branches."""
        # Check for track branches
        existing = self._get_local_branches()
        track_branches = [b for b in existing if b.startswith('track/')]

        if track_branches:
            return ValidationResult(
                passed=True,
                requirement_name=req.name,
                message=f'{len(track_branches)} track branches exist'
            )

        return ValidationResult(
            passed=False,
            requirement_name=req.name,
            message='No track branches found. Create with: git checkout -b track/<track-name>'
        )

    def _check_branch_base(self, req: StrategyRequirement) -> ValidationResult:
        """Check that branches are based on correct parent."""
        # This is advisory - hard to verify without more git analysis
        return ValidationResult(
            passed=True,
            requirement_name=req.name,
            message='Branch base check is advisory'
        )

    def _get_local_branches(self) -> List[str]:
        """Get list of local branch names."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--format=%(refname:short)'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return [b.strip() for b in result.stdout.strip().split('\n') if b.strip()]
        except Exception:
            pass
        return []

    def _get_suggested_fixes(self, preset: StrategyConfig) -> List[str]:
        """Get suggested fixes for a preset."""
        fixes = []

        if preset.preset == StrategyPreset.GITFLOW:
            fixes.append('git checkout -b develop  # Create develop branch if missing')

        if preset.preset == StrategyPreset.HIERARCHICAL:
            fixes.append('git checkout -b track/<track-name>  # Create track branch')

        return fixes

    def _load_config(self) -> Dict[str, Any]:
        """Load current git configuration."""
        if not self.git_config_file.exists():
            return {}

        try:
            import yaml
            with open(self.git_config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save git configuration."""
        import yaml

        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Merge with existing config
        existing = self._load_config()
        if 'git' in existing:
            existing['git'].update(config.get('git', {}))
        else:
            existing.update(config)

        with open(self.git_config_file, 'w') as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

    def format_preset_list(self, presets: List[StrategyConfig]) -> str:
        """Format preset list for display."""
        lines = ["Available Git Strategy Presets:", "=" * 60, ""]

        for preset in presets:
            lines.append(f"  {preset.preset.value}")
            lines.append(f"    Name: {preset.name}")
            lines.append(f"    {preset.description}")
            lines.append(f"    Use case: {preset.use_case}")
            lines.append(f"    Enforcement: {preset.enforcement.value}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("To adopt: vibey git strategy adopt <preset-name>")

        return "\n".join(lines)

    def format_validation_report(self, report: ValidationReport) -> str:
        """Format validation report for display."""
        status = "PASSED" if report.passed else "FAILED"
        lines = [
            f"Strategy Validation: {report.strategy}",
            "=" * 60,
            f"Status: {status}",
            f"Passed: {report.passed_count} | Failed: {report.failed_count} | Fixable: {report.fixable_count}",
            "",
            "Requirements:",
            "-" * 40,
        ]

        for result in report.results:
            icon = "OK" if result.passed else "X"
            lines.append(f"  [{icon}] {result.requirement_name}")
            lines.append(f"       {result.message}")
            if result.fix_command:
                lines.append(f"       Fix: {result.fix_command}")

        return "\n".join(lines)

    def format_adoption_result(self, result: AdoptionResult) -> str:
        """Format adoption result for display."""
        lines = [
            "Strategy Adoption Result",
            "=" * 60,
            f"Strategy: {result.strategy}",
            f"Status: {'SUCCESS' if result.success else 'FAILED'}",
            f"Message: {result.message}",
        ]

        if result.config_updated:
            lines.append("Configuration: Updated")

        if result.suggested_fixes:
            lines.append("")
            lines.append("Suggested Fixes:")
            for fix in result.suggested_fixes:
                lines.append(f"  $ {fix}")

        if result.validation_report:
            lines.append("")
            lines.append(self.format_validation_report(result.validation_report))

        return "\n".join(lines)


# Convenience functions

def list_strategies(repo_path: Optional[str] = None) -> List[StrategyConfig]:
    """List all available strategy presets."""
    manager = StrategyAdoption(repo_path)
    return manager.list_presets()


def adopt_strategy(
    preset_name: str,
    repo_path: Optional[str] = None,
    enforcement: Optional[str] = None,
    dry_run: bool = False
) -> AdoptionResult:
    """Adopt a strategy preset."""
    manager = StrategyAdoption(repo_path)
    return manager.adopt(preset_name, enforcement=enforcement, dry_run=dry_run)


def show_strategy(repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Show current strategy configuration."""
    manager = StrategyAdoption(repo_path)
    return manager.show_current()


def validate_strategy(
    preset_name: Optional[str] = None,
    repo_path: Optional[str] = None
) -> ValidationReport:
    """Validate strategy requirements."""
    manager = StrategyAdoption(repo_path)
    return manager.validate_strategy(preset_name)


def format_strategy_list(presets: List[StrategyConfig]) -> str:
    """Format preset list for display."""
    manager = StrategyAdoption()
    return manager.format_preset_list(presets)


def format_validation_report(report: ValidationReport) -> str:
    """Format validation report for display."""
    manager = StrategyAdoption()
    return manager.format_validation_report(report)
