"""
Tests for artifacts table schema.

Tests cover:
- Table creation and structure
- Column constraints and types
- Index creation
- View creation (where applicable)
- Migration script functionality
- Foreign key constraints
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def conn(temp_db):
    """Create a connection to temporary database."""
    connection = sqlite3.connect(temp_db)
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


@pytest.fixture
def schema_conn(conn):
    """Connection with schema created."""
    from vibey.roadmap.database.schema import get_schema_ddl, get_index_ddl
    conn.executescript(get_schema_ddl())
    conn.executescript(get_index_ddl())
    yield conn


# =============================================================================
# TABLE CREATION TESTS
# =============================================================================


class TestArtifactsTableCreation:
    """Tests for artifacts table creation."""

    def test_table_created(self, schema_conn):
        """Test that artifacts table is created."""
        result = schema_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='artifacts'"
        ).fetchone()
        assert result is not None
        assert result["name"] == "artifacts"

    def test_table_in_expected_tables(self):
        """Test that artifacts is in EXPECTED_TABLES."""
        from vibey.roadmap.database.schema import EXPECTED_TABLES
        assert "artifacts" in EXPECTED_TABLES

    def test_schema_validates_with_artifacts(self, schema_conn):
        """Test that schema validation passes with artifacts table."""
        from vibey.roadmap.database.schema import validate_schema
        result = validate_schema(schema_conn)
        assert result["valid"] is True
        assert "artifacts" not in result["missing_tables"]


# =============================================================================
# COLUMN STRUCTURE TESTS
# =============================================================================


class TestArtifactsTableColumns:
    """Tests for artifacts table column structure."""

    def test_has_id_column(self, schema_conn):
        """Test that id column exists and is primary key."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}
        assert "id" in columns
        assert columns["id"]["pk"] == 1  # Primary key
        assert columns["id"]["type"] == "TEXT"

    def test_has_name_column(self, schema_conn):
        """Test that name column exists and is NOT NULL."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}
        assert "name" in columns
        assert columns["name"]["notnull"] == 1
        assert columns["name"]["type"] == "TEXT"

    def test_has_paths_column(self, schema_conn):
        """Test that paths column exists and is NOT NULL."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}
        assert "paths" in columns
        assert columns["paths"]["notnull"] == 1
        assert columns["paths"]["type"] == "TEXT"

    def test_has_artifact_type_column(self, schema_conn):
        """Test that artifact_type column exists and is NOT NULL."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}
        assert "artifact_type" in columns
        assert columns["artifact_type"]["notnull"] == 1
        assert columns["artifact_type"]["type"] == "TEXT"

    def test_has_provenance_column(self, schema_conn):
        """Test that provenance column exists and is NOT NULL."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}
        assert "provenance" in columns
        assert columns["provenance"]["notnull"] == 1
        assert columns["provenance"]["type"] == "TEXT"

    def test_has_state_columns(self, schema_conn):
        """Test that file_exists and is_stale columns exist with defaults."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}

        assert "file_exists" in columns
        assert columns["file_exists"]["notnull"] == 1
        assert columns["file_exists"]["dflt_value"] == "1"

        assert "is_stale" in columns
        assert columns["is_stale"]["notnull"] == 1
        assert columns["is_stale"]["dflt_value"] == "0"

    def test_has_timestamp_columns(self, schema_conn):
        """Test that timestamp columns exist and are NOT NULL."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        columns = {row["name"]: row for row in result}

        assert "created_at" in columns
        assert columns["created_at"]["notnull"] == 1

        assert "updated_at" in columns
        assert columns["updated_at"]["notnull"] == 1

    def test_has_optional_columns(self, schema_conn):
        """Test that optional columns exist."""
        result = schema_conn.execute("PRAGMA table_info(artifacts)").fetchall()
        column_names = [row["name"] for row in result]

        optional_columns = [
            "description",
            "content_hash",
            "last_verified",
            "artifact_subtype",
            "documents_artifact_id",
            "depends_on_artifact_ids",
            "documented_source_hash",
        ]
        for col in optional_columns:
            assert col in column_names, f"Missing optional column: {col}"


# =============================================================================
# CONSTRAINT TESTS
# =============================================================================


class TestArtifactsTableConstraints:
    """Tests for artifacts table constraints."""

    def test_artifact_type_check_constraint(self, schema_conn):
        """Test that artifact_type has CHECK constraint."""
        now = datetime.now(timezone.utc).isoformat()
        valid_types = [
            "code", "test", "config", "documentation", "context",
            "agent", "workflow", "template", "data", "asset", "schema", "other"
        ]

        # Valid types should work
        for i, artifact_type in enumerate(valid_types):
            schema_conn.execute(
                """
                INSERT INTO artifacts (id, name, paths, artifact_type, provenance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (f"art-{i:03d}", f"Test {artifact_type}", "[]", artifact_type, "{}", now, now)
            )

        # Invalid type should fail
        with pytest.raises(sqlite3.IntegrityError):
            schema_conn.execute(
                """
                INSERT INTO artifacts (id, name, paths, artifact_type, provenance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("art-invalid", "Invalid", "[]", "invalid_type", "{}", now, now)
            )

    def test_foreign_key_constraint(self, schema_conn):
        """Test that documents_artifact_id has foreign key constraint."""
        # Enable foreign keys
        schema_conn.execute("PRAGMA foreign_keys = ON")

        now = datetime.now(timezone.utc).isoformat()

        # Create source artifact
        schema_conn.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("source-art", "Source", "[]", "code", "{}", now, now)
        )

        # Create doc artifact referencing source - should work
        schema_conn.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, documents_artifact_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("doc-art", "Doc", "[]", "documentation", "{}", "source-art", now, now)
        )

        # Referencing non-existent artifact should fail
        with pytest.raises(sqlite3.IntegrityError):
            schema_conn.execute(
                """
                INSERT INTO artifacts (id, name, paths, artifact_type, provenance, documents_artifact_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("bad-doc", "Bad Doc", "[]", "documentation", "{}", "nonexistent", now, now)
            )


# =============================================================================
# INDEX TESTS
# =============================================================================


class TestArtifactsIndexes:
    """Tests for artifacts table indexes."""

    def test_type_index_exists(self, schema_conn):
        """Test that idx_artifacts_type index exists."""
        result = schema_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_artifacts_type'"
        ).fetchone()
        assert result is not None

    def test_documents_index_exists(self, schema_conn):
        """Test that idx_artifacts_documents index exists."""
        result = schema_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_artifacts_documents'"
        ).fetchone()
        assert result is not None

    def test_stale_index_exists(self, schema_conn):
        """Test that idx_artifacts_stale partial index exists."""
        result = schema_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_artifacts_stale'"
        ).fetchone()
        assert result is not None

    def test_exists_index_exists(self, schema_conn):
        """Test that idx_artifacts_exists partial index exists."""
        result = schema_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_artifacts_exists'"
        ).fetchone()
        assert result is not None


# =============================================================================
# INSERT AND QUERY TESTS
# =============================================================================


class TestArtifactsInsertQuery:
    """Tests for inserting and querying artifacts."""

    def test_insert_minimal_artifact(self, schema_conn):
        """Test inserting artifact with minimal fields."""
        now = datetime.now(timezone.utc).isoformat()
        schema_conn.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("art-001", "Test Artifact", json.dumps(["src/test.py"]), "code", "{}", now, now)
        )

        result = schema_conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", ("art-001",)
        ).fetchone()

        assert result["id"] == "art-001"
        assert result["name"] == "Test Artifact"
        assert result["artifact_type"] == "code"
        assert result["file_exists"] == 1  # Default
        assert result["is_stale"] == 0  # Default

    def test_insert_full_artifact(self, schema_conn):
        """Test inserting artifact with all fields."""
        now = datetime.now(timezone.utc).isoformat()
        provenance = json.dumps({
            "provenance_type": "ticket_created",
            "created_by_ticket_id": "task-001"
        })

        schema_conn.execute(
            """
            INSERT INTO artifacts (
                id, name, description, paths, content_hash, last_verified,
                artifact_type, artifact_subtype, provenance,
                documents_artifact_id, depends_on_artifact_ids,
                file_exists, is_stale, documented_source_hash,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "art-full", "Full Artifact", "A complete artifact",
                json.dumps(["src/main.py", "src/utils.py"]),
                "abc123hash", now,
                "code", "python_module", provenance,
                None, json.dumps(["art-dep1", "art-dep2"]),
                1, 0, None,
                now, now
            )
        )

        result = schema_conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", ("art-full",)
        ).fetchone()

        assert result["description"] == "A complete artifact"
        assert result["content_hash"] == "abc123hash"
        assert json.loads(result["paths"]) == ["src/main.py", "src/utils.py"]
        assert json.loads(result["depends_on_artifact_ids"]) == ["art-dep1", "art-dep2"]

    def test_query_by_type(self, schema_conn):
        """Test querying artifacts by type."""
        now = datetime.now(timezone.utc).isoformat()

        # Insert various types
        for i, atype in enumerate(["code", "code", "test", "documentation"]):
            schema_conn.execute(
                """
                INSERT INTO artifacts (id, name, paths, artifact_type, provenance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (f"art-{i}", f"Artifact {i}", "[]", atype, "{}", now, now)
            )

        # Query code artifacts
        result = schema_conn.execute(
            "SELECT COUNT(*) as cnt FROM artifacts WHERE artifact_type = 'code'"
        ).fetchone()
        assert result["cnt"] == 2

    def test_query_stale_artifacts(self, schema_conn):
        """Test querying stale artifacts."""
        now = datetime.now(timezone.utc).isoformat()

        # Insert stale and non-stale
        schema_conn.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, is_stale, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("art-stale", "Stale", "[]", "documentation", "{}", 1, now, now)
        )
        schema_conn.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, is_stale, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("art-fresh", "Fresh", "[]", "documentation", "{}", 0, now, now)
        )

        result = schema_conn.execute(
            "SELECT * FROM artifacts WHERE is_stale = 1"
        ).fetchall()
        assert len(result) == 1
        assert result[0]["id"] == "art-stale"


# =============================================================================
# VIEW TESTS (Self-contained views only)
# =============================================================================


class TestDocumentationGraphView:
    """Tests for v_documentation_graph view."""

    @pytest.fixture
    def schema_with_views(self, schema_conn):
        """Create schema with views."""
        from vibey.roadmap.database.schema import get_views_ddl

        # Create only the self-contained views (not ones needing criteria table)
        schema_conn.execute("""
            CREATE VIEW IF NOT EXISTS v_documentation_graph AS
            SELECT
                doc.id AS doc_id,
                doc.name AS doc_name,
                doc.artifact_type AS doc_type,
                doc.is_stale,
                src.id AS source_id,
                src.name AS source_name,
                src.artifact_type AS source_type,
                src.content_hash AS source_hash,
                doc.documented_source_hash AS documented_hash,
                CASE
                    WHEN src.content_hash IS NOT NULL
                         AND doc.documented_source_hash IS NOT NULL
                         AND src.content_hash != doc.documented_source_hash THEN 1
                    ELSE 0
                END AS needs_update
            FROM artifacts doc
            JOIN artifacts src ON doc.documents_artifact_id = src.id
            WHERE doc.documents_artifact_id IS NOT NULL
        """)
        schema_conn.execute("""
            CREATE VIEW IF NOT EXISTS v_stale_documentation AS
            SELECT * FROM v_documentation_graph
            WHERE needs_update = 1 OR is_stale = 1
        """)
        return schema_conn

    def test_documentation_graph_empty(self, schema_with_views):
        """Test documentation graph view with no data."""
        result = schema_with_views.execute(
            "SELECT * FROM v_documentation_graph"
        ).fetchall()
        assert len(result) == 0

    def test_documentation_graph_with_data(self, schema_with_views):
        """Test documentation graph view with doc/source relationship."""
        now = datetime.now(timezone.utc).isoformat()

        # Create source artifact
        schema_with_views.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, content_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("source-001", "Source Code", "[]", "code", "{}", "hash123", now, now)
        )

        # Create documentation artifact
        schema_with_views.execute(
            """
            INSERT INTO artifacts (
                id, name, paths, artifact_type, provenance,
                documents_artifact_id, documented_source_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("doc-001", "API Docs", "[]", "documentation", "{}", "source-001", "hash123", now, now)
        )

        result = schema_with_views.execute(
            "SELECT * FROM v_documentation_graph"
        ).fetchall()

        assert len(result) == 1
        assert result[0]["doc_id"] == "doc-001"
        assert result[0]["source_id"] == "source-001"
        assert result[0]["needs_update"] == 0  # Hashes match

    def test_stale_documentation_view(self, schema_with_views):
        """Test stale documentation view detects hash changes."""
        now = datetime.now(timezone.utc).isoformat()

        # Create source with updated hash
        schema_with_views.execute(
            """
            INSERT INTO artifacts (id, name, paths, artifact_type, provenance, content_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("source-002", "Updated Source", "[]", "code", "{}", "new_hash", now, now)
        )

        # Create doc with old hash reference
        schema_with_views.execute(
            """
            INSERT INTO artifacts (
                id, name, paths, artifact_type, provenance,
                documents_artifact_id, documented_source_hash, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("doc-002", "Outdated Docs", "[]", "documentation", "{}", "source-002", "old_hash", now, now)
        )

        result = schema_with_views.execute(
            "SELECT * FROM v_stale_documentation"
        ).fetchall()

        assert len(result) == 1
        assert result[0]["doc_id"] == "doc-002"
        assert result[0]["needs_update"] == 1


# =============================================================================
# MIGRATION SCRIPT TESTS
# =============================================================================


class TestMigrationScript:
    """Tests for the add_artifacts migration script."""

    def test_migrate_creates_table(self, temp_db):
        """Test that migration creates artifacts table."""
        from vibey.roadmap.database.migrations.add_artifacts import migrate, table_exists

        conn = sqlite3.connect(temp_db)

        # Table shouldn't exist yet
        assert not table_exists(conn, "artifacts")

        # Run migration
        result = migrate(conn)

        assert result["success"] is True
        assert result["table_created"] is True
        assert result["indexes_created"] is True
        assert table_exists(conn, "artifacts")

        conn.close()

    def test_migrate_idempotent(self, temp_db):
        """Test that migration is idempotent."""
        from vibey.roadmap.database.migrations.add_artifacts import migrate

        conn = sqlite3.connect(temp_db)

        # Run twice
        result1 = migrate(conn)
        result2 = migrate(conn)

        assert result1["success"] is True
        assert result1["table_created"] is True

        assert result2["success"] is True
        assert result2["already_exists"] is True
        assert result2["table_created"] is False

        conn.close()

    def test_rollback_removes_table(self, temp_db):
        """Test that rollback removes artifacts table."""
        from vibey.roadmap.database.migrations.add_artifacts import migrate, rollback, table_exists

        conn = sqlite3.connect(temp_db)

        # Create table
        migrate(conn)
        assert table_exists(conn, "artifacts")

        # Rollback
        result = rollback(conn)
        assert result["success"] is True
        assert not table_exists(conn, "artifacts")

        conn.close()


# =============================================================================
# SCHEMA FUNCTION TESTS
# =============================================================================


class TestSchemaFunctions:
    """Tests for schema helper functions."""

    def test_get_views_ddl_returns_string(self):
        """Test that get_views_ddl returns valid SQL."""
        from vibey.roadmap.database.schema import get_views_ddl
        ddl = get_views_ddl()
        assert isinstance(ddl, str)
        assert "CREATE VIEW" in ddl
        assert "v_documentation_graph" in ddl
        assert "v_stale_documentation" in ddl
        assert "v_orphan_artifacts" in ddl
        assert "v_artifact_criteria" in ddl

    def test_create_schema_with_views_flag(self, temp_db):
        """Test that create_schema respects include_views flag."""
        from vibey.roadmap.database.schema import create_schema

        conn = sqlite3.connect(temp_db)

        # Create without views
        create_schema(conn, include_views=False)

        # Views should not exist
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        ).fetchall()
        # May have 0 views
        view_names = [r[0] for r in result]
        assert "v_documentation_graph" not in view_names

        conn.close()
