# Aider Platform Port - Implementation Plan

**Track ID:** `aider-port`
**Status:** Not Started
**Priority:** High
**Estimated Duration:** 2-3 weeks (1 sprint)
**Compatibility Score:** 95%

---

## Executive Summary

Aider is a production-ready, open-source CLI-based AI coding assistant with exceptional compatibility for a Vibey framework port. With 95% estimated compatibility and minimal effort, Aider represents the highest-priority new platform port after Goose.

**Key Stats:**
- GitHub Stars: 40,000+
- License: MIT (open source)
- Platform: Terminal/CLI (cross-platform)
- LLM Support: 100+ providers via LiteLLM

---

## Critical Architecture: Dynamic Generation from Source of Truth

> **All `.aider/` files are GENERATED, never manually edited.**

### Source of Truth Hierarchy

```
SOURCE OF TRUTH (edit these)              GENERATED OUTPUT (never edit)
────────────────────────────              ────────────────────────────
framework/agents/*.md            ───►     .aider/agents/*.md
framework/workflows/*.md         ───►     .aider/workflows/*.py
.vibey/config/*.yaml             ───►     .aider/aider.conf.yml
templates/aider/*.j2             ───►     .aider/hooks/*
```

### Why This Matters

1. **Prevents Drift**: Generated files always match source definitions
2. **Single Update Point**: Change `framework/agents/web-developer.md` once, regenerate for all platforms
3. **Consistent Behavior**: Same agent behaves identically across Claude Code, Goose, and Aider
4. **Version Control**: Source of truth is tracked; generated files can be `.gitignore`d

### Regeneration Commands

```bash
# Regenerate all .aider/ files from source
vibey deploy --platform aider

# Force regenerate (clears existing)
vibey deploy --platform aider --force

# Regenerate after framework update
vibey upgrade && vibey deploy --platform aider
```

### .gitignore Recommendation

```gitignore
# Generated platform files (regenerate with `vibey deploy`)
.aider/agents/
.aider/workflows/
.aider/hooks/

# Keep config if user customizes model/API settings
# .aider/aider.conf.yml
```

---

## 1. Platform Architecture

### Core Components

1. **Repository Map System**
   - Uses Tree-sitter (AST parser) to analyze codebase structure
   - Extracts function signatures, class definitions, type information
   - Builds dependency graph between files
   - Uses PageRank algorithm to identify most relevant code

2. **LLM Provider Abstraction (via LiteLLM)**
   - Unified interface to 100+ LLM providers
   - Supports: OpenAI, Claude, DeepSeek, Gemini, local models
   - No vendor lock-in (BYOK - Bring Your Own Key)

3. **Edit System**
   - Applies LLM-generated changes directly to files
   - Supports multiple edit formats for different languages
   - Includes automatic linting and error fixing

4. **Git Integration**
   - Auto-commits after each change
   - Conventional Commits format (configurable)
   - Customizable commit messages via `--commit-prompt`

---

## 2. Vibey Concept Mapping

| Vibey Concept | Aider Equivalent | Source → Generated |
|---------------|------------------|-------------------|
| **Agents** | System prompts (`.md` files) | `framework/agents/*.md` → `.aider/agents/*.md` |
| **Workflows** | Python API scripts | `framework/workflows/*.md` → `.aider/workflows/*.py` |
| **Handoffs** | Git commits + metadata | Embedded via `--commit-prompt` template |
| **Config** | `.aider.conf.yml` | `.vibey/config/*.yaml` → `.aider/aider.conf.yml` |
| **Quality Gates** | Git hooks | `templates/aider/*.j2` → `.aider/hooks/*` |
| **Context** | Repository map + `/add` | Aider's native tree-sitter analysis |

---

## 3. Integration Points

### Configuration System

**File:** `.aider.conf.yml`
- Stored in: home directory, repo root, or current directory
- Format: YAML (same as Vibey!)
- Priority: Last loaded file takes precedence

**Example Configuration:**
```yaml
model: claude-3-5-sonnet
api-key: $ANTHROPIC_API_KEY
auto-commits: true
commit-prompt: |
  Create a commit message following Conventional Commits format.
  Include [Vibey] tag and task ID if available.
```

### MCP Support (Pending)

- PR #3937 adds Model Context Protocol support
- Configuration via JSON in YAML
- Status: Pull request still pending merge

### Chat Modes

- `/ask` - Ask for advice without editing
- `/code` - Edit files (default mode)
- `/architect` - Architect mode (multi-file planning)
- `/add` - Add files to chat
- `/drop` - Remove files from chat
- `/clear` - Clear chat history

---

## 4. Implementation Architecture

### Directory Structure

```
.aider/                              # ⚠️ ALL FILES GENERATED - DO NOT EDIT
├── .generated                       # Marker file with generation timestamp
├── aider.conf.yml                   # Main config (generated from .vibey/config/)
├── agents/                          # Generated from framework/agents/
│   ├── web-developer.md             # System prompt for web-developer agent
│   ├── test-engineer.md             # System prompt for test-engineer agent
│   ├── security-reviewer.md         # System prompt for security-reviewer agent
│   └── ...                          # All 12 agents
├── workflows/                       # Generated from framework/workflows/
│   ├── weekly-sprint.py             # Python API workflow script
│   ├── feature-dev.py               # Python API workflow script
│   ├── infrastructure-setup.py      # Python API workflow script
│   └── ...                          # All 16 workflows
└── hooks/                           # Generated from templates/aider/
    ├── pre-commit                   # Quality gate validation
    └── post-commit                  # Handoff metadata tracking
```

### Adapter Class (Following Goose Pattern)

```python
class AiderAdapter(BaseAdapter):
    """
    Aider platform adapter.

    Generates .aider/ directory from Vibey source of truth.
    All output files are regenerated on each export() call.

    Source of Truth:
    - framework/agents/*.md → .aider/agents/*.md
    - framework/workflows/*.md → .aider/workflows/*.py
    - .vibey/config/*.yaml → .aider/aider.conf.yml
    """

    platform_name = "aider"
    display_name = "Aider"
    description = "Terminal-based AI coding assistant with git integration"

    def __init__(self, root_dir: Path, cache_ttl: int = 60):
        """
        Initialize Aider adapter.

        Args:
            root_dir: Root directory of Vibey repository
            cache_ttl: Cache time-to-live in seconds
        """
        self.root_dir = Path(root_dir)

        # Use same discovery system as MCP/Goose
        self._discovery = ToolDiscovery(
            root_dir=self.root_dir,
            cache_ttl=cache_ttl
        )

        # Generators for Aider-specific formats
        self._prompt_generator = AiderPromptGenerator()
        self._workflow_generator = AiderWorkflowGenerator()
        self._config_generator = AiderConfigGenerator()

    def get_agents(self) -> List[AgentDefinition]:
        """Get agents from source of truth (framework/agents/)."""
        return self._discovery.get_agents()

    def get_workflows(self) -> List[WorkflowDefinition]:
        """Get workflows from source of truth (framework/workflows/)."""
        return self._discovery.get_workflows()

    def translate_agent(self, agent: AgentDefinition) -> str:
        """Convert agent to Aider system prompt format."""
        return self._prompt_generator.generate(agent)

    def translate_workflow(self, workflow: WorkflowDefinition) -> str:
        """Convert workflow to Aider Python script."""
        return self._workflow_generator.generate(workflow)

    def export(self, output_dir: Path) -> ExportResult:
        """
        Export all Aider files. ALWAYS regenerates from source.

        Args:
            output_dir: Directory to write files (typically .aider/)

        Returns:
            ExportResult with list of created files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        files = []

        # Write generation marker
        marker = output_dir / ".generated"
        marker.write_text(f"Generated by vibey deploy --platform aider\n"
                          f"Timestamp: {datetime.now().isoformat()}\n"
                          f"DO NOT EDIT - Regenerate with: vibey deploy --platform aider\n")
        files.append(marker)

        # Generate agents (from framework/agents/)
        agents_dir = output_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        for agent in self.get_agents():
            prompt = self.translate_agent(agent)
            path = agents_dir / f"{agent.id}.md"
            path.write_text(prompt)
            files.append(path)

        # Generate workflows (from framework/workflows/)
        workflows_dir = output_dir / "workflows"
        workflows_dir.mkdir(exist_ok=True)
        for workflow in self.get_workflows():
            script = self.translate_workflow(workflow)
            path = workflows_dir / f"{workflow.id.replace('-', '_')}.py"
            path.write_text(script)
            files.append(path)

        # Generate config (from .vibey/config/)
        config = self._config_generator.generate(self.root_dir)
        config_path = output_dir / "aider.conf.yml"
        config_path.write_text(config)
        files.append(config_path)

        # Generate hooks (from templates/aider/)
        hooks_dir = output_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        # ... hook generation ...

        return ExportResult(platform=self.platform_name, files=files)

    def invalidate_cache(self) -> None:
        """Invalidate discovery cache to force re-read from source."""
        self._discovery.invalidate_cache()
```

---

## 5. Sprint Plan

### Sprint 1: Aider Platform Adapter Implementation (2-3 weeks)

#### Task 1: Create AiderAdapter class (2-3 days)
- Extend `PlatformAdapter` base class
- Implement platform-specific methods
- Handle config generation

#### Task 2: Generate aider.conf.yml template (1 day)
- Model selection based on config
- API key management
- Custom commit prompt template

#### Task 3: Agent prompt template system (2 days)
- Convert agent instructions to Aider system prompts
- Store in `.aider/agents/agent-id.md`
- Inject via `--system` flag in commands

#### Task 4: Workflow script generation (2-3 days)
- Simple workflows → Bash scripts with Aider commands
- Complex workflows → Python scripts using Aider API
- Store in `.aider/workflows/`

#### Task 5: Git hook integration (1-2 days)
- Pre-commit hooks for quality gate validation
- Post-commit hooks for handoff metadata tracking

#### Task 6: Handoff metadata in commits (1 day)
- Custom commit prompt template with handoff metadata
- Git commit message structure for agent tracking
- Parser to extract handoff state

#### Task 7: Integration testing (2-3 days)
- Test with real Aider installation
- Verify git commits work as expected
- Ensure multi-file workflows execute correctly

#### Task 8: Documentation (2-3 days)
- User guide for terminal users
- Developer guide for customization
- Example projects

---

## 6. Technical Decisions

### Config Format: YAML
- Both Vibey and Aider use YAML
- No translation needed
- Familiar to users

### Execution Method: Dual Approach

**Option A: Shell Scripts (Simple)**
```bash
#!/bin/bash
# .aider/workflows/weekly-sprint.sh
aider --model sonnet /add src/main.py tests/test_main.py
aider --message "First task: implement feature X"
aider --message "Second task: add tests"
```

**Option B: Python API (Powerful) - Recommended**
```python
# .aider/workflows/weekly_sprint.py
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

model = Model("claude-3-5-sonnet")
io = InputOutput(yes=True)
coder = Coder.create(main_model=model, io=io,
                     fnames=["src/main.py", "tests/test_main.py"])

coder.run("First task: implement feature X")
coder.run("Second task: add tests")
```

### Model Role Mapping
```yaml
# .aider/aider.conf.yml
system: |
  You are a Web Developer specialized in React.
  Your role is to build scalable user interfaces.
  Follow these patterns: [agent instructions]
```

---

## 7. Quality Gates

### Gate 1: Terminal Integration Testing (95% threshold)
- `.aider/aider.conf.yml` generates correctly
- Aider CLI can read and use generated configs
- Multi-file editing works as expected

### Gate 2: Git Workflow Compatibility (90% threshold)
- Auto-commit messages are properly formatted
- Handoff metadata embeds in commits
- Quality gates block non-compliant commits

### Gate 3: Comprehensive Testing (100% threshold)
- All journey tests pass
- Platform deployment tests pass
- >95% platform parity with Claude Code

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Configuration Drift** | High | **Never edit generated files**. All `.aider/` files regenerated from source on each `vibey deploy`. Add `.generated` marker file with warning. |
| **User Edits Generated Files** | High | Clear warnings in generated files, `.gitignore` generated dirs, documentation emphasizing regeneration workflow |
| **Python API Instability** | Medium | Use shell scripts as fallback; wrap API calls with try/except |
| **MCP Support Uncertainty** | Low | Don't depend on MCP for Phase 1; design adapter to be MCP-ready |
| **Limited Agent Customization** | Low | Customize in `framework/agents/`, not `.aider/agents/` |
| **Git Workflow Assumptions** | Low | Document requirement; quality gates check for .git |

---

## 9. Deliverables Checklist

### Core Adapter (Source of Truth Pattern)
- [ ] `framework/adapters/aider/adapter.py` - AiderAdapter class (follows GooseAdapter pattern)
- [ ] `framework/adapters/aider/prompts.py` - AiderPromptGenerator (agent → system prompt)
- [ ] `framework/adapters/aider/workflows.py` - AiderWorkflowGenerator (workflow → Python script)
- [ ] `framework/adapters/aider/config.py` - AiderConfigGenerator (config → aider.conf.yml)
- [ ] `framework/adapters/aider/__init__.py` - Module exports

### Templates (Jinja2)
- [ ] `templates/aider/aider.conf.yml.j2` - Config template
- [ ] `templates/aider/agent-prompt.md.j2` - Agent system prompt template
- [ ] `templates/aider/workflow-python.py.j2` - Python workflow script template
- [ ] `templates/aider/pre-commit.j2` - Pre-commit hook template
- [ ] `templates/aider/post-commit.j2` - Post-commit hook template
- [ ] `templates/aider/.generated.j2` - Generation marker template

### Tests
- [ ] `tests/adapters/test_aider_adapter.py` - Unit tests for adapter
- [ ] `tests/adapters/test_aider_generators.py` - Unit tests for generators
- [ ] `tests/integration/test_aider_deployment.py` - Integration tests
- [ ] `tests/integration/test_aider_regeneration.py` - Test regeneration overwrites

### Documentation
- [ ] `docs/guides/AIDER_INTEGRATION.md` - User guide (emphasize regeneration workflow)
- [ ] `docs/guides/AIDER_CUSTOMIZATION.md` - How to customize (edit source, not generated)
- [ ] Example project with Aider deployment
- [ ] `.gitignore` template for Aider projects

---

## 10. Success Criteria

1. **Functional Deployment**
   - `vibey deploy --platform aider` creates valid `.aider/` directory
   - Generated `aider.conf.yml` works with Aider CLI
   - All 12 agents available as system prompts

2. **Dynamic Regeneration (Critical)**
   - Running `vibey deploy --platform aider` twice produces identical output
   - Modifying `framework/agents/web-developer.md` and regenerating updates `.aider/agents/web-developer.md`
   - `.generated` marker file present with timestamp and warning
   - Generated files contain "DO NOT EDIT" header comments

3. **Workflow Execution**
   - At least 10 workflows converted to scripts
   - Python API workflows execute correctly
   - Multi-file editing works

4. **Quality Integration**
   - Git hooks validate commits
   - Quality gates block non-compliant code
   - Handoff metadata tracked in commits

5. **Documentation**
   - Complete user guide emphasizing regeneration workflow
   - Clear guidance: "Edit source, not generated"
   - 3+ example projects
   - `.gitignore` template provided

---

## References

- [Aider Official Site](https://aider.chat/)
- [Aider GitHub Repository](https://github.com/Aider-AI/aider)
- [Aider Documentation](https://aider.chat/docs/)
- [YAML Config Reference](https://aider.chat/docs/config/aider_conf.html)
- [Scripting Aider](https://aider.chat/docs/scripting.html)
- [MCP Support PR #3937](https://github.com/Aider-AI/aider/pull/3937)

---

**Last Updated:** 2025-11-23
**Author:** Vibey Framework Team
**Architecture Review:** Dynamic generation from source of truth (prevents drift)
