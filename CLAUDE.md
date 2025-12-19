# Vibey Agent Framework - Repository Context

**Version:** 2.5.0
**Purpose:** Agentic orchestration framework for AI coding assistants

---

## Quick Start

Every session working on this repository:

1. **Read this file** (CLAUDE.md) - Repository context
2. **Check roadmap status** - `vibey roadmap status`
3. **Run `git status`** - Understand current state
4. **Review recent commits** - `git log --oneline -10`

---

## What Is Vibey?

Vibey is a **roadmap management and AI orchestration framework** that helps development teams:

- Track development progress through tracks, sprints, and tasks
- Integrate AI assistants via the Model Context Protocol (MCP)
- Deploy configurations to 9 different AI platforms

### Key Statistics

| Component | Count |
|-----------|-------|
| CLI Commands | 203 |
| MCP Tools | 76 |
| Platform Adapters | 9 |
| Database Tables | 26 |

---

## Repository Structure

```
vibey/
├── vibey/                    # Python package (ALL code)
│   ├── cli/                  # CLI commands (Click framework)
│   ├── operations/           # Core business logic
│   │   ├── roadmap/          # Roadmap CRUD operations
│   │   └── docs/             # Documentation generation
│   ├── mcp/                  # MCP server implementation
│   ├── adapters/             # 9 platform adapters
│   ├── common/               # Shared utilities, errors
│   └── roadmap/              # Models and serialization
│
├── .vibey/                   # Framework data
│   ├── config/               # Modular configuration
│   └── roadmap/              # Roadmap system
│       ├── tracks/           # Track YAML files
│       ├── sprints/          # Sprint YAML files
│       ├── tasks/            # Task YAML files
│       └── roadmap.db        # SQLite query cache
│
├── docs/                     # Documentation
│   ├── development/          # SETUP.md, CODING_STANDARDS.md
│   ├── architecture/adr/     # Architectural Decision Records
│   ├── reference/            # CLI_REFERENCE.md, MCP_REFERENCE.md
│   ├── guides/               # User guides
│   ├── journeys/             # Persona-based user journeys
│   └── walkthroughs/         # Step-by-step tutorials
│
├── tests/                    # Test suite
├── CLAUDE.md                 # This file
├── README.md                 # Project overview
├── CONTRIBUTING.md           # Contribution guide
└── CHANGELOG.md              # Version history
```

---

## Core Architecture

### Dual Storage System

- **YAML files** - Source of truth, human-readable, git-friendly
- **SQLite database** - Query cache, fast operations, regenerable

```bash
# Rebuild database from YAML
vibey roadmap db rebuild

# Check sync status
vibey roadmap db status
```

### Flat Directory Structure

All roadmap entities use ULID-based filenames in flat directories:

```
.vibey/roadmap/
├── tracks/01KC2D0JK9JKQXGQW6MQEB0JZP.yaml
├── sprints/01KC2D0JKVT80AFQ6C1PA8CKJD.yaml
└── tasks/01KC2D0JK7READW9KAK1HBX4B8.yaml
```

Benefits: 98% directory reduction, fast git operations, simple file lookups.

See [ADR-0001](docs/architecture/adr/0001-ulid-identifiers.md) and [ADR-0002](docs/architecture/adr/0002-flat-directory-structure.md) for rationale.

---

## Common Commands

### Roadmap Operations

```bash
# View overall status
vibey roadmap status

# Show specific item
vibey roadmap show <ULID>

# Start working on a task
vibey roadmap start <task-id>

# Complete a task
vibey roadmap complete <task-id>

# View items (use status for overview, show for details)
vibey roadmap status
vibey roadmap show <track-id>
vibey roadmap show <sprint-id>
```

### Documentation

```bash
# Generate CLI reference
vibey docs generate-cli

# Generate MCP reference
vibey docs generate-mcp

# Check for documentation drift
vibey docs check-drift
```

### Database

```bash
# Rebuild database from YAML
vibey roadmap db rebuild

# Check database status
vibey roadmap db status

# Validate database integrity
vibey roadmap db validate
```

---

## Development Guidelines

### Code Location

- **ALL Python code** lives in `vibey/` package
- **CLI commands** use Click framework (`vibey/cli/`)
- **Operations** are in `vibey/operations/`
- **Models** are in `vibey/roadmap/models/`

### Key Patterns

1. **CLI → Operations → Storage**
   ```
   CLI command → Operation function → YAML + SQLite
   ```

2. **YAML as Source of Truth**
   - Always update YAML files
   - Database is regenerable from YAML
   - Use `vibey roadmap db rebuild` after external YAML edits

3. **ULID Identifiers**
   - All entities use 26-character ULIDs
   - Time-sortable, URL-safe, globally unique

### Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **SQLite 3.35+** (included with Python)
- **Git 2.30+**

### Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -x -q
```

For complete setup: [docs/development/SETUP.md](docs/development/SETUP.md)

---

## Code Standards

### Python Style

- **Formatter**: Black (line length 88)
- **Imports**: isort
- **Linting**: flake8
- **Type hints**: Required for public APIs

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=vibey

# Type checking
mypy vibey/
```

For complete standards: [docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)

---

## Architecture Decisions

Key architectural decisions are documented as ADRs:

| ADR | Decision |
|-----|----------|
| [ADR-0001](docs/architecture/adr/0001-ulid-identifiers.md) | ULID identifiers |
| [ADR-0002](docs/architecture/adr/0002-flat-directory-structure.md) | Flat directory structure |
| [ADR-0003](docs/architecture/adr/0003-dual-storage-sqlite-yaml.md) | SQLite + YAML dual storage |
| [ADR-0004](docs/architecture/adr/0004-click-cli-framework.md) | Click CLI framework |
| [ADR-0005](docs/architecture/adr/0005-mcp-integration.md) | MCP protocol integration |

---

## Interfaces

### CLI Interface

Primary interface for terminal usage:

```bash
vibey --help                    # Show all commands
vibey roadmap --help            # Roadmap commands
vibey deploy --help             # Deployment commands
vibey docs --help               # Documentation commands
```

Full reference: [docs/reference/CLI_REFERENCE.md](docs/reference/CLI_REFERENCE.md)

### MCP Interface

For AI assistant integration via Model Context Protocol:

- **76 tools** - Task operations, queries, content access
- **8 resources** - Workflow and handoff templates
- **4 prompts** - Quality gates, security, testing

Full reference: [docs/reference/MCP_REFERENCE.md](docs/reference/MCP_REFERENCE.md)

### Platform Adapters

Deploy configurations to 9 platforms:

```bash
vibey deploy list               # Show available platforms
vibey deploy run --platform cursor
```

Supported: Claude Code, Cursor, Copilot, VS Code, Goose, Gemini, Aider, Continue, Windsurf

---

## Current State

### Version 2.5.0 Features

- **Auto-generated documentation** - CLI and MCP references
- **Documentation drift detection** - CI/CD enforcement
- **User journey documentation** - 5 personas, walkthroughs
- **Contributor documentation** - SETUP.md, CODING_STANDARDS.md, ADRs

### Check Current Work

```bash
# View roadmap status
vibey roadmap status

# See active tracks and sprints (status shows all with progress indicators)
vibey roadmap status
```

---

## Key Files

| File | Purpose |
|------|---------|
| `vibey/cli/main.py` | CLI entry point |
| `vibey/cli/commands.py` | Command implementations |
| `vibey/operations/roadmap/` | Roadmap business logic |
| `vibey/mcp/server.py` | MCP server |
| `vibey/roadmap/models/` | Data models |
| `.vibey/roadmap/` | Roadmap data (YAML + SQLite) |

---

## Troubleshooting

### Database Issues

```bash
# Rebuild database from YAML
vibey roadmap db rebuild

# If rebuild fails, delete and recreate
rm .vibey/roadmap/roadmap.db
vibey roadmap db rebuild
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e ".[dev]"
```

### Test Failures

```bash
# Run specific test with verbose output
pytest tests/path/to/test.py -v

# Run tests matching pattern
pytest tests/ -k "test_pattern"
```

---

## Resources

### Documentation

- [README.md](README.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/](docs/) - All documentation

### References

- [CLI Reference](docs/reference/CLI_REFERENCE.md) - All 203 commands
- [MCP Reference](docs/reference/MCP_REFERENCE.md) - All 76 tools
- [ADRs](docs/architecture/adr/) - Architecture decisions

### Walkthroughs

- [New User](docs/walkthroughs/WALKTHROUGH_NEW_USER.md) - First 30 minutes
- [Active Developer](docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md) - Daily workflow
- [Contributor](docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md) - Contributing code

---

**Version:** 2.5.0 | **Python:** 3.9+ | **Storage:** YAML + SQLite
