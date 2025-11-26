"""
Tests for database CLI commands (vibey roadmap db).

Tests the SQLite backend CLI integration including:
- Database initialization and management
- Backend mode detection and configuration
- Database queries and validation
- Fallback behavior
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from vibey.cli.main import cli
from vibey.cli.commands import (
    db_init_cmd,
    db_status_cmd,
    db_config_cmd,
    db_validate_cmd,
    db_query_stats_cmd,
    db_query_progress_cmd,
    db_query_blocked_cmd,
)


class TestDatabaseCommands:
    """Test database CLI command wrappers."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure with roadmap data."""
        # Create .vibey directory structure
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        roadmap_dir = vibey_dir / "roadmap"
        roadmap_dir.mkdir()
        config_dir = vibey_dir / "config"
        config_dir.mkdir()

        # Create minimal roadmap.yaml
        (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: "1.0.0"
  status: in_progress
  created: "2025-01-01T00:00:00+00:00"
  started: "2025-01-01T00:00:00+00:00"
  tracks: []
  progress:
    tracks_total: 0
    tracks_completed: 0
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0
""")

        # Create roadmap.yaml config
        (config_dir / "roadmap.yaml").write_text("""
backend: auto
database:
  path: .vibey/roadmap.db
  validate_on_load: true
  fallback_to_yaml: true
""")

        return tmp_path

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with minimal schema."""
        db_path = tmp_path / ".vibey" / "roadmap.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT,
                is_dirty INTEGER DEFAULT 0,
                last_yaml_load TEXT,
                last_yaml_dump TEXT
            )
        """)
        conn.execute("""
            INSERT INTO database_state (id, schema_version, is_dirty)
            VALUES (1, '1.0.0', 0)
        """)

        # Create required tables
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks',
                      'entity_depends_on', 'entity_blocked_by', 'entity_blocks',
                      'deliverables', 'commits', 'quality_gates', 'yaml_checksums']:
            conn.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")

        conn.commit()
        conn.close()

        return db_path


class TestBackendDetection:
    """Test backend mode detection and configuration."""

    def test_load_config_defaults(self, tmp_path):
        """Test config loading with defaults when no config file exists."""
        from vibey.roadmap.serialization.backend import load_roadmap_config

        config = load_roadmap_config(tmp_path)

        assert config['backend'] == 'auto'
        assert config['database']['validate_on_load'] is True
        assert config['database']['fallback_to_yaml'] is True

    def test_load_config_from_file(self, tmp_path):
        """Test config loading from file."""
        from vibey.roadmap.serialization.backend import load_roadmap_config

        # Create config file
        config_dir = tmp_path / ".vibey" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "roadmap.yaml").write_text("""
backend: sqlite
database:
  path: custom.db
  validate_on_load: false
""")

        config = load_roadmap_config(tmp_path)

        assert config['backend'] == 'sqlite'
        assert config['database']['validate_on_load'] is False
        # Defaults should still apply for unspecified fields
        assert config['database']['fallback_to_yaml'] is True

    def test_validate_database_missing_file(self, tmp_path):
        """Test database validation with missing file."""
        from vibey.roadmap.serialization.backend import validate_database

        is_valid, error = validate_database(tmp_path / "nonexistent.db")

        assert is_valid is False
        assert "not found" in error

    def test_validate_database_valid(self, tmp_path):
        """Test database validation with valid database."""
        from vibey.roadmap.serialization.backend import validate_database

        # Create valid database
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '1.0.0')")
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks']:
            conn.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()

        is_valid, error = validate_database(db_path)

        assert is_valid is True
        assert error == ""

    def test_validate_database_schema_mismatch(self, tmp_path):
        """Test database validation with schema version mismatch."""
        from vibey.roadmap.serialization.backend import validate_database

        # Create database with wrong version
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '0.9.0')")
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks']:
            conn.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()

        is_valid, error = validate_database(db_path)

        assert is_valid is False
        assert "version mismatch" in error


class TestGetBackend:
    """Test backend selection logic."""

    def test_yaml_mode(self, tmp_path):
        """Test explicit YAML mode selection."""
        from vibey.roadmap.serialization.backend import get_backend, YAMLBackend

        # Create roadmap directory
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)

        backend = get_backend(mode='yaml', root_dir=tmp_path)

        assert isinstance(backend, YAMLBackend)

    def test_auto_mode_no_db(self, tmp_path):
        """Test auto mode falls back to YAML when no database."""
        from vibey.roadmap.serialization.backend import get_backend, YAMLBackend

        # Create roadmap directory but no database
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)

        backend = get_backend(mode='auto', root_dir=tmp_path)

        assert isinstance(backend, YAMLBackend)

    def test_auto_mode_with_valid_db(self, tmp_path):
        """Test auto mode selects SQLite when valid database exists."""
        from vibey.roadmap.serialization.backend import get_backend, SQLiteBackend

        # Create roadmap directory
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)

        # Create valid database
        db_path = tmp_path / ".vibey" / "roadmap.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '1.0.0')")
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks']:
            conn.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()

        backend = get_backend(mode='auto', root_dir=tmp_path)

        assert isinstance(backend, SQLiteBackend)


class TestDbValidateCommand:
    """Test database validation command."""

    def test_validate_missing_db(self, tmp_path, capsys):
        """Test validation when database doesn't exist."""
        with patch('vibey.cli.commands.Path.cwd', return_value=tmp_path):
            exit_code = db_validate_cmd()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_validate_schema_level(self, tmp_path, capsys):
        """Test schema-level validation."""
        # Create database with required structure
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        db_path = vibey_dir / "roadmap.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '1.0.0')")
        for table in ['roadmaps', 'tracks', 'sprints', 'tasks',
                      'entity_depends_on', 'entity_blocked_by', 'entity_blocks',
                      'deliverables', 'commits', 'quality_gates',
                      'yaml_checksums']:
            conn.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()

        with patch('vibey.cli.commands.Path.cwd', return_value=tmp_path):
            exit_code = db_validate_cmd(level='schema')

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "All 12 required tables exist" in captured.out
        assert "Schema version: 1.0.0" in captured.out


class TestDbQueryCommands:
    """Test database query commands."""

    @pytest.fixture
    def populated_db(self, tmp_path):
        """Create a database with test data."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        db_path = vibey_dir / "roadmap.db"

        conn = sqlite3.connect(str(db_path))

        # Create schema
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT,
                is_dirty INTEGER DEFAULT 0
            )
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '1.0.0', 0)")

        conn.execute("""
            CREATE TABLE roadmaps (
                id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT
            )
        """)
        conn.execute("INSERT INTO roadmaps VALUES ('test', 'Test Roadmap', 'in_progress')")

        conn.execute("""
            CREATE TABLE tracks (
                id TEXT PRIMARY KEY,
                roadmap_id TEXT,
                name TEXT,
                status TEXT,
                blocked INTEGER DEFAULT 0,
                completion_percent REAL DEFAULT 0
            )
        """)
        conn.execute("INSERT INTO tracks VALUES ('track-1', 'test', 'Track 1', 'in_progress', 0, 50.0)")
        conn.execute("INSERT INTO tracks VALUES ('track-2', 'test', 'Track 2', 'completed', 0, 100.0)")

        conn.execute("""
            CREATE TABLE sprints (
                id TEXT PRIMARY KEY,
                track_id TEXT,
                name TEXT,
                status TEXT,
                blocked INTEGER DEFAULT 0
            )
        """)
        conn.execute("INSERT INTO sprints VALUES ('sprint-1', 'track-1', 'Sprint 1', 'in_progress', 0)")

        conn.execute("""
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                sprint_id TEXT,
                title TEXT,
                status TEXT,
                blocked INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium'
            )
        """)
        conn.execute("INSERT INTO tasks VALUES ('task-1', 'sprint-1', 'Task 1', 'completed', 0, 'high')")
        conn.execute("INSERT INTO tasks VALUES ('task-2', 'sprint-1', 'Task 2', 'not_started', 0, 'medium')")
        conn.execute("INSERT INTO tasks VALUES ('task-3', 'sprint-1', 'Task 3', 'in_progress', 0, 'low')")

        conn.commit()
        conn.close()

        return tmp_path

    def test_query_stats(self, populated_db, capsys):
        """Test statistics query command."""
        with patch('vibey.cli.commands.Path.cwd', return_value=populated_db):
            exit_code = db_query_stats_cmd()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Tracks:" in captured.out
        assert "Sprints:" in captured.out
        assert "Tasks:" in captured.out

    def test_query_progress(self, populated_db, capsys):
        """Test progress query command."""
        # Add track_id column to tasks for progress query
        db_path = populated_db / ".vibey" / "roadmap.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("ALTER TABLE tasks ADD COLUMN track_id TEXT")
        conn.execute("UPDATE tasks SET track_id = 'track-1'")
        conn.commit()
        conn.close()

        with patch('vibey.cli.commands.Path.cwd', return_value=populated_db):
            exit_code = db_query_progress_cmd(group_by='track')

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Progress by Track" in captured.out


class TestCLIIntegration:
    """Integration tests using Click's CliRunner."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_db_help(self, runner):
        """Test 'vibey roadmap db --help' command."""
        result = runner.invoke(cli, ['roadmap', 'db', '--help'])

        assert result.exit_code == 0
        assert 'Database' in result.output or 'db' in result.output

    def test_roadmap_backend_option(self, runner):
        """Test --backend option is available on roadmap group."""
        result = runner.invoke(cli, ['roadmap', '--help'])

        assert result.exit_code == 0
        assert '--backend' in result.output
        assert 'sqlite' in result.output
        assert 'yaml' in result.output


class TestPerformance:
    """Performance benchmarks for database vs YAML operations."""

    @pytest.fixture
    def large_roadmap_db(self, tmp_path):
        """Create a database with 100+ tasks for performance testing."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        db_path = vibey_dir / "roadmap.db"

        conn = sqlite3.connect(str(db_path))

        # Create schema
        conn.execute("""
            CREATE TABLE database_state (
                id INTEGER PRIMARY KEY,
                schema_version TEXT
            )
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '1.0.0')")

        conn.execute("CREATE TABLE roadmaps (id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO roadmaps VALUES ('test')")

        conn.execute("CREATE TABLE tracks (id TEXT PRIMARY KEY, roadmap_id TEXT, blocked INTEGER DEFAULT 0)")
        conn.execute("INSERT INTO tracks VALUES ('track-1', 'test', 0)")

        conn.execute("CREATE TABLE sprints (id TEXT PRIMARY KEY, track_id TEXT, blocked INTEGER DEFAULT 0)")
        for i in range(10):
            conn.execute(f"INSERT INTO sprints VALUES ('sprint-{i}', 'track-1', 0)")

        conn.execute("""
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                sprint_id TEXT,
                status TEXT,
                priority TEXT,
                blocked INTEGER DEFAULT 0
            )
        """)
        # Insert 100 tasks
        for i in range(100):
            sprint_id = f"sprint-{i % 10}"
            status = ['not_started', 'in_progress', 'completed'][i % 3]
            conn.execute(f"INSERT INTO tasks VALUES ('task-{i}', '{sprint_id}', '{status}', 'medium', 0)")

        conn.commit()
        conn.close()

        return tmp_path

    def test_query_performance(self, large_roadmap_db, capsys):
        """Test that queries complete in reasonable time."""
        import time

        start = time.time()

        with patch('vibey.cli.commands.Path.cwd', return_value=large_roadmap_db):
            exit_code = db_query_stats_cmd()

        elapsed = time.time() - start

        assert exit_code == 0
        # Should complete in under 1 second for 100 tasks
        assert elapsed < 1.0, f"Query took {elapsed:.2f}s, expected < 1.0s"
