"""
CLI commands for managing triangle relationships (Context System V2).

This module provides CLI commands for managing relationships between:
- Tickets (tasks)
- Commits
- Artifacts

Commands:
- task add-artifact: Associate an artifact with a task
- task artifacts: List artifacts associated with a task
- task commits: List commits linked to a task
- task link-commit: Manually link a commit to a task
- artifact history: Show commits that changed an artifact
- validate triangle: Validate consistency across relationship edges
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from vibey.cli.formatters import format_error, format_success, format_warning


def _get_db_path(root_dir: Optional[Path] = None) -> Path:
    """Get the path to the roadmap database."""
    if root_dir is None:
        root_dir = Path.cwd()
    return root_dir / ".vibey" / "roadmap.db"


def _get_connection(db_path: Path) -> sqlite3.Connection:
    """Get a database connection with row factory."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables_exist(conn: sqlite3.Connection) -> None:
    """Ensure the Context System V2 tables exist."""
    # Create ticket_artifact_associations if not exists
    # Uses composite primary key (ticket_id, artifact_id) - no id column
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ticket_artifact_associations (
            ticket_id TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            association_source TEXT NOT NULL CHECK (association_source IN (
                'plan_reference', 'runtime_tracking', 'commit_bootstrap', 'manual', 'criterion_target'
            )),
            added_at TEXT NOT NULL,
            added_by TEXT,
            PRIMARY KEY (ticket_id, artifact_id)
        )
    """)

    # Create ticket_commit_links if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ticket_commit_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            reference_type TEXT NOT NULL CHECK (reference_type IN (
                'task_reference', 'completion_claim'
            )),
            signals_json TEXT,
            aggregate_confidence REAL NOT NULL DEFAULT 1.0,
            linked_at TEXT NOT NULL,
            link_source TEXT NOT NULL,
            UNIQUE(ticket_id, commit_sha, reference_type)
        )
    """)

    # Create commit_artifact_changes if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS commit_artifact_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commit_sha TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            change_type TEXT NOT NULL CHECK (change_type IN (
                'added', 'modified', 'deleted', 'renamed'
            )),
            previous_path TEXT,
            lines_added INTEGER,
            lines_removed INTEGER,
            recorded_at TEXT NOT NULL,
            UNIQUE(commit_sha, artifact_id)
        )
    """)

    # Create indexes if not exist
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ticket_artifact_assoc_ticket
        ON ticket_artifact_associations(ticket_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ticket_commit_links_ticket
        ON ticket_commit_links(ticket_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ticket_commit_links_commit
        ON ticket_commit_links(commit_sha)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_commit_artifact_changes_commit
        ON commit_artifact_changes(commit_sha)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_commit_artifact_changes_artifact
        ON commit_artifact_changes(artifact_id)
    """)

    conn.commit()


def _resolve_artifact_path(
    artifact_path: str,
    conn: sqlite3.Connection
) -> Optional[str]:
    """
    Resolve an artifact path to an artifact ID.

    First checks if the path matches an existing artifact.
    If not found, returns None.

    Args:
        artifact_path: The file path of the artifact
        conn: Database connection

    Returns:
        Artifact ID if found, None otherwise
    """
    # Try to find artifact by path in the paths JSON array
    row = conn.execute("""
        SELECT id FROM artifacts
        WHERE paths LIKE ?
    """, (f'%"{artifact_path}"%',)).fetchone()

    if row:
        return row["id"]

    # Also try with just the path as-is (in case paths is stored differently)
    row = conn.execute("""
        SELECT id FROM artifacts
        WHERE paths LIKE ?
    """, (f'%{artifact_path}%',)).fetchone()

    if row:
        return row["id"]

    return None


def _create_artifact_from_path(
    artifact_path: str,
    conn: sqlite3.Connection
) -> str:
    """
    Create a new artifact entry for a file path.

    Args:
        artifact_path: The file path of the artifact
        conn: Database connection

    Returns:
        The new artifact ID
    """
    from ulid import ULID

    artifact_id = str(ULID())
    now = datetime.now(timezone.utc).isoformat()

    # Determine artifact type from file extension
    path = Path(artifact_path)
    suffix = path.suffix.lower()

    type_mapping = {
        '.py': 'code',
        '.js': 'code',
        '.ts': 'code',
        '.go': 'code',
        '.rs': 'code',
        '.java': 'code',
        '.c': 'code',
        '.cpp': 'code',
        '.h': 'code',
        '.md': 'documentation',
        '.txt': 'documentation',
        '.rst': 'documentation',
        '.yaml': 'config',
        '.yml': 'config',
        '.json': 'config',
        '.toml': 'config',
        '.ini': 'config',
        '.sql': 'schema',
        '.png': 'asset',
        '.jpg': 'asset',
        '.svg': 'asset',
    }

    artifact_type = type_mapping.get(suffix, 'other')

    # Insert the artifact
    conn.execute("""
        INSERT INTO artifacts (
            id, name, description, paths, artifact_type,
            provenance, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        artifact_id,
        path.name,
        f"Auto-created artifact for {artifact_path}",
        json.dumps([artifact_path]),
        artifact_type,
        json.dumps({"provenance_type": "manual", "created_by": "cli"}),
        now,
        now,
    ))

    conn.commit()
    return artifact_id


def task_add_artifact_cmd(
    task_id: str,
    artifact_path: str,
    create_if_missing: bool = True,
) -> int:
    """
    Associate an artifact with a task.

    Creates a TicketArtifactAssociation with source=manual.

    Args:
        task_id: The task/ticket ID (ULID)
        artifact_path: Path to the artifact file
        create_if_missing: If True, create artifact entry if not found

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        db_path = _get_db_path()
        conn = _get_connection(db_path)
        _ensure_tables_exist(conn)

        # Verify task exists
        task_row = conn.execute(
            "SELECT id, title FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not task_row:
            print(format_error(f"Task not found: {task_id}"))
            return 1

        # Resolve artifact path to artifact ID
        artifact_id = _resolve_artifact_path(artifact_path, conn)

        if artifact_id is None:
            if create_if_missing:
                try:
                    artifact_id = _create_artifact_from_path(artifact_path, conn)
                    print(f"   Created new artifact: {artifact_id}")
                except Exception as e:
                    print(format_error(f"Failed to create artifact: {e}"))
                    return 1
            else:
                print(format_error(
                    f"Artifact not found for path: {artifact_path}\n"
                    f"   Use --create-if-missing to create it automatically."
                ))
                return 1

        # Check if association already exists
        existing = conn.execute("""
            SELECT 1 FROM ticket_artifact_associations
            WHERE ticket_id = ? AND artifact_id = ?
        """, (task_id, artifact_id)).fetchone()

        if existing:
            print(format_warning(
                f"Association already exists between task {task_id} "
                f"and artifact {artifact_id}"
            ))
            return 0

        # Create the association
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            INSERT INTO ticket_artifact_associations
            (ticket_id, artifact_id, association_source, added_at, added_by)
            VALUES (?, ?, 'manual', ?, 'cli')
        """, (task_id, artifact_id, now))
        conn.commit()

        print(format_success(
            f"Associated artifact {artifact_path} with task {task_id}"
        ))
        print(f"   Artifact ID: {artifact_id}")
        print(f"   Source: manual")
        return 0

    except FileNotFoundError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to add artifact: {e}"))
        return 1


def task_artifacts_cmd(
    task_id: str,
    output_format: str = "table",
) -> int:
    """
    List all artifacts associated with a task.

    Shows association source and added_at date.

    Args:
        task_id: The task/ticket ID (ULID)
        output_format: Output format (table, json, yaml)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        db_path = _get_db_path()
        conn = _get_connection(db_path)
        _ensure_tables_exist(conn)

        # Verify task exists
        task_row = conn.execute(
            "SELECT id, title FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not task_row:
            print(format_error(f"Task not found: {task_id}"))
            return 1

        # Get all artifacts associated with this task
        rows = conn.execute("""
            SELECT
                taa.artifact_id,
                taa.association_source,
                taa.added_at,
                taa.added_by,
                a.name,
                a.paths,
                a.artifact_type
            FROM ticket_artifact_associations taa
            LEFT JOIN artifacts a ON taa.artifact_id = a.id
            WHERE taa.ticket_id = ?
            ORDER BY taa.added_at DESC
        """, (task_id,)).fetchall()

        if not rows:
            print(f"No artifacts associated with task {task_id}")
            return 0

        if output_format == "json":
            artifacts = []
            for row in rows:
                artifacts.append({
                    "artifact_id": row["artifact_id"],
                    "name": row["name"],
                    "paths": json.loads(row["paths"]) if row["paths"] else [],
                    "artifact_type": row["artifact_type"],
                    "association_source": row["association_source"],
                    "added_at": row["added_at"],
                    "added_by": row["added_by"],
                })
            print(json.dumps(artifacts, indent=2))
        else:
            # Table format
            print(f"\nArtifacts for Task: {task_id}")
            print(f"Task Title: {task_row['title']}")
            print("=" * 80)
            print(f"{'Artifact ID':<28} {'Name':<20} {'Source':<16} {'Added':<20}")
            print("-" * 80)

            for row in rows:
                artifact_id = row["artifact_id"][:26] if row["artifact_id"] else "N/A"
                name = (row["name"] or "Unknown")[:18]
                source = row["association_source"][:14]
                added = row["added_at"][:10] if row["added_at"] else "N/A"
                print(f"{artifact_id:<28} {name:<20} {source:<16} {added:<20}")

            print(f"\nTotal: {len(rows)} artifacts")

        return 0

    except FileNotFoundError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to list artifacts: {e}"))
        return 1


def task_commits_cmd(
    task_id: str,
    output_format: str = "table",
) -> int:
    """
    List all commits linked to a task.

    Shows reference_type, confidence, and commit info.

    Args:
        task_id: The task/ticket ID (ULID)
        output_format: Output format (table, json, yaml)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        db_path = _get_db_path()
        conn = _get_connection(db_path)
        _ensure_tables_exist(conn)

        # Verify task exists
        task_row = conn.execute(
            "SELECT id, title FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not task_row:
            print(format_error(f"Task not found: {task_id}"))
            return 1

        # Get all commits linked to this task from ticket_commit_links
        rows = conn.execute("""
            SELECT
                tcl.commit_sha,
                tcl.reference_type,
                tcl.aggregate_confidence,
                tcl.linked_at,
                tcl.link_source,
                c.commit_message,
                c.author,
                c.committed_at
            FROM ticket_commit_links tcl
            LEFT JOIN commits c ON tcl.commit_sha = c.commit_hash
            WHERE tcl.ticket_id = ?
            ORDER BY tcl.linked_at DESC
        """, (task_id,)).fetchall()

        # Also check entity_commits for legacy commits
        legacy_rows = conn.execute("""
            SELECT
                c.commit_hash,
                c.commit_message,
                c.author,
                c.committed_at
            FROM entity_commits ec
            JOIN commits c ON ec.commit_id = c.id
            WHERE ec.owner_type = 'task' AND ec.owner_id = ?
        """, (task_id,)).fetchall()

        if not rows and not legacy_rows:
            print(f"No commits linked to task {task_id}")
            return 0

        if output_format == "json":
            commits = []
            for row in rows:
                commits.append({
                    "commit_sha": row["commit_sha"],
                    "reference_type": row["reference_type"],
                    "aggregate_confidence": row["aggregate_confidence"],
                    "linked_at": row["linked_at"],
                    "link_source": row["link_source"],
                    "commit_message": row["commit_message"],
                    "author": row["author"],
                    "committed_at": row["committed_at"],
                })
            for row in legacy_rows:
                commits.append({
                    "commit_sha": row["commit_hash"],
                    "reference_type": "legacy",
                    "aggregate_confidence": 1.0,
                    "commit_message": row["commit_message"],
                    "author": row["author"],
                    "committed_at": row["committed_at"],
                })
            print(json.dumps(commits, indent=2))
        else:
            # Table format
            print(f"\nCommits for Task: {task_id}")
            print(f"Task Title: {task_row['title']}")
            print("=" * 90)
            print(f"{'Commit SHA':<12} {'Type':<18} {'Conf':<6} {'Source':<12} {'Message':<40}")
            print("-" * 90)

            for row in rows:
                sha = row["commit_sha"][:10] if row["commit_sha"] else "N/A"
                ref_type = row["reference_type"][:16] if row["reference_type"] else "N/A"
                conf = f"{row['aggregate_confidence']:.1f}" if row["aggregate_confidence"] else "N/A"
                source = (row["link_source"] or "N/A")[:10]
                msg = (row["commit_message"] or "No message")[:38]
                print(f"{sha:<12} {ref_type:<18} {conf:<6} {source:<12} {msg:<40}")

            for row in legacy_rows:
                sha = row["commit_hash"][:10] if row["commit_hash"] else "N/A"
                msg = (row["commit_message"] or "No message")[:38]
                print(f"{sha:<12} {'legacy':<18} {'1.0':<6} {'entity':<12} {msg:<40}")

            total = len(rows) + len(legacy_rows)
            print(f"\nTotal: {total} commits")

        return 0

    except FileNotFoundError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to list commits: {e}"))
        return 1


def task_link_commit_cmd(
    task_id: str,
    commit_sha: str,
    reference_type: str = "task_reference",
) -> int:
    """
    Manually link a commit to a task.

    Creates a TicketCommitLink with source=manual and confidence=1.0.

    Args:
        task_id: The task/ticket ID (ULID)
        commit_sha: The git commit SHA
        reference_type: Type of reference (task_reference or completion_claim)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        db_path = _get_db_path()
        conn = _get_connection(db_path)
        _ensure_tables_exist(conn)

        # Verify task exists
        task_row = conn.execute(
            "SELECT id, title FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not task_row:
            print(format_error(f"Task not found: {task_id}"))
            return 1

        # Validate reference type
        if reference_type not in ("task_reference", "completion_claim"):
            print(format_error(
                f"Invalid reference type: {reference_type}\n"
                f"   Valid types: task_reference, completion_claim"
            ))
            return 1

        # Check if link already exists
        existing = conn.execute("""
            SELECT id FROM ticket_commit_links
            WHERE ticket_id = ? AND commit_sha = ?
        """, (task_id, commit_sha)).fetchone()

        if existing:
            print(format_warning(
                f"Link already exists between task {task_id} "
                f"and commit {commit_sha[:10]}"
            ))
            return 0

        # Create the manual signal
        manual_signal = {
            "matched": True,
            "linked_by": "cli",
            "linked_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 1.0,
        }

        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            INSERT INTO ticket_commit_links
            (ticket_id, commit_sha, reference_type, manual_signal, aggregate_confidence, linked_at, link_source)
            VALUES (?, ?, ?, ?, 1.0, ?, 'manual')
        """, (task_id, commit_sha, reference_type, json.dumps(manual_signal), now))
        conn.commit()

        print(format_success(
            f"Linked commit {commit_sha[:10]} to task {task_id}"
        ))
        print(f"   Reference Type: {reference_type}")
        print(f"   Confidence: 1.0")
        print(f"   Source: manual")
        return 0

    except FileNotFoundError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to link commit: {e}"))
        return 1


def artifact_history_cmd(
    artifact_path: str,
    output_format: str = "table",
) -> int:
    """
    Show all commits that changed an artifact.

    Uses CommitArtifactChange records.

    Args:
        artifact_path: Path to the artifact file
        output_format: Output format (table, json, yaml)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        db_path = _get_db_path()
        conn = _get_connection(db_path)
        _ensure_tables_exist(conn)

        # Resolve artifact path to artifact ID
        artifact_id = _resolve_artifact_path(artifact_path, conn)

        if artifact_id is None:
            print(format_error(f"Artifact not found for path: {artifact_path}"))
            return 1

        # Get all commits that changed this artifact
        rows = conn.execute("""
            SELECT
                cac.commit_sha,
                cac.change_type,
                cac.previous_path,
                cac.lines_added,
                cac.lines_removed,
                cac.recorded_at,
                c.commit_message,
                c.author,
                c.committed_at
            FROM commit_artifact_changes cac
            LEFT JOIN commits c ON cac.commit_sha = c.commit_hash
            WHERE cac.artifact_id = ?
            ORDER BY cac.recorded_at DESC
        """, (artifact_id,)).fetchall()

        if not rows:
            print(f"No commit history found for artifact: {artifact_path}")
            print(f"   Artifact ID: {artifact_id}")
            return 0

        if output_format == "json":
            changes = []
            for row in rows:
                changes.append({
                    "commit_sha": row["commit_sha"],
                    "change_type": row["change_type"],
                    "previous_path": row["previous_path"],
                    "lines_added": row["lines_added"],
                    "lines_removed": row["lines_removed"],
                    "recorded_at": row["recorded_at"],
                    "commit_message": row["commit_message"],
                    "author": row["author"],
                    "committed_at": row["committed_at"],
                })
            print(json.dumps(changes, indent=2))
        else:
            # Table format
            print(f"\nCommit History for: {artifact_path}")
            print(f"Artifact ID: {artifact_id}")
            print("=" * 85)
            print(f"{'Commit SHA':<12} {'Change':<10} {'Lines +/-':<12} {'Date':<12} {'Message':<35}")
            print("-" * 85)

            for row in rows:
                sha = row["commit_sha"][:10] if row["commit_sha"] else "N/A"
                change = row["change_type"][:8] if row["change_type"] else "N/A"
                lines_added = row["lines_added"] or 0
                lines_removed = row["lines_removed"] or 0
                lines = f"+{lines_added}/-{lines_removed}"
                date = row["recorded_at"][:10] if row["recorded_at"] else "N/A"
                msg = (row["commit_message"] or "No message")[:33]
                print(f"{sha:<12} {change:<10} {lines:<12} {date:<12} {msg:<35}")

            print(f"\nTotal: {len(rows)} commits")

        return 0

    except FileNotFoundError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to get artifact history: {e}"))
        return 1


def validate_triangle_cmd(
    task_id: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """
    Validate consistency across all three relationship edges.

    Reports mismatches between ticket associations and commit changes.
    If task_id is provided, validate specific task; otherwise validate all.

    Args:
        task_id: Optional task ID to validate
        verbose: Show detailed validation output

    Returns:
        Exit code (0 for valid, 1 for issues found)
    """
    try:
        db_path = _get_db_path()
        conn = _get_connection(db_path)
        _ensure_tables_exist(conn)

        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        if task_id:
            # Validate specific task
            task_row = conn.execute(
                "SELECT id, title FROM tasks WHERE id = ?",
                (task_id,)
            ).fetchone()

            if not task_row:
                print(format_error(f"Task not found: {task_id}"))
                return 1

            task_ids = [task_id]
        else:
            # Get all tasks
            task_rows = conn.execute("SELECT id FROM tasks").fetchall()
            task_ids = [row["id"] for row in task_rows]

        if verbose:
            print(f"Validating triangle relationships for {len(task_ids)} tasks...")
            print()

        for tid in task_ids:
            task_issues, task_warnings = _validate_task_triangle(conn, tid, verbose)
            issues.extend(task_issues)
            warnings.extend(task_warnings)

        # Summary
        print("\nTriangle Validation Summary")
        print("=" * 60)

        if not issues and not warnings:
            print(format_success("All triangle relationships are consistent!"))
            return 0

        if warnings:
            print(f"\nWarnings: {len(warnings)}")
            print("-" * 40)
            for w in warnings[:10]:  # Limit output
                print(f"  [{w['type']}] {w['message']}")
                if verbose and w.get('details'):
                    print(f"         {w['details']}")
            if len(warnings) > 10:
                print(f"  ... and {len(warnings) - 10} more warnings")

        if issues:
            print(f"\nIssues: {len(issues)}")
            print("-" * 40)
            for i in issues[:10]:  # Limit output
                print(f"  [{i['type']}] {i['message']}")
                if verbose and i.get('details'):
                    print(f"         {i['details']}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more issues")

            return 1

        return 0

    except FileNotFoundError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Validation failed: {e}"))
        return 1


def _validate_task_triangle(
    conn: sqlite3.Connection,
    task_id: str,
    verbose: bool,
) -> tuple:
    """
    Validate triangle consistency for a single task.

    Returns:
        Tuple of (issues, warnings) lists
    """
    issues = []
    warnings = []

    # Get artifacts associated with this task
    artifact_rows = conn.execute("""
        SELECT artifact_id FROM ticket_artifact_associations
        WHERE ticket_id = ?
    """, (task_id,)).fetchall()
    task_artifacts = {row["artifact_id"] for row in artifact_rows}

    # Get commits linked to this task
    commit_rows = conn.execute("""
        SELECT commit_sha FROM ticket_commit_links
        WHERE ticket_id = ?
    """, (task_id,)).fetchall()
    task_commits = {row["commit_sha"] for row in commit_rows}

    # Get artifacts changed by task commits
    commit_artifacts = set()
    for commit_sha in task_commits:
        artifact_change_rows = conn.execute("""
            SELECT artifact_id FROM commit_artifact_changes
            WHERE commit_sha = ?
        """, (commit_sha,)).fetchall()
        for row in artifact_change_rows:
            commit_artifacts.add(row["artifact_id"])

    # Check for orphaned associations
    # Artifacts associated with task but never touched by any task commit
    if task_artifacts and task_commits and commit_artifacts:
        orphaned = task_artifacts - commit_artifacts
        if orphaned:
            warnings.append({
                "type": "orphaned_association",
                "message": f"Task {task_id}: {len(orphaned)} artifacts associated but not changed by any commit",
                "details": f"Artifact IDs: {list(orphaned)[:3]}..." if len(orphaned) > 3 else f"Artifact IDs: {list(orphaned)}"
            })

    # Check for undocumented changes
    # Artifacts changed by commits but not associated with task
    if task_commits and commit_artifacts:
        undocumented = commit_artifacts - task_artifacts
        if undocumented:
            warnings.append({
                "type": "undocumented_change",
                "message": f"Task {task_id}: {len(undocumented)} artifacts changed but not associated",
                "details": f"Artifact IDs: {list(undocumented)[:3]}..." if len(undocumented) > 3 else f"Artifact IDs: {list(undocumented)}"
            })

    # Check for commits without artifact changes
    for commit_sha in task_commits:
        artifact_change_count = conn.execute("""
            SELECT COUNT(*) as cnt FROM commit_artifact_changes
            WHERE commit_sha = ?
        """, (commit_sha,)).fetchone()["cnt"]

        if artifact_change_count == 0:
            warnings.append({
                "type": "empty_commit",
                "message": f"Task {task_id}: Commit {commit_sha[:10]} has no artifact changes recorded",
                "details": None
            })

    if verbose and (task_artifacts or task_commits):
        print(f"  Task {task_id}:")
        print(f"    Artifacts: {len(task_artifacts)}")
        print(f"    Commits: {len(task_commits)}")
        print(f"    Commit artifacts: {len(commit_artifacts)}")

    return issues, warnings
