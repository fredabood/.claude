# Sprint 1: Critical Documentation Fixes

## Overview
- **Track:** Documentation Quality
- **Sprint ID:** 01KCMTKTGB41SQCSNG893TXB3B
- **Tasks:** 6
- **Focus:** Fix broken, outdated, and incorrect documentation that blocks new users

## Success Criteria
- [ ] All installation instructions show `pip install -e .` workflow
- [ ] All path references use flat ULID structure
- [ ] All deprecated `/vibey` slash command references removed
- [ ] All broken internal links fixed
- [ ] All hardcoded versions replaced with semantic examples
- [ ] No commented code blocks in codebase

---

## Task 1: Fix Installation Documentation
**ID:** `01KCMGKFVX305KDTRFMKWQB66E`
**Priority:** Critical | **Complexity:** Simple | **Type:** Documentation

### Problem
Documentation shows `pip install vibey` but the package isn't published to PyPI. Users must clone and install in editable mode.

### Files to Modify
1. `README.md` - Main installation section
2. `docs/walkthroughs/WALKTHROUGH_NEW_USER.md` - Getting started steps
3. `docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md` - Developer setup
4. `docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md` - Daily workflow
5. `docs/journeys/JOURNEY_NEW_USER.md` - First-time user path
6. `docs/development/SETUP.md` - Development environment setup
7. `CONTRIBUTING.md` - Contributor instructions

### Implementation Steps
1. Search for all instances of `pip install vibey`:
   ```bash
   grep -r "pip install vibey" docs/ README.md CONTRIBUTING.md
   ```

2. Replace with the correct installation workflow:
   ```markdown
   ## Installation

   ```bash
   git clone https://github.com/your-org/vibey.git
   cd vibey
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Ensure each file includes:
   - Git clone step
   - Virtual environment creation
   - Editable install with dev dependencies

### Acceptance Criteria
- [ ] No instances of `pip install vibey` without clone context
- [ ] All installation sections include git clone
- [ ] Virtual environment setup included
- [ ] Dev dependencies mentioned where appropriate

---

## Task 2: Update Path References to Flat ULID Structure
**ID:** `01KCMGKKFVJMGTXYS94Z8XA6BP`
**Priority:** Critical | **Complexity:** Medium | **Type:** Documentation

### Problem
Documentation references old hierarchical paths like `.vibey/roadmap/track-name/sprint-name/task-name/` but the system now uses flat ULID-based paths.

### Old vs New Format
```
# OLD (hierarchical)
.vibey/roadmap/sqlite-backend/sqlite-backend-1/sqlite-backend-1-task-001/task.yaml

# NEW (flat ULID)
.vibey/roadmap/tasks/01KC2D0JK7READW9KAK1HBX4B8.yaml
```

### Files to Modify
1. All files in `docs/journeys/`
2. All files in `docs/walkthroughs/`
3. `docs/reference/CLI_REFERENCE.md`
4. `docs/reference/MCP_REFERENCE.md`
5. `CLAUDE.md`
6. `README.md`
7. Any ADRs referencing paths

### Implementation Steps
1. Search for old path patterns:
   ```bash
   grep -rE "\.vibey/roadmap/[a-z]+-[a-z]+/" docs/ CLAUDE.md README.md
   grep -rE "track-name|sprint-name|task-name" docs/
   ```

2. Replace hierarchical examples with ULID examples:
   ```markdown
   # Task files
   .vibey/roadmap/tasks/01KC2D0JK7READW9KAK1HBX4B8.yaml

   # Sprint files
   .vibey/roadmap/sprints/01KC2D0JKVT80AFQ6C1PA8CKJD.yaml

   # Track files
   .vibey/roadmap/tracks/01KC2D0JK9JKQXGQW6MQEB0JZP.yaml
   ```

3. Update any directory structure diagrams to show:
   ```
   .vibey/roadmap/
   ├── tracks/           # All track YAML files
   ├── sprints/          # All sprint YAML files
   ├── tasks/            # All task YAML files
   ├── context/          # Sprint plans and context docs
   └── roadmap.db        # SQLite cache
   ```

### Acceptance Criteria
- [ ] No hierarchical path examples in documentation
- [ ] All examples use 26-character ULIDs
- [ ] Directory structure diagrams updated
- [ ] CLI examples show ULID-based commands

---

## Task 3: Update Deprecated /vibey Slash Command References
**ID:** `01KCMJQYE66NZQFBJDN4JTPDJA`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
56 files reference deprecated `/vibey` slash commands that were removed in v2.5.0. Users attempting these commands will fail.

### Files to Modify
Run this to find all affected files:
```bash
grep -rl "/vibey" docs/ --include="*.md"
```

### Slash Command to CLI Mapping
| Deprecated Slash Command | New CLI Command |
|--------------------------|-----------------|
| `/vibey status` | `vibey roadmap status` |
| `/vibey start <task>` | `vibey roadmap start <task-id>` |
| `/vibey complete <task>` | `vibey roadmap complete <task-id>` |
| `/vibey list tasks` | `vibey roadmap list tasks` |
| `/vibey show <id>` | `vibey roadmap show <id>` |

### Implementation Steps
1. Find all slash command references:
   ```bash
   grep -rn "/vibey" docs/ CLAUDE.md README.md
   ```

2. For each occurrence:
   - Replace `/vibey <command>` with `vibey <command>`
   - Update any surrounding context explaining slash commands
   - Remove references to "slash command" interface

3. Update any sections explaining the slash command interface to explain CLI usage instead

### Acceptance Criteria
- [ ] No `/vibey` references in documentation
- [ ] All command examples use `vibey` CLI format
- [ ] No references to "slash commands" for vibey operations

---

## Task 4: Fix Broken Documentation Links
**ID:** `01KCMGKTSVT6EVSSBPK1ZDY51G`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
Internal documentation links reference files that have been moved, renamed, or deleted.

### Implementation Steps
1. Find all markdown links:
   ```bash
   grep -rhoE "\[.*?\]\(.*?\.md\)" docs/ | sort | uniq
   ```

2. For each link, verify the target exists:
   ```bash
   # Example verification script
   for link in $(grep -rhoE "\]\([^)]+\.md\)" docs/ | sed 's/.*(\(.*\))/\1/'); do
     if [ ! -f "docs/$link" ] && [ ! -f "$link" ]; then
       echo "BROKEN: $link"
     fi
   done
   ```

3. Fix each broken link by either:
   - Updating the path to the correct location
   - Removing the link if the content no longer exists
   - Creating a redirect note if content was merged elsewhere

### Common Broken Link Patterns
- Links to old hierarchical paths
- Links to removed architecture docs
- Links to renamed journey files
- Relative vs absolute path issues

### Acceptance Criteria
- [ ] All internal markdown links resolve
- [ ] No 404s when navigating documentation
- [ ] Link audit script passes with 0 broken links

---

## Task 5: Fix Version Hardcoding in Examples
**ID:** `01KCMGKQ45XM3PVZVH02ZJGQQ0`
**Priority:** Medium | **Complexity:** Simple | **Type:** Documentation

### Problem
Documentation hardcodes version "2.5.0" which becomes outdated. Should use semantic version patterns or dynamic references.

### Files to Modify
```bash
grep -rn "2\.5\.0" docs/ CLAUDE.md README.md CHANGELOG.md
```

### Implementation Steps
1. Find all version hardcoding:
   ```bash
   grep -rn "2\.[0-9]\.[0-9]" docs/
   ```

2. Replace with appropriate alternatives:
   - For examples: Use `X.Y.Z` or `2.x.x`
   - For "current version": Reference CHANGELOG.md
   - For installation: Remove version pinning

3. Keep version references only in:
   - CHANGELOG.md (historical record)
   - Release notes
   - Migration guides (specific version context needed)

### Acceptance Criteria
- [ ] No hardcoded versions in example code
- [ ] Version references in docs point to CHANGELOG.md
- [ ] Examples use semantic version placeholders

---

## Task 6: Clean Up Commented Code Blocks
**ID:** `01KCMGKYG26JYBNT81Z6KWQPYY`
**Priority:** Low | **Complexity:** Simple | **Type:** Infrastructure

### Problem
Codebase contains commented-out code blocks that should be removed for cleanliness.

### Files to Search
```bash
# Python files with large comment blocks
grep -rn "^#.*#.*#" vibey/ --include="*.py"

# Multi-line commented code
grep -B2 -A2 "# TODO: remove" vibey/
grep -B2 -A2 "# DEPRECATED" vibey/
```

### Implementation Steps
1. Search for commented code patterns:
   ```bash
   # Find files with 3+ consecutive comment lines (potential commented code)
   grep -l "^#" vibey/**/*.py | xargs -I{} sh -c 'echo "=== {} ===" && grep -n "^#" {}'
   ```

2. Review each instance and determine if it's:
   - Documentation comment (KEEP)
   - TODO/FIXME comment (REVIEW)
   - Commented-out code (REMOVE)
   - Debug code (REMOVE)

3. Remove commented code, keeping only:
   - Module/function docstrings
   - Explanatory comments
   - Type hints comments
   - License headers

### Acceptance Criteria
- [ ] No commented-out code blocks
- [ ] No `# TODO: remove` comments
- [ ] No deprecated code left commented
- [ ] All remaining comments add value

---

## Sprint Completion Checklist
- [ ] All 6 tasks completed
- [ ] Documentation builds without errors
- [ ] All internal links verified
- [ ] Changes committed with descriptive messages
- [ ] CHANGELOG.md updated if needed
