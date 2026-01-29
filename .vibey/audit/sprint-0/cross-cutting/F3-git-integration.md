# F3: Git Integration Audit

**Task ID:** 01KFXKDJ24EZF2KBVJYP3EWYM0
**Phase:** F3: Cross-Cutting
**Date:** 2026-01-29

## Executive Summary

Complete audit of the Vibey Git Integration system covering 23 git operation modules in `vibey/operations/git/`. The system provides commit-task linking, branch management, hook installation, and git-primary synchronization. Key finding: Git integration supports bidirectional sync between commits/branches and roadmap state. Remote coordination requires mapping local git hooks to remote CI/CD pipelines, and leveraging Databricks Repos API for workspace-level git operations.

## Methodology

**Files Analyzed:**
- `vibey/operations/git/*.py` - 23 git operation modules
- `.git/hooks/pre-commit` - Pre-commit hook
- `.git/hooks/commit-msg` - Commit message hook
- `.git/hooks/post-commit` - Post-commit hook
- `.git/hooks/post-merge` - Post-merge hook

## Findings

### 2. Commit Linking Table

| Aspect | Implementation | Storage | Example |
|--------|----------------|---------|---------|
| Task References | `CommitParser.parse()` | In-memory, YAML | `feat(01KC..): description` |
| Sprint References | Footer parsing | Task YAML | `Sprint: 01KC...` |
| Track References | Footer parsing | Task YAML | `Track: 01KC...` |
| Status Keywords | Regex patterns | None (derived) | `completes`, `starts`, `blocks` |
| SHA Storage | `commit_evidence.py` | Task YAML `commits` field | `abc123` |
| Batch Parsing | `parse_batch()` | List\[ParsedCommit\] | Multiple commits |

**Supported Commit Formats:**
| Format | Pattern | Example |
|--------|---------|---------|
| Conventional | `type(scope): subject` | `feat(01KC...): Add feature` |
| Footer | `Task: id` in body | `Task: 01KC...` |
| Bracket | `[task-id] subject` | `[01KC...] Fix bug` |
| Inline | Task ID anywhere | `Relates to 01KC...` |

### 3. Git Hooks Table

| Hook | Type | Purpose | Installation |
|------|------|---------|--------------|
| `pre-commit` | Blocking | Validate roadmap YAML, enforce CLI usage | `vibey roadmap install-hooks` |
| `commit-msg` | Blocking | Validate commit format, check task references | `vibey roadmap install-hooks` |
| `post-commit` | Non-blocking | Clear CLI change tracker | `vibey roadmap install-hooks` |
| `post-merge` | Non-blocking | Update roadmap state after merge | `vibey roadmap install-hooks` |
| `pre-push` | Optional | Validate before push | Custom |

**Hook Bypass Methods:**
| Method | Command | Scope |
|--------|---------|-------|
| Git flag | `git commit --no-verify` | Single commit |
| Environment | `VIBEY_SKIP_HOOKS=1` | Single command |
| Environment | `VIBEY_OVERRIDE=1` | Single command |
| Uninstall | `vibey git hooks uninstall` | Permanent |

### 4. Git Operations Table

| Operation | Function | Parameters | State Required |
|-----------|----------|------------|----------------|
| Parse commits | `CommitParser.parse()` | `message, sha` | None |
| Batch parse | `CommitParser.parse_batch()` | `List[commits]` | None |
| Validate commit | `CommitParser.validate()` | `ParsedCommit` | Config |
| Link branch | `BranchLinker.link_task_to_branch()` | `task_id, branch_name` | Git repo |
| Parse branch | `BranchLinker.parse_branch_name()` | `branch_name` | None |
| Sync from git | `GitPrimarySync.sync()` | `dry_run` | Git + Roadmap |
| Update status | `TaskStatusUpdater.apply_updates()` | `ParsedCommit` | YAML files |
| Tag sprint | `SprintTagger.tag_sprint_start()` | `sprint_id` | Git repo |
| Check merge | `merge_checker.check_merge_safe()` | `branch_name` | Git repo |
| Calculate velocity | `velocity_calculator.calculate()` | `sprint_id` | Git history |

### 5. Branch Management Table

| Pattern | Convention | Task Association | Protection |
|---------|------------|------------------|------------|
| `task/<task-id>` | Feature branches | Direct ULID link | None by default |
| `sprint/<sprint-id>` | Sprint integration | Sprint scope | Optional |
| `track/<track-id>` | Track integration | Track scope | Optional |
| `main` | Primary branch | None | Protected |
| `develop` | Development | None | Optional |

**Branch State Derivation (Git-Primary Mode):**
| Task Status | Branch Condition | Commit Condition |
|-------------|------------------|------------------|
| not_started | No branch exists | No commits reference task |
| in_progress | Branch exists OR | Commits exist, branch not merged |
| completed | Branch merged | Task commits exist |

### 6. Git State Dependencies Table

| Operation | Clean Required | Safe During Changes | Conflict Handling |
|-----------|----------------|---------------------|-------------------|
| `git sync` | No | Yes (reads only) | Warns on divergence |
| Branch create | No | Yes | Fails if exists |
| Branch delete | Yes | No | Refuses if unmerged |
| Hook install | No | Yes | Overwrites existing |
| YAML update | No | Yes | Atomic write |
| Commit parse | No | Yes | Read-only |
| Status update | No | Yes | Checks current status |
| Sprint tag | No | Yes | Fails if exists |

### 7. Remote Coordination Strategy

| Flow | Local Action | Remote Notification | Databricks Integration |
|------|--------------|---------------------|------------------------|
| Commit | Git commit with hooks | Webhook to remote API | Repos API sync trigger |
| Push | Git push | CI/CD pipeline | Repos API pull |
| PR Open | GitHub PR create | Webhook | Repos API sync |
| PR Merge | GitHub merge | CI/CD + webhook | Repos API pull + sync |
| Status Update | YAML update | Sync to remote DB | Delta Lake update |
| Sprint Start | Tag creation | Webhook | Repos state update |
| Sprint Complete | Tag creation | Webhook | Delta Lake update |

**Remote Git Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REMOTE GIT COORDINATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  LOCAL MACHINE                    GITHUB                     DATABRICKS
  ─────────────────               ────────                    ──────────

┌─────────────────┐           ┌─────────────┐           ┌─────────────────┐
│ git commit      │──push────▶│ Repository  │◀─webhook─▶│ Repos API       │
│ (with hooks)    │           │             │           │                 │
└────────┬────────┘           └──────┬──────┘           └────────┬────────┘
         │                           │                           │
         │ Hooks validate            │ Actions CI                │ Auto-sync
         │ Parse task refs           │ Run tests                 │ to workspace
         ▼                           ▼                           ▼
┌─────────────────┐           ┌─────────────┐           ┌─────────────────┐
│ YAML updates    │           │ Build/Test  │           │ /Repos/project  │
│ Task status     │           │ Deploy      │           │ (workspace copy)│
└─────────────────┘           └─────────────┘           └─────────────────┘
         │                                                       │
         │ Local state                               Remote state│
         ▼                                                       ▼
┌─────────────────┐                               ┌─────────────────┐
│ roadmap.db      │◀──────── Sync ───────────────▶│ Delta Lake      │
│ (SQLite)        │                               │ (roadmap tables)│
└─────────────────┘                               └─────────────────┘
```

### 8. Credential Management Table

| Context | Method | Storage | Security |
|---------|--------|---------|----------|
| Local git | SSH keys | `~/.ssh/` | File permissions |
| Local git | Credentials helper | macOS Keychain | OS-managed |
| GitHub API | Personal Access Token | Environment variable | Encrypted in CI |
| Databricks | PAT or OAuth | Environment / Unity Catalog | Workspace scoped |
| CI/CD | Secrets | GitHub Secrets | Encrypted at rest |
| Hooks | None needed | N/A | Local execution only |

## Git Operation Modules Inventory

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `commit_parser.py` | Parse commit messages | `CommitParser`, `ParsedCommit` |
| `commit_parser_schema.py` | Parser data models | `TaskReference`, `ParseResult` |
| `branch_linker.py` | Branch-task linking | `BranchLinker`, `BranchInfo` |
| `git_sync.py` | Git-primary sync | `GitPrimarySync`, `SyncResult` |
| `status_updater.py` | Auto status update | `TaskStatusUpdater`, `StatusUpdate` |
| `sprint_tagger.py` | Sprint tag management | `SprintTagger` |
| `tag_parser.py` | Parse git tags | Tag extraction |
| `tag_repair.py` | Fix tag inconsistencies | Tag repair utilities |
| `commit_evidence.py` | Store commit refs | Evidence linking |
| `velocity_calculator.py` | Sprint velocity | Velocity metrics |
| `merge_checker.py` | Check merge safety | Merge validation |
| `merge_ordering.py` | PR merge order | Dependency ordering |
| `pr_generator.py` | Generate PRs | PR creation utilities |
| `ci_integration.py` | CI/CD integration | Pipeline utilities |
| `log_analyzer.py` | Analyze git log | Log parsing |
| `yaml_analyzer.py` | YAML file analysis | YAML utilities |
| `state_reconstructor.py` | Rebuild state from git | State reconstruction |
| `mode_detector.py` | Detect sync mode | Mode detection |
| `strategy_adoption.py` | Sync strategy | Strategy selection |
| `blocker_enforcer.py` | Enforce blockers | Blocker validation |
| `error_handler.py` | Git error handling | Error utilities |
| `cli_change_tracker.py` | Track CLI changes | Change tracking |

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Hooks run locally only | Map to CI/CD pipelines | M | Critical |
| Git-primary sync is local | Add remote sync endpoint | M | High |
| Branch linking is local | Sync branch state to remote | S | Medium |
| Credentials are local | Use Databricks service principal | S | High |
| Commit parsing is portable | Run in remote compute | S | Low |
| 23 git modules available | Most can run remotely | M | Medium |
| Tag creation is local | Remote tag via API | S | Medium |
| Databricks Repos supports git | Leverage Repos API | M | Critical |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Git hooks table lists >= 3 hook types: PASS (4 hooks + 1 optional)
- [x] Git operations table lists >= 5 operations: PASS (10 operations)
- [x] Branch management documents naming conventions: PASS (5 patterns)
- [x] Remote coordination addresses Databricks Repos: PASS (Repos API integration)

## References

- `vibey/operations/git/commit_parser.py:29-88` - CommitParser class
- `vibey/operations/git/branch_linker.py:50-100` - BranchLinker class
- `vibey/operations/git/git_sync.py:67-96` - GitPrimarySync class
- `vibey/operations/git/status_updater.py:43-80` - TaskStatusUpdater class
- `.git/hooks/pre-commit:1-50` - Pre-commit hook
- `.git/hooks/commit-msg:1-46` - Commit-msg hook
- `.git/hooks/post-commit:1-30` - Post-commit hook
