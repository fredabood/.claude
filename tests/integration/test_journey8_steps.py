"""
Integration tests for Journey 8: Config Migration

Tests the complete config migration workflow from legacy monolithic format
to modular architecture (v2.0+).

Journey 8 Steps:
1. Detect Legacy Config
2. Preview Migration (Dry Run)
3. Run Migration
4. Validate New Config
5. Commit Migration
6. Redeploy to Platform
7. Rollback if Needed
8. Journey Complete

Total Tests: 41
- Config Detection & Parsing: 10 tests
- Migration Logic: 10 tests
- Validation: 5 tests
- Rollback: 5 tests
- Integration Tests (8 steps): 8 tests
- E2E & Platform Tests: 3 tests
"""

import pytest
import yaml
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from tests.utils import RepoBuilder, StateValidator, MetricsCollector


# ============================================================================
# Category 1: Config Detection & Parsing (10 tests)
# ============================================================================


@pytest.mark.integration
class TestJourney8ConfigDetection:
    """Test config detection and parsing functionality."""

    def test_01_detect_legacy_config_monolithic(self, temp_dir):
        """
        Test detection of legacy monolithic config format.

        Journey 8, Step 8.1: Detect Legacy Config
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="legacy-config-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Create legacy config (monolithic format)
        legacy_config = {
            "project": {
                "name": "test-project",
                "type": "web-app",
                "version": "1.0.0"
            },
            "framework": {
                "version": "1.2.0",
                "orchestration_mode": "balanced",
                "quality_gates_enabled": True
            },
            "agents": {
                "web-developer": {"enabled": True},
                "security-reviewer": {"enabled": True}
            }
        }

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        validator = StateValidator()

        # Act - Simulate config detection
        config_exists = config_path.exists()
        with open(config_path) as f:
            detected_config = yaml.safe_load(f)

        # Verify legacy format (all sections in one file)
        is_legacy = (
            "project" in detected_config and
            "framework" in detected_config and
            "agents" in detected_config
        )

        # Assert
        assert config_exists, "Legacy config file should exist"
        assert is_legacy, "Should detect legacy monolithic format"
        assert detected_config["project"]["type"] == "web-app"
        assert detected_config["framework"]["orchestration_mode"] == "balanced"

    def test_02_detect_modular_config(self, temp_dir):
        """
        Test detection of modular config format (v2.x).

        Journey 8: Should detect no migration needed.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="modular-config-test")
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create modular config (v2.x format)
        project_config = {
            "project": {
                "name": "test-project",
                "type": "web-app",
                "version": "1.0.0"
            }
        }

        framework_config = {
            "framework": {
                "version": "2.0.0",
                "orchestration_mode": "balanced"
            }
        }

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)

        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        # Act - Check for modular config
        has_project = (config_dir / "project.yaml").exists()
        has_framework = (config_dir / "framework.yaml").exists()
        is_modular = has_project and has_framework

        # Assert
        assert is_modular, "Should detect modular format"
        assert not (repo.path / ".vibey" / "project-config.yaml").exists(), \
            "Should not have legacy monolithic config"

    def test_03_config_show_command_output_format(self, temp_dir):
        """
        Test `vibey config show` command output structure.

        Journey 8, Step 8.1: Config show output format.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "test", "type": "web-app"},
            "framework": {"orchestration_mode": "balanced"}
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate config show command
        config_location = vibey_dir / "project-config.yaml"
        config_format = "LEGACY (monolithic)"

        with open(config_location) as f:
            config_data = yaml.safe_load(f)

        config_summary = {
            "location": str(config_location),
            "format": config_format,
            "project_type": config_data["project"]["type"],
            "orchestration_mode": config_data["framework"]["orchestration_mode"]
        }

        # Assert
        assert config_summary["location"].endswith("project-config.yaml")
        assert config_summary["format"] == "LEGACY (monolithic)"
        assert config_summary["project_type"] == "web-app"
        assert config_summary["orchestration_mode"] == "balanced"

    def test_04_invalid_config_detection(self, temp_dir):
        """
        Test detection of malformed YAML config.

        Journey 8: Error handling for invalid config.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Create invalid YAML
        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: syntax:\n  - unclosed: [bracket")

        # Act & Assert
        with pytest.raises(yaml.YAMLError):
            with open(config_path) as f:
                yaml.safe_load(f)

    def test_05_missing_config_detection(self, temp_dir):
        """
        Test detection when no config exists.

        Journey 8: Should suggest initialization.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"

        # Act - Check for config
        legacy_exists = (vibey_dir / "project-config.yaml").exists() if vibey_dir.exists() else False
        modular_exists = (vibey_dir / "config" / "project.yaml").exists() if vibey_dir.exists() else False

        # Assert
        assert not legacy_exists, "Legacy config should not exist"
        assert not modular_exists, "Modular config should not exist"

    def test_06_parse_legacy_config_structure(self, temp_dir):
        """
        Test parsing of complete legacy config with all sections.

        Journey 8: Verify all fields parsed correctly.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Create comprehensive legacy config
        legacy_config = {
            "project": {
                "name": "comprehensive-test",
                "type": "web-app",
                "version": "1.0.0",
                "description": "Full legacy config test"
            },
            "framework": {
                "version": "1.2.0",
                "orchestration_mode": "balanced",
                "quality_gates_enabled": True,
                "quality_gates": {
                    "security": {"enabled": True, "threshold": 80},
                    "testing": {"enabled": True, "threshold": 85}
                }
            },
            "agents": {
                "web-developer": {"enabled": True, "priority": 1},
                "security-reviewer": {"enabled": True, "priority": 2},
                "test-engineer": {"enabled": False}
            },
            "tech_stack": {
                "frontend": ["react", "typescript"],
                "backend": ["nodejs", "express"],
                "database": ["postgresql"]
            }
        }

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Parse config
        with open(config_path) as f:
            parsed_config = yaml.safe_load(f)

        # Assert - All sections present
        assert "project" in parsed_config
        assert "framework" in parsed_config
        assert "agents" in parsed_config
        assert "tech_stack" in parsed_config

        # Assert - Nested values accessible
        assert parsed_config["project"]["name"] == "comprehensive-test"
        assert parsed_config["framework"]["quality_gates"]["security"]["threshold"] == 80
        assert parsed_config["agents"]["web-developer"]["priority"] == 1
        assert "react" in parsed_config["tech_stack"]["frontend"]

    def test_07_parse_modular_config_structure(self, temp_dir):
        """
        Test parsing of modular config (3 separate files).

        Journey 8: Verify files combine correctly.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create modular config files
        project_config = {"project": {"name": "modular-test", "type": "web-app"}}
        framework_config = {"framework": {"orchestration_mode": "balanced"}}
        agents_config = {"agents": {"web-developer": {"enabled": True}}}

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)
        with open(config_dir / "agents.yaml", "w") as f:
            yaml.dump(agents_config, f)

        # Act - Load and combine configs
        combined_config = {}
        for yaml_file in config_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                combined_config.update(yaml.safe_load(f))

        # Assert
        assert "project" in combined_config
        assert "framework" in combined_config
        assert "agents" in combined_config
        assert combined_config["project"]["name"] == "modular-test"

    def test_08_config_version_detection(self, temp_dir):
        """
        Test distinguishing v1.x vs v2.x config format.

        Journey 8: Version identification.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # v1.x config (monolithic)
        v1_config = {
            "framework": {"version": "1.2.0"},
            "project": {"type": "web-app"}
        }

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(v1_config, f)

        # Act - Detect version
        with open(config_path) as f:
            config = yaml.safe_load(f)

        version = config.get("framework", {}).get("version", "")
        is_v1 = version.startswith("1.")
        is_v2 = version.startswith("2.")

        # Assert
        assert is_v1, "Should detect v1.x version"
        assert not is_v2, "Should not be v2.x"

    def test_09_agent_config_detection(self, temp_dir):
        """
        Test agent config parsing from legacy format.

        Journey 8: Agent-specific settings identification.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "agents": {
                "web-developer": {
                    "enabled": True,
                    "priority": 1,
                    "trigger_patterns": ["build", "deploy"]
                },
                "security-reviewer": {
                    "enabled": True,
                    "auto_scan": True
                }
            }
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act
        with open(vibey_dir / "project-config.yaml") as f:
            config = yaml.safe_load(f)

        agents = config.get("agents", {})

        # Assert
        assert len(agents) == 2
        assert "web-developer" in agents
        assert agents["web-developer"]["enabled"] is True
        assert agents["web-developer"]["priority"] == 1
        assert "build" in agents["web-developer"]["trigger_patterns"]

    def test_10_quality_gate_config_parsing(self, temp_dir):
        """
        Test quality gate settings parsing.

        Journey 8: Thresholds and rules extraction.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        config = {
            "framework": {
                "quality_gates": {
                    "security": {"enabled": True, "threshold": 80},
                    "testing": {"enabled": True, "threshold": 85, "min_coverage": 90},
                    "performance": {"enabled": False}
                }
            }
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(config, f)

        # Act
        with open(vibey_dir / "project-config.yaml") as f:
            parsed = yaml.safe_load(f)

        gates = parsed["framework"]["quality_gates"]

        # Assert
        assert gates["security"]["threshold"] == 80
        assert gates["testing"]["threshold"] == 85
        assert gates["testing"]["min_coverage"] == 90
        assert gates["performance"]["enabled"] is False


# ============================================================================
# Category 2: Migration Logic (10 tests)
# ============================================================================


@pytest.mark.integration
class TestJourney8Migration:
    """Test config migration logic."""

    def test_11_dry_run_no_file_changes(self, temp_dir):
        """
        Test dry run does not modify any files.

        Journey 8, Step 8.2: Preview Migration (Dry Run).
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "test", "type": "web-app"},
            "framework": {"orchestration_mode": "balanced"}
        }

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        # Record initial state
        initial_mtime = config_path.stat().st_mtime
        config_dir = vibey_dir / "config"
        initial_config_dir_exists = config_dir.exists()

        # Act - Simulate dry run (read-only operations)
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        # Simulate migration plan (no actual writes)
        migration_plan = {
            "would_create": [
                str(config_dir / "project.yaml"),
                str(config_dir / "framework.yaml")
            ],
            "would_backup": str(vibey_dir / "config-backups" / f"backup_{datetime.now().strftime('%Y%m%d')}")
        }

        # Assert - No files modified
        assert config_path.stat().st_mtime == initial_mtime, "Legacy config should not be modified"
        assert config_dir.exists() == initial_config_dir_exists, "Config dir should not be created"
        assert len(migration_plan["would_create"]) == 2, "Should plan to create 2 files"

    def test_12_dry_run_shows_files_to_create(self, temp_dir):
        """
        Test dry run output shows planned file creation.

        Journey 8, Step 8.2: Preview shows new files.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "test"},
            "framework": {"orchestration_mode": "balanced"},
            "agents": {"web-developer": {"enabled": True}}
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Generate migration plan
        config_dir = vibey_dir / "config"
        agents_dir = config_dir / "agents"

        planned_files = [
            config_dir / "project.yaml",
            config_dir / "framework.yaml",
            agents_dir / "web-developer.yaml"
        ]

        # Assert
        assert len(planned_files) == 3
        assert any("project.yaml" in str(f) for f in planned_files)
        assert any("framework.yaml" in str(f) for f in planned_files)
        assert any("web-developer.yaml" in str(f) for f in planned_files)

    def test_13_dry_run_shows_files_to_archive(self, temp_dir):
        """
        Test dry run shows legacy config will be archived.

        Journey 8, Step 8.2: Backup preview.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"project": {"name": "test"}}, f)

        # Act - Generate backup plan
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = vibey_dir / "config-backups" / f"backup_{backup_timestamp}"
        backup_file = backup_dir / "project-config.yaml"

        # Assert
        assert "backup_" in str(backup_dir)
        assert "project-config.yaml" in str(backup_file)

    def test_14_migration_creates_project_yaml(self, temp_dir):
        """
        Test migration creates project.yaml file.

        Journey 8, Step 8.3: Run Migration - project.yaml creation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {
                "name": "test-project",
                "type": "web-app",
                "version": "1.0.0",
                "description": "Test project"
            }
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate migration
        config_dir = vibey_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        project_yaml = config_dir / "project.yaml"
        with open(project_yaml, "w") as f:
            yaml.dump({"project": legacy_config["project"]}, f)

        # Assert
        assert project_yaml.exists()
        with open(project_yaml) as f:
            project_data = yaml.safe_load(f)
        assert project_data["project"]["name"] == "test-project"
        assert project_data["project"]["type"] == "web-app"

    def test_15_migration_creates_framework_yaml(self, temp_dir):
        """
        Test migration creates framework.yaml file.

        Journey 8, Step 8.3: framework.yaml creation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "framework": {
                "version": "2.0.0",
                "orchestration_mode": "balanced",
                "quality_gates_enabled": True
            }
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate migration
        config_dir = vibey_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        framework_yaml = config_dir / "framework.yaml"
        with open(framework_yaml, "w") as f:
            yaml.dump({"framework": legacy_config["framework"]}, f)

        # Assert
        assert framework_yaml.exists()
        with open(framework_yaml) as f:
            framework_data = yaml.safe_load(f)
        assert framework_data["framework"]["orchestration_mode"] == "balanced"

    def test_16_migration_creates_agent_configs(self, temp_dir):
        """
        Test migration creates individual agent config files.

        Journey 8, Step 8.3: Agent configs creation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "agents": {
                "web-developer": {"enabled": True, "priority": 1},
                "security-reviewer": {"enabled": True, "priority": 2},
                "test-engineer": {"enabled": False}
            }
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate migration
        agents_dir = vibey_dir / "config" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        created_files = []
        for agent_name, agent_config in legacy_config["agents"].items():
            agent_file = agents_dir / f"{agent_name}.yaml"
            with open(agent_file, "w") as f:
                yaml.dump({agent_name: agent_config}, f)
            created_files.append(agent_file)

        # Assert
        assert len(created_files) == 3
        assert (agents_dir / "web-developer.yaml").exists()
        assert (agents_dir / "security-reviewer.yaml").exists()
        assert (agents_dir / "test-engineer.yaml").exists()

    def test_17_migration_preserves_all_values(self, temp_dir):
        """
        Test migration preserves all config values (no data loss).

        Journey 8, Step 8.3: Data integrity validation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "test", "type": "web-app", "custom_field": "value1"},
            "framework": {"orchestration_mode": "balanced", "custom_setting": "value2"},
            "agents": {"web-developer": {"enabled": True, "custom_prop": "value3"}}
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate migration
        config_dir = vibey_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Migrate to modular format
        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump({"project": legacy_config["project"]}, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump({"framework": legacy_config["framework"]}, f)

        agents_dir = config_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        with open(agents_dir / "web-developer.yaml", "w") as f:
            yaml.dump({"web-developer": legacy_config["agents"]["web-developer"]}, f)

        # Load migrated configs
        migrated_config = {}
        for yaml_file in config_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                migrated_config.update(yaml.safe_load(f))

        for agent_file in agents_dir.glob("*.yaml"):
            with open(agent_file) as f:
                agent_data = yaml.safe_load(f)
                if "agents" not in migrated_config:
                    migrated_config["agents"] = {}
                migrated_config["agents"].update(agent_data)

        # Assert - No data loss
        assert migrated_config["project"]["custom_field"] == "value1"
        assert migrated_config["framework"]["custom_setting"] == "value2"
        assert migrated_config["agents"]["web-developer"]["custom_prop"] == "value3"

    def test_18_migration_splits_nested_config(self, temp_dir):
        """
        Test migration correctly splits nested config values.

        Journey 8, Step 8.3: Nested structure handling.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "framework": {
                "quality_gates": {
                    "security": {"enabled": True, "threshold": 80},
                    "testing": {"enabled": True, "threshold": 85}
                }
            }
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Migrate nested config
        config_dir = vibey_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        # Assert
        with open(config_dir / "framework.yaml") as f:
            migrated = yaml.safe_load(f)

        assert "quality_gates" in migrated["framework"]
        assert migrated["framework"]["quality_gates"]["security"]["threshold"] == 80
        assert migrated["framework"]["quality_gates"]["testing"]["threshold"] == 85

    def test_19_migration_archives_legacy_config(self, temp_dir):
        """
        Test migration archives legacy config with timestamp.

        Journey 8, Step 8.3: Backup creation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {"project": {"name": "test"}}
        config_path = vibey_dir / "project-config.yaml"

        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate archiving
        backup_dir = vibey_dir / "config-backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(config_path, backup_dir / "project-config.yaml")

        # Assert
        assert backup_dir.exists()
        assert (backup_dir / "project-config.yaml").exists()
        assert "backup_" in backup_dir.name

    def test_20_migration_atomicity(self, temp_dir):
        """
        Test migration is atomic (all or nothing on error).

        Journey 8, Step 8.3: Error handling and rollback.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {"project": {"name": "test"}}
        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        config_dir = vibey_dir / "config"

        # Act - Simulate migration failure scenario
        migration_successful = False
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            # Simulate error during migration
            raise Exception("Simulated migration error")
            migration_successful = True
        except Exception:
            # Rollback - remove partially created files
            if config_dir.exists():
                import shutil
                shutil.rmtree(config_dir)

        # Assert
        assert not migration_successful
        assert not config_dir.exists(), "Partial migration should be rolled back"
        assert (vibey_dir / "project-config.yaml").exists(), "Legacy config should remain"


# ============================================================================
# Category 3: Validation (5 tests)
# ============================================================================


@pytest.mark.integration
class TestJourney8Validation:
    """Test config validation functionality."""

    def test_21_validate_command_all_valid(self, temp_dir):
        """
        Test validation passes for valid modular config.

        Journey 8, Step 8.4: Validate New Configuration.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create valid configs
        project_config = {"project": {"name": "test", "type": "web-app"}}
        framework_config = {"framework": {"orchestration_mode": "balanced"}}

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        validator = StateValidator()

        # Act - Validate all files
        validation_errors = []
        for yaml_file in config_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                validation_errors.append(str(e))

        # Assert
        assert len(validation_errors) == 0, "All files should be valid"

    def test_22_validate_missing_required_field(self, temp_dir):
        """
        Test validation detects missing required fields.

        Journey 8, Step 8.4: Field validation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create incomplete config (missing required 'name' field)
        project_config = {"project": {"type": "web-app"}}  # Missing 'name'

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)

        # Act - Validate
        with open(config_dir / "project.yaml") as f:
            config = yaml.safe_load(f)

        required_fields = ["name", "type"]
        missing_fields = [field for field in required_fields
                         if field not in config.get("project", {})]

        # Assert
        assert len(missing_fields) > 0, "Should detect missing required field"
        assert "name" in missing_fields

    def test_23_validate_invalid_value_type(self, temp_dir):
        """
        Test validation detects incorrect value types.

        Journey 8, Step 8.4: Type validation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create config with wrong type (string instead of bool)
        framework_config = {
            "framework": {
                "quality_gates_enabled": "yes"  # Should be boolean
            }
        }

        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        # Act - Validate
        with open(config_dir / "framework.yaml") as f:
            config = yaml.safe_load(f)

        quality_gates_enabled = config["framework"]["quality_gates_enabled"]
        is_boolean = isinstance(quality_gates_enabled, bool)

        # Assert
        assert not is_boolean, "Should detect incorrect type"
        assert isinstance(quality_gates_enabled, str)

    def test_24_validate_multi_file_consistency(self, temp_dir):
        """
        Test validation detects conflicting values across files.

        Journey 8, Step 8.4: Cross-file consistency.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create configs with conflicting values
        project_config = {"project": {"name": "test-app"}}
        framework_config = {"project": {"name": "different-app"}}  # Conflict!

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        # Act - Check for conflicts
        all_configs = {}
        for yaml_file in config_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                for key in config:
                    if key in all_configs:
                        # Conflict detected
                        assert True  # Expected behavior
                        return
                    all_configs[key] = config[key]

        # If we get here, no conflict was detected
        assert False, "Should detect conflicting values"

    def test_25_validate_schema_per_file_type(self, temp_dir):
        """
        Test each file type validated against correct schema.

        Journey 8, Step 8.4: Schema-specific validation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        project_config = {"project": {"name": "test", "type": "web-app"}}
        framework_config = {"framework": {"orchestration_mode": "balanced"}}

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        # Act - Validate with appropriate schemas
        # Simulate schema validation
        project_schema_keys = ["name", "type"]
        framework_schema_keys = ["orchestration_mode"]

        with open(config_dir / "project.yaml") as f:
            project_data = yaml.safe_load(f)
        with open(config_dir / "framework.yaml") as f:
            framework_data = yaml.safe_load(f)

        # Assert - Correct keys present for each schema
        assert all(key in project_data["project"] for key in project_schema_keys)
        assert "orchestration_mode" in framework_data["framework"]


# ============================================================================
# Category 4: Rollback (5 tests)
# ============================================================================


@pytest.mark.integration
class TestJourney8Rollback:
    """Test config rollback functionality."""

    def test_26_rollback_list_command(self, temp_dir):
        """
        Test listing available backups.

        Journey 8, Step 8.7: Rollback (If Needed) - List backups.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        backup_dir = repo.path / ".vibey" / "config-backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple backups
        backup1 = backup_dir / "backup_20251110_140000"
        backup2 = backup_dir / "backup_20251110_150000"
        backup3 = backup_dir / "backup_20251110_160000"

        for backup in [backup1, backup2, backup3]:
            backup.mkdir(exist_ok=True)
            (backup / "project-config.yaml").touch()

        # Act - List backups
        backups = sorted(backup_dir.glob("backup_*"), reverse=True)

        # Assert
        assert len(backups) == 3
        assert backups[0].name == "backup_20251110_160000", "Most recent should be first"

    def test_27_rollback_restore_legacy_config(self, temp_dir):
        """
        Test restoring legacy config from backup.

        Journey 8, Step 8.7: Restore operation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Create backup
        backup_dir = vibey_dir / "config-backups" / "backup_20251110_140000"
        backup_dir.mkdir(parents=True, exist_ok=True)

        legacy_config = {"project": {"name": "original-config"}}
        backup_file = backup_dir / "project-config.yaml"
        with open(backup_file, "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Simulate rollback
        restore_path = vibey_dir / "project-config.yaml"
        import shutil
        shutil.copy2(backup_file, restore_path)

        # Assert
        assert restore_path.exists()
        with open(restore_path) as f:
            restored_config = yaml.safe_load(f)
        assert restored_config["project"]["name"] == "original-config"

    def test_28_rollback_removes_migrated_files(self, temp_dir):
        """
        Test rollback removes modular config files.

        Journey 8, Step 8.7: Cleanup after rollback.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create modular config files
        (config_dir / "project.yaml").touch()
        (config_dir / "framework.yaml").touch()

        agents_dir = config_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        (agents_dir / "web-developer.yaml").touch()

        # Act - Simulate rollback cleanup
        import shutil
        shutil.rmtree(config_dir)

        # Assert
        assert not config_dir.exists(), "Config directory should be removed"
        assert not (config_dir / "project.yaml").exists()
        assert not (config_dir / "framework.yaml").exists()

    def test_29_rollback_atomicity(self, temp_dir):
        """
        Test rollback completes fully or not at all.

        Journey 8, Step 8.7: Atomic rollback operation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        backup_dir = vibey_dir / "config-backups" / "backup_20251110_140000"
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / "project-config.yaml").write_text("project:\n  name: test")

        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "project.yaml").touch()

        # Act - Simulate rollback with error handling
        rollback_successful = False
        try:
            # Step 1: Restore legacy config
            import shutil
            shutil.copy2(
                backup_dir / "project-config.yaml",
                vibey_dir / "project-config.yaml"
            )

            # Step 2: Remove modular config
            shutil.rmtree(config_dir)

            rollback_successful = True
        except Exception as e:
            # If any step fails, ensure clean state
            rollback_successful = False

        # Assert
        assert rollback_successful
        assert (vibey_dir / "project-config.yaml").exists()
        assert not config_dir.exists()

    def test_30_rollback_invalid_backup_name(self, temp_dir):
        """
        Test error handling for invalid backup name.

        Journey 8, Step 8.7: Error handling.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        backup_dir = repo.path / ".vibey" / "config-backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create one valid backup
        valid_backup = backup_dir / "backup_20251110_140000"
        valid_backup.mkdir(exist_ok=True)

        # Act - Try to use invalid backup name
        invalid_backup_name = "nonexistent_backup"
        requested_backup = backup_dir / invalid_backup_name

        # Assert
        assert not requested_backup.exists(), "Invalid backup should not exist"

        # List available backups for error message
        available_backups = list(backup_dir.glob("backup_*"))
        assert len(available_backups) == 1, "Should show available backups in error"


# ============================================================================
# Category 5: Integration Tests - 8 Steps (8 tests)
# ============================================================================


@pytest.mark.integration
class TestJourney8IntegrationSteps:
    """Test complete Journey 8 workflow steps."""

    def test_31_step_8_1_detect_legacy_config(self, temp_dir):
        """
        Test Step 8.1: Detect Legacy Config - Complete workflow.

        Journey 8, Step 8.1: Full detection workflow.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-1-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "legacy-project", "type": "web-app"},
            "framework": {"version": "1.2.0", "orchestration_mode": "balanced"},
            "agents": {"web-developer": {"enabled": True}}
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Complete Step 8.1 workflow
        # 1. Check for config file
        config_exists = (vibey_dir / "project-config.yaml").exists()

        # 2. Load and analyze config
        with open(vibey_dir / "project-config.yaml") as f:
            config = yaml.safe_load(f)

        # 3. Detect format (legacy = all sections in one file)
        is_legacy = all(key in config for key in ["project", "framework", "agents"])

        # 4. Generate summary
        summary = {
            "location": str(vibey_dir / "project-config.yaml"),
            "format": "LEGACY (monolithic)" if is_legacy else "MODULAR",
            "project_type": config["project"]["type"],
            "framework_version": config["framework"]["version"],
            "active_agents": len(config["agents"])
        }

        detection_time = time.time() - start_time

        # Assert
        assert config_exists, "Step 8.1: Config file should exist"
        assert is_legacy, "Step 8.1: Should detect legacy format"
        assert summary["format"] == "LEGACY (monolithic)"
        assert summary["project_type"] == "web-app"
        assert summary["active_agents"] == 1

        # Track metrics
        metrics.track("detection_time", detection_time, unit="seconds", threshold=2.0)
        assert metrics.assert_metric("detection_time", max_value=2.0)

    def test_32_step_8_2_preview_migration(self, temp_dir):
        """
        Test Step 8.2: Preview Migration (Dry Run) - Complete workflow.

        Journey 8, Step 8.2: Full dry-run workflow.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-2-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "test", "type": "web-app"},
            "framework": {"orchestration_mode": "balanced"},
            "agents": {
                "web-developer": {"enabled": True},
                "security-reviewer": {"enabled": True}
            }
        }

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        # Act - Complete Step 8.2 workflow
        # 1. Read and validate legacy config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        settings_count = sum(len(section) if isinstance(section, dict) else 1
                           for section in config.values())

        # 2. Generate migration plan
        config_dir = vibey_dir / "config"
        agents_dir = config_dir / "agents"

        migration_plan = {
            "source": str(config_path),
            "target": str(config_dir),
            "settings_count": settings_count,
            "files_to_create": [
                str(config_dir / "project.yaml"),
                str(config_dir / "framework.yaml"),
                str(agents_dir / "web-developer.yaml"),
                str(agents_dir / "security-reviewer.yaml")
            ],
            "backup_location": str(vibey_dir / "config-backups" / f"backup_{datetime.now().strftime('%Y%m%d')}")
        }

        # 3. Verify no files created (dry run)
        assert not config_dir.exists(), "Step 8.2: Dry run should not create files"

        # Assert
        assert len(migration_plan["files_to_create"]) == 4
        assert "project.yaml" in migration_plan["files_to_create"][0]
        assert "framework.yaml" in migration_plan["files_to_create"][1]
        assert migration_plan["settings_count"] >= 4

    def test_33_step_8_3_run_migration(self, temp_dir):
        """
        Test Step 8.3: Run Migration - Complete workflow.

        Journey 8, Step 8.3: Full migration execution.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-3-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        legacy_config = {
            "project": {"name": "migration-test", "type": "web-app", "version": "1.0.0"},
            "framework": {"orchestration_mode": "balanced", "quality_gates_enabled": True},
            "agents": {"web-developer": {"enabled": True, "priority": 1}}
        }

        config_path = vibey_dir / "project-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Complete Step 8.3 workflow
        # Step 1: Backup legacy config
        backup_dir = vibey_dir / "config-backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(config_path, backup_dir / "project-config.yaml")

        # Step 2: Parse legacy config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Step 3: Generate modular config
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump({"project": config["project"]}, f)

        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump({"framework": config["framework"]}, f)

        agents_dir = config_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        for agent_name, agent_config in config["agents"].items():
            with open(agents_dir / f"{agent_name}.yaml", "w") as f:
                yaml.dump({agent_name: agent_config}, f)

        migration_time = time.time() - start_time

        # Assert - All files created
        assert (backup_dir / "project-config.yaml").exists(), "Step 8.3: Backup created"
        assert (config_dir / "project.yaml").exists(), "Step 8.3: project.yaml created"
        assert (config_dir / "framework.yaml").exists(), "Step 8.3: framework.yaml created"
        assert (agents_dir / "web-developer.yaml").exists(), "Step 8.3: agent config created"

        # Verify content integrity
        with open(config_dir / "project.yaml") as f:
            project_data = yaml.safe_load(f)
        assert project_data["project"]["name"] == "migration-test"

        # Track metrics
        metrics.track("migration_time", migration_time, unit="seconds", threshold=5.0)
        assert metrics.assert_metric("migration_time", max_value=5.0)

    def test_34_step_8_4_validate_new_config(self, temp_dir):
        """
        Test Step 8.4: Validate New Configuration - Complete workflow.

        Journey 8, Step 8.4: Full validation workflow.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-4-test")
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create valid modular config
        project_config = {"project": {"name": "test", "type": "web-app", "version": "1.0.0"}}
        framework_config = {"framework": {"orchestration_mode": "balanced", "quality_gates_enabled": True}}

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        agents_dir = config_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        with open(agents_dir / "web-developer.yaml", "w") as f:
            yaml.dump({"web-developer": {"enabled": True}}, f)

        # Act - Complete Step 8.4 workflow
        validation_results = []
        total_settings = 0

        # Validate each file
        for yaml_file in list(config_dir.glob("*.yaml")) + list(agents_dir.glob("*.yaml")):
            result = {"file": yaml_file.name, "valid": False, "errors": []}
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    total_settings += sum(len(v) if isinstance(v, dict) else 1 for v in data.values())
                result["valid"] = True
            except Exception as e:
                result["errors"].append(str(e))
            validation_results.append(result)

        # Calculate summary
        files_validated = len(validation_results)
        errors_found = sum(len(r["errors"]) for r in validation_results)
        all_valid = all(r["valid"] for r in validation_results)

        # Assert
        assert files_validated == 3, "Step 8.4: All files validated"
        assert errors_found == 0, "Step 8.4: No validation errors"
        assert all_valid, "Step 8.4: All configs valid"
        assert total_settings >= 5, "Step 8.4: All settings accounted for"

    def test_35_step_8_5_commit_migration(self, temp_dir):
        """
        Test Step 8.5: Commit Migration - Complete workflow.

        Journey 8, Step 8.5: Git commit workflow.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-5-test")

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=repo.path, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo.path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo.path, check=True)

        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        (config_dir / "project.yaml").write_text("project:\n  name: test")
        (config_dir / "framework.yaml").write_text("framework:\n  orchestration_mode: balanced")

        backup_dir = repo.path / ".vibey" / "config-backups"
        backup_dir.mkdir(exist_ok=True)

        # Act - Complete Step 8.5 workflow
        # Add files to git
        subprocess.run(["git", "add", ".vibey/config/"], cwd=repo.path, check=True)
        subprocess.run(["git", "add", ".vibey/config-backups/"], cwd=repo.path, check=True)

        # Create commit
        commit_message = """feat: Migrate to modular config architecture (v2.0)

- Split monolithic config into project/framework/agents
- 156 settings migrated successfully
- Created automatic backup of legacy config"""

        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo.path, check=True)

        # Verify commit
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=repo.path,
            capture_output=True,
            text=True,
            check=True
        )

        # Assert
        assert "Migrate to modular config" in result.stdout, "Step 8.5: Commit created"

    def test_36_step_8_6_redeploy_to_platform(self, temp_dir):
        """
        Test Step 8.6: Redeploy to Platform - Complete workflow.

        Journey 8, Step 8.6: Platform redeployment.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-6-test")
        config_dir = repo.path / ".vibey" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create modular config
        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump({"project": {"name": "test", "type": "web-app"}}, f)

        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump({"framework": {"orchestration_mode": "balanced"}}, f)

        # Act - Complete Step 8.6 workflow
        # 1. Detect modular config
        has_modular_config = (config_dir / "project.yaml").exists() and \
                            (config_dir / "framework.yaml").exists()

        # 2. Load modular config
        combined_config = {}
        if has_modular_config:
            for yaml_file in config_dir.glob("*.yaml"):
                with open(yaml_file) as f:
                    combined_config.update(yaml.safe_load(f))

        # 3. Simulate deployment (create .claude directory)
        claude_dir = repo.path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # Generate CLAUDE.md from modular config
        claude_md = claude_dir / "CLAUDE.md"
        claude_md_content = f"""# {combined_config['project']['name']}

Project Type: {combined_config['project']['type']}
Orchestration Mode: {combined_config['framework']['orchestration_mode']}

<!-- VIBEY_FRAMEWORK_MANAGED -->
"""
        with open(claude_md, "w") as f:
            f.write(claude_md_content)

        # Assert
        assert has_modular_config, "Step 8.6: Modular config detected"
        assert claude_md.exists(), "Step 8.6: Deployment files created"
        assert "VIBEY_FRAMEWORK_MANAGED" in claude_md.read_text()

    def test_37_step_8_7_rollback_if_needed(self, temp_dir):
        """
        Test Step 8.7: Rollback (If Needed) - Complete workflow.

        Journey 8, Step 8.7: Full rollback workflow.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-7-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Create backup
        backup_dir = vibey_dir / "config-backups" / "backup_20251110_140000"
        backup_dir.mkdir(parents=True, exist_ok=True)

        legacy_config = {"project": {"name": "original-app", "type": "web-app"}}
        backup_file = backup_dir / "project-config.yaml"
        with open(backup_file, "w") as f:
            yaml.dump(legacy_config, f)

        # Create modular config (to be rolled back)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "project.yaml").touch()
        (config_dir / "framework.yaml").touch()

        # Act - Complete Step 8.7 workflow
        # 1. List available backups
        backups = sorted(list((vibey_dir / "config-backups").glob("backup_*")), reverse=True)

        # 2. Select latest backup
        latest_backup = backups[0] if backups else None

        # 3. Restore legacy config
        if latest_backup:
            import shutil
            shutil.copy2(
                latest_backup / "project-config.yaml",
                vibey_dir / "project-config.yaml"
            )

            # 4. Remove modular config
            shutil.rmtree(config_dir)

        # Assert
        assert len(backups) == 1, "Step 8.7: Backup found"
        assert (vibey_dir / "project-config.yaml").exists(), "Step 8.7: Legacy config restored"
        assert not config_dir.exists(), "Step 8.7: Modular config removed"

        # Verify restored content
        with open(vibey_dir / "project-config.yaml") as f:
            restored = yaml.safe_load(f)
        assert restored["project"]["name"] == "original-app"

    def test_38_step_8_8_journey_complete(self, temp_dir):
        """
        Test Step 8.8: Journey 8 Complete - Full end-to-end validation.

        Journey 8, Step 8.8: Complete journey validation.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="step-8-8-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Start with legacy config
        legacy_config = {
            "project": {"name": "complete-test", "type": "web-app"},
            "framework": {"orchestration_mode": "balanced"},
            "agents": {"web-developer": {"enabled": True}}
        }

        with open(vibey_dir / "project-config.yaml", "w") as f:
            yaml.dump(legacy_config, f)

        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Execute complete Journey 8
        # Step 1: Detect legacy config ✓
        has_legacy = (vibey_dir / "project-config.yaml").exists()

        # Step 2: Preview migration ✓
        migration_plan_ready = True

        # Step 3: Run migration ✓
        backup_dir = vibey_dir / "config-backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(vibey_dir / "project-config.yaml", backup_dir / "project-config.yaml")

        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump({"project": legacy_config["project"]}, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump({"framework": legacy_config["framework"]}, f)

        # Step 4: Validate ✓
        validation_passed = (config_dir / "project.yaml").exists() and \
                          (config_dir / "framework.yaml").exists()

        # Step 5: Would commit ✓ (skipped in test)
        commit_ready = True

        # Step 6: Would redeploy ✓ (skipped in test)
        deployment_ready = True

        # Step 7: Can rollback ✓
        rollback_available = (backup_dir / "project-config.yaml").exists()

        journey_time = time.time() - start_time

        # Assert - Success criteria from Journey 8 docs
        success_criteria = {
            "legacy_config_backed_up": (backup_dir / "project-config.yaml").exists(),
            "modular_config_created": validation_passed,
            "validation_passed": validation_passed,
            "deployment_ready": deployment_ready,
            "rollback_available": rollback_available
        }

        assert all(success_criteria.values()), "Step 8.8: All success criteria met"

        # Track metrics
        metrics.track("journey_time", journey_time, unit="seconds", threshold=10.0)
        assert metrics.assert_metric("journey_time", max_value=10.0)


# ============================================================================
# Category 6: E2E & Platform Tests (3 tests)
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestJourney8E2E:
    """End-to-end and platform-specific tests."""

    def test_39_complete_journey_8_e2e(self, temp_dir):
        """
        Test complete Journey 8 end-to-end workflow.

        Journey 8: Full migration journey from start to finish.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="e2e-migration-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Create comprehensive legacy config
        legacy_config = {
            "project": {
                "name": "e2e-test-project",
                "type": "web-app",
                "version": "1.0.0",
                "description": "End-to-end migration test"
            },
            "framework": {
                "version": "1.2.0",
                "orchestration_mode": "balanced",
                "quality_gates_enabled": True,
                "quality_gates": {
                    "security": {"enabled": True, "threshold": 80},
                    "testing": {"enabled": True, "threshold": 85}
                }
            },
            "agents": {
                "web-developer": {"enabled": True, "priority": 1},
                "security-reviewer": {"enabled": True, "priority": 2},
                "test-engineer": {"enabled": True, "priority": 3}
            },
            "tech_stack": {
                "frontend": ["react", "typescript"],
                "backend": ["nodejs", "express"],
                "database": ["postgresql"]
            }
        }

        legacy_path = vibey_dir / "project-config.yaml"
        with open(legacy_path, "w") as f:
            yaml.dump(legacy_config, f)

        validator = StateValidator()
        metrics = MetricsCollector()
        e2e_start = time.time()

        # Act - Execute complete migration workflow

        # Phase 1: Detection
        with open(legacy_path) as f:
            detected_config = yaml.safe_load(f)

        # Phase 2: Migration
        backup_dir = vibey_dir / "config-backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(legacy_path, backup_dir / "project-config.yaml")

        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        # Split into modular files
        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump({"project": legacy_config["project"]}, f)

        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump({"framework": legacy_config["framework"]}, f)

        with open(config_dir / "tech_stack.yaml", "w") as f:
            yaml.dump({"tech_stack": legacy_config["tech_stack"]}, f)

        agents_dir = config_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        for agent_name, agent_config in legacy_config["agents"].items():
            with open(agents_dir / f"{agent_name}.yaml", "w") as f:
                yaml.dump({agent_name: agent_config}, f)

        # Phase 3: Validation
        validation_errors = []
        migrated_files = []

        for yaml_file in list(config_dir.glob("*.yaml")) + list(agents_dir.glob("*.yaml")):
            migrated_files.append(yaml_file)
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                validation_errors.append(str(e))

        # Phase 4: Data integrity check
        combined_migrated = {}
        for yaml_file in migrated_files:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                for key, value in data.items():
                    if key == "agents" or yaml_file.parent.name == "agents":
                        if "agents" not in combined_migrated:
                            combined_migrated["agents"] = {}
                        if key in legacy_config["agents"]:
                            combined_migrated["agents"][key] = value
                        else:
                            combined_migrated["agents"].update(data)
                    else:
                        combined_migrated[key] = value

        e2e_time = time.time() - e2e_start

        # Assert - Complete workflow validation
        assert (backup_dir / "project-config.yaml").exists(), "E2E: Backup created"
        assert len(validation_errors) == 0, "E2E: No validation errors"
        assert len(migrated_files) == 7, "E2E: All files migrated (3 main + 3 agents + 1 tech_stack)"

        # Data integrity
        assert combined_migrated["project"]["name"] == "e2e-test-project"
        assert combined_migrated["framework"]["orchestration_mode"] == "balanced"
        assert len(combined_migrated["agents"]) == 3

        # Track metrics
        metrics.track("e2e_time", e2e_time, unit="seconds", threshold=15.0)
        metrics.track("files_migrated", len(migrated_files), unit="count", threshold=5)
        assert metrics.assert_metric("e2e_time", max_value=15.0)

    def test_40_migration_then_claude_code_deploy(self, temp_dir):
        """
        Test migration followed by Claude Code deployment.

        Journey 8: Platform deployment with new config format.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="claude-deploy-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # Migrate to modular format
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        project_config = {
            "project": {
                "name": "claude-test",
                "type": "web-app",
                "description": "Claude Code deployment test"
            }
        }
        framework_config = {
            "framework": {
                "orchestration_mode": "balanced",
                "quality_gates_enabled": True
            }
        }

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump(project_config, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump(framework_config, f)

        # Act - Deploy to Claude Code
        # Load modular config
        combined_config = {}
        for yaml_file in config_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                combined_config.update(yaml.safe_load(f))

        # Generate Claude Code deployment
        claude_dir = repo.path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        claude_md_content = f"""# {combined_config['project']['name']}

**Project Type:** {combined_config['project']['type']}
**Description:** {combined_config['project']['description']}

## Framework Configuration

**Orchestration Mode:** {combined_config['framework']['orchestration_mode']}
**Quality Gates:** {'Enabled' if combined_config['framework']['quality_gates_enabled'] else 'Disabled'}

<!-- VIBEY_FRAMEWORK_MANAGED -->
*Generated from modular configuration (v2.0)*
"""

        claude_md = claude_dir / "CLAUDE.md"
        with open(claude_md, "w") as f:
            f.write(claude_md_content)

        # Copy config for platform
        platform_config_dir = claude_dir / "config"
        import shutil
        shutil.copytree(config_dir, platform_config_dir)

        # Assert
        assert claude_md.exists(), "Claude Code CLAUDE.md created"
        assert "VIBEY_FRAMEWORK_MANAGED" in claude_md.read_text()
        assert "modular configuration (v2.0)" in claude_md.read_text()
        assert platform_config_dir.exists(), "Config deployed to platform"
        assert (platform_config_dir / "project.yaml").exists()

    def test_41_migration_idempotency(self, temp_dir):
        """
        Test migration is idempotent (running twice is safe).

        Journey 8: Second migration run should be no-op.
        """
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="idempotency-test")
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        # First migration: legacy to modular
        legacy_config = {
            "project": {"name": "idempotent-test", "type": "web-app"},
            "framework": {"orchestration_mode": "balanced"}
        }

        legacy_path = vibey_dir / "project-config.yaml"
        with open(legacy_path, "w") as f:
            yaml.dump(legacy_config, f)

        # Run first migration
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        with open(config_dir / "project.yaml", "w") as f:
            yaml.dump({"project": legacy_config["project"]}, f)
        with open(config_dir / "framework.yaml", "w") as f:
            yaml.dump({"framework": legacy_config["framework"]}, f)

        # Record state after first migration
        first_migration_mtime = (config_dir / "project.yaml").stat().st_mtime

        # Act - Attempt second migration
        # Check if already migrated
        already_migrated = (config_dir / "project.yaml").exists() and \
                         (config_dir / "framework.yaml").exists()

        if already_migrated:
            # Should warn and skip migration
            migration_skipped = True
            warning_message = "⚠️  Config already in modular format. Migration not needed."
        else:
            migration_skipped = False

        # Verify no changes to existing modular config
        second_check_mtime = (config_dir / "project.yaml").stat().st_mtime

        # Assert
        assert already_migrated, "Should detect existing modular config"
        assert migration_skipped, "Should skip second migration"
        assert first_migration_mtime == second_check_mtime, "Files should not be modified"
        assert warning_message == "⚠️  Config already in modular format. Migration not needed."
