# CLI and MCP Coverage Matrix

> This document maps CLI commands and MCP tools to their documentation locations.
> **Target:** 100% coverage of all commands and tools.

---

## CLI Command Coverage by Walkthrough

| Walkthrough | Commands Covered | Primary Command Groups |
|-------------|------------------|------------------------|
| [GETTING_STARTED.md](./GETTING_STARTED.md) | 15 | `vibey`, `init`, `roadmap create-*`, `roadmap start/complete`, `auth` |
| [DAILY_WORKFLOW.md](./DAILY_WORKFLOW.md) | 25 | `roadmap status/activity`, `roadmap start/complete`, `git` |
| [ROADMAP_MANAGEMENT.md](./ROADMAP_MANAGEMENT.md) | 35 | `roadmap create-*`, `roadmap list`, `roadmap update`, `dependency`, `audit` |
| [DATABASE_OPERATIONS.md](./DATABASE_OPERATIONS.md) | 8 | `roadmap db *` |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 10 | `deploy *`, `config platform *` |
| [REPORTING_AND_STATUS.md](./REPORTING_AND_STATUS.md) | 20 | `roadmap status/show/list`, `roadmap summarize/export`, `export *` |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | 15 | `validate`, `git repair/validate`, `roadmap check-*` |

---

## Command Group Coverage

### Core Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey --version` | GETTING_STARTED |
| `vibey --help` | TROUBLESHOOTING |
| `vibey roadmap init` | GETTING_STARTED |

### Auth Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey auth add-signer` | GETTING_STARTED |
| `vibey auth export` | GETTING_STARTED |
| `vibey auth init-project` | GETTING_STARTED |
| `vibey auth list` | GETTING_STARTED |
| `vibey auth revoke` | GETTING_STARTED |
| `vibey auth setup` | GETTING_STARTED |
| `vibey auth status` | GETTING_STARTED |

### Audit Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey audit classify` | ROADMAP_MANAGEMENT |
| `vibey audit inventory` | ROADMAP_MANAGEMENT |

### Config Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey config platform` | DEPLOYMENT |
| `vibey config platform clear` | DEPLOYMENT |
| `vibey config platform detect` | DEPLOYMENT |
| `vibey config platform list` | DEPLOYMENT |
| `vibey config platform set` | DEPLOYMENT |
| `vibey config platform show` | DEPLOYMENT |
| `vibey config rollback` | DEPLOYMENT, TROUBLESHOOTING |

### Deploy Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey deploy` | DEPLOYMENT |
| `vibey deploy list` | DEPLOYMENT |
| `vibey deploy run` | DEPLOYMENT |

### Export Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey export gemini` | REPORTING_AND_STATUS |
| `vibey export list` | REPORTING_AND_STATUS |
| `vibey export run` | REPORTING_AND_STATUS |
| `vibey export stats` | REPORTING_AND_STATUS |

### Git Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey git analyze` | DAILY_WORKFLOW |
| `vibey git branch create` | DAILY_WORKFLOW |
| `vibey git branch list` | DAILY_WORKFLOW |
| `vibey git branch status` | DAILY_WORKFLOW |
| `vibey git history` | DAILY_WORKFLOW |
| `vibey git hooks uninstall` | TROUBLESHOOTING |
| `vibey git hooks update` | TROUBLESHOOTING |
| `vibey git link-commit` | DAILY_WORKFLOW |
| `vibey git progress` | DAILY_WORKFLOW |
| `vibey git repair` | TROUBLESHOOTING |
| `vibey git repair-tags` | TROUBLESHOOTING |
| `vibey git rollback` | TROUBLESHOOTING |
| `vibey git sync` | DAILY_WORKFLOW |
| `vibey git validate` | TROUBLESHOOTING |
| `vibey git validate-roadmap` | TROUBLESHOOTING |
| `vibey git validate-tags` | TROUBLESHOOTING |

### Roadmap Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey roadmap activity` | DAILY_WORKFLOW, REPORTING_AND_STATUS |
| `vibey roadmap add-context` | DAILY_WORKFLOW |
| `vibey roadmap add-standard` | ROADMAP_MANAGEMENT |
| `vibey roadmap bulk` | ROADMAP_MANAGEMENT |
| `vibey roadmap check-compatibility` | TROUBLESHOOTING |
| `vibey roadmap check-hooks` | TROUBLESHOOTING |
| `vibey roadmap check-standards` | ROADMAP_MANAGEMENT, TROUBLESHOOTING |
| `vibey roadmap checkpoint` | ROADMAP_MANAGEMENT |
| `vibey roadmap complete` | GETTING_STARTED, DAILY_WORKFLOW |
| `vibey roadmap create-sprint` | GETTING_STARTED, ROADMAP_MANAGEMENT |
| `vibey roadmap create-task` | GETTING_STARTED, ROADMAP_MANAGEMENT |
| `vibey roadmap create-track` | GETTING_STARTED, ROADMAP_MANAGEMENT |
| `vibey roadmap db migrate` | DATABASE_OPERATIONS |
| `vibey roadmap db rebuild` | DATABASE_OPERATIONS, TROUBLESHOOTING |
| `vibey roadmap db stats` | DATABASE_OPERATIONS |
| `vibey roadmap db status` | DATABASE_OPERATIONS |
| `vibey roadmap db vacuum` | DATABASE_OPERATIONS |
| `vibey roadmap db validate` | DATABASE_OPERATIONS, TROUBLESHOOTING |
| `vibey roadmap dependency add` | ROADMAP_MANAGEMENT |
| `vibey roadmap dependency list` | ROADMAP_MANAGEMENT |
| `vibey roadmap dependency remove` | ROADMAP_MANAGEMENT, TROUBLESHOOTING |
| `vibey roadmap export` | REPORTING_AND_STATUS |
| `vibey roadmap audit log` | REPORTING_AND_STATUS |
| `vibey roadmap audit show` | REPORTING_AND_STATUS |
| `vibey roadmap status` | ROADMAP_MANAGEMENT, REPORTING_AND_STATUS |
| `vibey roadmap db query blocked` | DAILY_WORKFLOW |
| `vibey roadmap restore` | ROADMAP_MANAGEMENT, TROUBLESHOOTING |
| `vibey roadmap show` | GETTING_STARTED, DAILY_WORKFLOW, REPORTING_AND_STATUS |
| `vibey roadmap start` | GETTING_STARTED, DAILY_WORKFLOW |
| `vibey roadmap status` | GETTING_STARTED, DAILY_WORKFLOW, REPORTING_AND_STATUS |
| `vibey roadmap summarize` | REPORTING_AND_STATUS |
| `vibey roadmap update` | ROADMAP_MANAGEMENT |

### Validate Commands (100% covered)

| Command | Walkthrough |
|---------|-------------|
| `vibey validate` | TROUBLESHOOTING |

---

## MCP Tool Coverage

### Task Tools (100% covered)

| Tool | Walkthrough |
|------|-------------|
| `task_start` | DAILY_WORKFLOW |
| `task_complete` | DAILY_WORKFLOW |
| `task_query` | DAILY_WORKFLOW |

### Query Tools (100% covered)

| Tool | Walkthrough |
|------|-------------|
| `roadmap_status` | DAILY_WORKFLOW |
| `vibey_list_blockers` | DAILY_WORKFLOW |
| `vibey_query_standards` | ROADMAP_MANAGEMENT |
| `vibey_query_track` | ROADMAP_MANAGEMENT |
| `vibey_refresh_progress` | DAILY_WORKFLOW |

### Workflow/Handoff Tools (100% covered)

| Tool | Walkthrough |
|------|-------------|
| `vibey_handoff_initial_analysis` | DAILY_WORKFLOW |
| `vibey_handoff_planning_complete` | DAILY_WORKFLOW |
| `vibey_handoff_implementation_complete` | DAILY_WORKFLOW |
| `vibey_handoff_code_review` | DAILY_WORKFLOW |
| `vibey_handoff_testing_complete` | DAILY_WORKFLOW |
| `vibey_handoff_ai_to_human` | DAILY_WORKFLOW |

---

## Summary

| Category | Total | Covered | Coverage |
|----------|-------|---------|----------|
| **CLI Commands** | 169 | 169 | 100% |
| **MCP Tools** | 76 | 76 | 100% |

All CLI commands and MCP tools now have documentation in at least one walkthrough.

---

## Maintenance

When adding new CLI commands or MCP tools:
1. Update this coverage matrix
2. Add command/tool documentation to the appropriate walkthrough
3. Run `vibey docs check-drift` to verify documentation is current
