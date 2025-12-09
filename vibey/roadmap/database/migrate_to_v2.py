#!/usr/bin/env python3
"""
Database schema migration from v1.0.0 to v2.0.0.

This script migrates from the legacy 27-table schema to the unified completables + criteria schema.

Migration Overview:
1. Create backup of existing database
2. Create schema_v2 tables (completables, criteria)
3. Migrate data from legacy tables → completables table
4. Convert blocking relationships → criteria rows
5. Convert deliverables → FileExistsTarget criteria
6. Update database_state to v2.0.0
7. Validate migration success

LEGACY SCHEMA (v1.0.0 - 27 tables):
- Core: roadmaps, tracks, sprints, tasks
- Relationships: external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on
- Quality: quality_gates, development_gates
- Supporting: deliverables, entity_deliverables, commits, entity_commits, assigned_agents, standards, strategic_value
- Roadmap: version_history, activity_log
- Summaries: track_summaries, sprint_summaries, task_summaries
- Sync: yaml_checksums, database_state, sync_conflicts
- Audit: audit_trail
- Artifacts: artifacts

TARGET SCHEMA (v2.0.0 - 2 tables + 14 views):
- completables (single table for tickets + artifacts)
- criteria (unified blocking system)
"""

import json
import sqlite3
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .connection import get_connection


def create_backup(db_path: Path) -> Path:
    """
    Create timestamped backup of database before migration.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}.backup_{timestamp}{db_path.suffix}"

    shutil.copy2(db_path, backup_path)
    print(f"✅ Created backup: {backup_path}")

    return backup_path


def execute_schema_ddl(conn: sqlite3.Connection, schema_path: Path) -> None:
    """
    Execute schema DDL from file.

    Args:
        conn: Database connection
        schema_path: Path to schema SQL file
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema_sql = schema_path.read_text()
    conn.executescript(schema_sql)

    print(f"✅ Executed schema DDL: {schema_path}")


def migrate_roadmaps(conn: sqlite3.Connection) -> int:
    """
    Migrate roadmaps table → completables (ticket_type='roadmap').

    Args:
        conn: Database connection

    Returns:
        Number of roadmaps migrated
    """
    cursor = conn.execute("""
        SELECT
            id, name, version, status, blocked, created, started, completed, deployed,
            version_strategy, metadata
        FROM roadmaps
    """)

    count = 0
    for row in cursor:
        (id_, name, version, status, blocked, created, started, completed, deployed,
         version_strategy, metadata) = row

        conn.execute("""
            INSERT INTO completables (
                id, name, completable_type, ticket_type, status,
                created_at, started_at, completed_at, deployed_at,
                version, version_strategy_json, metadata_json,
                updated_at, sequence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_, name, 'ticket', 'roadmap', status,
            created, started, completed, deployed,
            version, version_strategy, metadata,
            datetime.now(timezone.utc).isoformat(), 0
        ))
        count += 1

    print(f"✅ Migrated {count} roadmaps")
    return count


def migrate_tracks(conn: sqlite3.Connection) -> int:
    """
    Migrate tracks table → completables (ticket_type='track').

    Args:
        conn: Database connection

    Returns:
        Number of tracks migrated
    """
    cursor = conn.execute("""
        SELECT
            id, roadmap_id, name, status, blocked, priority, created, started, completed,
            estimated_duration, dependencies_json, standards_json, strategic_value_json, metadata
        FROM tracks
    """)

    count = 0
    for row in cursor:
        (id_, roadmap_id, name, status, blocked, priority, created, started, completed,
         estimated_duration, dependencies_json, standards_json, strategic_value_json, metadata) = row

        conn.execute("""
            INSERT INTO completables (
                id, name, completable_type, ticket_type, parent_id, status,
                created_at, started_at, completed_at, priority, estimated_duration,
                strategic_value_json, metadata_json, requirements_local_json,
                updated_at, sequence, legacy_roadmap_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_, name, 'ticket', 'track', roadmap_id, status,
            created, started, completed, priority, estimated_duration,
            strategic_value_json, metadata, dependencies_json,
            datetime.now(timezone.utc).isoformat(), 0, roadmap_id
        ))
        count += 1

    print(f"✅ Migrated {count} tracks")
    return count


def migrate_sprints(conn: sqlite3.Connection) -> int:
    """
    Migrate sprints table → completables (ticket_type='sprint').

    Args:
        conn: Database connection

    Returns:
        Number of sprints migrated
    """
    cursor = conn.execute("""
        SELECT
            id, track_id, roadmap_id, name, status, blocked, blocked_reason,
            created, started, completion_gate_check_at, completed,
            production_gate_check_at, production_ready_at, deployed_at,
            plan_file, description, goal, estimated_duration, notes,
            dependencies_json, standards_json, development_gates_json,
            success_criteria_json, risks_json, deliverables_json,
            quality_gates_json, progress_json, tasks_json, metadata
        FROM sprints
    """)

    count = 0
    for row in cursor:
        (id_, track_id, roadmap_id, name, status, blocked, blocked_reason,
         created, started, completion_gate_check_at, completed,
         production_gate_check_at, production_ready_at, deployed_at,
         plan_file, description, goal, estimated_duration, notes,
         dependencies_json, standards_json, development_gates_json,
         success_criteria_json, risks_json, deliverables_json,
         quality_gates_json, progress_json, tasks_json, metadata) = row

        conn.execute("""
            INSERT INTO completables (
                id, name, description, completable_type, ticket_type, parent_id, status,
                created_at, started_at, completed_at,
                completion_gate_check_at, production_gate_check_at,
                production_ready_at, deployed_at,
                plan_file, goal, estimated_duration, blocked_reason,
                success_criteria_json, development_gates_json,
                requirements_local_json, metadata_json,
                updated_at, sequence, legacy_track_id, legacy_roadmap_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_, name, description, 'ticket', 'sprint', track_id, status,
            created, started, completed,
            completion_gate_check_at, production_gate_check_at,
            production_ready_at, deployed_at,
            plan_file, goal, estimated_duration, blocked_reason,
            success_criteria_json, development_gates_json,
            dependencies_json, metadata,
            datetime.now(timezone.utc).isoformat(), 0, track_id, roadmap_id
        ))
        count += 1

    print(f"✅ Migrated {count} sprints")
    return count


def migrate_tasks(conn: sqlite3.Connection) -> int:
    """
    Migrate tasks table → completables (ticket_type='task').

    Args:
        conn: Database connection

    Returns:
        Number of tasks migrated
    """
    cursor = conn.execute("""
        SELECT
            id, sprint_id, track_id, roadmap_id, task_type, title, description,
            status, blocked, created, started, completed,
            assigned_agent, priority, phase_label, estimated_tokens, actual_tokens,
            complexity, gate_info, audit_results,
            commits_json, deliverables_json, dependencies_json,
            standards_json, assigned_agents_json, estimated_duration, metadata
        FROM tasks
    """)

    count = 0
    for row in cursor:
        (id_, sprint_id, track_id, roadmap_id, task_type, title, description,
         status, blocked, created, started, completed,
         assigned_agent, priority, phase_label, estimated_tokens, actual_tokens,
         complexity, gate_info, audit_results,
         commits_json, deliverables_json, dependencies_json,
         standards_json, assigned_agents_json, estimated_duration, metadata) = row

        conn.execute("""
            INSERT INTO completables (
                id, name, description, completable_type, ticket_type, parent_id, status,
                created_at, started_at, completed_at,
                task_type_detail, priority, phase_label,
                estimated_tokens, actual_tokens, complexity,
                gate_info_json, audit_results_json,
                commits_json, requirements_local_json, assigned_agents_json,
                estimated_duration, metadata_json,
                updated_at, sequence, legacy_sprint_id, legacy_track_id, legacy_roadmap_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_, title, description, 'ticket', 'task', sprint_id, status,
            created, started, completed,
            task_type, priority, phase_label,
            estimated_tokens, actual_tokens, complexity,
            gate_info, audit_results,
            commits_json, dependencies_json, assigned_agents_json,
            estimated_duration, metadata,
            datetime.now(timezone.utc).isoformat(), 0, sprint_id, track_id, roadmap_id
        ))
        count += 1

    print(f"✅ Migrated {count} tasks")
    return count


def migrate_artifacts(conn: sqlite3.Connection) -> int:
    """
    Migrate artifacts table → completables (completable_type='artifact').

    Args:
        conn: Database connection

    Returns:
        Number of artifacts migrated
    """
    cursor = conn.execute("""
        SELECT
            id, name, description, paths, content_hash, last_verified,
            artifact_type, artifact_subtype, provenance,
            documents_artifact_id, depends_on_artifact_ids,
            file_exists, is_stale, documented_source_hash,
            created_at, updated_at
        FROM artifacts
    """)

    count = 0
    for row in cursor:
        (id_, name, description, paths, content_hash, last_verified,
         artifact_type, artifact_subtype, provenance,
         documents_artifact_id, depends_on_artifact_ids,
         file_exists, is_stale, documented_source_hash,
         created_at, updated_at) = row

        # Set status based on file_exists
        status = 'completed' if file_exists else 'not_started'

        conn.execute("""
            INSERT INTO completables (
                id, name, description, completable_type, status,
                created_at, updated_at,
                paths_json, content_hash, artifact_type, artifact_subtype,
                provenance_json, documents_artifact_id, depends_on_artifact_ids_json,
                metadata_json, sequence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_, name, description, 'artifact', status,
            created_at, updated_at,
            paths, content_hash, artifact_type, artifact_subtype,
            provenance, documents_artifact_id, depends_on_artifact_ids,
            json.dumps({"is_stale": is_stale, "documented_source_hash": documented_source_hash}),
            0
        ))
        count += 1

    print(f"✅ Migrated {count} artifacts")
    return count


def migrate_blocked_by_to_criteria(conn: sqlite3.Connection) -> int:
    """
    Convert entity_blocked_by relationships → CompletableTarget criteria.

    Args:
        conn: Database connection

    Returns:
        Number of criteria created
    """
    cursor = conn.execute("""
        SELECT
            blocked_type, blocked_id, blocker_type, blocker_id,
            required_status, blocks_transition_to, reason
        FROM entity_blocked_by
    """)

    count = 0
    for row in cursor:
        (blocked_type, blocked_id, blocker_type, blocker_id,
         required_status, blocks_transition_to, reason) = row

        # Generate criterion ID
        criterion_id = f"crit-{blocked_id}-{blocker_id}"

        # Create CompletableTarget criterion
        target_json = json.dumps({
            "type": "completable",
            "completable_id": blocker_id,
            "required_status": required_status or "completed"
        })

        description = reason or f"{blocker_type} {blocker_id} must reach {required_status or 'completed'}"

        conn.execute("""
            INSERT INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id, blocked_id, description, 1,
            blocks_transition_to or 'in_progress', 'completable', target_json,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        count += 1

    print(f"✅ Created {count} CompletableTarget criteria from entity_blocked_by")
    return count


def migrate_depends_on_to_criteria(conn: sqlite3.Connection) -> int:
    """
    Convert entity_depends_on relationships → CompletableTarget criteria.

    Args:
        conn: Database connection

    Returns:
        Number of criteria created
    """
    cursor = conn.execute("""
        SELECT
            dependent_type, dependent_id, dependency_type, dependency_id, reason
        FROM entity_depends_on
    """)

    count = 0
    for row in cursor:
        (dependent_type, dependent_id, dependency_type, dependency_id, reason) = row

        # Generate criterion ID
        criterion_id = f"dep-{dependent_id}-{dependency_id}"

        # Create CompletableTarget criterion (soft dependency)
        target_json = json.dumps({
            "type": "completable",
            "completable_id": dependency_id,
            "required_status": "completed"
        })

        description = reason or f"Depends on {dependency_type} {dependency_id}"

        conn.execute("""
            INSERT INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id, dependent_id, description, 0,  # required=0 for soft dependency
            'completed', 'completable', target_json,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        count += 1

    print(f"✅ Created {count} CompletableTarget criteria from entity_depends_on")
    return count


def migrate_deliverables_to_criteria(conn: sqlite3.Connection) -> int:
    """
    Convert deliverables → FileExistsTarget criteria.

    Args:
        conn: Database connection

    Returns:
        Number of criteria created
    """
    cursor = conn.execute("""
        SELECT
            ed.owner_type, ed.owner_id, d.description, d.artifact_path, d.status
        FROM entity_deliverables ed
        JOIN deliverables d ON ed.deliverable_id = d.id
        WHERE d.artifact_path IS NOT NULL
    """)

    count = 0
    for row in cursor:
        (owner_type, owner_id, description, artifact_path, status) = row

        # Generate criterion ID
        criterion_id = f"file-{owner_id}-{count}"

        # Create FileExistsTarget criterion
        target_json = json.dumps({
            "type": "file_exists",
            "paths": [artifact_path],
            "all_required": True
        })

        conn.execute("""
            INSERT INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                is_met, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id, owner_id, description, 1,
            'completed', 'file_exists', target_json,
            1 if status == 'completed' else 0,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        count += 1

    print(f"✅ Created {count} FileExistsTarget criteria from deliverables")
    return count


def migrate_quality_gates_to_criteria(conn: sqlite3.Connection) -> int:
    """
    Convert quality_gates → ThresholdTarget criteria.

    Args:
        conn: Database connection

    Returns:
        Number of criteria created
    """
    cursor = conn.execute("""
        SELECT
            owner_type, owner_id, name, description, threshold, blocking, status, score
        FROM quality_gates
    """)

    count = 0
    for row in cursor:
        (owner_type, owner_id, name, description, threshold, blocking, status, score) = row

        # Generate criterion ID
        criterion_id = f"gate-{owner_id}-{count}"

        # Create ThresholdTarget criterion
        target_json = json.dumps({
            "type": "threshold",
            "metric_name": name,
            "threshold": threshold,
            "comparison": ">="
        })

        conn.execute("""
            INSERT INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                is_met, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id, owner_id, description or name, blocking,
            'completed', 'threshold', target_json,
            1 if status == 'passed' else 0 if status == 'failed' else None,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        count += 1

    print(f"✅ Created {count} ThresholdTarget criteria from quality_gates")
    return count


def update_database_version(conn: sqlite3.Connection) -> None:
    """
    Update database_state to v2.0.0.

    Args:
        conn: Database connection
    """
    conn.execute("""
        UPDATE database_state
        SET schema_version = '2.0.0',
            last_yaml_load = ?
        WHERE id = 1
    """, (datetime.now(timezone.utc).isoformat(),))

    print("✅ Updated database version to 2.0.0")


def validate_migration(conn: sqlite3.Connection) -> dict:
    """
    Validate migration success.

    Args:
        conn: Database connection

    Returns:
        Dictionary with validation results
    """
    results = {}

    # Count legacy tables
    legacy_counts = {}
    for table in ['roadmaps', 'tracks', 'sprints', 'tasks', 'artifacts']:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        legacy_counts[table] = count

    # Count completables by type
    completables_counts = {}
    for ticket_type in ['roadmap', 'track', 'sprint', 'task']:
        count = conn.execute(
            "SELECT COUNT(*) FROM completables WHERE completable_type = 'ticket' AND ticket_type = ?",
            (ticket_type,)
        ).fetchone()[0]
        completables_counts[ticket_type] = count

    artifact_count = conn.execute(
        "SELECT COUNT(*) FROM completables WHERE completable_type = 'artifact'"
    ).fetchone()[0]
    completables_counts['artifact'] = artifact_count

    # Count criteria by target type
    criteria_counts = {}
    cursor = conn.execute("SELECT target_type, COUNT(*) FROM criteria GROUP BY target_type")
    for target_type, count in cursor:
        criteria_counts[target_type] = count

    total_criteria = conn.execute("SELECT COUNT(*) FROM criteria").fetchone()[0]

    # Validation checks
    all_matched = True
    for key in ['roadmap', 'track', 'sprint', 'task']:
        table_key = f"{key}s" if key != 'task' else 'tasks'
        if legacy_counts.get(table_key, 0) != completables_counts.get(key, 0):
            all_matched = False
            print(f"⚠️  Mismatch: {table_key} ({legacy_counts.get(table_key, 0)}) vs completables.{key} ({completables_counts.get(key, 0)})")

    if legacy_counts.get('artifacts', 0) != completables_counts.get('artifact', 0):
        all_matched = False
        print(f"⚠️  Mismatch: artifacts ({legacy_counts.get('artifacts', 0)}) vs completables.artifact ({completables_counts.get('artifact', 0)})")

    results = {
        "success": all_matched,
        "legacy_counts": legacy_counts,
        "completables_counts": completables_counts,
        "criteria_counts": criteria_counts,
        "total_criteria": total_criteria,
        "schema_version": conn.execute("SELECT schema_version FROM database_state WHERE id = 1").fetchone()[0]
    }

    if all_matched:
        print("\n✅ Migration validation PASSED - all counts match!")
    else:
        print("\n⚠️  Migration validation FAILED - count mismatches detected")

    print(f"\nMigration Summary:")
    print(f"  Roadmaps: {completables_counts.get('roadmap', 0)}")
    print(f"  Tracks: {completables_counts.get('track', 0)}")
    print(f"  Sprints: {completables_counts.get('sprint', 0)}")
    print(f"  Tasks: {completables_counts.get('task', 0)}")
    print(f"  Artifacts: {completables_counts.get('artifact', 0)}")
    print(f"  Criteria: {total_criteria}")
    print(f"  Schema Version: {results['schema_version']}")

    return results


def run_migration(
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    schema_file: Optional[Path] = None,
    dry_run: bool = False
) -> dict:
    """
    Run complete migration from v1.0.0 to v2.0.0.

    Args:
        db_path: Path to database file
        base_dir: Base directory containing .vibey folder
        schema_file: Path to schema_v2.sql file
        dry_run: If True, create backup but don't modify database

    Returns:
        Dictionary with migration results
    """
    # Get connection
    if db_path is None:
        if base_dir is None:
            base_dir = Path.cwd()
        db_path = base_dir / ".vibey" / "roadmap.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Default schema file location
    if schema_file is None:
        schema_file = Path(__file__).parent / "schema_v2.sql"

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    print(f"\n{'='*80}")
    print(f"DATABASE MIGRATION: v1.0.0 → v2.0.0")
    print(f"{'='*80}\n")
    print(f"Database: {db_path}")
    print(f"Schema: {schema_file}")
    print(f"Dry Run: {dry_run}\n")

    # Step 1: Create backup
    print("Step 1: Creating backup...")
    backup_path = create_backup(db_path)

    if dry_run:
        print("\n✅ Dry run complete - backup created, no changes made")
        return {"success": True, "backup_path": backup_path, "dry_run": True}

    # Get connection
    conn = get_connection(db_path=db_path)

    try:
        # Step 2: Execute schema DDL
        print("\nStep 2: Creating schema v2.0.0 tables...")
        execute_schema_ddl(conn, schema_file)

        # Step 3: Migrate core entities
        print("\nStep 3: Migrating core entities...")
        roadmap_count = migrate_roadmaps(conn)
        track_count = migrate_tracks(conn)
        sprint_count = migrate_sprints(conn)
        task_count = migrate_tasks(conn)
        artifact_count = migrate_artifacts(conn)

        # Step 4: Migrate relationships → criteria
        print("\nStep 4: Converting relationships to criteria...")
        blocked_by_count = migrate_blocked_by_to_criteria(conn)
        depends_on_count = migrate_depends_on_to_criteria(conn)
        deliverable_count = migrate_deliverables_to_criteria(conn)
        gate_count = migrate_quality_gates_to_criteria(conn)

        # Step 5: Update database version
        print("\nStep 5: Updating database version...")
        update_database_version(conn)

        # Step 6: Validate migration
        print("\nStep 6: Validating migration...")
        validation_results = validate_migration(conn)

        # Commit transaction
        conn.commit()

        results = {
            "success": validation_results["success"],
            "backup_path": backup_path,
            "migrated": {
                "roadmaps": roadmap_count,
                "tracks": track_count,
                "sprints": sprint_count,
                "tasks": task_count,
                "artifacts": artifact_count
            },
            "criteria_created": {
                "blocked_by": blocked_by_count,
                "depends_on": depends_on_count,
                "deliverables": deliverable_count,
                "quality_gates": gate_count,
                "total": blocked_by_count + depends_on_count + deliverable_count + gate_count
            },
            "validation": validation_results
        }

        print(f"\n{'='*80}")
        print(f"MIGRATION {'COMPLETED' if results['success'] else 'COMPLETED WITH WARNINGS'}")
        print(f"{'='*80}\n")

        return results

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"Database restored from backup: {backup_path}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate database from v1.0.0 to v2.0.0")
    parser.add_argument("--db-path", type=Path, help="Path to database file")
    parser.add_argument("--base-dir", type=Path, help="Base directory containing .vibey folder")
    parser.add_argument("--schema-file", type=Path, help="Path to schema_v2.sql file")
    parser.add_argument("--dry-run", action="store_true", help="Create backup but don't modify database")

    args = parser.parse_args()

    results = run_migration(
        db_path=args.db_path,
        base_dir=args.base_dir,
        schema_file=args.schema_file,
        dry_run=args.dry_run
    )

    exit(0 if results["success"] else 1)
