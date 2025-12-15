# Task Plan: roadmap edit file --set appends field instead of updating existing

## Bug ID
01KC9J8R2FVP68GPFWCBJ5MN1X

## Problem Statement
When using `vibey roadmap edit file <file> --set status=in_progress`, the command appends 'status: in_progress' at the end of the file instead of modifying the existing status field. This creates an invalid YAML structure with duplicate keys.

## Root Cause Analysis
The edit command's `--set` implementation naively appends to the file instead of properly parsing YAML, updating the field, and re-serializing.

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap-update.py` or relevant edit command file
2. `vibey/operations/roadmap/safe_yaml_editor.py` - YAML editing utilities

## Implementation Steps

1. **Find edit --set implementation**
   ```bash
   grep -rn "\-\-set\|edit.*file" vibey/cli/
   ```

2. **Fix to use proper YAML parsing**
   ```python
   def edit_yaml_field(file_path: Path, field: str, value: str):
       """Edit a field in a YAML file properly."""
       import ruamel.yaml

       yaml = ruamel.yaml.YAML()
       yaml.preserve_quotes = True

       with open(file_path) as f:
           data = yaml.load(f)

       # Navigate to nested field if needed (e.g., "progress.tasks_total")
       keys = field.split('.')
       target = data
       for key in keys[:-1]:
           target = target[key]

       # Update the value
       target[keys[-1]] = value

       with open(file_path, 'w') as f:
           yaml.dump(data, f)
   ```

3. **Handle nested fields**
   - Support dot notation: `progress.tasks_total`
   - Support array indexing if needed: `tasks[0].status`

4. **Preserve YAML formatting**
   - Use ruamel.yaml to preserve comments and formatting
   - Don't re-order fields

5. **Add validation**
   - Verify field exists before updating
   - Validate value against schema if applicable

## Test Requirements
- `--set status=in_progress` on task - updates existing field
- `--set progress.tasks_total=5` - handles nested fields
- File should have same structure after edit (no duplicate keys)

## Estimated Complexity
Medium - requires proper YAML round-trip editing
