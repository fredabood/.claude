# Progress Tracking Guide

> **Note:** This guide references deprecated `/vibey` slash commands. Use the CLI equivalents:
> - `/vibey code` → `vibey roadmap status`
> - Task management → `vibey roadmap start/complete <task-id>`

**Version:** 1.0.0
**Last Updated:** November 8, 2025
**Applies To:** Vibey Framework v1.2.0+

---

## Overview

Vibey's progress tracking system provides real-time visibility into sprint execution, task status, and team productivity. Integrated with the roadmap system, it automatically tracks progress, visualizes completion, and recommends next steps.

**Key Features:**
- Real-time dashboard with live progress updates
- Conversational task management (start, complete, view)
- Visual progress bars and completion tracking
- Smart task recommendations
- Quality gate monitoring
- Agent workload visibility

---

## Quick Start

### Viewing Progress

Run `/vibey code` to see your sprint execution dashboard:

```markdown
# 🚀 Sprint Execution Dashboard

**Current Sprint:** Sprint 2 - Progress Tracking & Vibey Manager
**Status:** in_progress
**Started:** 2025-11-08

---

## 📊 Sprint Progress

**Task Progress:** 4/6 completed (67%)

Progress Bar: [██████░░░░]

**Task Status:**
- ✅ Completed: 4
- 🔄 In Progress: 0
- ⏸️  Not Started: 2
```

### Starting a Task

From the dashboard, select **Option 2: Start a task**:

```
Available tasks:

1. Add real-time progress visualization (suggested: web-developer)
   Create automatic progress updates after task operations
   ID: roadmap-integration-2-task-004

2. Create integration tests (suggested: test-engineer)
   Test progress tracking functionality
   ID: roadmap-integration-2-task-005

Which task would you like to start?
```

Select a task by number or ID, and it's automatically marked in progress.

### Completing a Task

Select **Option 3: Complete current task**:

```
Currently in progress:

🔄 Add real-time progress visualization
   ID: roadmap-integration-2-task-004

Which task have you completed?
```

After completion, you'll see an automatic progress update:

```
✅ Task completed: roadmap-integration-2-task-004

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Updated Progress:
- Completed: 5/6 tasks (83%)
- Progress: [████████░░]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Next recommended task: Create integration tests
   ID: roadmap-integration-2-task-005
   Estimated: 5 hours
```

---

## Dashboard Components

### 1. Sprint Progress Section

Shows overall sprint completion:

```markdown
## 📊 Sprint Progress

**Task Progress:** 4/6 completed (67%)

Progress Bar: [██████░░░░]

**Task Status:**
- ✅ Completed: 4
- 🔄 In Progress: 1
- ⏸️  Not Started: 1
```

**Data Source:** `.vibey/sprints/<sprint-id>.yaml`

**How it works:**
- Reads sprint progress from roadmap system
- Calculates completion percentage
- Renders visual progress bar (10 segments)
- Groups tasks by status

### 2. Quality Gates Summary

Displays quality gate status:

```markdown
**Quality Gates:**
- ✅ Unit Testing (90%) - Threshold: 80%
- ⏸️  Security Audit - Threshold: 85%
- ⏸️  Code Review - Threshold: 100%
```

**Gate States:**
- ✅ **Passed** - Gate met or exceeded threshold
- ❌ **Failed** - Below threshold (blocks completion)
- ⏸️  **Not Run** - Not yet executed

**Data Source:** `sprint.quality_gates` in sprint YAML

### 3. Current Tasks

Lists tasks by phase or priority:

```markdown
## 📋 Current Tasks

**In Progress (1):**
- 🔄 Add real-time progress visualization (web-developer)

**Not Started (1):**
- ⏸️  Create integration tests (test-engineer)
```

**Data Source:** `.vibey/tasks/<sprint-id>-tasks.yaml`

### 4. Recent Activity

Shows recently completed tasks:

```markdown
## 📝 Recent Activity

- ✅ Extend Vibey Manager with roadmap commands (2 hours ago)
- ✅ Implement task status updates (4 hours ago)
- ✅ Update /vibey code dashboard (6 hours ago)
```

**Data Source:** Task completion timestamps

---

## Task Management

### Starting Tasks

**Command:** Dashboard Option 2

**Process:**
1. View all `not_started` tasks for the sprint
2. Select task by number or ID
3. Task automatically marked as `in_progress`
4. Progress display updates

**Example:**
```bash
# User selects task 1 or provides task ID
Input: 1
or
Input: roadmap-integration-2-task-004

# System response
✅ Task started: roadmap-integration-2-task-004

📊 Updated Progress:
- In Progress: 1 task
- Progress: [████░░░░░░]

💡 Continue working on: Add real-time progress visualization
```

**Behind the scenes:**
```bash
python3 .claude/scripts/roadmap start "roadmap-integration-2-task-004"
```

### Completing Tasks

**Command:** Dashboard Option 3

**Process:**
1. View all `in_progress` tasks
2. Select completed task
3. Task marked as `completed`
4. Sprint progress recalculated
5. Next task recommended

**Automatic Actions:**
- Progress percentage updated
- Completion count incremented
- Next high-priority task identified
- Sprint completion detected (if all tasks done)

**Example:**
```bash
# Complete a task
Input: roadmap-integration-2-task-004

# System response
✅ Task completed: roadmap-integration-2-task-004

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Updated Progress:
- Completed: 5/6 tasks (83%)
- Progress: [████████░░]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Next recommended task: Create integration tests
   ID: roadmap-integration-2-task-005
   Estimated: 5 hours
```

### Viewing All Tasks

**Command:** Dashboard Option 4

**Output:**
```markdown
## 📋 All Sprint Tasks

### ✅ Completed (4)

**Update /vibey code dashboard** (ID: roadmap-integration-2-task-001)
- Status: completed
- Estimated: 6 hours
- Agents: web-developer

**Implement task status updates** (ID: roadmap-integration-2-task-002)
- Status: completed
- Estimated: 4 hours
- Agents: web-developer

### ⏸️ Not Started (2)

**Create integration tests** (ID: roadmap-integration-2-task-005)
- Status: not_started
- Priority: high
- Estimated: 5 hours
- Agents: test-engineer
```

---

## Real-Time Progress Visualization

### Auto-Update Function

After any task status change, the dashboard automatically refreshes:

**Function:** `update_progress_display()`

**Triggers:**
- Starting a task (Option 2)
- Completing a task (Option 3)
- Marking phase complete (Option 6)

**Display Format:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Updated Progress:
- Completed: 3/6 tasks (50%)
- Progress: [█████░░░░░]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Next recommended task: Extend Vibey Manager
   ID: roadmap-integration-2-task-003
   Estimated: 6 hours
```

### Progress Bar

**Rendering:**
- 10 segments total
- Filled segments: `█` (dark block)
- Empty segments: `░` (light block)

**Calculation:**
```python
completion_percent = (tasks_completed / tasks_total) * 100
filled = int(completion_percent / 10)
empty = 10 - filled
bar = "█" * filled + "░" * empty
```

**Examples:**
```
  0% - [░░░░░░░░░░]
 25% - [██░░░░░░░░]
 50% - [█████░░░░░]
 75% - [███████░░░]
100% - [██████████]
```

### Next Task Recommendation

**Logic:**
1. Get all `not_started` tasks for sprint
2. Filter by unblocked (no pending dependencies)
3. Sort by priority (high > medium > low)
4. Return highest-priority unblocked task

**Command:**
```bash
python3 .claude/scripts/roadmap recommend --limit 1
```

**Output:**
```
💡 Next recommended task: Create integration tests
   ID: roadmap-integration-2-task-005
   Estimated: 5 hours
```

---

## Quality Gates

### Gate Configuration

Quality gates are defined in sprint YAML:

```yaml
quality_gates:
  - name: "Unit Testing"
    threshold: 80
    blocking: true
    status: "not_run"
    score: null

  - name: "Security Audit"
    threshold: 85
    blocking: true
    status: "not_run"
    score: null
```

**Fields:**
- `name` - Gate identifier
- `threshold` - Minimum passing score (0-100)
- `blocking` - Whether gate blocks sprint completion
- `status` - Current state (`not_run`, `passed`, `failed`)
- `score` - Actual score achieved (null until run)

### Checking Gate Status

**Command:** Dashboard Option 5

**Display:**
```
Quality Gates Status:

⏸️  Unit Testing: ≥80%
   Status: not_run
   Blocking: Yes

⏸️  Security Audit: ≥85%
   Status: not_run
   Blocking: Yes

✅ Code Review: ≥100%
   Status: passed (100%)
   Blocking: Yes
```

### Running Quality Checks

Quality gates are executed through specific workflows:

**Unit Testing:**
```bash
# Run tests with coverage
pytest --cov=. --cov-report=term

# Get coverage percentage
COVERAGE=$(pytest --cov=. --cov-report=json | jq '.totals.percent_covered')

# Update gate
python3 .claude/scripts/roadmap gate update "$SPRINT_ID" "Unit Testing" \
  --score "$COVERAGE" \
  --status "passed"  # or "failed"
```

**Security Audit:**
```bash
# Run security scan
bandit -r . -f json -o security-report.json

# Calculate score
SCORE=$(calculate_security_score security-report.json)

# Update gate
python3 .claude/scripts/roadmap gate update "$SPRINT_ID" "Security Audit" \
  --score "$SCORE" \
  --status "passed"
```

---

## Integration with Roadmap System

### Data Flow

```
┌─────────────────────────────────────────────┐
│  /vibey code Dashboard                       │
│  (framework/commands/vibey-code.md)          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Roadmap CLI                                 │
│  (framework/scripts/roadmap)                 │
│  - roadmap show <sprint-id>                  │
│  - roadmap list tasks                        │
│  - roadmap start <task-id>                   │
│  - roadmap complete <task-id>                │
│  - roadmap recommend                         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  .vibey/ State Files                         │
│  - sprints/<sprint-id>.yaml                  │
│  - tasks/<sprint-id>-tasks.yaml              │
│  - roadmap.yaml                              │
└─────────────────────────────────────────────┘
```

### State File Structure

**Sprint File:** `.vibey/sprints/<sprint-id>.yaml`

```yaml
sprint:
  id: roadmap-integration-2
  name: Progress Tracking & Vibey Manager
  status: in_progress

  progress:
    tasks_total: 6
    tasks_completed: 4
    completion_percent: 67

  quality_gates:
    - name: Unit Testing
      threshold: 80
      status: passed
      score: 95
```

**Tasks File:** `.vibey/tasks/<sprint-id>-tasks.yaml`

```yaml
tasks:
  - id: roadmap-integration-2-task-001
    sprint_id: roadmap-integration-2
    title: Update /vibey code dashboard
    status: completed
    priority: high
    estimated_hours: 6
    assigned_agents:
      - web-developer
```

---

## Agent Library Management

### Viewing Agent Workload

**Via Vibey Manager:**

Request: "Show me agent workload"

**Response:**
```
👥 Agent Workload

🔴 Overloaded (>5 tasks):
- web-developer: 4 in_progress, 3 pending (7 total)

🟡 Busy (3-5 tasks):
- test-engineer: 2 in_progress, 1 pending (3 total)

🟢 Available (<3 tasks):
- docs-writer: 0 in_progress, 2 pending (2 total)
- security-reviewer: 1 in_progress, 0 pending (1 total)

💡 Recommendation: Consider reassigning tasks from web-developer
```

### AI-Powered Optimization

**Analyze Roadmap:**

Request: "Analyze my roadmap for optimization opportunities"

**Process:**
1. Scans all roadmap tasks
2. Identifies technology patterns
3. Finds missing specialized agents
4. Detects workflow gaps
5. Recommends optimizations

**Example Output:**
```
🔍 Roadmap Analysis Complete

Analyzed:
- 24 tasks across 3 sprints
- 12 current agents
- 16 current workflows

📊 Findings (3 recommendations):

🟢 High Impact:
1. **Create "Terraform Specialist" agent** (Confidence: 95%)
   - 8 tasks involve Terraform/IaC (33% of roadmap)
   - Would reduce infrastructure agent workload by 40%

2. **Create "React Component Builder" workflow** (Confidence: 88%)
   - 6 tasks follow similar pattern
   - Would save ~2 hours per component task
```

**Auto-Generate Agent:**

Request: "Create the Terraform Specialist agent"

**Result:**
- Agent file generated at `.claude/agents/custom/terraform-specialist.md`
- Registered in `project-config.yaml`
- Relevant tasks auto-assigned
- CLAUDE.md regenerated

---

## Best Practices

### 1. Regular Progress Updates

**Do:**
- Start tasks when you begin work
- Complete tasks immediately when done
- Review dashboard at least daily

**Don't:**
- Batch multiple task completions
- Leave tasks in `in_progress` indefinitely
- Skip progress tracking "to save time"

### 2. Quality Gate Management

**Do:**
- Run gates before marking phase complete
- Address failures immediately
- Document gate results in sprint retrospective

**Don't:**
- Skip gates to "move faster"
- Lower thresholds without team discussion
- Ignore repeated gate failures

### 3. Agent Workload Balancing

**Do:**
- Monitor agent workload weekly
- Reassign tasks from overloaded agents
- Use AI recommendations for optimization

**Don't:**
- Assign all tasks to one agent
- Ignore agent capacity warnings
- Create custom agents unnecessarily

### 4. Task Estimation

**Do:**
- Estimate hours for all tasks
- Update estimates based on actual time
- Use historical data for future sprints

**Don't:**
- Leave `estimated_hours` blank
- Ignore significant estimation errors
- Blame estimates for delays (use for learning)

---

## Troubleshooting

### Dashboard Not Showing Data

**Symptom:** Dashboard displays empty or "No sprint active"

**Solutions:**
1. Verify `.vibey/` directory exists
2. Check sprint status: `python3 .claude/scripts/roadmap status`
3. Ensure sprint is `in_progress` status
4. Verify tasks file exists: `.vibey/tasks/<sprint-id>-tasks.yaml`

### Progress Not Updating

**Symptom:** Task completion doesn't update progress percentage

**Solutions:**
1. Verify roadmap CLI working: `python3 .claude/scripts/roadmap show <sprint-id>`
2. Check task status in YAML file directly
3. Manually recalculate progress:
   ```bash
   python3 .claude/scripts/roadmap recalculate <sprint-id>
   ```

### Task Recommendation Not Working

**Symptom:** "No pending tasks" when tasks exist

**Solutions:**
1. Check if tasks are blocked: `python3 .claude/scripts/roadmap deps`
2. Verify task status (may all be `in_progress` or `completed`)
3. Check task priorities are set

### Quality Gates Failing

**Symptom:** Gate repeatedly fails below threshold

**Solutions:**
1. Run audit manually to see detailed results
2. Address specific issues (test coverage, security vulns)
3. Consider if threshold is realistic for current sprint
4. Document decision to adjust threshold (with rationale)

---

## Performance

### Dashboard Load Time

**Typical:** <200ms

**Components:**
- Read sprint YAML: ~20ms
- Read tasks YAML: ~30ms
- Calculate progress: ~10ms
- Render display: ~50ms
- Total: ~110ms

### Progress Update Time

**Typical:** <100ms

**Components:**
- Update task status: ~30ms
- Recalculate sprint progress: ~20ms
- Fetch recommendations: ~40ms
- Total: ~90ms

### Optimization Tips

1. **Cache sprint data** - Read once per session
2. **Batch task operations** - Update multiple tasks together
3. **Limit task recommendations** - Use `--limit` flag
4. **Disable verbose output** - Use `--quiet` for faster CLI

---

## API Reference

### CLI Commands

**Show Sprint:**
```bash
python3 .claude/scripts/roadmap show <sprint-id> [--json]
```

**List Tasks:**
```bash
python3 .claude/scripts/roadmap list tasks [--sprint <sprint-id>] [--status <status>] [--json]
```

**Start Task:**
```bash
python3 .claude/scripts/roadmap start <task-id>
```

**Complete Task:**
```bash
python3 .claude/scripts/roadmap complete <task-id>
```

**Recommend Tasks:**
```bash
python3 .claude/scripts/roadmap recommend [--agent <agent-id>] [--limit <n>] [--json]
```

**Update Quality Gate:**
```bash
python3 .claude/scripts/roadmap gate update <sprint-id> <gate-name> --status <status> --score <score>
```

### JSON Output Format

**Sprint Data:**
```json
{
  "sprint": {
    "id": "roadmap-integration-2",
    "name": "Progress Tracking & Vibey Manager",
    "status": "in_progress",
    "progress": {
      "tasks_total": 6,
      "tasks_completed": 4,
      "completion_percent": 67
    },
    "quality_gates": [
      {
        "name": "Unit Testing",
        "threshold": 80,
        "status": "passed",
        "score": 95
      }
    ]
  }
}
```

**Task List:**
```json
{
  "tasks": [
    {
      "id": "roadmap-integration-2-task-001",
      "sprint_id": "roadmap-integration-2",
      "title": "Update /vibey code dashboard",
      "status": "completed",
      "priority": "high",
      "estimated_hours": 6,
      "assigned_agents": ["web-developer"]
    }
  ]
}
```

---

## Changelog

### v1.0.0 (2025-11-08)

**Added:**
- Real-time progress visualization
- Conversational task management
- Agent library management
- AI-powered roadmap optimization
- Quality gate tracking
- Progress bar rendering
- Task recommendations

**Features:**
- Dashboard data extraction from roadmap
- Auto-update after task operations
- Visual progress indicators
- Smart next-task suggestions
- Agent workload monitoring

---

## See Also

- [Roadmap System Documentation](../reference/ROADMAP_SYSTEM.md)
- [Vibey Manager Agent](../../agents/core/vibey-manager.md)
- [/vibey code Command](../reference/COMMANDS.md#vibey-code)
- [Agent Library Guide](AGENT_LIBRARY.md)
