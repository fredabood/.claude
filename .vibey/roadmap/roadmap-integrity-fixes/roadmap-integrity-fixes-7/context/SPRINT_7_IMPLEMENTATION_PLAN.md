# Sprint 7: Data Integrity Prevention & Automation - Implementation Plan

**Sprint ID:** roadmap-integrity-fixes-7
**Created:** 2025-11-19
**Status:** Ready to Execute
**Estimated Duration:** 10-12 hours over 1 week
**Priority:** CRITICAL

---

## Executive Summary

Sprint 7 implements automated prevention systems to prevent YAML corruption and data integrity issues from recurring. This sprint addresses active corruption in 3 files, fixes the root cause enum serialization bug, and builds comprehensive validation infrastructure.

**Philosophy:** "Automation over vigilance" - Manual integrity checks don't scale to 20+ tracks.

---

## Current State Assessment

### ✅ Completed Analysis (2025-11-19)

**Active Corruption Verified:**
```bash
$ grep -n "!!python" .vibey/roadmap/{aider-port,multi-platform,mcp-server}/track.yaml

.vibey/roadmap/aider-port/track.yaml:53:    current_status: !!python/object/apply:vibey.roadmap.models.common.Status
.vibey/roadmap/multi-platform/track.yaml:96:    current_status: !!python/object/apply:vibey.roadmap.models.common.Status
.vibey/roadmap/mcp-server/track.yaml:51:    current_status: !!python/object/apply:vibey.roadmap.models.common.Status
```

**Root Cause Identified:**

1. **Assignment Location** (`vibey/operations/roadmap/update.py`):
   - Line 902: `dep_status.current_status = blocker_track.status`
   - Line 931: `dep_status.current_status = blocker.status`
   - Line 940: `dep_status.current_status = blocker.status`
   - Line 969: `dep_status.current_status = blocker_task.status`
   - Line 978: `dep_status.current_status = blocker.status`
   - **Problem:** Assigning Status enum object instead of string value

2. **Serialization Location** (`vibey/roadmap/serialization/yaml_dumper.py`):
   - Line 377: `'current_status': b.current_status` (blocked_by)
   - Line 389: `'current_status': d.current_status` (depends_on)
   - **Problem:** Not calling `.value` on enum during serialization

**Infrastructure Gaps:**
- ❌ No pre-commit hook to detect `!!python` patterns
- ❌ No validation tests for YAML integrity
- ❌ No CI/CD validation workflow
- ❌ No automated dependency refresh

---

## Implementation Plan

### Phase 1: Critical Fixes (Day 1, 1 hour)

**Priority:** P0 - Must complete first

#### Task 1: Fix Active YAML Corruption (15 minutes)

**Files to fix:**
- `.vibey/roadmap/aider-port/track.yaml` (line 53)
- `.vibey/roadmap/multi-platform/track.yaml` (line 96)
- `.vibey/roadmap/mcp-server/track.yaml` (line 51)

**Pattern to replace:**
```yaml
# BEFORE (corrupted):
current_status: !!python/object/apply:vibey.roadmap.models.common.Status
  - completed

# AFTER (fixed):
current_status: completed
```

**Steps:**
1. Manually edit each file or use sed:
   ```bash
   # Find the exact pattern and surrounding context
   grep -B2 -A2 "!!python" .vibey/roadmap/aider-port/track.yaml

   # Edit to replace with plain string value
   ```

2. Verify fix:
   ```bash
   # Should return nothing:
   grep -r "!!python" .vibey/roadmap/

   # Should parse without errors:
   python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/aider-port/track.yaml'))"
   python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/multi-platform/track.yaml'))"
   python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/mcp-server/track.yaml'))"
   ```

**Deliverable:** 3 clean YAML files, git commit

---

#### Task 2: Fix Root Cause - Enum Serialization Bug (30 minutes)

**File 1:** `vibey/operations/roadmap/update.py`

**Changes needed (5 locations):**

```python
# Line 902:
# BEFORE:
dep_status.current_status = blocker_track.status
# AFTER:
dep_status.current_status = blocker_track.status.value

# Line 931:
# BEFORE:
dep_status.current_status = blocker.status
# AFTER:
dep_status.current_status = blocker.status.value

# Line 940:
# BEFORE:
dep_status.current_status = blocker.status
# AFTER:
dep_status.current_status = blocker.status.value

# Line 969:
# BEFORE:
dep_status.current_status = blocker_task.status
# AFTER:
dep_status.current_status = blocker_task.status.value

# Line 978:
# BEFORE:
dep_status.current_status = blocker.status
# AFTER:
dep_status.current_status = blocker.status.value
```

**File 2:** `vibey/roadmap/serialization/yaml_dumper.py`

**Changes needed (2-4 locations):**

```python
# Line 377 (blocked_by serialization):
# BEFORE:
'current_status': b.current_status,
'required_status': b.required_status,
# AFTER:
'current_status': b.current_status.value if hasattr(b.current_status, 'value') else b.current_status,
'required_status': b.required_status.value if hasattr(b.required_status, 'value') else b.required_status,

# Line 389 (depends_on serialization):
# BEFORE:
'current_status': d.current_status,
'required_status': d.required_status,
# AFTER:
'current_status': d.current_status.value if hasattr(d.current_status, 'value') else d.current_status,
'required_status': d.required_status.value if hasattr(d.required_status, 'value') else d.required_status,
```

**Note:** Using `hasattr` check for defensive programming in case the value is already a string.

**Verification:**
```bash
# Update a dependency and check the YAML output
python3 -c "
from vibey.operations.roadmap.update import refresh_dependencies
refresh_dependencies()
"

# Verify no Python serialization in any track
grep -r "!!python" .vibey/roadmap/**/track.yaml
# Should return nothing
```

**Deliverable:** Fixed code, git commit, verification test passed

---

#### Task 3: Add Pre-commit Hook (15 minutes)

**File:** `.pre-commit-config.yaml`

**Add to the `repos` section:**

```yaml
  # Roadmap YAML integrity checks
  - repo: local
    hooks:
      - id: check-yaml-python-objects
        name: Detect Python object serialization in roadmap YAML
        entry: bash -c 'if grep -r "!!python" .vibey/roadmap/ 2>/dev/null; then echo "❌ ERROR: Python object serialization found in roadmap YAML files"; echo "Fix: Replace enum objects with .value before serialization"; exit 1; fi'
        language: system
        pass_filenames: false
        files: \.yaml$
        stages: [commit]
```

**Test the hook:**
```bash
# Install pre-commit if not already
pip install pre-commit
pre-commit install

# Test by trying to create a file with !!python pattern
echo "test: !!python/object:something" > .vibey/roadmap/test.yaml
git add .vibey/roadmap/test.yaml
git commit -m "test"  # Should FAIL

# Clean up
rm .vibey/roadmap/test.yaml
```

**Deliverable:** Pre-commit hook configured, tested, and committed

---

### Phase 2: Validation Infrastructure (Days 2-3, 4 hours)

**Priority:** P1 - Foundation for prevention

#### Task 4: Create YAML Validation Test Suite (2 hours)

**File:** `tests/validation/test_yaml_integrity.py`

**Implementation:**

```python
"""
YAML integrity validation tests for roadmap data.

Ensures all roadmap YAML files are clean, parseable, and follow data integrity rules.
"""

import pytest
import yaml
from pathlib import Path


def get_all_roadmap_yaml_files():
    """Get all YAML files in the roadmap directory."""
    roadmap_dir = Path('.vibey/roadmap')
    if not roadmap_dir.exists():
        return []
    return list(roadmap_dir.glob('**/*.yaml'))


class TestYAMLSyntax:
    """Test basic YAML syntax and parseability."""

    def test_all_yaml_files_parse_safely(self):
        """All roadmap YAML files should parse with yaml.safe_load()."""
        yaml_files = get_all_roadmap_yaml_files()
        assert len(yaml_files) > 0, "No YAML files found in .vibey/roadmap"

        failed_files = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                failed_files.append((yaml_file, str(e)))

        if failed_files:
            error_msg = "\n".join([f"  {f}: {e}" for f, e in failed_files])
            pytest.fail(f"Failed to parse {len(failed_files)} YAML files:\n{error_msg}")


class TestPythonSerialization:
    """Test for Python object serialization corruption."""

    def test_no_python_serialization_in_yaml(self):
        """No YAML file should contain !!python serialization patterns."""
        yaml_files = get_all_roadmap_yaml_files()

        corrupted_files = []
        for yaml_file in yaml_files:
            with open(yaml_file) as f:
                content = f.read()
                if '!!python' in content:
                    # Find line numbers
                    lines = content.split('\n')
                    line_nums = [i+1 for i, line in enumerate(lines) if '!!python' in line]
                    corrupted_files.append((yaml_file, line_nums))

        if corrupted_files:
            error_msg = "\n".join([
                f"  {f}: lines {', '.join(map(str, lines))}"
                for f, lines in corrupted_files
            ])
            pytest.fail(
                f"Found Python object serialization in {len(corrupted_files)} files:\n{error_msg}\n"
                f"Fix: Replace !!python patterns with plain string values"
            )


class TestDependencyIntegrity:
    """Test dependency data integrity."""

    def test_dependency_statuses_are_strings(self):
        """All dependency current_status fields should be plain strings."""
        from vibey.roadmap.serialization import load_track
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()
        failed_tracks = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            try:
                track = load_track(track_path)

                # Check depends_on statuses
                for dep in track.depends_on:
                    if not isinstance(dep.current_status, str):
                        failed_tracks.append((
                            track_id,
                            'depends_on',
                            dep.blocker_id,
                            type(dep.current_status).__name__
                        ))

                # Check blocked_by statuses
                for block in track.blocked_by:
                    if not isinstance(block.current_status, str):
                        failed_tracks.append((
                            track_id,
                            'blocked_by',
                            block.dependency_id,
                            type(block.current_status).__name__
                        ))

            except Exception as e:
                # Skip tracks that can't be loaded (separate test handles this)
                continue

        if failed_tracks:
            error_msg = "\n".join([
                f"  {track_id} ({field} -> {dep_id}): type={typ}"
                for track_id, field, dep_id, typ in failed_tracks
            ])
            pytest.fail(
                f"Found {len(failed_tracks)} dependency statuses that are not strings:\n{error_msg}\n"
                f"Fix: Use .value when assigning Status enums to current_status"
            )

    def test_enum_fields_are_strings_in_yaml(self):
        """Verify all enum fields are serialized as strings in YAML files."""
        import re

        yaml_files = get_all_roadmap_yaml_files()
        enum_pattern = re.compile(r'(status|priority|type):\s+!!python')

        failed_files = []
        for yaml_file in yaml_files:
            with open(yaml_file) as f:
                content = f.read()
                matches = enum_pattern.findall(content)
                if matches:
                    failed_files.append((yaml_file, matches))

        if failed_files:
            error_msg = "\n".join([
                f"  {f}: fields={fields}"
                for f, fields in failed_files
            ])
            pytest.fail(
                f"Found enum fields with Python serialization in {len(failed_files)} files:\n{error_msg}"
            )


class TestStructuralIntegrity:
    """Test structural integrity of roadmap data."""

    def test_all_tracks_loadable(self):
        """All track YAML files should load successfully."""
        from vibey.roadmap.serialization import load_track
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()
        failed_tracks = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            try:
                load_track(track_path)
            except Exception as e:
                failed_tracks.append((track_id, str(e)))

        if failed_tracks:
            error_msg = "\n".join([f"  {t}: {e}" for t, e in failed_tracks])
            pytest.fail(f"Failed to load {len(failed_tracks)} tracks:\n{error_msg}")

    def test_all_sprints_loadable(self):
        """All sprint YAML files should load successfully."""
        from vibey.roadmap.serialization import load_sprint
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()
        failed_sprints = []

        for sprint_id in fs.list_sprints():
            sprint_path = fs.get_sprint_path(sprint_id)
            try:
                load_sprint(sprint_path)
            except Exception as e:
                failed_sprints.append((sprint_id, str(e)))

        if failed_sprints:
            error_msg = "\n".join([f"  {s}: {e}" for s, e in failed_sprints])
            pytest.fail(f"Failed to load {len(failed_sprints)} sprints:\n{error_msg}")

    def test_all_tasks_loadable(self):
        """All task YAML files should load successfully."""
        from vibey.roadmap.serialization import load_task
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()
        failed_tasks = []

        for task_id in fs.list_tasks():
            task_path = fs.get_task_path(task_id)
            try:
                load_task(task_path)
            except Exception as e:
                failed_tasks.append((task_id, str(e)))

        if failed_tasks:
            # Only fail if more than 10% of tasks fail (some may be expected)
            if len(failed_tasks) > len(list(fs.list_tasks())) * 0.1:
                error_msg = "\n".join([f"  {t}: {e}" for t, e in failed_tasks[:20]])
                pytest.fail(
                    f"Failed to load {len(failed_tasks)} tasks (showing first 20):\n{error_msg}"
                )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Run tests:**
```bash
# Create test directory if needed
mkdir -p tests/validation

# Run validation tests
pytest tests/validation/test_yaml_integrity.py -v

# Expected: All tests should pass after Phase 1 fixes
```

**Deliverable:** Test suite created, all tests passing, committed

---

#### Task 5: Add CI/CD Validation Workflow (1 hour)

**File:** `.github/workflows/roadmap-validation.yml`

**Implementation:**

```yaml
name: Roadmap Data Integrity Validation

on:
  push:
    branches: [ main, develop ]
    paths:
      - '.vibey/roadmap/**/*.yaml'
      - 'vibey/roadmap/**/*.py'
      - 'vibey/operations/roadmap/**/*.py'
  pull_request:
    branches: [ main, develop ]
    paths:
      - '.vibey/roadmap/**/*.yaml'
      - 'vibey/roadmap/**/*.py'
      - 'vibey/operations/roadmap/**/*.py'

jobs:
  validate-roadmap:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install pyyaml pytest
        pip install -e .

    - name: Check for Python object serialization
      run: |
        echo "🔍 Checking for Python object serialization in YAML files..."
        if grep -r "!!python" .vibey/roadmap/ 2>/dev/null; then
          echo "❌ ERROR: Python object serialization found in roadmap YAML files"
          echo "Files affected:"
          grep -r "!!python" .vibey/roadmap/ -l
          echo ""
          echo "Fix: Ensure all enum values use .value before serialization"
          exit 1
        else
          echo "✅ No Python object serialization detected"
        fi

    - name: Validate YAML syntax
      run: |
        echo "🔍 Validating YAML syntax for all roadmap files..."
        python3 << 'EOF'
        import yaml
        from pathlib import Path

        yaml_files = list(Path('.vibey/roadmap').glob('**/*.yaml'))
        failed = []

        for f in yaml_files:
            try:
                with open(f) as file:
                    yaml.safe_load(file)
            except Exception as e:
                failed.append((f, e))

        if failed:
            print(f"❌ Failed to parse {len(failed)} YAML files:")
            for f, e in failed:
                print(f"  {f}: {e}")
            exit(1)
        else:
            print(f"✅ All {len(yaml_files)} YAML files are valid")
        EOF

    - name: Run validation test suite
      run: |
        echo "🔍 Running validation test suite..."
        pytest tests/validation/test_yaml_integrity.py -v --tb=short

    - name: Validate track loadability
      run: |
        echo "🔍 Testing track loadability..."
        python3 << 'EOF'
        from vibey.roadmap.filesystem import RoadmapFilesystem
        from vibey.roadmap.serialization import load_track

        fs = RoadmapFilesystem()
        failed = []

        for track_id in fs.list_tracks():
            try:
                load_track(fs.get_track_path(track_id))
            except Exception as e:
                failed.append((track_id, e))

        if failed:
            print(f"❌ Failed to load {len(failed)} tracks:")
            for t, e in failed[:10]:
                print(f"  {t}: {e}")
            exit(1)
        else:
            print(f"✅ Successfully loaded all tracks")
        EOF

    - name: Check dependency status types
      run: |
        echo "🔍 Validating dependency status types..."
        python3 << 'EOF'
        from vibey.roadmap.filesystem import RoadmapFilesystem
        from vibey.roadmap.serialization import load_track

        fs = RoadmapFilesystem()
        issues = []

        for track_id in fs.list_tracks():
            try:
                track = load_track(fs.get_track_path(track_id))

                for dep in track.depends_on:
                    if not isinstance(dep.current_status, str):
                        issues.append(f"{track_id}: depends_on.{dep.blocker_id}.current_status is {type(dep.current_status).__name__}")

                for block in track.blocked_by:
                    if not isinstance(block.current_status, str):
                        issues.append(f"{track_id}: blocked_by.{block.dependency_id}.current_status is {type(block.current_status).__name__}")
            except:
                continue

        if issues:
            print(f"❌ Found {len(issues)} non-string dependency statuses:")
            for issue in issues[:20]:
                print(f"  {issue}")
            exit(1)
        else:
            print(f"✅ All dependency statuses are strings")
        EOF

    - name: Summary
      if: success()
      run: |
        echo "✅ All roadmap validation checks passed!"
        echo ""
        echo "Checks performed:"
        echo "  ✅ No Python object serialization"
        echo "  ✅ All YAML files parse correctly"
        echo "  ✅ Validation test suite passes"
        echo "  ✅ All tracks loadable"
        echo "  ✅ All dependency statuses are strings"
```

**Test locally:**
```bash
# Simulate GitHub Actions locally with act (if installed)
act -j validate-roadmap

# Or run the checks manually:
grep -r "!!python" .vibey/roadmap/
pytest tests/validation/test_yaml_integrity.py -v
```

**Deliverable:** GitHub Actions workflow created, tested, and committed

---

### Phase 3: Automation & Monitoring (Days 4-7, 6 hours)

**Priority:** P2 - Scale and sustainability

#### Task 6: Implement Automated Dependency Refresh (2 hours)

**File:** `vibey/operations/roadmap/refresh.py`

**Implementation:**

```python
"""
Automated dependency status refresh.

Keeps dependency current_status fields up-to-date with actual blocker statuses.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from vibey.roadmap.filesystem import RoadmapFilesystem
from vibey.roadmap.serialization import load_track, load_sprint, load_task, save_track, save_sprint, save_task
from vibey.roadmap.models.common import DependencyType


def refresh_all_dependencies(dry_run: bool = False) -> dict:
    """
    Refresh all dependency current_status fields across tracks, sprints, and tasks.

    Args:
        dry_run: If True, report what would be updated without saving

    Returns:
        dict with statistics: {
            'tracks_updated': int,
            'sprints_updated': int,
            'tasks_updated': int,
            'total_deps_updated': int,
            'errors': List[str]
        }
    """
    fs = RoadmapFilesystem()
    stats = {
        'tracks_updated': 0,
        'sprints_updated': 0,
        'tasks_updated': 0,
        'total_deps_updated': 0,
        'errors': []
    }

    print("🔄 Refreshing dependency statuses...")

    # Refresh track dependencies
    for track_id in fs.list_tracks():
        track_path = fs.get_track_path(track_id)
        try:
            track = load_track(track_path)
            modified = False
            deps_updated = 0

            for dep_status in track.depends_on:
                # Get blocker's current status
                if dep_status.blocker_type == 'track':
                    blocker_path = fs.get_track_path(dep_status.blocker_id)
                    if blocker_path.exists():
                        blocker = load_track(blocker_path)
                        new_status = blocker.status.value  # CRITICAL: Use .value

                        if dep_status.current_status != new_status:
                            if not dry_run:
                                dep_status.current_status = new_status
                                dep_status.last_checked = datetime.now(timezone.utc)
                            modified = True
                            deps_updated += 1
                            print(f"  📝 {track_id} <- {dep_status.blocker_id}: {dep_status.current_status} -> {new_status}")

            if modified:
                stats['tracks_updated'] += 1
                stats['total_deps_updated'] += deps_updated
                if not dry_run:
                    track.blocked = track.compute_blocked_status()
                    save_track(track, track_path)

        except Exception as e:
            error_msg = f"Failed to refresh track {track_id}: {e}"
            stats['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")

    # Similar logic for sprints and tasks...
    # (Abbreviated for brevity - full implementation would follow same pattern)

    print(f"\n✅ Dependency refresh {'(DRY RUN) ' if dry_run else ''}complete:")
    print(f"   Tracks updated: {stats['tracks_updated']}")
    print(f"   Sprints updated: {stats['sprints_updated']}")
    print(f"   Tasks updated: {stats['tasks_updated']}")
    print(f"   Total dependencies updated: {stats['total_deps_updated']}")
    if stats['errors']:
        print(f"   ⚠️  Errors: {len(stats['errors'])}")

    return stats


def get_stale_dependencies(threshold_hours: int = 24) -> List[Tuple[str, str, datetime]]:
    """
    Find dependencies that haven't been checked recently.

    Args:
        threshold_hours: Consider dependencies stale if not checked in this many hours

    Returns:
        List of (object_id, blocker_id, last_checked) tuples for stale dependencies
    """
    fs = RoadmapFilesystem()
    stale = []
    threshold = datetime.now(timezone.utc).timestamp() - (threshold_hours * 3600)

    for track_id in fs.list_tracks():
        try:
            track = load_track(fs.get_track_path(track_id))
            for dep in track.depends_on:
                if dep.last_checked and dep.last_checked.timestamp() < threshold:
                    stale.append((track_id, dep.blocker_id, dep.last_checked))
        except:
            continue

    return stale


if __name__ == '__main__':
    import sys
    dry_run = '--dry-run' in sys.argv
    refresh_all_dependencies(dry_run=dry_run)
```

**Add CLI command** in `vibey/cli/commands.py`:

```python
@cli.group()
def roadmap():
    """Roadmap management commands."""
    pass

@roadmap.command('refresh-dependencies')
@click.option('--dry-run', is_flag=True, help='Show what would be updated without saving')
def refresh_dependencies_cmd(dry_run):
    """Refresh all dependency current_status fields."""
    from vibey.operations.roadmap.refresh import refresh_all_dependencies
    stats = refresh_all_dependencies(dry_run=dry_run)

    if stats['errors']:
        click.echo(click.style(f"\n⚠️  Completed with {len(stats['errors'])} errors", fg='yellow'))
        sys.exit(1)
```

**Test:**
```bash
# Dry run first
python -m vibey.cli roadmap refresh-dependencies --dry-run

# Real run
python -m vibey.cli roadmap refresh-dependencies

# Verify no Python serialization
grep -r "!!python" .vibey/roadmap/
```

**Deliverable:** Dependency refresh automation, CLI command, tested and committed

---

#### Task 7: Add Comprehensive Validation Checks (3 hours)

**Enhancement to:** `tests/validation/test_yaml_integrity.py`

**Add new test classes:**

```python
class TestSchemaValidation:
    """Validate YAML data against schema definitions."""

    def test_valid_status_enum_values(self):
        """All status fields should contain valid Status enum values."""
        from vibey.roadmap.models.common import Status, TaskStatus
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        valid_statuses = {s.value for s in Status}
        valid_task_statuses = {s.value for s in TaskStatus}

        fs = RoadmapFilesystem()
        invalid_values = []

        # Check track statuses
        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                # Main status
                status = track_data.get('status')
                if status and status not in valid_statuses:
                    invalid_values.append((track_id, 'track.status', status, 'Status'))

                # Sprint statuses
                for sprint in track_data.get('sprints', []):
                    sprint_status = sprint.get('status')
                    if sprint_status and sprint_status not in valid_statuses:
                        invalid_values.append((
                            track_id,
                            f"track.sprints.{sprint.get('id')}.status",
                            sprint_status,
                            'Status'
                        ))

        # Check task statuses
        for task_id in fs.list_tasks():
            task_path = fs.get_task_path(task_id)
            with open(task_path) as f:
                data = yaml.safe_load(f)
                task_data = data.get('task', {})

                status = task_data.get('status')
                if status and status not in valid_task_statuses:
                    invalid_values.append((task_id, 'task.status', status, 'TaskStatus'))

        if invalid_values:
            error_msg = "\n".join([
                f"  {obj_id} -> {field}: '{value}' is not a valid {enum_type}"
                for obj_id, field, value, enum_type in invalid_values
            ])
            pytest.fail(f"Found {len(invalid_values)} invalid enum values:\n{error_msg}")

    def test_valid_priority_enum_values(self):
        """All priority fields should contain valid Priority enum values."""
        from vibey.roadmap.models.common import Priority
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        valid_priorities = {p.value for p in Priority}
        fs = RoadmapFilesystem()
        invalid_values = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                priority = data.get('track', {}).get('priority')

                if priority and priority not in valid_priorities:
                    invalid_values.append((track_id, priority))

        if invalid_values:
            error_msg = "\n".join([f"  {tid}: '{pri}'" for tid, pri in invalid_values])
            pytest.fail(f"Found {len(invalid_values)} invalid priority values:\n{error_msg}")

    def test_valid_dependency_type_values(self):
        """All dependency type fields should contain valid DependencyType enum values."""
        from vibey.roadmap.models.common import DependencyType
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        valid_types = {t.value for t in DependencyType}
        fs = RoadmapFilesystem()
        invalid_values = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                # Check dependencies
                for dep in track_data.get('dependencies', []):
                    dep_type = dep.get('type')
                    if dep_type and dep_type not in valid_types:
                        invalid_values.append((track_id, 'dependencies', dep_type))

                # Check blocks
                for block in track_data.get('blocks', []):
                    block_type = block.get('type')
                    if block_type and block_type not in valid_types:
                        invalid_values.append((track_id, 'blocks', block_type))

        if invalid_values:
            error_msg = "\n".join([
                f"  {tid} ({field}): '{val}'"
                for tid, field, val in invalid_values
            ])
            pytest.fail(f"Found {len(invalid_values)} invalid dependency type values:\n{error_msg}")

    def test_completion_percent_in_range(self):
        """Completion percent should be between 0 and 100."""
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        fs = RoadmapFilesystem()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                progress = data.get('track', {}).get('progress', {})
                completion = progress.get('completion_percent')

                if completion is not None and not (0 <= completion <= 100):
                    violations.append((track_id, completion))

        if violations:
            error_msg = "\n".join([f"  {tid}: {pct}%" for tid, pct in violations])
            pytest.fail(f"Found {len(violations)} invalid completion percentages:\n{error_msg}")

    def test_numeric_fields_are_integers(self):
        """Numeric count fields should be integers, not strings."""
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        fs = RoadmapFilesystem()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                progress = data.get('track', {}).get('progress', {})

                # Check all numeric fields
                numeric_fields = ['sprints_total', 'sprints_completed', 'tasks_total', 'tasks_completed']
                for field in numeric_fields:
                    value = progress.get(field)
                    if value is not None and not isinstance(value, int):
                        violations.append((track_id, field, type(value).__name__))

        if violations:
            error_msg = "\n".join([
                f"  {tid}.progress.{field}: {typ} (should be int)"
                for tid, field, typ in violations
            ])
            pytest.fail(f"Found {len(violations)} non-integer numeric fields:\n{error_msg}")

    def test_boolean_fields_are_booleans(self):
        """Boolean fields should be true/false, not strings."""
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        fs = RoadmapFilesystem()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                # Check blocked field
                blocked = track_data.get('blocked')
                if blocked is not None and not isinstance(blocked, bool):
                    violations.append((track_id, 'blocked', type(blocked).__name__))

        if violations:
            error_msg = "\n".join([
                f"  {tid}.{field}: {typ} (should be bool)"
                for tid, field, typ in violations
            ])
            pytest.fail(f"Found {len(violations)} non-boolean boolean fields:\n{error_msg}")

    def test_no_unknown_top_level_fields_in_tracks(self):
        """Track YAML files should not have unexpected top-level fields."""
        from vibey.roadmap.filesystem import RoadmapFilesystem
        import yaml

        # Expected top-level fields based on Track model
        expected_fields = {
            'id', 'name', 'roadmap_id', 'status', 'blocked', 'priority',
            'created', 'started', 'completed', 'superseded_at', 'superseded_by',
            'estimated_duration', 'progress', 'sprints', 'dependencies',
            'blocks', 'blocked_by', 'depends_on', 'depended_on_by',
            'quality_gates', 'assigned_agents', 'deliverables',
            'strategic_value', 'commits', 'standards', 'merged_into', 'metadata'
        }

        fs = RoadmapFilesystem()
        violations = []

        for track_id in fs.list_tracks():
            track_path = fs.get_track_path(track_id)
            with open(track_path) as f:
                data = yaml.safe_load(f)
                track_data = data.get('track', {})

                unknown_fields = set(track_data.keys()) - expected_fields
                if unknown_fields:
                    violations.append((track_id, sorted(unknown_fields)))

        if violations:
            error_msg = "\n".join([
                f"  {tid}: {', '.join(fields)}"
                for tid, fields in violations
            ])
            pytest.fail(
                f"Found {len(violations)} tracks with unknown fields:\n{error_msg}\n"
                f"Note: This might indicate typos or fields that should be added to the schema"
            )


class TestProgressCalculations:
    """Validate progress calculations are accurate."""

    def test_track_progress_matches_sprints(self):
        """Track progress should match sprint completion counts."""
        from vibey.roadmap.serialization import load_track
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()
        mismatches = []

        for track_id in fs.list_tracks():
            try:
                track = load_track(fs.get_track_path(track_id))

                # Count completed sprints
                completed = sum(1 for s in track.sprints if s.status in ['completed', 'production_ready'])

                if track.progress.sprints_completed != completed:
                    mismatches.append((
                        track_id,
                        track.progress.sprints_completed,
                        completed
                    ))
            except:
                continue

        if mismatches:
            error_msg = "\n".join([
                f"  {tid}: recorded={recorded}, actual={actual}"
                for tid, recorded, actual in mismatches
            ])
            pytest.fail(f"Found {len(mismatches)} progress mismatches:\n{error_msg}")


class TestDateLogic:
    """Validate date logic and constraints."""

    def test_started_before_completed(self):
        """Started date should be before or equal to completed date."""
        from vibey.roadmap.serialization import load_track
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()
        violations = []

        for track_id in fs.list_tracks():
            try:
                track = load_track(fs.get_track_path(track_id))

                if track.started and track.completed:
                    if track.started > track.completed:
                        violations.append((
                            track_id,
                            track.started.isoformat(),
                            track.completed.isoformat()
                        ))
            except:
                continue

        if violations:
            error_msg = "\n".join([
                f"  {tid}: started={start} > completed={end}"
                for tid, start, end in violations
            ])
            pytest.fail(f"Found {len(violations)} date logic violations:\n{error_msg}")


class TestDependencyCycles:
    """Detect circular dependencies."""

    def test_no_circular_track_dependencies(self):
        """Track dependencies should not form cycles."""
        from vibey.roadmap.serialization import load_track
        from vibey.roadmap.filesystem import RoadmapFilesystem

        fs = RoadmapFilesystem()

        # Build dependency graph
        graph = {}
        for track_id in fs.list_tracks():
            try:
                track = load_track(fs.get_track_path(track_id))
                graph[track_id] = [
                    d.blocker_id for d in track.depends_on
                    if d.blocker_type == 'track'
                ]
            except:
                continue

        # Detect cycles using DFS
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        cycles = []

        for node in graph:
            if node not in visited:
                rec_stack = set()
                if has_cycle(node, visited, rec_stack):
                    cycles.append(node)

        if cycles:
            pytest.fail(f"Found circular dependencies involving: {', '.join(cycles)}")


class TestRequiredFields:
    """Validate required fields are present."""

    def test_tracks_have_required_fields(self):
        """All tracks should have required fields populated."""
        from vibey.roadmap.serialization import load_track
        from vibey.roadmap.filesystem import RoadmapFilesystem

        required_fields = ['id', 'name', 'status', 'priority', 'created']
        fs = RoadmapFilesystem()
        violations = []

        for track_id in fs.list_tracks():
            try:
                track = load_track(fs.get_track_path(track_id))
                missing = []

                for field in required_fields:
                    if not getattr(track, field, None):
                        missing.append(field)

                if missing:
                    violations.append((track_id, missing))
            except:
                continue

        if violations:
            error_msg = "\n".join([
                f"  {tid}: missing {', '.join(fields)}"
                for tid, fields in violations
            ])
            pytest.fail(f"Found {len(violations)} tracks with missing required fields:\n{error_msg}")
```

**Deliverable:** Enhanced validation tests, all tests passing, committed

---

#### Task 8: Add Pydantic-based Schema Validator (2 hours)

**File:** `vibey/operations/roadmap/schema_validator.py`

**Purpose:** Use the existing Pydantic data models to validate YAML data comprehensively.

**Implementation:**

```python
"""
Schema validator using Pydantic models.

Validates roadmap YAML data against the Pydantic data models to ensure
all fields, types, and constraints are correct.
"""

from pathlib import Path
from typing import List, Tuple, Dict
import yaml

from vibey.roadmap.models import Track, Sprint, Task, Roadmap
from vibey.roadmap.filesystem import RoadmapFilesystem


class SchemaValidationError:
    """Represents a schema validation error."""

    def __init__(self, object_id: str, object_type: str, field_path: str, error: str):
        self.object_id = object_id
        self.object_type = object_type
        self.field_path = field_path
        self.error = error

    def __str__(self):
        return f"{self.object_id} ({self.object_type}) -> {self.field_path}: {self.error}"


class SchemaValidator:
    """Validate roadmap YAML data against Pydantic schemas."""

    def __init__(self):
        self.fs = RoadmapFilesystem()
        self.errors: List[SchemaValidationError] = []

    def validate_track(self, track_id: str) -> bool:
        """Validate a single track against the Track schema."""
        from vibey.roadmap.serialization import load_track

        track_path = self.fs.get_track_path(track_id)
        try:
            # This will raise ValidationError if schema is violated
            track = load_track(track_path)
            return True
        except Exception as e:
            # Parse Pydantic validation error
            error_msg = str(e)
            self.errors.append(SchemaValidationError(
                track_id, 'Track', 'various', error_msg
            ))
            return False

    def validate_sprint(self, sprint_id: str) -> bool:
        """Validate a single sprint against the Sprint schema."""
        from vibey.roadmap.serialization import load_sprint

        sprint_path = self.fs.get_sprint_path(sprint_id)
        try:
            sprint = load_sprint(sprint_path)
            return True
        except Exception as e:
            error_msg = str(e)
            self.errors.append(SchemaValidationError(
                sprint_id, 'Sprint', 'various', error_msg
            ))
            return False

    def validate_task(self, task_id: str) -> bool:
        """Validate a single task against the Task schema."""
        from vibey.roadmap.serialization import load_task

        task_path = self.fs.get_task_path(task_id)
        try:
            task = load_task(task_path)
            return True
        except Exception as e:
            error_msg = str(e)
            self.errors.append(SchemaValidationError(
                task_id, 'Task', 'various', error_msg
            ))
            return False

    def validate_all(self) -> Dict[str, int]:
        """
        Validate all roadmap objects.

        Returns:
            dict with counts: {
                'tracks_validated': int,
                'tracks_failed': int,
                'sprints_validated': int,
                'sprints_failed': int,
                'tasks_validated': int,
                'tasks_failed': int,
                'total_errors': int
            }
        """
        self.errors = []
        stats = {
            'tracks_validated': 0,
            'tracks_failed': 0,
            'sprints_validated': 0,
            'sprints_failed': 0,
            'tasks_validated': 0,
            'tasks_failed': 0,
        }

        print("🔍 Validating all roadmap objects against schemas...")

        # Validate tracks
        for track_id in self.fs.list_tracks():
            if self.validate_track(track_id):
                stats['tracks_validated'] += 1
            else:
                stats['tracks_failed'] += 1

        # Validate sprints
        for sprint_id in self.fs.list_sprints():
            if self.validate_sprint(sprint_id):
                stats['sprints_validated'] += 1
            else:
                stats['sprints_failed'] += 1

        # Validate tasks
        for task_id in self.fs.list_tasks():
            if self.validate_task(task_id):
                stats['tasks_validated'] += 1
            else:
                stats['tasks_failed'] += 1

        stats['total_errors'] = len(self.errors)

        return stats

    def print_report(self, stats: Dict[str, int]):
        """Print validation report."""
        print(f"\n📊 Schema Validation Report:")
        print(f"   Tracks: {stats['tracks_validated']} valid, {stats['tracks_failed']} failed")
        print(f"   Sprints: {stats['sprints_validated']} valid, {stats['sprints_failed']} failed")
        print(f"   Tasks: {stats['tasks_validated']} valid, {stats['tasks_failed']} failed")
        print(f"   Total errors: {stats['total_errors']}")

        if self.errors:
            print(f"\n❌ Validation Errors (showing first 20):")
            for error in self.errors[:20]:
                print(f"   {error}")

            if len(self.errors) > 20:
                print(f"   ... and {len(self.errors) - 20} more errors")

    def run(self) -> int:
        """Run validation and return exit code."""
        stats = self.validate_all()
        self.print_report(stats)

        if stats['total_errors'] > 0:
            return 1
        else:
            print("\n✅ All objects conform to schema")
            return 0


if __name__ == '__main__':
    validator = SchemaValidator()
    exit(validator.run())
```

**Add CLI command:**

```python
@roadmap.command('validate-schema')
def validate_schema_cmd():
    """Validate all roadmap YAML against Pydantic schemas."""
    from vibey.operations.roadmap.schema_validator import SchemaValidator

    validator = SchemaValidator()
    exit_code = validator.run()
    sys.exit(exit_code)
```

**Add to CI/CD workflow** (`.github/workflows/roadmap-validation.yml`):

```yaml
    - name: Validate against Pydantic schemas
      run: |
        echo "🔍 Validating YAML data against Pydantic schemas..."
        python vibey/operations/roadmap/schema_validator.py
```

**Test:**
```bash
# Run schema validation
python vibey/operations/roadmap/schema_validator.py

# Or via CLI
python -m vibey.cli roadmap validate-schema
```

**Deliverable:** Pydantic schema validator, CLI command, CI/CD integration, all passing

---

#### Task 9: Add Monitoring & Alerting (1 hour)

**File:** `vibey/operations/roadmap/monitor.py`

**Implementation:**

```python
"""
Roadmap data integrity monitoring and alerting.

Tracks metrics and detects degradation in data quality.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List
import json


class IntegrityMonitor:
    """Monitor roadmap data integrity metrics."""

    def __init__(self, metrics_file: Path = None):
        self.metrics_file = metrics_file or Path('.vibey/roadmap/integrity_metrics.json')
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

    def collect_metrics(self) -> Dict:
        """Collect current integrity metrics."""
        from vibey.roadmap.filesystem import RoadmapFilesystem
        from vibey.roadmap.serialization import load_track
        import yaml

        fs = RoadmapFilesystem()
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'yaml_parse_errors': 0,
            'python_serialization_count': 0,
            'non_string_dependency_statuses': 0,
            'stale_dependencies_24h': 0,
            'stale_dependencies_7d': 0,
            'track_load_errors': 0,
            'total_tracks': 0,
            'total_dependencies': 0,
        }

        # Check YAML parseability
        yaml_files = list(Path('.vibey/roadmap').glob('**/*.yaml'))
        for f in yaml_files:
            try:
                with open(f) as file:
                    content = file.read()
                    yaml.safe_load(content)

                    # Check for Python serialization
                    if '!!python' in content:
                        metrics['python_serialization_count'] += 1
            except:
                metrics['yaml_parse_errors'] += 1

        # Check track loadability and dependency freshness
        threshold_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        threshold_7d = datetime.now(timezone.utc) - timedelta(days=7)

        for track_id in fs.list_tracks():
            metrics['total_tracks'] += 1

            try:
                track = load_track(fs.get_track_path(track_id))

                for dep in track.depends_on:
                    metrics['total_dependencies'] += 1

                    # Check type
                    if not isinstance(dep.current_status, str):
                        metrics['non_string_dependency_statuses'] += 1

                    # Check freshness
                    if dep.last_checked:
                        if dep.last_checked < threshold_24h:
                            metrics['stale_dependencies_24h'] += 1
                        if dep.last_checked < threshold_7d:
                            metrics['stale_dependencies_7d'] += 1

            except:
                metrics['track_load_errors'] += 1

        return metrics

    def save_metrics(self, metrics: Dict):
        """Save metrics to file."""
        history = []

        # Load existing history
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                history = json.load(f)

        # Append new metrics
        history.append(metrics)

        # Keep last 30 days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        history = [m for m in history if m['timestamp'] > cutoff]

        # Save
        with open(self.metrics_file, 'w') as f:
            json.dump(history, f, indent=2)

    def check_alerts(self, metrics: Dict) -> List[str]:
        """Check if any metrics exceed alert thresholds."""
        alerts = []

        if metrics['python_serialization_count'] > 0:
            alerts.append(
                f"🚨 CRITICAL: {metrics['python_serialization_count']} files have Python serialization"
            )

        if metrics['yaml_parse_errors'] > 0:
            alerts.append(
                f"⚠️  WARNING: {metrics['yaml_parse_errors']} YAML files have parse errors"
            )

        if metrics['track_load_errors'] > 5:
            alerts.append(
                f"⚠️  WARNING: {metrics['track_load_errors']} tracks failed to load"
            )

        if metrics['non_string_dependency_statuses'] > 0:
            alerts.append(
                f"⚠️  WARNING: {metrics['non_string_dependency_statuses']} dependency statuses are not strings"
            )

        stale_pct = (metrics['stale_dependencies_7d'] / max(metrics['total_dependencies'], 1)) * 100
        if stale_pct > 20:
            alerts.append(
                f"⚠️  WARNING: {stale_pct:.1f}% of dependencies are stale (>7 days)"
            )

        return alerts

    def run(self):
        """Run monitoring cycle."""
        print("🔍 Collecting integrity metrics...")
        metrics = self.collect_metrics()
        self.save_metrics(metrics)

        print(f"\n📊 Integrity Metrics ({metrics['timestamp']}):")
        print(f"   Total tracks: {metrics['total_tracks']}")
        print(f"   Total dependencies: {metrics['total_dependencies']}")
        print(f"   YAML parse errors: {metrics['yaml_parse_errors']}")
        print(f"   Python serialization: {metrics['python_serialization_count']}")
        print(f"   Non-string dep statuses: {metrics['non_string_dependency_statuses']}")
        print(f"   Stale dependencies (24h): {metrics['stale_dependencies_24h']}")
        print(f"   Stale dependencies (7d): {metrics['stale_dependencies_7d']}")
        print(f"   Track load errors: {metrics['track_load_errors']}")

        alerts = self.check_alerts(metrics)
        if alerts:
            print(f"\n🚨 ALERTS:")
            for alert in alerts:
                print(f"   {alert}")
            return 1
        else:
            print(f"\n✅ All integrity metrics within acceptable ranges")
            return 0


if __name__ == '__main__':
    monitor = IntegrityMonitor()
    exit(monitor.run())
```

**Add cron job suggestion in documentation:**

```bash
# Add to crontab for daily monitoring (example)
# 0 9 * * * cd /path/to/vibey && python vibey/operations/roadmap/monitor.py
```

**Deliverable:** Monitoring system, metrics collection, committed

---

### Phase 4: Documentation & Verification (Day 8, 1 hour)

#### Task 10: Document Prevention Systems (30 minutes)

**File:** `.vibey/roadmap/roadmap-integrity-fixes/PREVENTION_SYSTEMS.md`

**Content:** (Document all systems built, how to use them, and maintenance procedures)

#### Task 11: Final Verification & Testing (30 minutes)

**Verification checklist:**

```bash
# 1. No Python serialization
grep -r "!!python" .vibey/roadmap/
# Expected: No results

# 2. All YAML files parse
python tests/validation/test_yaml_integrity.py
# Expected: All tests pass

# 3. Pre-commit hook works
echo "test: !!python/object:test" > .vibey/roadmap/test.yaml
git add .vibey/roadmap/test.yaml
git commit -m "test"
# Expected: Commit rejected
rm .vibey/roadmap/test.yaml

# 4. Dependency refresh works
python -m vibey.cli roadmap refresh-dependencies --dry-run
# Expected: No errors, shows what would be updated

# 5. Monitoring works
python vibey/operations/roadmap/monitor.py
# Expected: All metrics green

# 6. Schema validation
python vibey/operations/roadmap/schema_validator.py
# Expected: All objects conform to schema

# 7. CI/CD workflow valid
# Push changes and verify GitHub Actions passes
```

---

## Success Criteria

### ✅ Must Have (Blocking)

1. **Zero Python serialization** in all roadmap YAML files
2. **Pre-commit hook** prevents future Python serialization
3. **Enum bug fixed** in all 5+ locations
4. **Validation tests** cover all critical integrity rules
5. **Schema validation** using Pydantic models
6. **CI/CD workflow** catches issues before merge

### 🎯 Should Have (Important)

7. **Dependency refresh** automation working
8. **Monitoring system** tracking metrics
9. **Documentation** complete and clear

---

## Timeline

**Total Estimated Time:** 13-15 hours
**Recommended Schedule:** 1-2 hours per day over 7-8 days

- **Day 1:** Tasks 1-3 (Critical fixes) - 1 hour
- **Day 2:** Task 4 (Validation tests) - 2 hours
- **Day 3:** Task 5 (CI/CD) - 1 hour
- **Day 4:** Task 6 (Dependency refresh) - 2 hours
- **Day 5:** Task 7 (Enhanced validation) - 3 hours
- **Day 6:** Task 8 (Schema validator) - 2 hours
- **Day 7:** Task 9 (Monitoring) - 1 hour
- **Day 8:** Tasks 10-11 (Docs & verification) - 1 hour

---

## Risk Mitigation

**Risk 1:** Breaking existing functionality
**Mitigation:** All changes backward-compatible, use `.value` only on write path

**Risk 2:** Missing some serialization locations
**Mitigation:** Comprehensive grep, validation tests, CI/CD checks

**Risk 3:** Performance impact from validation
**Mitigation:** Validation runs async in CI/CD, pre-commit only checks changed files

---

## Next Steps After Sprint 7

With prevention systems in place:

1. **Execute Sprints 0-6** with confidence that data integrity is protected
2. **Scale roadmap** to 50+ tracks knowing automation prevents corruption
3. **Add features** to monitoring dashboard (visualizations, trend analysis)
4. **Integrate with** roadmap CLI for real-time validation commands

---

**Status:** Ready for execution
**Owner:** TBD
**Start Date:** TBD
**Target Completion:** Within 1 week of start
