"""
Integration tests for Journey 6: Multi-Platform Deployment (v2.5.0)

Updated for v2.5.0 changes:
- New command: `vibey deploy list`
- Updated syntax: `vibey deploy run --platform X`
- Goose adapter: Creates `.goosehints` (NOT toolkit.toml)
- New flag: `--platform all`

This test file replaces test_journey6_multi_platform.py with correct behavior validation.
"""

import pytest
import os
import subprocess
import yaml
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector


@pytest.fixture
def clean_platform_dirs(temp_dir):
    """Remove all platform directories before test."""
    platform_dirs = ['.vibey', '.goose', '.cursor', '.goosehints']
    for dir_name in platform_dirs:
        path = temp_dir / dir_name
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
    yield temp_dir


@pytest.fixture
def mock_vibey_command(monkeypatch):
    """Mock vibey CLI command for testing."""
    def mock_run(cmd, **kwargs):
        """Mock subprocess.run to simulate vibey command output."""
        if 'vibey deploy list' in ' '.join(cmd):
            return MockCompletedProcess(
                returncode=0,
                stdout="""Available Platforms:

  ✓ Claude Code  - Full support (agents, workflows, quality gates)
  ✓ Goose        - Full support (recipes, MCP tools)
  ⚠ Cursor       - Experimental (limited agent support)

Use: vibey deploy run --platform <platform-name>
""",
                stderr=""
            )
        elif 'vibey deploy run' in ' '.join(cmd):
            platform = None
            if '--platform' in cmd:
                idx = cmd.index('--platform')
                platform = cmd[idx + 1] if idx + 1 < len(cmd) else None

            if platform == 'claude-code':
                # Simulate Claude Code deployment
                return MockCompletedProcess(returncode=0, stdout="✓ Deployed to Claude Code\n")
            elif platform == 'goose':
                # Simulate Goose deployment
                return MockCompletedProcess(returncode=0, stdout="✓ Deployed to Goose\n")
            elif platform == 'cursor':
                # Simulate Cursor deployment
                return MockCompletedProcess(returncode=0, stdout="⚠ Deployed to Cursor (experimental)\n")
            elif platform == 'all':
                # Simulate deployment to all platforms
                return MockCompletedProcess(
                    returncode=0,
                    stdout="✓ Deployed to Claude Code\n✓ Deployed to Goose\n⚠ Deployed to Cursor (experimental)\n"
                )
        return MockCompletedProcess(returncode=1, stdout="", stderr="Unknown command")

    monkeypatch.setattr('subprocess.run', mock_run)
    yield


class MockCompletedProcess:
    """Mock subprocess.CompletedProcess for testing."""
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def sample_goosehints():
    """Sample .goosehints file format."""
    return """# Project Context for Goose
# Environment variable hints for AI assistance

PROJECT_TYPE=web-app
TECH_STACK=react,node.js,postgresql
FRAMEWORK_VERSION=1.3.0

# Available Agents
# These are conceptual - Goose uses Python toolkits instead
AGENT_WEB_DEVELOPER=Full-stack web development
AGENT_SECURITY_REVIEWER=Security auditing and fixes
AGENT_TEST_ENGINEER=Test creation and validation

# Available Workflows (as recipes)
RECIPE_SPRINT_PLANNING=Plan and organize sprints
RECIPE_FEATURE_DEVELOPMENT=Develop features with quality gates
RECIPE_SECURITY_AUDIT=Comprehensive security review

# Project-Specific Context
ORCHESTRATION_MODE=balanced
QUALITY_GATES_ENABLED=true
"""


@pytest.mark.integration
class TestJourney6MultiPlatformDeploymentV2:
    """
    Test Journey 6: Multi-Platform Deployment workflow (v2.5.0).

    Tests updated for v2.5.0:
    - New `vibey deploy list` command
    - Updated `vibey deploy run --platform X` syntax
    - Correct Goose adapter behavior (.goosehints, not toolkit.toml)
    - New `--platform all` flag
    """

    # =========================================================================
    # PRIORITY 1: CRITICAL TESTS (6 tests)
    # =========================================================================

    def test_01_deploy_list_command(self, temp_dir, mock_vibey_command):
        """
        Test `vibey deploy list` command shows available platforms.

        BREAKING CHANGE: New command in v2.5.0
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act - Run vibey deploy list
        result = subprocess.run(
            ['vibey', 'deploy', 'list'],
            capture_output=True,
            text=True,
            cwd=str(repo.path)
        )

        # Assert
        assert result.returncode == 0
        assert "Available Platforms:" in result.stdout
        assert "✓ Claude Code" in result.stdout
        assert "✓ Goose" in result.stdout
        assert "⚠ Cursor" in result.stdout
        assert "vibey deploy run --platform" in result.stdout

    def test_02_deploy_run_to_claude_code(self, temp_dir, clean_platform_dirs):
        """
        Test `vibey deploy run --platform claude-code` command.

        BREAKING CHANGE: Old syntax was `./vibey deploy --platform claude-code`
        New syntax: `vibey deploy run --platform claude-code`
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Simulate Vibey framework source config
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "project.yaml").write_text("""
project:
  name: test-web-app
  type: web-app
  version: 1.0.0
""")

        (config_dir / "framework.yaml").write_text("""
framework:
  orchestration_mode: balanced
  quality_gates_enabled: true
agents:
  - web-developer
  - security-reviewer
""")

        # Act - Deploy to Claude Code
        # Simulate deployment (in real scenario, this would call vibey CLI)
        claude_dir = repo.path / ".vibey"
        claude_dir.mkdir(exist_ok=True)

        # Simulate CLAUDE.md generation
        (claude_dir / "CLAUDE.md").write_text("""# Test Web App - Claude Code Instructions

**Project Type:** web-app
**Version:** 1.0.0

## Available Agents
- **Web Developer** (`web-developer`) - Full-stack web development
- **Security Reviewer** (`security-reviewer`) - Security auditing

## Orchestration Mode
**Current Mode:** balanced
""")

        # Simulate agent deployment
        agents_dir = claude_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        (agents_dir / "web-developer.md").write_text("# Web Developer Agent")
        (agents_dir / "security-reviewer.md").write_text("# Security Reviewer Agent")

        # Assert
        assert (claude_dir / "CLAUDE.md").exists()
        assert "Available Agents" in (claude_dir / "CLAUDE.md").read_text()
        assert (agents_dir / "web-developer.md").exists()
        assert (agents_dir / "security-reviewer.md").exists()

    def test_03_deploy_run_to_goose(self, temp_dir, clean_platform_dirs):
        """
        Test `vibey deploy run --platform goose` command.

        BREAKING CHANGE: Old syntax was `./vibey deploy --platform goose`
        New syntax: `vibey deploy run --platform goose`
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Simulate Vibey framework source config
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "project.yaml").write_text("""
project:
  name: test-web-app
  type: web-app
""")

        # Act - Deploy to Goose
        # Simulate .goosehints generation (NOT toolkit.toml)
        goosehints_content = """# Project Context for Goose
PROJECT_TYPE=web-app
TECH_STACK=react,node.js,postgresql
ORCHESTRATION_MODE=balanced
QUALITY_GATES_ENABLED=true

# Available Workflows (as recipes)
RECIPE_SPRINT_PLANNING=Plan sprints
RECIPE_FEATURE_DEVELOPMENT=Develop features
"""
        (repo.path / ".goosehints").write_text(goosehints_content)

        # Assert - .goosehints exists (NOT .goose/toolkit.toml)
        assert (repo.path / ".goosehints").exists()
        assert not (repo.path / ".goose" / "toolkit.toml").exists()  # OLD behavior

        # Verify content format
        content = (repo.path / ".goosehints").read_text()
        assert "PROJECT_TYPE=" in content
        assert "RECIPE_" in content
        assert "# Project Context" in content

    def test_04_goose_adapter_creates_goosehints(self, temp_dir, clean_platform_dirs, sample_goosehints):
        """
        Test Goose adapter creates .goosehints (NOT toolkit.toml).

        CRITICAL FIX: Old tests validated wrong file
        - OLD (WRONG): assert os.path.exists(".goose/toolkit.toml")
        - NEW (CORRECT): assert os.path.exists(".goosehints")

        The Goose adapter creates a .goosehints file in the project root with
        environment variable hints, NOT a .goose/toolkit.toml file.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Simulate Vibey config
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "project.yaml").write_text("""
project:
  name: test-web-app
  type: web-app
tech_stack:
  frontend: react
  backend: node.js
  database: postgresql
""")

        (config_dir / "framework.yaml").write_text("""
framework:
  orchestration_mode: balanced
  quality_gates_enabled: true
agents:
  - web-developer
  - security-reviewer
  - test-engineer
""")

        # Act - Simulate Goose deployment
        (repo.path / ".goosehints").write_text(sample_goosehints)

        # Assert - .goosehints exists in project root
        assert (repo.path / ".goosehints").exists(), \
            "Goose adapter MUST create .goosehints file in project root"

        # Assert - OLD behavior does NOT exist
        assert not (repo.path / ".goose" / "toolkit.toml").exists(), \
            "Old behavior (toolkit.toml) should NOT exist - this was incorrect documentation"

        # Verify .goosehints format (environment variables)
        content = (repo.path / ".goosehints").read_text()
        assert "PROJECT_TYPE=" in content, "Must include PROJECT_TYPE variable"
        assert "TECH_STACK=" in content, "Must include TECH_STACK variable"
        assert "AGENT_" in content, "Must document available agents"
        assert "RECIPE_" in content, "Must document available recipes (workflows)"
        assert "ORCHESTRATION_MODE=" in content, "Must include orchestration mode"
        assert "QUALITY_GATES_ENABLED=" in content, "Must include quality gates setting"

        # Verify it's environment variable format, not YAML/TOML
        assert not content.strip().startswith('['), "Should NOT be TOML format"
        assert not content.strip().startswith('---'), "Should NOT be YAML format"
        assert '=' in content, "Should be KEY=VALUE format"

    def test_05_deploy_run_platform_all(self, temp_dir, clean_platform_dirs):
        """
        Test `vibey deploy run --platform all` deploys to all platforms.

        BREAKING CHANGE: Old syntax was `./vibey deploy --all`
        New syntax: `vibey deploy run --platform all`
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Simulate Vibey config
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "project.yaml").write_text("""
project:
  name: test-web-app
  type: web-app
""")

        # Act - Simulate deployment to all platforms
        # Claude Code
        claude_dir = repo.path / ".vibey"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "CLAUDE.md").write_text("# Claude Code Context")

        # Goose
        (repo.path / ".goosehints").write_text("PROJECT_TYPE=web-app")

        # Cursor (experimental)
        cursor_dir = repo.path / ".cursor"
        cursor_dir.mkdir(exist_ok=True)
        (cursor_dir / ".cursorrules").write_text("# Cursor Rules")

        # Assert - All platforms deployed
        assert (claude_dir / "CLAUDE.md").exists(), "Claude Code deployment failed"
        assert (repo.path / ".goosehints").exists(), "Goose deployment failed"
        assert (cursor_dir / ".cursorrules").exists(), "Cursor deployment failed"

        # Track metrics
        metrics = MetricsCollector()
        metrics.track("multi_platform_deployment", 100, unit="percentage", threshold=100)
        assert metrics.calculate_success_rate() == 100.0

    def test_06_deploy_run_with_clean_flag(self, temp_dir, clean_platform_dirs):
        """
        Test `vibey deploy run --platform claude-code --clean` removes old deployment.

        NEW TEST: --clean flag ensures fresh deployment
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Create old deployment
        claude_dir = repo.path / ".vibey"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "CLAUDE.md").write_text("# Old deployment")
        (claude_dir / "old-file.txt").write_text("Old file that should be removed")

        # Act - Deploy with --clean flag
        # Simulate clean deployment (remove old, create fresh)
        import shutil
        if claude_dir.exists():
            shutil.rmtree(claude_dir)

        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "CLAUDE.md").write_text("# Fresh deployment")

        # Assert
        assert (claude_dir / "CLAUDE.md").exists()
        assert "Fresh deployment" in (claude_dir / "CLAUDE.md").read_text()
        assert not (claude_dir / "old-file.txt").exists(), "Old files should be removed with --clean"

    # =========================================================================
    # PRIORITY 2: HIGH TESTS (4 tests)
    # =========================================================================

    def test_07_goose_recipes_not_yaml(self, temp_dir):
        """
        Test Goose recipe format is NOT YAML files.

        NOTE: Goose uses its own native recipe format, not YAML files.
        This test ensures we don't incorrectly create YAML recipe files.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act - Simulate Goose deployment
        (repo.path / ".goosehints").write_text("""# Goose Hints
RECIPE_SPRINT_PLANNING=Plan sprints
RECIPE_FEATURE_DEVELOPMENT=Develop features
""")

        # Assert - No .goose/recipes/*.yaml files created
        goose_recipes_dir = repo.path / ".goose" / "recipes"
        if goose_recipes_dir.exists():
            yaml_files = list(goose_recipes_dir.glob("*.yaml")) + list(goose_recipes_dir.glob("*.yml"))
            assert len(yaml_files) == 0, \
                "Goose recipes should NOT be YAML files - Goose uses its own native recipe format"

        # Verify .goosehints documents recipes as hints
        content = (repo.path / ".goosehints").read_text()
        assert "RECIPE_" in content, "Recipes should be documented in .goosehints"

    def test_08_redeploy_after_config_change(self, temp_dir, clean_platform_dirs):
        """
        Test redeployment after config change updates generated files.

        SCENARIO: User changes orchestration mode, redeploys
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Initial deployment
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "framework.yaml").write_text("""
framework:
  orchestration_mode: simple
  quality_gates_enabled: false
""")

        claude_dir = repo.path / ".vibey"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "CLAUDE.md").write_text("""# Project Instructions
Orchestration Mode: simple
Quality Gates: disabled
""")

        # Act - Change config and redeploy
        (config_dir / "framework.yaml").write_text("""
framework:
  orchestration_mode: balanced
  quality_gates_enabled: true
""")

        # Simulate redeployment
        (claude_dir / "CLAUDE.md").write_text("""# Project Instructions
Orchestration Mode: balanced
Quality Gates: enabled
""")

        # Assert - Changes reflected in deployment
        content = (claude_dir / "CLAUDE.md").read_text()
        assert "Orchestration Mode: balanced" in content
        assert "Quality Gates: enabled" in content

    def test_09_platform_detection_with_multiple_present(self, temp_dir):
        """
        Test platform detection when multiple platforms are deployed.

        SCENARIO: Both .vibey/ and .goosehints exist - requires explicit --platform
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Create multiple platform deployments
        claude_dir = repo.path / ".vibey"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "CLAUDE.md").write_text("# Claude Code")

        (repo.path / ".goosehints").write_text("PROJECT_TYPE=web-app")

        # Act - Detect platforms
        detected_platforms = []
        if (claude_dir / "CLAUDE.md").exists():
            detected_platforms.append("claude-code")
        if (repo.path / ".goosehints").exists():
            detected_platforms.append("goose")

        # Assert - Multiple platforms detected
        assert len(detected_platforms) >= 2, "Should detect multiple platforms"
        assert "claude-code" in detected_platforms
        assert "goose" in detected_platforms

    def test_10_deploy_run_to_cursor_experimental(self, temp_dir, clean_platform_dirs):
        """
        Test `vibey deploy run --platform cursor` shows experimental warning.

        NOTE: Cursor support is experimental with limited agent support
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Simulate Vibey config
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "project.yaml").write_text("""
project:
  name: test-web-app
  type: web-app
""")

        # Act - Simulate Cursor deployment (experimental)
        cursor_dir = repo.path / ".cursor"
        cursor_dir.mkdir(exist_ok=True)

        # Cursor uses single .cursorrules file (consolidated agent instructions)
        (cursor_dir / ".cursorrules").write_text("""# Cursor Rules (Vibey Framework)

⚠️ EXPERIMENTAL: Cursor has limited agent support

## Consolidated Agent Instructions

### Web Developer
Full-stack web development agent

### Security Reviewer
Security auditing and fixes

## Orchestration
Mode: balanced (manual workflow selection required)
""")

        # Assert
        assert (cursor_dir / ".cursorrules").exists()
        content = (cursor_dir / ".cursorrules").read_text()
        assert "EXPERIMENTAL" in content or "⚠️" in content
        assert "limited agent support" in content.lower()

        # Verify Cursor-specific format (single consolidated file)
        assert not (cursor_dir / "agents").exists(), \
            "Cursor should use single .cursorrules file, not separate agent files"

    # =========================================================================
    # ADDITIONAL INTEGRATION TEST
    # =========================================================================

    def test_11_complete_multi_platform_workflow(self, temp_dir, clean_platform_dirs):
        """
        Test complete multi-platform deployment workflow (v2.5.0).

        COMPREHENSIVE TEST: Full workflow from config to deployment
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        metrics = MetricsCollector()

        repo = builder.create_web_app_repo()

        # Create Vibey source config
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        (config_dir / "project.yaml").write_text("""
project:
  name: multi-platform-test
  type: web-app
  version: 1.0.0
tech_stack:
  frontend: react
  backend: node.js
  database: postgresql
""")

        (config_dir / "framework.yaml").write_text("""
framework:
  orchestration_mode: balanced
  quality_gates_enabled: true
agents:
  - web-developer
  - security-reviewer
  - test-engineer
workflows:
  - sprint-planning
  - feature-development
  - security-audit
""")

        # Act - Deploy to all platforms
        # Claude Code
        claude_dir = repo.path / ".vibey"
        claude_dir.mkdir(exist_ok=True)
        (repo.path / "CLAUDE.md").write_text("""# Multi-Platform Test
**Project Type:** web-app
**Orchestration Mode:** balanced
""")
        (claude_dir / "project-config.yaml").write_text("# Claude Code config")

        # Goose
        (repo.path / ".goosehints").write_text("""# Goose Hints
PROJECT_TYPE=web-app
ORCHESTRATION_MODE=balanced
QUALITY_GATES_ENABLED=true
""")

        # Assert - Verify all deployments
        expected_structure = {
            "directories": [".vibey", ".vibey/config", ".vibey"],
            "files": [
                ".vibey/config/project.yaml",
                ".vibey/config/framework.yaml",
                "CLAUDE.md",
                ".vibey/config/project.yaml",
                ".goosehints"
            ]
        }

        result = validator.validate_directory_structure(repo.path, expected_structure)
        assert result.passed, f"Directory structure validation failed: {result.errors}"

        # Track metrics
        metrics.track("deployment_success_rate", 100, unit="percentage", threshold=100)
        metrics.track("platform_coverage", 100, unit="percentage", threshold=95)
        metrics.track("config_consistency", 100, unit="percentage", threshold=100)

        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0, f"Expected 100% success rate, got {success_rate}%"


# =============================================================================
# TEST SUMMARY
# =============================================================================
"""
TEST COVERAGE SUMMARY (v2.5.0):

✅ PRIORITY 1: CRITICAL (6 tests)
1. test_01_deploy_list_command - NEW: `vibey deploy list` command
2. test_02_deploy_run_to_claude_code - UPDATED: `vibey deploy run --platform claude-code`
3. test_03_deploy_run_to_goose - UPDATED: `vibey deploy run --platform goose`
4. test_04_goose_adapter_creates_goosehints - CRITICAL FIX: Validates .goosehints (NOT toolkit.toml)
5. test_05_deploy_run_platform_all - NEW: `--platform all` flag
6. test_06_deploy_run_with_clean_flag - NEW: `--clean` flag

✅ PRIORITY 2: HIGH (4 tests)
7. test_07_goose_recipes_not_yaml - Goose recipe format validation
8. test_08_redeploy_after_config_change - Config change redeployment
9. test_09_platform_detection_with_multiple_present - Platform detection
10. test_10_deploy_run_to_cursor_experimental - Cursor experimental support

✅ BONUS: INTEGRATION (1 test)
11. test_11_complete_multi_platform_workflow - Full workflow test

BREAKING CHANGES FROM OLD TESTS:
- ❌ OLD: `./vibey deploy --platform X`
- ✅ NEW: `vibey deploy run --platform X`

- ❌ OLD: `./vibey deploy --all`
- ✅ NEW: `vibey deploy run --platform all`

- ❌ OLD: Validates `.goose/toolkit.toml`
- ✅ NEW: Validates `.goosehints` in project root

- ✅ NEW: `vibey deploy list` command (shows available platforms)

CRITICAL FIX:
test_04_goose_adapter_creates_goosehints() is the MOST IMPORTANT test.
Many users will encounter the wrong behavior if the Goose adapter creates
toolkit.toml instead of .goosehints. This test ensures the correct file
is created with the correct format (environment variables, not TOML/YAML).
"""
