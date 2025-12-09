# Windsurf/Codeium Platform Port - Implementation Plan

**Document Version:** 1.0.0
**Created:** 2025-11-23
**Track ID:** `windsurf-port`
**Status:** Research Complete - Ready for Implementation
**Estimated Duration:** 4 weeks (2 sprints)

---

## Executive Summary

This implementation plan details how to port the Vibey Agent Framework to the Windsurf IDE (formerly Codeium). Windsurf is positioned as the "first agentic IDE" with its Cascade AI system that provides deep codebase understanding and multi-file editing capabilities.

**Key Finding:** Windsurf has **native MCP support** with the same configuration schema as Claude Desktop, meaning the existing Vibey MCP server can be reused directly with minimal adaptation.

**Strategic Value:**
- First-mover advantage in the "agentic IDE" category
- Cascade's multi-step execution complements Vibey's orchestration
- Free BYOK model makes adoption accessible
- 100-tool limit aligns well with Vibey's ~46 tools

---

## Research Findings

### Platform Overview

**Windsurf IDE** is built by Codeium, featuring:
- **Cascade** - AI assistant with deep codebase understanding and real-time awareness
- **Flow Awareness** - Maintains shared temporal context with the developer
- **SWE-1 Models** - Suite of models trained specifically on software engineering logic
- **VS Code Fork** - Electron/Rust-based with VS Code extension compatibility

### MCP Integration (Critical)

Windsurf supports MCP natively through Cascade with the following characteristics:

| Feature | Support Status | Notes |
|---------|---------------|-------|
| Tools | Supported | Primary integration point |
| Resources | Supported | Data access capabilities |
| Prompts | NOT Supported | Limitation vs Claude |
| Transport: stdio | Supported | Default for local servers |
| Transport: HTTP/SSE | Supported | For remote servers |
| Authentication | Supported | OAuth flows available |
| Tool Limit | 100 max | Per-session limit |

**Configuration Location:**
- macOS: `~/.codeium/windsurf/mcp_config.json`
- Windows: `%USERPROFILE%\.codeium\windsurf\mcp_config.json`

**Configuration Schema:** Uses **identical format to Claude Desktop**:
```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

### Rules System

Windsurf uses a **rules-based context system** with two mechanisms:

1. **Workspace Rules** (`.windsurf/rules/*.md`)
   - Markdown files with natural language instructions
   - Tied to file patterns (globs) or natural language descriptions
   - 6,000 character limit per rule file
   - 12,000 character total limit (global + workspace)
   - Four activation modes: Manual, Always On, Model Decision, Auto

2. **Legacy Rules** (`.windsurfrules`)
   - Single file at project root
   - Simpler format with numbered instructions
   - Compatible with existing `.cursorrules` patterns

**Rule Activation Modes:**
| Mode | Behavior |
|------|----------|
| Manual | Activated by @mentioning in Cascade input |
| Always On | Always applied to all requests |
| Model Decision | AI decides based on natural language description |
| Auto | Activated when file patterns match |

### Cascade Agent Architecture

Cascade operates with two modes:
- **Write Mode** - Direct code edits
- **Chat Mode** - Discussion and planning

Cascade's transformer-based NLP translates prompts into AST-aware edits, making it ideal for Vibey's workflow orchestration where each step produces code changes.

---

## Architecture Decisions

### Decision 1: Direct MCP Reuse

**Decision:** Reuse the existing Vibey MCP server at `framework/mcp/server.py` directly.

**Rationale:**
- Windsurf uses identical MCP config schema as Claude Desktop
- 46 Vibey tools fits well under 100-tool limit
- Eliminates translation layer complexity
- Proven stability from Claude Code and Goose deployments

**Implementation:**
```python
# No changes to framework/mcp/server.py needed
# Windsurf reads standard MCP protocol
```

### Decision 2: Adapter Pattern Extension

**Decision:** Create `WindsurfAdapter` as a composite adapter that extends the base MCP integration.

**Rationale:**
- Follows established pattern from `GeminiAdapter`, `GooseAdapter`
- Adds Windsurf-specific artifacts (rules, context files)
- Maintains zero-drift from frontmatter source of truth

**File:** `vibey/adapters/windsurf/adapter.py`

### Decision 3: Rules Generation Strategy

**Decision:** Generate `.windsurf/rules/` from agent and workflow frontmatter.

**Mapping:**
| Vibey Asset | Windsurf Output | Purpose |
|-------------|-----------------|---------|
| Agent frontmatter | `.windsurf/rules/{agent}.md` | Agent-specific context |
| Workflow frontmatter | `.windsurf/rules/{workflow}.md` | Workflow guidance |
| Project config | `.windsurfrules` (root) | Global context |

**Example Generated Rule:**
```markdown
---
trigger:
  type: model_decision
  description: When building web user interfaces or frontend components
---

# Web Developer Agent

**Role:** Build and maintain web applications for user-facing interfaces

## Trigger Context
- Keywords: frontend, UI, user interface, web app, dashboard, React, Vue
- File Patterns: src/components/*, src/pages/*, *.tsx, *.jsx, *.vue, *.css

## Responsibilities
- Analyze sprint requirements for web interface needs
- Design user interface and user experience
- Build web applications (frontend and/or backend)
- Integrate with backend services and data sources

## Quality Criteria
- Responsive design implementation
- Accessibility compliance (WCAG 2.1)
- Performance optimization (Core Web Vitals)
- Cross-browser compatibility
```

### Decision 4: Zero-Drift Implementation

**Decision:** All Windsurf artifacts are generated from `.vibey/` source with checksums for drift detection.

**Components:**
1. **Source of Truth:** YAML frontmatter in `framework/agents/*.md` and `framework/workflows/*.md`
2. **Generated Artifacts:** `.windsurf/rules/`, `.windsurfrules`, `mcp_config.json`
3. **Drift Detection:** `.windsurf/.checksums.json` with SHA256 hashes
4. **CI Validation:** `vibey export windsurf --validate` command

---

## MCP Reuse Strategy

### Existing Infrastructure

The Vibey MCP server provides 46 tools:
- 19 agent tools (from `framework/agents/`)
- 16 workflow tools (from `framework/workflows/`)
- 11 roadmap management tools (static)

### Windsurf Integration Path

```
~/.codeium/windsurf/mcp_config.json
           │
           ▼
    ┌─────────────────────┐
    │   Vibey MCP Server   │ ← framework/mcp/server.py
    │   (46 tools)         │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │                      │
    ▼                      ▼
  Cascade             ToolDiscovery
(MCP Client)         (Agent/Workflow
                      from frontmatter)
```

### Configuration Generation

The adapter generates a user-installable config snippet:

```python
def generate_mcp_config(self, project_root: Path) -> dict:
    """Generate mcp_config.json entry for Windsurf."""
    return {
        "mcpServers": {
            "vibey": {
                "command": sys.executable,
                "args": ["-m", "framework.mcp.server"],
                "env": {
                    "VIBEY_PROJECT_ROOT": str(project_root),
                    "VIBEY_ROADMAP_ROOT": str(project_root / ".vibey" / "roadmap")
                }
            }
        }
    }
```

---

## Adapter Design

### Class Hierarchy

```
PlatformAdapter (base.py)
       │
       ├── ClaudeCodeAdapter (claude_code.py)
       ├── GooseAdapter (goose.py)
       ├── AiderAdapter (aider.py)
       ├── GeminiAdapter (gemini/)
       │
       └── WindsurfAdapter (windsurf/)  ← NEW
              ├── RuleGenerator
              ├── ContextGenerator
              └── ConfigGenerator
```

### WindsurfAdapter Structure

```
vibey/adapters/windsurf/
├── __init__.py
├── adapter.py           # Main WindsurfAdapter class
├── rule_generator.py    # .windsurf/rules/ generation
├── context_generator.py # .windsurfrules generation
├── config_generator.py  # MCP config generation
└── tests/
    ├── __init__.py
    ├── test_adapter.py
    ├── test_rule_generator.py
    └── test_context_generator.py
```

### Core Implementation

```python
class WindsurfAdapter(PlatformAdapter):
    """
    Adapter for Windsurf IDE (Codeium).

    Deploys Vibey framework to Windsurf with:
    - MCP server configuration (direct reuse)
    - .windsurf/rules/ (agent/workflow context)
    - .windsurfrules (global project context)

    Zero-Drift Architecture:
    All artifacts generated from frontmatter, checksums tracked.
    """

    def get_platform_name(self) -> str:
        return "windsurf"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".windsurf"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy to Windsurf.

        Steps:
        1. Generate .windsurf/rules/ from agents/workflows
        2. Generate .windsurfrules (global context)
        3. Generate MCP config snippet
        4. Write checksums manifest
        5. Validate deployment
        """
        # Implementation follows established adapter pattern
```

---

## Sprint Plan

### Sprint 1: Windsurf Adapter & Cascade Integration (2 weeks)

**Goal:** Core adapter with MCP integration and rule generation

#### Task 1.1: Create WindsurfAdapter Base Class
**Duration:** 2-3 days
**Files:**
- `vibey/adapters/windsurf/__init__.py` (new)
- `vibey/adapters/windsurf/adapter.py` (new)
**Acceptance Criteria:**
- [ ] Extends `PlatformAdapter` base class
- [ ] Implements all abstract methods
- [ ] Generates `.windsurf/` directory structure
- [ ] Includes pre/post deploy hooks

#### Task 1.2: Implement RuleGenerator
**Duration:** 3-4 days
**Files:**
- `vibey/adapters/windsurf/rule_generator.py` (new)
**Acceptance Criteria:**
- [ ] Parses agent frontmatter to rules
- [ ] Parses workflow frontmatter to rules
- [ ] Respects 6,000 char per-rule limit
- [ ] Generates correct activation mode metadata
- [ ] Creates `.windsurf/rules/agents/` directory
- [ ] Creates `.windsurf/rules/workflows/` directory

#### Task 1.3: Implement ContextGenerator
**Duration:** 2 days
**Files:**
- `vibey/adapters/windsurf/context_generator.py` (new)
**Acceptance Criteria:**
- [ ] Generates `.windsurfrules` at project root
- [ ] Includes project name, type, tech stack
- [ ] Lists available agents and workflows
- [ ] Respects 12,000 char total limit
- [ ] Includes `VIBEY_FRAMEWORK_MANAGED` marker

#### Task 1.4: Implement ConfigGenerator
**Duration:** 2 days
**Files:**
- `vibey/adapters/windsurf/config_generator.py` (new)
**Acceptance Criteria:**
- [ ] Generates `mcp_config.json` snippet for user installation
- [ ] Detects Python interpreter path automatically
- [ ] Includes project-specific environment variables
- [ ] Provides installation instructions

#### Task 1.5: MCP Server Validation
**Duration:** 1-2 days
**Files:**
- `framework/mcp/server.py` (verify compatibility, no changes expected)
**Acceptance Criteria:**
- [ ] Verify all 46 tools load correctly in Windsurf
- [ ] Test tool invocation via Cascade
- [ ] Confirm no protocol incompatibilities
- [ ] Document any Windsurf-specific behaviors

#### Task 1.6: Drift Detection Implementation
**Duration:** 1-2 days
**Files:**
- `vibey/adapters/windsurf/adapter.py` (extend)
**Acceptance Criteria:**
- [ ] Generate `.windsurf/.checksums.json`
- [ ] Implement `validate_export()` method
- [ ] SHA256 checksums for all generated files
- [ ] Validation command in CLI

#### Task 1.7: Unit Tests
**Duration:** 2 days
**Files:**
- `vibey/adapters/windsurf/tests/test_adapter.py` (new)
- `vibey/adapters/windsurf/tests/test_rule_generator.py` (new)
- `vibey/adapters/windsurf/tests/test_context_generator.py` (new)
**Acceptance Criteria:**
- [ ] 90%+ code coverage
- [ ] Test frontmatter to rule conversion
- [ ] Test character limit enforcement
- [ ] Test checksum generation

---

### Sprint 2: Agentic Workflow & VS Code Compatibility (2 weeks)

**Goal:** Full workflow integration and production readiness

#### Task 2.1: Workflow-to-Cascade Mapping
**Duration:** 3 days
**Files:**
- `vibey/adapters/windsurf/rule_generator.py` (extend)
**Acceptance Criteria:**
- [ ] Map multi-step workflows to Cascade operations
- [ ] Include step-by-step instructions in rules
- [ ] Reference MCP tools for each workflow step
- [ ] Quality gate integration in workflow rules

#### Task 2.2: Orchestration Mode Support
**Duration:** 2 days
**Files:**
- `vibey/adapters/windsurf/orchestration.py` (new)
**Acceptance Criteria:**
- [ ] Map Vibey orchestration modes to Cascade behavior
- [ ] Simple mode: explicit agent selection rules
- [ ] Balanced mode: model-decision activation
- [ ] Tiered mode: coordinator-based rules

#### Task 2.3: Integration Testing
**Duration:** 2-3 days
**Files:**
- `vibey/adapters/windsurf/tests/test_integration.py` (new)
**Acceptance Criteria:**
- [ ] End-to-end deployment test
- [ ] Cascade tool invocation test
- [ ] Workflow execution test
- [ ] Drift detection validation

#### Task 2.4: CLI Command Integration
**Duration:** 2 days
**Files:**
- `vibey/cli/commands.py` (extend)
**Acceptance Criteria:**
- [ ] `vibey export --platform windsurf` command
- [ ] `vibey export windsurf --validate` command
- [ ] `vibey deploy --platform windsurf` command
- [ ] Progress output and error handling

#### Task 2.5: Documentation
**Duration:** 2 days
**Files:**
- `docs/platforms/windsurf.md` (new)
- `docs/getting-started/QUICK_START.md` (update)
**Acceptance Criteria:**
- [ ] Installation guide for Windsurf users
- [ ] MCP configuration instructions
- [ ] Workflow usage examples
- [ ] Troubleshooting section

#### Task 2.6: Quality Validation
**Duration:** 2 days
**Files:**
- Various test files
**Acceptance Criteria:**
- [ ] All tests pass (>95% coverage)
- [ ] Documentation review complete
- [ ] Manual testing in Windsurf IDE
- [ ] No drift between source and generated files

---

## Zero-Drift Implementation Details

### File Generation Flow

```
framework/agents/*.md          framework/workflows/*.md
        │                              │
        │ FrontmatterParser            │ FrontmatterParser
        ▼                              ▼
┌─────────────────────────────────────────────────────┐
│                  Asset Registry                      │
│  - AgentDefinition[]                                │
│  - WorkflowDefinition[]                             │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ WindsurfAdapter.export()
                      ▼
    ┌─────────────────────────────────────────┐
    │        Generated Artifacts               │
    │                                          │
    │  .windsurf/                             │
    │  ├── rules/                             │
    │  │   ├── agents/                        │
    │  │   │   ├── web-developer.md           │
    │  │   │   ├── test-engineer.md           │
    │  │   │   └── ...                        │
    │  │   └── workflows/                     │
    │  │       ├── feature-development.md     │
    │  │       ├── sprint-planning.md         │
    │  │       └── ...                        │
    │  └── .checksums.json                    │
    │                                          │
    │  .windsurfrules (root)                  │
    │  mcp_config_snippet.json                │
    └─────────────────────────────────────────┘
```

### Checksum Manifest Format

```json
{
  "version": "1.0.0",
  "generated_at": "2025-11-23T12:00:00Z",
  "generator": "vibey-windsurf-adapter",
  "source_hash": "a1b2c3d4...",
  "artifacts": {
    "rules/agents/web-developer.md": "sha256:e5f6g7h8...",
    "rules/agents/test-engineer.md": "sha256:i9j0k1l2...",
    "rules/workflows/feature-development.md": "sha256:m3n4o5p6...",
    ".windsurfrules": "sha256:q7r8s9t0..."
  },
  "validation_command": "vibey export windsurf --validate"
}
```

### CI Validation Integration

```yaml
# .github/workflows/validate-exports.yml
- name: Validate Windsurf Export
  run: |
    vibey export --platform windsurf --output ./dist/windsurf
    vibey export windsurf --validate --dir ./dist/windsurf
```

---

## Testing Strategy

### Unit Tests
- `test_rule_generator.py` - Frontmatter to rule conversion
- `test_context_generator.py` - Global context generation
- `test_config_generator.py` - MCP config generation
- `test_adapter.py` - Full adapter lifecycle

### Integration Tests
- Deploy to test project
- Load MCP server in Windsurf
- Invoke tools via Cascade
- Execute sample workflows

### Validation Tests
- Checksum verification
- Character limit enforcement
- Directory structure validation
- Schema compliance

---

## Risk Analysis

### Risk 1: Tool Limit (100 tools)
**Probability:** Low
**Impact:** Medium
**Mitigation:** Vibey has 46 tools, well under limit. Monitor if adding tools.

### Risk 2: Prompts Not Supported
**Probability:** 100%
**Impact:** Low
**Mitigation:** Use rules for context instead of MCP prompts.

### Risk 3: Character Limit Overflow
**Probability:** Medium
**Impact:** Medium
**Mitigation:** Implement truncation with priority (description > examples > details).

### Risk 4: Cascade Behavior Differences
**Probability:** Low
**Impact:** Medium
**Mitigation:** Thorough testing with real Windsurf IDE before release.

---

## Success Criteria

1. **MCP Integration:** All 46 Vibey tools accessible in Windsurf Cascade
2. **Rules Generation:** All agents/workflows have corresponding `.windsurf/rules/`
3. **Zero Drift:** 100% of artifacts generated from frontmatter with checksums
4. **Documentation:** Complete installation guide for Windsurf users
5. **Test Coverage:** >90% code coverage, all integration tests passing
6. **Performance:** Export completes in <5 seconds for standard project

---

## References

### Research Sources

- [Windsurf Cascade Overview](https://windsurf.com/cascade)
- [Windsurf MCP Integration](https://docs.windsurf.com/windsurf/cascade/mcp)
- [Windsurf Rules Directory](https://windsurf.com/editor/directory)
- [Windsurf IDE Review 2025](https://medium.com/@urano10/windsurf-ide-review-2025-the-ai-native-low-code-coding-environment-formerly-codeium-335093f5619b)
- [MCP Setup Guide for Windsurf](https://natoma.ai/blog/how-to-enabling-mcp-in-windsurf)
- [Windsurf Rules Best Practices](https://playbooks.com/windsurf-rules)

### Internal References

- `/Users/fredabood/Repositories/vibey/framework/mcp/server.py` - MCP server implementation
- `/Users/fredabood/Repositories/vibey/vibey/adapters/base.py` - Base adapter class
- `/Users/fredabood/Repositories/vibey/vibey/adapters/gemini/adapter.py` - Reference adapter implementation
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/goose-port/goose-port-3/context/PLATFORM_ADAPTER_ARCHITECTURE.md` - Adapter architecture design

---

## Appendix A: Sample Generated Files

### Sample Agent Rule (`.windsurf/rules/agents/web-developer.md`)

```markdown
---
trigger:
  type: model_decision
  description: Building web user interfaces, frontend development, React/Vue/Angular components
globs:
  - "src/components/**/*"
  - "src/pages/**/*"
  - "*.tsx"
  - "*.jsx"
  - "*.vue"
  - "*.css"
  - "*.scss"
---

# Web Developer Agent (Vibey)

Use the **vibey_web_developer** MCP tool for this agent.

## When to Use
- Building user interfaces for web applications
- Creating React, Vue, or Angular components
- Implementing responsive designs
- Working with CSS, SCSS, or Tailwind

## Key Responsibilities
1. Analyze sprint requirements for UI needs
2. Design component architecture
3. Implement accessible, responsive components
4. Integrate with backend APIs
5. Write component tests

## Quality Criteria
- WCAG 2.1 AA compliance
- Core Web Vitals passing
- Cross-browser compatibility
- 80%+ test coverage

---
*Vibey Agent Framework - Auto-generated rule*
```

### Sample .windsurfrules

```
# Project: Vibey Agent Framework
# Type: framework
# Generated by Vibey - Do not edit manually

## Available Agents (via MCP)
Use `@vibey_<agent_name>` to invoke any agent:
- web-developer: Frontend UI development
- test-engineer: Testing and quality assurance
- backend-engineer: API and service development
- docs-writer: Technical documentation
- security-reviewer: Security analysis
- performance-engineer: Performance optimization

## Available Workflows (via MCP)
Use `@vibey_workflow_<name>` for multi-step processes:
- feature-development: End-to-end feature implementation
- sprint-planning: Sprint organization and task breakdown
- codebase-audit: Code quality and architecture review

## Project Standards
1. Use TypeScript for all new code
2. Follow ESLint configuration
3. Write tests for all new features
4. Document public APIs

<!-- VIBEY_FRAMEWORK_MANAGED -->
```

---

## Appendix B: CLI Commands

```bash
# Export to Windsurf format
vibey export --platform windsurf --output ./dist/windsurf

# Deploy to current project
vibey deploy --platform windsurf

# Validate existing export
vibey export windsurf --validate --dir ./.windsurf

# Show export preview
vibey export --platform windsurf --dry-run

# Clean and regenerate
vibey deploy --platform windsurf --clean
```

---

**Document Status:** Complete
**Next Action:** Begin Sprint 1, Task 1.1 - Create WindsurfAdapter Base Class
**Assigned Agents:** web-developer, test-engineer, docs-writer
