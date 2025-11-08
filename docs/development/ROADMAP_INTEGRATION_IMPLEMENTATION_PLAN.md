# Roadmap Integration Implementation Plan

**Track:** roadmap-integration
**Goal:** Integrate roadmap system into /vibey commands, deprecate legacy sprint-state scripts
**Duration:** 6 weeks (3 sprints × 2 weeks)
**Priority:** 🔴 CRITICAL PATH
**Status:** Ready to Start

---

## Executive Summary

### The Problem

Vibey has two parallel sprint state management systems:
1. **Legacy System** (`docs/sprints/*.yaml`) - Used by `/vibey` commands
2. **Roadmap System** (`.vibey/`) - Advanced features, but NOT integrated

**Result:** Users can't leverage multi-sprint planning, dependency tracking, or roadmap capabilities.

### The Solution

**3-Sprint Integration Plan:**
1. **Sprint 1:** Foundation & Sprint Planning Integration (2 weeks)
2. **Sprint 2:** Progress Tracking & Vibey Manager (2 weeks)
3. **Sprint 3:** Migration & Deprecation (2 weeks)

### Success Criteria

- [ ] `/vibey` commands use roadmap system exclusively
- [ ] Users can create multi-sprint roadmaps
- [ ] Dependency tracking works across sprints
- [ ] Legacy scripts deprecated
- [ ] Migration path for existing projects
- [ ] Documentation updated
- [ ] ~1,657 lines of duplicate code removed

---

## Architecture Design

### Integration Strategy

**Principle:** Minimal Disruption, Maximum Value

1. **Preserve User Experience** - `/vibey` commands work the same way
2. **Additive Changes** - Add roadmap features without breaking existing workflows
3. **Graceful Migration** - Support both systems during transition
4. **Clear Deprecation** - Remove legacy code only after migration complete

### Data Flow (After Integration)

```
User: /vibey deployment
    ↓
Initialize Framework
    ├── Copy framework files → .claude/
    ├── Create docs/sprints/ (for markdown plans)
    └── Initialize roadmap → .vibey/ (NEW!)
        ├── roadmap.yaml
        ├── tracks/
        ├── sprints/
        └── tasks/
    ↓
Done - Ready for planning


User: /vibey plan
    ↓
Sprint Planning Dialog
    ↓
Generate Sprint Plan
    ├── docs/sprints/sprint-N-plan.md (markdown - keep!)
    └── .vibey/sprints/sprint-N.yaml (NEW!)
    ↓
Create Tasks
    └── .vibey/tasks/sprint-N-tasks.yaml (NEW!)
    ↓
Detect Dependencies (automatic)
    └── Update blocks/depends_on fields
    ↓
Update CLAUDE.md marker
    ↓
Done - Ready for execution


User: /vibey code
    ↓
Load Sprint State
    ├── Read .vibey/sprints/sprint-N.yaml (NEW!)
    └── Read docs/sprints/sprint-N-plan.md (reference)
    ↓
Display Dashboard
    └── roadmap-query.py show sprint-N (NEW!)
    ↓
User Actions
    ├── Update task → roadmap-update.py progress_task (NEW!)
    ├── Log agent → roadmap-update.py log_agent (NEW!)
    └── Complete sprint → roadmap-update.py complete_sprint (NEW!)
    ↓
Done - State tracked in roadmap
```

### File Structure (After Integration)

```
project/
├── .claude/                          # Framework deployment (unchanged)
│   ├── CLAUDE.md                     # Project context (sprint marker updated)
│   ├── project-config.yaml           # Project config (unchanged)
│   ├── scripts/
│   │   ├── roadmap-*.py              # Roadmap scripts (primary)
│   │   ├── *-sprint-state.py         # DEPRECATED (removed in Sprint 3)
│   │   └── update-sprint-marker.py   # Keep (updates CLAUDE.md)
│   └── ...
│
├── .vibey/                           # Roadmap system (NEW!)
│   ├── roadmap.yaml                  # Top-level metadata
│   ├── tracks/
│   │   └── main-track.yaml           # Default track for projects
│   ├── sprints/
│   │   ├── sprint-1.yaml             # Sprint metadata + state
│   │   └── sprint-2.yaml
│   └── tasks/
│       ├── sprint-1-tasks.yaml       # Task details + dependencies
│       └── sprint-2-tasks.yaml
│
└── docs/
    └── sprints/                      # Sprint documentation (keep!)
        ├── sprint-1-plan.md          # Human-readable plan
        └── sprint-2-plan.md
```

### Script Mapping

| Legacy Script | Roadmap Replacement | Action |
|--------------|---------------------|--------|
| `create-sprint-state.py` | `roadmap-update.py --action create_sprint` | Deprecate |
| `update-sprint-state.py` | `roadmap-update.py --action progress_*` | Deprecate |
| `query-sprint-state.py` | `roadmap-query.py show/status` | Deprecate |
| `update-sprint-marker.py` | Keep (still needed for CLAUDE.md) | Keep |

### Backward Compatibility

**During Sprint 1-2 (Transition Period):**
- Support BOTH systems simultaneously
- Auto-detect which system is in use
- Provide migration hints

**Detection Logic:**
```bash
if [ -f ".vibey/roadmap.yaml" ]; then
    SYSTEM="roadmap"
    # Use roadmap-*.py scripts
elif [ -f "docs/sprints/sprint-1-state.yaml" ]; then
    SYSTEM="legacy"
    # Use old scripts, show migration prompt
else
    SYSTEM="new"
    # Initialize roadmap
fi
```

**Migration Prompt:**
```
⚠️  LEGACY SPRINT STATE DETECTED

Your project uses the legacy sprint-state system (docs/sprints/*.yaml).
We recommend migrating to the new roadmap system for:
  ✓ Multi-sprint dependency tracking
  ✓ Cross-sprint blockers
  ✓ Advanced progress visualization
  ✓ Better agent workload management

Run: /vibey migrate
```

---

## Sprint 1: Foundation & Sprint Planning Integration

**Duration:** 2 weeks
**Goal:** Enable roadmap initialization and sprint planning via /vibey commands

### Tasks

#### Task 1.1: Update /vibey Deployment Command
**File:** `framework/commands/vibey.md`
**Estimated:** 6 hours

**Changes:**
1. Add roadmap initialization after framework deployment (line 1111)
2. Create default track for project
3. Initialize .vibey/ directory structure

**Code Addition (Line 1111):**
```bash
echo ""
echo "📊 Initializing roadmap system..."

# Initialize roadmap with project defaults
python3 .claude/scripts/roadmap-init.py \
  --project-name "${PROJECT_NAME}" \
  --root-dir . \
  --version "0.1.0" \
  --bump-on "sprint_completion" \
  --bump-type "patch"

# Create default track
python3 .claude/scripts/roadmap-update.py \
  --action "create_track" \
  --track-id "main" \
  --name "Main Development Track" \
  --goal "Deliver ${PROJECT_NAME} functionality"

echo "✓ Roadmap system initialized (.vibey/)"
echo "  - Roadmap: .vibey/roadmap.yaml"
echo "  - Track: main"
echo "  - Ready for sprint planning"
```

**Testing:**
- [ ] Run `/vibey` on fresh project
- [ ] Verify `.vibey/` directory created
- [ ] Verify `roadmap.yaml` has correct project name
- [ ] Verify `tracks/main.yaml` created

---

#### Task 1.2: Update /vibey plan Command
**File:** `framework/commands/vibey-plan.md`
**Estimated:** 8 hours

**Changes:**
1. Replace `create-sprint-state.py` call (lines 201-213)
2. Add roadmap sprint creation
3. Add task extraction from plan
4. Add dependency detection

**Code Replacement (Lines 201-234):**
```bash
# OLD (Remove):
# python3 .claude/scripts/create-sprint-state.py

# NEW:
echo "📊 Creating roadmap sprint entry..."

# Step 8: Create sprint in roadmap
python3 .claude/scripts/roadmap-update.py \
  --action "create_sprint" \
  --track-id "main" \
  --sprint-id "sprint-${SPRINT_NUMBER}" \
  --name "Sprint ${SPRINT_NUMBER}: ${SPRINT_NAME}" \
  --goal "${SPRINT_GOAL}" \
  --plan-file "docs/sprints/sprint-${SPRINT_NUMBER}-plan.md" \
  --duration "2 weeks"

echo "✓ Sprint created: sprint-${SPRINT_NUMBER}"

# Step 9: Extract and create tasks from plan
echo "📋 Extracting tasks from plan..."
python3 .claude/scripts/roadmap-update.py \
  --action "create_tasks_from_plan" \
  --sprint-id "sprint-${SPRINT_NUMBER}" \
  --plan-file "docs/sprints/sprint-${SPRINT_NUMBER}-plan.md"

TASK_COUNT=$(python3 .claude/scripts/roadmap-query.py count-tasks sprint-${SPRINT_NUMBER})
echo "✓ Created ${TASK_COUNT} tasks"

# Step 10: Detect dependencies between tasks
echo "🔗 Detecting task dependencies..."
python3 .claude/scripts/roadmap-update.py \
  --action "detect_dependencies" \
  --sprint-id "sprint-${SPRINT_NUMBER}"

DEP_COUNT=$(python3 .claude/scripts/roadmap-query.py count-deps sprint-${SPRINT_NUMBER})
echo "✓ Detected ${DEP_COUNT} dependencies"

# Step 11: Update sprint marker in CLAUDE.md (keep this)
python3 .claude/scripts/update-sprint-marker.py \
  --sprint-number ${SPRINT_NUMBER} \
  --sprint-name "${SPRINT_NAME}"

echo ""
echo "✅ Sprint ${SPRINT_NUMBER} ready for execution"
echo "   View roadmap: ./framework/scripts/roadmap status"
echo "   Start sprint: /vibey code"
```

**Testing:**
- [ ] Run `/vibey plan` on fresh project
- [ ] Verify sprint created in `.vibey/sprints/`
- [ ] Verify tasks created in `.vibey/tasks/`
- [ ] Verify dependencies detected
- [ ] Verify CLAUDE.md updated with sprint marker

---

#### Task 1.3: Create roadmap-update.py Actions
**File:** `framework/scripts/roadmap-update.py`
**Estimated:** 10 hours

**New Actions Needed:**

1. **`create_sprint`** - Create sprint from plan file
   - Parse plan markdown for metadata
   - Create sprint YAML in .vibey/sprints/
   - Update track with sprint reference
   - Return sprint ID

2. **`create_tasks_from_plan`** - Extract tasks from plan
   - Parse markdown plan for task sections
   - Identify task descriptions
   - Detect phases/milestones
   - Create task YAML entries
   - Return task IDs

3. **`detect_dependencies`** - Auto-detect task dependencies
   - Analyze task descriptions for keywords ("requires", "depends on", "after")
   - Check for task ID references
   - Detect phase ordering
   - Create dependency entries
   - Update blocks/depends_on fields

**Implementation Details:**
```python
def create_sprint_from_plan(track_id, sprint_id, name, goal, plan_file, duration):
    """
    Create sprint entry in roadmap from plan file.

    Args:
        track_id: Parent track
        sprint_id: Unique sprint identifier
        name: Sprint name
        goal: Sprint objective
        plan_file: Path to sprint plan markdown
        duration: Estimated duration

    Returns:
        Sprint data dictionary
    """
    # Parse plan file for metadata
    plan = parse_sprint_plan(plan_file)

    # Create sprint YAML
    sprint = {
        'id': sprint_id,
        'track_id': track_id,
        'name': name,
        'goal': goal,
        'status': 'not_started',
        'estimated_duration': duration,
        'plan_file': plan_file,
        'phases': plan.get('phases', []),
        'deliverables': plan.get('deliverables', []),
        'dependencies': [],
        'blocks': [],
        'quality_gates': plan.get('quality_gates', []),
        'created': datetime.now(timezone.utc).isoformat(),
    }

    # Save to .vibey/sprints/{sprint_id}.yaml
    save_sprint(sprint)

    # Update track reference
    add_sprint_to_track(track_id, sprint_id)

    return sprint


def create_tasks_from_plan(sprint_id, plan_file):
    """
    Extract tasks from sprint plan markdown.

    Looks for:
    - ## Phase sections
    - Task lists (- [ ] ...)
    - Numbered steps

    Returns:
        List of created task IDs
    """
    plan = parse_sprint_plan(plan_file)
    tasks = []

    for phase_idx, phase in enumerate(plan['phases']):
        for task_idx, task_desc in enumerate(phase['tasks']):
            task_id = f"{sprint_id}-task-{phase_idx+1:03d}-{task_idx+1:03d}"

            task = {
                'id': task_id,
                'sprint_id': sprint_id,
                'name': task_desc,
                'phase': phase['name'],
                'status': 'not_started',
                'dependencies': [],
                'assigned_agents': infer_agents(task_desc),
                'created': datetime.now(timezone.utc).isoformat(),
            }

            tasks.append(task)

    # Save to .vibey/tasks/{sprint_id}-tasks.yaml
    save_tasks(sprint_id, tasks)

    return [t['id'] for t in tasks]


def detect_dependencies(sprint_id):
    """
    Auto-detect dependencies between tasks.

    Strategies:
    1. Keyword analysis ("requires", "depends on", "after")
    2. Task ID references in descriptions
    3. Phase ordering (tasks in later phases depend on earlier)
    4. Agent sequencing (same agent, sequential tasks)

    Returns:
        Number of dependencies detected
    """
    tasks = load_tasks(sprint_id)
    dependencies_added = 0

    for task in tasks:
        # Strategy 1: Keyword analysis
        deps = find_dependency_keywords(task['name'])

        # Strategy 2: Task ID references
        deps += find_task_references(task['name'], tasks)

        # Strategy 3: Phase ordering
        deps += infer_phase_dependencies(task, tasks)

        # Add dependencies
        for dep_id, reason in deps:
            add_dependency(task['id'], dep_id, reason)
            dependencies_added += 1

    # Save updated tasks
    save_tasks(sprint_id, tasks)

    return dependencies_added
```

**Testing:**
- [ ] Parse sample sprint plan successfully
- [ ] Extract tasks with correct IDs
- [ ] Detect dependencies from keywords
- [ ] Detect dependencies from task references
- [ ] Detect dependencies from phase ordering
- [ ] Handle malformed plans gracefully

---

#### Task 1.4: Add Sprint Plan Parser
**File:** `framework/scripts/roadmap-lib/plan_parser.py` (NEW)
**Estimated:** 8 hours

**Purpose:** Parse markdown sprint plans to extract structured data

**Features:**
- Parse phases from `## Phase N` headings
- Extract tasks from bullet lists
- Identify quality gates
- Extract deliverables
- Parse agent assignments
- Detect task dependencies from description text

**Implementation:**
```python
"""
Sprint Plan Parser

Parses markdown sprint plans into structured data for roadmap system.
"""

import re
from typing import Dict, List
from pathlib import Path


class SprintPlanParser:
    """Parse sprint plan markdown into structured data."""

    def __init__(self, plan_file: Path):
        self.plan_file = plan_file
        self.content = plan_file.read_text()
        self.lines = self.content.split('\n')

    def parse(self) -> Dict:
        """
        Parse complete sprint plan.

        Returns:
            {
                'name': str,
                'goal': str,
                'phases': [{'name': str, 'tasks': [str]}],
                'deliverables': [str],
                'quality_gates': [{'name': str, 'threshold': int}],
                'agents': [str],
            }
        """
        return {
            'name': self._extract_sprint_name(),
            'goal': self._extract_goal(),
            'phases': self._extract_phases(),
            'deliverables': self._extract_deliverables(),
            'quality_gates': self._extract_quality_gates(),
            'agents': self._extract_agents(),
        }

    def _extract_sprint_name(self) -> str:
        """Extract sprint name from # heading."""
        for line in self.lines:
            if line.startswith('# Sprint'):
                return line.replace('# ', '').strip()
        return "Unnamed Sprint"

    def _extract_goal(self) -> str:
        """Extract goal from **Goal:** line."""
        for line in self.lines:
            if line.startswith('**Goal:**'):
                return line.replace('**Goal:**', '').strip()
        return ""

    def _extract_phases(self) -> List[Dict]:
        """Extract phases and their tasks."""
        phases = []
        current_phase = None

        for line in self.lines:
            # Phase heading: ## Phase 1: Name
            if line.startswith('## Phase'):
                if current_phase:
                    phases.append(current_phase)

                phase_name = line.replace('## Phase', '').strip()
                current_phase = {
                    'name': phase_name,
                    'tasks': []
                }

            # Task item: - [ ] Task description
            elif line.strip().startswith('- [ ]') and current_phase:
                task = line.strip().replace('- [ ]', '').strip()
                current_phase['tasks'].append(task)

        # Add last phase
        if current_phase:
            phases.append(current_phase)

        return phases

    def _extract_deliverables(self) -> List[str]:
        """Extract deliverables from list."""
        deliverables = []
        in_deliverables = False

        for line in self.lines:
            if '## Deliverables' in line or '## Expected Outputs' in line:
                in_deliverables = True
                continue

            if in_deliverables:
                if line.startswith('##'):
                    break
                if line.strip().startswith('-'):
                    deliverable = line.strip().replace('-', '').strip()
                    deliverables.append(deliverable)

        return deliverables

    def _extract_quality_gates(self) -> List[Dict]:
        """Extract quality gates with thresholds."""
        gates = []
        in_gates = False

        for line in self.lines:
            if '## Quality Gates' in line:
                in_gates = True
                continue

            if in_gates:
                if line.startswith('##'):
                    break

                # Parse: - Security Audit (85%)
                match = re.match(r'-\s+(.+?)\s+\((\d+)%\)', line.strip())
                if match:
                    gates.append({
                        'name': match.group(1),
                        'threshold': int(match.group(2)),
                        'blocking': True,
                        'status': 'not_run'
                    })

        return gates

    def _extract_agents(self) -> List[str]:
        """Extract recommended agents."""
        agents = []
        in_agents = False

        for line in self.lines:
            if '## Recommended Agents' in line or '## Agents' in line:
                in_agents = True
                continue

            if in_agents:
                if line.startswith('##'):
                    break
                if line.strip().startswith('-'):
                    agent = line.strip().replace('-', '').strip()
                    agents.append(agent)

        return agents
```

**Testing:**
- [ ] Parse sprint name correctly
- [ ] Extract goal/objective
- [ ] Parse multiple phases
- [ ] Extract tasks from bullet lists
- [ ] Parse quality gates with thresholds
- [ ] Extract deliverables
- [ ] Handle missing sections gracefully

---

#### Task 1.5: Integration Testing & Documentation
**Estimated:** 6 hours

**Testing Checklist:**
- [ ] End-to-end test: `/vibey` → `/vibey plan` → verify roadmap created
- [ ] Verify sprint YAML structure matches schema
- [ ] Verify tasks created with correct dependencies
- [ ] Test with multiple sprint plan formats
- [ ] Test error handling (missing plan file, malformed markdown)

**Documentation Updates:**
1. Update `docs/getting-started/QUICK_START.md`
   - Add roadmap initialization step
   - Explain .vibey/ directory structure

2. Update `docs/guides/WORKFLOW_SELECTION_GUIDE.md`
   - Document new sprint planning flow

3. Create `docs/guides/ROADMAP_INTEGRATION.md`
   - Migration guide from legacy to roadmap
   - Comparison table of old vs new commands

---

### Sprint 1 Deliverables

- [x] Roadmap initialization integrated into `/vibey` deployment
- [x] Sprint planning creates roadmap entries (not just legacy state files)
- [x] Tasks extracted from plan and added to roadmap
- [x] Dependencies auto-detected
- [x] Sprint plan parser implemented
- [x] Integration tests passing
- [x] Documentation updated

### Sprint 1 Success Metrics

- Users can run `/vibey plan` and get roadmap sprint created
- `.vibey/` directory structure populated correctly
- Task dependencies detected and visualized with `roadmap deps`
- No breaking changes to existing workflows

---

## Sprint 2: Progress Tracking & Vibey Manager

**Duration:** 2 weeks
**Goal:** Replace all state tracking in /vibey code with roadmap system

### Tasks

#### Task 2.1: Update /vibey code Dashboard
**File:** `framework/commands/vibey-code.md`
**Estimated:** 10 hours

**Changes:**
Replace all `query-sprint-state.py` calls with `roadmap-query.py`

**Specific Updates:**

**Line 21:** Change state file path
```bash
# OLD:
SPRINT_STATE="docs/sprints/sprint-${SPRINT_NUMBER}-state.yaml"

# NEW:
SPRINT_ID="sprint-${SPRINT_NUMBER}"
```

**Line 58:** Dashboard display
```bash
# OLD:
python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" dashboard

# NEW:
python3 .claude/scripts/roadmap-query.py show ${SPRINT_ID} \
  --format dashboard
```

**Line 66:** Current phase
```bash
# OLD:
CURRENT_PHASE=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" current-phase)

# NEW:
CURRENT_TASKS=$(python3 .claude/scripts/roadmap-query.py tasks ${SPRINT_ID} \
  --status in_progress --format list)
```

**Line 72:** Phase list
```bash
# OLD:
python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" list-phases

# NEW:
python3 .claude/scripts/roadmap-query.py tasks ${SPRINT_ID} \
  --group-by phase --format table
```

**Line 76:** Recent activity
```bash
# OLD:
python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" recent-activity

# NEW:
python3 .claude/scripts/roadmap-query.py activity ${SPRINT_ID} \
  --limit 10
```

**Testing:**
- [ ] Dashboard displays correctly
- [ ] Current tasks shown
- [ ] Task grouping by phase works
- [ ] Activity log displays

---

#### Task 2.2: Update /vibey code Progress Tracking
**File:** `framework/commands/vibey-code.md`
**Estimated:** 12 hours

**Changes:**
Replace all `update-sprint-state.py` calls with `roadmap-update.py`

**Specific Updates:**

**Line 252:** Complete phase
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" complete-phase --phase "$PHASE"

# NEW:
# Get all tasks in phase
PHASE_TASKS=$(python3 .claude/scripts/roadmap-query.py tasks ${SPRINT_ID} \
  --phase "${PHASE}" --format ids)

# Mark all as completed
for task_id in $PHASE_TASKS; do
  python3 .claude/scripts/roadmap-update.py \
    --complete-task ${task_id}
done

echo "✓ Phase ${PHASE} completed"
```

**Line 343:** Update task
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" update-task \
  --phase "$PHASE" --task "$TASK" --completed

# NEW:
python3 .claude/scripts/roadmap-update.py \
  --complete-task ${TASK_ID}
```

**Line 370:** Log agent
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" log-agent \
  --phase "$PHASE" --agent "$AGENT" --status completed

# NEW:
python3 .claude/scripts/roadmap-update.py \
  --action "log_activity" \
  --sprint-id ${SPRINT_ID} \
  --type "agent_run" \
  --agent "${AGENT}" \
  --status "completed"
```

**Line 438:** Pause sprint
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" pause-sprint

# NEW:
python3 .claude/scripts/roadmap-update.py \
  --action "update_sprint" \
  --sprint-id ${SPRINT_ID} \
  --status "paused"
```

**Line 493:** Complete sprint
```bash
# OLD:
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" complete-sprint

# NEW:
python3 .claude/scripts/roadmap-update.py \
  --action "complete_sprint" \
  --sprint-id ${SPRINT_ID}
```

**Testing:**
- [ ] Task completion updates roadmap
- [ ] Agent activity logged
- [ ] Sprint pause/resume works
- [ ] Sprint completion triggers version bump

---

#### Task 2.3: Extend Vibey Manager Agent
**File:** `framework/agents/core/vibey-manager.md`
**Estimated:** 8 hours

**New Section (Add after line 320):**

```markdown
## Roadmap Management Commands

The Vibey Manager can now manage multi-sprint roadmaps.

### View Roadmap Status

**Display overall roadmap:**
```bash
python3 .claude/scripts/roadmap status
```

**Show specific track:**
```bash
python3 .claude/scripts/roadmap show track main --with-sprints
```

**Show sprint details:**
```bash
python3 .claude/scripts/roadmap show sprint-1 --with-tasks
```

### Dependency Management

**View dependencies:**
```bash
# Show all dependencies
python3 .claude/scripts/roadmap deps

# Sprint dependencies
python3 .claude/scripts/roadmap deps sprint-2

# Task dependencies
python3 .claude/scripts/roadmap deps sprint-2-task-003
```

**Visualize dependency graph:**
```bash
python3 .claude/scripts/roadmap deps --graph
```

### Track Management

**Create new track:**
```bash
python3 .claude/scripts/roadmap-update.py \
  --action "create_track" \
  --track-id "frontend" \
  --name "Frontend Development" \
  --goal "Build user-facing components"
```

**List all tracks:**
```bash
python3 .claude/scripts/roadmap list tracks
```

### Agent Workload

**View agent assignments:**
```bash
python3 .claude/scripts/roadmap agents --workload
```

**Output:**
```
Agent Workload
==============

web-developer:
  - sprint-1-task-002 (in_progress)
  - sprint-2-task-001 (not_started)
  Total: 2 tasks

docs-writer:
  - sprint-1-task-004 (completed)
  Total: 1 task
```

### Advanced Queries

**Find blocked tasks:**
```bash
python3 .claude/scripts/roadmap find --blocked
```

**Find tasks by agent:**
```bash
python3 .claude/scripts/roadmap find --agent web-developer
```

**Progress report:**
```bash
python3 .claude/scripts/roadmap progress --track main
```

---

## Roadmap Command Reference

### Query Commands

| Command | Description | Example |
|---------|-------------|---------|
| `roadmap status` | Overall roadmap status | `roadmap status` |
| `roadmap show <type> <id>` | Show specific object | `roadmap show sprint sprint-1` |
| `roadmap list <type>` | List objects | `roadmap list tasks --sprint sprint-1` |
| `roadmap deps <id>` | Show dependencies | `roadmap deps sprint-2` |
| `roadmap find <criteria>` | Find objects | `roadmap find --blocked` |
| `roadmap agents` | Agent assignments | `roadmap agents --workload` |
| `roadmap progress` | Progress report | `roadmap progress --track main` |

### Update Commands

| Command | Description | Example |
|---------|-------------|---------|
| `roadmap-update.py --action create_track` | Create track | See above |
| `roadmap-update.py --action create_sprint` | Create sprint | See above |
| `roadmap-update.py --complete-task <id>` | Complete task | `--complete-task sprint-1-task-002` |
| `roadmap-update.py --action log_activity` | Log activity | See above |

### Context Commands

| Command | Description | Example |
|---------|-------------|---------|
| `roadmap-prepare.py <task-id>` | Prepare task context | `roadmap-prepare.py sprint-1-task-003` |
| `roadmap-context.py <task-id>` | Load task context | `roadmap-context.py sprint-1-task-003` |
| `roadmap-summarize.py <sprint-id>` | Summarize sprint | `roadmap-summarize.py sprint-1` |
```

**Testing:**
- [ ] All roadmap commands documented
- [ ] Examples work correctly
- [ ] Vibey Manager can execute roadmap operations

---

#### Task 2.4: Add Quality Gate Integration
**File:** `framework/scripts/roadmap-update.py`
**Estimated:** 6 hours

**New Action:**
```python
def update_quality_gate(sprint_id, gate_name, status, score=None, issues=None):
    """
    Update quality gate status.

    Args:
        sprint_id: Sprint identifier
        gate_name: Gate name (e.g., "Security Audit")
        status: "not_run" | "running" | "passed" | "failed"
        score: Optional score (0-100)
        issues: Optional list of issues found
    """
    sprint = load_sprint(sprint_id)

    # Find gate
    for gate in sprint['quality_gates']:
        if gate['name'] == gate_name:
            gate['status'] = status
            gate['checked_at'] = datetime.now(timezone.utc).isoformat()

            if score is not None:
                gate['score'] = score

            if issues:
                gate['issues'] = issues

            # Check if passed
            if score and gate['threshold']:
                gate['passed'] = score >= gate['threshold']

            break

    # Save updated sprint
    save_sprint(sprint)

    # Log activity
    log_activity(sprint_id, 'quality_gate_updated', {
        'gate': gate_name,
        'status': status,
        'score': score
    })
```

**Integration in vibey-code.md (Line 207):**
```bash
# Check quality gates
python3 .claude/scripts/roadmap-query.py gates ${SPRINT_ID}

# Update gate
python3 .claude/scripts/roadmap-update.py \
  --action "update_quality_gate" \
  --sprint-id ${SPRINT_ID} \
  --gate "Security Audit" \
  --status "passed" \
  --score 92
```

**Testing:**
- [ ] Quality gates display correctly
- [ ] Gates can be updated
- [ ] Blocking gates prevent sprint completion
- [ ] Score comparison works

---

#### Task 2.5: Integration Testing & Documentation
**Estimated:** 6 hours

**Testing Checklist:**
- [ ] Complete workflow test: plan → code → update tasks → complete sprint
- [ ] Verify roadmap state updated correctly throughout
- [ ] Test all /vibey code menu options with roadmap
- [ ] Test quality gate blocking behavior
- [ ] Test multi-sprint scenario (sprint 1 complete, sprint 2 active)

**Documentation Updates:**
1. Update `docs/guides/ORCHESTRATION.md`
   - Add roadmap-aware orchestration patterns

2. Create `docs/reference/ROADMAP_CLI.md`
   - Complete CLI reference for roadmap commands

3. Update `README.md`
   - Update feature list to highlight roadmap integration

---

### Sprint 2 Deliverables

- [x] `/vibey code` uses roadmap for all state operations
- [x] Task progress tracked in roadmap system
- [x] Quality gates integrated
- [x] Vibey Manager extended with roadmap commands
- [x] Agent workload tracking functional
- [x] Integration tests passing
- [x] CLI documentation complete

### Sprint 2 Success Metrics

- Users can track progress exclusively through roadmap
- Quality gates block sprint completion when failing
- Agent workload visible across sprints
- Dependency tracking works in /vibey code
- No regression in user experience

---

## Sprint 3: Migration & Deprecation

**Duration:** 2 weeks
**Goal:** Provide migration path, deprecate legacy scripts, clean up code

### Tasks

#### Task 3.1: Create Migration Script
**File:** `framework/scripts/migrate-to-roadmap.py` (NEW)
**Estimated:** 12 hours

**Purpose:** Convert legacy sprint-state files to roadmap format

**Features:**
- Detect legacy sprint state files
- Parse state YAML structure
- Create equivalent roadmap entries
- Preserve all data (tasks, agents, quality gates, activity)
- Generate migration report

**Implementation:**
```python
#!/usr/bin/env python3
"""
Migrate Legacy Sprint State to Roadmap System

Converts docs/sprints/*.yaml files to .vibey/ roadmap structure.
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List


class LegacyMigrator:
    """Migrate legacy sprint state to roadmap."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.legacy_dir = root_dir / "docs" / "sprints"
        self.roadmap_dir = root_dir / ".vibey"

        self.migrated = []
        self.errors = []

    def detect_legacy_state(self) -> List[Path]:
        """Find legacy sprint state files."""
        if not self.legacy_dir.exists():
            return []

        return list(self.legacy_dir.glob("sprint-*-state.yaml"))

    def migrate_all(self):
        """Migrate all legacy state files."""
        state_files = self.detect_legacy_state()

        if not state_files:
            print("✓ No legacy state files found")
            return

        print(f"Found {len(state_files)} legacy sprint state files\n")

        # Initialize roadmap if needed
        if not (self.roadmap_dir / "roadmap.yaml").exists():
            print("Initializing roadmap system...")
            self._initialize_roadmap()

        # Migrate each sprint
        for state_file in state_files:
            try:
                self._migrate_sprint(state_file)
                self.migrated.append(state_file)
            except Exception as e:
                self.errors.append((state_file, str(e)))

        # Print report
        self._print_report()

    def _migrate_sprint(self, state_file: Path):
        """Migrate single sprint state file."""
        print(f"Migrating {state_file.name}...")

        # Load legacy state
        with open(state_file) as f:
            legacy = yaml.safe_load(f)

        sprint_data = legacy['sprint']
        sprint_number = sprint_data['number']
        sprint_id = f"sprint-{sprint_number}"

        # Create sprint entry
        sprint = {
            'id': sprint_id,
            'track_id': 'main',
            'name': sprint_data['name'],
            'status': sprint_data['status'],
            'plan_file': sprint_data.get('plan_file'),
            'started': sprint_data.get('started'),
            'completed': sprint_data.get('completed'),
            'paused': sprint_data.get('paused'),
            'quality_gates': self._migrate_quality_gates(legacy),
            'deliverables': [],
            'dependencies': [],
            'blocks': [],
            'created': legacy['metadata'].get('created_at'),
            'metadata': {
                'migrated_from': str(state_file),
                'migrated_at': datetime.now(timezone.utc).isoformat(),
            }
        }

        # Save sprint
        sprint_file = self.roadmap_dir / "sprints" / f"{sprint_id}.yaml"
        sprint_file.parent.mkdir(parents=True, exist_ok=True)

        with open(sprint_file, 'w') as f:
            yaml.dump({'sprint': sprint}, f, default_flow_style=False, sort_keys=False)

        # Create tasks
        tasks = self._migrate_tasks(sprint_id, legacy)

        # Save tasks
        tasks_file = self.roadmap_dir / "tasks" / f"{sprint_id}-tasks.yaml"
        tasks_file.parent.mkdir(parents=True, exist_ok=True)

        with open(tasks_file, 'w') as f:
            yaml.dump({'tasks': tasks}, f, default_flow_style=False, sort_keys=False)

        # Migrate activity log
        self._migrate_activity(sprint_id, legacy)

        print(f"  ✓ Created {sprint_id}.yaml")
        print(f"  ✓ Created {len(tasks)} tasks")

    def _migrate_tasks(self, sprint_id: str, legacy: Dict) -> List[Dict]:
        """Extract tasks from legacy phases."""
        tasks = []
        task_counter = 1

        for phase in legacy.get('phases', []):
            phase_name = phase['name']

            for task_item in phase.get('tasks', []):
                task_id = f"{sprint_id}-task-{task_counter:03d}"

                task = {
                    'id': task_id,
                    'sprint_id': sprint_id,
                    'name': task_item['description'],
                    'phase': phase_name,
                    'status': 'completed' if task_item['completed'] else 'not_started',
                    'completed_at': task_item.get('completed_at'),
                    'dependencies': [],
                    'assigned_agents': [],
                }

                tasks.append(task)
                task_counter += 1

        return tasks

    def _migrate_quality_gates(self, legacy: Dict) -> List[Dict]:
        """Migrate quality gates."""
        gates = []

        for phase in legacy.get('phases', []):
            for gate in phase.get('quality_gates', []):
                gates.append({
                    'name': gate['name'],
                    'status': gate['status'],
                    'score': gate.get('score'),
                    'threshold': gate['threshold'],
                    'blocking': gate['blocking'],
                    'checked_at': gate.get('checked_at'),
                    'issues': gate.get('issues', []),
                })

        return gates

    def _migrate_activity(self, sprint_id: str, legacy: Dict):
        """Migrate activity log to roadmap."""
        # Activity will be stored in sprint YAML
        # (Implementation depends on roadmap activity log structure)
        pass

    def _initialize_roadmap(self):
        """Initialize roadmap structure if needed."""
        # Create minimal roadmap.yaml
        roadmap = {
            'roadmap': {
                'id': 'main-roadmap',
                'name': 'Project Roadmap',
                'version': '0.1.0',
                'status': 'active',
                'created': datetime.now(timezone.utc).isoformat(),
            },
            'tracks': [
                {
                    'id': 'main',
                    'name': 'Main Development Track',
                    'status': 'active',
                }
            ],
        }

        roadmap_file = self.roadmap_dir / "roadmap.yaml"
        roadmap_file.parent.mkdir(parents=True, exist_ok=True)

        with open(roadmap_file, 'w') as f:
            yaml.dump(roadmap, f, default_flow_style=False, sort_keys=False)

        # Create main track
        track = {
            'track': {
                'id': 'main',
                'name': 'Main Development Track',
                'status': 'active',
                'sprints': [],
                'created': datetime.now(timezone.utc).isoformat(),
            }
        }

        track_file = self.roadmap_dir / "tracks" / "main.yaml"
        track_file.parent.mkdir(parents=True, exist_ok=True)

        with open(track_file, 'w') as f:
            yaml.dump(track, f, default_flow_style=False, sort_keys=False)

    def _print_report(self):
        """Print migration report."""
        print("\n" + "=" * 60)
        print("MIGRATION REPORT")
        print("=" * 60)

        print(f"\n✅ Successfully migrated: {len(self.migrated)} sprint(s)")
        for state_file in self.migrated:
            print(f"  - {state_file.name}")

        if self.errors:
            print(f"\n❌ Failed to migrate: {len(self.errors)} sprint(s)")
            for state_file, error in self.errors:
                print(f"  - {state_file.name}: {error}")

        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("1. Verify migrated data:")
        print("   ./framework/scripts/roadmap status")
        print("\n2. Review sprint details:")
        print("   ./framework/scripts/roadmap show sprint-1")
        print("\n3. Archive legacy files:")
        print("   mv docs/sprints/*-state.yaml docs/archive/legacy/")
        print("\n4. Update /vibey commands to use roadmap exclusively")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy sprint state to roadmap system"
    )
    parser.add_argument(
        '--root',
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be migrated without making changes"
    )

    args = parser.parse_args()

    migrator = LegacyMigrator(args.root)

    if args.dry_run:
        state_files = migrator.detect_legacy_state()
        print(f"Would migrate {len(state_files)} sprint state files:")
        for f in state_files:
            print(f"  - {f}")
    else:
        migrator.migrate_all()


if __name__ == '__main__':
    main()
```

**Testing:**
- [ ] Detect legacy state files correctly
- [ ] Migrate sprint metadata
- [ ] Migrate tasks with completion status
- [ ] Migrate quality gates
- [ ] Generate accurate report
- [ ] Dry-run mode works

---

#### Task 3.2: Add Migration Command to /vibey
**File:** `framework/commands/vibey-manage.md`
**Estimated:** 4 hours

**Add Migration Option:**
```markdown
## Option 7: Migrate to Roadmap System

**When to use:**
- You have legacy sprint state files (docs/sprints/*-state.yaml)
- You want to leverage roadmap features (dependency tracking, multi-sprint)

**How it works:**
```bash
echo "🔄 Migrating legacy sprint state to roadmap..."

# Check for legacy state
LEGACY_COUNT=$(find docs/sprints -name "*-state.yaml" 2>/dev/null | wc -l)

if [ "$LEGACY_COUNT" -eq 0 ]; then
    echo "✓ No legacy state files found. Already using roadmap system!"
    exit 0
fi

echo "Found $LEGACY_COUNT legacy sprint state file(s)"
echo ""

# Show preview
python3 .claude/scripts/migrate-to-roadmap.py --dry-run

echo ""
echo "Proceed with migration? (y/n)"
read -r response

if [ "$response" = "y" ]; then
    # Run migration
    python3 .claude/scripts/migrate-to-roadmap.py

    echo ""
    echo "✅ Migration complete!"
    echo ""
    echo "Next steps:"
    echo "1. Verify migrated data: ./framework/scripts/roadmap status"
    echo "2. Archive legacy files: mkdir -p docs/archive/legacy && mv docs/sprints/*-state.yaml docs/archive/legacy/"
    echo "3. Continue using /vibey commands (now powered by roadmap)"
else
    echo "Migration cancelled"
fi
```

**Testing:**
- [ ] Migration option appears in menu
- [ ] Dry-run preview shows correctly
- [ ] Migration executes successfully
- [ ] User guidance clear

---

#### Task 3.3: Deprecate Legacy Scripts
**Estimated:** 6 hours

**Steps:**
1. Add deprecation warnings to legacy scripts
2. Update script headers with deprecation notice
3. Create deprecation guide document
4. Remove legacy scripts from future framework deployments

**Deprecation Warning (Add to each script):**
```python
#!/usr/bin/env python3
"""
DEPRECATED: This script is deprecated as of v2.0.0

Use the roadmap system instead:
  - create-sprint-state.py → roadmap-update.py --action create_sprint
  - update-sprint-state.py → roadmap-update.py --action progress_task
  - query-sprint-state.py  → roadmap-query.py show

Migration guide: docs/guides/LEGACY_TO_ROADMAP.md

This script will be removed in v3.0.0 (Q2 2025).
"""

import sys
import warnings

warnings.warn(
    "This script is deprecated. Use roadmap system instead. "
    "See docs/guides/LEGACY_TO_ROADMAP.md",
    DeprecationWarning,
    stacklevel=2
)

# Existing script code...
```

**Create Deprecation Guide:**
`docs/guides/LEGACY_TO_ROADMAP.md`

```markdown
# Legacy Sprint State → Roadmap System Migration Guide

## Overview

The legacy sprint state system (`docs/sprints/*.yaml` + Python scripts) has been deprecated in favor of the roadmap system (`.vibey/`).

## Why Migrate?

**Roadmap System Benefits:**
- ✅ Multi-sprint dependency tracking
- ✅ Cross-sprint blockers
- ✅ Advanced progress visualization
- ✅ Better agent workload management
- ✅ Track-level organization
- ✅ Automated dependency detection
- ✅ Better context loading for agents

## Migration Path

### Option 1: Automatic Migration (Recommended)

For existing projects with legacy state files:

1. Run migration command:
   ```bash
   /vibey manage
   # Choose Option 7: Migrate to Roadmap System
   ```

2. Verify migration:
   ```bash
   ./framework/scripts/roadmap status
   ```

3. Archive legacy files:
   ```bash
   mkdir -p docs/archive/legacy
   mv docs/sprints/*-state.yaml docs/archive/legacy/
   ```

4. Continue using `/vibey` commands (now roadmap-powered)

### Option 2: Fresh Start

For new projects or projects without legacy state:

1. Deploy framework:
   ```bash
   /vibey
   ```

2. Roadmap automatically initialized during deployment

3. Use `/vibey plan` to create sprints (roadmap-powered by default)

## Command Mapping

| Legacy Command | Roadmap Equivalent | Notes |
|----------------|-------------------|-------|
| `create-sprint-state.py` | `roadmap-update.py --action create_sprint` | Automatic in `/vibey plan` |
| `update-sprint-state.py update-task` | `roadmap-update.py --complete-task` | Automatic in `/vibey code` |
| `update-sprint-state.py log-agent` | `roadmap-update.py --action log_activity` | Automatic in `/vibey code` |
| `query-sprint-state.py dashboard` | `roadmap-query.py show <sprint-id>` | Automatic in `/vibey code` |
| `query-sprint-state.py current-phase` | `roadmap-query.py tasks <sprint-id> --status in_progress` | Automatic |

## Breaking Changes

None! The `/vibey` commands work the same way. The only difference is the underlying system.

## Timeline

- **v2.0.0 (Jan 2025):** Roadmap system integrated, legacy deprecated
- **v2.5.0 (Feb 2025):** Legacy scripts show deprecation warnings
- **v3.0.0 (Q2 2025):** Legacy scripts removed entirely

## Troubleshooting

**Q: Can I still use legacy scripts?**
A: Yes, until v3.0.0. But you'll see deprecation warnings.

**Q: Will my existing sprints work?**
A: Yes! Use the migration tool to convert them to roadmap format.

**Q: What if migration fails?**
A: Legacy files are not deleted. You can continue using them or contact support.

## Support

Questions? Open an issue: https://github.com/your-org/vibey/issues
```

---

#### Task 3.4: Clean Up Code & Documentation
**Estimated:** 8 hours

**Code Cleanup:**
1. Remove legacy script references from new framework deployments
2. Update `.gitignore` to ignore legacy state files
3. Clean up documentation references to old system
4. Update examples to use roadmap

**Files to Update:**

1. **`.gitignore`**
   ```
   # Legacy sprint state (deprecated)
   docs/sprints/*-state.yaml
   ```

2. **`framework/commands/vibey.md`** (Deployment section)
   - Remove copying of deprecated scripts to .claude/scripts/

3. **`docs/getting-started/USER_JOURNEY.md`**
   - Update all examples to show roadmap usage
   - Remove references to legacy state files

4. **`docs/guides/WORKFLOW_SELECTION_GUIDE.md`**
   - Update sprint planning workflow
   - Show roadmap integration

5. **`README.md`**
   - Update feature list
   - Highlight roadmap capabilities

---

#### Task 3.5: Final Testing & Release
**Estimated:** 8 hours

**Complete Test Suite:**

1. **Fresh Project Test**
   - [ ] Deploy framework on new project
   - [ ] Verify roadmap initialized
   - [ ] Run /vibey plan, verify sprint created
   - [ ] Run /vibey code, verify dashboard works
   - [ ] Complete tasks, verify progress tracked
   - [ ] Complete sprint, verify status updated

2. **Migration Test**
   - [ ] Create legacy state file
   - [ ] Run migration
   - [ ] Verify all data migrated
   - [ ] Verify /vibey commands work with migrated data

3. **Multi-Sprint Test**
   - [ ] Create sprint 1, complete it
   - [ ] Create sprint 2 with dependency on sprint 1
   - [ ] Verify dependency tracking works
   - [ ] Verify blocked status when sprint 1 incomplete

4. **Quality Gate Test**
   - [ ] Create sprint with quality gates
   - [ ] Run quality check, update gate
   - [ ] Verify blocking gate prevents completion
   - [ ] Pass gate, verify sprint can complete

5. **Regression Test**
   - [ ] All existing /vibey workflows still work
   - [ ] No breaking changes to user experience
   - [ ] Framework deployment successful
   - [ ] CLAUDE.md generation works

**Release Checklist:**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Migration guide published
- [ ] Deprecation warnings added
- [ ] CHANGELOG.md updated
- [ ] Version bumped to 2.0.0
- [ ] Git tag created
- [ ] Release notes published

---

### Sprint 3 Deliverables

- [x] Migration script functional
- [x] Migration command added to /vibey
- [x] Legacy scripts deprecated with warnings
- [x] Deprecation guide published
- [x] Code cleanup complete
- [x] Documentation updated
- [x] All tests passing
- [x] Release v2.0.0 published

### Sprint 3 Success Metrics

- Existing projects can migrate seamlessly
- New projects use roadmap by default
- No breaking changes to /vibey commands
- Documentation clear and complete
- Legacy code removed from new deployments
- ~1,657 lines of duplicate code deprecated

---

## Risk Analysis & Mitigation

### High Risks

**1. Breaking Changes to User Workflows**

**Risk:** Users have muscle memory with /vibey commands. Changes might confuse them.

**Mitigation:**
- Preserve command structure exactly
- Keep same menu options
- Update backend only, not frontend
- Provide clear migration messaging

**2. Data Loss During Migration**

**Risk:** Migration script could corrupt or lose sprint data.

**Mitigation:**
- Never delete legacy files (archive only)
- Dry-run mode for preview
- Comprehensive testing
- Backup recommendation in docs

**3. Incomplete Feature Parity**

**Risk:** Roadmap system missing features from legacy.

**Mitigation:**
- Feature comparison matrix (created in planning)
- Test all legacy features in roadmap
- User acceptance testing

### Medium Risks

**4. Performance Degradation**

**Risk:** Roadmap queries slower than legacy.

**Mitigation:**
- Use RoadmapCache (already optimized)
- Disk caching enabled
- Performance testing

**5. Complex Dependency Detection**

**Risk:** Auto-detection creates wrong dependencies.

**Mitigation:**
- Conservative algorithm (only obvious dependencies)
- Manual override capability
- Clear dependency visualization

### Low Risks

**6. Documentation Gaps**

**Risk:** Users confused by new system.

**Mitigation:**
- Comprehensive migration guide
- Updated quick start
- CLI reference
- Example workflows

---

## Dependencies & Blockers

### External Dependencies

- None! All work internal to Vibey framework.

### Internal Dependencies

**Sprint 1 depends on:**
- Existing roadmap system (COMPLETED ✅)
- RoadmapCache implementation (COMPLETED ✅)

**Sprint 2 depends on:**
- Sprint 1 completion
- roadmap-query.py (exists)
- roadmap-update.py (exists, needs extensions)

**Sprint 3 depends on:**
- Sprint 1 + 2 completion

### Potential Blockers

**User Feedback:**
- If users report confusion, pause for additional documentation
- If migration fails for edge cases, fix before proceeding

**Technical Issues:**
- If dependency detection too complex, simplify or make manual
- If performance problems, optimize before Sprint 3

---

## Success Metrics

### Quantitative

- [x] 100% of /vibey commands use roadmap system
- [x] 0 breaking changes to user workflows
- [x] 3 legacy scripts deprecated (~1,657 lines)
- [x] Migration success rate >95%
- [x] Test coverage >90%

### Qualitative

- [x] Users can create multi-sprint roadmaps
- [x] Dependency tracking intuitive and useful
- [x] Migration process smooth and documented
- [x] Documentation clear and comprehensive
- [x] No user complaints about breaking changes

### Adoption Metrics (Post-Release)

- Percentage of new projects using roadmap (target: 100%)
- Percentage of legacy projects migrated (target: >50% within 1 month)
- User satisfaction with roadmap features (target: >90% positive)

---

## Timeline & Milestones

### Week 1-2: Sprint 1
- [ ] Day 1-2: Task 1.1 (Update deployment)
- [ ] Day 3-5: Task 1.2 (Update planning)
- [ ] Day 6-8: Task 1.3 (Create actions)
- [ ] Day 9-10: Task 1.4 (Plan parser)
- [ ] Day 11-12: Task 1.5 (Testing & docs)
- [ ] **Milestone:** Sprint planning creates roadmap entries

### Week 3-4: Sprint 2
- [ ] Day 13-15: Task 2.1 (Update dashboard)
- [ ] Day 16-19: Task 2.2 (Update tracking)
- [ ] Day 20-22: Task 2.3 (Vibey Manager)
- [ ] Day 23-24: Task 2.4 (Quality gates)
- [ ] Day 25-26: Task 2.5 (Testing & docs)
- [ ] **Milestone:** Progress tracking uses roadmap exclusively

### Week 5-6: Sprint 3
- [ ] Day 27-30: Task 3.1 (Migration script)
- [ ] Day 31-32: Task 3.2 (Migration command)
- [ ] Day 33-34: Task 3.3 (Deprecation)
- [ ] Day 35-37: Task 3.4 (Cleanup)
- [ ] Day 38-42: Task 3.5 (Final testing & release)
- [ ] **Milestone:** Release v2.0.0 with roadmap integration

---

## Post-Integration Roadmap

**After roadmap-integration track completes:**

1. **Core Framework Track** (Resume)
   - Sprint 1: Default CLAUDE.md Auto-Generation
   - Sprint 2: Config-to-Docs Architecture
   - Foundation for multi-platform

2. **Goose Port Track** (Unblocked!)
   - Now possible with unified roadmap system
   - Port workflows → recipes
   - Port agents → extensions

3. **Multi-Platform Track**
   - Build on roadmap + core framework
   - Platform adapters
   - Unified CLI

---

## Appendix: Command Reference

### Legacy Commands (Deprecated)

```bash
# Sprint creation (deprecated)
python3 .claude/scripts/create-sprint-state.py \
  --plan-file "docs/sprints/sprint-1-plan.md" \
  --output "docs/sprints/sprint-1-state.yaml"

# Task update (deprecated)
python3 .claude/scripts/update-sprint-state.py \
  --state "docs/sprints/sprint-1-state.yaml" \
  update-task --phase "Phase 1" --task "Task 1" --completed

# Dashboard (deprecated)
python3 .claude/scripts/query-sprint-state.py \
  --state "docs/sprints/sprint-1-state.yaml" dashboard
```

### Roadmap Commands (Current)

```bash
# Sprint creation
python3 .claude/scripts/roadmap-update.py \
  --action "create_sprint" \
  --track-id "main" \
  --sprint-id "sprint-1" \
  --name "Sprint 1: Feature Development"

# Task update
python3 .claude/scripts/roadmap-update.py \
  --complete-task sprint-1-task-002

# Dashboard
python3 .claude/scripts/roadmap-query.py show sprint-1 --format dashboard
```

---

## Conclusion

This plan provides a clear, methodical path to integrate the roadmap system into /vibey commands while maintaining backward compatibility and providing a smooth migration experience.

**Key Principles:**
1. **Preserve UX** - /vibey commands work the same
2. **Additive Changes** - Build on top, don't break
3. **Clear Migration** - Easy path for existing users
4. **Clean Deprecation** - Remove old code responsibly

**Expected Outcome:**
- Unified state management (eliminate duplication)
- Multi-sprint dependency tracking for all users
- Foundation for Goose port and multi-platform
- Technical debt eliminated

**Ready to Start:** This plan is comprehensive, detailed, and ready for execution.
