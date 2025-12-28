# Sprint 4: Documentation Sync - Detailed Plan

## Sprint Overview

| Field | Value |
|-------|-------|
| Sprint ID | 01KDJKTRVZS618BM5ZZTQ3442X |
| Track | Comprehensive Repository Audit V2 |
| Status | not_started |
| Tasks | 8 |
| Estimated Tokens | ~20,000 |
| Dependencies | Sprints 1-3 (for accurate content) |

## Goal

Update all documentation to reflect current implementation. Ensure CLI reference, MCP reference, ADRs, user journeys, and walkthroughs are accurate and current.

---

## Task Details

### Task 4.1: Audit Documentation Accuracy and Drift

**Task ID:** `01KDDE9NEKAH3BM9PRFPHNNCNB`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Systematically check documentation against implementation to identify drift (outdated content).

#### Implementation Steps

1. **Inventory all documentation files**
   ```bash
   find docs -name "*.md" | wc -l
   # Expected: ~50+ files
   ```

2. **For each doc file, check:**
   - Last modified date
   - References to code that may have changed
   - Examples that may be outdated

3. **Create drift score**
   ```
   Drift Score = (days since update) * (references to changed code)
   ```

4. **Prioritize updates**

#### Deliverables
- `DOCUMENTATION_DRIFT_REPORT.md`
- Priority update list
- Stale file inventory

---

### Task 4.2: Run vibey docs check-drift and Catalog Discrepancies

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34438`
**Type:** research | **Complexity:** simple | **Priority:** medium

#### Description
Use the built-in drift detection tool to find discrepancies.

#### Implementation Steps

```bash
# Run drift check
vibey docs check-drift

# Generate detailed report
vibey docs check-drift --verbose --output drift_report.json
```

#### Deliverables
- Drift check output
- Categorized discrepancies
- Auto-fix recommendations

---

### Task 4.3: Update CLI_REFERENCE.md

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34439`
**Type:** documentation | **Complexity:** medium | **Priority:** high

#### Description
Update CLI reference with all new and changed commands. Currently 203 commands.

#### Source File
```
docs/reference/CLI_REFERENCE.md
```

#### Implementation Steps

1. **Regenerate CLI reference**
   ```bash
   vibey docs generate-cli --output docs/reference/CLI_REFERENCE.md
   ```

2. **Or manually update:**
   - List new commands added since Dec 12
   - Update changed command signatures
   - Add new examples

3. **Verify completeness**
   ```bash
   # Count commands in docs
   grep -c "^### " docs/reference/CLI_REFERENCE.md

   # Compare with actual
   vibey --help 2>&1 | grep -E "^\s+\w+" | wc -l
   ```

#### New Commands to Document
- `vibey implement` commands
- `vibey roadmap` new subcommands
- Any new `vibey git` commands

#### Deliverables
- Updated `CLI_REFERENCE.md`
- Change log of updates

---

### Task 4.4: Update MCP_REFERENCE.md

**Task ID:** `01KDJKTRVZS618BM5ZZTQ3443A`
**Type:** documentation | **Complexity:** medium | **Priority:** high

#### Description
Update MCP reference with all new tools, resources, and prompts. Currently 76 tools, 8 resources, 4 prompts.

#### Source File
```
docs/reference/MCP_REFERENCE.md
```

#### Implementation Steps

1. **Regenerate MCP reference**
   ```bash
   vibey docs generate-mcp --output docs/reference/MCP_REFERENCE.md
   ```

2. **Verify tool count**
   ```bash
   grep -c "^### " docs/reference/MCP_REFERENCE.md
   ```

3. **Document new tools:**
   - Token estimation tools
   - Implementation mode tools
   - Context tools

#### Deliverables
- Updated `MCP_REFERENCE.md`
- New tool documentation

---

### Task 4.5: Update ADRs for Recent Architectural Decisions

**Task ID:** `01KDJKTRVZS618BM5ZZTQ3443B`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Review and update Architecture Decision Records for recent decisions.

#### ADR Location
```
docs/architecture/adr/
├── 0001-ulid-identifiers.md
├── 0002-flat-directory-structure.md
├── 0003-dual-storage-sqlite-yaml.md
├── 0004-click-cli-framework.md
├── 0005-mcp-integration.md
└── ...
```

#### Implementation Steps

1. **Review existing ADRs for accuracy**
2. **Identify new decisions needing ADRs:**
   - Implementation mode architecture
   - Token estimation system
   - Context system design

3. **Create new ADRs if needed**
4. **Update superseded ADRs**

#### ADR Template
```markdown
# ADR-XXXX: [Title]

## Status
Accepted | Superseded | Deprecated

## Context
[Why this decision was needed]

## Decision
[What we decided]

## Consequences
[What are the results]
```

#### Deliverables
- Updated existing ADRs
- New ADRs for recent decisions
- ADR index update

---

### Task 4.6: Update User Journeys with New Features

**Task ID:** `01KDJKTRVZS618BM5ZZTQ3443C`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Update persona-based user journeys with new features and workflows.

#### Source Files
```
docs/journeys/
├── JOURNEY_NEW_USER.md
├── JOURNEY_ACTIVE_DEVELOPER.md
├── JOURNEY_PROJECT_LEAD.md
└── ...
```

#### Implementation Steps

1. **Review each journey for outdated content**
2. **Add new features:**
   - Implementation mode
   - Token estimation
   - New CLI commands

3. **Update screenshots if included**
4. **Verify all commands still work**

#### Deliverables
- Updated journey documents
- New feature sections added

---

### Task 4.7: Update Walkthroughs with Current Workflows

**Task ID:** `01KDJKTRVZS618BM5ZZTQ3443D`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Update step-by-step walkthroughs to reflect current workflows.

#### Source Files
```
docs/walkthroughs/
├── WALKTHROUGH_NEW_USER.md
├── WALKTHROUGH_ACTIVE_DEVELOPER.md
├── WALKTHROUGH_CONTRIBUTOR.md
└── WALKTHROUGH_PROJECT_LEAD.md
```

#### Implementation Steps

1. **Test each walkthrough step**
2. **Update outdated commands**
3. **Fix incorrect paths/outputs**
4. **Add new workflow sections**

#### Deliverables
- Updated walkthrough documents
- All steps verified working

---

### Task 4.8: Verify CLAUDE.md Accuracy

**Task ID:** `01KDJKTRVZS618BM5ZZTQ3443E`
**Type:** documentation | **Complexity:** simple | **Priority:** medium

#### Description
Verify the main CLAUDE.md file accurately reflects current codebase state.

#### Source File
```
CLAUDE.md
```

#### Implementation Steps

1. **Verify statistics are current:**
   - CLI Commands: 203
   - MCP Tools: 76
   - Platform Adapters: 9
   - Database Tables: 39 (was 30)

2. **Check repository structure is accurate**

3. **Verify common commands work**

4. **Update any outdated sections**

#### Deliverables
- Updated `CLAUDE.md`
- Statistics verified

---

## Sprint Execution Order

```
Task 4.1 (drift audit) ──> Task 4.2 (check-drift)
                            │
Task 4.3 (CLI ref)     ────┬┴──> All updates in parallel
Task 4.4 (MCP ref)     ────┤
Task 4.5 (ADRs)        ────┤
Task 4.6 (journeys)    ────┤
Task 4.7 (walkthroughs)────┤
Task 4.8 (CLAUDE.md)   ────┘
```

## Output Location

Updated files go in their original locations. Change logs go to:
```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-4/outputs/
```

## Success Criteria

- [ ] All 8 tasks completed
- [ ] Documentation drift < 5%
- [ ] CLI reference current (203 commands)
- [ ] MCP reference current (76 tools)
- [ ] All walkthroughs tested
- [ ] CLAUDE.md statistics accurate
