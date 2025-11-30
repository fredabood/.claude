# File Format Evaluation: YAML vs JSON vs XML

**Task:** sqlite-backend-6-task-002
**Date:** 2025-11-30
**Status:** Complete

## Executive Summary

**Recommendation: Keep YAML for all roadmap files**

Despite JSON being 100-200x faster to parse, YAML's benefits for this use case outweigh the performance difference:
1. Human readability is critical for AI context and manual editing
2. Parse time difference (708ms vs 3ms for 945 tasks) is negligible in practice
3. Git diffs are significantly more readable with YAML
4. Existing tooling and codebase is YAML-based

---

## Benchmark Results

### File Size Comparison (Single Task)
| Format | Size | vs YAML |
|--------|------|---------|
| YAML | 1,276 bytes | baseline |
| JSON (pretty) | 1,530 bytes | +20% |
| JSON (compact) | 1,292 bytes | +1% |
| JSONL | 1,283 bytes | +0.5% |

### Parse Time (1000 iterations)
| Format | Time | vs JSON |
|--------|------|---------|
| YAML | 749.84 ms | 236x slower |
| JSON | 3.18 ms | baseline |
| JSONL | 2.97 ms | 0.9x |

### Serialize Time (1000 iterations)
| Format | Time | vs JSON |
|--------|------|---------|
| YAML | 538.25 ms | 119x slower |
| JSON | 4.51 ms | baseline |

### Full Roadmap Estimates (945 tasks)
| Metric | YAML | JSON |
|--------|------|------|
| Total size | 1.2 MB | 1.4 MB |
| Parse time | 709 ms | 3 ms |
| Serialize time | 509 ms | 4 ms |

---

## Format Analysis

### YAML (Current)
```yaml
task:
  id: sqlite-backend-6-task-001
  title: Analyze optimal directory structure
  description: |
    Design the new .vibey directory structure.

    DELIVERABLES:
    - Comparison matrix
    - Recommendation
  status: completed
  blocked: false
  deliverables:
    - type: code
      paths:
        - Directory structure comparison matrix
```

**Pros:**
- ✅ Human readable - natural language-like syntax
- ✅ AI-friendly - excellent for LLM context windows
- ✅ Comments supported - inline documentation
- ✅ Multiline strings - clean description blocks
- ✅ Anchors/aliases - deduplication possible
- ✅ Smaller file size than pretty JSON

**Cons:**
- ❌ 100-200x slower parsing than JSON
- ❌ Indentation-sensitive (error-prone)
- ❌ Multiple parser implementations vary
- ❌ No native schema validation

**Mitigations for YAML Cons:**

| Con | Mitigation | Implementation |
|-----|------------|----------------|
| **Slow parsing** | SQLite is hot path; YAML only on dump/init | Already designed this way |
| **Indentation errors** | Pydantic validation on load | Catches malformed YAML immediately |
| **Parser variations** | Use `ruamel.yaml` exclusively | Consistent round-trip behavior |
| **No native schema** | Pydantic models as schema | Full validation on deserialize |

**Additional Design Considerations:**

1. **Strict mode parsing** - Use `ruamel.yaml` with `typ='safe'` to reject dangerous YAML constructs
2. **Schema-first loading** - Always deserialize into Pydantic models; never use raw dicts
3. **Validation errors** - Surface clear error messages with line numbers when YAML is malformed
4. **IDE support** - Generate JSON Schema from Pydantic models for editor autocompletion

### JSON (Alternative)
```json
{
  "task": {
    "id": "sqlite-backend-6-task-001",
    "title": "Analyze optimal directory structure",
    "description": "Design the new .vibey directory structure.\n\nDELIVERABLES:\n- Comparison matrix\n- Recommendation",
    "status": "completed",
    "blocked": false,
    "deliverables": [
      {
        "type": "code",
        "paths": ["Directory structure comparison matrix"]
      }
    ]
  }
}
```

**Pros:**
- ✅ 100-200x faster parsing
- ✅ Pandas/Spark native support
- ✅ Strict schema (JSON Schema)
- ✅ Universal tooling (jq, etc.)
- ✅ SQLite JSON functions

**Cons:**
- ❌ Less human readable
- ❌ No comments
- ❌ No multiline strings (escaped \n)
- ❌ 20% larger (pretty) or harder to read (compact)
- ❌ Verbose for nested structures

### JSONL (JSON Lines)
```
{"id":"sqlite-backend-6-task-001","title":"Analyze optimal directory structure",...}
{"id":"sqlite-backend-6-task-002","title":"Evaluate file formats",...}
```

**Pros:**
- ✅ Streaming-friendly
- ✅ One record per line (easy append)
- ✅ Pandas `read_json(lines=True)`

**Cons:**
- ❌ Not human readable at all
- ❌ Poor git diffs (entire line changes)
- ❌ No structure visibility
- ❌ Loses the "file per entity" benefit

### XML (Not Recommended)
```xml
<task>
  <id>sqlite-backend-6-task-001</id>
  <title>Analyze optimal directory structure</title>
  <description>Design the new .vibey directory structure.</description>
</task>
```

**Pros:**
- ✅ Schema validation (XSD)
- ✅ XSLT transformations

**Cons:**
- ❌ Very verbose (2-3x size)
- ❌ Poor AI readability
- ❌ Heavy parsing overhead
- ❌ Outdated ecosystem
- ❌ No modern tooling support

---

## Evaluation Criteria Matrix

| Criterion | Weight | YAML | JSON | JSONL | XML |
|-----------|--------|------|------|-------|-----|
| **AI Readability** | 5 | 5 | 3 | 1 | 2 |
| **Human Editability** | 5 | 5 | 3 | 1 | 2 |
| **Parse Speed** | 2 | 1 | 5 | 5 | 2 |
| **Git Diff Quality** | 4 | 5 | 4 | 1 | 3 |
| **Schema Validation** | 2 | 2 | 4 | 4 | 5 |
| **File Size** | 1 | 4 | 3 | 4 | 1 |
| **Tooling Ecosystem** | 3 | 4 | 5 | 4 | 2 |
| **Multiline Support** | 3 | 5 | 1 | 1 | 3 |
| **Comment Support** | 2 | 5 | 1 | 1 | 3 |
| **Weighted Total** | | **113** | **89** | **57** | **65** |

---

## Git Diff Comparison

### YAML Diff (Readable)
```diff
 task:
   id: sqlite-backend-6-task-001
-  status: in_progress
+  status: completed
   blocked: false
+  completed: '2025-11-30T20:12:46+00:00'
```

### JSON Diff (Noisier)
```diff
 {
   "task": {
     "id": "sqlite-backend-6-task-001",
-    "status": "in_progress",
+    "status": "completed",
     "blocked": false,
+    "completed": "2025-11-30T20:12:46+00:00",
     ...
```

### JSONL Diff (Unusable)
```diff
-{"id":"sqlite-backend-6-task-001","status":"in_progress","blocked":false,...}
+{"id":"sqlite-backend-6-task-001","status":"completed","blocked":false,"completed":"2025-11-30T20:12:46+00:00",...}
```

---

## Performance Context

### When Does Parse Speed Matter?

| Operation | YAML (945 tasks) | JSON (945 tasks) | Impact |
|-----------|------------------|------------------|--------|
| `db init` (full load) | 709 ms | 3 ms | One-time on clone |
| `db rebuild` | 709 ms | 3 ms | Rare operation |
| Single task read | 0.75 ms | 0.003 ms | Negligible |
| Single task write | 0.54 ms | 0.005 ms | Negligible |

**Conclusion:** The 200x performance difference is irrelevant because:
1. Full roadmap operations happen rarely (clone, rebuild)
2. 709ms is still fast for a one-time operation
3. Single-file operations are sub-millisecond either way
4. SQLite is the hot path, not YAML files

---

## Recommendation

### Keep YAML

**Rationale:**
1. **AI Context** - YAML is significantly more readable in LLM prompts
2. **Human Editing** - Developers can manually edit task files
3. **Git Diffs** - YAML diffs are cleaner and more reviewable
4. **Comments** - Inline documentation is valuable
5. **Multiline** - Description fields are much cleaner
6. **Existing Code** - All serialization code uses YAML
7. **Performance OK** - 700ms for full load is acceptable

### Hybrid Approach: YAML + JSONL

**Adopted for activity_log:**
- **YAML** for tickets, artifacts, context (human-editable, AI-readable)
- **JSONL** for activity_log (append-only, not human-edited)

| Entity | Format | Rationale |
|--------|--------|-----------|
| Tickets | YAML | Human-editable, multiline descriptions |
| Artifacts | YAML | Human-editable, provenance tracking |
| Activity Log | **JSONL** | Append-friendly, fast parse, 10K+ entries |
| Context | Markdown | Human/AI documentation |

**Why JSONL for Activity Log:**
- **Append-friendly** - New entries added to end of file
- **Fast parse** - JSON is 200x faster than YAML
- **Git-friendly** - Each line is independent, clean diffs
- **Time-bucketed** - Monthly files (`activity_log/YYYY-MM.jsonl`)
- **Not human-edited** - Machine-generated, no need for YAML readability
- **Rebuildable** - SQLite can be rebuilt from JSONL files

### Migration Path

**For tickets/artifacts:** No migration needed - continue with YAML format.

**For activity_log:** Convert from YAML to JSONL:
1. Create `activity_log/` directory
2. Convert existing `audit_trail/*.yaml` to time-bucketed JSONL
3. Update loaders/dumpers to use JSONL for activity_log
4. Remove old `audit_trail/` directory

---

## Sample Files

### Current YAML (Recommended - No Change)
```yaml
task:
  id: sqlite-backend-6-task-001
  sprint_id: sqlite-backend-6
  track_id: sqlite-backend
  roadmap_id: vibey-framework-v2
  task_type: development
  title: Analyze optimal directory structure mirroring SQLite schema
  description: |
    Design the new .vibey directory structure that mirrors SQLite database 1:1.
    This analysis informs the unified ticket architecture design.

    DELIVERABLES:
    - Comparison matrix of options
    - Recommendation with rationale
  status: completed
  blocked: false
  created: '2025-11-30T20:00:00+00:00'
  # ... rest of fields
```

---

## Next Steps

1. ✅ Task 001 complete - Directory structure analysis
2. ✅ Task 002 complete - File format evaluation (this document)
3. → Task 003 - Context file consolidation (uses YAML, new directory structure)
4. → Continue with core model implementation (Tasks 004-018)
