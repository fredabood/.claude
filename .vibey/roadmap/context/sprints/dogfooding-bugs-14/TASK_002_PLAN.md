# Task Plan: CLI roadmap show command doesn't find tracks by name

## Bug ID
01KCC8YGKPXGCVBZX29Y2M53KF

## Problem Statement
`vibey roadmap show "CLI Dogfooding Bug Fixes"` returns 'Track not found' but `vibey roadmap show 01KC39XSXJ39N12HWJ93F77KQ9` works. The show command should support both name and ID lookup.

## Root Cause Analysis
The show command only accepts IDs, not names. The lookup logic doesn't search by name field.

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap_commands/show.py` - Show command implementation
2. `vibey/operations/roadmap/query.py` - Query functions

## Implementation Steps

1. **Find show command implementation**
   ```bash
   grep -n "def show\|roadmap show" vibey/cli/roadmap_commands/show.py
   ```

2. **Add name-based lookup**
   ```python
   def find_item_by_name_or_id(root_dir: Path, identifier: str) -> tuple[str, str]:
       """Find item by name or ID.

       Returns:
           Tuple of (item_type, item_id)
       """
       fs = FileSystemManager(root_dir)

       # First, try as direct ID (ULID or slug)
       for item_type, directory in [
           ("track", "tracks"),
           ("sprint", "sprints"),
           ("task", "tasks")
       ]:
           path = fs.roadmap_root / directory / f"{identifier}.yaml"
           if path.exists():
               return (item_type, identifier)

       # If not found, search by name
       # Search tracks
       for track_file in (fs.roadmap_root / "tracks").glob("*.yaml"):
           track = load_track(track_file)
           if track.name == identifier or track.name.lower() == identifier.lower():
               return ("track", track.id)

       # Search sprints
       for sprint_file in (fs.roadmap_root / "sprints").glob("*.yaml"):
           sprint = load_sprint(sprint_file)
           if sprint.name == identifier or sprint.name.lower() == identifier.lower():
               return ("sprint", sprint.id)

       # Search tasks by title
       for task_file in (fs.roadmap_root / "tasks").glob("*.yaml"):
           task = load_task(task_file)
           if task.title == identifier or task.title.lower() == identifier.lower():
               return ("task", task.id)

       raise ValueError(f"Item not found: {identifier}")
   ```

3. **Update show command to use lookup**
   ```python
   def handle_show(args):
       try:
           item_type, item_id = find_item_by_name_or_id(root_dir, args.identifier)
       except ValueError as e:
           click.echo(f"Error: {e}")
           return 1
   ```

4. **Add fuzzy matching option**
   - For partial matches, show suggestions
   - "Did you mean: ..."

## Test Requirements
- `vibey roadmap show "CLI Dogfooding Bug Fixes"` - should find track
- `vibey roadmap show 01KC39XSXJ39N12HWJ93F77KQ9` - still works
- Case-insensitive matching should work
- Non-existent name should show helpful error

## Estimated Complexity
Medium - requires iteration over all items for name search
