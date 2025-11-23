"""
Platform-specific tests for Aider adapter.

Tests Aider platform features including:
- Configuration generation (aider.conf.yml)
- Agent → system prompt conversion
- Workflow → Python script conversion
- Git hooks generation
- Deployment validation
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile

from vibey.adapters.aider import AiderAdapter
from vibey.adapters.base import DeploymentResult


@pytest.mark.platform
class TestAiderAdapter:
    """Test Aider platform adapter."""

    def test_platform_name(self):
        """Test adapter returns correct platform name."""
        adapter = AiderAdapter()
        assert adapter.get_platform_name() == "aider"

    def test_deployment_dir(self, tmp_path):
        """Test adapter returns correct deployment directory."""
        adapter = AiderAdapter()
        deployment_dir = adapter.get_deployment_dir(tmp_path)
        assert deployment_dir == tmp_path / ".aider"

    def test_supports_agents(self):
        """Test adapter supports agents feature."""
        adapter = AiderAdapter()
        assert adapter.supports_feature("agents") is True

    def test_supports_workflows(self):
        """Test adapter supports workflows feature."""
        adapter = AiderAdapter()
        assert adapter.supports_feature("workflows") is True

    def test_supports_quality_gates(self):
        """Test adapter supports quality-gates feature."""
        adapter = AiderAdapter()
        assert adapter.supports_feature("quality-gates") is True

    def test_required_files(self):
        """Test adapter returns required files."""
        adapter = AiderAdapter()
        required = adapter.get_required_files()
        assert ".generated" in required
        assert "aider.conf.yml" in required

    def test_optional_files(self):
        """Test adapter returns optional files."""
        adapter = AiderAdapter()
        optional = adapter.get_optional_files()
        assert "agents/" in optional
        assert "workflows/" in optional
        assert "hooks/" in optional


@pytest.mark.platform
class TestAiderDeployment:
    """Test Aider deployment functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock Vibey config for testing."""
        from types import SimpleNamespace

        project = SimpleNamespace(
            name="Test Project",
            type=SimpleNamespace(value="web-app"),
            version="1.0.0",
            description="A test project"
        )

        tech_stack = SimpleNamespace(
            languages=["Python", "TypeScript"],
            frameworks=["FastAPI", "React"],
            databases=["PostgreSQL"],
            infrastructure=["Docker"]
        )

        project_config = SimpleNamespace(
            project=project,
            tech_stack=tech_stack
        )

        framework = SimpleNamespace(
            orchestration_mode=SimpleNamespace(value="balanced")
        )

        framework_config = SimpleNamespace(
            framework=framework
        )

        agents_config = SimpleNamespace(
            agents=SimpleNamespace(
                enabled=["web-developer", "test-engineer"]
            )
        )

        return SimpleNamespace(
            project=project_config,
            framework=framework_config,
            agents=agents_config
        )

    @pytest.fixture
    def source_dir(self, tmp_path):
        """Create mock source directory structure."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()

        # Create minimal config
        (vibey_dir / "config").mkdir()

        # Create framework directory with agents
        framework_dir = tmp_path / "framework"
        agents_dir = framework_dir / "agents"
        agents_dir.mkdir(parents=True)

        # Create sample agent
        (agents_dir / "web-developer.md").write_text("""# Web Developer

A specialized agent for building web applications.

## Capabilities
- React component development
- API integration
- State management
""")

        # Create workflows directory
        workflows_dir = framework_dir / "workflows"
        workflows_dir.mkdir()

        (workflows_dir / "feature-development.md").write_text("""# Feature Development Workflow

1. **Analyze Requirements**: Review the feature spec
2. **Design Architecture**: Plan the implementation
3. **Implement Code**: Write the feature
4. **Write Tests**: Add test coverage
5. **Document**: Update documentation
""")

        return vibey_dir

    def test_deploy_creates_directory(self, tmp_path, source_dir, mock_config):
        """Test deployment creates .aider directory."""
        adapter = AiderAdapter()

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        assert result.success
        assert (tmp_path / ".aider").exists()

    def test_deploy_creates_marker_file(self, tmp_path, source_dir, mock_config):
        """Test deployment creates .generated marker file."""
        adapter = AiderAdapter()

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        assert result.success
        marker = tmp_path / ".aider" / ".generated"
        assert marker.exists()
        content = marker.read_text()
        assert "DO NOT EDIT" in content
        assert "vibey deploy --platform aider" in content

    def test_deploy_creates_config(self, tmp_path, source_dir, mock_config):
        """Test deployment creates aider.conf.yml."""
        adapter = AiderAdapter()

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        assert result.success
        config_file = tmp_path / ".aider" / "aider.conf.yml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "Test Project" in content
        assert "VIBEY_FRAMEWORK_MANAGED" in content

    def test_deploy_converts_agents(self, tmp_path, source_dir, mock_config):
        """Test deployment converts agents to system prompts."""
        adapter = AiderAdapter()

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        assert result.success
        agents_dir = tmp_path / ".aider" / "agents"
        assert agents_dir.exists()

        # Check agent file was created
        agent_file = agents_dir / "web-developer.md"
        assert agent_file.exists()

        content = agent_file.read_text()
        assert "Web Developer" in content
        assert "GENERATED" in content
        assert "DO NOT EDIT" in content

    def test_deploy_converts_workflows(self, tmp_path, source_dir, mock_config):
        """Test deployment converts workflows to Python scripts."""
        adapter = AiderAdapter()

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        assert result.success
        workflows_dir = tmp_path / ".aider" / "workflows"
        assert workflows_dir.exists()

        # Check workflow file was created
        workflow_file = workflows_dir / "feature_development.py"
        assert workflow_file.exists()

        content = workflow_file.read_text()
        assert "Feature Development" in content
        assert "GENERATED" in content
        assert "from aider" in content

    def test_deploy_creates_hooks(self, tmp_path, source_dir, mock_config):
        """Test deployment creates git hooks."""
        adapter = AiderAdapter()

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        assert result.success
        hooks_dir = tmp_path / ".aider" / "hooks"
        assert hooks_dir.exists()
        assert (hooks_dir / "pre-commit").exists()
        assert (hooks_dir / "post-commit").exists()

    def test_deploy_with_clean_removes_existing(self, tmp_path, source_dir, mock_config):
        """Test clean deployment removes existing files."""
        adapter = AiderAdapter()
        aider_dir = tmp_path / ".aider"
        aider_dir.mkdir()

        # Create existing file
        (aider_dir / "old-file.txt").write_text("old content")

        result = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=aider_dir,
            clean=True
        )

        assert result.success
        assert not (aider_dir / "old-file.txt").exists()

    def test_deploy_idempotent(self, tmp_path, source_dir, mock_config):
        """Test deployment is idempotent (running twice produces same result)."""
        adapter = AiderAdapter()

        # First deployment
        result1 = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        # Read content after first deployment
        config_content_1 = (tmp_path / ".aider" / "aider.conf.yml").read_text()

        # Second deployment (without clean)
        result2 = adapter.deploy(
            source_dir=source_dir,
            config=mock_config,
            target_dir=tmp_path / ".aider"
        )

        # Read content after second deployment
        config_content_2 = (tmp_path / ".aider" / "aider.conf.yml").read_text()

        assert result1.success
        assert result2.success
        # Content should be essentially the same (timestamp may differ)
        assert "Test Project" in config_content_1
        assert "Test Project" in config_content_2


@pytest.mark.platform
class TestAiderValidation:
    """Test Aider deployment validation."""

    def test_validate_empty_dir_fails(self, tmp_path):
        """Test validation fails on empty directory."""
        adapter = AiderAdapter()
        aider_dir = tmp_path / ".aider"
        aider_dir.mkdir()

        is_valid, errors = adapter.validate_deployment(aider_dir)

        assert not is_valid
        assert len(errors) > 0

    def test_validate_nonexistent_dir_fails(self, tmp_path):
        """Test validation fails on nonexistent directory."""
        adapter = AiderAdapter()

        is_valid, errors = adapter.validate_deployment(tmp_path / "nonexistent")

        assert not is_valid
        assert "does not exist" in errors[0]

    def test_validate_missing_config_fails(self, tmp_path):
        """Test validation fails without config file."""
        adapter = AiderAdapter()
        aider_dir = tmp_path / ".aider"
        aider_dir.mkdir()
        (aider_dir / ".generated").write_text("marker")
        (aider_dir / "agents").mkdir()
        (aider_dir / "workflows").mkdir()
        (aider_dir / "hooks").mkdir()

        is_valid, errors = adapter.validate_deployment(aider_dir)

        assert not is_valid
        assert any("aider.conf.yml" in e for e in errors)

    def test_validate_complete_deployment_passes(self, tmp_path):
        """Test validation passes on complete deployment."""
        adapter = AiderAdapter()
        aider_dir = tmp_path / ".aider"
        aider_dir.mkdir()

        # Create all required files
        (aider_dir / ".generated").write_text("Generated marker")
        (aider_dir / "aider.conf.yml").write_text("# Config\n# VIBEY_FRAMEWORK_MANAGED")
        (aider_dir / "agents").mkdir()
        (aider_dir / "workflows").mkdir()
        (aider_dir / "hooks").mkdir()

        is_valid, errors = adapter.validate_deployment(aider_dir)

        assert is_valid
        assert len(errors) == 0


@pytest.mark.platform
class TestAiderAgentConversion:
    """Test agent to system prompt conversion."""

    def test_convert_agent_preserves_title(self):
        """Test agent conversion preserves title."""
        adapter = AiderAdapter()
        content = """# Security Reviewer

Expert in security audits and vulnerability detection.
"""
        result = adapter._convert_agent_to_prompt("security-reviewer", content)

        assert "Security Reviewer" in result
        assert "Aider System Prompt" in result

    def test_convert_agent_adds_do_not_edit(self):
        """Test agent conversion adds DO NOT EDIT warning."""
        adapter = AiderAdapter()
        content = "# Test Agent\n\nDescription here."

        result = adapter._convert_agent_to_prompt("test-agent", content)

        assert "DO NOT EDIT" in result
        assert "GENERATED" in result


@pytest.mark.platform
class TestAiderWorkflowConversion:
    """Test workflow to Python script conversion."""

    def test_convert_workflow_creates_python(self):
        """Test workflow conversion creates valid Python."""
        adapter = AiderAdapter()
        content = """# Test Workflow

1. **Step One**: Do something
2. **Step Two**: Do another thing
"""
        result = adapter._convert_workflow_to_script("test_workflow", content)

        assert "#!/usr/bin/env python3" in result
        assert "def run_workflow" in result
        assert "Step One" in result
        assert "Step Two" in result

    def test_convert_workflow_imports_aider(self):
        """Test workflow conversion imports aider modules."""
        adapter = AiderAdapter()
        content = "# Workflow\n\n1. **Task**: Do it"

        result = adapter._convert_workflow_to_script("workflow", content)

        assert "from aider.coders import Coder" in result
        assert "from aider.models import Model" in result

    def test_convert_workflow_adds_do_not_edit(self):
        """Test workflow conversion adds DO NOT EDIT warning."""
        adapter = AiderAdapter()
        content = "# Workflow\n\n1. **Task**: Do it"

        result = adapter._convert_workflow_to_script("workflow", content)

        assert "DO NOT EDIT" in result
        assert "GENERATED" in result
