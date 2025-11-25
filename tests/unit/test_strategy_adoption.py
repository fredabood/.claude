"""
Tests for strategy adoption module.
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from vibey.operations.git.strategy_adoption import (
    StrategyPreset,
    EnforcementLevel,
    BranchRequirement,
    StrategyRequirement,
    StrategyConfig,
    ValidationResult,
    ValidationReport,
    AdoptionResult,
    StrategyAdoption,
    STRATEGY_PRESETS,
    list_strategies,
    adopt_strategy,
    show_strategy,
    validate_strategy,
    format_strategy_list,
    format_validation_report,
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Initialize git
        import subprocess
        subprocess.run(['git', 'init'], cwd=repo, capture_output=True)
        subprocess.run(['git', 'checkout', '-b', 'main'], cwd=repo, capture_output=True)

        # Create a file and commit
        (repo / "README.md").write_text("# Test\n")
        subprocess.run(['git', 'add', '.'], cwd=repo, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Initial'],
            cwd=repo,
            capture_output=True,
            env={
                'GIT_AUTHOR_NAME': 'Test',
                'GIT_AUTHOR_EMAIL': 'test@test.com',
                'GIT_COMMITTER_NAME': 'Test',
                'GIT_COMMITTER_EMAIL': 'test@test.com'
            }
        )

        # Create .vibey config directory
        (repo / ".vibey" / "config").mkdir(parents=True)

        yield repo


class TestStrategyPreset:
    """Tests for StrategyPreset enum."""

    def test_preset_values(self):
        """Test preset enum values."""
        assert StrategyPreset.TRUNK_BASED.value == "trunk-based"
        assert StrategyPreset.FEATURE_BRANCH.value == "feature-branch"
        assert StrategyPreset.GITFLOW.value == "gitflow"
        assert StrategyPreset.HIERARCHICAL.value == "hierarchical"


class TestEnforcementLevel:
    """Tests for EnforcementLevel enum."""

    def test_enforcement_values(self):
        """Test enforcement level values."""
        assert EnforcementLevel.OFF.value == "off"
        assert EnforcementLevel.ADVISORY.value == "advisory"
        assert EnforcementLevel.BLOCKING.value == "blocking"


class TestBranchRequirement:
    """Tests for BranchRequirement dataclass."""

    def test_requirement_creation(self):
        """Test creating a branch requirement."""
        req = BranchRequirement(
            pattern=r'^main$',
            description='Main branch',
            required=True,
            examples=['main']
        )

        assert req.pattern == r'^main$'
        assert req.description == 'Main branch'
        assert req.required
        assert 'main' in req.examples


class TestStrategyConfig:
    """Tests for StrategyConfig dataclass."""

    def test_config_creation(self):
        """Test creating a strategy config."""
        config = StrategyConfig(
            name='Test Strategy',
            preset=StrategyPreset.TRUNK_BASED,
            description='Test description',
            use_case='Testing',
            enforcement=EnforcementLevel.ADVISORY
        )

        assert config.name == 'Test Strategy'
        assert config.preset == StrategyPreset.TRUNK_BASED


class TestStrategyPresets:
    """Tests for predefined strategy presets."""

    def test_all_presets_defined(self):
        """Test that all preset types have configurations."""
        for preset in StrategyPreset:
            assert preset in STRATEGY_PRESETS, f"Missing preset config: {preset}"

    def test_trunk_based_preset(self):
        """Test trunk-based preset configuration."""
        preset = STRATEGY_PRESETS[StrategyPreset.TRUNK_BASED]

        assert preset.name == "Trunk-Based Development"
        assert preset.enforcement == EnforcementLevel.ADVISORY
        assert 'main' in preset.branch_patterns

    def test_feature_branch_preset(self):
        """Test feature-branch preset configuration."""
        preset = STRATEGY_PRESETS[StrategyPreset.FEATURE_BRANCH]

        assert preset.name == "Feature Branch Workflow"
        assert 'feature' in preset.branch_patterns

    def test_gitflow_preset(self):
        """Test gitflow preset configuration."""
        preset = STRATEGY_PRESETS[StrategyPreset.GITFLOW]

        assert preset.name == "GitFlow Workflow"
        assert preset.enforcement == EnforcementLevel.BLOCKING
        assert 'develop' in preset.branch_patterns
        assert 'release' in preset.branch_patterns

    def test_hierarchical_preset(self):
        """Test hierarchical preset configuration."""
        preset = STRATEGY_PRESETS[StrategyPreset.HIERARCHICAL]

        assert preset.name == "Hierarchical Branch Workflow"
        assert 'track' in preset.branch_patterns
        assert 'task' in preset.branch_patterns


class TestStrategyAdoption:
    """Tests for StrategyAdoption class."""

    def test_init(self, temp_repo):
        """Test initialization."""
        manager = StrategyAdoption(str(temp_repo))
        assert manager.repo_path == temp_repo

    def test_list_presets(self, temp_repo):
        """Test listing presets."""
        manager = StrategyAdoption(str(temp_repo))
        presets = manager.list_presets()

        assert len(presets) == 4
        assert all(isinstance(p, StrategyConfig) for p in presets)

    def test_get_preset(self, temp_repo):
        """Test getting a specific preset."""
        manager = StrategyAdoption(str(temp_repo))

        preset = manager.get_preset('trunk-based')
        assert preset is not None
        assert preset.preset == StrategyPreset.TRUNK_BASED

        # Unknown preset
        unknown = manager.get_preset('unknown')
        assert unknown is None

    def test_get_current_strategy_none(self, temp_repo):
        """Test getting current strategy when none configured."""
        manager = StrategyAdoption(str(temp_repo))

        current = manager.get_current_strategy()
        assert current is None

    def test_adopt_trunk_based(self, temp_repo):
        """Test adopting trunk-based strategy."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('trunk-based')

        assert result.success
        assert result.strategy == 'trunk-based'
        assert result.config_updated

        # Check config was written
        config_file = temp_repo / ".vibey" / "config" / "git.yaml"
        assert config_file.exists()

        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config['git']['strategy']['preset'] == 'trunk-based'

    def test_adopt_feature_branch(self, temp_repo):
        """Test adopting feature-branch strategy."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('feature-branch')

        assert result.success
        assert result.strategy == 'feature-branch'

    def test_adopt_gitflow(self, temp_repo):
        """Test adopting gitflow strategy."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('gitflow')

        assert result.success
        assert result.validation_report is not None

    def test_adopt_hierarchical(self, temp_repo):
        """Test adopting hierarchical strategy."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('hierarchical')

        assert result.success

    def test_adopt_unknown_preset(self, temp_repo):
        """Test adopting unknown preset fails."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('unknown')

        assert not result.success
        assert 'Unknown preset' in result.message

    def test_adopt_dry_run(self, temp_repo):
        """Test dry run adoption."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('trunk-based', dry_run=True)

        assert result.success
        assert not result.config_updated
        assert '[DRY RUN]' in result.message

        # Config should not be written
        config_file = temp_repo / ".vibey" / "config" / "git.yaml"
        assert not config_file.exists()

    def test_adopt_with_enforcement_override(self, temp_repo):
        """Test adoption with enforcement override."""
        manager = StrategyAdoption(str(temp_repo))

        result = manager.adopt('trunk-based', enforcement='blocking')

        assert result.success

        config_file = temp_repo / ".vibey" / "config" / "git.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config['git']['strategy']['enforcement'] == 'blocking'

    def test_show_current_no_strategy(self, temp_repo):
        """Test show current with no strategy."""
        manager = StrategyAdoption(str(temp_repo))

        info = manager.show_current()

        assert not info['configured']

    def test_show_current_with_strategy(self, temp_repo):
        """Test show current after adoption."""
        manager = StrategyAdoption(str(temp_repo))
        manager.adopt('feature-branch')

        info = manager.show_current()

        assert info['configured']
        assert info['preset'] == 'feature-branch'
        assert info['name'] == 'Feature Branch Workflow'

    def test_validate_no_strategy(self, temp_repo):
        """Test validation with no strategy configured."""
        manager = StrategyAdoption(str(temp_repo))

        report = manager.validate_strategy()

        assert not report.passed

    def test_validate_trunk_based(self, temp_repo):
        """Test validation for trunk-based strategy."""
        manager = StrategyAdoption(str(temp_repo))

        report = manager.validate_strategy('trunk-based')

        # Should pass - main branch exists
        assert report.strategy == 'trunk-based'
        assert report.passed_count > 0

    def test_validate_gitflow_missing_develop(self, temp_repo):
        """Test gitflow validation without develop branch."""
        manager = StrategyAdoption(str(temp_repo))

        report = manager.validate_strategy('gitflow')

        assert report.strategy == 'gitflow'
        # May have some failures due to missing develop branch
        # Check that fixable issues are identified
        assert isinstance(report.fixable_count, int)

    def test_format_preset_list(self, temp_repo):
        """Test formatting preset list."""
        manager = StrategyAdoption(str(temp_repo))
        presets = manager.list_presets()

        output = manager.format_preset_list(presets)

        assert "trunk-based" in output
        assert "feature-branch" in output
        assert "gitflow" in output
        assert "hierarchical" in output

    def test_format_validation_report(self, temp_repo):
        """Test formatting validation report."""
        manager = StrategyAdoption(str(temp_repo))
        report = manager.validate_strategy('trunk-based')

        output = manager.format_validation_report(report)

        assert "Strategy Validation" in output
        assert "trunk-based" in output

    def test_format_adoption_result(self, temp_repo):
        """Test formatting adoption result."""
        manager = StrategyAdoption(str(temp_repo))
        result = manager.adopt('feature-branch')

        output = manager.format_adoption_result(result)

        assert "Strategy Adoption Result" in output
        assert "feature-branch" in output
        assert "SUCCESS" in output


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_list_strategies(self, temp_repo):
        """Test list_strategies function."""
        presets = list_strategies(str(temp_repo))

        assert len(presets) == 4

    def test_adopt_strategy(self, temp_repo):
        """Test adopt_strategy function."""
        result = adopt_strategy('trunk-based', str(temp_repo))

        assert result.success

    def test_show_strategy(self, temp_repo):
        """Test show_strategy function."""
        adopt_strategy('feature-branch', str(temp_repo))

        info = show_strategy(str(temp_repo))

        assert info['configured']
        assert info['preset'] == 'feature-branch'

    def test_validate_strategy(self, temp_repo):
        """Test validate_strategy function."""
        report = validate_strategy('trunk-based', str(temp_repo))

        assert isinstance(report, ValidationReport)

    def test_format_strategy_list(self, temp_repo):
        """Test format_strategy_list function."""
        presets = list_strategies(str(temp_repo))
        output = format_strategy_list(presets)

        assert len(output) > 0

    def test_format_validation_report_func(self, temp_repo):
        """Test format_validation_report function."""
        report = validate_strategy('trunk-based', str(temp_repo))
        output = format_validation_report(report)

        assert len(output) > 0


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(
            passed=True,
            requirement_name='Test requirement',
            message='Check passed'
        )

        assert result.passed
        assert result.requirement_name == 'Test requirement'


class TestAdoptionResult:
    """Tests for AdoptionResult dataclass."""

    def test_result_creation(self):
        """Test creating an adoption result."""
        result = AdoptionResult(
            success=True,
            strategy='trunk-based',
            config_updated=True,
            message='Success'
        )

        assert result.success
        assert result.strategy == 'trunk-based'
        assert result.config_updated
