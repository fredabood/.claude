# Task 006: Document Canonical Location in CLAUDE.md

**Task ID:** dogfooding-bugs-06-task-006
**Bug Addressed:** #14 (Duplicate roadmap.yaml Files Existed at Two Locations)
**Complexity:** Low
**Type:** Documentation

---

## Problem Statement

The canonical location of `roadmap.yaml` should be clearly documented in CLAUDE.md to:

1. Prevent future confusion about file locations
2. Help developers understand the flat structure
3. Provide reference for troubleshooting

---

## Current State

CLAUDE.md mentions the `.vibey/roadmap/` directory structure but may not explicitly state the canonical location for `roadmap.yaml`.

---

## Implementation

### Add to CLAUDE.md Repository Structure Section

```markdown
## Repository Structure

```
vibey/                            # Repository root
├── .vibey/                       # Vibey framework data
│   ├── config/                   # Modular configuration
│   ├── roadmap/                  # Roadmap system (ULID flat structure)
│   │   ├── roadmap.yaml          # ⭐ CANONICAL roadmap file
│   │   ├── tracks/               # Track YAML files ({ulid}.yaml)
│   │   ├── sprints/              # Sprint YAML files ({ulid}.yaml)
│   │   ├── tasks/                # Task YAML files ({ulid}.yaml)
│   │   ├── artifacts/            # Artifact files
│   │   └── context/              # Sprint context and plans
│   └── sprint_summaries/         # Archived sprint completion docs
```

### Canonical File Locations

**Important:** The roadmap system uses a **flat ULID structure**. All roadmap data files are in specific locations:

| File | Canonical Location | Format |
|------|-------------------|--------|
| Roadmap | `.vibey/roadmap/roadmap.yaml` | Single file |
| Tracks | `.vibey/roadmap/tracks/{ulid}.yaml` | ULID-named files |
| Sprints | `.vibey/roadmap/sprints/{ulid}.yaml` | ULID-named files |
| Tasks | `.vibey/roadmap/tasks/{ulid}.yaml` | ULID-named files |

⚠️ **Deprecated Locations:**
- `.vibey/roadmap.yaml` - OLD location, should NOT exist
- Nested directories like `.vibey/roadmap/{track}/{sprint}/` - OLD hierarchical structure
```

### Add Troubleshooting Section

```markdown
## Troubleshooting

### "Roadmap not found" Error

If you see this error, check that `roadmap.yaml` exists at the correct location:

```bash
# Correct location
ls .vibey/roadmap/roadmap.yaml

# Wrong location (should NOT exist)
ls .vibey/roadmap.yaml  # This is deprecated!
```

**Fix:** If you have a file at `.vibey/roadmap.yaml`, move or delete it:
```bash
# Option 1: Delete old file (if .vibey/roadmap/roadmap.yaml exists)
rm .vibey/roadmap.yaml

# Option 2: Move to correct location (if only old file exists)
mv .vibey/roadmap.yaml .vibey/roadmap/roadmap.yaml
```

### "Duplicate roadmap.yaml" Warning

If you see a warning about duplicate files:
```
⚠️  WARNING: Duplicate roadmap.yaml files detected!
```

**Fix:** Delete the old file:
```bash
rm .vibey/roadmap.yaml
```

The canonical location is always `.vibey/roadmap/roadmap.yaml`.
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `CLAUDE.md` | Add canonical location documentation |

---

## Specific Edits

### Edit 1: Update Repository Structure

Find the "Repository Structure" section and update it to clearly show the canonical roadmap.yaml location with a star or highlight.

### Edit 2: Add Canonical Locations Table

Add a new subsection after the directory tree explaining the canonical file locations.

### Edit 3: Add Troubleshooting Section

If a troubleshooting section doesn't exist, create one. If it does, add the roadmap location troubleshooting entries.

---

## Testing Strategy

```bash
# Verify documentation is accurate

# 1. Check canonical location exists
ls -la .vibey/roadmap/roadmap.yaml

# 2. Check deprecated location does NOT exist
ls -la .vibey/roadmap.yaml  # Should fail

# 3. Verify CLAUDE.md mentions correct location
grep "roadmap/roadmap.yaml" CLAUDE.md

# 4. Verify CLAUDE.md warns about old location
grep "deprecated" CLAUDE.md
```

---

## Success Criteria

- [ ] Repository structure clearly shows `.vibey/roadmap/roadmap.yaml`
- [ ] Canonical locations table added with all file types
- [ ] Deprecated locations explicitly mentioned with ⚠️ warning
- [ ] Troubleshooting section includes "roadmap not found" fix
- [ ] Troubleshooting section includes duplicate warning fix
- [ ] Documentation matches actual file structure

---

## Dependencies

- Tasks 004-005 (implementation and verification complete)

---

## Notes

Good documentation prevents:
1. Users manually creating files at wrong locations
2. Migration scripts creating duplicates
3. Confusion about which file is authoritative
4. Time wasted debugging location issues

The CLAUDE.md file is read by AI assistants, so clear documentation here directly improves the AI's ability to help users with roadmap issues.

### Key Messages to Communicate

1. **Single Source of Truth:** `.vibey/roadmap/roadmap.yaml`
2. **ULID Structure:** Files named by ULID, not slug
3. **Flat Organization:** No nested track/sprint directories
4. **Deprecated Patterns:** Old locations should NOT be used
