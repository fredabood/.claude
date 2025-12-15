"""
Tests for vibey.operations.config.generate module.

Tests config generation operations from templates.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import yaml

from vibey.operations.config.generate import (
    load_template,
    populate_config,
    find_template_directory,
    generate_config,
)


class TestLoadTemplate:
    """Test load_template function."""

    @pytest.fixture
    def template_dir(self, tmp_path):
        """Create a temporary template directory with sample templates."""
        # Create sample template files
        templates = {
            "web-application-fullstack.yaml": {
                "project": {"name": "", "type": "web-app"},
                "technology_stack": {"backend": "", "frontend": "", "database": ""},
            },
            "microservices.yaml": {
                "project": {"name": "", "type": "api"},
                "technology_stack": {"backend": ""},
            },
        }
        for name, content in templates.items():
            with open(tmp_path / name, "w") as f:
                yaml.dump(content, f)
        return tmp_path

    def test_load_web_app_template(self, template_dir):
        """Test loading web-app template."""
        result = load_template("web-app", template_dir)
        assert result["project"]["type"] == "web-app"

    def test_load_api_template(self, template_dir):
        """Test loading api template."""
        result = load_template("api", template_dir)
        assert result["project"]["type"] == "api"

    def test_unknown_project_type_raises_error(self, template_dir):
        """Test unknown project type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            load_template("unknown", template_dir)
        assert "Unknown project type" in str(exc_info.value)
        assert "web-app" in str(exc_info.value)  # Shows valid types

    def test_missing_template_file_raises_error(self, tmp_path):
        """Test missing template file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_template("web-app", tmp_path)
        assert "Template not found" in str(exc_info.value)

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Test invalid YAML raises error."""
        # Create invalid YAML file
        with open(tmp_path / "web-application-fullstack.yaml", "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            load_template("web-app", tmp_path)


class TestPopulateConfig:
    """Test populate_config function."""

    def test_populate_project_name(self):
        """Test populating project name."""
        config = {"project": {"name": "", "created_at": ""}}
        result = populate_config(config, "My Project", "")
        assert result["project"]["name"] == "My Project"
        assert result["project"]["created_at"]  # Should be set

    def test_populate_tech_stack_python(self):
        """Test detecting Python backend."""
        config = {"project": {}, "technology_stack": {"backend": "", "description": ""}}
        result = populate_config(config, "Test", "Python with FastAPI")
        assert result["technology_stack"]["backend"] == "Python"

    def test_populate_tech_stack_node(self):
        """Test detecting Node.js backend."""
        config = {"project": {}, "technology_stack": {"backend": "", "description": ""}}
        result = populate_config(config, "Test", "Node.js Express server")
        assert result["technology_stack"]["backend"] == "Node.js"

    def test_populate_tech_stack_java(self):
        """Test detecting Java backend."""
        config = {"project": {}, "technology_stack": {"backend": "", "description": ""}}
        result = populate_config(config, "Test", "Java Spring Boot")
        assert result["technology_stack"]["backend"] == "Java"

    def test_populate_tech_stack_go(self):
        """Test detecting Go backend."""
        config = {"project": {}, "technology_stack": {"backend": "", "description": ""}}
        result = populate_config(config, "Test", "Go with Gin")
        assert result["technology_stack"]["backend"] == "Go"

    def test_populate_frontend_react(self):
        """Test detecting React frontend."""
        config = {"project": {}, "technology_stack": {"frontend": "", "description": ""}}
        result = populate_config(config, "Test", "React with TypeScript")
        assert result["technology_stack"]["frontend"] == "React"

    def test_populate_frontend_vue(self):
        """Test detecting Vue frontend."""
        config = {"project": {}, "technology_stack": {"frontend": "", "description": ""}}
        result = populate_config(config, "Test", "Vue.js frontend")
        assert result["technology_stack"]["frontend"] == "Vue.js"

    def test_populate_frontend_angular(self):
        """Test detecting Angular frontend."""
        config = {"project": {}, "technology_stack": {"frontend": "", "description": ""}}
        result = populate_config(config, "Test", "Angular application")
        assert result["technology_stack"]["frontend"] == "Angular"

    def test_populate_database_postgres(self):
        """Test detecting PostgreSQL database."""
        config = {"project": {}, "technology_stack": {"database": "", "description": ""}}
        result = populate_config(config, "Test", "PostgreSQL database")
        assert result["technology_stack"]["database"] == "PostgreSQL"

    def test_populate_database_mysql(self):
        """Test detecting MySQL database."""
        config = {"project": {}, "technology_stack": {"database": "", "description": ""}}
        result = populate_config(config, "Test", "MySQL storage")
        assert result["technology_stack"]["database"] == "MySQL"

    def test_populate_database_mongodb(self):
        """Test detecting MongoDB database."""
        config = {"project": {}, "technology_stack": {"database": "", "description": ""}}
        result = populate_config(config, "Test", "MongoDB for data")
        assert result["technology_stack"]["database"] == "MongoDB"

    def test_populate_full_stack(self):
        """Test populating full stack detection."""
        config = {
            "project": {"name": ""},
            "technology_stack": {
                "backend": "",
                "frontend": "",
                "database": "",
                "description": "",
            },
        }
        result = populate_config(
            config, "Full Stack App", "Python FastAPI with React and PostgreSQL"
        )
        assert result["technology_stack"]["backend"] == "Python"
        assert result["technology_stack"]["frontend"] == "React"
        assert result["technology_stack"]["database"] == "PostgreSQL"

    def test_no_tech_stack_section(self):
        """Test config without technology_stack section."""
        config = {"project": {"name": ""}}
        result = populate_config(config, "Test", "Python Django")
        # Should not crash, just skip tech stack population
        assert result["project"]["name"] == "Test"


class TestFindTemplateDirectory:
    """Test find_template_directory function."""

    def test_returns_path_object(self):
        """Test returns Path object."""
        with patch("pathlib.Path.exists", return_value=True):
            result = find_template_directory()
            assert isinstance(result, Path)

    def test_not_found_raises_error(self):
        """Test raises FileNotFoundError when not found."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                find_template_directory()
            assert "Cannot find config templates directory" in str(exc_info.value)


class TestGenerateConfig:
    """Test generate_config function."""

    @pytest.fixture
    def template_dir(self, tmp_path):
        """Create a temporary template directory."""
        template = {
            "project": {"name": "", "type": "web-app"},
            "technology_stack": {
                "backend": "",
                "frontend": "",
                "database": "",
                "description": "",
            },
        }
        with open(tmp_path / "web-application-fullstack.yaml", "w") as f:
            yaml.dump(template, f)
        return tmp_path

    def test_generate_config_success(self, template_dir, tmp_path):
        """Test successful config generation."""
        output_path = tmp_path / "output" / "config.yaml"

        result = generate_config(
            project_name="Test Project",
            project_type="web-app",
            output_path=output_path,
            tech_stack="Python React PostgreSQL",
            template_dir=template_dir,
            verbose=False,
        )

        assert result == 0
        assert output_path.exists()

        with open(output_path) as f:
            config = yaml.safe_load(f)
        assert config["project"]["name"] == "Test Project"
        assert config["technology_stack"]["backend"] == "Python"

    def test_generate_config_creates_output_dir(self, template_dir, tmp_path):
        """Test generate_config creates output directory."""
        output_path = tmp_path / "deep" / "nested" / "config.yaml"

        result = generate_config(
            project_name="Test",
            project_type="web-app",
            output_path=output_path,
            template_dir=template_dir,
            verbose=False,
        )

        assert result == 0
        assert output_path.parent.exists()

    def test_generate_config_invalid_project_type(self, template_dir, tmp_path):
        """Test generate_config with invalid project type."""
        output_path = tmp_path / "config.yaml"

        result = generate_config(
            project_name="Test",
            project_type="invalid",
            output_path=output_path,
            template_dir=template_dir,
            verbose=False,
        )

        assert result == 1

    def test_generate_config_missing_template_dir(self, tmp_path):
        """Test generate_config with missing template directory."""
        output_path = tmp_path / "config.yaml"

        result = generate_config(
            project_name="Test",
            project_type="web-app",
            output_path=output_path,
            template_dir=tmp_path / "nonexistent",
            verbose=False,
        )

        assert result == 1

    def test_generate_config_without_tech_stack(self, template_dir, tmp_path):
        """Test generate_config without tech stack."""
        output_path = tmp_path / "config.yaml"

        result = generate_config(
            project_name="Minimal Project",
            project_type="web-app",
            output_path=output_path,
            tech_stack=None,
            template_dir=template_dir,
            verbose=False,
        )

        assert result == 0
        assert output_path.exists()


class TestIntegration:
    """Integration tests for config generation."""

    def test_full_workflow(self, tmp_path):
        """Test complete config generation workflow."""
        # Create template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template = {
            "project": {"name": "", "version": "1.0.0"},
            "technology_stack": {"backend": "", "frontend": "", "description": ""},
            "settings": {"debug": False},
        }
        with open(template_dir / "web-application-fullstack.yaml", "w") as f:
            yaml.dump(template, f)

        # Generate config
        output_path = tmp_path / "project-config.yaml"
        result = generate_config(
            project_name="My App",
            project_type="web-app",
            output_path=output_path,
            tech_stack="FastAPI React",
            template_dir=template_dir,
            verbose=False,
        )

        assert result == 0

        # Verify output
        with open(output_path) as f:
            config = yaml.safe_load(f)

        assert config["project"]["name"] == "My App"
        assert config["project"]["version"] == "1.0.0"
        assert config["technology_stack"]["backend"] == "Python"
        assert config["technology_stack"]["frontend"] == "React"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
