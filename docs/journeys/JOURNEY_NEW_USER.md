# New User Journey

> From discovery to first productive use of Vibey

**Persona:** Nina the New User
**Duration:** 2-4 hours initial, ongoing as needed

---

## Journey Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEW USER JOURNEY                                   │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│  Discovery  │ Installation│ First Steps │ Basic Usage │ Continued Learning  │
│  (30 min)   │  (15 min)   │  (30 min)   │  (1 hour)   │   (ongoing)         │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ - Hear about│ - pip/pipx  │ - vibey init│ - status    │ - Advanced features │
│   Vibey     │ - Clone repo│ - First     │ - show      │ - Join community    │
│ - Read docs │ - Verify    │   roadmap   │ - start     │ - Provide feedback  │
│ - Evaluate  │   install   │ - Config    │ - complete  │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

---

## Stage 1: Discovery

**Duration:** ~30 minutes
**Goal:** Understand what Vibey is and whether it fits their needs

### Entry Points

1. **Search**: "AI coding assistant workflow management"
2. **Referral**: Colleague recommends Vibey
3. **GitHub**: Discover repository
4. **Documentation**: Find via Anthropic/Claude resources

### Actions & Documentation

| Action | Documentation | Commands |
|--------|---------------|----------|
| Learn what Vibey is | README.md | - |
| Understand key concepts | docs/getting-started/QUICK_START.md | - |
| See feature overview | docs/getting-started/USER_JOURNEY.md | - |
| Check requirements | README.md#Prerequisites | - |

### Key Questions at This Stage

- "What is Vibey?"
- "How is it different from Jira/Linear/Trello?"
- "Does it work with my tools?"
- "Is it worth the time investment?"

### Success Criteria

- [ ] Understands Vibey is for AI-assisted development workflow
- [ ] Knows the track/sprint/task hierarchy concept
- [ ] Decides to try installation

### Emotional Journey

```
Curious → Interested → Cautiously Optimistic
```

---

## Stage 2: Installation

**Duration:** ~15 minutes
**Goal:** Get Vibey installed and verify it works

### Actions & Documentation

| Action | Documentation | Commands |
|--------|---------------|----------|
| Install via pip | README.md#Installation | `pip install vibey` |
| Verify installation | - | `vibey --version` |
| Check help | - | `vibey --help` |
| Explore subcommands | - | `vibey roadmap --help` |

### Commands Used

```bash
# Install Vibey
pip install vibey

# Verify installation
vibey --version

# Explore available commands
vibey --help
vibey roadmap --help
```

### Potential Blockers

| Blocker | Solution |
|---------|----------|
| Python version mismatch | Install Python 3.9+ |
| Permission errors | Use `--user` or virtual environment |
| Missing dependencies | Follow error message guidance |

### Success Criteria

- [ ] `vibey --version` shows version number
- [ ] `vibey --help` shows available commands
- [ ] No error messages on basic commands

### Emotional Journey

```
Uncertain → Relieved → Ready to proceed
```

---

## Stage 3: First Steps

**Duration:** ~30 minutes
**Goal:** Initialize Vibey and create first roadmap structure

### Actions & Documentation

| Action | Documentation | Commands |
|--------|---------------|----------|
| Initialize Vibey | docs/getting-started/QUICK_START.md | `vibey init` |
| Run project discovery | docs/reference/CLI_REFERENCE.md#vibey-discover | `vibey discover run` |
| Understand structure | docs/reference/ROADMAP_SYSTEM.md | - |
| View initial status | - | `vibey roadmap status` |
| Create first track | - | `vibey roadmap create-track` |

### Commands Used

```bash
# Initialize Vibey in current project
vibey init

# Run project discovery to analyze your codebase
vibey discover run
# Discovery analyzes:
# - Project type (cli, api, library, etc.)
# - Languages and frameworks used
# - Directory structure and key files
# - Dependencies and their health
# - Code patterns and conventions

# View discovery output
vibey discover show

# View roadmap status
vibey roadmap status

# Create your first track
vibey roadmap create-track --name "My First Track"

# View what was created
vibey roadmap show track <track-id>
```

### First Roadmap Structure

After initialization, user sees:

```
.vibey/
├── roadmap/
│   ├── roadmap.yaml      # Main roadmap config
│   └── tracks/           # Track YAML files
├── roadmap.db            # SQLite database
└── config/               # Framework configuration
```

### Potential Blockers

| Blocker | Solution |
|---------|----------|
| "Already initialized" | Check existing .vibey directory |
| Git not configured | Run `git init` first (optional) |
| Confused by output | Refer to QUICK_START.md |

### Success Criteria

- [ ] `.vibey/` directory created
- [ ] `vibey roadmap status` shows roadmap info
- [ ] Understands what tracks and sprints are

### Emotional Journey

```
Excited → Slightly confused → Accomplished
```

---

## Stage 4: Basic Usage

**Duration:** ~1 hour
**Goal:** Perform basic workflow operations

### Actions & Documentation

| Action | Documentation | Commands |
|--------|---------------|----------|
| Check status | - | `vibey roadmap status` |
| View details | - | `vibey roadmap show <type> <id>` |
| Create sprint | - | `vibey roadmap create-sprint` |
| Create task | - | `vibey roadmap create-task` |
| Start task | - | `vibey roadmap start <task-id>` |
| Complete task | - | `vibey roadmap complete <task-id>` |

### Commands Used

```bash
# Check overall status
vibey roadmap status

# Create a sprint
vibey roadmap create-sprint --track <track-id> --name "Sprint 1"

# Create a task
vibey roadmap create-task --sprint <sprint-id> --title "First task"

# Start working on task
vibey roadmap start <task-id>

# Mark task complete
vibey roadmap complete <task-id>

# View updated status
vibey roadmap status
```

### Workflow Cycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Create  │───▶│  Start   │───▶│ Complete │
│  Task    │    │  Task    │    │  Task    │
└──────────┘    └──────────┘    └──────────┘
      │                               │
      └───────────────────────────────┘
              (repeat for each task)
```

### Potential Blockers

| Blocker | Solution |
|---------|----------|
| "Task not found" | Verify task ID with `vibey roadmap status` |
| Wrong status transition | Check current status first |
| Confused about IDs | Use `show` command to inspect |

### Success Criteria

- [ ] Created at least one track, sprint, and task
- [ ] Successfully started and completed a task
- [ ] Understands the create → start → complete workflow

### Emotional Journey

```
Learning → Productive → Confident
```

---

## Stage 5: Continued Learning

**Duration:** Ongoing
**Goal:** Expand knowledge and integrate Vibey into daily workflow

### Actions & Documentation

| Action | Documentation | Commands |
|--------|---------------|----------|
| Explore more commands | docs/reference/CLI_REFERENCE.md | Various |
| Learn about context | - | `vibey roadmap context` |
| Set up git hooks | docs/guides/GIT_HOOKS.md | `vibey git hooks install` |
| Join community | GitHub Discussions | - |

### Advanced Features to Explore

1. **Context Management**
   - `vibey roadmap context` - View current working context
   - `vibey roadmap add-context` - Add context to tasks

2. **Activity Tracking**
   - `vibey roadmap activity` - View recent activity
   - `vibey roadmap auto-progress` - Auto-update progress

3. **Git Integration**
   - Pre-commit hooks for task validation
   - Commit message task linking

### Success Criteria

- [ ] Uses Vibey daily without consulting docs
- [ ] Has explored advanced features
- [ ] Can help others get started

### Emotional Journey

```
Confident → Efficient → Advocate
```

---

## Command Summary

All commands used in this journey:

| Stage | Command | Purpose |
|-------|---------|---------|
| Installation | `pip install vibey` | Install framework |
| Installation | `vibey --version` | Verify installation |
| Installation | `vibey --help` | Explore commands |
| First Steps | `vibey init` | Initialize in project |
| First Steps | `vibey roadmap status` | View status |
| First Steps | `vibey roadmap create-track` | Create track |
| Basic Usage | `vibey roadmap show <type> <id>` | View details |
| Basic Usage | `vibey roadmap create-sprint` | Create sprint |
| Basic Usage | `vibey roadmap create-task` | Create task |
| Basic Usage | `vibey roadmap start <task-id>` | Start task |
| Basic Usage | `vibey roadmap complete <task-id>` | Complete task |
| Advanced | `vibey roadmap context` | View context |
| Advanced | `vibey context init` | Initialize context directory |
| Advanced | `vibey context list` | List context items |
| Advanced | `vibey context show <id>` | View context details |
| Advanced | `vibey git hooks install` | Set up hooks |

---

## Documentation Touchpoints

| Stage | Documents Read |
|-------|----------------|
| Discovery | README.md, QUICK_START.md |
| Installation | README.md (Prerequisites) |
| First Steps | QUICK_START.md, ROADMAP_SYSTEM.md |
| Basic Usage | CLI_REFERENCE.md (as needed) |
| Continued | GIT_HOOKS.md, advanced guides |

---

## Common Questions & Answers

**Q: How long until I'm productive?**
A: Most users complete basic tasks within 1 hour of installation.

**Q: Do I need to use all features?**
A: No! Start with `status`, `start`, and `complete`. Add features as needed.

**Q: What if I make a mistake?**
A: Most operations are reversible. Use `show` commands to inspect state.

**Q: Can I use Vibey with an existing project?**
A: Yes! `vibey init` can be run in any directory with or without existing code.

---

## Hands-On Tutorial

Ready to get started? Follow the step-by-step walkthrough:

**📚 [New User Walkthrough: Your First 30 Minutes with Vibey](../walkthroughs/WALKTHROUGH_NEW_USER.md)**

This walkthrough includes:
- Copy-paste ready commands
- Expected output examples
- Troubleshooting tips
- Checkpoints to verify progress
