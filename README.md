# Vibey Agent Framework

**Version:** 1.3.0 (Config-to-Docs Architecture)
**Status:** Production Ready (Platform-Agnostic Core)

An intelligent, platform-agnostic agent orchestration framework that provides specialized agents, structured workflows, quality gates, and automatic agent selection for building production-quality software across multiple AI coding platforms.

**Platforms Supported:**
- ✅ **Claude Code** (Production Ready)
- ✅ **Goose** (Production Ready - NEW!)
- 🔬 **Cursor** (Research Phase)

---

## 🎯 What's New in v1.3.0

### Platform-Agnostic Architecture

Vibey now uses a **config-to-docs** architecture that separates source configuration from platform-specific deployments:

```
.vibey/ (source)          →     .claude/ (deployment)
├── config/                     ├── CLAUDE.md
│   ├── project.yaml            ├── agents/
│   ├── framework.yaml          └── workflows/
│   ├── agents/
│   └── workflows/
```

**Benefits:**
- 🎯 **Single Source of Truth** - Configuration in `.vibey/config/`
- 🔄 **Multi-Platform** - Deploy to Claude Code, Goose, Cursor from same source
- ⚡ **Fast Regeneration** - Recreate deployments instantly
- 🛡️ **Version Control** - `.vibey/` committed, deployments gitignored
- 🔌 **Extensible** - Add new platforms via adapter pattern

### New Unified CLI

```bash
# Deploy to any platform
./vibey deploy --platform claude-code
./vibey deploy --platform goose

# Generate documentation
./vibey docs generate

# Manage roadmaps
./vibey roadmap summarize sprint core-framework-2
./vibey roadmap context task-id
```

### Permanent .vibey/ Directory

The `.vibey/` directory is now **permanent** and contains:
- **config/** - Platform-agnostic configuration
- **roadmap/** - Project state tracking (YAML)
- **sprint_docs/** - Rich context (Markdown)
- **summaries/** - Auto-generated summaries
- **templates/** - Custom templates
- **backups/** - Deployment backups

---

## Quick Start (3 Steps)

### 1. Navigate to Your Project

```bash
cd /path/to/your-project
```

### 2. Clone Framework

```bash
git clone https://github.com/fredabood/vibey.git .vibey
```

### 3. Deploy to Your Platform

```bash
# For Claude Code users
cd .vibey
./vibey deploy --platform claude-code

# For Goose users
./vibey deploy --platform goose
```

**That's it!** The framework will:
- Generate platform-specific deployment (`.claude/`, `.goose/`, etc.)
- Create optimized instruction files
- Set up all agents and workflows
- Ready to use immediately!

---

## 🦆 Goose Quick Start (MCP Server)

Vibey integrates with Goose via the Model Context Protocol (MCP), exposing **46 tools**:

### 1. Set Up Environment

```bash
cd /path/to/vibey
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Goose

Add to `~/.config/goose/config.yaml`:

```yaml
extensions:
  vibey:
    name: vibey
    type: stdio
    cmd: /absolute/path/to/vibey/.venv/bin/python
    args:
      - /absolute/path/to/vibey/scripts/run-mcp-server.py
    enabled: true
    timeout: 300
```

### 3. Use Vibey Tools in Goose

```
> What's the roadmap status?
> Use vibey_test_engineer to write tests
> Run vibey_workflow_feature_development
```

**Available Tools:**
- 19 agent tools (`vibey_test_engineer`, `vibey_web_developer`, etc.)
- 16 workflow tools (`vibey_workflow_feature_development`, etc.)
- 11 roadmap tools (`vibey_roadmap_status`, `vibey_start_task`, etc.)

📚 See [Goose Integration Guide](docs/guides/GOOSE_INTEGRATION.md) for full setup.

---

## What Is Vibey?

Vibey is a platform-agnostic agent orchestration framework that transforms AI coding assistants into specialized development teams with:

### 🤖 19 Specialized Agents
- **Planning:** Sprint Planning Agent, Researcher
- **Development:** Web Developer, Backend Engineer, Frontend Engineer, Database Specialist, ML Engineer, Infrastructure Engineer
- **Quality:** Test Engineer, Security Reviewer, Performance Engineer, Observability Engineer
- **Documentation:** Documentation Engineer, Documentation Maintenance Engineer, Diagram Engineer, Git Committer
- **Architecture:** Architecture Agent
- **Core:** Coordinator Agent (intelligent routing), Vibey Manager

### 📋 16 Structured Workflows
- Sprint Planning & Roadmap Management
- Codebase Audit & Discovery
- Single Feature Development
- ML Model Development
- Infrastructure Setup
- Performance Optimization
- Security Audit
- And 9 more...

### 📝 22 Handoff Templates
- API Specifications
- Security Reports
- Codebase Audit Reports
- Research Summaries
- Architecture Decision Records
- ML Evaluation Reports
- And 16 more...

### 🎯 Automatic Quality Gates
- Security Review (≥85/100)
- Test Coverage (≥90%)
- Logging Audit (≥80/100)
- Documentation Completeness

### 🔀 3 Orchestration Modes
1. **Simple** - Explicit keyword-based rules (best for learning)
2. **Balanced** - Pattern matching (⭐ recommended for most projects)
3. **Tiered** - Intelligent coordination (best for complex projects)

---

## Architecture Overview

### Source vs Deployment Separation

```
┌─────────────────────────────────────────────────────┐
│                    .vibey/                          │
│         Platform-Agnostic Source                    │
│                                                     │
│  ├── config/         (What to deploy)              │
│  ├── roadmap/        (Project state - YAML)        │
│  ├── sprint_docs/    (Rich context - Markdown)     │
│  ├── summaries/      (Auto-generated)              │
│  └── templates/      (User-customizable)           │
└─────────────────────────────────────────────────────┘
                          │
                          │ Generate via Platform Adapters
                          ▼
        ┌─────────────────┬─────────────────┬─────────────────┐
        │   .claude/      │   .goose/       │   .cursor/      │
        │  (Generated)    │  (Generated)    │  (Generated)    │
        │  CLAUDE.md      │  README.md      │  .cursorrules   │
        │  agents/        │  extensions/    │  agents/        │
        │  workflows/     │  recipes/       │  workflows/     │
        └─────────────────┴─────────────────┴─────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**
   - Source: `.vibey/` (platform-agnostic, version-controlled)
   - Deployment: `.claude/`, `.goose/`, `.cursor/` (generated, gitignored)

2. **Single Source of Truth**
   - All configuration in `.vibey/config/`
   - Platform deployments generated on-demand
   - No manual editing of generated files

3. **Platform Adapter Pattern**
   - Each platform gets dedicated adapter
   - Adapters handle platform-specific quirks
   - Easy to add new platforms

---

## Vibey CLI Reference

The `vibey` command is your unified interface to the framework:

### Deploy Command

Deploy framework to target platform:

```bash
# Deploy to Claude Code
./vibey deploy --platform claude-code

# List available platforms
./vibey deploy --list-platforms

# Deploy without backup
./vibey deploy --platform claude-code --no-backup

# Deploy without validation
./vibey deploy --platform claude-code --no-validate
```

### Docs Command

Generate documentation from configuration:

```bash
# Generate all documentation
./vibey docs generate

# Overwrite existing documentation
./vibey docs generate --overwrite

# Custom output directory
./vibey docs generate --output custom-docs/
```

### Roadmap Command

Interact with roadmap system:

```bash
# Summarize a sprint
./vibey roadmap summarize sprint core-framework-2

# Summarize a task
./vibey roadmap summarize task core-framework-2-task-003

# Load task context
./vibey roadmap context core-framework-2-task-003

# Load context with custom distance
./vibey roadmap context task-id --max-distance 2

# Output as JSON
./vibey roadmap context task-id --format json
```

### Help

```bash
# Show help
./vibey help
./vibey --help

# Command-specific help
./vibey deploy --help
./vibey docs --help
./vibey roadmap --help
```

---

## Directory Structure

After deployment, your project will have:

```
your-project/
├── .vibey/                          # Platform-agnostic source (COMMITTED)
│   ├── config/                      # Configuration files
│   │   ├── project.yaml             # Project metadata
│   │   ├── framework.yaml           # Framework settings
│   │   ├── agents/                  # Agent configs (YAML)
│   │   │   └── web-developer.yaml
│   │   ├── workflows/               # Workflow configs (YAML)
│   │   └── quality-gates.yaml       # Quality gate definitions
│   ├── roadmap/                     # Roadmap state (YAML)
│   │   ├── roadmap.yaml
│   │   ├── tracks/
│   │   ├── sprints/
│   │   └── tasks/
│   ├── sprint_docs/                 # Sprint documentation (Markdown)
│   │   └── core-framework-2/
│   │       ├── plan.md
│   │       ├── architecture.md
│   │       └── retrospective.md
│   ├── summaries/                   # Auto-generated (GITIGNORED)
│   │   ├── dependency_summaries/
│   │   └── task_summaries/
│   ├── templates/                   # Custom templates
│   ├── backups/                     # Deployment backups (GITIGNORED)
│   └── vibey                        # CLI command
├── .claude/                         # Claude Code deployment (GITIGNORED)
│   ├── CLAUDE.md                    # Generated instructions
│   ├── agents/                      # Generated agent files
│   │   └── web-developer.md
│   └── workflows/                   # Generated workflow files
├── .goose/                          # Goose deployment (GITIGNORED, future)
│   ├── README.md
│   ├── extensions/
│   └── recipes/
└── [your code]
```

---

## Installation

### Prerequisites

- **AI Coding Assistant** - Claude Code (or Goose/Cursor in future)
- **Python 3.7+** - For CLI tools
- **PyYAML & Jinja2** - Python dependencies

```bash
pip install pyyaml jinja2
```

### Install Framework

```bash
# Navigate to your project
cd /path/to/your-project

# Clone framework
git clone https://github.com/fredabood/vibey.git .vibey

# Make CLI executable
chmod +x .vibey/vibey

# Deploy to your platform
.vibey/vibey deploy --platform claude-code
```

### Add to PATH (Optional)

For easier access:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/your-project/.vibey"

# Then use anywhere in your project
vibey deploy --platform claude-code
vibey docs generate
```

---

## Configuration

### .vibey/config/project.yaml

Platform-agnostic project configuration:

```yaml
project:
  name: "MyProject"
  type: "web-app"  # or api, ml, data-platform, infrastructure
  description: "Project description"
  version: "1.0.0"

tech_stack:
  languages:
    - python
    - typescript
  frameworks:
    - fastapi
    - react
  databases:
    - postgresql
```

### .vibey/config/framework.yaml

Framework behavior settings:

```yaml
orchestration:
  mode: "balanced"  # simple, balanced, or tiered
  auto_agent_launch: true
  require_quality_gates: true

context_loading:
  strategy: "distance_based"
  max_distance: 2
  mode: "summary"  # minimal, summary, or full
```

### .vibey/config/quality-gates.yaml

Quality gate definitions:

```yaml
gates:
  security:
    threshold: 85
    blocking: true
  test_coverage:
    threshold: 90
    blocking: true
  logging_audit:
    threshold: 80
    blocking: true
  documentation:
    threshold: 90
    blocking: false
```

---

## Usage

### For Claude Code Users

After deployment, Claude automatically reads the generated `CLAUDE.md`. Just tell Claude what you want:

```
"I want to implement user authentication with JWT tokens"
```

Claude automatically:
1. Detects this is a security-critical feature
2. Launches appropriate agents (API Specialist, Security Reviewer, Test Engineer)
3. Follows single-feature-development workflow
4. Runs quality gates before completion

### Updating Configuration

Edit `.vibey/config/` files, then redeploy:

```bash
# Edit config
vim .vibey/config/framework.yaml

# Regenerate deployment
./vibey deploy --platform claude-code
```

### Changing Platforms

Deploy to multiple platforms simultaneously:

```bash
# Deploy to Claude Code
./vibey deploy --platform claude-code

# Deploy to Goose (when available)
./vibey deploy --platform goose
```

---

## Platform Adapters

### Currently Supported

- **Claude Code** (`claude-code`) - ✅ Production Ready
  - Generates: `CLAUDE.md`, `agents/*.md`, `workflows/*.md`
  - Directory: `.claude/`

### Coming Soon

- **Goose** (`goose`) - 🚧 Q2 2025
  - Generates: `README.md`, `extensions/*.toml`, `recipes/*.yaml`
  - Directory: `.goose/`

- **Cursor** (`cursor`) - 🔬 Research Phase
  - Generates: `.cursorrules`, `agents/*.md`
  - Directory: `.cursor/`

### Creating Custom Adapters

See `docs/development/PLATFORM_ADAPTER_PATTERN.md` for adapter development guide.

---

## 🗺️ Roadmap System

Vibey includes a comprehensive project management system for tracking development work.

### Quick Start

```bash
# View roadmap status
./vibey roadmap status

# Summarize a sprint
./vibey roadmap summarize sprint core-framework-2

# Get task context
./vibey roadmap context task-id
```

### Documentation

- **[Roadmap User Guide](docs/development/ROADMAP_USER_GUIDE.md)** - Complete guide
- **[CLI Reference](framework/scripts/CLI.md)** - CLI documentation
- **[Examples](docs/development/ROADMAP_EXAMPLES.md)** - Practical examples

---

## Documentation

### User Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 10 minutes
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete CLI documentation
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Upgrade from v1.2 to v1.3

### Developer Documentation

- **[Platform-Agnostic Architecture](docs/development/PLATFORM_AGNOSTIC_ARCHITECTURE.md)** - System architecture
- **[Platform Adapter Pattern](docs/development/PLATFORM_ADAPTER_PATTERN.md)** - Adapter development
- **[YAML-Markdown Separation](docs/development/YAML_MARKDOWN_SEPARATION.md)** - Design principles
- **[Contributing Guide](CONTRIBUTING.md)** - Contribution guidelines

### Framework Documentation

- **[Agents Reference](docs/AGENTS.md)** - All 12 agents
- **[Workflows Reference](docs/WORKFLOWS.md)** - All 16 workflows
- **[Configuration Reference](docs/CONFIGURATION.md)** - Config schema
- **[Architecture Reference](docs/ARCHITECTURE.md)** - System architecture

---

## Supported Project Types

- ✅ **Web Applications** - Frontend + Backend
- ✅ **API Services** - Backend only (REST, GraphQL, gRPC)
- ✅ **ML Projects** - Model training, experimentation, deployment
- ✅ **Data Platforms** - ETL, analytics, data pipelines
- ✅ **Infrastructure** - IaC, cloud deployments

---

## Troubleshooting

### "vibey command not found"

```bash
# Make executable
chmod +x .vibey/vibey

# Or use full path
./.vibey/vibey deploy --platform claude-code
```

### "Platform not registered"

```bash
# List available platforms
./vibey deploy --list-platforms

# Ensure spelling matches exactly
./vibey deploy --platform claude-code  # ✅
./vibey deploy --platform claude       # ❌
```

### "Configuration invalid"

```bash
# Check YAML syntax
python3 framework/scripts/validate-config.py .vibey/config/project.yaml

# Review error messages
./vibey deploy --platform claude-code  # Shows validation errors
```

### "PyYAML not found" or "Jinja2 not found"

```bash
pip install pyyaml jinja2
```

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**Areas for improvement:**
- Additional platform adapters (Cursor, Aider, etc.)
- More agents (DevOps, QA, etc.)
- Additional workflows
- Language-specific templates
- Framework translations
- Example projects

---

## Version History

### v1.3.0 - Config-to-Docs Architecture (Current)
- ✅ Platform-agnostic architecture
- ✅ Unified `vibey` CLI
- ✅ Claude Code adapter
- ✅ Permanent `.vibey/` directory
- ✅ Platform adapter pattern

### v1.2.0 - Vibey Manager & Production Readiness
- ✅ Vibey Manager agent
- ✅ Framework management commands
- ✅ Sprint state management
- ✅ Production-ready deployment

### v1.1.0 - Sprint State Management
- ✅ Comprehensive sprint tracking
- ✅ Roadmap system

### v1.0.0 - Initial Production Release
- ✅ 12 specialized agents
- ✅ 16 structured workflows
- ✅ 22 handoff templates
- ✅ Quality gate system

---

## License

MIT License - see LICENSE file

---

## Framework Statistics

**Total Lines:** ~50,600+ across 68 components

**Components:**
- 12 specialized agents
- 16 structured workflows
- 22 handoff templates
- 3 orchestration modes
- 1 unified CLI
- Platform adapter system
- Complete documentation

**Platforms:**
- 1 production-ready (Claude Code)
- 2 in development (Goose, Cursor)

---

## Support & Community

**Issues:**
- Report bugs or request features on [GitHub Issues](https://github.com/fredabood/vibey/issues)

**Questions:**
- Ask your AI assistant! The framework is self-documenting
- Check the [documentation](docs/)

---

**Ready to build production-quality software with Vibey!** 🚀

```bash
cd your-project
git clone https://github.com/fredabood/vibey.git .vibey
.vibey/vibey deploy --platform claude-code
```
