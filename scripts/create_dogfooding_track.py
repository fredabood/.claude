#!/usr/bin/env python3
"""Create dogfooding-bugs track from CLI_BUGS.md content."""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from ulid import ULID

# Bug definitions from CLI_BUGS.md
BUGS = [
    {
        "number": 1,
        "title": "Track and Sprint Progress Not Auto-Updated After Task Completion",
        "severity": "medium",
        "status": "documented",
        "description": "After completing all tasks in a sprint, the track and sprint progress fields are not automatically updated to reflect completion.",
        "root_cause": "Progress update logic not integrated with flat directory structure migration.",
        "files_affected": ["vibey/operations/roadmap/update.py"],
        "tasks": [
            {"title": "Analyze current progress update flow", "type": "research", "complexity": "low"},
            {"title": "Implement auto-progression logic in update.py", "type": "development", "complexity": "medium"},
            {"title": "Add post-task-completion hook for parent updates", "type": "development", "complexity": "medium"},
            {"title": "Add unit tests for progress propagation", "type": "testing", "complexity": "medium"},
            {"title": "Manual verification with test sprint", "type": "testing", "complexity": "low"}
        ]
    },
    {
        "number": 2,
        "title": "Track Not Showing in roadmap status",
        "severity": "low",
        "status": "documented",
        "description": "The `vibey roadmap status` command does not display certain tracks in its output.",
        "root_cause": "Track discovery issue in flat structure implementation.",
        "files_affected": ["vibey/operations/roadmap/query.py", "vibey/cli/roadmap_lib/filesystem.py"],
        "tasks": [
            {"title": "Debug track discovery in FileSystemManager.list_tracks()", "type": "research", "complexity": "low"},
            {"title": "Fix track filtering/discovery logic", "type": "development", "complexity": "medium"},
            {"title": "Add integration test for track listing", "type": "testing", "complexity": "low"}
        ]
    },
    {
        "number": 3,
        "title": "CLI Looks for roadmap.yaml in Wrong Location",
        "severity": "high",
        "status": "documented",
        "description": "CLI commands look for roadmap.yaml at wrong location after flat structure migration.",
        "root_cause": "FileSystemManager.get_roadmap_path() returns wrong path.",
        "files_affected": ["vibey/cli/roadmap_lib/filesystem.py"],
        "tasks": [
            {"title": "Update FileSystemManager.get_roadmap_path() to use roadmap_root", "type": "development", "complexity": "low"},
            {"title": "Update all callers to use correct path", "type": "development", "complexity": "low"},
            {"title": "Add unit test for path resolution", "type": "testing", "complexity": "low"}
        ]
    },
    {
        "number": 4,
        "title": "Track Model Validation Fails for Flat Structure Sprint IDs",
        "severity": "critical",
        "status": "documented",
        "description": "Track model validation fails because sprint IDs don't match expected hierarchical format.",
        "root_cause": "Migration assigned ULIDs but didn't update validation logic.",
        "files_affected": ["vibey/roadmap/models/track.py"],
        "tasks": [
            {"title": "Analyze Track.__post_init__ validation requirements", "type": "research", "complexity": "low"},
            {"title": "Update validation to accept ULID-based sprint IDs", "type": "development", "complexity": "medium"},
            {"title": "Add backward compatibility for slug-based IDs", "type": "development", "complexity": "low"},
            {"title": "Add unit tests for both ID formats", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 5,
        "title": "SQLite Database Out of Sync with YAML",
        "severity": "critical",
        "status": "documented",
        "description": "SQLite database out of sync with YAML files after migration.",
        "root_cause": "Migration updated YAML but not SQLite database.",
        "files_affected": [".vibey/roadmap.db", "vibey/roadmap/serialization/sql_loader.py"],
        "tasks": [
            {"title": "Add database sync step to migration script", "type": "development", "complexity": "medium"},
            {"title": "Implement automatic db rebuild after YAML changes", "type": "development", "complexity": "high"},
            {"title": "Add CLI command to force db resync", "type": "development", "complexity": "medium"},
            {"title": "Add integration test for YAML-DB sync", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 6,
        "title": "Missing SQLAlchemy Dependency Breaks CLI",
        "severity": "critical",
        "status": "documented",
        "description": "All CLI commands fail due to unconditional SQLAlchemy import.",
        "root_cause": "orm.py unconditionally imports SQLAlchemy at module load time.",
        "files_affected": ["vibey/roadmap/models/ticket/__init__.py", "vibey/roadmap/models/ticket/orm.py"],
        "tasks": [
            {"title": "Implement lazy imports in orm.py", "type": "development", "complexity": "medium"},
            {"title": "Move ORM imports behind try/except ImportError", "type": "development", "complexity": "low"},
            {"title": "Add SQLAlchemy to optional dependencies", "type": "development", "complexity": "low"},
            {"title": "Add test for CLI without SQLAlchemy installed", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 7,
        "title": "Validator Doesn't Exclude context/sample_code",
        "severity": "low",
        "status": "documented",
        "description": "Validator checks files in context/sample_code which are not roadmap data.",
        "root_cause": "Missing exclusion pattern for sample_code directories.",
        "files_affected": ["vibey/cli/roadmap_lib/validation.py"],
        "tasks": [
            {"title": "Add VALIDATION_EXCLUDE_PATTERNS constant", "type": "development", "complexity": "low"},
            {"title": "Update validator to skip excluded paths", "type": "development", "complexity": "low"},
            {"title": "Add unit test for exclusion patterns", "type": "testing", "complexity": "low"}
        ]
    },
    {
        "number": 8,
        "title": "YAML Loader Missing blocked Field",
        "severity": "critical",
        "status": "documented",
        "description": "yaml_loader.py expects 'blocked' field but v2 migration removed it.",
        "root_cause": "v1_to_v2.py removed blocked field but loader still requires it.",
        "files_affected": ["vibey/roadmap/serialization/yaml_loader.py"],
        "tasks": [
            {"title": "Update load_roadmap to use .get('blocked', False)", "type": "development", "complexity": "low"},
            {"title": "Update load_track for backward compatibility", "type": "development", "complexity": "low"},
            {"title": "Update load_sprint for backward compatibility", "type": "development", "complexity": "low"},
            {"title": "Update load_task for backward compatibility", "type": "development", "complexity": "low"},
            {"title": "Add migration test for v1 to v2 loading", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 9,
        "title": "Pre-commit Hook Database Error",
        "severity": "medium",
        "status": "documented",
        "description": "Pre-commit hook fails with 'no such column: is_dirty' error.",
        "root_cause": "Database schema out of date or hook queries non-existent column.",
        "files_affected": [".vibey/hooks/"],
        "tasks": [
            {"title": "Investigate is_dirty column in schema history", "type": "research", "complexity": "low"},
            {"title": "Update pre-commit hook to use correct schema", "type": "development", "complexity": "medium"},
            {"title": "Add database migration script for schema updates", "type": "development", "complexity": "medium"},
            {"title": "Test pre-commit hook with fresh database", "type": "testing", "complexity": "low"}
        ]
    },
    {
        "number": 10,
        "title": "CLI Reads from Monolithic roadmap.yaml",
        "severity": "critical",
        "status": "documented",
        "description": "CLI reads from monolithic file instead of ULID files.",
        "root_cause": "load_roadmap reads from monolithic file which only has TrackSummary.",
        "files_affected": ["vibey/roadmap/serialization/yaml_loader.py", "vibey/operations/roadmap/query.py"],
        "tasks": [
            {"title": "Design new loading strategy for ULID files", "type": "research", "complexity": "medium"},
            {"title": "Update load_roadmap to discover tracks from tracks/*.yaml", "type": "development", "complexity": "high"},
            {"title": "Implement lazy loading for track details", "type": "development", "complexity": "medium"},
            {"title": "Update query.py to use new loading strategy", "type": "development", "complexity": "medium"},
            {"title": "Add integration tests for ULID file loading", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 11,
        "title": "Database Rebuild Loads 0 Items",
        "severity": "critical",
        "status": "documented",
        "description": "`vibey roadmap db rebuild` reports 0 items loaded.",
        "root_cause": "Database init uses load_roadmap which only gets TrackSummary.",
        "files_affected": ["vibey/cli/commands.py", "vibey/roadmap/serialization/sql_loader.py"],
        "tasks": [
            {"title": "Update db_rebuild_cmd to load from ULID files", "type": "development", "complexity": "medium"},
            {"title": "Update sql_loader init to iterate tracks/*.yaml", "type": "development", "complexity": "medium"},
            {"title": "Add progress reporting during rebuild", "type": "development", "complexity": "low"},
            {"title": "Add integration test for database rebuild", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 12,
        "title": "New Tracks Missing from roadmap.yaml",
        "severity": "high",
        "status": "documented",
        "description": "Tracks created in ULID system don't appear in monolithic roadmap.yaml.",
        "root_cause": "No sync mechanism from ULID files back to roadmap.yaml.",
        "files_affected": [".vibey/roadmap/roadmap.yaml"],
        "tasks": [
            {"title": "Implement sync mechanism ULID files → roadmap.yaml", "type": "development", "complexity": "medium"},
            {"title": "Add CLI command to sync roadmap.yaml", "type": "development", "complexity": "medium"},
            {"title": "Consider deprecating roadmap.yaml as source of truth", "type": "research", "complexity": "low"},
            {"title": "Add validation to detect sync discrepancies", "type": "development", "complexity": "medium"}
        ]
    },
    {
        "number": 13,
        "title": "Activity Log Not Migrated to JSONL",
        "severity": "medium",
        "status": "documented",
        "description": "Activity log uses audit-trail.yaml instead of designed JSONL format.",
        "root_cause": "Unified architecture migration did not include activity log.",
        "files_affected": ["vibey/operations/roadmap/activity_log.py", ".vibey/roadmap/audit-trail.yaml"],
        "tasks": [
            {"title": "Create activity_log/ directory structure", "type": "development", "complexity": "low"},
            {"title": "Write JSONL writer for activity events", "type": "development", "complexity": "medium"},
            {"title": "Write JSONL reader for activity queries", "type": "development", "complexity": "medium"},
            {"title": "Migrate existing audit-trail.yaml to JSONL", "type": "development", "complexity": "medium"},
            {"title": "Update all activity log consumers", "type": "development", "complexity": "medium"},
            {"title": "Add tests for JSONL activity log", "type": "testing", "complexity": "medium"}
        ]
    },
    {
        "number": 14,
        "title": "Duplicate roadmap.yaml Files",
        "severity": "high",
        "status": "fixed",
        "description": "Two roadmap.yaml files existed with different data.",
        "root_cause": "Bug #3 caused CLI to use wrong location.",
        "files_affected": [],
        "tasks": [
            {"title": "Verify single roadmap.yaml exists at correct location", "type": "testing", "complexity": "low"},
            {"title": "Add startup check to warn if duplicate exists", "type": "development", "complexity": "low"},
            {"title": "Document canonical location in CLAUDE.md", "type": "documentation", "complexity": "low"}
        ]
    },
    {
        "number": 15,
        "title": "No CLI Commands to Create Tracks/Sprints/Tasks",
        "severity": "high",
        "status": "documented",
        "description": "CLI lacks commands to create new tracks/sprints/tasks in ULID structure.",
        "root_cause": "ULID migration focused on data migration, not CLI operations.",
        "files_affected": ["vibey/cli/roadmap_create_from_plan.py", "vibey/cli/commands.py"],
        "tasks": [
            {"title": "Add create track CLI command", "type": "development", "complexity": "medium"},
            {"title": "Add create sprint CLI command", "type": "development", "complexity": "medium"},
            {"title": "Add create task CLI command", "type": "development", "complexity": "medium"},
            {"title": "Update create-from-plan to use ULID flat structure", "type": "development", "complexity": "high"},
            {"title": "Create ULIDManager for ULID generation", "type": "development", "complexity": "low"},
            {"title": "Add integration tests for create commands", "type": "testing", "complexity": "medium"}
        ]
    }
]

def generate_ulid():
    """Generate a ULID string."""
    return str(ULID())

def main():
    """Generate all dogfooding track files."""
    base_dir = Path(__file__).parent.parent / ".vibey" / "roadmap"
    tracks_dir = base_dir / "tracks"
    sprints_dir = base_dir / "sprints"
    tasks_dir = base_dir / "tasks"
    context_dir = base_dir / "context" / "sprints"

    now = datetime.now(timezone.utc).isoformat()

    # Generate ULIDs
    track_ulid = generate_ulid()
    time.sleep(0.002)

    sprint_ulids = []
    task_ulids = []

    for bug in BUGS:
        sprint_ulid = generate_ulid()
        time.sleep(0.002)
        sprint_ulids.append(sprint_ulid)

        bug_task_ulids = []
        for _ in bug["tasks"]:
            task_ulid = generate_ulid()
            time.sleep(0.002)
            bug_task_ulids.append(task_ulid)
        task_ulids.append(bug_task_ulids)

    # Calculate totals
    total_tasks = sum(len(bug["tasks"]) for bug in BUGS)
    completed_sprints = sum(1 for bug in BUGS if bug["status"] == "fixed")
    completed_tasks = sum(len(bug["tasks"]) for bug in BUGS if bug["status"] == "fixed")

    # Create sprint refs for track
    sprint_refs = []
    for i, (bug, sprint_ulid) in enumerate(zip(BUGS, sprint_ulids)):
        status = "completed" if bug["status"] == "fixed" else ("in_progress" if bug["status"] == "fixing" else "not_started")
        sprint_refs.append({
            "id": sprint_ulid,
            "name": f"Bug #{bug['number']}: {bug['title'][:40]}{'...' if len(bug['title']) > 40 else ''}",
            "status": status,
            "estimated_duration": None,
            "tasks_count": len(bug["tasks"]),
            "started": now if status != "not_started" else None
        })

    # Create track YAML
    track_data = {
        "track": {
            "id": track_ulid,
            "name": "CLI Dogfooding Bug Fixes",
            "roadmap_id": "vibey-framework-v2",
            "status": "not_started",
            "priority": "critical",
            "created": now,
            "started": None,
            "completed": None,
            "estimated_duration": None,
            "progress": {
                "sprints_total": len(BUGS),
                "sprints_completed": completed_sprints,
                "tasks_total": total_tasks,
                "tasks_completed": completed_tasks,
                "completion_percent": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
            },
            "sprints": sprint_refs,
            "dependencies": [],
            "blocked_by": [],
            "depends_on": [],
            "assigned_agents": [],
            "deliverables": [],
            "strategic_value": [
                "Resolve bugs discovered during Vibey dogfooding",
                "Improve CLI reliability and user experience",
                "Complete ULID migration properly",
                "Enable YAML backend to work correctly",
                "Maintain development velocity"
            ],
            "commits": [],
            "standards": [],
            "metadata": {
                "created_by": "claude-code",
                "last_updated": None,
                "source": "CLI_BUGS.md",
                "notes": "Track created from bugs discovered during Vibey development"
            },
            "slug": "dogfooding-bugs",
            "criteria": []
        }
    }

    track_file = tracks_dir / f"{track_ulid}.yaml"
    print(f"Creating track: {track_file}")
    with open(track_file, 'w') as f:
        yaml.dump(track_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Update tracks .id file
    id_file = tracks_dir / ".id"
    with open(id_file, 'a') as f:
        f.write(f"dogfooding-bugs={track_ulid}\n")
    print(f"Updated {id_file}")

    # Create sprint and task files
    sprints_id_entries = []
    tasks_id_entries = []

    for i, (bug, sprint_ulid, bug_task_ulids) in enumerate(zip(BUGS, sprint_ulids, task_ulids)):
        status = "completed" if bug["status"] == "fixed" else ("in_progress" if bug["status"] == "fixing" else "not_started")
        sprint_slug = f"dogfooding-bugs-{bug['number']:02d}"

        task_refs = []
        for j, task in enumerate(bug["tasks"]):
            task_slug = f"{sprint_slug}-task-{j+1:03d}"
            task_refs.append({
                "id": task_slug,
                "title": task["title"],
                "status": "completed" if bug["status"] == "fixed" else "not_started"
            })

        # Create sprint YAML
        sprint_data = {
            "sprint": {
                "id": sprint_ulid,
                "track_id": "dogfooding-bugs",
                "roadmap_id": "vibey-framework-v2",
                "name": f"Bug #{bug['number']}: {bug['title']}",
                "description": bug["description"],
                "status": status,
                "created": now,
                "started": now if status != "not_started" else None,
                "completed": now if status == "completed" else None,
                "goal": f"Fix Bug #{bug['number']}: {bug['title']}",
                "success_criteria": [
                    f"Root cause addressed: {bug['root_cause']}",
                    "All affected files updated",
                    "Unit tests pass",
                    "Integration tests pass"
                ],
                "tasks": task_refs,
                "dependencies": [],
                "blocked_by": [],
                "depends_on": [],
                "deliverables": [],
                "risks": [],
                "metadata": {
                    "bug_number": bug["number"],
                    "severity": bug["severity"],
                    "original_status": bug["status"],
                    "root_cause": bug["root_cause"]
                },
                "slug": sprint_slug,
                "parent_ref": track_ulid,
                "criteria": [],
                "sequence": i + 1
            }
        }

        sprint_file = sprints_dir / f"{sprint_ulid}.yaml"
        print(f"Creating sprint: {sprint_file}")
        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        sprints_id_entries.append(f"{sprint_slug}={sprint_ulid}")

        # Create task files
        for j, (task, task_ulid) in enumerate(zip(bug["tasks"], bug_task_ulids)):
            task_slug = f"{sprint_slug}-task-{j+1:03d}"
            task_status = "completed" if bug["status"] == "fixed" else "not_started"

            task_data = {
                "task": {
                    "id": task_ulid,
                    "sprint_id": sprint_slug,
                    "track_id": "dogfooding-bugs",
                    "roadmap_id": "vibey-framework-v2",
                    "task_type": task.get("type", "development"),
                    "title": task["title"],
                    "description": None,
                    "status": task_status,
                    "created": now,
                    "started": now if task_status != "not_started" else None,
                    "completed": now if task_status == "completed" else None,
                    "assigned_agent": None,
                    "priority": "high" if bug["severity"] == "critical" else "medium",
                    "phase_label": None,
                    "estimated_tokens": 1,
                    "actual_tokens": None,
                    "complexity": task.get("complexity", "medium"),
                    "gate_info": None,
                    "audit_results": None,
                    "dependencies": [],
                    "blocked_by": [],
                    "depends_on": [],
                    "deliverables": [],
                    "commits": [],
                    "metadata": {
                        "last_updated": None,
                        "token_efficiency": None,
                        "duration_hours": None,
                        "bug_number": bug["number"]
                    },
                    "slug": task_slug,
                    "parent_ref": sprint_ulid,
                    "criteria": [],
                    "sequence": j + 1
                }
            }

            task_file = tasks_dir / f"{task_ulid}.yaml"
            print(f"Creating task: {task_file}")
            with open(task_file, 'w') as f:
                yaml.dump(task_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            tasks_id_entries.append(f"{task_slug}={task_ulid}")

        # Create context file for this bug
        context_sprint_dir = context_dir / sprint_slug
        context_sprint_dir.mkdir(parents=True, exist_ok=True)

        context_content = f"""# Bug #{bug['number']}: {bug['title']}

**Date:** 2025-12-09
**Severity:** {bug['severity'].upper()}
**Status:** {bug['status'].upper()}

---

## Description

{bug['description']}

---

## Root Cause

{bug['root_cause']}

---

## Files Affected

{chr(10).join(f"- `{f}`" for f in bug['files_affected']) if bug['files_affected'] else "None identified"}

---

## Tasks

{chr(10).join(f"{j+1}. **{t['title']}** ({t.get('type', 'development')}, {t.get('complexity', 'medium')} complexity)" for j, t in enumerate(bug['tasks']))}

---

## Sprint Plan

### Goal
Fix Bug #{bug['number']}: {bug['title']}

### Success Criteria
1. Root cause addressed: {bug['root_cause']}
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
"""
        context_file = context_sprint_dir / f"BUG_{bug['number']:02d}.md"
        print(f"Creating context: {context_file}")
        with open(context_file, 'w') as f:
            f.write(context_content)

    # Update sprints .id file
    sprints_id_file = sprints_dir / ".id"
    with open(sprints_id_file, 'a') as f:
        for entry in sprints_id_entries:
            f.write(f"{entry}\n")
    print(f"Updated {sprints_id_file}")

    # Update tasks .id file
    tasks_id_file = tasks_dir / ".id"
    with open(tasks_id_file, 'a') as f:
        for entry in tasks_id_entries:
            f.write(f"{entry}\n")
    print(f"Updated {tasks_id_file}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Track ULID: {track_ulid}")
    print(f"Track slug: dogfooding-bugs")
    print(f"Sprints created: {len(BUGS)}")
    print(f"Tasks created: {total_tasks}")
    print(f"Context files created: {len(BUGS)}")
    print(f"\nTrack file: {track_file}")

    # Output for roadmap.yaml update
    print("\n" + "="*60)
    print("ADD TO .vibey/roadmap/roadmap.yaml tracks list:")
    print("="*60)
    print("""
- id: dogfooding-bugs
  name: CLI Dogfooding Bug Fixes
  status: not_started
  priority: critical
""")

    return track_ulid

if __name__ == "__main__":
    track_ulid = main()
