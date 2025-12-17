"""
Tests for vibey.roadmap.serialization.backend module.

Tests the backend abstraction layer for roadmap storage.
"""

import pytest
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

from vibey.roadmap.serialization.backend import (
    BackendError,
    YAMLModifiedError,
    DirtyDatabaseError,
    SchemaMismatchError,
    DatabaseValidationError,
    DatabaseCorruptedError,
    RoadmapBackend,
    YAMLBackend,
    SQLiteBackend,
    SyncManager,
    EXPECTED_SCHEMA_VERSION,
    load_roadmap_config,
    validate_database,
    get_backend,
    get_default_backend,
)


class TestBackendError:
    """Test BackendError class."""

    def test_basic_construction(self):
        """Test basic BackendError construction."""
        error = BackendError("Test error")
        assert str(error) == "Test error"

    def test_inherits_from_exception(self):
        """Test inherits from Exception."""
        assert issubclass(BackendError, Exception)


class TestYAMLModifiedError:
    """Test YAMLModifiedError class."""

    def test_construction(self):
        """Test YAMLModifiedError construction."""
        modified_files = ["/path/to/file1.yaml", "/path/to/file2.yaml"]
        error = YAMLModifiedError(modified_files)
        
        assert error.modified_files == modified_files
        assert "YAML files modified" in str(error)

    def test_includes_files_in_message(self):
        """Test modified files are in error message."""
        error = YAMLModifiedError(["/a.yaml", "/b.yaml"])
        message = str(error)
        
        assert "/a.yaml" in message
        assert "/b.yaml" in message

    def test_includes_recovery_options(self):
        """Test recovery options are in error message."""
        error = YAMLModifiedError(["file.yaml"])
        message = str(error)
        
        assert "vibey roadmap rebuild" in message
        assert "vibey roadmap dump" in message


class TestDirtyDatabaseError:
    """Test DirtyDatabaseError class."""

    def test_construction(self):
        """Test DirtyDatabaseError construction."""
        error = DirtyDatabaseError()
        assert "uncommitted changes" in str(error)

    def test_includes_recovery_options(self):
        """Test recovery options are in error message."""
        error = DirtyDatabaseError()
        message = str(error)
        
        assert "vibey roadmap dump" in message
        assert "vibey roadmap rebuild" in message


class TestSchemaMismatchError:
    """Test SchemaMismatchError class."""

    def test_construction(self):
        """Test SchemaMismatchError construction."""
        error = SchemaMismatchError(db_version="0.9.0", expected_version="1.0.0")
        
        assert error.db_version == "0.9.0"
        assert error.expected_version == "1.0.0"
        assert "0.9.0" in str(error)
        assert "1.0.0" in str(error)

    def test_includes_migration_hint(self):
        """Test migration hint is in error message."""
        error = SchemaMismatchError("0.9.0", "1.0.0")
        assert "migrate" in str(error).lower()


class TestDatabaseValidationError:
    """Test DatabaseValidationError class."""

    def test_inherits_from_backend_error(self):
        """Test inherits from BackendError."""
        assert issubclass(DatabaseValidationError, BackendError)


class TestDatabaseCorruptedError:
    """Test DatabaseCorruptedError class."""

    def test_construction_no_details(self):
        """Test construction without details."""
        error = DatabaseCorruptedError()
        # When no details provided, message still contains recovery options
        assert "rebuild" in str(error).lower()

    def test_construction_with_details(self):
        """Test construction with details."""
        error = DatabaseCorruptedError("Page 123 corrupted")
        message = str(error)
        
        assert "Page 123 corrupted" in message

    def test_includes_recovery_options(self):
        """Test recovery options are in error message."""
        error = DatabaseCorruptedError()
        message = str(error)
        
        assert "rebuild" in message.lower()


class TestYAMLBackend:
    """Test YAMLBackend class."""

    @pytest.fixture
    def tmp_roadmap_dir(self, tmp_path):
        """Create temporary roadmap directory structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()
        return roadmap_dir

    @pytest.fixture
    def backend(self, tmp_roadmap_dir):
        """Create YAMLBackend instance."""
        return YAMLBackend(tmp_roadmap_dir)

    def test_init_sets_roadmap_dir(self, tmp_roadmap_dir):
        """Test initialization sets roadmap_dir."""
        backend = YAMLBackend(tmp_roadmap_dir)
        assert backend.roadmap_dir == tmp_roadmap_dir

    def test_init_with_string_path(self, tmp_roadmap_dir):
        """Test initialization with string path."""
        backend = YAMLBackend(str(tmp_roadmap_dir))
        assert backend.roadmap_dir == tmp_roadmap_dir

    def test_load_sprint_not_found(self, backend):
        """Test load_sprint raises error for missing sprint."""
        with pytest.raises(ValueError, match="not found"):
            backend.load_sprint("nonexistent-sprint")

    def test_load_task_not_found(self, backend):
        """Test load_task raises error for missing task."""
        with pytest.raises(ValueError, match="not found"):
            backend.load_task("nonexistent-task")

    def test_load_tasks_by_sprint_empty(self, backend):
        """Test load_tasks_by_sprint returns empty list when no tasks."""
        tasks = backend.load_tasks_by_sprint("sprint-1")
        assert tasks == []

    def test_load_tasks_by_track_empty(self, backend):
        """Test load_tasks_by_track returns empty list when no tasks."""
        tasks = backend.load_tasks_by_track("track-1")
        assert tasks == []

    def test_load_all_tasks_empty(self, backend):
        """Test load_all_tasks returns empty list when no tasks."""
        tasks = backend.load_all_tasks()
        assert tasks == []


class TestSQLiteBackend:
    """Test SQLiteBackend class."""

    def test_init_with_path(self, tmp_path):
        """Test initialization with path."""
        db_path = tmp_path / "test.db"
        backend = SQLiteBackend(db_path)
        assert backend.db_path == db_path

    def test_init_with_string(self, tmp_path):
        """Test initialization with string path."""
        db_path = tmp_path / "test.db"
        backend = SQLiteBackend(str(db_path))
        assert backend.db_path == db_path

    def test_init_no_path(self):
        """Test initialization without path."""
        backend = SQLiteBackend()
        assert backend.db_path is None

    def test_ensure_connection_no_db(self, tmp_path):
        """Test _ensure_connection raises error when no DB."""
        db_path = tmp_path / "nonexistent.db"
        backend = SQLiteBackend(db_path)
        
        with pytest.raises(BackendError, match="not found"):
            backend._ensure_connection()


class TestSyncManager:
    """Test SyncManager class."""

    @pytest.fixture
    def tmp_roadmap_dir(self, tmp_path):
        """Create temporary roadmap directory."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()
        return roadmap_dir

    @pytest.fixture
    def tmp_db_path(self, tmp_path):
        """Create temporary database path."""
        return tmp_path / ".vibey" / "roadmap.db"

    @pytest.fixture
    def manager(self, tmp_roadmap_dir, tmp_db_path):
        """Create SyncManager instance."""
        return SyncManager(
            roadmap_dir=tmp_roadmap_dir,
            db_path=tmp_db_path
        )

    def test_init_sets_paths(self, tmp_roadmap_dir, tmp_db_path):
        """Test initialization sets paths."""
        manager = SyncManager(tmp_roadmap_dir, tmp_db_path)
        
        assert manager.roadmap_dir == tmp_roadmap_dir
        assert manager.db_path == tmp_db_path

    def test_compute_file_checksum(self, manager, tmp_path):
        """Test compute_file_checksum computes SHA-256."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = manager.compute_file_checksum(test_file)
        
        # SHA-256 is 64 hex characters
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_compute_file_checksum_consistent(self, manager, tmp_path):
        """Test checksum is consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")
        
        checksum1 = manager.compute_file_checksum(test_file)
        checksum2 = manager.compute_file_checksum(test_file)
        
        assert checksum1 == checksum2

    def test_compute_file_checksum_changes(self, manager, tmp_path):
        """Test checksum changes when content changes."""
        test_file = tmp_path / "test.txt"
        
        test_file.write_text("Content A")
        checksum1 = manager.compute_file_checksum(test_file)
        
        test_file.write_text("Content B")
        checksum2 = manager.compute_file_checksum(test_file)
        
        assert checksum1 != checksum2

    def test_find_all_yaml_files_empty(self, manager):
        """Test find_all_yaml_files returns empty for new dir."""
        files = manager.find_all_yaml_files()
        assert files == []

    def test_find_all_yaml_files_with_files(self, manager, tmp_roadmap_dir):
        """Test find_all_yaml_files finds YAML files."""
        # Create some YAML files
        (tmp_roadmap_dir / "roadmap.yaml").write_text("id: test")
        (tmp_roadmap_dir / "tracks" / "track1.yaml").write_text("id: track1")
        (tmp_roadmap_dir / "sprints" / "sprint1.yaml").write_text("id: sprint1")
        (tmp_roadmap_dir / "tasks" / "task1.yaml").write_text("id: task1")
        
        files = manager.find_all_yaml_files()
        
        assert len(files) == 4

    def test_find_all_yaml_files_ignores_hidden(self, manager, tmp_roadmap_dir):
        """Test find_all_yaml_files ignores hidden files."""
        (tmp_roadmap_dir / "tracks" / ".hidden.yaml").write_text("hidden: true")
        (tmp_roadmap_dir / "tracks" / "visible.yaml").write_text("visible: true")
        
        files = manager.find_all_yaml_files()
        
        # Should only find visible.yaml
        assert len(files) == 1
        assert any("visible" in str(f) for f in files)


class TestLoadRoadmapConfig:
    """Test load_roadmap_config function."""

    def test_default_config_when_no_file(self, tmp_path):
        """Test returns defaults when config file doesn't exist."""
        config = load_roadmap_config(tmp_path)
        
        assert config["backend"] == "auto"
        assert "database" in config
        assert config["database"]["path"] == ".vibey/roadmap.db"

    def test_loads_custom_config(self, tmp_path):
        """Test loads custom configuration."""
        config_dir = tmp_path / ".vibey" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "roadmap.yaml").write_text("""
backend: sqlite
database:
  path: custom/path.db
  validate_on_load: false
""")
        
        config = load_roadmap_config(tmp_path)
        
        assert config["backend"] == "sqlite"
        assert config["database"]["path"] == "custom/path.db"
        assert config["database"]["validate_on_load"] is False

    def test_merges_with_defaults(self, tmp_path):
        """Test partial config merges with defaults."""
        config_dir = tmp_path / ".vibey" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "roadmap.yaml").write_text("""
backend: yaml
""")
        
        config = load_roadmap_config(tmp_path)
        
        assert config["backend"] == "yaml"
        # Should still have default database config
        assert "database" in config
        assert config["database"]["fallback_to_yaml"] is True


class TestValidateDatabase:
    """Test validate_database function."""

    def test_returns_false_for_missing_file(self, tmp_path):
        """Test returns False for missing database file."""
        db_path = tmp_path / "nonexistent.db"
        is_valid, error = validate_database(db_path)
        
        assert is_valid is False
        assert "not found" in error.lower()

    def test_returns_false_for_uninitialized_db(self, tmp_path):
        """Test returns False for uninitialized database."""
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()
        
        is_valid, error = validate_database(db_path)
        
        assert is_valid is False
        assert "database_state" in error or "not initialized" in error.lower()

    def test_returns_false_for_missing_tables(self, tmp_path):
        """Test returns False when required tables missing."""
        db_path = tmp_path / "incomplete.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute(f"INSERT INTO database_state VALUES (1, '{EXPECTED_SCHEMA_VERSION}')")
        conn.commit()
        conn.close()
        
        is_valid, error = validate_database(db_path)
        
        assert is_valid is False
        assert "missing tables" in error.lower()

    def test_returns_true_for_valid_db(self, tmp_path):
        """Test returns True for valid database."""
        db_path = tmp_path / "valid.db"
        conn = sqlite3.connect(str(db_path))
        
        # Create required tables
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute(f"INSERT INTO database_state VALUES (1, '{EXPECTED_SCHEMA_VERSION}')")
        conn.execute("CREATE TABLE roadmaps (id TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE tracks (id TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE sprints (id TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()
        
        is_valid, error = validate_database(db_path)
        
        assert is_valid is True
        assert error == ""


class TestGetBackend:
    """Test get_backend function."""

    def test_returns_yaml_backend_for_yaml_mode(self, tmp_path):
        """Test returns YAMLBackend for yaml mode."""
        # Create .vibey/roadmap directory
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        
        backend = get_backend(mode="yaml", root_dir=tmp_path)
        
        assert isinstance(backend, YAMLBackend)

    def test_auto_mode_falls_back_to_yaml(self, tmp_path):
        """Test auto mode falls back to YAML when no DB."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        
        backend = get_backend(mode="auto", root_dir=tmp_path)
        
        assert isinstance(backend, YAMLBackend)

    def test_raises_for_unknown_mode(self, tmp_path):
        """Test raises error for unknown mode."""
        with pytest.raises(BackendError, match="Unknown backend mode"):
            get_backend(mode="invalid", root_dir=tmp_path)


class TestGetDefaultBackend:
    """Test get_default_backend function."""

    def test_returns_backend(self, tmp_path):
        """Test returns a backend instance."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        
        # Mock cwd to use tmp_path
        with patch("vibey.roadmap.serialization.backend.Path") as mock_path:
            mock_path.cwd.return_value = tmp_path
            mock_path.return_value = tmp_path
            
            # Just verify it doesn't crash - actual behavior depends on config
            try:
                backend = get_default_backend()
                assert backend is not None
            except BackendError:
                pass  # Expected if no valid backend available


class TestRoadmapBackendProtocol:
    """Test RoadmapBackend protocol."""

    def test_yaml_backend_is_roadmap_backend(self):
        """Test YAMLBackend implements RoadmapBackend."""
        assert isinstance(YAMLBackend(".vibey/roadmap"), RoadmapBackend)

    def test_sqlite_backend_is_roadmap_backend(self):
        """Test SQLiteBackend implements RoadmapBackend."""
        assert isinstance(SQLiteBackend(), RoadmapBackend)


class TestExpectedSchemaVersion:
    """Test EXPECTED_SCHEMA_VERSION constant."""

    def test_version_is_string(self):
        """Test schema version is a string."""
        assert isinstance(EXPECTED_SCHEMA_VERSION, str)

    def test_version_format(self):
        """Test schema version has expected format."""
        # Should be semver-like format
        parts = EXPECTED_SCHEMA_VERSION.split(".")
        assert len(parts) >= 2
        assert all(p.isdigit() for p in parts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
