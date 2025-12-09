# Vibey Interface Audit

**Date:** 2025-11-12
**Purpose:** Assess all user-facing entry points, integration quality, duplication, and coverage gaps
**Status:** Complete

---

## Executive Summary

Vibey has **4 distinct user interfaces** with varying levels of maturity and integration:

1. **Slash Commands** (`/vibey`) - Claude Code entry point (MATURE, 4,389 lines)
2. **Python CLI** (`vibey` command) - Standalone CLI tool (MATURE, full-featured)
3. **MCP Server** - Protocol-based integration (IMPLEMENTED, awaiting SDK)
4. **Direct AI Interaction** - Natural language through coding assistant (IMPLICIT)

**Key Findings:**
- ✅ **Strong Separation:** CLI and slash commands serve different purposes with minimal duplication
- ⚠️ **Integration Gap:** Slash commands don't leverage CLI for roadmap operations
- ⚠️ **Coverage Gap:** Not all CLI features available via slash commands
- ⚠️ **MCP Incomplete:** Server structure ready but awaiting MCP SDK
- ⚠️ **Documentation:** No unified interface guide for users

---

## Interface Inventory

### 1. Slash Commands (`/vibey`)

**Location:** `framework/commands/`
**Entry Point:** `/vibey` (Claude Code)
**Purpose:** Interactive AI-guided workflows
**Lines of Code:** 4,389 total (6 commands)

**Commands:**
- `/vibey` - Main menu (1,454 lines)
- `/vibey plan` - Sprint planning (336 lines)
- `/vibey code` - Execute sprint (1,095 lines)
- `/vibey think` - Discovery mode (765 lines)
- `/vibey manage` - Framework management (617 lines)
- `/vibey audit` - Project audit (122 lines)

**Capabilities:**
- Interactive conversational workflows
- Context-aware guidance
- First-time user onboarding
- Sprint planning and execution
- Framework initialization
- Project auditing

**Target User:** Developers using Claude Code

---

### 2. Python CLI (`vibey`)

**Location:** `vibey/cli/`
**Entry Point:** `vibey` command (installed via pip)
**Purpose:** Standalone CLI tool for framework management
**Version:** 2.5.0

**Command Groups:**

#### Roadmap Commands (`vibey roadmap`)
```
vibey roadmap init           # Initialize roadmap
vibey roadmap status         # Show status (tracks/sprints/tasks)
vibey roadmap show <id>      # Show details for item
vibey roadmap start <id>     # Start sprint/task
vibey roadmap complete <id>  # Complete sprint/task
vibey roadmap context <id>   # Get AI-optimized context
vibey roadmap summarize <type> <id>  # Summarize item
vibey roadmap add-commit <id> [sha]  # Add git commit to task
```

#### Deploy Commands (`vibey deploy`)
```
vibey deploy run --platform <name>  # Deploy to platform
vibey deploy list                   # List platforms
```

#### Docs Commands (`vibey docs`)
```
vibey docs generate          # Generate documentation
```

#### Config Commands (`vibey config`)
```
vibey config show            # Show current config
vibey config validate        # Validate config files
vibey config migrate         # Migrate legacy config
vibey config rollback        # Rollback config backup
```

**Capabilities:**
- Complete roadmap lifecycle management
- Multi-platform deployment
- Configuration management
- Documentation generation
- Git integration
- Scripting and automation friendly

**Target User:** Any developer (platform-agnostic)

---

### 3. MCP Server

**Location:** `framework/mcp/`
**Entry Point:** MCP protocol (stdio/HTTP+SSE)
**Purpose:** Expose Vibey as MCP tools for any MCP-compatible client
**Status:** Implemented, awaiting MCP SDK installation

**Tools Available (11 total):**

#### Task Tools
```
vibey_query_task          # Query task details
vibey_start_task          # Start a task
vibey_complete_task       # Complete a task
```

#### Sprint Tools
```
vibey_query_sprint        # Query sprint details
vibey_start_sprint        # Start a sprint
vibey_complete_sprint     # Complete a sprint
vibey_refresh_progress    # Refresh progress calculation
```

#### Query Tools
```
vibey_query_track         # Query track details
vibey_roadmap_status      # Get roadmap status
vibey_list_dependencies   # List dependencies
vibey_list_blockers       # List blockers
```

**Capabilities:**
- Read-only queries (tracks, sprints, tasks)
- Task lifecycle (start, complete)
- Sprint lifecycle (start, complete)
- Dependency analysis
- Blocker detection
- Progress tracking

**Target User:** Any AI assistant with MCP support (Claude Desktop, etc.)

---

### 4. Direct AI Interaction (Implicit)

**Location:** N/A (natural language)
**Entry Point:** Conversation with AI coding assistant
**Purpose:** Ad-hoc interactions without formal commands

**Capabilities:**
- Natural language queries about roadmap
- Code generation for framework tasks
- Documentation reading and explanation
- Troubleshooting and debugging

**Target User:** Developers working with AI assistants

---

## Functional Comparison Matrix

| Function | Slash Commands | Python CLI | MCP Server | Direct AI |
|----------|---------------|------------|------------|-----------|
| **Roadmap Management** |
| Initialize roadmap | ✅ (/vibey) | ✅ (roadmap init) | ❌ | ⚠️ (manual) |
| View status | ⚠️ (via think/manage) | ✅ (roadmap status) | ✅ (vibey_roadmap_status) | ✅ (ask) |
| Show details | ⚠️ (via think/manage) | ✅ (roadmap show) | ✅ (vibey_query_*) | ✅ (ask) |
| Start sprint/task | ❌ | ✅ (roadmap start) | ✅ (vibey_start_*) | ⚠️ (manual) |
| Complete sprint/task | ❌ | ✅ (roadmap complete) | ✅ (vibey_complete_*) | ⚠️ (manual) |
| Add git commit | ❌ | ✅ (roadmap add-commit) | ❌ | ❌ |
| Get context | ❌ | ✅ (roadmap context) | ❌ | ⚠️ (ask) |
| Summarize | ❌ | ✅ (roadmap summarize) | ❌ | ✅ (ask) |
| Dependencies | ❌ | ❌ | ✅ (vibey_list_dependencies) | ⚠️ (ask) |
| Blockers | ❌ | ❌ | ✅ (vibey_list_blockers) | ⚠️ (ask) |
| **Framework Management** |
| Deploy framework | ⚠️ (initialization) | ✅ (deploy run) | ❌ | ❌ |
| List platforms | ❌ | ✅ (deploy list) | ❌ | ⚠️ (ask) |
| Manage config | ✅ (/vibey manage) | ✅ (config *) | ❌ | ⚠️ (manual) |
| Migrate config | ❌ | ✅ (config migrate) | ❌ | ❌ |
| Rollback config | ❌ | ✅ (config rollback) | ❌ | ❌ |
| **Documentation** |
| Generate docs | ❌ | ✅ (docs generate) | ❌ | ❌ |
| **Workflows** |
| Sprint planning | ✅ (/vibey plan) | ⚠️ (manual CLI calls) | ⚠️ (manual tool calls) | ✅ (guided) |
| Sprint execution | ✅ (/vibey code) | ⚠️ (manual CLI calls) | ⚠️ (manual tool calls) | ✅ (guided) |
| Discovery mode | ✅ (/vibey think) | ❌ | ❌ | ✅ (natural) |
| Project audit | ✅ (/vibey audit) | ❌ | ❌ | ⚠️ (manual) |

**Legend:**
- ✅ Fully supported
- ⚠️ Partially supported or requires manual steps
- ❌ Not available

---

## Duplication Analysis

### Minimal Duplication (Good)

**Slash Commands vs CLI:**
- **Different Purposes:** Slash commands provide guided workflows; CLI provides atomic operations
- **Complementary:** Slash commands could/should call CLI internally (currently don't)
- **No Direct Overlap:** `/vibey` doesn't duplicate `vibey` commands

**MCP vs CLI:**
- **Different Transport:** MCP wraps roadmap operations; CLI is standalone
- **Shared Logic:** MCP uses roadmap adapter, CLI uses commands module
- **No Duplication:** MCP tools are thin wrappers around core roadmap library

### Unnecessary Duplication (Needs Attention)

**Standalone Python Scripts:**
```
vibey/cli/roadmap-init.py
vibey/cli/roadmap-update.py
vibey/cli/roadmap-query.py
vibey/cli/roadmap-summarize.py
vibey/cli/roadmap-add-commit.py
vibey/cli/manage-project-context.py
vibey/cli/generate-config.py
vibey/cli/update-config.py
... (20+ standalone scripts)
```

**Issue:** Many standalone Python scripts in `vibey/cli/` that overlap with:
- CLI commands in `vibey/cli/main.py`
- Command implementations in `vibey/cli/commands.py`

**Root Cause:** Scripts were created before unified CLI existed

**Impact:**
- Confusion about which to use
- Maintenance burden (two ways to do same thing)
- Inconsistent interfaces

---

## Integration Quality Assessment

### Strong Integration ✅

**1. MCP Server → Roadmap Library**
- Clean adapter pattern
- Shared data models
- Consistent error handling
- Tool/handler separation

**2. CLI → Commands Module**
- Organized command structure
- Consistent argument handling
- Unified error handling
- Click framework benefits

### Weak Integration ⚠️

**1. Slash Commands ↛ CLI**
- Slash commands don't call `vibey` CLI internally
- Duplicate roadmap manipulation logic
- No shared error handling
- Inconsistent user experience

**Example Issue:**
```bash
# In /vibey plan, roadmap initialization is manual Python logic
# Could instead call: vibey roadmap init

# In /vibey code, task completion is manual
# Could instead call: vibey roadmap complete <task-id>
```

**2. Standalone Scripts ↛ CLI**
- Scripts don't import from CLI commands
- Scripts implement own argument parsing
- Scripts bypass unified error handling
- No consistency with `vibey` command UX

### Missing Integration ⚠️

**1. No Unified Interface Documentation**
- Users don't know which interface to use when
- No decision tree (slash vs CLI vs MCP)
- No compatibility matrix

**2. No Cross-Platform Tool Detection**
- Slash commands assume Claude Code
- CLI doesn't know it's being called from Claude
- No handoff mechanism between interfaces

---

## Coverage Gaps

### Gap 1: Roadmap Operations in Slash Commands

**Missing from `/vibey`:**
- Direct roadmap status query (must use /vibey think or manage)
- Task start/complete commands
- Sprint start/complete commands
- Git commit tracking (add-commit)
- Dependency visualization
- Blocker analysis

**Impact:** Users must switch to CLI for these operations

**Recommendation:** Add `/vibey roadmap` sub-command or integrate CLI calls

---

### Gap 2: Workflow Guidance in CLI

**Missing from `vibey` CLI:**
- Interactive sprint planning workflow (like /vibey plan)
- Guided sprint execution (like /vibey code)
- Discovery mode (like /vibey think)
- First-time user onboarding

**Impact:** CLI users miss the guided experience that makes Vibey powerful

**Recommendation:** Add `vibey interactive` or `vibey wizard` commands

---

### Gap 3: Write Operations in MCP

**Missing from MCP Server:**
- Create sprint/task
- Update sprint/task metadata
- Add git commits
- Modify dependencies
- Configure quality gates

**Impact:** MCP is read-heavy, can't manage full lifecycle

**Recommendation:** Add write tools in MCP Sprint 3

---

### Gap 4: Advanced Roadmap Features in All Interfaces

**Missing everywhere:**
- Platform context management (our new track!)
- Sprint recalculation
- Quality gate enforcement (standards-system)
- Dependency conflict resolution
- Automated task assignment

**Impact:** New features not yet exposed to users

**Recommendation:** Add support as features are implemented

---

## Conflicts and Inconsistencies

### Conflict 1: Entry Point Confusion

**Problem:** Users don't know whether to use `/vibey` or `vibey` command

**Manifestation:**
- "/vibey vs vibey: what's the difference?" (common question)
- Users try `vibey` in Claude and it fails
- Users try `/vibey` in terminal and it fails

**Solution:** Clear documentation + tool detection

---

### Conflict 2: Standalone Scripts vs CLI Commands

**Problem:** Two ways to invoke same functionality

**Examples:**
```bash
# Two ways to init roadmap:
python vibey/cli/roadmap-init.py
vibey roadmap init

# Two ways to add commit:
python vibey/cli/roadmap-add-commit.py task-001 abc123
vibey roadmap add-commit task-001 abc123

# Two ways to generate config:
python vibey/cli/generate-config.py
vibey config ... (no direct equivalent)
```

**Solution:** Deprecate standalone scripts, consolidate to CLI

---

### Conflict 3: Inconsistent Error Handling

**Problem:** Each interface handles errors differently

- **Slash commands:** Natural language explanations in Claude
- **CLI:** Click error messages + exit codes
- **MCP:** JSON error responses with isError flag
- **Standalone scripts:** Plain print() statements + sys.exit()

**Solution:** Unified error handling library

---

## User Experience Assessment

### Scenario 1: First-Time User (Claude Code)

**Current Experience:**
1. Run `/vibey` ✅ Great! Interactive menu, guided setup
2. Complete sprint planning ✅ Excellent guided workflow
3. Want to check status midway ⚠️ Must use `/vibey think` (not obvious)
4. Want to mark task complete ❌ No command! Must manually edit YAML or use CLI

**Gap:** Mid-sprint roadmap operations missing

---

### Scenario 2: Power User (Terminal + Claude)

**Current Experience:**
1. Use `vibey roadmap status` in terminal ✅ Fast, scriptable
2. Use `vibey roadmap start sprint-1` ✅ Works great
3. Switch to Claude for coding ✅ Works
4. Want to run `/vibey` to execute sprint ⚠️ Loses context from CLI start
5. Want to use CLI from Claude ❌ Must switch to terminal

**Gap:** No handoff between interfaces

---

### Scenario 3: MCP-Only User (Claude Desktop)

**Current Experience:**
1. Install MCP server ⚠️ Awaiting SDK installation
2. Query roadmap status ✅ Should work via vibey_roadmap_status
3. Start a task ✅ Should work via vibey_start_task
4. Try to create new sprint ❌ No write tools yet
5. Try to add git commit ❌ Not exposed via MCP

**Gap:** Read-only MCP server

---

### Scenario 4: Multi-Platform Team

**Current Experience:**
1. Alice (Claude Code) runs `/vibey plan` ✅ Creates sprint
2. Bob (Goose) wants to see status ❌ No Goose integration yet
3. Bob uses `vibey roadmap status` ✅ CLI works!
4. Carol (Cursor) wants guided execution ❌ `/vibey` not available
5. Carol uses CLI ⚠️ Works but no guidance

**Gap:** Platform-specific entry points, no unified experience

---

## Recommendations

### Priority 1: CRITICAL - Interface Unification Track

Create a new track: `interface-unification` (4-6 weeks)

**Goals:**
1. Consolidate standalone scripts into CLI commands
2. Make slash commands call CLI internally
3. Create unified error handling
4. Build tool detection and handoff
5. Document interface decision tree

**Sprints:**
1. **Sprint 1:** Deprecate standalone scripts (migrate to CLI)
2. **Sprint 2:** Slash command → CLI integration
3. **Sprint 3:** Unified error handling library
4. **Sprint 4:** Cross-interface context passing
5. **Sprint 5:** Documentation and testing

**Blocks:** None (can start immediately)
**Priority:** CRITICAL (affects all users, all platforms)

---

### Priority 2: HIGH - Complete MCP Server

**Status:** Already tracked in `mcp-server` track

**Missing:**
- MCP SDK installation and integration
- Write operation tools
- Resource support
- Prompt support

**Timeline:** 2 sprints remaining (mcp-server track shows completed?)

---

### Priority 3: HIGH - CLI Interactive Mode

Add guided workflows to CLI:

```bash
vibey interactive plan        # Interactive sprint planning
vibey interactive execute     # Guided sprint execution
vibey interactive discover    # Discovery mode
```

**Benefits:**
- CLI users get guided experience
- Slash commands can delegate to CLI
- Consistent UX across platforms

**Effort:** 2-3 weeks
**Depends on:** Interface unification (Priority 1)

---

### Priority 4: MEDIUM - Unified Documentation

Create comprehensive interface guide:

**Documents Needed:**
1. `docs/guides/INTERFACE_SELECTION_GUIDE.md` - When to use which interface
2. `docs/guides/CLAUDE_CODE_WORKFLOW.md` - Slash command workflows
3. `docs/guides/CLI_REFERENCE.md` - Complete CLI documentation
4. `docs/guides/MCP_INTEGRATION.md` - MCP server setup and usage
5. `docs/guides/CROSS_PLATFORM_WORKFLOWS.md` - Multi-platform teams

**Effort:** 1-2 weeks

---

### Priority 5: LOW - Platform Adapters

Create adapters for each platform:

```python
# vibey/platform/adapters/claude_code.py
# vibey/platform/adapters/goose.py
# vibey/platform/adapters/cursor.py
```

**Purpose:**
- Detect current platform
- Route to appropriate interface
- Handle platform-specific quirks

**Effort:** 1 week per platform
**Depends on:** platform-context-management track

---

## Decision Tree: Which Interface Should I Use?

```
Are you using Claude Code?
├─ YES → Use /vibey slash commands
│         ├─ First time? → /vibey (guided setup)
│         ├─ Sprint planning? → /vibey plan
│         ├─ Coding? → /vibey code
│         ├─ Exploring? → /vibey think
│         └─ Managing? → /vibey manage
│
├─ NO → Are you using MCP-compatible client?
│       ├─ YES → Use MCP tools
│       │         └─ Query roadmap, start/complete tasks
│       │
│       └─ NO → Use vibey CLI
│                 ├─ Scripting/automation? → vibey roadmap
│                 ├─ Deployment? → vibey deploy
│                 ├─ Config management? → vibey config
│                 └─ Documentation? → vibey docs

Power users: Combine interfaces!
  - Use CLI for quick ops in terminal
  - Use slash commands for guided workflows in Claude
  - Use MCP from any MCP-compatible client
```

---

## Proposed Track: Interface Unification

### Track Definition

**ID:** `interface-unification`
**Name:** Interface Unification & Consolidation
**Priority:** CRITICAL
**Timeline:** 5 weeks
**Dependencies:** None

**Problem:** Multiple overlapping interfaces with inconsistent UX, no integration between them, and users confused about which to use.

**Solution:** Consolidate standalone scripts, integrate slash commands with CLI, create unified error handling, and document clear interface boundaries.

**Deliverables:**
1. All standalone scripts migrated to CLI commands
2. Slash commands call CLI internally (no duplicate logic)
3. Unified error handling library used by all interfaces
4. Tool detection and cross-interface context passing
5. Complete interface documentation
6. Deprecation warnings and migration guide

---

## Success Metrics

### Current State (Baseline)
- 4 interfaces (slash, CLI, MCP, direct AI)
- 20+ standalone scripts overlapping with CLI
- 0% integration between slash commands and CLI
- No unified documentation
- Users confused about interface selection

### Target State (Post-Unification)
- 4 interfaces with clear boundaries
- 0 standalone scripts (all migrated to CLI)
- 100% slash commands call CLI internally
- Unified error handling across all interfaces
- Complete interface selection guide
- <5% user confusion about interface choice

### Metrics
- Lines of duplicate code eliminated
- Number of user questions about "vibey vs /vibey"
- CLI command coverage (% of features available)
- Documentation completeness
- Cross-interface handoff success rate

---

## Conclusion

Vibey's multiple interfaces are a **strength** (flexibility) but currently suffer from **poor integration** and **unclear boundaries**. The framework would benefit significantly from:

1. **Consolidation:** Migrate standalone scripts to CLI
2. **Integration:** Make slash commands call CLI
3. **Documentation:** Clear guide on which interface to use when
4. **Standardization:** Unified error handling and UX patterns

**Recommended Next Steps:**
1. Create `interface-unification` track (5 weeks, CRITICAL priority)
2. Schedule after `platform-context-management` (or parallel if resources allow)
3. Assign: 1-2 developers, 1 technical writer
4. Target: Q1 2025 completion

---

**Document Version:** 1.0
**Created:** 2025-11-12
**Next Review:** After interface-unification track completion
