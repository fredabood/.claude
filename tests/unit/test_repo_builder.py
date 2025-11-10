"""
Unit tests for RepoBuilder test utility.

Tests the functionality of creating mock repositories for testing.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, TestRepo


@pytest.mark.unit
class TestRepoBuilder:
    """Test RepoBuilder utility."""

    def test_init(self, temp_dir):
        """Test RepoBuilder initialization."""
        builder = RepoBuilder(temp_dir)
        assert builder.base_path == temp_dir
        assert builder.base_path.exists()

    def test_create_web_app_repo(self, temp_dir):
        """Test creating web app repository."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        assert isinstance(repo, TestRepo)
        assert repo.repo_type == "web-app"
        assert repo.path.exists()
        assert not repo.has_git
        assert not repo.has_vibey

    def test_web_app_structure(self, temp_dir):
        """Test web app directory structure."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Check directories
        assert (repo.path / "src").exists()
        assert (repo.path / "src" / "components").exists()
        assert (repo.path / "server").exists()
        assert (repo.path / "tests").exists()

        # Check files
        assert (repo.path / "package.json").exists()
        assert (repo.path / "README.md").exists()
        assert (repo.path / ".gitignore").exists()

    def test_web_app_content(self, temp_dir):
        """Test web app file content."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Check App.jsx contains React
        app_content = (repo.path / "src" / "App.jsx").read_text()
        assert "import React" in app_content
        assert "function App()" in app_content

        # Check server has Express
        server_content = (repo.path / "server" / "index.js").read_text()
        assert "express" in server_content

    def test_create_api_service_repo(self, temp_dir):
        """Test creating API service repository."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()

        assert isinstance(repo, TestRepo)
        assert repo.repo_type == "api-service"
        assert repo.path.exists()

    def test_api_service_structure(self, temp_dir):
        """Test API service directory structure."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()

        # Check directories
        assert (repo.path / "app").exists()
        assert (repo.path / "app" / "routers").exists()
        assert (repo.path / "tests").exists()

        # Check files
        assert (repo.path / "requirements.txt").exists()
        assert (repo.path / "README.md").exists()

    def test_api_service_content(self, temp_dir):
        """Test API service file content."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()

        # Check main.py contains FastAPI
        main_content = (repo.path / "app" / "main.py").read_text()
        assert "FastAPI" in main_content
        assert "app = FastAPI" in main_content

    def test_create_ml_project_repo(self, temp_dir):
        """Test creating ML project repository."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_ml_project_repo()

        assert isinstance(repo, TestRepo)
        assert repo.repo_type == "ml-project"
        assert repo.path.exists()

    def test_ml_project_structure(self, temp_dir):
        """Test ML project directory structure."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_ml_project_repo()

        # Check directories
        assert (repo.path / "notebooks").exists()
        assert (repo.path / "src").exists()
        assert (repo.path / "data").exists()

        # Check files
        assert (repo.path / "requirements.txt").exists()
        assert (repo.path / "README.md").exists()

    def test_ml_project_content(self, temp_dir):
        """Test ML project file content."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_ml_project_repo()

        # Check train.py contains TensorFlow
        train_content = (repo.path / "src" / "train.py").read_text()
        assert "tensorflow" in train_content
        assert "def train_model" in train_content

    def test_add_vibey_framework(self, temp_dir):
        """Test adding Vibey framework to repository."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        assert not repo.has_vibey

        builder.add_vibey_framework(repo)

        assert repo.has_vibey
        assert (repo.path / ".claude").exists()
        assert (repo.path / ".claude" / "CLAUDE.md").exists()
        assert (repo.path / ".claude" / "project-config.yaml").exists()

    def test_vibey_claude_md_content(self, temp_dir):
        """Test CLAUDE.md content after Vibey deployment."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        claude_md = (repo.path / ".claude" / "CLAUDE.md").read_text()
        assert "VIBEY_FRAMEWORK_MANAGED" in claude_md
        assert repo.name in claude_md
        assert repo.repo_type in claude_md

    def test_vibey_config_content(self, temp_dir):
        """Test project-config.yaml content."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo)

        config = (repo.path / ".claude" / "project-config.yaml").read_text()
        assert "project:" in config
        assert "framework:" in config
        assert "orchestration_mode:" in config

    @pytest.mark.requires_git
    def test_init_git(self, temp_dir):
        """Test git initialization."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        assert not repo.has_git

        builder.init_git(repo, initial_commit=True)

        assert repo.has_git
        assert (repo.path / ".git").exists()

    @pytest.mark.requires_git
    def test_git_config(self, temp_dir):
        """Test git configuration."""
        import subprocess

        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo)

        # Check user name
        result = subprocess.run(
            ["git", "config", "user.name"],
            cwd=repo.path,
            capture_output=True,
            text=True
        )
        assert "Test User" in result.stdout

        # Check user email
        result = subprocess.run(
            ["git", "config", "user.email"],
            cwd=repo.path,
            capture_output=True,
            text=True
        )
        assert "test@example.com" in result.stdout

    def test_custom_repo_name(self, temp_dir):
        """Test creating repository with custom name."""
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="my-custom-app")

        assert repo.name == "my-custom-app"
        assert repo.path.name == "my-custom-app"
