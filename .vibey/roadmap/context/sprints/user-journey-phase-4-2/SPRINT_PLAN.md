# Sprint 4.2: Discovery Output Architecture

## Sprint Overview

**Goal:** Design and implement structured discovery outputs that integrate with the context versioning system.

**Theme:** Discovery Enhancement & Context Integration

**Estimated Duration:** 4-5 sessions

**Prerequisites:** Phase 3.5 (Documentation Sync) completed

---

## Background

The `vibey discover` command analyzes a project and generates context about its structure, patterns, and conventions. Currently, discovery outputs may be unstructured or not well-integrated with the context management system.

This sprint enhances discovery to:
1. Produce structured, versioned outputs
2. Integrate with the context system from Phase 3
3. Enable discovery refresh and change tracking
4. Support automatic context seeding

---

## Tasks

### Task 1: Audit current discovery mode

**Objective:** Document current discovery mode functionality: what it discovers, output format, storage location, usage patterns. Identify gaps.

**Deliverables:**
- `DISCOVERY_AUDIT.md` - Current state documentation

**Audit Areas:**
1. **Discovery Commands:**
   - What commands exist?
   - What do they discover?
   - What output do they produce?

2. **Output Format:**
   - Structured or unstructured?
   - Machine-readable?
   - Human-readable?

3. **Storage:**
   - Where are outputs stored?
   - Are they versioned?
   - How are they refreshed?

4. **Integration:**
   - How does discovery integrate with other features?
   - Is output used by AI agents?
   - Is output used by CLI commands?

**Acceptance Criteria:**
- [ ] All discovery commands documented
- [ ] Output formats documented
- [ ] Storage patterns documented
- [ ] Integration points mapped
- [ ] Gaps identified

---

### Task 2: Design discovery output schema

**Objective:** Design structured schema for discovery outputs that integrates with context versioning. Include: project structure, dependencies, patterns, recommendations.

**Deliverables:**
- `DISCOVERY_SCHEMA.yaml` - Schema definition
- `DISCOVERY_SCHEMA.md` - Schema documentation

**Schema Components:**

```yaml
discovery:
  metadata:
    version: string          # Schema version
    discovered_at: datetime  # When discovery ran
    project_root: string     # Absolute path
    git_commit: string       # Commit at discovery time

  project:
    name: string
    type: string             # web-app, cli, library, etc.
    languages: [string]
    frameworks: [string]

  structure:
    directories: [DirectoryInfo]
    key_files: [FileInfo]
    entry_points: [string]

  dependencies:
    runtime: [Dependency]
    development: [Dependency]

  patterns:
    architectural: [Pattern]
    coding: [Pattern]
    testing: [Pattern]

  conventions:
    naming: [Convention]
    organization: [Convention]

  recommendations:
    immediate: [Recommendation]
    suggested: [Recommendation]
```

**Acceptance Criteria:**
- [ ] Schema covers all discovery areas
- [ ] Schema is extensible
- [ ] Schema supports versioning
- [ ] Schema documentation complete
- [ ] Example output provided

---

### Task 3: Design discovery-to-context integration

**Objective:** Design how discovery outputs feed into context management: automatic context seeding, discovery refresh triggers, staleness detection.

**Deliverables:**
- `DISCOVERY_CONTEXT_INTEGRATION.md` - Integration design

**Integration Points:**

1. **Context Seeding:**
   - When a new project is initialized, run discovery
   - Seed context directory with discovery results
   - Generate initial CLAUDE.md from discovery

2. **Refresh Triggers:**
   - File system changes (new files, deleted files)
   - Dependency changes (package.json, requirements.txt)
   - Git events (branch switch, significant commits)

3. **Staleness Detection:**
   - Compare current state to last discovery
   - Flag when discovery is likely stale
   - Suggest refresh when needed

4. **Context Correlation:**
   - Link discovery to sessions
   - Track which discovery version was active during session
   - Enable "reproduce session" with same discovery context

**Acceptance Criteria:**
- [ ] Seeding workflow designed
- [ ] Refresh triggers defined
- [ ] Staleness detection algorithm
- [ ] Context correlation approach
- [ ] API/CLI interfaces defined

---

### Task 4: Implement structured discovery outputs

**Objective:** Update discovery mode to produce structured outputs in new schema. Ensure backward compatibility with existing workflows.

**Deliverables:**
- Updated `vibey/operations/discovery/` modules
- Updated output generation

**Implementation Approach:**
1. Create `DiscoveryOutput` dataclass matching schema
2. Update discovery analyzers to populate dataclass
3. Add YAML serialization for outputs
4. Add JSON serialization for programmatic access
5. Maintain backward-compatible text output option

**New Files:**
```
vibey/operations/discovery/
├── schema.py              # DiscoveryOutput dataclass
├── serializers.py         # YAML/JSON serialization
└── analyzers/
    ├── project.py         # Project info analyzer
    ├── structure.py       # Structure analyzer
    ├── dependencies.py    # Dependency analyzer
    ├── patterns.py        # Pattern analyzer
    └── conventions.py     # Convention analyzer
```

**Acceptance Criteria:**
- [ ] DiscoveryOutput dataclass implemented
- [ ] All analyzers produce structured output
- [ ] YAML serialization working
- [ ] JSON serialization working
- [ ] Backward compatibility maintained

---

### Task 5: Implement discovery versioning

**Objective:** Add versioning to discovery outputs so changes can be tracked over time and correlated with project evolution.

**Deliverables:**
- Versioned discovery storage
- Discovery diff capability

**Implementation Approach:**
1. Store discovery outputs with timestamps:
   ```
   .vibey/discovery/
   ├── current.yaml           # Latest discovery
   ├── history/
   │   ├── 2025-12-12T10-00-00.yaml
   │   └── 2025-12-11T15-30-00.yaml
   └── diffs/
       └── 2025-12-12T10-00-00.diff.yaml
   ```

2. Implement discovery diff:
   - Compare two discovery outputs
   - Highlight additions, removals, changes
   - Focus on significant changes (ignore noise)

3. Retention policy:
   - Keep last N discoveries
   - Keep discoveries at significant milestones
   - Configurable retention

**Acceptance Criteria:**
- [ ] Discovery history stored
- [ ] Diff capability working
- [ ] Retention policy implemented
- [ ] History queryable

---

### Task 6: Update discovery CLI commands

**Objective:** Update 'vibey discover' command family to support new output formats, versioning, and context integration.

**Deliverables:**
- Updated CLI commands

**Commands:**

```bash
# Run discovery
vibey discover [--output yaml|json|text] [--save]
# Run discovery and optionally save to history

# Show current discovery
vibey discover show [--format yaml|json|text]
# Display current discovery output

# Compare discoveries
vibey discover diff [VERSION1] [VERSION2]
# Compare two discovery versions (default: current vs previous)

# List discovery history
vibey discover history [--limit N]
# Show discovery history

# Check staleness
vibey discover status
# Show if current discovery is stale

# Refresh discovery
vibey discover refresh [--force]
# Re-run discovery if stale (or force)
```

**Acceptance Criteria:**
- [ ] All commands implemented
- [ ] Help text complete
- [ ] Output formats working
- [ ] History commands working
- [ ] Staleness detection working

---

## Task Dependencies

```
Task 1 (Audit)
    ↓
Tasks 2, 3 (Design) - can run in parallel
    ↓
Task 4 (Implement outputs)
    ↓
Task 5 (Implement versioning)
    ↓
Task 6 (CLI commands)
```

---

## Success Criteria

- [ ] Current discovery mode audited
- [ ] Structured schema designed and documented
- [ ] Context integration designed
- [ ] Structured outputs implemented
- [ ] Versioning implemented
- [ ] CLI commands updated

---

## File Changes Summary

**New Files:**
- `vibey/operations/discovery/schema.py`
- `vibey/operations/discovery/serializers.py`
- `vibey/operations/discovery/analyzers/*.py`
- `docs/reference/DISCOVERY_SCHEMA.md`

**Modified Files:**
- `vibey/cli/commands.py` (discover commands)
- `vibey/cli/main.py` (command registration)

**New Directories:**
- `.vibey/discovery/` (runtime)
- `.vibey/discovery/history/` (runtime)

---

## Notes

This sprint focuses on discovery infrastructure. The actual context integration (Phase 4.4) will build on this foundation.
