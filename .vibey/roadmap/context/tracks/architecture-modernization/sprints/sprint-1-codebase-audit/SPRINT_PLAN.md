# Sprint 1: Codebase Audit

## Overview
- **Track:** Architecture Modernization
- **Sprint ID:** 01KCMTXFCYYQM97JBH3ST8ZK7V
- **Tasks:** 7
- **Focus:** Comprehensive audit of codebase, CLI commands, and current architecture

## Success Criteria
- [ ] All 169 CLI commands verified and documented
- [ ] Dead code identified and cataloged
- [ ] YAML schema versions audited
- [ ] Directory structure coupling documented
- [ ] Documentation-to-implementation gaps identified

---

## Task 1: Audit All CLI Commands for Existence
**ID:** `01KCMGPAZFAESKAG48GP9ESXTM`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Problem
Documentation claims 169 CLI commands exist, but no systematic verification has been done.

### Implementation Steps
1. Extract documented commands from CLI_REFERENCE.md:
   ```bash
   grep -E "^vibey " docs/reference/CLI_REFERENCE.md | sort -u
   ```

2. Extract actual commands from Click CLI:
   ```python
   # scripts/audit_cli_commands.py
   import click
   from vibey.cli.main import cli

   def get_all_commands(group, prefix=""):
       commands = []
       for name, cmd in group.commands.items():
           full_name = f"{prefix} {name}".strip()
           if isinstance(cmd, click.Group):
               commands.extend(get_all_commands(cmd, full_name))
           else:
               commands.append(full_name)
       return commands

   all_commands = get_all_commands(cli, "vibey")
   print(f"Total commands: {len(all_commands)}")
   ```

3. Compare documented vs actual:
   ```python
   documented = set(documented_commands)
   actual = set(actual_commands)

   missing_from_code = documented - actual
   undocumented = actual - documented
   ```

4. Test each command exists and runs with --help:
   ```bash
   for cmd in "${commands[@]}"; do
       $cmd --help > /dev/null 2>&1 || echo "FAILED: $cmd"
   done
   ```

### Deliverables
- `CLI_COMMAND_AUDIT.md` - Full audit results
- List of missing commands (if any)
- List of undocumented commands (if any)

### Acceptance Criteria
- [ ] All 169 commands verified
- [ ] Discrepancies documented
- [ ] --help works for each command

---

## Task 2: Implement Missing CLI Command Options
**ID:** `01KCMGPER4DR1WFTSRPQ03J40S`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Some documented command options (--filter, --detailed, --format) may not be implemented.

### Implementation Steps
1. Audit documented options per command:
   ```bash
   grep -E "\-\-[a-z]+" docs/reference/CLI_REFERENCE.md
   ```

2. Compare with actual Click options:
   ```python
   def get_command_options(cmd):
       return [p.name for p in cmd.params if isinstance(p, click.Option)]
   ```

3. For each missing option, implement:
   ```python
   @click.option('--filter', '-f',
       help='Filter results by pattern')
   @click.option('--format',
       type=click.Choice(['table', 'json', 'yaml']),
       default='table',
       help='Output format')
   ```

4. Files to modify:
   - `vibey/cli/commands.py`
   - `vibey/cli/roadmap_lib/` modules

### Acceptance Criteria
- [ ] All documented options implemented
- [ ] Options behave as documented
- [ ] Tests added for new options

---

## Task 3: Update Documentation for CLI Command Variations
**ID:** `01KCMGPJFBZ5BWETD1SBGE1N57`
**Priority:** Medium | **Complexity:** Medium | **Type:** Documentation

### Problem
Some commands may have different syntax than documented.

### Implementation Steps
1. For each discrepancy found in Task 1:
   - Determine correct behavior (code or docs is authoritative)
   - Update the incorrect source

2. Update `docs/reference/CLI_REFERENCE.md`:
   ```markdown
   ## vibey roadmap status

   Show roadmap status overview.

   **Actual syntax:**
   ```bash
   vibey roadmap status [--format FORMAT] [--verbose]
   ```
   ```

3. Regenerate CLI reference if auto-generation exists:
   ```bash
   vibey docs generate-cli
   ```

### Acceptance Criteria
- [ ] Documentation matches implementation
- [ ] Examples tested and working
- [ ] No syntax discrepancies

---

## Task 4: Standardize Command Syntax Across Documentation
**ID:** `01KCMGPP8HTCZV0ZPX3TPR2G1W`
**Priority:** Medium | **Complexity:** Medium | **Type:** Documentation

### Problem
Inconsistent command syntax patterns across documentation files.

### Implementation Steps
1. Define syntax conventions:
   ```markdown
   # Command Syntax Conventions
   - Required args: `<arg>`
   - Optional args: `[arg]`
   - Choices: `{option1|option2}`
   - Flags: `--flag` or `-f`
   ```

2. Audit all docs for syntax usage:
   ```bash
   grep -rn "vibey " docs/ --include="*.md"
   ```

3. Standardize across files:
   - `docs/reference/CLI_REFERENCE.md`
   - `docs/walkthroughs/*.md`
   - `docs/journeys/*.md`
   - `README.md`
   - `CLAUDE.md`

### Acceptance Criteria
- [ ] Syntax conventions documented
- [ ] All docs use consistent syntax
- [ ] Examples are copy-pasteable

---

## Task 5: Run Dead Code Analysis with Vulture
**ID:** `01KCMK21BDCPD9K0HSMNKSBZZM`
**Priority:** Low | **Complexity:** Simple | **Type:** Development

### Problem
Codebase may contain dead/unreachable code that should be removed.

### Implementation Steps
1. Install and run vulture:
   ```bash
   pip install vulture
   vulture vibey/ --min-confidence 80
   ```

2. Analyze results:
   ```bash
   # Save results
   vulture vibey/ --min-confidence 80 > dead_code_report.txt

   # Categorize findings:
   # - Confirmed dead (safe to remove)
   # - False positives (dynamically called)
   # - Uncertain (needs investigation)
   ```

3. Create whitelist for false positives:
   ```python
   # vulture_whitelist.py
   # MCP tools called dynamically
   roadmap_status  # unused function
   task_start  # unused function
   ```

4. Document findings in `DEAD_CODE_AUDIT.md`

### Deliverables
- `DEAD_CODE_AUDIT.md` - Analysis results
- `vulture_whitelist.py` - False positives
- List of code safe to remove

### Acceptance Criteria
- [ ] Vulture scan completed
- [ ] False positives identified
- [ ] Removal candidates documented

---

## Task 6: Audit YAML Schema Versions Before Cleanup
**ID:** `01KCMJRNHDRD8XGAG19JD8Q63V`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Legacy YAML schema support may exist in codebase. Need to audit before removal.

### Implementation Steps
1. Identify schema version handling code:
   ```bash
   grep -rn "schema_version\|version:" vibey/
   grep -rn "v1\|v2\|legacy" vibey/roadmap/
   ```

2. Check current YAML files for version markers:
   ```bash
   head -5 .vibey/roadmap/tracks/*.yaml
   head -5 .vibey/roadmap/sprints/*.yaml
   head -5 .vibey/roadmap/tasks/*.yaml
   ```

3. Document schema evolution:
   ```markdown
   # YAML Schema History

   ## v1 (Legacy)
   - Hierarchical directory structure
   - Slug-based IDs

   ## v2 (Current)
   - Flat ULID structure (ADR-0002)
   - ULID identifiers (ADR-0001)
   ```

4. Assess backward compatibility needs:
   - Any external tools consuming YAML?
   - Any migration scripts needed?

### Acceptance Criteria
- [ ] Schema versions documented
- [ ] Legacy code paths identified
- [ ] Migration needs assessed

---

## Task 7: Audit Current Directory Structure Coupling to Semantic Layer
**ID:** `01KCMNWN6AFSP5NMVQHBG5RWXD`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Directory structure (tracks/, sprints/, tasks/) mirrors semantic concepts. This coupling may limit flexibility.

### Implementation Steps
1. Map directory structure to semantic concepts:
   ```
   Directory              | Semantic Concept
   -----------------------|------------------
   .vibey/roadmap/tracks/ | Track (work unit)
   .vibey/roadmap/sprints/| Sprint (time box)
   .vibey/roadmap/tasks/  | Task (atomic unit)
   ```

2. Identify coupling points in code:
   ```bash
   grep -rn "tracks/\|sprints/\|tasks/" vibey/
   ```

3. Document where coupling exists:
   - Path construction utilities
   - YAML loaders/dumpers
   - SQL queries
   - CLI commands
   - MCP tools

4. Identify decoupling opportunities:
   - Abstract path construction
   - Use IDs not paths for references
   - Separate storage from semantics

### Deliverables
- `SEMANTIC_COUPLING_AUDIT.md` - Analysis document
- Coupling points inventory
- Decoupling recommendations

### Acceptance Criteria
- [ ] All coupling points documented
- [ ] Impact assessment complete
- [ ] Decoupling strategy outlined

---

## Sprint Completion Checklist
- [ ] CLI command audit complete (169 commands)
- [ ] Dead code identified
- [ ] Schema versions documented
- [ ] Directory coupling analyzed
- [ ] Documentation synchronized
- [ ] All findings in context/ directory
