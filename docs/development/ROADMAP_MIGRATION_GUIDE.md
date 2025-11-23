# Roadmap System Migration Guide

**Version:** 1.0
**Last Updated:** 2025-11-07
**Target Audience:** Existing Vibey users upgrading to v1.2+

---

## Overview

This guide helps existing Vibey framework users adopt the new Roadmap Object Hierarchy system introduced in v1.2. The roadmap system is **optional** but provides significant benefits for project tracking and agent coordination.

---

## Table of Contents

1. [Should You Migrate?](#should-you-migrate)
2. [Migration Overview](#migration-overview)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Migrating Existing Sprint Plans](#migrating-existing-sprint-plans)
5. [Integration with Vibey Framework](#integration-with-vibey-framework)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Instructions](#rollback-instructions)

---

## Should You Migrate?

### Benefits of the Roadmap System

✅ **Structured Tracking** - Four-tier hierarchy (Roadmap → Track → Sprint → Task)
✅ **Intelligent Agent Routing** - Automatic task-to-agent matching
✅ **Dependency Management** - Graph-based tracking with circular detection
✅ **Progress Automation** - Automatic status progression and progress calculation
✅ **Quality Gates** - Enforced gates at sprint level
✅ **CLI Interface** - Full command-line control
✅ **Health Validation** - Comprehensive health checks

### Who Should Migrate?

**Migrate if you:**
- Have complex projects with multiple tracks/features
- Want structured task management
- Need dependency tracking
- Want intelligent agent recommendations
- Have multi-sprint roadmaps
- Need team coordination

**Don't migrate if you:**
- Have simple single-feature projects
- Prefer informal task tracking
- Don't need dependency management
- Are satisfied with current workflow

### Compatibility

- ✅ **Fully backward compatible** - Existing Vibey projects continue to work
- ✅ **Optional adoption** - Use roadmap system only when beneficial
- ✅ **No breaking changes** - Framework behavior unchanged
- ✅ **Incremental migration** - Adopt one sprint at a time

---

## Migration Overview

### What Changes?

**Added:**
- `.vibey/` directory structure (roadmap, tracks, sprints, tasks)
- `roadmap` CLI command
- Agent routing capabilities
- Dependency management
- Progress tracking automation

**Unchanged:**
- Existing agents still work the same
- Workflows remain unchanged
- Quality gates work as before
- `/vibey` command unchanged
- `project-config.yaml` format unchanged
- `CLAUDE.md` format unchanged

### Migration Timeline

**Estimated Time:** 30-60 minutes (depending on project size)

**Steps:**
1. Update framework (5 minutes)
2. Install roadmap CLI (2 minutes)
3. Initialize roadmap (5 minutes)
4. Create track(s) (10-20 minutes)
5. Migrate current sprint (10-20 minutes)
6. Test and validate (5-10 minutes)

---

## Step-by-Step Migration

### Step 1: Update Vibey Framework

#### Option A: Fresh Install (Recommended)

```bash
# In your project directory
cd /path/to/your-project

# Backup existing framework
mv .claude .claude-backup

# Re-clone framework
git clone https://github.com/fredabood/vibey.git .vibey

# Re-run /vibey initialization
claude
# Type: /vibey
```

The `/vibey` command will detect your existing `project-config.yaml` and offer to preserve it.

#### Option B: Update In-Place

```bash
# In the vibey repository
cd /path/to/vibey
git pull origin main

# Copy scripts to your project
cp -r framework/scripts /path/to/your-project/.claude/scripts
```

### Step 2: Install Roadmap CLI

Add the CLI to your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/your-project/.claude/scripts"

# Or create a symlink
ln -s /path/to/your-project/.claude/scripts/roadmap /usr/local/bin/roadmap

# Verify installation
roadmap --version
```

### Step 3: Initialize Roadmap

```bash
cd /path/to/your-project

# Initialize roadmap
roadmap init

# Or non-interactive
roadmap init \
  --id my-project \
  --name "My Project" \
  --version 1.0.0 \
  --bump-on sprint_completion \
  --bump-type minor
```

This creates `.vibey/` directory structure:
```
.vibey/
├── roadmap.yaml
├── tracks/
├── sprints/
├── tasks/
└── activity/
```

### Step 4: Create Your First Track

Based on your project, create a track file:

**Example: Backend Track**

Create `.vibey/tracks/backend.yaml`:

```yaml
track:
  # Identity
  id: "backend"
  name: "Backend API Development"
  roadmap_id: "my-project"

  # Status
  status: "in_progress"  # If you're currently working on it
  blocked: false
  priority: "high"

  # Timing
  created: "2025-11-07T10:00:00Z"
  started: "2025-11-07T10:00:00Z"
  estimated_duration: "8 weeks"

  # Progress
  progress:
    sprints_total: 4
    sprints_completed: 1
    tasks_total: 32
    tasks_completed: 8
    completion_percent: 25

  # Sprints in this track
  sprints:
    - id: "backend-1"
      name: "Authentication & User Management"
      status: "completed"
      completed: "2025-10-15T18:00:00Z"

    - id: "backend-2"
      name: "Core Business Logic"
      status: "in_progress"
      started: "2025-10-16T09:00:00Z"

    - id: "backend-3"
      name: "Third-Party Integrations"
      status: "not_started"

    - id: "backend-4"
      name: "Performance & Polish"
      status: "not_started"

  # Dependencies
  dependencies: []

  # What this track blocks
  blocks:
    - type: "track"
      target_id: "frontend"
      at_status: "completed"
      reason: "Frontend needs backend API"
```

### Step 5: Migrate Current Sprint

If you have an existing sprint plan (e.g., `docs/sprints/sprint-002-plan.md`), convert it to roadmap format.

#### Example: Existing Sprint Plan

**Before (docs/sprints/sprint-002-plan.md):**
```markdown
# Sprint 2: Core Business Logic

## Goals
- Implement order processing
- Add payment integration
- Create admin dashboard

## Tasks
1. Design order schema
2. Implement order CRUD
3. Integrate Stripe
4. Build admin UI

## Timeline
2 weeks (Oct 16 - Oct 30)
```

#### After: Convert to Roadmap Format

**Create `.vibey/sprints/backend-2.yaml`:**

```yaml
sprint:
  # Identity
  id: "backend-2"
  name: "Core Business Logic"
  track_id: "backend"
  roadmap_id: "my-project"

  # Status
  status: "in_progress"
  priority: "high"

  # Timing
  created: "2025-10-10T10:00:00Z"
  started: "2025-10-16T09:00:00Z"
  estimated_duration: "2 weeks"

  # Quality gates
  quality_gates:
    - name: "Unit Tests"
      threshold: 90
      blocking: true
      status: "not_run"

    - name: "Integration Tests"
      threshold: 85
      blocking: true
      status: "not_run"

    - name: "API Documentation"
      threshold: 100
      blocking: true
      status: "not_run"

  # Dependencies
  dependencies:
    - type: "sprint"
      target_id: "backend-1"
      at_status: "completed"
      reason: "Need auth system before business logic"

  # What this sprint blocks
  blocks:
    - type: "sprint"
      target_id: "frontend-2"
      at_status: "completed"
```

**Create `.vibey/tasks/backend-2-tasks.yaml`:**

```yaml
tasks:
  # Development Tasks
  - id: "backend-2-task-001"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Design order schema"
    description: |
      Create database schema for:
      - Order (id, user_id, status, total, created_at)
      - OrderItem (id, order_id, product_id, quantity, price)
    type: "development"
    status: "completed"

    estimated_duration: "3 hours"
    completed: "2025-10-16T15:00:00Z"
    assigned_agent: "web-developer"
    dependencies: []

  - id: "backend-2-task-002"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Implement order CRUD endpoints"
    description: |
      Create REST endpoints:
      - POST /api/orders (create order)
      - GET /api/orders/:id (get order)
      - GET /api/orders (list user's orders)
      - PUT /api/orders/:id (update status)
    type: "development"
    status: "in_progress"

    estimated_duration: "6 hours"
    started: "2025-10-17T09:00:00Z"
    assigned_agent: "web-developer"
    dependencies:
      - type: "task"
        target_id: "backend-2-task-001"
        at_status: "completed"

  - id: "backend-2-task-003"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Integrate Stripe payment processing"
    description: |
      Stripe integration:
      - Setup Stripe SDK
      - Create payment intent endpoint
      - Handle webhooks
      - Store payment records
    type: "development"
    status: "not_started"

    estimated_duration: "8 hours"
    assigned_agent: "web-developer"
    dependencies:
      - type: "task"
        target_id: "backend-2-task-002"
        at_status: "completed"

  - id: "backend-2-task-004"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Build admin dashboard API"
    description: |
      Admin endpoints:
      - GET /api/admin/orders (all orders)
      - GET /api/admin/stats (dashboard stats)
      - PUT /api/admin/orders/:id/status (update order)
    type: "development"
    status: "not_started"

    estimated_duration: "5 hours"
    assigned_agent: "web-developer"
    dependencies:
      - type: "task"
        target_id: "backend-2-task-002"
        at_status: "completed"

  # Gate Tasks
  - id: "backend-2-task-gate-001"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Write unit tests for order endpoints"
    description: "Test coverage: Order creation, updates, edge cases"
    type: "gate"
    status: "not_started"

    gate_name: "Unit Tests"
    gate_type: "completion"
    estimated_duration: "4 hours"
    assigned_agent: "test-engineer"
    dependencies:
      - type: "task"
        target_id: "backend-2-task-004"
        at_status: "completed"

  - id: "backend-2-task-gate-002"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Write integration tests"
    description: "End-to-end order flow tests with Stripe test mode"
    type: "gate"
    status: "not_started"

    gate_name: "Integration Tests"
    gate_type: "completion"
    estimated_duration: "5 hours"
    assigned_agent: "test-engineer"
    dependencies:
      - type: "task"
        target_id: "backend-2-task-004"
        at_status: "completed"

  - id: "backend-2-task-gate-003"
    sprint_id: "backend-2"
    track_id: "backend"
    roadmap_id: "my-project"

    name: "Document all order API endpoints"
    description: "OpenAPI/Swagger docs for all order and admin endpoints"
    type: "gate"
    status: "not_started"

    gate_name: "API Documentation"
    gate_type: "completion"
    estimated_duration: "3 hours"
    assigned_agent: "docs-writer"
    dependencies:
      - type: "task"
        target_id: "backend-2-task-004"
        at_status: "completed"
```

### Step 6: Test and Validate

```bash
# View roadmap status
roadmap status

# Show sprint details
roadmap show backend-2

# List all tasks
roadmap list tasks

# Validate roadmap health
roadmap validate

# Check dependencies
roadmap deps
```

---

## Migrating Existing Sprint Plans

### Conversion Pattern

**Old Sprint Plan → New Roadmap Objects:**

1. **Sprint Plan File** → Sprint YAML + Tasks YAML
2. **Goals** → Sprint description + task names
3. **Tasks** → Individual task objects
4. **Timeline** → `estimated_duration` + dates
5. **Dependencies** → Dependency objects
6. **Acceptance Criteria** → Task descriptions + gate tasks

### Automated Conversion Script

Create a helper script for bulk conversion:

```python
#!/usr/bin/env python3
"""
Convert old sprint plans to roadmap format.
"""

import yaml
import re
from pathlib import Path

def parse_sprint_plan(md_file):
    """Parse markdown sprint plan."""
    content = Path(md_file).read_text()

    # Extract sprint number and name
    title_match = re.search(r'# Sprint (\d+): (.+)', content)
    sprint_num = title_match.group(1)
    sprint_name = title_match.group(2)

    # Extract tasks
    tasks = []
    task_section = re.search(r'## Tasks\n(.+?)(?=##|\Z)', content, re.DOTALL)
    if task_section:
        task_lines = task_section.group(1).strip().split('\n')
        for line in task_lines:
            task_match = re.match(r'\d+\.\s+(.+)', line)
            if task_match:
                tasks.append(task_match.group(1))

    return sprint_num, sprint_name, tasks

def create_roadmap_sprint(sprint_num, sprint_name, tasks, track_id="backend"):
    """Create roadmap sprint structure."""
    sprint_id = f"{track_id}-{sprint_num}"

    sprint_yaml = {
        "sprint": {
            "id": sprint_id,
            "name": sprint_name,
            "track_id": track_id,
            "roadmap_id": "my-project",
            "status": "not_started",
            "estimated_duration": "2 weeks",
            "quality_gates": [
                {"name": "Unit Tests", "threshold": 90, "blocking": True, "status": "not_run"},
                {"name": "Integration Tests", "threshold": 85, "blocking": True, "status": "not_run"},
            ],
            "dependencies": [],
            "blocks": []
        }
    }

    task_objects = []
    for idx, task_name in enumerate(tasks, 1):
        task_id = f"{sprint_id}-task-{idx:03d}"
        task_obj = {
            "id": task_id,
            "sprint_id": sprint_id,
            "track_id": track_id,
            "roadmap_id": "my-project",
            "name": task_name,
            "description": f"Implement: {task_name}",
            "type": "development",
            "status": "not_started",
            "estimated_duration": "4 hours",
            "dependencies": []
        }
        task_objects.append(task_obj)

    return sprint_yaml, {"tasks": task_objects}

# Usage
sprint_num, sprint_name, tasks = parse_sprint_plan("docs/sprints/sprint-002-plan.md")
sprint_yaml, tasks_yaml = create_roadmap_sprint(sprint_num, sprint_name, tasks)

# Write files
Path(f".vibey/sprints/backend-{sprint_num}.yaml").write_text(yaml.dump(sprint_yaml))
Path(f".vibey/tasks/backend-{sprint_num}-tasks.yaml").write_text(yaml.dump(tasks_yaml))
```

---

## Integration with Vibey Framework

### Using Roadmap with Existing Agents

Agents now have access to roadmap data via the roadmap CLI:

```bash
# Agent can query current sprint
roadmap show backend-2

# Agent can get next task
roadmap recommend --agent web-developer

# Agent can update status
roadmap start backend-2-task-003
roadmap complete backend-2-task-003
```

### Integrating with `/vibey` Command

The `/vibey` command detects roadmap presence:

**With roadmap:**
```
You: /vibey
Claude: I see you have an active roadmap. Would you like to:
  1. Continue current sprint (backend-2)
  2. Plan next sprint
  3. Manage framework
```

**Without roadmap:**
```
You: /vibey
Claude: [Shows standard Vibey Manager menu]
```

### Quality Gates Integration

Roadmap quality gates work alongside Vibey's quality gate system:

- Sprint-level gates defined in sprint YAML
- Framework-level gates in `project-config.yaml`
- Both enforced during sprint completion

---

## Troubleshooting

### Issue: "roadmap: command not found"

**Solution:**
```bash
# Check PATH
echo $PATH

# Add to PATH
export PATH="$PATH:/path/to/vibey/framework/scripts"

# Or create symlink
ln -s /path/to/vibey/framework/scripts/roadmap /usr/local/bin/roadmap
```

### Issue: "No roadmap found"

**Solution:**
```bash
# Initialize roadmap
roadmap init

# Verify structure
ls -la .vibey/
```

### Issue: Import errors in roadmap CLI

**Solution:**
```bash
# Install dependencies
pip install pyyaml

# Verify Python version
python3 --version  # Should be 3.7+
```

### Issue: Circular dependency detected

**Solution:**
```bash
# Validate roadmap
roadmap validate --verbose

# View dependency graph
roadmap deps

# Fix circular dependencies by removing unnecessary deps
```

### Issue: Old sprint plans conflict with roadmap

**Solution:**

Keep both! They serve different purposes:
- **Old sprint plans** (`docs/sprints/*.md`) - Human-readable planning docs
- **Roadmap YAML** (`.vibey/`) - Machine-readable tracking data

Or archive old plans:
```bash
mkdir docs/sprints/archive
mv docs/sprints/sprint-*.md docs/sprints/archive/
```

---

## Rollback Instructions

If you need to roll back the roadmap system:

### Step 1: Backup Current State

```bash
# Backup roadmap data
tar -czf roadmap-backup.tar.gz .vibey/

# Backup modified files
cp .claude/scripts/roadmap .claude/scripts/roadmap.backup
```

### Step 2: Remove Roadmap System

```bash
# Remove roadmap directory
rm -rf .vibey/

# Remove CLI from PATH (edit ~/.bashrc or ~/.zshrc)
# Remove line: export PATH="$PATH:/path/to/.claude/scripts"

# Or remove symlink
rm /usr/local/bin/roadmap
```

### Step 3: Verify Framework Still Works

```bash
# Start Claude
claude

# Test /vibey command
# Should work normally without roadmap features
```

### Step 4: Restore from Backup (If Needed)

```bash
# Restore roadmap data
tar -xzf roadmap-backup.tar.gz

# Restore CLI
cp .claude/scripts/roadmap.backup .claude/scripts/roadmap
```

---

## Best Practices After Migration

1. **Start Small** - Migrate one sprint at a time
2. **Use Recommendations** - Leverage `roadmap recommend` for task selection
3. **Check Workload** - Monitor agent distribution with `roadmap agents --workload`
4. **Validate Regularly** - Run `roadmap validate` weekly
5. **Update Progress** - Run `roadmap progress --refresh` after batch changes
6. **Document Dependencies** - Add clear `reason` fields to all dependencies

---

## Next Steps

After successful migration:

1. **Read the User Guide** - `docs/development/ROADMAP_USER_GUIDE.md`
2. **Explore Examples** - `docs/development/ROADMAP_EXAMPLES.md`
3. **Learn CLI** - `framework/scripts/CLI.md`
4. **Create Future Sprints** - Use roadmap format for all new sprints
5. **Leverage Agent Routing** - Let the system recommend task assignments

---

## Support

**Issues:**
- Check troubleshooting section above
- Review User Guide for detailed instructions
- See examples for common patterns

**Questions:**
- Refer to CLI Reference for command details
- Check Object Hierarchy doc for data model
- Review Implementation Plan for technical details

---

**Happy tracking!** 🗺️

The roadmap system will help you manage complex projects with confidence. Start small, build incrementally, and enjoy the benefits of structured project management.
