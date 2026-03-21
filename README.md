# Vibey

A deployable `.claude/` directory that gives any project structured AI-assisted development workflows.

Vibey bridges Jira, git, and Claude's context using native Claude Code primitives: skills, subagents, rules, and hooks.

## Deploy

```bash
git clone https://github.com/fredabood/vibey.git your-project/.claude
```

## What's Included

### Skills (user-invocable)

| Command | What it does |
|---------|-------------|
| `/start-task` | Transition Jira ticket to In Progress, set working context |
| `/complete-task` | Run quality gates, summarize work, transition to Done |
| `/create-ticket` | Create structured Jira ticket with acceptance criteria |
| `/review-ticket` | Verify acceptance criteria, post report to Jira |
| `/status` | Query Jira for active sprint overview |
| `/implement-feature` | 7-step dev lifecycle: design → implement → test → security → integrate → document → commit |
| `/plan-sprint` | 9-step sprint planning with prioritization framework |
| `/handoff` | Generate session summary for continuity |
| `/discovery` | Codebase analysis: structure, tech stack, quality, security, roadmap |
| `/post-mortem` | Structured post-mortem for completed ticket |
| `/obsidian-lint` | Lint Obsidian vault: frontmatter, tags, wikilinks |
| `/vault-add` | Create Obsidian vault note with frontmatter + deduplication |
| `/sync-homelab` | Regenerate homelab-services.md from Caddyfile |
| `/deploy-service` | Guided new service deployment workflow |

### Commands (project-scoped)

| Command | What it does |
|---------|-------------|
| `/sprint-next` | Top 3 unblocked tickets in current sprint |
| `/check-blockers` | All tickets blocked by unresolved issues |
| `/stack-status` | Docker container health across all stacks |
| `/context` | Active ticket, recent commits, modified files |
| `/deploy-stack` | Guided stack deployment with verification |

### Subagents (auto-delegated)

Claude automatically delegates to these specialists based on task context:

| Agent | Triggers on |
|-------|------------|
| Security Reviewer | Security review, vulnerability assessment, auth code |
| Test Engineer | Writing tests, coverage improvement, test failures |
| Performance Reviewer | Optimization, slow queries, profiling, benchmarking |
| Observability Reviewer | Logging audit, monitoring, production readiness |
| Code Reviewer | Code review, PR review, refactoring assessment |
| Architecture Reviewer | System design, ADRs, scalability assessment |
| Documentation Reviewer | Doc review, README quality, inline comment audit |
| Project Manager | Sprint planning, ticket triage, dependency analysis |
| Homelab Ops | Docker troubleshooting, Caddyfile, service deployment, 502 errors |
| n8n Designer | n8n workflows, Code node debugging, workflow deployment |
| Data Engineer | Postgres queries, MinIO/S3, MLflow, jira schema analysis |

### Rules (path-scoped)

| Rule | Applies to |
|------|-----------|
| homelab-services | All sessions — service catalog, MCP capabilities, data schemas, Docker conventions |
| Security | All sessions — no hardcoded secrets, parameterized queries, HTTPS everywhere |
| Testing | All sessions — AAA pattern, 90%+ coverage, test-first |
| Documentation | All sessions — when/where to persist decisions |
| Planning | All sessions — 5-section plan structure |
| Success Criteria | All sessions — acceptance criteria format and gates |
| Vault Management | All sessions — Obsidian vault write conventions |
| Work Tracking | All sessions — Jira-first behavior |

### Hooks (quality gates)

| Hook | Trigger | Behavior |
|------|---------|----------|
| Pre-commit tests | `git commit` | Runs test suite; blocks commit on failure |
| Memory frontmatter check | `git commit` | Validates vault YAML frontmatter before commit |
| Docker safety check | `docker stop/rm/rmi/kill *` | Blocks destructive commands on production containers |
| Jira ticket check | `git commit` (async) | Warns if commit message lacks ticket reference |

## Structure

```
your-project/.claude/
├── settings.json              # Hook configuration
├── skills/
│   └── vibey/                 # Single /vibey command with subcommands
│       └── SKILL.md
├── agents/                    # 6 auto-delegated specialists
│   ├── security-reviewer.md
│   ├── test-engineer.md
│   ├── performance-reviewer.md
│   ├── observability-reviewer.md
│   ├── code-reviewer.md
│   └── architecture-reviewer.md
├── rules/                     # Path-scoped standards
│   ├── security.md
│   └── testing.md
└── hooks/                     # Shell scripts for quality gates
    ├── pre-commit-tests.sh
    └── jira-ticket-check.sh
```

## Customize

- **Add skills:** Create `skills/<name>/SKILL.md` with `user_invocable: true`
- **Add agents:** Create `agents/<name>.md` with a description for auto-delegation
- **Add rules:** Create `rules/<name>.md` with `globs:` for path matching
- **Edit hooks:** Modify `settings.json` and scripts in `hooks/`
