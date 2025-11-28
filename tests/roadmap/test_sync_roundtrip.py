"""
Roundtrip Tests for SQLite ↔ YAML Synchronization

Verifies data integrity through the full sync cycle:
- YAML → SQLite (rebuild)
- SQLite → YAML (dump)
- Compare original and final data

Task: sqlite-backend-3-task-005
Status: Complete
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

import yaml


class TestRoundtripWithRealProject:
    """Test roundtrip sync using real project data."""

    @pytest.fixture
    def vibey_project(self):
        """Get the real vibey project path."""
        return Path(__file__).parent.parent.parent

    def test_dump_and_rebuild_preserves_entity_counts(self, vibey_project):
        """Test that dump → rebuild preserves entity counts."""
        from vibey.roadmap.serialization.backend import SyncManager
        from vibey.roadmap.database.connection import database_exists, get_db_path

        db_path = get_db_path(vibey_project)
        roadmap_dir = vibey_project / ".vibey" / "roadmap"

        if not database_exists(db_path=db_path):
            pytest.skip("Database not initialized - run 'vibey roadmap db init' first")

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # Get initial counts from database
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        initial_tracks = cursor.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        initial_sprints = cursor.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]
        initial_tasks = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        conn.close()

        # Dump to YAML and rebuild
        sync.dump()
        sync.rebuild(force=True)

        # Get final counts
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        final_tracks = cursor.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        final_sprints = cursor.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]
        final_tasks = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        conn.close()

        assert initial_tracks == final_tracks, f"Tracks changed: {initial_tracks} → {final_tracks}"
        assert initial_sprints == final_sprints, f"Sprints changed: {initial_sprints} → {final_sprints}"
        assert initial_tasks == final_tasks, f"Tasks changed: {initial_tasks} → {final_tasks}"

    def test_multiple_roundtrips_stable(self, vibey_project):
        """Test that multiple roundtrips produce stable counts."""
        from vibey.roadmap.serialization.backend import SyncManager
        from vibey.roadmap.database.connection import database_exists, get_db_path

        db_path = get_db_path(vibey_project)
        roadmap_dir = vibey_project / ".vibey" / "roadmap"

        if not database_exists(db_path=db_path):
            pytest.skip("Database not initialized")

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # First roundtrip
        sync.dump()
        sync.rebuild(force=True)

        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        first_tasks = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        conn.close()

        # Second roundtrip
        sync.dump()
        sync.rebuild(force=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        second_tasks = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        conn.close()

        assert first_tasks == second_tasks, "Task count changed between roundtrips"


class TestSyncWithTempCopy:
    """Test roundtrip sync with a temporary copy to avoid modifying real data."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary copy of the roadmap for testing."""
        real_project = Path(__file__).parent.parent.parent
        vibey_dir = real_project / ".vibey"

        if not vibey_dir.exists():
            pytest.skip("No .vibey directory found")

        # Copy just the roadmap directory (not the database)
        temp_vibey = tmp_path / ".vibey"
        temp_roadmap = temp_vibey / "roadmap"
        temp_vibey.mkdir()

        # Copy roadmap YAML files
        shutil.copytree(vibey_dir / "roadmap", temp_roadmap)

        # Remove any existing database
        for db_file in temp_vibey.glob("*.db*"):
            db_file.unlink()

        return tmp_path

    def test_rebuild_creates_database(self, temp_project):
        """Test that rebuild creates a database from YAML files."""
        from vibey.roadmap.serialization.backend import SyncManager

        db_path = temp_project / ".vibey" / "roadmap.db"
        roadmap_dir = temp_project / ".vibey" / "roadmap"

        assert not db_path.exists()

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)
        sync.rebuild(force=True)

        assert db_path.exists()

        # Verify data was loaded
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tracks = cursor.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        conn.close()

        assert tracks > 0, "No tracks loaded"

    def test_dump_creates_yaml_files(self, temp_project):
        """Test that dump writes YAML files from database."""
        from vibey.roadmap.serialization.backend import SyncManager

        db_path = temp_project / ".vibey" / "roadmap.db"
        roadmap_dir = temp_project / ".vibey" / "roadmap"

        # First rebuild to populate database
        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)
        sync.rebuild(force=True)

        # Count YAML files before dump
        yaml_before = len(list(roadmap_dir.rglob("*.yaml")))

        # Dump back to YAML
        sync.dump()

        # Count YAML files after dump
        yaml_after = len(list(roadmap_dir.rglob("*.yaml")))

        assert yaml_after >= yaml_before, "Dump removed YAML files"

    def test_roundtrip_preserves_task_details(self, temp_project):
        """Test that task details survive roundtrip."""
        from vibey.roadmap.serialization.backend import SyncManager

        db_path = temp_project / ".vibey" / "roadmap.db"
        roadmap_dir = temp_project / ".vibey" / "roadmap"

        # Find a task YAML file
        task_files = list(roadmap_dir.rglob("task.yaml"))
        if not task_files:
            pytest.skip("No task.yaml files found")

        task_file = task_files[0]
        with open(task_file) as f:
            original = yaml.safe_load(f)

        original_id = original['task']['id']
        # Handle both 'title' and 'name' field names
        original_title = original['task'].get('title') or original['task'].get('name', '')
        original_status = original['task']['status']

        # Roundtrip
        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)
        sync.rebuild(force=True)
        sync.dump()

        # Read task back
        with open(task_file) as f:
            final = yaml.safe_load(f)

        final_title = final['task'].get('title') or final['task'].get('name', '')

        assert final['task']['id'] == original_id
        assert final_title == original_title
        assert final['task']['status'] == original_status


class TestDatabaseDirtyFlag:
    """Test dirty flag management during sync operations."""

    @pytest.fixture
    def initialized_project(self, tmp_path):
        """Create a project with initialized database."""
        real_project = Path(__file__).parent.parent.parent
        vibey_dir = real_project / ".vibey"

        if not vibey_dir.exists():
            pytest.skip("No .vibey directory found")

        temp_vibey = tmp_path / ".vibey"
        temp_roadmap = temp_vibey / "roadmap"
        temp_vibey.mkdir()

        # Copy roadmap files
        shutil.copytree(vibey_dir / "roadmap", temp_roadmap)

        # Initialize database
        from vibey.roadmap.serialization.backend import SyncManager
        db_path = temp_vibey / "roadmap.db"
        sync = SyncManager(roadmap_dir=temp_roadmap, db_path=db_path)
        sync.rebuild(force=True)

        return tmp_path

    def test_rebuild_marks_clean(self, initialized_project):
        """Test that rebuild marks database as clean."""
        from vibey.roadmap.serialization.backend import SyncManager

        vibey_dir = initialized_project / ".vibey"
        db_path = vibey_dir / "roadmap.db"
        roadmap_dir = vibey_dir / "roadmap"

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)
        sync.rebuild(force=True)

        # Check dirty flag
        assert not sync.is_db_dirty()

    def test_dump_marks_clean(self, initialized_project):
        """Test that dump marks database as clean."""
        from vibey.roadmap.serialization.backend import SyncManager
        from vibey.roadmap.database.connection import get_connection

        vibey_dir = initialized_project / ".vibey"
        db_path = vibey_dir / "roadmap.db"
        roadmap_dir = vibey_dir / "roadmap"

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # Mark dirty manually
        conn = get_connection(db_path=db_path)
        conn.execute("UPDATE database_state SET is_dirty = 1 WHERE id = 1")
        conn.commit()

        assert sync.is_db_dirty()

        # Dump should mark clean
        sync.dump()

        assert not sync.is_db_dirty()


class TestChecksumTracking:
    """Test YAML checksum tracking for change detection."""

    @pytest.fixture
    def project_with_checksums(self, tmp_path):
        """Create a project with checksum tracking enabled."""
        real_project = Path(__file__).parent.parent.parent
        vibey_dir = real_project / ".vibey"

        if not vibey_dir.exists():
            pytest.skip("No .vibey directory found")

        temp_vibey = tmp_path / ".vibey"
        temp_roadmap = temp_vibey / "roadmap"
        temp_vibey.mkdir()

        # Copy roadmap files
        shutil.copytree(vibey_dir / "roadmap", temp_roadmap)

        # Initialize database with checksums
        from vibey.roadmap.serialization.backend import SyncManager
        db_path = temp_vibey / "roadmap.db"
        sync = SyncManager(roadmap_dir=temp_roadmap, db_path=db_path)
        sync.rebuild(force=True)
        sync.store_yaml_checksums()

        return tmp_path

    def test_checksum_detects_modification(self, project_with_checksums):
        """Test that checksum tracking detects YAML modifications."""
        from vibey.roadmap.serialization.backend import SyncManager

        vibey_dir = project_with_checksums / ".vibey"
        db_path = vibey_dir / "roadmap.db"
        roadmap_dir = vibey_dir / "roadmap"

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # Initially no modifications
        modified = sync.check_yaml_modified()
        assert len(modified) == 0

        # Modify roadmap.yaml
        roadmap_path = roadmap_dir / "roadmap.yaml"
        data = yaml.safe_load(roadmap_path.read_text())
        data["roadmap"]["name"] = "Modified Name"
        roadmap_path.write_text(yaml.dump(data))

        # Should detect modification
        modified = sync.check_yaml_modified()
        assert len(modified) > 0
        assert any("roadmap.yaml" in m for m in modified)
