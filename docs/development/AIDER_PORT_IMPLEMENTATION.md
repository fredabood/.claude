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

| Vibey Concept | Aider Equivalent | Implementation Strategy |
|---------------|------------------|------------------------|
| **Agents** | Model roles via system prompts | Store agent instructions in `.aider/agents/` as prompt templates |
| **Workflows** | Chat session + command sequences | Script workflow steps as Aider Python API calls or CLI chains |
| **Handoffs** | Git commits + metadata | Use `--commit-prompt` to embed handoff info in commit messages |
| **Config** | `.aider.conf.yml` | Generate from Vibey's modular config via Jinja2 template |
| **Quality Gates** | Git hooks (pre-commit, post-commit) | Validate commits against quality gates |
| **Context** | Repository map + file selection | Use `/add` command to manage file context |

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
.aider/
├── aider.conf.yml           # Main config (generated)
├── agents/
│   ├── web-developer.md     # System prompts
│   ├── test-engineer.md
│   ├── security-reviewer.md
│   └── ...
├── workflows/
│   ├── weekly-sprint.py     # Python API chains
│   ├── feature-dev.sh       # Bash script chains
│   └── ...
└── hooks/
    ├── pre-commit           # Quality gate validation
    └── post-commit          # Metadata tracking
```

### Adapter Class

```python
class AiderAdapter(PlatformAdapter):
    """Aider platform deployment adapter."""

    def get_platform_name(self) -> str:
        return "aider"

    def get_deployment_dir(self, project_root: Path) -> Path:
        return project_root / ".aider"

    def deploy(self, source_dir: Path, config: Any) -> DeploymentResult:
        # 1. Create .aider/ structure
        # 2. Generate aider.conf.yml
        # 3. Convert agents to prompt templates
        # 4. Generate workflow scripts
        # 5. Create git hooks
        pass
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
| **Python API Instability** | Medium | Use shell scripts as fallback; wrap API calls with try/except |
| **MCP Support Uncertainty** | Low | Don't depend on MCP for Phase 1; design adapter to be MCP-ready |
| **Limited Agent Customization** | Low | Use system prompts; future contribution opportunity |
| **Git Workflow Assumptions** | Low | Document requirement; quality gates check for .git |

---

## 9. Deliverables Checklist

- [ ] `vibey/adapters/aider.py` - AiderAdapter class
- [ ] `templates/aider/aider.conf.yml.j2` - Config template
- [ ] `templates/aider/agent-prompt.md.j2` - Agent prompt template
- [ ] `templates/aider/workflow-bash.sh.j2` - Bash workflow template
- [ ] `templates/aider/workflow-python.py.j2` - Python workflow template
- [ ] `templates/aider/pre-commit.j2` - Pre-commit hook template
- [ ] `tests/adapters/test_aider.py` - Unit tests
- [ ] `tests/integration/test_aider_deployment.py` - Integration tests
- [ ] `docs/guides/AIDER_INTEGRATION.md` - User guide
- [ ] Example project with Aider deployment

---

## 10. Success Criteria

1. **Functional Deployment**
   - `vibey deploy --platform aider` creates valid `.aider/` directory
   - Generated `aider.conf.yml` works with Aider CLI
   - All 12 agents available as system prompts

2. **Workflow Execution**
   - At least 10 workflows converted to scripts
   - Python API workflows execute correctly
   - Multi-file editing works

3. **Quality Integration**
   - Git hooks validate commits
   - Quality gates block non-compliant code
   - Handoff metadata tracked in commits

4. **Documentation**
   - Complete user guide
   - 3+ example projects
   - Troubleshooting guide

---

## References

- [Aider Official Site](https://aider.chat/)
- [Aider GitHub Repository](https://github.com/Aider-AI/aider)
- [Aider Documentation](https://aider.chat/docs/)
- [YAML Config Reference](https://aider.chat/docs/config/aider_conf.html)
- [Scripting Aider](https://aider.chat/docs/scripting.html)
- [MCP Support PR #3937](https://github.com/Aider-AI/aider/pull/3937)

---

**Last Updated:** 2025-11-22
**Author:** Vibey Framework Team
