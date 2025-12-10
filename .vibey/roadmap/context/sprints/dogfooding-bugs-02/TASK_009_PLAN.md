# Task 009: Debug Track Discovery in FileSystemManager.list_tracks()

**Task ID:** dogfooding-bugs-02-task-009
**Bug Addressed:** #2 (Tracks not showing in status)
**Complexity:** Low
**Type:** Research/Debug

---

## Problem Statement

The `FileSystemManager.list_tracks()` method may not be correctly discovering all tracks from the flat ULID structure, causing some tracks (like unified-architecture-migration) to be missing from `roadmap status`.

---

## Current Implementation

```python
# filesystem.py:330-350
def list_tracks(self) -> list[str]:
    """List all track IDs (supports both flat and nested structures)."""
    if self.structure_format == "flat":
        tracks_dir = self.roadmap_root / "tracks"
        if not tracks_dir.exists():
            return []

        # Return all .yaml files (excluding .id file)
        track_files = tracks_dir.glob("*.yaml")
        return [f.stem for f in track_files]  # stem removes .yaml extension
    else:
        # Nested structure: list track directories
        ...
```

---

## Investigation Steps

### 1. Verify Structure Detection

```python
def debug_structure_detection():
    fs = FileSystemManager(Path.cwd())
    print(f"Structure format: {fs.structure_format}")
    print(f"Roadmap root: {fs.roadmap_root}")
    print(f"Tracks dir exists: {(fs.roadmap_root / 'tracks').exists()}")
```

### 2. Check Track Files

```bash
# List all track files
ls -la .vibey/roadmap/tracks/*.yaml | wc -l

# Check for the missing track
ls .vibey/roadmap/tracks/ | grep -i unified
```

### 3. Verify list_tracks Output

```python
def debug_list_tracks():
    fs = FileSystemManager(Path.cwd())
    tracks = fs.list_tracks()
    print(f"Found {len(tracks)} tracks")

    # Check for specific track
    unified_track = "01KC2D0JKTE7Z4HCNHST8ZVW4R"
    if unified_track in tracks:
        print(f"✓ Found unified-architecture-migration track")
    else:
        print(f"✗ Missing unified-architecture-migration track")
        print(f"Looking in: {fs.roadmap_root / 'tracks'}")
```

---

## Potential Issues

### Issue 1: Structure Detection Wrong

If `structure_format` is "nested" instead of "flat", the wrong listing logic is used.

**Fix:**
```python
def _detect_structure_format(self) -> Literal["flat", "nested"]:
    # More robust detection
    tracks_dir = self.roadmap_root / "tracks"
    if tracks_dir.exists() and any(tracks_dir.glob("*.yaml")):
        return "flat"
    return "nested"
```

### Issue 2: File Permissions

Track files may have wrong permissions, causing `glob()` to skip them.

**Check:**
```bash
ls -la .vibey/roadmap/tracks/*.yaml | head -5
```

### Issue 3: Symlink Issues

If tracks are symlinks, `glob()` may not follow them.

**Fix:**
```python
track_files = list(tracks_dir.glob("*.yaml"))
# Also check for symlinks
track_files.extend(f for f in tracks_dir.iterdir()
                   if f.is_symlink() and f.suffix == '.yaml')
```

---

## Debug Script

```python
#!/usr/bin/env python3
"""Debug script for track discovery issues."""

from pathlib import Path
from vibey.cli.roadmap_lib.filesystem import FileSystemManager

def main():
    root = Path.cwd()
    fs = FileSystemManager(root)

    print("=== FileSystemManager Debug ===")
    print(f"Root dir: {fs.root_dir}")
    print(f"Vibey dir: {fs.vibey_dir}")
    print(f"Roadmap root: {fs.roadmap_root}")
    print(f"Structure format: {fs.structure_format}")

    print("\n=== Tracks Directory ===")
    tracks_dir = fs.roadmap_root / "tracks"
    print(f"Tracks dir: {tracks_dir}")
    print(f"Exists: {tracks_dir.exists()}")

    if tracks_dir.exists():
        files = list(tracks_dir.glob("*.yaml"))
        print(f"YAML files found: {len(files)}")

        # List first 5
        for f in files[:5]:
            print(f"  - {f.name}")

    print("\n=== list_tracks() Output ===")
    tracks = fs.list_tracks()
    print(f"Total tracks: {len(tracks)}")

    # Check for unified-architecture-migration
    # First find its ULID
    for f in tracks_dir.glob("*.yaml"):
        if "unified" in f.read_text().lower():
            print(f"\nFound unified track file: {f.name}")
            if f.stem in tracks:
                print("  ✓ Included in list_tracks()")
            else:
                print("  ✗ NOT included in list_tracks()")

if __name__ == "__main__":
    main()
```

---

## Files to Check

| File | What to Check |
|------|---------------|
| `vibey/cli/roadmap_lib/filesystem.py` | `_detect_structure_format()` |
| `vibey/cli/roadmap_lib/filesystem.py` | `list_tracks()` |
| `.vibey/roadmap/tracks/` | All track files present? |

---

## Success Criteria

- [ ] Root cause of missing tracks identified
- [ ] Debug script created and run
- [ ] Issue documented with fix recommendation
- [ ] All 39 tracks discoverable

---

## Dependencies

None - this is a debugging/research task.

---

## Notes

This task is primarily investigation. The actual fix will be implemented in Task 010.

Output should include:
1. Debug script output
2. Root cause analysis
3. Recommended fix
