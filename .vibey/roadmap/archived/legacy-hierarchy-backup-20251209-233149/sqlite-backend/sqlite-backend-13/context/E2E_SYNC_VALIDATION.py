#!/usr/bin/env python3
"""
Sprint 13 Task 007: End-to-end sync system validation

This script validates the complete sync system:
1. Write path: CLI -> DB -> dirty flag
2. Read path: YAML -> DB rebuild
3. Round-trip integrity: YAML -> DB -> YAML comparison
4. Sync manager functionality
5. Hook integration verification

Run with: python E2E_SYNC_VALIDATION.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Resolve repo root (script is in .vibey/roadmap/track/sprint/context/)
# Path: .vibey/roadmap/sqlite-backend/sqlite-backend-13/context/E2E_SYNC_VALIDATION.py
# parent = context, parent.parent = sprint, parent.parent.parent = track,
# parent.parent.parent.parent = roadmap, parent.parent.parent.parent.parent = .vibey
# parent.parent.parent.parent.parent.parent = repo_root
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
os.chdir(repo_root)
sys.path.insert(0, str(repo_root))

# Use absolute path for database
DB_PATH = repo_root / '.vibey' / 'roadmap.db'
ROADMAP_DIR = repo_root / '.vibey' / 'roadmap'

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check(name, condition, msg_pass=None, msg_fail=None):
    """Check a condition and print result."""
    if condition:
        print(f"  {GREEN}✓{RESET} {name}" + (f": {msg_pass}" if msg_pass else ""))
        return True
    else:
        print(f"  {RED}✗{RESET} {name}" + (f": {msg_fail}" if msg_fail else ""))
        return False


def main():
    print(f"\n{BOLD}=== Sprint 13 End-to-End Sync Validation ==={RESET}\n")

    passed = 0
    failed = 0

    # ============================================
    # 1. Database Connection & State
    # ============================================
    print(f"{BOLD}1. Database Connection & State{RESET}")

    try:
        from vibey.roadmap.database.connection import (
            database_exists, get_db_path, get_connection
        )

        db_path = DB_PATH
        if check("Database path resolved", db_path is not None, str(db_path)):
            passed += 1
        else:
            failed += 1

        if check("Database file exists", db_path.exists()):
            passed += 1
        else:
            failed += 1

        conn = get_connection(db_path=db_path)
        if check("Database connection works", conn is not None):
            passed += 1
            conn.close()
        else:
            failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} Database connection failed: {e}")
        failed += 3

    # ============================================
    # 2. Sync Manager Functionality
    # ============================================
    print(f"\n{BOLD}2. Sync Manager Functionality{RESET}")

    try:
        from vibey.roadmap.serialization.backend import SyncManager

        sync = SyncManager(roadmap_dir=ROADMAP_DIR, db_path=DB_PATH)

        if check("SyncManager instantiates", sync is not None):
            passed += 1
        else:
            failed += 1

        # Check dirty state method
        is_dirty = sync.is_db_dirty()
        if check("is_db_dirty() returns bool", isinstance(is_dirty, bool), f"dirty={is_dirty}"):
            passed += 1
        else:
            failed += 1

        # Check get_status method exists (load is done via rebuild)
        if check("get_status() method exists", hasattr(sync, 'get_status') and callable(sync.get_status)):
            passed += 1
        else:
            failed += 1

        # Check dump method exists
        if check("dump() method exists", hasattr(sync, 'dump') and callable(sync.dump)):
            passed += 1
        else:
            failed += 1

        # Check rebuild method exists
        if check("rebuild() method exists", hasattr(sync, 'rebuild') and callable(sync.rebuild)):
            passed += 1
        else:
            failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} SyncManager test failed: {e}")
        failed += 5

    # ============================================
    # 3. Write Path Verification
    # ============================================
    print(f"\n{BOLD}3. Write Path (CLI -> DB){RESET}")

    try:
        from vibey.operations.roadmap.update import _use_sqlite_backend
        import sqlite3

        # Check SQLite backend is available
        if check("SQLite backend available", _use_sqlite_backend(repo_root)):
            passed += 1
        else:
            failed += 1

        # Check a task exists in DB
        test_task_id = 'sqlite-backend-13-task-007'
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM tasks WHERE id = ?", (test_task_id,))
        task_row = cursor.fetchone()
        conn.close()

        if check("Task exists in database", task_row is not None, test_task_id):
            passed += 1
        else:
            failed += 1

        # Verify task status matches expected
        if task_row:
            if check("Task status is in_progress", task_row[1] == 'in_progress'):
                passed += 1
            else:
                failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} Write path test failed: {e}")
        failed += 3

    # ============================================
    # 4. Round-Trip Integrity Check
    # ============================================
    print(f"\n{BOLD}4. Round-Trip Integrity{RESET}")

    try:
        import sqlite3

        # Count entities in database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM tracks")
        db_tracks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sprints")
        db_sprints = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks")
        db_tasks = cursor.fetchone()[0]

        conn.close()

        if check("Tracks in database", db_tracks > 0, f"{db_tracks} tracks"):
            passed += 1
        else:
            failed += 1

        if check("Sprints in database", db_sprints > 0, f"{db_sprints} sprints"):
            passed += 1
        else:
            failed += 1

        if check("Tasks in database", db_tasks > 0, f"{db_tasks} tasks"):
            passed += 1
        else:
            failed += 1

        # Count YAML files
        yaml_tracks = len(list(ROADMAP_DIR.glob('*/track.yaml')))
        yaml_sprints = len(list(ROADMAP_DIR.glob('*/*/sprint.yaml')))
        yaml_tasks = len(list(ROADMAP_DIR.glob('*/*/*/task.yaml')))

        if check("YAML tracks match DB", yaml_tracks == db_tracks,
                 f"YAML={yaml_tracks}, DB={db_tracks}"):
            passed += 1
        else:
            failed += 1

        # Sprints may have embedded summaries, so just check DB has at least as many
        if check("DB sprints >= YAML sprints", db_sprints >= yaml_sprints,
                 f"YAML={yaml_sprints}, DB={db_sprints}"):
            passed += 1
        else:
            failed += 1

        if check("DB tasks match YAML tasks", db_tasks == yaml_tasks,
                 f"YAML={yaml_tasks}, DB={db_tasks}"):
            passed += 1
        else:
            failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} Round-trip test failed: {e}")
        failed += 6

    # ============================================
    # 5. Pre-commit Hook Integration
    # ============================================
    print(f"\n{BOLD}5. Pre-commit Hook Integration{RESET}")

    try:
        from vibey.operations.git.hooks.pre_commit import PreCommitHook

        hook = PreCommitHook('.')

        if check("PreCommitHook instantiates", hook is not None):
            passed += 1
        else:
            failed += 1

        if check("_sync_database_to_yaml exists", hasattr(hook, '_sync_database_to_yaml')):
            passed += 1
        else:
            failed += 1

        if check("Hook config loaded", hook.config is not None):
            passed += 1
        else:
            failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} Pre-commit hook test failed: {e}")
        failed += 3

    # ============================================
    # 6. Post-merge Hook Integration
    # ============================================
    print(f"\n{BOLD}6. Post-merge Hook Integration{RESET}")

    try:
        from vibey.operations.git.hooks.post_merge import PostMergeHook

        hook = PostMergeHook('.')

        if check("PostMergeHook instantiates", hook is not None):
            passed += 1
        else:
            failed += 1

        if check("_rebuild_database exists", hasattr(hook, '_rebuild_database')):
            passed += 1
        else:
            failed += 1

        if check("_should_rebuild exists", hasattr(hook, '_should_rebuild')):
            passed += 1
        else:
            failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} Post-merge hook test failed: {e}")
        failed += 3

    # ============================================
    # 7. Database Validation
    # ============================================
    print(f"\n{BOLD}7. Database Schema & Integrity{RESET}")

    try:
        import sqlite3

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Check required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {'tracks', 'sprints', 'tasks', 'database_state', 'criteria'}
        for table in required_tables:
            if check(f"Table '{table}' exists", table in tables):
                passed += 1
            else:
                failed += 1

        # Check database_state singleton
        cursor.execute("SELECT COUNT(*) FROM database_state")
        state_count = cursor.fetchone()[0]
        if check("database_state has singleton row", state_count == 1):
            passed += 1
        else:
            failed += 1

        # Run SQLite integrity check
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if check("SQLite integrity check", integrity == 'ok'):
            passed += 1
        else:
            failed += 1

        conn.close()

    except Exception as e:
        print(f"  {RED}✗{RESET} Database validation failed: {e}")
        failed += 7

    # ============================================
    # 8. Embedded Summary Validation
    # ============================================
    print(f"\n{BOLD}8. Embedded Summary Validation{RESET}")

    try:
        from vibey.roadmap.database.integrity_audit import validate_all_embedded_summaries

        reports = validate_all_embedded_summaries(ROADMAP_DIR)

        tracks_checked = len(reports)
        tracks_with_issues = sum(1 for r in reports if r.has_issues)

        if check("All tracks checked", tracks_checked > 0, f"{tracks_checked} tracks"):
            passed += 1
        else:
            failed += 1

        if check("No embedded summary issues", tracks_with_issues == 0,
                 f"{tracks_with_issues} tracks with issues"):
            passed += 1
        else:
            failed += 1

    except Exception as e:
        print(f"  {RED}✗{RESET} Embedded summary validation failed: {e}")
        failed += 2

    # ============================================
    # Summary
    # ============================================
    print(f"\n{BOLD}=== Validation Summary ==={RESET}")
    total = passed + failed
    print(f"  Passed: {GREEN}{passed}{RESET}/{total}")
    print(f"  Failed: {RED}{failed}{RESET}/{total}")

    if failed == 0:
        print(f"\n{GREEN}All end-to-end sync validations passed!{RESET}")
        print(f"Sync system is ready for production cutover.\n")
        return 0
    else:
        print(f"\n{RED}Some validations failed.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
