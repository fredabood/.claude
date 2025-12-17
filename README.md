# Vibey Agent Framework

**Version:** 2.5.0
**Status:** Production Ready

An intelligent, platform-agnostic agent orchestration framework for AI coding assistants. Vibey provides specialized agents, structured workflows, project roadmap management, and multi-platform deployment support.

**Platform Support:**
- Claude Code
- Cursor
- GitHub Copilot
- Goose
- VS Code MCP
- Google Gemini Code Assist
- Aider
- Continue.dev
- Windsurf/Codeium

---

## Quick Start

### Installation

```bash
# From source (recommended for development)
git clone https://github.com/fredabood/vibey.git
cd vibey
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Initialize & Use

```bash
# Initialize in your project
cd /path/to/your-project
vibey init

# Check roadmap status
vibey roadmap status

# Start a task
vibey roadmap start <task-id>

# Complete a task
vibey roadmap complete <task-id>
```

### Deploy to Platform

```bash
# List available platforms
vibey deploy list

# Deploy to Claude Code
vibey deploy run --platform claude-code

# Deploy to Cursor
vibey deploy run --platform cursor
```

---

## What Is Vibey?

Vibey transforms AI coding assistants into specialized development teams by providing:

### Roadmap Management System

- **SQLite + YAML dual storage** - Fast queries with git-friendly files
- **Track → Sprint → Task hierarchy** - Organize complex projects
- **Activity logging** - Audit trail for all changes
- **Auto-progress** - Automatic status updates
- **Git hooks integration** - Pre-commit validation, post-commit tracking

### Multi-Platform Deployment

- **9 supported platforms** - Claude Code, Cursor, Copilot, and more
- **Platform adapters** - Generate platform-specific configurations
- **MCP Server** - 76+ tools for AI assistant integration

### CLI Interface

- **203 commands** - Comprehensive project management
- **Auto-generated documentation** - CLI and MCP references that can't drift

---

## Core Commands

### Roadmap Commands

```bash
# View overall status
vibey roadmap status

# Show track/sprint/task details
vibey roadmap show <item-id>

# Start and complete tasks
vibey roadmap start <task-id>
vibey roadmap complete <task-id>

# View activity
vibey roadmap activity --limit 10

# List blocked items
vibey roadmap list-blockers

# Get task context for AI assistants
vibey roadmap context <task-id>
```

### Deployment Commands

```bash
# Deploy to platform
vibey deploy run --platform claude-code

# List available platforms
vibey deploy list
```

### Documentation Commands

```bash
# Generate CLI reference
vibey docs generate-cli

# Generate MCP reference
vibey docs generate-mcp

# Check for documentation drift
vibey docs check-drift
vibey docs check-mcp-drift
```

---

## Project Structure

```
vibey/                          # Repository root
├── .vibey/                     # Vibey data directory
│   ├── config/                 # Configuration files
│   ├── roadmap/                # Roadmap data (YAML)
│   │   ├── tracks/             # Track files (ULID.yaml)
│   │   ├── sprints/            # Sprint files (ULID.yaml)
│   │   ├── tasks/              # Task files (ULID.yaml)
│   │   └── context/            # Sprint context documents
│   └── roadmap.db              # SQLite database cache
│
├── vibey/                      # Python package
│   ├── cli/                    # CLI commands (Click-based)
│   ├── operations/             # Core business logic
│   │   ├── roadmap/            # Roadmap operations
│   │   ├── git/                # Git integration
│   │   └── docs/               # Documentation generation
│   ├── mcp/                    # MCP server implementation
│   │   └── tools/              # 76+ MCP tools
│   ├── adapters/               # Platform adapters
│   ├── common/                 # Shared utilities
│   └── roadmap/                # Data models
│
├── docs/                       # Documentation
│   ├── guides/                 # User guides
│   ├── reference/              # CLI & MCP references
│   ├── journeys/               # User journey maps
│   └── walkthroughs/           # Step-by-step tutorials
│
└── tests/                      # Test suite
```

---

## MCP Server Integration

Vibey provides an MCP (Model Context Protocol) server with 76+ tools for AI assistant integration.

### Available Tools

| Category | Count | Description |
|----------|-------|-------------|
| Task | 3 | Start, complete, query tasks |
| Sprint | 4 | Sprint management |
| Query | 5 | Roadmap status and queries |
| Content | 7 | Context management |
| Agent | 19 | Agent invocation |
| Workflow | 16 | Workflow execution |
| Handoff | 22 | Handoff templates |

### Resources & Prompts

- **8 Resource Templates** - Workflow and handoff discovery
- **4 Prompts** - Quality gates, security, testing, documentation

See [MCP Reference](docs/reference/MCP_REFERENCE.md) for complete documentation.

---

## Documentation

### Getting Started

- **[New User Walkthrough](docs/walkthroughs/WALKTHROUGH_NEW_USER.md)** - First 30 minutes
- **[Active Developer Walkthrough](docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md)** - Daily workflow

### Reference

- **[CLI Reference](docs/reference/CLI_REFERENCE.md)** - All 203 commands (auto-generated)
- **[MCP Reference](docs/reference/MCP_REFERENCE.md)** - 76+ MCP tools (auto-generated)
- **[Roadmap System](docs/reference/ROADMAP_SYSTEM.md)** - Data model guide

### User Journeys

- **[New User Journey](docs/journeys/JOURNEY_NEW_USER.md)** - From discovery to first use
- **[Active Developer Journey](docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md)** - Daily productivity
- **[Project Lead Journey](docs/journeys/JOURNEY_PROJECT_LEAD.md)** - Multi-track management
- **[Contributor Journey](docs/journeys/JOURNEY_CONTRIBUTOR.md)** - Contributing to Vibey
- **[Platform Integrator Journey](docs/journeys/JOURNEY_PLATFORM_INTEGRATOR.md)** - MCP integration

---

## Development

### Prerequisites

- Python 3.9+
- Git
- SQLite (included with Python)

### Setup

```bash
git clone https://github.com/fredabood/vibey.git
cd vibey
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Verify installation
vibey --version
pytest tests/ -v
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=vibey --cov-report=term-missing
```

---

## Key Features

### ULID Identifiers

All entities use ULIDs (Universally Unique Lexicographically Sortable Identifiers):
- Time-sortable by default
- URL and filename safe
- Decentralized generation

### Dual Storage Architecture

- **YAML files** - Git-friendly, human-readable, source of truth
- **SQLite database** - Fast queries, relationship integrity
- **Auto-sync** - Database rebuilt from YAML as needed

### Auto-Generated Documentation

Documentation that can't drift from implementation:
- CLI Reference generated from Click commands
- MCP Reference generated from server introspection
- CI/CD drift detection

### Activity Logging

Complete audit trail for:
- Task status changes
- Sprint progress
- Context additions
- Git commits linked to tasks

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Improvement

- Additional platform adapters
- Enhanced MCP tools
- Improved documentation
- Test coverage expansion
- Performance optimization

---

## Statistics

| Metric | Count |
|--------|-------|
| CLI Commands | 203 |
| MCP Tools | 76 |
| MCP Resources | 8 |
| MCP Prompts | 4 |
| Platform Adapters | 9 |

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Support

- **Issues:** [GitHub Issues](https://github.com/fredabood/vibey/issues)
- **Documentation:** [docs/](docs/)
- **Help:** `vibey --help`

---

**Ready to get started?**

```bash
git clone https://github.com/fredabood/vibey.git
cd vibey && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
vibey roadmap status
```
