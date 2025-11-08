# Sprint Execution Implementation

**Loaded when:** User selects Option 2 (Execute Sprint) or runs `/vibey code`

---

## Sprint Execution Flow

### Step 1: Check for Active Sprint

```bash
# Read current sprint ID from CLAUDE.md
# Format: <!-- CURRENT_SPRINT: sprint-1 -->
if [ -f ".claude/CLAUDE.md" ]; then
  SPRINT_ID=$(grep "<!-- CURRENT_SPRINT:" .claude/CLAUDE.md | sed 's/.*CURRENT_SPRINT: \([^ ]*\) .*/\1/')

  if [ -n "$SPRINT_ID" ]; then
    # Sprint ID found - verify it exists in roadmap
    if python3 .claude/scripts/roadmap show "$SPRINT_ID" --json >/dev/null 2>&1; then
      echo "✓ Active sprint: $SPRINT_ID"
    else
      echo "⚠️  Sprint $SPRINT_ID not found in roadmap"
      SPRINT_ID=""
    fi
  fi
fi
```

**If Active Sprint Exists** → Display Sprint Dashboard (Step 2)

**If No Active Sprint:**
```markdown
## No Active Sprint

You don't have an active sprint. Would you like to:

**A. Start an existing sprint plan**
   - Select from available sprint plans in `docs/sprints/`
   - Resume a paused sprint

**B. Create a new sprint plan**
   - Run `/vibey plan` to create a sprint

**C. Return to main menu**

**Choose an option (A/B/C):**
```

**Handle Choice:**
- **A:** List sprint plans → User selects → Update CLAUDE.md → Show Phase 1
- **B:** Route to Sprint Planning (load vibey-plan.md)
- **C:** Return to main menu

---

### Step 2: Display Sprint Dashboard

```bash
# Query roadmap for sprint data
SPRINT_DATA=$(python3 .claude/scripts/roadmap show "$SPRINT_ID" --json)

# Extract key metrics
SPRINT_NAME=$(echo "$SPRINT_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('sprint', {}).get('name', 'Unknown'))")
SPRINT_STATUS=$(echo "$SPRINT_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('sprint', {}).get('status', 'unknown'))")
START_DATE=$(echo "$SPRINT_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('sprint', {}).get('started', 'Not started'))")
PROGRESS=$(echo "$SPRINT_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); p=d.get('sprint', {}).get('progress', {}); print(f\"{p.get('tasks_completed', 0)}/{p.get('tasks_total', 0)}\")")

# Extract sprint number from ID (e.g., "roadmap-integration-2" -> "2" or "main-1" -> "1")
SPRINT_NUMBER=$(echo "$SPRINT_ID" | grep -oE '[0-9]+$')

# Get tasks for this sprint
TASKS_DATA=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); tasks=[t for t in data.get('tasks', []) if t.get('sprint_id') == '$SPRINT_ID']; print(json.dumps(tasks))")

# Count task statuses
TASKS_TOTAL=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
TASKS_IN_PROGRESS=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('status') == 'in_progress']))")
TASKS_COMPLETED=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('status') == 'completed']))")
TASKS_NOT_STARTED=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('status') == 'not_started']))")
TASKS_BLOCKED=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('blocked') == True]))")

# Calculate completion percentage
COMPLETION_PERCENT=$([[ $TASKS_TOTAL -gt 0 ]] && echo "scale=0; ($TASKS_COMPLETED * 100) / $TASKS_TOTAL" | bc || echo "0")

# Build task list for display
PHASE_LIST=$(python3 -c "
import sys, json
tasks = json.loads('$TASKS_DATA')
total = len(tasks)
completed = sum(1 for t in tasks if t.get('status') == 'completed')
in_progress = sum(1 for t in tasks if t.get('status') == 'in_progress')
not_started = sum(1 for t in tasks if t.get('status') == 'not_started')
blocked = sum(1 for t in tasks if t.get('blocked'))

print(f'''**Task Progress:** {completed}/{total} completed ({int(completed/total*100) if total > 0 else 0}%)

Progress Bar: [{'█' * int(completed/total*10) if total > 0 else ''}{'░' * (10 - int(completed/total*10) if total > 0 else 10)}]

**Task Status:**
- ✅ Completed: {completed}
- 🔄 In Progress: {in_progress}
- ⏸️  Not Started: {not_started}
''' + (f'- 🚫 Blocked: {blocked}\n' if blocked > 0 else ''))
")

# Get current in-progress tasks
CURRENT_PHASE_DATA=$(python3 -c "
import sys, json
tasks = json.loads('$TASKS_DATA')
in_progress = [t for t in tasks if t.get('status') == 'in_progress']
not_started = [t for t in tasks if t.get('status') == 'not_started']

if in_progress:
    print('**Currently Working On:**\n')
    for t in in_progress:
        assigned = t.get('assigned_agents', [])
        agent_str = f\" (assigned: {', '.join(assigned)})\" if assigned else ''
        print(f\"🔄 {t.get('title', t.get('id', 'Unknown'))}{agent_str}\")
        if t.get('description'):
            desc_short = t.get('description', '')[:100] + '...' if len(t.get('description', '')) > 100 else t.get('description', '')
            print(f\"   {desc_short}\")
        print()
elif not_started:
    print('**Next Tasks:**\n')
    for i, t in enumerate(not_started[:3]):  # Show first 3 not started tasks
        print(f\"{i+1}. {t.get('title', t.get('id', 'Unknown'))}\")
    print()
else:
    print('**All tasks completed!** 🎉\n')
    print('Ready to complete the sprint.')
")

# Get quality gates status
QUALITY_GATES_SUMMARY=$(echo "$SPRINT_DATA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
gates = d.get('sprint', {}).get('quality_gates', [])
if gates:
    passed = sum(1 for g in gates if g.get('status') == 'passed')
    total = len(gates)
    print(f'**Quality Gates:** {passed}/{total} passed')
else:
    print('')
")

# Get recent activity (last 5 task updates)
RECENT_ACTIVITY=$(python3 -c "
import sys, json
from datetime import datetime
tasks = json.loads('$TASKS_DATA')

# Get tasks with recent updates (completed tasks)
completed_tasks = [(t, t.get('completed_at', '')) for t in tasks if t.get('status') == 'completed' and t.get('completed_at')]
completed_tasks.sort(key=lambda x: x[1], reverse=True)

if completed_tasks:
    print('**Recent Completions:**\n')
    for t, _ in completed_tasks[:5]:
        print(f\"✅ {t.get('title', t.get('id', 'Unknown'))}\")
else:
    print('No tasks completed yet.')
")
```

```markdown
# 🚀 Sprint Execution Dashboard

**Current Sprint:** Sprint $SPRINT_NUMBER - $SPRINT_NAME
**Status:** $SPRINT_STATUS
**Started:** $START_DATE

---

## 📊 Sprint Progress

$PHASE_LIST

$QUALITY_GATES_SUMMARY

---

## 📋 Current Tasks

$CURRENT_PHASE_DATA

---

## 📝 Recent Activity

$RECENT_ACTIVITY

---

## What would you like to do?

1. **Continue current phase** - Resume work with phase orchestration
2. **Start a task** - Mark a task as in progress
3. **Complete current task** - Finish task you're working on
4. **View all tasks** - See all sprint tasks with status
5. **Check quality gate status** - Run quality checks for current phase
6. **Mark phase complete** - Finish current phase and move to next
7. **View sprint plan** - Review full sprint plan document
8. **Pause sprint** - Save progress and pause sprint execution
9. **Complete sprint** - Finish sprint and generate retrospective
10. **Return to main menu**

**Choose an option (1-10) or describe what you want to work on:**
```

**Progress Auto-Update Function:**

After any task status change (start, complete, block), automatically refresh the progress display:

```bash
function update_progress_display() {
    # Refresh sprint data
    SPRINT_DATA=$(python3 .claude/scripts/roadmap show "$SPRINT_ID" --json 2>/dev/null)

    # Extract updated progress
    UPDATED_PROGRESS=$(echo "$SPRINT_DATA" | python3 -c "
import sys, json
data = json.load(sys.stdin)
sprint = data.get('sprint', {})
progress = sprint.get('progress', {})
tasks_total = progress.get('tasks_total', 0)
tasks_completed = progress.get('tasks_completed', 0)
completion_percent = progress.get('completion_percent', 0)

print(f'''
📊 Updated Progress:
- Completed: {tasks_completed}/{tasks_total} tasks ({completion_percent}%)
- Progress: [{'█' * int(completion_percent/10)}{'░' * (10 - int(completion_percent/10))}]
''')
" 2>/dev/null)

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$UPDATED_PROGRESS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Show next recommended task
    NEXT_TASK=$(python3 .claude/scripts/roadmap recommend --limit 1 --json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data and len(data) > 0:
        task = data[0]
        print(f\"💡 Next recommended task: {task.get('title', 'Unknown')}\")
        print(f\"   ID: {task.get('id', 'unknown')}\")
        print(f\"   Estimated: {task.get('estimated_hours', 'N/A')} hours\")
    else:
        print('No pending tasks.')
except:
    pass
" 2>/dev/null)

    if [ ! -z "$NEXT_TASK" ]; then
        echo "$NEXT_TASK"
        echo ""
    fi
}
```

This function is called after:
- Starting a task (Option 2)
- Completing a task (Option 3)
- Marking a phase complete (Option 6)
- Any other state change

---

### Option 1: Continue Current Phase

```markdown
## Continuing Phase {{ current_phase_number }}: {{ current_phase_name }}

**Loading phase orchestration from:** {{ sprint_plan_file }}

---

## 📋 Phase Context

{{ phase_description }}

**Agent Orchestration:**
```yaml
agents:
{% for agent in phase_agents %}
  - name: "{{ agent.name }}"
    priority: "{{ agent.priority }}"
    mode: "{{ agent.mode }}"
{% endfor %}

sequence:
  type: "{{ sequence_type }}"
  order: {{ agent_order | to_json }}

quality_gates:
{% for gate in quality_gates %}
  - gate: "{{ gate.name }}"
    threshold: {{ gate.threshold }}
    blocking: {{ gate.blocking }}
{% endfor %}
```

**I'll follow this orchestration to help you execute this phase.**

What specific task would you like to work on?
```

**Execution:**
- Follow agent sequence from phase orchestration
- Launch mandatory agents automatically
- Check quality gates before allowing phase completion
- Update sprint plan with progress as work completes

---

### Option 2: Start a Task

```bash
# Get all not-started tasks for this sprint
NOT_STARTED_TASKS=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', []) if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') == 'not_started']

if tasks:
    print('Available tasks:\n')
    for i, t in enumerate(tasks, 1):
        assigned = t.get('assigned_agents', [])
        agent_str = f\" (suggested: {', '.join(assigned)})\" if assigned else ''
        print(f\"{i}. {t.get('title', t.get('id', 'Unknown'))}{agent_str}\")
        if t.get('description'):
            desc_short = t.get('description', '')[:80] + '...' if len(t.get('description', '')) > 80 else t.get('description', '')
            print(f\"   {desc_short}\")
        print(f\"   ID: {t.get('id', 'unknown')}\")
        print()
else:
    print('No tasks available to start.')
")

echo "$NOT_STARTED_TASKS"
```

**Ask the user:**
"Which task would you like to start? (Enter number or task ID, or describe what you want to work on)"

Parse their response:
- If they provide a number: Get task at that index
- If they provide a task ID: Use that ID directly
- If they describe work naturally: Try to match description to task title

```bash
# Example: User says "I want to work on the dashboard" or selects "2"
# Map to task ID
if [[ "$user_input" =~ ^[0-9]+$ ]]; then
  # Numeric selection
  TASK_ID=$(python3 -c "
import sys, json
data = json.loads('$NOT_STARTED_TASKS')
# Extract task ID from line containing 'ID: '
lines = '$NOT_STARTED_TASKS'.split('\n')
task_lines = [l for l in lines if 'ID: ' in l]
if len(task_lines) >= int('$user_input'):
    print(task_lines[int('$user_input')-1].split('ID: ')[1].strip())
")
else
  # Try to match description or use as task ID
  TASK_ID="$user_input"
fi

# Start the task
if python3 .claude/scripts/roadmap start "$TASK_ID" 2>/dev/null; then
  echo "✅ Task started: $TASK_ID"
  echo ""
  echo "Task is now marked as in progress. Continue working on it!"
  echo ""

  # Auto-update progress display
  update_progress_display
else
  echo "❌ Could not start task. Please check the task ID."
fi
```

---

### Option 3: Complete Current Task

```bash
# Get in-progress tasks
IN_PROGRESS_TASKS=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', []) if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') == 'in_progress']

if tasks:
    print('Currently in progress:\n')
    for t in tasks:
        print(f\"🔄 {t.get('title', t.get('id', 'Unknown'))}\")
        print(f\"   ID: {t.get('id', 'unknown')}\")
        print()
else:
    print('No tasks currently in progress.')
")

echo "$IN_PROGRESS_TASKS"
```

**Ask the user:**
"Which task have you completed? (Enter task ID or number)"

```bash
# Parse user selection
if [[ "$user_input" =~ ^[0-9]+$ ]]; then
  # Get task at index
  TASK_ID=$(python3 -c "
import sys
lines = '$IN_PROGRESS_TASKS'.split('\n')
task_lines = [l for l in lines if 'ID: ' in l]
if len(task_lines) >= int('$user_input'):
    print(task_lines[int('$user_input')-1].split('ID: ')[1].strip())
")
else
  TASK_ID="$user_input"
fi

# Complete the task
if python3 .claude/scripts/roadmap complete "$TASK_ID" 2>/dev/null; then
  echo "✅ Task completed: $TASK_ID"
  echo ""

  # Auto-update progress display with full visualization
  update_progress_display

  # Check if sprint complete
  TASKS_COMPLETED=$(python3 .claude/scripts/roadmap show "$SPRINT_ID" --json 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); p=d.get('sprint', {}).get('progress', {}); print(p.get('tasks_completed', 0))")
  TASKS_TOTAL=$(python3 .claude/scripts/roadmap show "$SPRINT_ID" --json 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); p=d.get('sprint', {}).get('progress', {}); print(p.get('tasks_total', 0))")

  if [ "$TASKS_COMPLETED" -eq "$TASKS_TOTAL" ] && [ "$TASKS_TOTAL" -gt 0 ]; then
    echo "🎉 All sprint tasks completed! Ready to complete the sprint."
  fi
else
  echo "❌ Could not complete task. Please check the task ID."
fi
```

---

### Option 4: View All Tasks

```bash
# Display all tasks with full details
echo "## 📋 All Sprint Tasks"
echo ""

python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', []) if t.get('sprint_id') == '$SPRINT_ID']

# Group by status
statuses = {
    'completed': [],
    'in_progress': [],
    'not_started': [],
    'blocked': []
}

for t in tasks:
    status = t.get('status', 'not_started')
    if t.get('blocked'):
        statuses['blocked'].append(t)
    else:
        statuses.get(status, statuses['not_started']).append(t)

# Display by status
if statuses['in_progress']:
    print('### 🔄 In Progress\n')
    for t in statuses['in_progress']:
        print(f\"**{t.get('title', 'Unknown')}** (ID: {t.get('id', 'unknown')})\")
        if t.get('assigned_agents'):
            print(f\"Assigned: {', '.join(t.get('assigned_agents'))}\" )
        if t.get('description'):
            print(f\"{t.get('description')[:200]}\")
        print()

if statuses['completed']:
    print('### ✅ Completed\n')
    for t in statuses['completed']:
        print(f\"- {t.get('title', 'Unknown')}\")
    print()

if statuses['not_started']:
    print('### ⏸️  Not Started\n')
    for t in statuses['not_started']:
        print(f\"**{t.get('title', 'Unknown')}** (ID: {t.get('id', 'unknown')})\")
        if t.get('assigned_agents'):
            print(f\"Suggested: {', '.join(t.get('assigned_agents'))}\")
        if t.get('estimated_hours'):
            print(f\"Estimated: {t.get('estimated_hours')} hours\")
        print()

if statuses['blocked']:
    print('### 🚫 Blocked\n')
    for t in statuses['blocked']:
        print(f\"**{t.get('title', 'Unknown')}** (ID: {t.get('id', 'unknown')})\")
        print(f\"Reason: {t.get('blocked_reason', 'Unknown')}\")
        print()
"
```

**Return to dashboard menu**

---

### Old Options Note

(Options 2-4 above replace old phase orchestration view. Continuing with remaining options renumbered...)
- Quality gates with thresholds
- Completion criteria
- Rationale for orchestration design

---

### Option 5 (continued): Check Quality Gate Status

```bash
# Note: Phase numbers are tracked in sprint plan markdown for documentation purposes
# The roadmap system focuses on task-level tracking rather than phase-level tracking
# For now, assume phase 1 unless specified otherwise
CURRENT_PHASE_NUM=1

# Get quality gates status from sprint
SPRINT_DATA=$(python3 .claude/scripts/roadmap show "$SPRINT_ID" --json)
QUALITY_GATES=$(echo "$SPRINT_DATA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
gates = d.get('sprint', {}).get('quality_gates', [])
for gate in gates:
    status_emoji = '✅' if gate.get('status') == 'passed' else '⏸️' if gate.get('status') == 'not_run' else '❌'
    print(f\"{status_emoji} {gate.get('name', 'Unknown')}: {gate.get('threshold', 'N/A')}\")
" 2>/dev/null)

echo "Quality Gates Status:"
echo "$QUALITY_GATES"
```

**Implementation Note:** Quality gate checks (test coverage, security audit, etc.) are run separately and results are recorded using:

```bash
# Example: Run security audit and record result
# (actual audit command depends on project type)
SECURITY_SCORE=$(run_security_audit)

# Update quality gate in roadmap
python3 .claude/scripts/roadmap gate update "$SPRINT_ID" "Security Audit" "passed" --score "$SECURITY_SCORE"

echo "✓ Security Audit completed with score: $SECURITY_SCORE"
```

---

### Option 6: Mark Phase Complete

```bash
# Check if phase can be completed
echo "Running pre-flight checks..."

# Check for incomplete/blocked tasks
INCOMPLETE_TASKS=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', []) if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') not in ['completed']]
print(len(tasks))
")

if [ "$INCOMPLETE_TASKS" -gt 0 ]; then
  echo "❌ Cannot complete phase - $INCOMPLETE_TASKS incomplete tasks"
  echo ""
  echo "Options:"
  echo "1. Continue working on tasks"
  echo "2. View task details"
  echo "3. Override (not recommended)"
  echo "4. Cancel"
  # Handle user choice
else
  echo "✅ Phase $CURRENT_PHASE_NUM ready for completion"
  echo ""
```

**Ask the user:**
"Mark Phase $CURRENT_PHASE_NUM as complete?"

Parse their response. If they agree (default yes), set `confirm=""`. If they say no, set `confirm="n"`.

```bash
  if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
    # Note: Phase tracking within sprints is handled in sprint plan markdown
    # The roadmap system tracks tasks and sprint status, not individual phases

    echo ""
    echo "✅ Phase $CURRENT_PHASE_NUM marked complete!"
    echo ""

    # Auto-update progress display after phase completion
    update_progress_display

    echo "Continue working on remaining sprint tasks or move to next phase."
  fi
fi
```

---

### Option 7: View Sprint Plan

Open and display full sprint plan document:
- `docs/sprints/sprint-{{ sprint_number }}-plan.md`

---

### Option 8 (Deprecated): Update Sprint Progress

Note: This option is now automated through Options 2-3 (Start/Complete tasks).
Task status updates automatically update sprint progress.

```markdown
## Log Sprint Activity

What would you like to log?

1. **Mark task complete**
2. **Log agent execution**
3. **Add quality gate result**
4. **Add note or observation**

Choose an option (1-4):
```

**Option 1: Mark task complete**
```bash
# List incomplete tasks for this sprint
TASKS_JSON=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', [])
         if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') != 'completed']
for i, task in enumerate(tasks, 1):
    print(f\"{i}. {task.get('title', task.get('id', 'Unknown'))} ({task.get('status', 'unknown')})\")
")

echo "Incomplete tasks:"
echo "$TASKS_JSON"
echo ""
```

**Ask the user:**
"Which task would you like to mark as complete? (Provide the task number or ID)"

Parse their response and set `TASK_INPUT` to the task number or ID they provide.

```bash
# If numeric, find task by position
if [[ "$TASK_INPUT" =~ ^[0-9]+$ ]]; then
  TASK_ID=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', [])
         if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') != 'completed']
if $TASK_INPUT <= len(tasks):
    print(tasks[$TASK_INPUT - 1]['id'])
")
else
  TASK_ID="$TASK_INPUT"
fi

# Mark task complete
python3 .claude/scripts/roadmap complete "$TASK_ID"

echo "✓ Task marked complete"
```

**Option 2: Log agent execution**
```markdown
```

**Ask the user these questions:**
1. "Which task ID is this agent working on?"
2. "Which agent was executed?"
3. "Any notes or observations? (optional - press enter to skip)"

Parse their responses and set:
- `TASK_ID` to their answer to question 1
- `AGENT_NAME` to their answer to question 2
- `AGENT_NOTES` to their answer to question 3 (can be empty)

```bash
# Assign agent to task
python3 .claude/scripts/roadmap assign "$TASK_ID" "$AGENT_NAME"

echo "✓ Agent $AGENT_NAME assigned to task $TASK_ID"
if [ -n "$AGENT_NOTES" ]; then
  echo "  Notes: $AGENT_NOTES"
fi
```

**Option 3: Add quality gate result**
```markdown
```

**Ask the user these questions:**
1. "Which quality gate are you recording? (e.g., Security Audit, Test Coverage, Code Review)"
2. "What was the result? (passed or failed)"
3. "What was the score? (optional - press enter to skip)"

Parse their responses and set:
- `GATE_NAME` to their answer to question 1
- `GATE_STATUS` to their answer to question 2
- `GATE_SCORE` to their answer to question 3 (can be empty)

```bash
# Update quality gate in roadmap
if [ -n "$GATE_SCORE" ]; then
  python3 .claude/scripts/roadmap gate update "$SPRINT_ID" "$GATE_NAME" "$GATE_STATUS" --score "$GATE_SCORE"
else
  python3 .claude/scripts/roadmap gate update "$SPRINT_ID" "$GATE_NAME" "$GATE_STATUS"
fi

echo "✓ Quality gate result recorded: $GATE_NAME = $GATE_STATUS"
if [ -n "$GATE_SCORE" ]; then
  echo "  Score: $GATE_SCORE"
fi
```

**Option 4: Add note**
```markdown
```

**Ask the user:**
"What note or observation would you like to add to the sprint activity log?"

Parse their response and set `NOTE_TEXT` to the note they provide.

```bash
# Note: Activity logging could be added to roadmap system in the future
# For now, notes can be added to task descriptions or git commits
echo "✓ Note recorded: $NOTE_TEXT"
echo ""
echo "Consider adding this to:"
echo "  - Task description (roadmap show <task-id>)"
echo "  - Git commit message"
echo "  - Sprint retrospective"
```

---

### Option 8: Pause Sprint

```markdown
```

**Ask the user:**
"Pause sprint and save progress?"

Parse their response. If they agree (default yes), set `confirm=""`. If they say no, set `confirm="n"`.

```bash
if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
  # Update CLAUDE.md to clear current sprint marker
  sed -i.bak 's/<!-- CURRENT_SPRINT: .* -->/<!-- CURRENT_SPRINT: none -->/' .claude/CLAUDE.md
  sed -i.bak 's/\*\*Current Sprint:\*\* .*/\*\*Current Sprint:\*\* none (paused)/' .claude/CLAUDE.md

  # Git commit
  git add .vibey/ .claude/CLAUDE.md
  git commit -m "Pause Sprint $SPRINT_ID

All progress preserved in roadmap.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

  echo ""
  echo "✅ Sprint paused"
  echo "📁 Progress saved in: .vibey/"
  echo ""
  echo "To resume: run /vibey code and select the sprint"
fi
```

---

### Option 9: Complete Sprint

```bash
# Check if all tasks are complete
INCOMPLETE_TASKS=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', [])
         if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') != 'completed']
print(len(tasks))
")

if [ "$INCOMPLETE_TASKS" -gt 0 ]; then
  echo "❌ Cannot complete sprint - $INCOMPLETE_TASKS incomplete tasks"
  echo ""
  echo "Options:"
  echo "1. Return to dashboard"
  echo "2. Complete anyway (not recommended)"
  # Handle user choice
else
```

**Ask the user:**
"All tasks complete! Mark Sprint $SPRINT_ID as complete and generate retrospective?"

Parse their response. If they agree (default yes), set `confirm=""`. If they say no, set `confirm="n"`.

```bash
  if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
    # Mark sprint complete in roadmap
    python3 .claude/scripts/roadmap complete "$SPRINT_ID"

    # Update CLAUDE.md marker (deactivate)
    sed -i.bak 's/<!-- CURRENT_SPRINT: .* -->/<!-- CURRENT_SPRINT: none -->/' .claude/CLAUDE.md
    sed -i.bak 's/\*\*Current Sprint:\*\* .*/\*\*Current Sprint:\*\* none/' .claude/CLAUDE.md

    # Generate retrospective
    echo "📝 Generating sprint retrospective..."

    # Get sprint data
    SPRINT_DATA=$(python3 .claude/scripts/roadmap show "$SPRINT_ID" --json)
    SPRINT_GOAL=$(echo "$SPRINT_DATA" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('sprint', {}).get('goal', 'N/A'))")

    # Get completed tasks
    TASKS_LIST=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = [t for t in data.get('tasks', []) if t.get('sprint_id') == '$SPRINT_ID']
for t in tasks:
    status = '✅' if t.get('status') == 'completed' else '⏸️'
    print(f\"- {status} {t.get('title', t.get('id', 'Unknown'))}\")
")

    # Create retrospective file
    cat > "docs/sprints/$SPRINT_ID-retrospective.md" << EOF
# Sprint Retrospective: $SPRINT_NAME

**Sprint ID:** $SPRINT_ID
**Completed:** $(date +%Y-%m-%d)

## Sprint Goal

$SPRINT_GOAL

## Completed Tasks

$TASKS_LIST

## What Went Well

- [To be filled in]

## What Could Be Improved

- [To be filled in]

## Action Items for Next Sprint

- [To be filled in]

---

*Retrospective template - fill in observations and learnings*
EOF

    # Update FRAMEWORK_ROADMAP.md (if exists)
    if [ -f "docs/FRAMEWORK_ROADMAP.md" ]; then
      echo "" >> docs/FRAMEWORK_ROADMAP.md
      echo "## ✅ $SPRINT_ID: $SPRINT_NAME (Completed $(date +%Y-%m-%d))" >> docs/FRAMEWORK_ROADMAP.md
      echo "See: docs/sprints/$SPRINT_ID-retrospective.md" >> docs/FRAMEWORK_ROADMAP.md
    fi

    # Git commit
    git add .vibey/ docs/sprints/$SPRINT_ID-*.* .claude/CLAUDE.md docs/FRAMEWORK_ROADMAP.md
    git commit -m "Complete Sprint $SPRINT_ID: $SPRINT_NAME

🎉 Sprint successfully completed!

See retrospective: docs/sprints/$SPRINT_ID-retrospective.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    echo ""
    echo "🎉 Sprint $SPRINT_ID completed!"
    echo "📄 Retrospective: docs/sprints/sprint-$SPRINT_NUMBER-retrospective.md"
    echo ""
    echo "Ready to plan your next sprint? Run /vibey plan"
  fi
fi
```

---

### Option 10: Return to Main Menu

Return to main `/vibey` menu

---

## Sprint Execution Loop

After any action → Return to Sprint Dashboard (unless user chooses Return to Main Menu)

This creates a continuous execution loop:
1. View dashboard
2. Choose action
3. Execute action
4. Return to dashboard
5. Repeat

---

## Guidelines for Sprint Execution

### Do's:
✅ Follow phase orchestration rules
✅ Enforce quality gates (block phase completion if gates fail)
✅ Update sprint plan continuously
✅ Git commit after each phase completion
✅ Track progress for retrospective

### Don'ts:
❌ Don't skip mandatory agents
❌ Don't ignore blocking quality gate failures
❌ Don't move to next phase without completing current
❌ Don't forget to update sprint marker in CLAUDE.md

---

**Sprint execution ready!** User can work through phases systematically with quality enforcement.
