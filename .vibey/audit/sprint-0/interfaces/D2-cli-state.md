# D2: CLI State Management Audit

**Task ID:** 01KFXJVERN4135W7BR2DHSC979
**Phase:** D2: Interfaces
**Date:** 2026-01-29

## Executive Summary

Complete audit of the Vibey CLI state management system covering configuration loading, context state, session tracking, and state initialization. The system uses a modular configuration architecture with 10 configuration files in `.vibey/config/`, supports dual storage (YAML + SQLite), and implements comprehensive session state tracking. Key finding: Configuration uses hierarchical precedence (modular > legacy > defaults), state is loaded lazily on command invocation, and session state persists across CLI invocations via YAML files.

## Methodology

**Files Analyzed:**
- `vibey/config/loader.py:1-150` - Configuration loading with fallback
- `vibey/config/models.py:1-150` - Pydantic configuration models
- `vibey/operations/roadmap/session_manager.py:1-100` - Session lifecycle management
- `vibey/roadmap/models/session.py:1-100` - Session data models
- `vibey/platform/config.py:1-100` - Platform detection and config
- `.vibey/config/*.yaml` - 10 configuration files

## Findings

### 2. Configuration State Table

| Config Type | Location | Format | Precedence | Scope |
|-------------|----------|--------|------------|-------|
| Framework | `.vibey/config/framework.yaml` | YAML | 1 (highest) | Framework-wide settings |
| Project | `.vibey/config/project.yaml` | YAML | 1 | Project metadata |
| Roadmap | `.vibey/config/roadmap.yaml` | YAML | 1 | Roadmap backend settings |
| Git | `.vibey/config/git.yaml` | YAML | 1 | Git integration rules |
| Platform | `.vibey/config/platform.yaml` | YAML | 1 | Platform detection overrides |
| Implement | `.vibey/config/implement.yaml` | YAML | 1 | Implementation mode settings |
| Quality Gates | `.vibey/config/quality-gates.yaml` | YAML | 1 | Gate enforcement rules |
| Token Budgets | `.vibey/config/token_budgets.yaml` | YAML | 1 | Token limit settings |
| Token Calibration | `.vibey/config/token_calibration.yaml` | YAML | 1 | Estimation calibration |
| Git Hooks | `.vibey/config/git_hooks.yaml` | YAML | 1 | Hook configuration |
| Legacy (fallback) | `.claude/project-config.yaml` | YAML | 2 | All settings (deprecated) |
| Defaults | Pydantic models | Python | 3 (lowest) | Hardcoded defaults |

### 3. Context State Table

| Context | Source | Loaded When | Used By |
|---------|--------|-------------|---------|
| Roadmap Context | `.vibey/roadmap/*.yaml` | On roadmap command | roadmap commands |
| Git Context | `.git/` repository | On git command | git commands, sync-commits |
| Track Context | `tracks/{ulid}.yaml` | On track operations | show, start, complete |
| Sprint Context | `sprints/{ulid}.yaml` | On sprint operations | show, start, complete |
| Task Context | `tasks/{ulid}.yaml` | On task operations | show, start, complete, context |
| Platform Context | Auto-detect + config | On CLI start | check-compatibility, recalculate |
| Session Context | `sessions/{ulid}.yaml` | On session command | session commands |
| Directory Context | `Path.cwd()` | Implicit | All commands |
| Database Context | `.vibey/roadmap.db` | On query commands | db commands, fast queries |
| Activity Log | `.vibey/roadmap/activity.jsonl` | On audit commands | audit log, verify-change |

### 4. Session State Table

| State | Persistence | Reset Trigger | Purpose |
|-------|-------------|---------------|---------|
| Active Session | YAML + SQLite | `session end` | Track current coding session |
| Session Events | YAML (append) | Never (audit trail) | Event log for reconstruction |
| Session Decisions | YAML (append) | Never (audit trail) | Decision audit trail |
| Session Commits | YAML (list) | Never | Git commits in session |
| Context Snapshots | YAML (embedded) | Never | Point-in-time context |
| Implementation State | `.vibey/implement/state.json` | `implement resume` | Execution loop state |
| Regression State | `.vibey/implement/regressions.json` | `implement acknowledge` | Regression tracking |
| Checkpoint State | `.vibey/checkpoints/` | Manual restore | Integrity snapshots |

### 5. State Initialization Flow (ASCII Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CLI STATE INITIALIZATION FLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ CLI Start   │────▶│ Parse Args   │────▶│ Load Click   │
│ (main.py)   │     │ (Click)      │     │ Context      │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
                    ▼                            ▼                            ▼
          ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
          │ Global Options  │        │ Detect Platform │        │ Set Verbosity   │
          │ --verbose,-q    │        │ (auto-detect)   │        │ VERBOSE/QUIET   │
          └────────┬────────┘        └────────┬────────┘        └────────┬────────┘
                   │                          │                          │
                   └──────────────────────────┼──────────────────────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │ Route to Command  │
                                    │ Group (roadmap,   │
                                    │ git, session...)  │
                                    └─────────┬─────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
          │ roadmap group   │       │ git group       │       │ session group   │
          │ --backend       │       │ (no options)    │       │ (no options)    │
          │ --no-sync       │       └────────┬────────┘       └────────┬────────┘
          └────────┬────────┘                │                         │
                   │                         │                         │
        ┌──────────▼──────────┐              │                         │
        │ Auto-sync check     │              │                         │
        │ (ensure_synced)     │              │                         │
        └──────────┬──────────┘              │                         │
                   │                         │                         │
                   └─────────────────────────┼─────────────────────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │ Load Config       │
                                   │ (ConfigLoader)    │
                                   └─────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
          ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
          │ Modular Config  │      │ Legacy Config   │      │ Default Values  │
          │ .vibey/config/  │      │ .claude/*.yaml  │      │ (Pydantic)      │
          │ (preferred)     │      │ (fallback)      │      │ (ultimate)      │
          └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
                   │                        │                        │
                   └────────────────────────┼────────────────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │ Execute Command   │
                                  │ (with loaded      │
                                  │  state context)   │
                                  └───────────────────┘
```

### 6. State Dependencies Table

| Command Group | Required State | Modifies State | Propagates To |
|---------------|----------------|----------------|---------------|
| `roadmap status/show` | Roadmap YAML/SQLite | None (read-only) | None |
| `roadmap start/complete` | Roadmap YAML | YAML, SQLite, Activity Log | Parent entities |
| `roadmap create-*` | Roadmap YAML | YAML, SQLite | Parent entity refs |
| `roadmap db rebuild` | Roadmap YAML | SQLite | None |
| `roadmap validate-*` | Roadmap YAML | None (read-only) | None |
| `roadmap repair` | Roadmap YAML | YAML | Progress counters |
| `roadmap tokens` | Roadmap YAML/SQLite | None (read-only) | None |
| `roadmap checkpoint` | All .vibey/ | Checkpoint dir | None |
| `git analyze/velocity` | Git history, Roadmap | None (read-only) | None |
| `git hooks install` | Filesystem | .git/hooks/ | None |
| `git sprint start/end` | Git, Roadmap | Git tags | None |
| `git sync` | Git branches/tags | Roadmap YAML | SQLite |
| `session start` | Roadmap | Session YAML, SQLite | Active session flag |
| `session end` | Session YAML | Session YAML, SQLite | Session status |
| `implement run` | Roadmap, Config | Task YAML, State file | Session, Commits |
| `config show/set` | Config YAML | Config YAML | None |
| `deploy run` | Config, Content | Target platform files | None |

### 7. Remote State Strategy Table

| State Type | Local Only | Sync to Remote | Caching | Offline Handling |
|------------|------------|----------------|---------|------------------|
| Framework Config | Yes | No (local settings) | N/A | Use local |
| Project Config | Yes | No | N/A | Use local |
| Roadmap Config | Yes | No | N/A | Use local |
| Git Config | Yes | No | N/A | Use local |
| Platform Config | Yes | No | N/A | Use local |
| Implement Config | Yes | No | N/A | Use local |
| Roadmap YAML | Partial | Yes (bidirectional) | Local SQLite | Queue changes |
| Session State | Partial | Yes (upload) | Local YAML | Queue session events |
| Activity Log | Partial | Yes (append) | Local JSONL | Queue entries |
| Database (SQLite) | Yes | No (regenerable) | Is the cache | Rebuild from YAML |
| Git Tags | Yes | Partial (push/pull) | N/A | Local-only until push |
| Checkpoints | Yes | No (local backup) | N/A | Use local |

### 8. State Validation Table

| State | Validation Rules | Default Value | Error Handling |
|-------|------------------|---------------|----------------|
| Framework Config | Pydantic schema validation | Defaults in model | ConfigValidationError |
| Project Config | Pydantic schema, required fields | None (required) | ConfigValidationError |
| Roadmap YAML | YAML syntax, required fields, status enum | None | ValidationError |
| Task YAML | Required fields (id, sprint_id, title, status) | Generated ULID | ValidationError |
| Sprint YAML | Required fields (id, track_id, name, status) | Generated ULID | ValidationError |
| Track YAML | Required fields (id, name, status) | Generated ULID | ValidationError |
| Session YAML | Required fields (id, status, started) | Generated ULID | ValidationError |
| SQLite Database | Schema validation, foreign keys | Empty tables | Rebuild from YAML |
| Platform Config | Optional fields, auto-detect | auto_detect: true | Fallback to detection |
| Git Config | Optional fields | enforcement: blocking | Use defaults |
| Activity Log | JSONL format, required fields | Empty file | Append-only |

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| 10 config files are local-only | Keep local, sync via Git | - | N/A |
| Roadmap YAML is source of truth | Implement bidirectional sync | L | Critical |
| SQLite is regenerable cache | Keep local, rebuild on sync | S | High |
| Session state has ULID IDs | Direct sync to remote | M | Medium |
| Activity log is append-only | Sync as append-only Delta table | M | High |
| Platform detection is local | Keep local (platform-specific) | - | N/A |
| Config precedence is well-defined | Maintain in remote mode | S | Medium |
| State initialization is lazy | Add remote check step | M | High |
| Checkpoints are local backups | Keep local (manual backup) | - | Low |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Configuration state table lists >= 3 config types: PASS (12 config types)
- [x] Context state table lists >= 4 context types: PASS (10 context types)
- [x] ASCII state initialization flow diagram present: PASS
- [x] Remote state strategy addresses offline handling: PASS (all 12 state types)

## References

- `vibey/config/loader.py:57-134` - ConfigLoader class
- `vibey/config/models.py:43-150` - Pydantic config models
- `vibey/operations/roadmap/session_manager.py:55-100` - SessionManager class
- `vibey/roadmap/models/session.py:21-77` - SessionStatus, SessionEventType enums
- `vibey/platform/config.py:31-84` - PlatformConfig dataclass
- `.vibey/config/framework.yaml:1-56` - Framework configuration example
- `.vibey/config/roadmap.yaml:1-18` - Roadmap backend configuration
- `.vibey/config/implement.yaml:1-181` - Implementation mode settings
