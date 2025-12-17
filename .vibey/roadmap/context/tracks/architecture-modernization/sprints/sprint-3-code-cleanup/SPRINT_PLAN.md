# Sprint 3: Code Cleanup

## Overview
- **Track:** Architecture Modernization
- **Sprint ID:** 01KCMTXK2X59MAT3YPMXP8E8BE
- **Tasks:** 12
- **Focus:** Remove obsolete code, consolidate utilities, standardize patterns

## Success Criteria
- [ ] All identified obsolete code removed
- [ ] Duplicate utilities consolidated
- [ ] Error handling standardized
- [ ] commands.py split into modules
- [ ] Zero ruff F401 (unused imports) violations

---

## Task 1: Remove Hierarchical Directory Support
**ID:** `01KCMGZEZD25B4133WNYTKYBEC`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Old hierarchical directory structure code exists despite migration to flat ULID structure (ADR-0002).

### Implementation Steps
1. Search for hierarchical path handling:
   ```bash
   grep -rn "tracks/.*sprints/\|sprints/.*tasks/" vibey/
   grep -rn "os.path.join.*track.*sprint" vibey/
   ```

2. Identify code paths:
   ```python
   # OLD (hierarchical) - REMOVE
   path = f".vibey/roadmap/tracks/{track_id}/sprints/{sprint_id}/tasks/{task_id}.yaml"

   # NEW (flat) - KEEP
   path = f".vibey/roadmap/tasks/{task_id}.yaml"
   ```

3. Files likely affected:
   - `vibey/roadmap/serialization/yaml_loader.py`
   - `vibey/operations/roadmap/update.py`
   - `vibey/cli/roadmap_lib/filesystem.py`

4. Verify no production data uses old structure:
   ```bash
   find .vibey/roadmap/tracks -type d -name "sprints"
   ```

5. Remove identified code paths

### Acceptance Criteria
- [ ] No hierarchical path code remains
- [ ] All tests pass
- [ ] Database rebuilds correctly

---

## Task 2: Remove Slug-Based ID Handling
**ID:** `01KCMGZJW2W0G77EAQMBQXCM6X`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Legacy slug-based ID code exists despite ULID being standard (ADR-0001).

### Implementation Steps
1. Search for slug handling:
   ```bash
   grep -rn "slug\|_to_ulid\|slugify" vibey/
   grep -rn "is_slug\|convert_slug" vibey/
   ```

2. Identify slug patterns:
   ```python
   # OLD (slug) - REMOVE
   id = "my-track-name"
   id = slugify(track.name)

   # NEW (ULID) - KEEP
   id = "01KC2D0JK9JKQXGQW6MQEB0JZP"
   id = ulid.new()
   ```

3. Files likely affected:
   - `vibey/roadmap/models/*.py`
   - `vibey/cli/commands.py` (ID validation)
   - `vibey/operations/roadmap/*.py`

4. Remove:
   - Slug validation functions
   - Slug-to-ULID conversion
   - Slug generation utilities

### Acceptance Criteria
- [ ] No slug handling code remains
- [ ] All IDs are ULID format
- [ ] Tests updated

---

## Task 3: Remove Old Activity Log Format Handlers
**ID:** `01KCMGZPR3R643SBJ8QT2KHXTZ`
**Priority:** Medium | **Complexity:** Simple | **Type:** Development

### Problem
Legacy activity log format handlers exist after migration to JSONL format.

### Implementation Steps
1. Identify legacy handlers:
   ```bash
   grep -rn "activity.*yaml\|yaml.*activity" vibey/
   grep -rn "ActivityLogV1\|legacy.*log" vibey/
   ```

2. Files to review:
   - `vibey/operations/roadmap/activity_log.py`
   - `vibey/operations/roadmap/jsonl_activity_log.py`
   - `vibey/operations/roadmap/migrate_activity_log.py`

3. Remove:
   - Old YAML-based log readers
   - Migration utilities (if migration complete)
   - Legacy format parsers

4. Verify current format works:
   ```python
   from vibey.operations.roadmap.jsonl_activity_log import ActivityLog
   log = ActivityLog(".vibey/roadmap/activity_log/")
   entries = log.read_all()
   ```

### Acceptance Criteria
- [ ] Legacy handlers removed
- [ ] JSONL format is only format
- [ ] All activity operations work

---

## Task 4: Remove Identified Obsolete Functions
**ID:** `01KCMJZGVQ717A80GXSSHSSQAP`
**Priority:** Medium | **Complexity:** Simple | **Type:** Development

### Problem
Three specific obsolete functions identified in OBSOLETE_CODE_REPORT.yaml.

### Functions to Remove
1. `format_legacy_output` in `roadmap_lib/legacy_helpers.py`
2. `migrate_v1_to_v2` in `migration.py`
3. `_legacy_init` in `adapters/base.py`

### Implementation Steps
1. Verify no callers:
   ```bash
   grep -rn "format_legacy_output" vibey/ tests/
   grep -rn "migrate_v1_to_v2" vibey/ tests/
   grep -rn "_legacy_init" vibey/ tests/
   ```

2. For each function:
   - Confirm zero callers
   - Remove function definition
   - Remove any imports
   - Update any __all__ exports

3. If callers exist:
   - Assess if caller is also obsolete
   - Update caller to use new function
   - Then remove obsolete function

### Acceptance Criteria
- [ ] All 3 functions removed
- [ ] No import errors
- [ ] Tests pass

---

## Task 5: Remove Unused Imports
**ID:** `01KCMGQS9RH1RYVHFVX49HN187`
**Priority:** Low | **Complexity:** Simple | **Type:** Infrastructure

### Problem
Unused imports clutter codebase and violate ruff F401.

### Implementation Steps
1. Run ruff to find violations:
   ```bash
   ruff check vibey/ --select F401
   ```

2. Auto-fix where possible:
   ```bash
   ruff check vibey/ --select F401 --fix
   ```

3. Review remaining violations:
   - Some may be intentional re-exports
   - Some may be used dynamically
   - Add noqa comments if intentional

4. Verify no import errors:
   ```bash
   python -c "import vibey"
   pytest tests/ -x
   ```

### Acceptance Criteria
- [ ] Zero F401 violations
- [ ] All imports intentional
- [ ] No runtime import errors

---

## Task 6: Consolidate ID Validation Functions
**ID:** `01KCMGQHRKP26WEJK45T3HC6HW`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
ID validation logic duplicated across CLI validators, model validators, and serialization.

### Implementation Steps
1. Find all validation locations:
   ```bash
   grep -rn "validate.*id\|is_valid.*id\|ulid.*valid" vibey/
   ```

2. Audit current implementations:
   ```python
   # CLI validation
   def validate_task_id(ctx, param, value):
       if not is_valid_ulid(value):
           raise click.BadParameter(...)

   # Model validation
   @field_validator('id')
   def validate_id(cls, v):
       if not ulid.is_valid(v):
           raise ValueError(...)

   # Serialization
   def load_by_id(id: str):
       if len(id) != 26:
           raise InvalidIdError(...)
   ```

3. Create unified module:
   ```python
   # vibey/common/id_validation.py

   import ulid

   class InvalidIdError(ValueError):
       """Raised when an ID is invalid."""
       pass

   def validate_ulid(value: str, context: str = "ID") -> str:
       """
       Validate a ULID string.

       Args:
           value: The ID to validate
           context: Context for error messages

       Returns:
           The validated ID

       Raises:
           InvalidIdError: If ID is invalid
       """
       if not value or len(value) != 26:
           raise InvalidIdError(f"{context} must be 26 characters")
       try:
           ulid.parse(value)
       except ValueError as e:
           raise InvalidIdError(f"Invalid {context}: {e}")
       return value

   def is_valid_ulid(value: str) -> bool:
       """Check if value is a valid ULID."""
       try:
           validate_ulid(value)
           return True
       except InvalidIdError:
           return False
   ```

4. Update all callers to use unified module

### Acceptance Criteria
- [ ] Single source of truth for ID validation
- [ ] All validators use common module
- [ ] Consistent error messages

---

## Task 7: Consolidate Path Construction Utilities
**ID:** `01KCMGQNGYAX09Z1NTNDC0Q5ZN`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Path building logic repeated across codebase.

### Implementation Steps
1. Find path construction:
   ```bash
   grep -rn ".vibey/roadmap" vibey/
   grep -rn "os.path.join.*roadmap\|Path.*roadmap" vibey/
   ```

2. Audit current patterns:
   ```python
   # Pattern 1
   path = f".vibey/roadmap/tasks/{task_id}.yaml"

   # Pattern 2
   path = os.path.join(roadmap_dir, "tasks", f"{task_id}.yaml")

   # Pattern 3
   path = Path(".vibey") / "roadmap" / "tasks" / f"{task_id}.yaml"
   ```

3. Create unified module:
   ```python
   # vibey/common/paths.py

   from pathlib import Path
   from typing import Optional

   class RoadmapPaths:
       """Centralized path construction for roadmap files."""

       def __init__(self, base: Path = Path(".vibey/roadmap")):
           self.base = base

       def track(self, track_id: str) -> Path:
           return self.base / "tracks" / f"{track_id}.yaml"

       def sprint(self, sprint_id: str) -> Path:
           return self.base / "sprints" / f"{sprint_id}.yaml"

       def task(self, task_id: str) -> Path:
           return self.base / "tasks" / f"{task_id}.yaml"

       def context_dir(self, entity_type: str, slug: str) -> Path:
           return self.base / "context" / entity_type / slug

       def database(self) -> Path:
           return self.base / "roadmap.db"

   # Default instance
   paths = RoadmapPaths()
   ```

4. Update all callers

### Acceptance Criteria
- [ ] Single source for path construction
- [ ] All paths go through utility
- [ ] Easy to change path structure

---

## Task 8: Fix Activity Log Integration Gaps
**ID:** `01KCMGQDYCTFCBTK3ZQE7AHZ59`
**Priority:** Medium | **Complexity:** Simple | **Type:** Development

### Problem
create-sprint and create-task commands don't log operations.

### Implementation Steps
1. Find commands missing logging:
   ```bash
   grep -rn "create_sprint\|create_task" vibey/cli/
   # Then check if ActivityLog is used
   ```

2. Audit logging in similar commands:
   ```python
   # Example of command WITH logging
   def roadmap_update(...):
       # ... do operation
       activity_log.log_update(entity_id, changes)
   ```

3. Add logging to missing commands:
   ```python
   # vibey/cli/commands.py

   @cli.command()
   def create_sprint(...):
       # Create sprint
       sprint = create_sprint_operation(...)

       # ADD: Log the operation
       activity_log.log_create(
           entity_type="sprint",
           entity_id=sprint.id,
           details={"name": sprint.name, "track_id": track_id}
       )

       click.echo(f"Created sprint {sprint.id}")
   ```

4. Verify logging works:
   ```bash
   vibey roadmap create-sprint --track <id> --name "Test"
   cat .vibey/roadmap/activity_log/*.jsonl | tail -1
   ```

### Acceptance Criteria
- [ ] create-sprint logs operations
- [ ] create-task logs operations
- [ ] Consistent log format

---

## Task 9: Implement Backup File Cleanup Policy
**ID:** `01KCMJSBWRE0MA9JFJYX9GHK3A`
**Priority:** Low | **Complexity:** Simple | **Type:** Development

### Problem
`.vibey/safe-edit-backups/` accumulates without cleanup.

### Implementation Steps
1. Assess current state:
   ```bash
   ls -la .vibey/safe-edit-backups/ | wc -l
   du -sh .vibey/safe-edit-backups/
   ```

2. Design cleanup policy:
   ```python
   # Options:
   # - Age-based: Delete files older than N days
   # - Size-based: Keep directory under N MB
   # - Count-based: Keep last N backups per file

   BACKUP_RETENTION_DAYS = 7
   MAX_BACKUP_SIZE_MB = 100
   ```

3. Implement cleanup:
   ```python
   # vibey/operations/roadmap/backup_cleanup.py

   from pathlib import Path
   from datetime import datetime, timedelta

   def cleanup_old_backups(
       backup_dir: Path,
       max_age_days: int = 7
   ) -> int:
       """Remove backups older than max_age_days."""
       cutoff = datetime.now() - timedelta(days=max_age_days)
       removed = 0

       for backup_file in backup_dir.glob("*.yaml.bak"):
           if backup_file.stat().st_mtime < cutoff.timestamp():
               backup_file.unlink()
               removed += 1

       return removed
   ```

4. Add to CLI:
   ```python
   @cli.command()
   @click.option('--days', default=7)
   def cleanup_backups(days):
       """Remove old backup files."""
       removed = cleanup_old_backups(BACKUP_DIR, days)
       click.echo(f"Removed {removed} old backups")
   ```

### Acceptance Criteria
- [ ] Cleanup policy implemented
- [ ] CLI command available
- [ ] Backups don't grow unbounded

---

## Task 10: Standardize Error Handling in CLI Commands
**ID:** `01KCMGQA6GJHX1QM5JRWZP17NE`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Inconsistent error handling: some commands silently fail, some raise, some log.

### Implementation Steps
1. Audit error handling patterns:
   ```bash
   grep -rn "except\|raise\|click.echo.*error\|sys.exit" vibey/cli/
   ```

2. Define standard pattern:
   ```python
   # Standard error handling pattern

   from vibey.common.errors import VibeyError

   @cli.command()
   def my_command():
       try:
           result = operation()
           click.echo(format_result(result))
       except VibeyError as e:
           # Known errors: show user-friendly message
           click.echo(f"Error: {e.message}", err=True)
           raise SystemExit(1)
       except Exception as e:
           # Unknown errors: show with context
           click.echo(f"Unexpected error: {e}", err=True)
           if ctx.obj.get('debug'):
               raise
           raise SystemExit(2)
   ```

3. Create error decorator:
   ```python
   # vibey/cli/error_handling.py

   def handle_errors(f):
       @functools.wraps(f)
       def wrapper(*args, **kwargs):
           try:
               return f(*args, **kwargs)
           except VibeyError as e:
               click.echo(f"Error: {e.message}", err=True)
               raise SystemExit(1)
       return wrapper
   ```

4. Apply to all commands

### Acceptance Criteria
- [ ] Consistent error handling
- [ ] User-friendly error messages
- [ ] Appropriate exit codes

---

## Task 11: Split commands.py into Logical Modules
**ID:** `01KCMGZB4G0322MRJZ8VX3KYM8`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
commands.py is 3000+ lines, difficult to navigate and maintain.

### Implementation Steps
1. Analyze current structure:
   ```bash
   wc -l vibey/cli/commands.py
   grep -n "^@cli\|^def " vibey/cli/commands.py
   ```

2. Design module split:
   ```
   vibey/cli/
   ├── main.py              # Entry point, CLI group
   ├── commands/
   │   ├── __init__.py      # Register all command groups
   │   ├── roadmap.py       # roadmap command group
   │   ├── docs.py          # docs command group
   │   ├── deploy.py        # deploy command group
   │   ├── discover.py      # discover command group
   │   └── mcp.py           # mcp command group
   └── roadmap_lib/         # Existing helpers
   ```

3. Create module structure:
   ```python
   # vibey/cli/commands/roadmap.py

   import click
   from vibey.cli.main import cli

   @cli.group()
   def roadmap():
       """Roadmap management commands."""
       pass

   @roadmap.command()
   def status():
       """Show roadmap status."""
       ...
   ```

4. Update imports:
   ```python
   # vibey/cli/commands/__init__.py

   from vibey.cli.commands.roadmap import roadmap
   from vibey.cli.commands.docs import docs
   from vibey.cli.commands.deploy import deploy

   __all__ = ['roadmap', 'docs', 'deploy']
   ```

5. Migrate commands group by group:
   - Start with smallest group
   - Verify tests pass after each
   - Update any absolute imports

### Acceptance Criteria
- [ ] commands.py split into modules
- [ ] Each module < 500 lines
- [ ] All commands still work
- [ ] Tests pass

---

## Task 12: Standardize Error Handling in CLI Commands
**ID:** `01KCMGQA6GJHX1QM5JRWZP17NE`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

(Note: This is a duplicate of Task 10 in the database - likely a data issue)

---

## Sprint Completion Checklist
- [ ] Hierarchical directory code removed
- [ ] Slug-based ID code removed
- [ ] Legacy activity log handlers removed
- [ ] 3 obsolete functions removed
- [ ] Unused imports cleaned
- [ ] ID validation consolidated
- [ ] Path utilities consolidated
- [ ] Activity log gaps fixed
- [ ] Backup cleanup implemented
- [ ] Error handling standardized
- [ ] commands.py split
