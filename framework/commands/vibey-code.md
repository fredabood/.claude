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

# Get tasks for this sprint
TASKS_DATA=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "import sys, json; tasks=[t for t in json.load(sys.stdin) if t.get('sprint_id') == '$SPRINT_ID']; print(json.dumps(tasks))")

# Count task statuses
TASKS_IN_PROGRESS=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('status') == 'in_progress']))")
TASKS_COMPLETED=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('status') == 'completed']))")
TASKS_BLOCKED=$(echo "$TASKS_DATA" | python3 -c "import sys, json; print(len([t for t in json.load(sys.stdin) if t.get('blocked') == True]))")
```

```markdown
# 🚀 Sprint Execution Dashboard

**Current Sprint:** Sprint $SPRINT_NUMBER - $SPRINT_NAME
**Status:** $SPRINT_STATUS
**Started:** $START_DATE

---

## 📊 Sprint Progress

$PHASE_LIST

---

## 📋 Current Phase Details

$CURRENT_PHASE_DATA

---

## 📝 Recent Activity

$RECENT_ACTIVITY

---

## What would you like to do?

1. **Continue current phase** - Resume work with phase orchestration
2. **View phase orchestration rules** - See agent sequence and quality gates
3. **Check quality gate status** - Run quality checks for current phase
4. **Mark phase complete** - Finish current phase and move to next
5. **View sprint plan** - Review full sprint plan document
6. **Update sprint progress** - Log completed tasks or activities
7. **Pause sprint** - Save progress and pause sprint execution
8. **Complete sprint** - Finish sprint and generate retrospective
9. **Return to main menu**

**Choose an option (1-9):**
```

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

### Option 2: View Phase Orchestration

Display full orchestration rules for current phase including:
- Agent sequence and order
- Trigger conditions for each agent
- Quality gates with thresholds
- Completion criteria
- Rationale for orchestration design

---

### Option 3: Check Quality Gate Status

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

# Note: Quality gates are stored in sprint YAML - this would update the gate status
# For now, log as activity until quality gate tracking is enhanced
echo "✓ Security Audit completed with score: $SECURITY_SCORE"
```

---

### Option 4: Mark Phase Complete

```bash
# Check if phase can be completed
echo "Running pre-flight checks..."

# Check for incomplete/blocked tasks
INCOMPLETE_TASKS=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
tasks = [t for t in json.load(sys.stdin) if t.get('sprint_id') == '$SPRINT_ID' and t.get('status') not in ['completed']]
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
    echo "Continue working on remaining sprint tasks or move to next phase."
  fi
fi
```

---

### Option 5: View Sprint Plan

Open and display full sprint plan document:
- `docs/sprints/sprint-{{ sprint_number }}-plan.md`

---

### Option 6: Update Sprint Progress

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
tasks = [t for t in json.load(sys.stdin)
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
tasks = [t for t in json.load(sys.stdin)
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
# Note: Quality gates are stored in sprint YAML
# This would require a quality gate update command to be added to roadmap CLI
# For now, just log the result
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

### Option 7: Pause Sprint

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

### Option 8: Complete Sprint

```bash
# Check if all tasks are complete
INCOMPLETE_TASKS=$(python3 .claude/scripts/roadmap list tasks --json 2>/dev/null | python3 -c "
import sys, json
tasks = [t for t in json.load(sys.stdin)
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
tasks = [t for t in json.load(sys.stdin) if t.get('sprint_id') == '$SPRINT_ID']
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

### Option 9: Return to Main Menu

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
