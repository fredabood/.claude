# Command Reference

Complete reference for all Vibey slash commands.

---

## Overview

Vibey provides a unified `/vibey` command that adapts to your project state:
- **First-time:** Initialization and setup
- **Returning:** Access to all framework features

---

## Main Command

### `/vibey`

**Dual-Mode Command:** Detects framework state and adapts behavior.

**First-Time Usage (Initialization Mode):**
```
/vibey
```

Shows welcome and 5 main options:
1. Sprint Planning
2. Execute Sprint
3. Discovery Mode (Brainstorming & Audit)
4. Framework Management
5. Exit

**Returning Usage (Management Mode):**
```
/vibey
```

Shows brief welcome and same 4 options.

**How Detection Works:**
- Checks for `.claude/.vibey-initialized` marker
- Checks for `.claude/CLAUDE.md` with Vibey marker
- Checks for `.claude/project-config.yaml`
- If all present: Management Mode
- Otherwise: Initialization Mode

---

## Sub-Commands

### `/vibey plan`

**Purpose:** Sprint planning

**Usage:**
```
/vibey plan
```

**What It Does:**
1. Checks for existing PROJECT-CONTEXT.md
2. Offers to use existing context or start fresh
3. Launches conversational sprint planning
4. Generates:
   - `docs/sprints/sprint-N-plan.md` - Sprint plan
   - `docs/sprints/sprint-N-state.yaml` - Sprint state tracking
   - `.claude/project-config.yaml` - Project configuration (first sprint only)
   - `.claude/CLAUDE.md` - Framework context (first sprint only)

**Options During Planning:**
- Use existing context (if available)
- Run codebase audit first (recommended for existing projects)
- Start from scratch

**Output Files:**
- Sprint plan: `docs/sprints/sprint-N-plan.md`
- Sprint state: `docs/sprints/sprint-N-state.yaml`
- Context archive: `docs/sprints/sprint-N-context.md` (if PROJECT-CONTEXT existed)

---

### `/vibey code`

**Purpose:** Sprint execution

**Usage:**
```
/vibey code
```

**What It Does:**
1. Checks for active sprint
2. If active: Shows sprint dashboard
3. If none: Offers to start existing or create new

**Sprint Dashboard Options:**
1. Continue current phase
2. View phase orchestration rules
3. Check quality gate status
4. Mark phase complete
5. View sprint plan
6. Update sprint progress
7. Pause sprint
8. Complete sprint
9. Return to main menu

**State Management:**
- Tracks tasks, agents, quality gates
- Updates sprint state file continuously
- Git commits after each phase
- Archives sprint on completion

---

### `/vibey think`

**Purpose:** Discovery Mode (Audit & Brainstorming)

**Usage:**
```
/vibey think
```

**What It Does:**

**If PROJECT-CONTEXT.md Exists:**
- Resume existing context
- Replace with new context (archives old)
- View current context
- Restore from archive

**If No Context:**
- Option 1: Start with project audit (recommended for existing projects)
  - Full Audit (codebase + git history) - 70-125 min
  - Codebase Only - 60-105 min
  - Git History Only - 10-20 min
- Option 2: Start with conversation (for new projects)
  - Interactive Q&A
  - Iterative context building

**Output:**
- `.claude/PROJECT-CONTEXT.md` - Unified discovery output
- Archived contexts: `docs/archive/discovery/`

**Context Lifecycle:**
- Create → Update → Archive on replace
- Archive to sprint: `docs/sprints/sprint-N-context.md`
- Restore from archives

---

### `/vibey manage`

**Purpose:** Framework configuration management

**Usage:**
```
/vibey manage
```

**Configuration Options:**
1. Update quality gate thresholds
2. Modify tech stack
3. Change framework settings
4. Regenerate CLAUDE.md
5. Framework health check
6. View framework files
7. Return to main menu
8. Exit

**Management Features:**

**1. Update Quality Gate Thresholds:**
- Test coverage minimum
- Security score minimum
- Logging audit minimum
- All thresholds

**2. Modify Tech Stack:**
- Backend framework
- Frontend framework
- Database
- Testing frameworks
- All tech stack

**3. Change Framework Settings:**
- Auto agent launch (true/false)
- Quality gates required (true/false)
- Sprint-driven orchestration (enabled/disabled)

**4. Regenerate CLAUDE.md:**
- Backup current (optional)
- Regenerate from template
- Applies all config changes

**5. Framework Health Check:**
- Python environment
- Framework files
- Framework directories
- Critical scripts
- Framework version
- Sprint context
- Project directories
- Actionable recommendations

**6. View Framework Files:**
- List agents by category
- List workflows
- List templates

---

## Command Workflows

### First-Time Project Setup

```
/vibey
└─> Choose deployment option
    └─> Framework files copied to .claude/
        └─> Choose: Sprint Planning
            └─> /vibey plan
                └─> Sprint plan created
                    └─> /vibey code
                        └─> Sprint execution begins
```

### Existing Project with Codebase

```
/vibey
└─> Choose: Discovery Mode
    └─> /vibey think
        └─> Choose: Start with project audit
            └─> Audit completes
                └─> PROJECT-CONTEXT.md created
                    └─> Choose: Continue with Q&A or Plan sprint
                        └─> /vibey plan
                            └─> Sprint plan created (uses context)
```

### Ongoing Development

```
/vibey code
└─> Dashboard shows current phase
    └─> Work on tasks
        └─> Mark phase complete
            └─> Move to next phase
                └─> Repeat until sprint complete
                    └─> /vibey plan (for next sprint)
```

### Framework Management

```
/vibey manage
└─> Choose management task
    └─> Update configuration
        └─> CLAUDE.md regenerated
            └─> Changes applied
```

---

## Script Commands

### Version Checking

**Check Version:**
```bash
python3 .claude/scripts/check-version.py
```

**Options:**
```bash
--verbose      # Show message even when up to date
--quiet        # Exit code only (0=current, 1=upgrade available)
--version      # Show available version
```

**Exit Codes:**
- 0: Up to date
- 1: Upgrade available
- 2: Error or unknown version

---

### Config Management

**Generate Config:**
```bash
python3 .claude/scripts/generate-config.py \
  --project-name "Your Project" \
  --project-type web-app \
  --tech-stack "Python/FastAPI, React, PostgreSQL" \
  --output .claude/project-config.yaml
```

**Update Config:**
```bash
python3 .claude/scripts/update-config.py \
  --config .claude/project-config.yaml \
  --key "quality_gates.unit_testing.coverage_minimum" \
  --value "90"
```

**Validate Config:**
```bash
python3 .claude/scripts/validate-config.py .claude/project-config.yaml
```

---

### Project Context Management

**Create Context:**
```bash
python3 .claude/scripts/manage-project-context.py create \
  --source audit \
  --audit-file docs/codebase-audit-report.md
```

**Update Context:**
```bash
python3 .claude/scripts/manage-project-context.py update \
  --ready-for-sprint true
```

**Archive Context:**
```bash
python3 .claude/scripts/manage-project-context.py archive \
  --reason sprint_created \
  --sprint 1
```

**Restore Context:**
```bash
python3 .claude/scripts/manage-project-context.py restore \
  --file docs/archive/discovery/context-20241105-140022-replaced.md
```

**Query Context:**
```bash
python3 .claude/scripts/manage-project-context.py query \
  --field summary
```

**List Archives:**
```bash
python3 .claude/scripts/manage-project-context.py list-archives
```

---

### Roadmap Management

**View Roadmap Status:**
```bash
# Overview of all tracks and sprints
python3 .claude/scripts/roadmap status

# JSON output for programmatic access
python3 .claude/scripts/roadmap status --json
```

**Sprint Management:**
```bash
# Create sprint from plan file
python3 .claude/scripts/roadmap plan create \
  --track-id main \
  --from-plan sprint-1-plan.md \
  --sprint-id sprint-1 \
  --start

# List all sprints
python3 .claude/scripts/roadmap list sprints

# Start a sprint
python3 .claude/scripts/roadmap start sprint-1

# Complete a sprint
python3 .claude/scripts/roadmap complete sprint-1
```

**Task Management:**
```bash
# List all tasks
python3 .claude/scripts/roadmap list tasks

# List tasks with JSON output
python3 .claude/scripts/roadmap list tasks --json

# Start a task
python3 .claude/scripts/roadmap start task-001

# Complete a task
python3 .claude/scripts/roadmap complete task-001

# Assign task to agent
python3 .claude/scripts/roadmap assign task-001 web-developer
```

**Quality Gate Management:**
```bash
# List quality gates for a sprint
python3 .claude/scripts/roadmap gate list sprint-1

# Update quality gate status
python3 .claude/scripts/roadmap gate update sprint-1 "Security Audit" passed --score 85

# Update gate without score
python3 .claude/scripts/roadmap gate update sprint-1 "Code Review" failed
```

**Dependency Management:**
```bash
# Show all dependencies
python3 .claude/scripts/roadmap deps

# Show dependencies for specific sprint/task
python3 .claude/scripts/roadmap deps sprint-2

# Show only blockers
python3 .claude/scripts/roadmap deps --blockers

# Show what depends on this (reverse dependencies)
python3 .claude/scripts/roadmap deps task-001 --dependents
```

**Agent Management:**
```bash
# View agent workload
python3 .claude/scripts/roadmap agents --workload

# View specific agent details
python3 .claude/scripts/roadmap agents --agent web-developer

# Get task recommendations
python3 .claude/scripts/roadmap recommend

# Get recommendations for specific agent
python3 .claude/scripts/roadmap recommend --agent web-developer --limit 5
```

**Search and Validation:**
```bash
# Search for tasks/sprints
python3 .claude/scripts/roadmap find "authentication"

# Search specific type
python3 .claude/scripts/roadmap find "security" --type sprint

# Validate roadmap structure
python3 .claude/scripts/roadmap validate

# Validate and fix issues
python3 .claude/scripts/roadmap validate --fix
```

**Note:** Sprint markers in CLAUDE.md are updated via sed commands:
```bash
# Update CLAUDE.md sprint marker
sed -i.bak 's/<!-- CURRENT_SPRINT: .* -->/<!-- CURRENT_SPRINT: sprint-1 -->/' .claude/CLAUDE.md
sed -i.bak 's/\*\*Current Sprint:\*\* .*/\*\*Current Sprint:\*\* sprint-1/' .claude/CLAUDE.md
```

---

### Framework Rollback

**List Backups:**
```bash
python3 .claude/scripts/rollback-framework.py --list
```

**Rollback to Recent:**
```bash
python3 .claude/scripts/rollback-framework.py --auto
```

**Rollback to Specific:**
```bash
python3 .claude/scripts/rollback-framework.py \
  --backup .claude-backup-20241105-143022
```

**Dry Run:**
```bash
python3 .claude/scripts/rollback-framework.py --auto --dry-run
```

---

### Template Rendering

**Render Template:**
```bash
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

---

## Environment Variables

Vibey doesn't currently use environment variables, but configuration is managed through:
- `.claude/project-config.yaml` - Project configuration
- `.claude/.vibey-initialized` - Framework marker
- `.claude/CLAUDE.md` - Generated context file

---

## Exit Codes

**Standard Exit Codes:**
- 0: Success
- 1: Error or failure
- 2: Invalid usage or configuration error

**Script-Specific:**
- `check-version.py`: 0=current, 1=upgrade, 2=error
- Most other scripts: 0=success, 1=error

---

## Tips & Tricks

### Quick Health Check
```bash
python3 .claude/scripts/check-version.py && echo "Framework OK"
```

### Backup Before Changes
```bash
cp -r .claude .claude-backup-$(date +%Y%m%d-%H%M%S)
```

### Reset Sprint State
```bash
# Recreate from plan
python3 .claude/scripts/create-sprint-state.py \
  --plan-file docs/sprints/sprint-1-plan.md \
  --output docs/sprints/sprint-1-state.yaml
```

### View Raw State
```bash
cat docs/sprints/sprint-1-state.yaml
```

### Grep for Issues
```bash
grep -r "TODO\|FIXME\|XXX" docs/sprints/
```

---

## See Also

- [Getting Started](../getting-started/QUICK_START.md) - Setup and first steps
- [Troubleshooting](../TROUBLESHOOTING.md) - Common issues and solutions
- [FAQ](../FAQ.md) - Frequently asked questions
- [Guides](../guides/) - In-depth usage guides

---

**Last Updated:** 2024-11-05
**Framework Version:** 1.2.0
