#!/usr/bin/env python3
"""Consolidate dogfooding-bugs track from 15 sprints to 7 sprints."""

import os
import sys
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from ulid import ULID

def generate_ulid():
    """Generate a ULID string."""
    return str(ULID())

# Consolidated sprint definitions
SPRINTS = [
    {
        "number": 1,
        "name": "CLI Startup Unblock",
        "bugs": [6, 8],
        "priority": "critical",
        "depends_on": [],
        "description": "Fix critical import and schema issues blocking CLI startup. SQLAlchemy must be optional, and YAML loader must handle v2 format without 'blocked' field.",
        "goal": "Make CLI commands executable without errors",
        "success_criteria": [
            "CLI starts without SQLAlchemy installed",
            "YAML files load without KeyError for blocked field",
            "All load_* functions handle v1 and v2 formats"
        ],
        "tasks": [
            {"title": "Implement lazy imports in orm.py", "type": "development", "complexity": "medium", "bug": 6},
            {"title": "Move ORM imports behind try/except ImportError", "type": "development", "complexity": "low", "bug": 6},
            {"title": "Add SQLAlchemy to optional dependencies in pyproject.toml", "type": "development", "complexity": "low", "bug": 6},
            {"title": "Add test for CLI without SQLAlchemy installed", "type": "testing", "complexity": "medium", "bug": 6},
            {"title": "Update load_roadmap to use .get('blocked', False)", "type": "development", "complexity": "low", "bug": 8},
            {"title": "Update load_track for backward compatibility", "type": "development", "complexity": "low", "bug": 8},
            {"title": "Update load_sprint for backward compatibility", "type": "development", "complexity": "low", "bug": 8},
            {"title": "Update load_task for backward compatibility", "type": "development", "complexity": "low", "bug": 8},
            {"title": "Add migration test for v1 to v2 loading", "type": "testing", "complexity": "medium", "bug": 8}
        ]
    },
    {
        "number": 2,
        "name": "ULID File Loading System",
        "bugs": [3, 10, 2, 12, 4],
        "priority": "critical",
        "depends_on": ["dogfooding-bugs-01"],
        "description": "Complete the ULID migration by updating CLI to read from individual ULID files instead of monolithic roadmap.yaml. Fix path resolution, track discovery, and model validation.",
        "goal": "CLI correctly reads all data from ULID flat file structure",
        "success_criteria": [
            "FileSystemManager uses correct roadmap.yaml location",
            "load_roadmap discovers tracks from tracks/*.yaml",
            "All 39 tracks visible in 'roadmap status'",
            "Track model validates ULID-based sprint IDs",
            "New tracks sync back to roadmap.yaml"
        ],
        "tasks": [
            {"title": "Update FileSystemManager.get_roadmap_path() to use roadmap_root", "type": "development", "complexity": "low", "bug": 3},
            {"title": "Update all callers to use correct path", "type": "development", "complexity": "low", "bug": 3},
            {"title": "Add unit test for path resolution", "type": "testing", "complexity": "low", "bug": 3},
            {"title": "Design new loading strategy for ULID files", "type": "research", "complexity": "medium", "bug": 10},
            {"title": "Update load_roadmap to discover tracks from tracks/*.yaml", "type": "development", "complexity": "high", "bug": 10},
            {"title": "Implement lazy loading for track details", "type": "development", "complexity": "medium", "bug": 10},
            {"title": "Update query.py to use new loading strategy", "type": "development", "complexity": "medium", "bug": 10},
            {"title": "Add integration tests for ULID file loading", "type": "testing", "complexity": "medium", "bug": 10},
            {"title": "Debug track discovery in FileSystemManager.list_tracks()", "type": "research", "complexity": "low", "bug": 2},
            {"title": "Fix track filtering/discovery logic", "type": "development", "complexity": "medium", "bug": 2},
            {"title": "Add integration test for track listing", "type": "testing", "complexity": "low", "bug": 2},
            {"title": "Implement sync mechanism ULID files to roadmap.yaml", "type": "development", "complexity": "medium", "bug": 12},
            {"title": "Add CLI command to sync roadmap.yaml", "type": "development", "complexity": "medium", "bug": 12},
            {"title": "Add validation to detect sync discrepancies", "type": "development", "complexity": "medium", "bug": 12},
            {"title": "Update validation to accept ULID-based sprint IDs", "type": "development", "complexity": "medium", "bug": 4},
            {"title": "Add backward compatibility for slug-based IDs", "type": "development", "complexity": "low", "bug": 4},
            {"title": "Add unit tests for both ID formats", "type": "testing", "complexity": "medium", "bug": 4}
        ]
    },
    {
        "number": 3,
        "name": "Database Synchronization",
        "bugs": [5, 9, 11],
        "priority": "high",
        "depends_on": ["dogfooding-bugs-02"],
        "description": "Fix SQLite database backend to properly sync with YAML files. Update schema, fix rebuild command, and ensure pre-commit hook works.",
        "goal": "SQLite backend works correctly with ULID file system",
        "success_criteria": [
            "Database rebuild loads all 39 tracks, 213 sprints, 1125 tasks",
            "Pre-commit hook runs without is_dirty error",
            "Database stays in sync with YAML changes"
        ],
        "tasks": [
            {"title": "Add database sync step to migration script", "type": "development", "complexity": "medium", "bug": 5},
            {"title": "Implement automatic db rebuild after YAML changes", "type": "development", "complexity": "high", "bug": 5},
            {"title": "Add CLI command to force db resync", "type": "development", "complexity": "medium", "bug": 5},
            {"title": "Add integration test for YAML-DB sync", "type": "testing", "complexity": "medium", "bug": 5},
            {"title": "Investigate is_dirty column in schema history", "type": "research", "complexity": "low", "bug": 9},
            {"title": "Update pre-commit hook to use correct schema", "type": "development", "complexity": "medium", "bug": 9},
            {"title": "Add database migration script for schema updates", "type": "development", "complexity": "medium", "bug": 9},
            {"title": "Test pre-commit hook with fresh database", "type": "testing", "complexity": "low", "bug": 9},
            {"title": "Update db_rebuild_cmd to load from ULID files", "type": "development", "complexity": "medium", "bug": 11},
            {"title": "Update sql_loader init to iterate tracks/*.yaml", "type": "development", "complexity": "medium", "bug": 11},
            {"title": "Add progress reporting during rebuild", "type": "development", "complexity": "low", "bug": 11},
            {"title": "Add integration test for database rebuild", "type": "testing", "complexity": "medium", "bug": 11}
        ]
    },
    {
        "number": 4,
        "name": "Progress Auto-Update",
        "bugs": [1],
        "priority": "medium",
        "depends_on": ["dogfooding-bugs-02"],
        "description": "Implement automatic progress propagation when tasks/sprints are completed. Parent objects should automatically update their progress counters.",
        "goal": "Progress updates automatically propagate up the hierarchy",
        "success_criteria": [
            "Completing a task updates sprint progress",
            "Completing all tasks marks sprint as completed",
            "Sprint completion updates track progress",
            "Track completion updates roadmap progress"
        ],
        "tasks": [
            {"title": "Analyze current progress update flow", "type": "research", "complexity": "low", "bug": 1},
            {"title": "Implement auto-progression logic in update.py", "type": "development", "complexity": "medium", "bug": 1},
            {"title": "Add post-task-completion hook for parent updates", "type": "development", "complexity": "medium", "bug": 1},
            {"title": "Add unit tests for progress propagation", "type": "testing", "complexity": "medium", "bug": 1},
            {"title": "Manual verification with test sprint", "type": "testing", "complexity": "low", "bug": 1}
        ]
    },
    {
        "number": 5,
        "name": "CLI Create Commands",
        "bugs": [15],
        "priority": "high",
        "depends_on": ["dogfooding-bugs-02"],
        "description": "Add CLI commands to create new tracks, sprints, and tasks using the ULID flat file structure. Update create-from-plan to use new structure.",
        "goal": "Users can create roadmap objects via CLI",
        "success_criteria": [
            "'vibey roadmap create track' works",
            "'vibey roadmap create sprint' works",
            "'vibey roadmap create task' works",
            "create-from-plan uses ULID flat structure"
        ],
        "tasks": [
            {"title": "Add create track CLI command", "type": "development", "complexity": "medium", "bug": 15},
            {"title": "Add create sprint CLI command", "type": "development", "complexity": "medium", "bug": 15},
            {"title": "Add create task CLI command", "type": "development", "complexity": "medium", "bug": 15},
            {"title": "Update create-from-plan to use ULID flat structure", "type": "development", "complexity": "high", "bug": 15},
            {"title": "Create ULIDManager for ULID generation", "type": "development", "complexity": "low", "bug": 15},
            {"title": "Add integration tests for create commands", "type": "testing", "complexity": "medium", "bug": 15}
        ]
    },
    {
        "number": 6,
        "name": "Tooling Polish",
        "bugs": [7, 14],
        "priority": "low",
        "depends_on": [],
        "description": "Clean up validator to exclude sample code directories and verify duplicate roadmap.yaml fix is complete.",
        "goal": "Validation and tooling work correctly",
        "success_criteria": [
            "Validator skips context/sample_code directories",
            "Single roadmap.yaml verified at correct location",
            "Startup warns if duplicate found"
        ],
        "tasks": [
            {"title": "Add VALIDATION_EXCLUDE_PATTERNS constant", "type": "development", "complexity": "low", "bug": 7},
            {"title": "Update validator to skip excluded paths", "type": "development", "complexity": "low", "bug": 7},
            {"title": "Add unit test for exclusion patterns", "type": "testing", "complexity": "low", "bug": 7},
            {"title": "Verify single roadmap.yaml exists at correct location", "type": "testing", "complexity": "low", "bug": 14},
            {"title": "Add startup check to warn if duplicate exists", "type": "development", "complexity": "low", "bug": 14},
            {"title": "Document canonical location in CLAUDE.md", "type": "documentation", "complexity": "low", "bug": 14}
        ]
    },
    {
        "number": 7,
        "name": "Activity Log Migration",
        "bugs": [13],
        "priority": "medium",
        "depends_on": [],
        "description": "Migrate activity log from audit-trail.yaml to time-bucketed JSONL format as designed in unified architecture.",
        "goal": "Activity log uses JSONL format",
        "success_criteria": [
            "activity_log/ directory exists",
            "Events written to YYYY-MM.jsonl files",
            "Old audit-trail.yaml migrated",
            "All consumers use new format"
        ],
        "tasks": [
            {"title": "Create activity_log/ directory structure", "type": "development", "complexity": "low", "bug": 13},
            {"title": "Write JSONL writer for activity events", "type": "development", "complexity": "medium", "bug": 13},
            {"title": "Write JSONL reader for activity queries", "type": "development", "complexity": "medium", "bug": 13},
            {"title": "Migrate existing audit-trail.yaml to JSONL", "type": "development", "complexity": "medium", "bug": 13},
            {"title": "Update all activity log consumers", "type": "development", "complexity": "medium", "bug": 13},
            {"title": "Add tests for JSONL activity log", "type": "testing", "complexity": "medium", "bug": 13}
        ]
    }
]

def get_old_sprint_ulids(base_dir):
    """Get list of old sprint ULIDs for dogfooding-bugs track."""
    sprints_id_file = base_dir / "sprints" / ".id"
    ulids = []
    with open(sprints_id_file, 'r') as f:
        for line in f:
            if line.startswith("dogfooding-bugs-"):
                slug, ulid = line.strip().split("=")
                ulids.append(ulid)
    return ulids

def get_old_task_ulids(base_dir):
    """Get list of old task ULIDs for dogfooding-bugs track."""
    tasks_id_file = base_dir / "tasks" / ".id"
    ulids = []
    with open(tasks_id_file, 'r') as f:
        for line in f:
            if line.startswith("dogfooding-bugs-"):
                slug, ulid = line.strip().split("=")
                ulids.append(ulid)
    return ulids

def remove_old_files(base_dir):
    """Remove old sprint and task files."""
    # Get old ULIDs
    old_sprint_ulids = get_old_sprint_ulids(base_dir)
    old_task_ulids = get_old_task_ulids(base_dir)

    # Remove old sprint files
    for ulid in old_sprint_ulids:
        sprint_file = base_dir / "sprints" / f"{ulid}.yaml"
        if sprint_file.exists():
            sprint_file.unlink()
            print(f"Removed: {sprint_file}")

    # Remove old task files
    for ulid in old_task_ulids:
        task_file = base_dir / "tasks" / f"{ulid}.yaml"
        if task_file.exists():
            task_file.unlink()
            print(f"Removed: {task_file}")

    # Remove old context directories
    context_dir = base_dir / "context" / "sprints"
    for i in range(1, 16):
        old_context_dir = context_dir / f"dogfooding-bugs-{i:02d}"
        if old_context_dir.exists():
            shutil.rmtree(old_context_dir)
            print(f"Removed: {old_context_dir}")

    # Clean up .id files
    for id_file in [base_dir / "sprints" / ".id", base_dir / "tasks" / ".id"]:
        lines = []
        with open(id_file, 'r') as f:
            for line in f:
                if not line.startswith("dogfooding-bugs-"):
                    lines.append(line)
        with open(id_file, 'w') as f:
            f.writelines(lines)
        print(f"Cleaned: {id_file}")

def main():
    """Consolidate dogfooding-bugs track."""
    base_dir = Path(__file__).parent.parent / ".vibey" / "roadmap"
    tracks_dir = base_dir / "tracks"
    sprints_dir = base_dir / "sprints"
    tasks_dir = base_dir / "tasks"
    context_dir = base_dir / "context" / "sprints"

    now = datetime.now(timezone.utc).isoformat()

    # Get track ULID from .id file
    track_ulid = None
    with open(tracks_dir / ".id", 'r') as f:
        for line in f:
            if line.startswith("dogfooding-bugs="):
                track_ulid = line.strip().split("=")[1]
                break

    if not track_ulid:
        print("ERROR: Could not find dogfooding-bugs track ULID")
        return

    print(f"Track ULID: {track_ulid}")

    # Remove old files
    print("\n=== Removing old files ===")
    remove_old_files(base_dir)

    # Generate new ULIDs
    sprint_ulids = []
    task_ulids = []

    for sprint in SPRINTS:
        sprint_ulid = generate_ulid()
        time.sleep(0.002)
        sprint_ulids.append(sprint_ulid)

        sprint_task_ulids = []
        for _ in sprint["tasks"]:
            task_ulid = generate_ulid()
            time.sleep(0.002)
            sprint_task_ulids.append(task_ulid)
        task_ulids.append(sprint_task_ulids)

    # Calculate totals
    total_tasks = sum(len(s["tasks"]) for s in SPRINTS)

    # Create sprint refs for track
    sprint_refs = []
    for i, (sprint, sprint_ulid) in enumerate(zip(SPRINTS, sprint_ulids)):
        sprint_refs.append({
            "id": sprint_ulid,
            "name": f"Sprint {sprint['number']}: {sprint['name']}",
            "status": "not_started",
            "estimated_duration": None,
            "tasks_count": len(sprint["tasks"]),
            "started": None
        })

    # Update track file
    track_file = tracks_dir / f"{track_ulid}.yaml"
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
                "sprints_total": len(SPRINTS),
                "sprints_completed": 0,
                "tasks_total": total_tasks,
                "tasks_completed": 0,
                "completion_percent": 0
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
                "last_updated": now,
                "source": "CLI_BUGS.md",
                "notes": "Consolidated from 15 individual bug sprints to 7 thematic sprints"
            },
            "slug": "dogfooding-bugs",
            "criteria": []
        }
    }

    print(f"\n=== Creating consolidated track ===")
    print(f"Updating track: {track_file}")
    with open(track_file, 'w') as f:
        yaml.dump(track_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Create sprint and task files
    sprints_id_entries = []
    tasks_id_entries = []

    for i, (sprint, sprint_ulid, sprint_task_ulids) in enumerate(zip(SPRINTS, sprint_ulids, task_ulids)):
        sprint_slug = f"dogfooding-bugs-{sprint['number']:02d}"

        # Create task refs
        task_refs = []
        for j, task in enumerate(sprint["tasks"]):
            task_slug = f"{sprint_slug}-task-{j+1:03d}"
            task_refs.append({
                "id": task_slug,
                "title": task["title"],
                "status": "not_started"
            })

        # Create depends_on structure
        depends_on = []
        for dep in sprint["depends_on"]:
            depends_on.append({
                "blocker_id": dep,
                "blocker_type": "sprint",
                "required_status": "completed",
                "current_status": "not_started",
                "description": f"Requires {dep} to be completed first",
                "status": "pending",
                "last_checked": None
            })

        # Create sprint YAML
        sprint_data = {
            "sprint": {
                "id": sprint_ulid,
                "track_id": "dogfooding-bugs",
                "roadmap_id": "vibey-framework-v2",
                "name": f"Sprint {sprint['number']}: {sprint['name']}",
                "description": sprint["description"],
                "status": "not_started",
                "created": now,
                "started": None,
                "completed": None,
                "goal": sprint["goal"],
                "success_criteria": sprint["success_criteria"],
                "tasks": task_refs,
                "dependencies": [],
                "blocked_by": [],
                "depends_on": depends_on,
                "deliverables": [],
                "risks": [],
                "metadata": {
                    "bugs_addressed": sprint["bugs"],
                    "priority": sprint["priority"],
                    "consolidated_from": [f"Bug #{b}" for b in sprint["bugs"]]
                },
                "slug": sprint_slug,
                "parent_ref": track_ulid,
                "criteria": [],
                "sequence": sprint["number"]
            }
        }

        sprint_file = sprints_dir / f"{sprint_ulid}.yaml"
        print(f"Creating sprint: {sprint_file}")
        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        sprints_id_entries.append(f"{sprint_slug}={sprint_ulid}")

        # Create task files
        for j, (task, task_ulid) in enumerate(zip(sprint["tasks"], sprint_task_ulids)):
            task_slug = f"{sprint_slug}-task-{j+1:03d}"

            task_data = {
                "task": {
                    "id": task_ulid,
                    "sprint_id": sprint_slug,
                    "track_id": "dogfooding-bugs",
                    "roadmap_id": "vibey-framework-v2",
                    "task_type": task.get("type", "development"),
                    "title": task["title"],
                    "description": None,
                    "status": "not_started",
                    "created": now,
                    "started": None,
                    "completed": None,
                    "assigned_agent": None,
                    "priority": "high" if sprint["priority"] == "critical" else "medium",
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
                        "original_bug": task.get("bug")
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

        # Create context file for this sprint
        context_sprint_dir = context_dir / sprint_slug
        context_sprint_dir.mkdir(parents=True, exist_ok=True)

        bugs_list = ", ".join([f"#{b}" for b in sprint["bugs"]])
        tasks_list = "\n".join([f"{j+1}. **{t['title']}** ({t.get('type', 'development')}, {t.get('complexity', 'medium')} complexity)" for j, t in enumerate(sprint["tasks"])])
        deps_list = "\n".join([f"- {d}" for d in sprint["depends_on"]]) if sprint["depends_on"] else "None (can start immediately)"

        context_content = f"""# Sprint {sprint['number']}: {sprint['name']}

**Bugs Addressed:** {bugs_list}
**Priority:** {sprint['priority'].upper()}
**Status:** NOT_STARTED

---

## Description

{sprint['description']}

---

## Goal

{sprint['goal']}

---

## Success Criteria

{chr(10).join(f"- {c}" for c in sprint['success_criteria'])}

---

## Dependencies

{deps_list}

---

## Tasks ({len(sprint['tasks'])} total)

{tasks_list}

---

## Sprint Plan

### Approach
1. Review affected code and understand current behavior
2. Design solution that maintains backward compatibility
3. Implement changes with comprehensive tests
4. Verify all success criteria are met
5. Update documentation as needed

### Risks
- Changes may affect other parts of the system
- Backward compatibility must be maintained
- Tests must cover edge cases

### Notes
This sprint consolidates the following original bugs:
{chr(10).join(f"- Bug #{b}" for b in sprint['bugs'])}
"""
        context_file = context_sprint_dir / "SPRINT_PLAN.md"
        print(f"Creating context: {context_file}")
        with open(context_file, 'w') as f:
            f.write(context_content)

    # Update .id files
    with open(sprints_dir / ".id", 'a') as f:
        for entry in sprints_id_entries:
            f.write(f"{entry}\n")
    print(f"Updated: {sprints_dir / '.id'}")

    with open(tasks_dir / ".id", 'a') as f:
        for entry in tasks_id_entries:
            f.write(f"{entry}\n")
    print(f"Updated: {tasks_dir / '.id'}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Track ULID: {track_ulid}")
    print(f"Sprints: 15 → 7")
    print(f"Tasks: 63 → {total_tasks}")
    print(f"Context files: 15 → 7")

    print("\n=== Sprint Order ===")
    for i, sprint in enumerate(SPRINTS):
        deps = f" (depends on: {', '.join(sprint['depends_on'])})" if sprint['depends_on'] else ""
        print(f"{sprint['number']}. {sprint['name']} [{sprint['priority'].upper()}] - {len(sprint['tasks'])} tasks{deps}")

    return track_ulid

if __name__ == "__main__":
    track_ulid = main()
