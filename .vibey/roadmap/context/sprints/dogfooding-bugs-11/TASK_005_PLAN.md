# Task Plan: edit command warns Unknown YAML file type for ULID files

## Bug ID
01KC8FV5SAHS4BNZYYXH3KGEF8

## Problem Statement
The `roadmap edit file` command emits warning 'Unknown YAML file type' for ULID-named task/sprint files. Should recognize ULID naming pattern.

## Root Cause Analysis
The file type detection logic uses filename patterns to determine if a file is a track, sprint, or task. It expects patterns like `track.yaml`, `sprint.yaml`, or `task-*.yaml` but doesn't recognize `01KC2D0JK7READW9KAK1HBX4B8.yaml`.

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap_lib/filesystem.py` - File type detection
2. `vibey/roadmap/serialization/yaml_loader.py` - May have similar detection

## Implementation Steps

1. **Find file type detection logic**
   ```bash
   grep -rn "Unknown YAML\|file.*type\|detect.*type" vibey/cli/roadmap_lib/
   grep -rn "Unknown YAML\|file.*type" vibey/roadmap/serialization/
   ```

2. **Update detection to use directory structure**
   ```python
   def detect_yaml_file_type(file_path: Path) -> str:
       """Detect YAML file type from path."""
       # Use parent directory for flat structure
       parent_dir = file_path.parent.name

       if parent_dir == "tracks":
           return "track"
       elif parent_dir == "sprints":
           return "sprint"
       elif parent_dir == "tasks":
           return "task"

       # Fallback: check filename pattern
       filename = file_path.stem
       if filename == "track":
           return "track"
       elif filename == "sprint":
           return "sprint"
       elif is_ulid(filename):
           # ULID file - need to check content or directory
           return detect_from_content(file_path)

       return "unknown"
   ```

3. **Add ULID detection helper**
   ```python
   def is_ulid(s: str) -> bool:
       """Check if string is a valid ULID."""
       return len(s) == 26 and s.isalnum()
   ```

4. **Remove warning for known types**
   - Only warn for truly unknown files
   - ULID files in correct directories should not warn

## Test Requirements
- `vibey roadmap edit file tasks/01KC....yaml` - no warning
- `vibey roadmap edit file sprints/01KC....yaml` - no warning
- `vibey roadmap edit file random.yaml` - warning is appropriate

## Related Bugs
- 01KC9JEBHTHJ4VV5PDW2N0JCV4 (Sprint 13: same issue)

## Estimated Complexity
Simple - directory-based detection
