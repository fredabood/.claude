# Windsurf (Codeium) Platform Port - Implementation Plan

**Track ID:** `windsurf-port`
**Status:** Not Started
**Priority:** Medium
**Estimated Duration:** 4 weeks (2 sprints)
**Compatibility Score:** 75-80%

---

## Executive Summary

Windsurf is Codeium's "first agentic IDE" - a full-featured AI-native code editor built on a VS Code fork. The platform's Cascade agent system and native workflow support make it an excellent fit for Vibey's orchestration patterns.

**Key Stats:**
- Category: Full IDE (VS Code fork)
- Agent: Cascade (autonomous multi-step execution)
- Model: Free with BYOK + SWE-1 models
- MCP Support: Full (tools and resources)

---

## 1. Platform Architecture

### Core Components

#### Cascade Agent
The intelligent backbone of Windsurf:
- **Deep Codebase Understanding:** Indexes entire projects
- **Real-time Action Awareness:** Tracks terminal, edits, clipboard
- **Multi-file Editing:** Coherent changes across multiple files
- **Autonomous Reasoning:** Infers intent and adapts
- **Memory System:** Retains context between sessions
- **Tool Access:** 100+ integrated tools

#### Configuration Files

1. **`settings.json`** - Standard VS Code format
2. **`.windsurfrules`** - Cascade instructions (6KB individual, 12KB total)
3. **`mcp_config.json`** - MCP server configuration (`~/.codeium/windsurf/`)
4. **`.codeiumignore`** - Indexing control

#### Workflows System
- **Format:** Markdown files (`.md`)
- **Location:** `.windsurf/workflows/`
- **Invocation:** `/[workflow-name]` slash command
- **Limit:** 12,000 characters per workflow
- **Composition:** Workflows can call other workflows

---

## 2. Vibey Concept Mapping

| Vibey Concept | Windsurf Equivalent | Compatibility |
|---------------|---------------------|---------------|
| **Agents** | Cascade roles + MCP tools | Excellent |
| **Workflows** | `.windsurf/workflows/*.md` | Excellent (direct mapping!) |
| **Handoff Templates** | Cascade state/memory system | Good |
| **Quality Gates** | Cascade command suggestions + MCP | Moderate |
| **Configuration** | `.windsurfrules` + `mcp_config.json` | Good |
| **Context Files** | `.windsurfrules` (replaces CLAUDE.md) | Good |

---

## 3. Integration Points

### .windsurfrules (Project Context)

```markdown
# Project Configuration

## Tech Stack
- Language: TypeScript
- Framework: React
- Database: PostgreSQL
- Testing: Jest

## Architecture
- Monorepo structure
- API: Express.js
- Frontend: Next.js

## Code Standards
- Follow Airbnb TypeScript style guide
- Use absolute imports
- Prefer functional components
- 80% test coverage minimum

## Vibey Agents Available
- /web-developer - Full-stack development
- /test-engineer - Testing specialist
- /security-reviewer - Security audits
```

### Workflow Files

**`.windsurf/workflows/feature-development.md`:**
```markdown
# Feature Development Workflow

This workflow guides development from requirements to deployment.

## Step 1: Analyze Requirements
Understand the feature requirements and acceptance criteria.

Instructions:
- Identify affected components
- List database schema changes
- Check for breaking changes
- Plan test coverage

## Step 2: Create Test Plan
Define tests that verify the feature works.

## Step 3: Implement Feature
Write the feature code following project standards.

## Step 4: Review Code
Run /security-reviewer for security audit.

## Step 5: Deploy
Deploy to production environment.

Call /validate-deployment workflow to verify.
```

### MCP Configuration

**`~/.codeium/windsurf/mcp_config.json`:**
```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "vibey.mcp.server"],
      "env": {
        "VIBEY_PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

---

## 4. Implementation Architecture

### Directory Structure

```
.windsurf/
├── workflows/
│   ├── feature-development.md
│   ├── sprint-planning.md
│   ├── security-audit.md
│   └── performance-optimization.md
├── rules/
│   ├── backend-engineer.md
│   ├── frontend-engineer.md
│   ├── test-engineer.md
│   └── security-reviewer.md
├── settings.json
└── mcp_config.json (optional)

(Root project directory)
├── .windsurfrules (main project instructions)
└── .windsurf/ (as above)
```

### Adapter Class

```python
class WindsurfAdapter(PlatformAdapter):
    """Windsurf platform deployment adapter."""

    def get_platform_name(self) -> str:
        return "windsurf"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".windsurf"

    def deploy(self, source_dir: Path, config: Any) -> DeploymentResult:
        # 1. Create .windsurf/ structure
        # 2. Generate .windsurfrules
        # 3. Convert workflows to markdown
        # 4. Create agent rules
        # 5. Generate settings.json
        # 6. Create mcp_config.json (optional)
        pass
```

---

## 5. Sprint Plan

### Sprint 1: Windsurf Adapter & Cascade Integration (2 weeks)

#### Task 1: Create WindsurfAdapter class (2-3 days)
- Extend `PlatformAdapter` base class
- Implement deployment to `.windsurf/` directory
- Handle file generation

#### Task 2: .windsurfrules generation (2-3 days)
- Template for project context
- Tech stack extraction from config
- Code standards integration
- Character limit handling (6KB)

#### Task 3: Workflow → Markdown conversion (2-3 days)
- Convert Vibey workflows to Cascade workflow format
- Handle multi-step instructions
- Implement workflow composition (calling other workflows)
- Character limit handling (12KB)

#### Task 4: Agent rules generation (1-2 days)
- Convert agents to `.windsurf/rules/*.md`
- Activation mode configuration
- Glob pattern support

#### Task 5: Settings and MCP config (1 day)
- `settings.json` template
- `mcp_config.json` template (optional)

#### Task 6: Unit tests (2 days)
- Test deployment logic
- Validate markdown generation
- Verify character limits respected

#### Task 7: Manual testing with Windsurf (1-2 days)
- Deploy to real Windsurf IDE
- Execute workflows in Cascade
- Verify context preservation

---

### Sprint 2: Agentic Workflow & VS Code Compatibility (2 weeks)

#### Task 1: Advanced Cascade integration (2-3 days)
- Multi-step workflow optimization
- State passing between workflow steps
- Quality gate checkpoints

#### Task 2: MCP tool wrapper (optional) (2-3 days)
- Wrap select Vibey agents as MCP tools
- Return structured results to Cascade
- Test tool invocation

#### Task 3: VS Code compatibility testing (2 days)
- Verify VS Code extension compatibility
- Test with VS Code settings import
- Document differences

#### Task 4: Integration tests (2 days)
- End-to-end deployment tests
- Workflow execution tests
- MCP integration tests

#### Task 5: Documentation (2 days)
- Windsurf adapter guide
- Workflow best practices for Cascade
- Migration guide (VS Code → Windsurf)

#### Task 6: Example projects (1-2 days)
- Web-app example with Windsurf
- API project example
- Full workflow demonstration

---

## 6. Technical Decisions

### Workflow Format: Markdown
Windsurf workflows are natively markdown - direct mapping from Vibey!

```python
def generate_workflow(vibey_workflow, config):
    """Convert Vibey workflow to Windsurf workflow markdown."""

    steps = []
    for i, step in enumerate(vibey_workflow.steps, 1):
        step_md = f"""
## Step {i}: {step.name}

Agent: {step.agent.name}
Role: {step.agent.role}

Instructions for Cascade:
{step.description}

Expected Output:
{step.expected_output}
"""
        steps.append(step_md)

    return f"""
# {vibey_workflow.name}

{vibey_workflow.description}

{''.join(steps)}

---

## Validation Checklist
{generate_quality_gates(vibey_workflow.quality_gates)}
"""
```

### Agent Mapping: Rules + System Prompts
```markdown
# .windsurf/rules/web-developer.md

name: Web Developer
activation: automatic
scope: "**/*.{ts,tsx,js,jsx}"
description: "Full-stack web development specialist"

## Instructions
You are a Web Developer specialized in React and Node.js.
Follow these guidelines:
- Use TypeScript for type safety
- Follow React best practices
- Write comprehensive tests
```

### Quality Gates: Workflow Checkpoints
Since Windsurf doesn't have native quality gates, implement as workflow steps:
```markdown
## Validation Checkpoint

Before proceeding, verify:
- [ ] All tests pass
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] Code review complete

Run `/quality-check` workflow to validate.
```

---

## 7. Quality Gates

### Gate 1: Comprehensive Testing (100% threshold)
- All journey tests pass
- Platform deployment tests pass
- >95% platform parity

### Gate 2: Cascade Agent Integration (90% threshold)
- Workflows execute correctly in Cascade
- Multi-step operations work
- Context preserved across steps

### Gate 3: Agentic Workflow Testing (90% threshold)
- Complex workflows complete successfully
- Quality checkpoints trigger correctly
- State management works

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Workflow Size Limits (12KB)** | Medium | Split complex workflows into sub-workflows |
| **Rule Character Limits (6KB)** | Medium | Distribute rules across multiple files |
| **MCP Tool Limit (100 tools)** | Low | Prioritize high-value tools |
| **Cascade Memory Persistence** | Medium | Design stateless workflows where possible |
| **Version Compatibility** | Medium | Test with recent versions; document requirements |

---

## 9. Deliverables Checklist

### Core Implementation
- [ ] `vibey/adapters/windsurf.py` - WindsurfAdapter class
- [ ] `templates/windsurf/windsurfrules.j2` - Project context template
- [ ] `templates/windsurf/workflow.md.j2` - Workflow template
- [ ] `templates/windsurf/agent-rule.md.j2` - Agent rule template
- [ ] `templates/windsurf/settings.json.j2` - Settings template
- [ ] `templates/windsurf/mcp_config.json.j2` - MCP config template

### Testing
- [ ] `tests/adapters/test_windsurf.py` - Unit tests
- [ ] `tests/integration/test_windsurf_deployment.py` - Integration tests

### Documentation
- [ ] `docs/guides/WINDSURF_INTEGRATION.md` - User guide
- [ ] `docs/guides/WINDSURF_WORKFLOWS.md` - Workflow guide
- [ ] Example projects

---

## 10. Success Criteria

1. **Functional Deployment**
   - `vibey deploy --platform windsurf` creates valid `.windsurf/` directory
   - `.windsurfrules` loads in Windsurf
   - All workflows accessible via `/workflow-name`

2. **Cascade Integration**
   - Workflows execute in Cascade
   - Multi-step operations work
   - Agent rules apply correctly

3. **Quality Integration**
   - Quality checkpoints in workflows
   - MCP tools for validation (optional)
   - State management across steps

4. **Documentation**
   - Complete user guide
   - Workflow examples
   - VS Code migration guide

---

## References

- [Windsurf Documentation](https://docs.windsurf.com/windsurf/getting-started)
- [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
- [Windsurf MCP Integration](https://docs.windsurf.com/windsurf/cascade/mcp)
- [Windsurf Rules Directory](https://windsurf.com/editor/directory)
- [Configuring MCP Servers](https://windsurf.com/university/tutorials/configuring-first-mcp-server)

---

**Last Updated:** 2025-11-22
**Author:** Vibey Framework Team
