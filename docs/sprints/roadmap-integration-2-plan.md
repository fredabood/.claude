# Sprint Plan: Progress Tracking & Vibey Manager

**Sprint ID:** roadmap-integration-2
**Track:** roadmap-integration
**Duration:** 2 weeks
**Status:** Planning

---

## Goals

1. Integrate real-time progress tracking into `/vibey code` command
2. Extend Vibey Manager agent with roadmap management capabilities
3. Enable users to track sprint progress during development
4. Provide seamless task status updates through conversational interface

---

## Context

Sprint 1 established the foundation by integrating roadmap initialization and sprint planning. However, users currently have no way to:
- Track progress during development
- Update task status through `/vibey` commands
- View current sprint dashboard
- Manage roadmap state conversationally

Sprint 2 bridges this gap by adding progress tracking to the execution phase (`/vibey code`) and extending the Vibey Manager agent to handle roadmap operations.

---

## Features

### 1. Update /vibey code Dashboard

**What:** Modify the sprint execution dashboard to show roadmap-based progress

**Why:** Users need to see current sprint status, tasks, and quality gates during development

**How:**
- Update vibey-code.md to query roadmap system for sprint status
- Display current sprint from `.vibey/sprints/` instead of legacy state
- Show task progress from `.vibey/tasks/` files
- Display quality gate status from roadmap
- Add "Mark task complete" option that updates roadmap state

**Files:**
- `framework/commands/vibey-code.md` (sprint dashboard section)
- Add roadmap CLI calls to display current sprint state

**Estimated Effort:** 6 hours

---

### 2. Implement Task Status Updates

**What:** Enable task status updates through `/vibey code` interface

**Why:** Users should be able to start/complete tasks without manual CLI commands

**How:**
- Add conversational task management to vibey-code.md
- When user says "I'm working on authentication", detect task and call `roadmap start <task-id>`
- When user says "Task complete", call `roadmap complete <task-id>`
- Automatic task detection based on keywords and context
- Confirmation prompts for status changes

**Files:**
- `framework/commands/vibey-code.md` (task management section)

**Estimated Effort:** 8 hours

---

### 3. Extend Vibey Manager with Roadmap Commands

**What:** Add roadmap management capabilities to Vibey Manager agent

**Why:** Users should be able to manage roadmap through `/vibey manage` conversationally

**How:**
- Add roadmap section to vibey-manager.md
- Support commands:
  - "Show roadmap status" → `roadmap status`
  - "List all sprints" → `roadmap list sprints`
  - "Show sprint details" → `roadmap show <sprint-id>`
  - "List tasks" → `roadmap list tasks`
  - "Start task" → `roadmap start <task-id>`
  - "Complete task" → `roadmap complete <task-id>`
  - "Assign task to agent" → `roadmap assign <task-id> <agent>`
- Natural language interface with confirmation prompts
- Error handling and validation

**Files:**
- `framework/agents/core/vibey-manager.md` (add roadmap section)

**Estimated Effort:** 6 hours

---

### 4. Add Real-time Progress Visualization

**What:** Display progress updates as work happens

**Why:** Users should see progress automatically update during development

**How:**
- After completing each feature/task during coding:
  - Call `roadmap progress <sprint-id>` to update completion percentage
  - Show updated progress bar
  - Display next recommended task
- Add progress checkpoint after quality gates pass
- Show sprint completion forecast based on velocity

**Files:**
- `framework/commands/vibey-code.md` (progress tracking)
- Add progress updates after phase completion

**Estimated Effort:** 4 hours

---

### 5. Create Integration Tests

**What:** Test progress tracking and Vibey Manager roadmap integration

**Why:** Ensure sprint execution and management features work correctly

**How:**
- Add tests to `test_roadmap_integration.py`
- Test scenarios:
  - Starting a sprint and tasks through vibey-code
  - Completing tasks and updating progress
  - Vibey Manager roadmap command execution
  - Progress calculation and forecasting
  - Error handling (invalid task IDs, already completed tasks)

**Files:**
- `framework/scripts/tests/test_roadmap_integration.py` (add new tests)

**Estimated Effort:** 5 hours

---

### 6. Update Documentation

**What:** Document progress tracking and roadmap management workflows

**Why:** Users need to understand new capabilities

**How:**
- Update QUICK_START.md with progress tracking section
- Add examples of task management during development
- Document Vibey Manager roadmap commands
- Add troubleshooting guide for common issues
- Update COMMANDS.md with new capabilities

**Files:**
- `framework/docs/getting-started/QUICK_START.md`
- `framework/docs/reference/COMMANDS.md`
- `framework/docs/guides/WORKFLOW_SELECTION_GUIDE.md`

**Estimated Effort:** 3 hours

---

## Success Criteria

- ✅ `/vibey code` dashboard shows roadmap-based sprint status
- ✅ Users can start/complete tasks through conversational interface
- ✅ Vibey Manager handles all roadmap commands
- ✅ Progress updates automatically during development
- ✅ Integration tests pass (>80% coverage)
- ✅ Documentation complete and clear

---

## Deliverables

1. Updated `/vibey code` command with roadmap integration
2. Extended Vibey Manager agent with roadmap capabilities
3. Real-time progress tracking during execution
4. Integration test suite for new features
5. Updated documentation (QUICK_START, COMMANDS, guides)
6. Sprint 2 completion summary

---

## Quality Gates

- Unit Testing (85%)
- Integration Testing (90%)
- Documentation Complete (90%)

---

## Dependencies

**Requires:**
- Sprint 1 completion (roadmap-integration-1) ✅

**Blocks:**
- Sprint 3 (roadmap-integration-3) - Migration needs execution integration

---

## Timeline

**Week 1:**
- Days 1-2: Update /vibey code dashboard and task status updates
- Days 3-4: Extend Vibey Manager with roadmap commands
- Day 5: Real-time progress visualization

**Week 2:**
- Days 1-2: Integration tests
- Days 3-4: Documentation updates
- Day 5: Sprint review and completion

---

## Notes

- Focus on conversational interface - users shouldn't need to know CLI commands
- Graceful degradation if roadmap files are missing or corrupted
- Maintain backward compatibility with legacy sprint-state system during transition
- Priority on user experience over feature completeness

---

## Related Documents

- `docs/development/ROADMAP_INTEGRATION_GAP.md` - Integration requirements
- `.vibey/sprint_summaries/roadmap-integration-1-COMPLETED.md` - Sprint 1 summary
- `framework/commands/vibey-code.md` - Sprint execution workflow
- `framework/agents/core/vibey-manager.md` - Framework management agent
