# Cursor Platform Port - Implementation Plan

**Track ID:** cursor-port
**Status:** Not Started
**Priority:** High (native MCP support enables direct integration)
**Created:** 2025-11-23
**Last Updated:** 2025-11-23 (Research Update)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Research Findings](#research-findings)
3. [Infrastructure Reuse Assessment](#infrastructure-reuse-assessment)
4. [Architecture Decisions](#architecture-decisions)
5. [Sprint Tasks](#sprint-tasks)
6. [Risk Assessment](#risk-assessment)
7. [Sources](#sources)

---

## Executive Summary

### Key Finding: Native MCP Support - No Paradigm Mismatch

**RESEARCH UPDATE (November 2025):** Cursor IDE has **full native MCP support** including tools, resources, prompts, and multiple transports. This completely eliminates the previously identified "paradigm mismatch" concern.

**Final Assessment:** 85-95% compatibility, 60-100 hours (2-3 weeks), low risk

### Strategic Recommendation

**Approach:** Direct MCP Integration (same as Windsurf, Continue.dev)

1. **Sprint 1 (1.5 weeks):** Create CursorAdapter with MCP config generation
2. **Sprint 2 (1 week):** Testing and documentation

**Why Direct Integration Works:**
- Cursor supports full MCP protocol (tools, resources, prompts)
- Config format `.cursor/mcp.json` matches Claude Desktop pattern
- Project-level configuration with variable interpolation
- Multiple transports: stdio, SSE, Streamable HTTP
- One-click server installation with OAuth support

---

## Research Findings

### Cursor 2.0 Architecture (Released October 29, 2025)

#### Composer Model
- Proprietary frontier coding model trained with RL
- Mixture-of-experts architecture
- 4x faster than similarly intelligent models
- Trained in an agentic setting with tools (semantic search, edit, test)
- Optimized for short interaction cycles (< 30 seconds per turn)

#### Multi-Agent System
- Up to 8 agents running in parallel per prompt
- Git worktree isolation prevents file conflicts
- Each agent operates in isolated codebase copy
- Agents can attempt same problem, user picks best result

#### Key Capabilities
- Sandboxed terminals (GA on macOS)
- DOM reading for frontend testing
- End-to-end test running in editor
- Native file, terminal, browser, and search tools

### .cursor/ and .cursorrules Format

#### Project Rules (Modern - Recommended)
- Location: `.cursor/rules/`
- Format: `.mdc` files (Markdown Domain Configuration)
- Frontmatter support with glob patterns:
  ```yaml
  ---
  Description: Rails Controller Standards
  Globs: app/controllers/**/*.rb
  alwaysApply: false
  ---
  ```
- Supports file pattern targeting
- Version controlled and project-scoped

#### Legacy .cursorrules
- Single file in project root
- Still supported but deprecated
- Plain markdown format

#### User Rules (Global)
- Location: Cursor Settings > Rules
- Applied to all projects
- Plain text only (no MDC)

### MCP Support in Cursor (CONFIRMED - Nov 2025)

#### Full Protocol Support
Cursor supports the complete MCP specification:
- **Tools:** Functions for AI model execution (primary use case)
- **Resources:** Structured, referenceable data sources
- **Prompts:** Templated messages and workflows
- **Roots:** Server-initiated URI/filesystem inquiries
- **Elicitation:** Server-initiated user information requests

#### Transport Types
- **stdio:** Local development (PRIMARY - Cursor-managed process)
- **SSE:** Server-sent events for distributed teams
- **Streamable HTTP:** Flexible distributed access with OAuth

#### Configuration Format
```json
// .cursor/mcp.json (project-level)
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_ROADMAP_ROOT": "${workspaceFolder}/.vibey/roadmap"
      }
    }
  }
}
```

#### Variable Interpolation
- `${env:NAME}` - Environment variables
- `${userHome}` - User home directory
- `${workspaceFolder}` - Project root
- `${workspaceFolderBasename}` - Project name
- `${pathSeparator}` / `${/}` - OS-specific paths

#### Key Benefit for Vibey
- Direct reuse of existing MCP server (46 tools)
- Same config pattern as Claude Desktop
- No paradigm adaptation required

### Parallel Execution Model

#### How It Works
1. User submits prompt to up to 8 agents
2. Each agent gets isolated git worktree
3. Agents work independently without file conflicts
4. User reviews and compares outputs
5. Best solution selected and merged

#### Use Cases
- Same task to different models (compare results)
- Parallel feature development (A, B, C simultaneously)
- "What-if" exploration at scale
- Refactor variants or testing pipelines

#### Limitations
- Maximum 8 agents
- Requires git worktree setup
- Sandboxed terminal has no internet access by default
- Large codebases with strict standards may be challenging

---

## Paradigm Mismatch Analysis

### Core Conflict: Sequential vs Parallel

| Aspect | Vibey Workflows | Cursor Agents |
|--------|-----------------|---------------|
| Execution | Sequential steps | Parallel agents |
| Dependencies | Explicit (step N requires step N-1) | Implicit (worktree isolation) |
| Handoffs | Structured (templates) | Merged (git) |
| Orchestration | Coordinator agent | User selection |
| Quality Gates | Blocking between steps | Post-merge validation |

### Impact Assessment

#### HIGH Impact (Requires Redesign)

1. **Sequential Workflows**
   - Vibey: Step 1 -> Step 2 -> Step 3 (strict order)
   - Cursor: Agent A, B, C (parallel), then merge
   - **Solution:** Identify parallelizable steps, restructure as DAG

2. **Agent Coordination**
   - Vibey: Coordinator routes to specialized agents
   - Cursor: User assigns tasks to parallel agents
   - **Solution:** Create "plan" files that define agent coordination

3. **Handoff Templates**
   - Vibey: Structured output -> structured input
   - Cursor: Git merge of isolated changes
   - **Solution:** Use shared context files instead of handoffs

#### MEDIUM Impact (Adaptation Required)

4. **Quality Gates**
   - Vibey: Blocking gates between workflow steps
   - Cursor: No built-in gate concept
   - **Solution:** Gate validation agents that run post-merge

5. **Context Management**
   - Vibey: CLAUDE.md auto-read, per-agent context
   - Cursor: .cursorrules, MCP tools for context
   - **Solution:** Generate .cursorrules from Vibey config

#### LOW Impact (Natural Fit)

6. **MCP Integration**
   - Vibey: Full MCP server with 46 tools
   - Cursor: Native MCP support
   - **Solution:** Direct integration (major win)

7. **Agent Instructions**
   - Vibey: Markdown agent files with frontmatter
   - Cursor: .mdc rules with frontmatter
   - **Solution:** Generate .mdc from agent markdown

### Mitigation Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│ PARADIGM ADAPTATION APPROACH                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Vibey Sequential:    Step1 → Step2 → Step3 → Step4             │
│                                                                  │
│  Cursor Parallel:     ┌─ Agent A ─┐                             │
│                       │           │                              │
│                       ├─ Agent B ─┼──→ Merge → Validate         │
│                       │           │                              │
│                       └─ Agent C ─┘                             │
│                                                                  │
│  Hybrid (Vibey-Cursor):                                         │
│                                                                  │
│     Phase 1 (Setup):  MCP context load                          │
│           ↓                                                      │
│     Phase 2 (Parallel): ┌─ Agent A ─┐                           │
│                         ├─ Agent B ─┤                           │
│                         └─ Agent C ─┘                           │
│           ↓                                                      │
│     Phase 3 (Gate):    Quality validation via MCP               │
│           ↓                                                      │
│     Phase 4 (Parallel): ┌─ Agent D ─┐                           │
│                         └─ Agent E ─┘                           │
│           ↓                                                      │
│     Phase 5 (Gate):    Final validation via MCP                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Infrastructure Reuse Assessment

### Direct Reuse (Zero Modification)

| Component | Path | Reuse |
|-----------|------|-------|
| MCP Server | `framework/mcp/server.py` | 100% |
| Tool Discovery | `framework/mcp/discovery/` | 100% |
| Roadmap Operations | `vibey/operations/roadmap/` | 100% |
| CLI Commands | `vibey/cli/` | 100% |
| Error Handling | `vibey/common/errors.py` | 100% |
| Config Loader | `vibey/config/loader.py` | 100% |

### Adaptation Required

| Component | Path | Adaptation |
|-----------|------|------------|
| Base Adapter | `vibey/adapters/base.py` | CursorAdapter subclass |
| Goose Adapter (reference) | `vibey/adapters/goose.py` | Pattern for Cursor |
| Agent Frontmatter | `framework/agents/*.md` | Generate .mdc rules |
| Workflow Frontmatter | `framework/workflows/*.md` | Parallel step mapping |

### New Development Required

| Component | Description | Effort |
|-----------|-------------|--------|
| CursorAdapter | Platform adapter for .cursor/ | 40-60 hours |
| Rules Generator | YAML frontmatter -> .mdc | 20-30 hours |
| Parallel Mapper | Workflow steps -> parallel phases | 30-50 hours |
| MCP Config Generator | .cursor/mcp.json generation | 10-15 hours |

### MCP Server Integration

The existing Vibey MCP server provides 46 tools:

**Roadmap Tools (Static):**
- Task management: start, complete, query
- Sprint management: start, complete, query
- Query tools: roadmap status, blockers, dependencies

**Agent Tools (Dynamic from frontmatter):**
- 12 specialized agents as MCP tools
- Auto-discovered from `framework/agents/*.md`

**Workflow Tools (Dynamic from frontmatter):**
- 16 workflows as MCP tools
- Auto-discovered from `framework/workflows/*.md`

**Cursor Integration Method:**
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_ROADMAP_ROOT": ".vibey/roadmap"
      }
    }
  }
}
```

---

## POC Success Criteria

### Sprint 1: POC & Paradigm Validation (4 weeks)

#### Go/No-Go Gate Criteria

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| MCP Integration | 100% | All 46 tools accessible in Cursor |
| Composer Instruction Following | 80% | Agent instructions followed accurately |
| Parallel Workflow Execution | 1 workflow | Successfully run parallelized workflow |
| Quality Gate Enforcement | 1 gate | Gate blocks until criteria met |
| Context Persistence | 100% | Session state maintained via MCP |

#### POC Deliverables

1. **MCP Integration Test**
   - Vibey MCP server running in Cursor
   - All tools callable
   - Roadmap operations functional

2. **Single Agent Test**
   - One agent converted to .mdc format
   - Agent instructions followed by Composer
   - Quality criteria validated

3. **Parallel Workflow Test**
   - One workflow converted to parallel phases
   - Multiple agents execute simultaneously
   - Results merge correctly

4. **Quality Gate Test**
   - Gate agent validates work
   - Blocks progression on failure
   - Passes on criteria met

#### Decision Matrix

| POC Results | Decision |
|-------------|----------|
| 4/4 criteria pass | Proceed to Sprint 2 |
| 3/4 criteria pass | Re-scope, address gaps, re-test |
| 2/4 criteria pass | Pause, investigate paradigm issues |
| <2 criteria pass | Abort port, focus on other platforms |

### Fallback Plan

If POC fails:
1. Document lessons learned
2. Identify specific failure points
3. Update FRAMEWORK_ROADMAP.md with findings
4. Reallocate resources to Goose/Aider ports
5. Revisit when Cursor 3.0 or major updates ship

---

## Architecture Decisions

### ADR-001: MCP-First Integration

**Status:** Proposed
**Context:** Cursor supports MCP natively; Vibey has full MCP server
**Decision:** Use MCP as primary integration layer, not rules-only
**Consequences:**
- Immediate access to all Vibey functionality
- Reduced paradigm mismatch impact
- Dynamic tool discovery works out-of-box

### ADR-002: Hybrid Sequential-Parallel Model

**Status:** Proposed
**Context:** Vibey workflows are sequential; Cursor is parallel-first
**Decision:** Introduce "phases" - sequential between phases, parallel within
**Consequences:**
- Workflow restructuring required
- Quality gates become phase boundaries
- Dependencies become phase ordering

### ADR-003: Zero-Drift .cursorrules Generation

**Status:** Proposed
**Context:** Must maintain single source of truth in .vibey/
**Decision:** Generate all .cursor/ artifacts from YAML frontmatter
**Consequences:**
- CursorAdapter generates .mdc files
- No manual editing of .cursor/ contents
- CI/CD can validate drift

### ADR-004: Parallel Step Mapping

**Status:** Proposed
**Context:** Need to map sequential workflow steps to parallel execution
**Decision:** Add `parallel_group` field to workflow step frontmatter
**Consequences:**
- Steps with same group execute in parallel
- Groups execute sequentially
- Existing workflows get sensible defaults

Example:
```yaml
steps:
- order: 1
  name: Setup Environment
  parallel_group: 1  # Sequential (alone in group)
- order: 2
  name: Write Backend
  parallel_group: 2  # Parallel
- order: 3
  name: Write Frontend
  parallel_group: 2  # Parallel (same group as step 2)
- order: 4
  name: Write Tests
  parallel_group: 2  # Parallel (same group as steps 2-3)
- order: 5
  name: Quality Review
  parallel_group: 3  # Sequential gate
```

---

## Sprint Tasks

### Sprint 1: POC & Paradigm Validation (4 weeks)

#### Week 1: MCP Integration

| Task | Hours | Description |
|------|-------|-------------|
| 1.1 | 4 | Set up Cursor dev environment |
| 1.2 | 8 | Create .cursor/mcp.json configuration |
| 1.3 | 12 | Test Vibey MCP server in Cursor |
| 1.4 | 8 | Debug and fix any MCP transport issues |
| 1.5 | 4 | Document MCP integration findings |

**Week 1 Gate:** MCP server accessible with all tools

#### Week 2: Agent Conversion Test

| Task | Hours | Description |
|------|-------|-------------|
| 2.1 | 8 | Create CursorAdapter skeleton |
| 2.2 | 12 | Implement .mdc rule generator |
| 2.3 | 8 | Convert test-engineer agent to .mdc |
| 2.4 | 8 | Validate Composer follows instructions |
| 2.5 | 4 | Document agent conversion findings |

**Week 2 Gate:** One agent functional in Cursor

#### Week 3: Parallel Workflow Test

| Task | Hours | Description |
|------|-------|-------------|
| 3.1 | 8 | Design parallel step mapping schema |
| 3.2 | 12 | Implement parallel group parser |
| 3.3 | 12 | Convert single-feature-development workflow |
| 3.4 | 8 | Test parallel execution |

**Week 3 Gate:** Parallelized workflow completes

#### Week 4: Quality Gate Test & Decision

| Task | Hours | Description |
|------|-------|-------------|
| 4.1 | 8 | Implement gate validation agent |
| 4.2 | 8 | Test gate blocking behavior |
| 4.3 | 8 | Run full POC scenario end-to-end |
| 4.4 | 8 | Compile POC report |
| 4.5 | 8 | Go/No-Go decision meeting |

**Week 4 Gate:** All POC criteria evaluated, decision made

### Sprint 2: Agent Reimplementation (Conditional - 4 weeks)

**Only if Sprint 1 POC passes**

| Task | Hours | Description |
|------|-------|-------------|
| 2.1 | 40 | Convert remaining 11 agents to .mdc |
| 2.2 | 20 | Create agent type-specific templates |
| 2.3 | 20 | Implement agent routing via MCP |
| 2.4 | 20 | Test all agents in Cursor |
| 2.5 | 20 | Document agent adaptations |

### Sprint 3: Workflow Restructuring (Conditional - 4 weeks)

**Only if Sprint 1 POC passes**

| Task | Hours | Description |
|------|-------|-------------|
| 3.1 | 40 | Add parallel_group to all workflows |
| 3.2 | 30 | Implement parallel workflow executor |
| 3.3 | 20 | Create workflow migration guide |
| 3.4 | 20 | Test all 16 workflows |
| 3.5 | 10 | Final documentation |

---

## Risk Assessment

### High Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Composer ignores instructions | Medium | Critical | POC validation, prompt engineering |
| Parallel model incompatible | Medium | Critical | Hybrid phase model, fallback to sequential |
| MCP transport issues | Low | High | Test all transport types in POC |

### Medium Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Quality gates ineffective | Medium | Medium | Gate validation agent design |
| Context loss between phases | Medium | Medium | MCP state persistence |
| Workflow restructuring complex | High | Medium | Incremental migration |

### Low Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| .mdc format changes | Low | Low | Generate from frontmatter |
| Cursor updates break integration | Low | Medium | Version pinning |
| User adoption challenges | Medium | Low | Clear migration guide |

### Risk Probability Matrix

```
           IMPACT
           Low    Medium   High    Critical
       ┌────────┬────────┬────────┬────────┐
High   │        │Workflow│        │        │
       │        │restrct │        │        │
       ├────────┼────────┼────────┼────────┤
Medium │User    │Context │        │Composer│
L      │adopt   │loss    │        │instrct │
I      │        │        │        │Parallel│
K      ├────────┼────────┼────────┼────────┤
E      │        │Cursor  │MCP     │        │
Low    │MDC fmt │updates │transp  │        │
       └────────┴────────┴────────┴────────┘
```

---

## Timeline Summary (UPDATED)

| Phase | Duration | Key Outcome |
|-------|----------|-------------|
| Sprint 1: Core Adapter & MCP | 1.5 weeks | Adapter, generators, CLI command |
| Sprint 2: Testing & Docs | 1 week | E2E tests, integration guide |
| **Total** | **2-3 weeks** | Full Cursor port |

**Estimated Effort:** 60-100 hours
**Team Size:** 1-2 developers
**Dependencies:** multi-platform track (completed)

**Note:** Original 12-week POC-based estimate was based on outdated "paradigm mismatch"
assessment. With native MCP support confirmed, Cursor follows the same integration
pattern as Windsurf and Continue.dev.

---

## Sources

### Cursor Architecture & Composer
- [Cursor 2.0 Blog Post](https://cursor.com/blog/2-0)
- [Cursor 2.0 Changelog](https://cursor.com/changelog/2-0)
- [Cursor 2.0 Multi-Agent Guide](https://www.artezio.com/pressroom/blog/revolutionizes-architecture-proprietary/)
- [InfoQ Cursor Coverage](https://www.infoq.com/news/2025/11/cursor-composer-multiagent/)

### .cursorrules Format
- [Cursor Rules Documentation](https://docs.cursor.com/context/rules)
- [Cursor Rules for AI](https://docs.cursor.com/context/rules-for-ai)
- [Awesome Cursorrules Collection](https://github.com/PatrickJS/awesome-cursorrules)

### MCP Support
- [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol)
- [MCP Introduction (Phil Schmid)](https://www.philschmid.de/mcp-introduction)
- [MCP Integration Guide](https://steveshao.com/posts/2025/note-use-mcp-for-cursor/)

### Parallel Execution
- [Cursor Parallel Agents Docs](https://cursor.com/docs/configuration/worktrees)
- [Git Worktrees Explanation](https://dev.to/arifszn/git-worktrees-the-power-behind-cursors-parallel-agents-19j1)

---

## Appendix A: MCP Server Tools Reference

```
Vibey MCP Server - 46 Tools

ROADMAP TOOLS (Static):
- vibey_start_task
- vibey_complete_task
- vibey_query_task
- vibey_start_sprint
- vibey_complete_sprint
- vibey_query_sprint
- vibey_query_track
- vibey_roadmap_status
- vibey_list_blockers
- vibey_list_dependencies
- vibey_refresh_progress

AGENT TOOLS (Dynamic - 12):
- vibey_documentation_maintenance_engineer
- vibey_git_committer
- vibey_documentation_engineer
- vibey_diagram_engineer
- vibey_vibey_manager
- vibey_coordinator
- vibey_security_reviewer
- vibey_test_engineer
- vibey_performance_engineer
- vibey_observability_engineer
- vibey_ml_engineer
- vibey_web_developer

WORKFLOW TOOLS (Dynamic - 16):
- vibey_workflow_integration_only
- vibey_workflow_frontend_production_deployment
- vibey_workflow_sprint_planning
- vibey_workflow_documentation_research
- vibey_workflow_performance_optimization
- vibey_workflow_infrastructure_setup
- vibey_workflow_logging_audit
- vibey_workflow_dashboard_visualization_creation
- vibey_workflow_ml_model_development
- vibey_workflow_frontend_security_hardening
- vibey_workflow_weekly_sprint
- vibey_workflow_architecture_review
- vibey_workflow_claude_md_auto_update
- vibey_workflow_single_feature_development
- vibey_workflow_documentation_diagrams
- vibey_workflow_codebase_audit_discovery

+ Additional planning/research/specialist agents
```

---

## Appendix B: CursorAdapter Interface

```python
class CursorAdapter(PlatformAdapter):
    """
    Adapter for Cursor IDE.

    Deploys Vibey framework to .cursor/ directory with:
    - .cursor/rules/*.mdc (agent and context rules)
    - .cursor/mcp.json (MCP server configuration)
    - .cursorrules (legacy, optional)
    """

    def get_platform_name(self) -> str:
        return "cursor"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".cursor"

    def deploy(self, source_dir: Path, config: Any, ...) -> DeploymentResult:
        # 1. Generate .cursor/mcp.json
        # 2. Generate .cursor/rules/*.mdc from agents
        # 3. Generate parallel workflow mappings
        # 4. Validate deployment
        pass

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        # Generate .cursorrules with project context
        pass

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        # Validate .cursor/ structure
        pass

    def supports_feature(self, feature: str) -> bool:
        # Cursor supports:
        # - workflows (via parallel phases)
        # - agents (via .mdc rules)
        # - quality-gates (via gate agents)
        # - roadmap (via MCP tools)
        # - templates (via .mdc generation)
        pass
```

---

**Document Version:** 1.0.0
**Author:** Vibey Framework Team
**Review Date:** Before Sprint 1 kickoff
