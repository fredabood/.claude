# CLI Reference

**Version:** 2.5.0
**Total Commands:** 200
**Generated:** 2025-12-15T23:21:29.641766+00:00

This document provides comprehensive reference documentation for all `vibey` CLI commands.

---

## Table of Contents

- [artifact](#artifact)
  - [adopt](#artifact-adopt)
  - [delete](#artifact-delete)
  - [impact](#artifact-impact)
  - [list](#artifact-list)
  - [orphans](#artifact-orphans)
  - *... and 3 more*
- [audit](#audit)
  - [classify](#audit-classify)
  - [inventory](#audit-inventory)
- [auth](#auth)
  - [add-signer](#auth-add-signer)
  - [export](#auth-export)
  - [init-project](#auth-init-project)
  - [list](#auth-list)
  - [revoke](#auth-revoke)
  - *... and 2 more*
- [config](#config)
  - [migrate](#config-migrate)
  - [platform](#config-platform)
  - [rollback](#config-rollback)
  - [show](#config-show)
  - [validate](#config-validate)
- [content](#content)
  - [create](#content-create)
  - [delete](#content-delete)
  - [edit](#content-edit)
  - [list](#content-list)
  - [search](#content-search)
  - *... and 2 more*
- [context](#context)
  - [archive](#context-archive)
  - [clean](#context-clean)
  - [export](#context-export)
  - [init](#context-init)
  - [list](#context-list)
  - *... and 2 more*
- [deploy](#deploy)
  - [list](#deploy-list)
  - [run](#deploy-run)
- [discover](#discover)
  - [diff](#discover-diff)
  - [history](#discover-history)
  - [refresh](#discover-refresh)
  - [run](#discover-run)
  - [show](#discover-show)
  - *... and 1 more*
- [docs](#docs)
  - [check-drift](#docs-check-drift)
  - [check-mcp-drift](#docs-check-mcp-drift)
  - [generate](#docs-generate)
  - [generate-cli](#docs-generate-cli)
  - [generate-mcp](#docs-generate-mcp)
  - *... and 2 more*
- [export](#export)
  - [gemini](#export-gemini)
  - [list](#export-list)
  - [run](#export-run)
  - [stats](#export-stats)
- [git](#git)
  - [analyze](#git-analyze)
  - [branch](#git-branch)
  - [check-merge](#git-check-merge)
  - [contributors](#git-contributors)
  - [history](#git-history)
  - *... and 20 more*
- [roadmap](#roadmap)
  - [activity](#roadmap-activity)
  - [add-commit](#roadmap-add-commit)
  - [add-context](#roadmap-add-context)
  - [add-standard](#roadmap-add-standard)
  - [audit](#roadmap-audit)
  - *... and 41 more*
- [session](#session)
  - [decisions](#session-decisions)
  - [end](#session-end)
  - [export](#session-export)
  - [list](#session-list)
  - [pause](#session-pause)
  - *... and 6 more*
- [validate](#validate)
  - [assets](#validate-assets)
  - [docs](#validate-docs)

---

## Command Index


**A**
- [`vibey artifact`](#vibey-artifact) - 
Manage artifacts - first-class file-based entitie...
- [`vibey artifact adopt`](#vibey-artifact-adopt) - Register an existing file as an artifact.

**D**
- [`vibey artifact delete`](#vibey-artifact-delete) - Delete an artifact from the registry (does not del...

**I**
- [`vibey artifact impact`](#vibey-artifact-impact) - Show tickets affected by changes to given files.

**L**
- [`vibey artifact list`](#vibey-artifact-list) - List all registered artifacts.

**O**
- [`vibey artifact orphans`](#vibey-artifact-orphans) - Show artifacts not referenced by any ticket.

**R**
- [`vibey artifact refresh`](#vibey-artifact-refresh) - Refresh content hashes for all artifacts.

**S**
- [`vibey artifact show`](#vibey-artifact-show) - Show details of a specific artifact.
- [`vibey artifact stale`](#vibey-artifact-stale) - Show stale documentation artifacts.

**A**
- [`vibey audit`](#vibey-audit) - 
Audit and analyze codebase structure, documentati...

**C**
- [`vibey audit classify`](#vibey-audit-classify) - Classify files according to taxonomy.

Analyzes fi...

**I**
- [`vibey audit inventory`](#vibey-audit-inventory) - Generate file inventory for codebase audit.

Scans...

**A**
- [`vibey auth`](#vibey-auth) - 
Manage authentication keys for roadmap signing.

...
- [`vibey auth add-signer`](#vibey-auth-add-signer) - Add an authorized signer to this project.

Registe...

**E**
- [`vibey auth export`](#vibey-auth-export) - Export your public key for sharing with project ow...

**I**
- [`vibey auth init-project`](#vibey-auth-init-project) - Initialize signing for this project.

Sets you up ...

**L**
- [`vibey auth list`](#vibey-auth-list) - List authorized signers for this project.

Shows a...

**R**
- [`vibey auth revoke`](#vibey-auth-revoke) - Revoke a signer's authorization.

Marks a signer a...

**S**
- [`vibey auth setup`](#vibey-auth-setup) - Generate Ed25519 keypair for signing roadmap chang...
- [`vibey auth status`](#vibey-auth-status) - Show current authentication status.

Displays whet...

**C**
- [`vibey config`](#vibey-config) - 
Manage framework configuration.

Examples:

  vib...

**M**
- [`vibey config migrate`](#vibey-config-migrate) - Migrate legacy config to modular format

**P**
- [`vibey config platform`](#vibey-config-platform) - 
Manage platform detection and configuration.

The...

**C**
- [`vibey config platform clear`](#vibey-config-platform-clear) - Clear platform configuration

Removes manual platf...

**D**
- [`vibey config platform detect`](#vibey-config-platform-detect) - Force platform re-detection

Runs platform detecti...

**L**
- [`vibey config platform list`](#vibey-config-platform-list) - List known platforms

Shows all platforms that Vib...

**S**
- [`vibey config platform set`](#vibey-config-platform-set) - Set platform configuration manually

Override auto...
- [`vibey config platform show`](#vibey-config-platform-show) - Show current platform configuration

Displays the ...

**R**
- [`vibey config rollback`](#vibey-config-rollback) - Rollback to a previous config backup

**S**
- [`vibey config show`](#vibey-config-show) - Show current configuration

**V**
- [`vibey config validate`](#vibey-config-validate) - Validate configuration files

**C**
- [`vibey content`](#vibey-content) - 
Manage framework content (agents, workflows, temp...
- [`vibey content create`](#vibey-content-create) - Create new content

Creates a new agent, workflow,...

**D**
- [`vibey content delete`](#vibey-content-delete) - Delete content (moves to trash)

Removes content b...

**E**
- [`vibey content edit`](#vibey-content-edit) - Edit existing content

Updates frontmatter fields ...

**L**
- [`vibey content list`](#vibey-content-list) - List all content items

Shows all agents, workflow...

**S**
- [`vibey content search`](#vibey-content-search) - Search content by keywords

Searches content by na...
- [`vibey content show`](#vibey-content-show) - Show content details

Displays metadata and option...

**V**
- [`vibey content validate`](#vibey-content-validate) - Validate content frontmatter

Checks content for r...

**C**
- [`vibey context`](#vibey-context) - Context management - manage session, task, and dec...

**A**
- [`vibey context archive`](#vibey-context-archive) - Archive context to history.

Moves context from cu...

**C**
- [`vibey context clean`](#vibey-context-clean) - Clean old archived context.

Removes archived cont...

**E**
- [`vibey context export`](#vibey-context-export) - Export context to file.

Examples:
  vibey context...

**I**
- [`vibey context init`](#vibey-context-init) - Initialize context directory structure.

Creates t...

**L**
- [`vibey context list`](#vibey-context-list) - List context items.

Examples:
  vibey context lis...

**S**
- [`vibey context search`](#vibey-context-search) - Search context by content.

Examples:
  vibey cont...
- [`vibey context show`](#vibey-context-show) - Show context details.

Examples:
  vibey context s...

**D**
- [`vibey deploy`](#vibey-deploy) - 
Deploy framework to target platforms.

Supports m...

**L**
- [`vibey deploy list`](#vibey-deploy-list) - List available deployment platforms

**R**
- [`vibey deploy run`](#vibey-deploy-run) - Deploy framework to specified platform

**D**
- [`vibey discover`](#vibey-discover) - 
Project discovery - analyze structure, dependenci...
- [`vibey discover diff`](#vibey-discover-diff) - Compare two discovery versions.

Shows differences...

**H**
- [`vibey discover history`](#vibey-discover-history) - List discovery version history.

Shows previous di...

**R**
- [`vibey discover refresh`](#vibey-discover-refresh) - Refresh discovery if stale.

Re-runs discovery onl...
- [`vibey discover run`](#vibey-discover-run) - Run project discovery and analyze the codebase.

A...

**S**
- [`vibey discover show`](#vibey-discover-show) - Show current discovery output.

Displays the most ...
- [`vibey discover status`](#vibey-discover-status) - Check if current discovery is stale.

Reports whet...

**D**
- [`vibey docs`](#vibey-docs) - 
Generate and manage documentation.

Examples:

  ...

**C**
- [`vibey docs check-drift`](#vibey-docs-check-drift) - 
Check if CLI documentation has drifted from imple...
- [`vibey docs check-mcp-drift`](#vibey-docs-check-mcp-drift) - 
Check if MCP documentation has drifted from imple...

**G**
- [`vibey docs generate`](#vibey-docs-generate) - Generate documentation from configuration
- [`vibey docs generate-cli`](#vibey-docs-generate-cli) - 
Auto-generate CLI reference documentation from co...
- [`vibey docs generate-mcp`](#vibey-docs-generate-mcp) - 
Auto-generate MCP server reference documentation ...

**I**
- [`vibey docs introspect`](#vibey-docs-introspect) - 
Introspect CLI structure and output documentation...
- [`vibey docs introspect-mcp`](#vibey-docs-introspect-mcp) - 
Introspect MCP server structure and output docume...

**E**
- [`vibey export`](#vibey-export) - 
Export Vibey assets to platform-specific formats....

**G**
- [`vibey export gemini`](#vibey-export-gemini) - Export Vibey to Gemini Code Assist extension forma...

**L**
- [`vibey export list`](#vibey-export-list) - List available export platforms

Shows all platfor...

**R**
- [`vibey export run`](#vibey-export-run) - Export assets to platform format

Generates platfo...

**S**
- [`vibey export stats`](#vibey-export-stats) - Show export statistics

Displays counts of tools, ...

**G**
- [`vibey git`](#vibey-git) - 
Analyze Git history for roadmap references.

Extr...

**A**
- [`vibey git analyze`](#vibey-git-analyze) - 
Analyze Git history for roadmap references.

Pars...

**B**
- [`vibey git branch`](#vibey-git-branch) - 
Manage task-branch linking.

Create branches with...

**C**
- [`vibey git branch create`](#vibey-git-branch-create) - 
Create a branch for a task with proper naming.

C...

**L**
- [`vibey git branch link`](#vibey-git-branch-link) - 
Link an existing branch to a task.

Records branc...
- [`vibey git branch list`](#vibey-git-branch-list) - 
List all branches following Vibey naming conventi...

**S**
- [`vibey git branch status`](#vibey-git-branch-status) - 
Show branch-task linkage status.

Displays which ...

**U**
- [`vibey git branch unlink`](#vibey-git-branch-unlink) - 
Unlink a branch from a task.

Removes branch meta...

**C**
- [`vibey git check-merge`](#vibey-git-check-merge) - 
Check for task completion conflicts before mergin...
- [`vibey git contributors`](#vibey-git-contributors) - 
Show contributor activity and statistics.

Analyz...

**H**
- [`vibey git history`](#vibey-git-history) - 
Show change history for an item.

Tracks how a ta...
- [`vibey git hooks`](#vibey-git-hooks) - 
Manage Git hooks for Vibey roadmap integration.

...

**I**
- [`vibey git hooks install`](#vibey-git-hooks-install) - 
Install Git hooks for Vibey roadmap integration.
...

**S**
- [`vibey git hooks status`](#vibey-git-hooks-status) - 
Show Git hooks installation status.

Displays whi...

**U**
- [`vibey git hooks uninstall`](#vibey-git-hooks-uninstall) - 
Uninstall Vibey Git hooks.

Removes pre-commit an...
- [`vibey git hooks update`](#vibey-git-hooks-update) - 
Update installed Git hooks to latest version.

Re...

**L**
- [`vibey git link-commit`](#vibey-git-link-commit) - 
Link a commit to a task and optionally update sta...

**M**
- [`vibey git mode`](#vibey-git-mode) - 
Show current source-of-truth mode and reasoning.
...

**P**
- [`vibey git pr-description`](#vibey-git-pr-description) - 
Generate PR description from task context.

Reads...
- [`vibey git progress`](#vibey-git-progress) - 
Show sprint progress over time (burndown chart).
...

**R**
- [`vibey git repair`](#vibey-git-repair) - 
Detect and repair roadmap inconsistencies.

Attem...
- [`vibey git repair-tags`](#vibey-git-repair-tags) - 
Automatically repair dangling tags.

Searches for...
- [`vibey git rollback`](#vibey-git-rollback) - 
Rollback roadmap to state at ref.

Restores all r...

**S**
- [`vibey git sprint`](#vibey-git-sprint) - 
Manage sprint boundary tags.

Create and manage g...

**D**
- [`vibey git sprint delete`](#vibey-git-sprint-delete) - 
Delete a sprint boundary tag.

Removes a sprint s...

**E**
- [`vibey git sprint end`](#vibey-git-sprint-end) - 
Create sprint end tag at current or specified com...

**L**
- [`vibey git sprint list`](#vibey-git-sprint-list) - 
List sprint tags, optionally filtered by sprint I...

**R**
- [`vibey git sprint range`](#vibey-git-sprint-range) - 
Show commit range for a sprint (start tag to end ...

**S**
- [`vibey git sprint start`](#vibey-git-sprint-start) - 
Create sprint start tag at current or specified c...
- [`vibey git state-at`](#vibey-git-state-at) - 
Show roadmap state at a specific ref.

Reconstruc...
- [`vibey git sync`](#vibey-git-sync) - 
Sync roadmap YAML from Git state (Git-primary mod...

**T**
- [`vibey git tag-move`](#vibey-git-tag-move) - 
Manually move a tag to a different commit.

Delet...
- [`vibey git tag-range`](#vibey-git-tag-range) - 
Get commits between boundary tags.

Retrieves com...
- [`vibey git tags`](#vibey-git-tags) - 
List Vibey roadmap tags.

Shows all Vibey tags (s...
- [`vibey git tasks`](#vibey-git-tasks) - 
Show commits for a specific task.

Lists all comm...

**U**
- [`vibey git update-status`](#vibey-git-update-status) - 
Update task status based on commit messages.

Par...

**V**
- [`vibey git validate`](#vibey-git-validate) - 
Validate git strategy requirements.

Checks that ...
- [`vibey git validate-roadmap`](#vibey-git-validate-roadmap) - 
Validate roadmap YAML files and consistency.

Che...
- [`vibey git validate-tags`](#vibey-git-validate-tags) - 
Detect dangling tags (pointing to missing commits...
- [`vibey git velocity`](#vibey-git-velocity) - 
Calculate sprint velocity metrics.

Analyzes comm...

**R**
- [`vibey roadmap`](#vibey-roadmap) - 
Manage roadmap system - tracks, sprints, tasks, a...

**A**
- [`vibey roadmap activity`](#vibey-roadmap-activity) - Show recent roadmap activity in a compact format.
...
- [`vibey roadmap add-commit`](#vibey-roadmap-add-commit) - Add a git commit to a task

Examples:
  vibey road...
- [`vibey roadmap add-context`](#vibey-roadmap-add-context) - Add a context file to a roadmap object

Context fi...
- [`vibey roadmap add-standard`](#vibey-roadmap-add-standard) - Add a new standard to roadmap/track/sprint

Create...
- [`vibey roadmap audit`](#vibey-roadmap-audit) - 
View and analyze roadmap change audit trail.

Tra...

**L**
- [`vibey roadmap audit log`](#vibey-roadmap-audit-log) - Show recent audit trail entries

Display the most ...

**R**
- [`vibey roadmap audit report`](#vibey-roadmap-audit-report) - Generate detailed audit report

Create a comprehen...

**S**
- [`vibey roadmap audit show`](#vibey-roadmap-audit-show) - Show change history for a specific object

Display...
- [`vibey roadmap audit suspicious`](#vibey-roadmap-audit-suspicious) - Detect suspicious changes in audit trail

Find pot...

**A**
- [`vibey roadmap auto-progress`](#vibey-roadmap-auto-progress) - Check or apply automatic status progressions.

Aut...

**B**
- [`vibey roadmap bulk`](#vibey-roadmap-bulk) - 
Bulk operations on roadmap items.

Commands for p...

**C**
- [`vibey roadmap bulk complete-sprint`](#vibey-roadmap-bulk-complete-sprint) - Mark all tasks in a sprint as completed.

Complete...
- [`vibey roadmap check-compatibility`](#vibey-roadmap-check-compatibility) - Check if sprint tasks fit in your platform's conte...
- [`vibey roadmap check-hooks`](#vibey-roadmap-check-hooks) - Check git hook installation status

Shows whether ...
- [`vibey roadmap check-standards`](#vibey-roadmap-check-standards) - Check which standards apply to an item

Validates ...
- [`vibey roadmap checkpoint`](#vibey-roadmap-checkpoint) - 
Manage roadmap integrity checkpoints.

Create, re...
- [`vibey roadmap checkpoint clean`](#vibey-roadmap-checkpoint-clean) - Clean old checkpoints

Removes old checkpoints whi...
- [`vibey roadmap checkpoint compare`](#vibey-roadmap-checkpoint-compare) - Compare two checkpoints

Shows files added, remove...
- [`vibey roadmap checkpoint create`](#vibey-roadmap-checkpoint-create) - Create a new integrity checkpoint

Creates a times...

**L**
- [`vibey roadmap checkpoint list`](#vibey-roadmap-checkpoint-list) - List all available checkpoints

Shows checkpoint n...

**R**
- [`vibey roadmap checkpoint restore`](#vibey-roadmap-checkpoint-restore) - Restore from a checkpoint

Restores .vibey/ direct...

**V**
- [`vibey roadmap checkpoint verify`](#vibey-roadmap-checkpoint-verify) - Verify checkpoint integrity

Validates all files m...

**C**
- [`vibey roadmap complete`](#vibey-roadmap-complete) - Complete a track, sprint, or task

For sprints, va...
- [`vibey roadmap context`](#vibey-roadmap-context) - Get AI-optimized context for a task
- [`vibey roadmap create-from-plan`](#vibey-roadmap-create-from-plan) - Create roadmap sprint from a plan markdown file

P...
- [`vibey roadmap create-sprint`](#vibey-roadmap-create-sprint) - Create a new sprint in a track.

Creates a new spr...
- [`vibey roadmap create-task`](#vibey-roadmap-create-task) - Create a new task in a sprint.

Creates a new task...
- [`vibey roadmap create-track`](#vibey-roadmap-create-track) - Create a new track in the roadmap.

Creates a new ...

**D**
- [`vibey roadmap db`](#vibey-roadmap-db) - 
Database operations for roadmap state management....

**B**
- [`vibey roadmap db backup`](#vibey-roadmap-db-backup) - Create a backup of the database.

Creates a timest...

**C**
- [`vibey roadmap db config`](#vibey-roadmap-db-config) - Show current backend configuration.

Displays the ...

**D**
- [`vibey roadmap db dump`](#vibey-roadmap-db-dump) - Dump database state to YAML files.

Exports the cu...

**I**
- [`vibey roadmap db init`](#vibey-roadmap-db-init) - Initialize SQLite database from YAML files.

Creat...

**Q**
- [`vibey roadmap db query`](#vibey-roadmap-db-query) - Query the database for roadmap insights.

These co...

**B**
- [`vibey roadmap db query blocked`](#vibey-roadmap-db-query-blocked) - List all blocked tasks with blocker information.

...

**D**
- [`vibey roadmap db query deps`](#vibey-roadmap-db-query-deps) - Show dependency chain for a task, sprint, or track...

**P**
- [`vibey roadmap db query progress`](#vibey-roadmap-db-query-progress) - Show progress summary grouped by track, sprint, or...

**S**
- [`vibey roadmap db query stats`](#vibey-roadmap-db-query-stats) - Show overall roadmap statistics.

Displays complet...

**R**
- [`vibey roadmap db rebuild`](#vibey-roadmap-db-rebuild) - Rebuild database from YAML files.

Drops all table...

**S**
- [`vibey roadmap db status`](#vibey-roadmap-db-status) - Show database status and health.

Displays:
- Data...

**V**
- [`vibey roadmap db validate`](#vibey-roadmap-db-validate) - Validate database integrity and consistency.

Vali...

**D**
- [`vibey roadmap doc-changelog`](#vibey-roadmap-doc-changelog) - Generate a documentation changelog

Generates a ma...

**E**
- [`vibey roadmap edit`](#vibey-roadmap-edit) - 
Safe YAML editing with automatic validation and b...

**B**
- [`vibey roadmap edit bulk`](#vibey-roadmap-edit-bulk) - Bulk edit multiple YAML files with transaction sem...

**F**
- [`vibey roadmap edit file`](#vibey-roadmap-edit-file) - Edit a single YAML file safely

Modifies fields us...

**R**
- [`vibey roadmap edit rollback`](#vibey-roadmap-edit-rollback) - Rollback recent edit operations

Restores files fr...

**V**
- [`vibey roadmap edit validate`](#vibey-roadmap-edit-validate) - Validate YAML file(s)

Validates YAML syntax, sche...

**E**
- [`vibey roadmap extract-embedded`](#vibey-roadmap-extract-embedded) - Extract embedded tasks from sprint files to standa...

**I**
- [`vibey roadmap init`](#vibey-roadmap-init) - Initialize a new roadmap in .vibey/roadmap.yaml
- [`vibey roadmap install-hooks`](#vibey-roadmap-install-hooks) - Install git pre-commit hook for roadmap validation...

**L**
- [`vibey roadmap link-doc`](#vibey-roadmap-link-doc) - Link a documentation file to a roadmap object

Cre...
- [`vibey roadmap list-docs`](#vibey-roadmap-list-docs) - List all tracked documentation files

Shows all do...

**M**
- [`vibey roadmap migrate-docs`](#vibey-roadmap-migrate-docs) - Migrate documentation fields from YAML to markdown...
- [`vibey roadmap migrate-format`](#vibey-roadmap-migrate-format) - Migrate YAML files from v1 format to v2 format.

V...

**O**
- [`vibey roadmap override-standard`](#vibey-roadmap-override-standard) - Override a standard for a specific item

Adds an o...

**R**
- [`vibey roadmap recalculate`](#vibey-roadmap-recalculate) - Recalculate sprint tasks for a different platform
...
- [`vibey roadmap reconcile`](#vibey-roadmap-reconcile) - Detect and fix status inconsistencies in roadmap d...
- [`vibey roadmap repair`](#vibey-roadmap-repair) - Auto-repair common roadmap integrity issues

Repai...
- [`vibey roadmap revert`](#vibey-roadmap-revert) - Revert a track, sprint, or task to a previous stat...

**S**
- [`vibey roadmap show`](#vibey-roadmap-show) - Show details for a track, sprint, or task

For spr...
- [`vibey roadmap start`](#vibey-roadmap-start) - Start a sprint or task

When starting a sprint, ch...
- [`vibey roadmap status`](#vibey-roadmap-status) - Show roadmap status - tracks, sprints, and tasks
- [`vibey roadmap summarize`](#vibey-roadmap-summarize) - Summarize a sprint, task, or track
- [`vibey roadmap sync`](#vibey-roadmap-sync) - Sync status from individual files to main roadmap....
- [`vibey roadmap sync-commits`](#vibey-roadmap-sync-commits) - Scan git history and link commits to tasks based o...
- [`vibey roadmap sync-docs`](#vibey-roadmap-sync-docs) - Synchronize documentation from .vibey/roadmap/ to ...

**U**
- [`vibey roadmap uninstall-hooks`](#vibey-roadmap-uninstall-hooks) - Uninstall git pre-commit hook

Removes the Vibey p...

**V**
- [`vibey roadmap validate-advanced`](#vibey-roadmap-validate-advanced) - Advanced validation for complex integrity issues

...
- [`vibey roadmap validate-commits`](#vibey-roadmap-validate-commits) - Validate that all completed tasks have commit evid...
- [`vibey roadmap validate-fast`](#vibey-roadmap-validate-fast) - Fast roadmap validation with caching and parallel ...
- [`vibey roadmap validate-structure`](#vibey-roadmap-validate-structure) - Validate roadmap directory structure is flat (no U...
- [`vibey roadmap verify-change`](#vibey-roadmap-verify-change) - Verify a roadmap file change has a matching activi...
- [`vibey roadmap verify-commits`](#vibey-roadmap-verify-commits) - Verify roadmap changes in a commit range have acti...

**S**
- [`vibey session`](#vibey-session) - 
Manage AI-assisted coding sessions.

Track sessio...

**D**
- [`vibey session decisions`](#vibey-session-decisions) - Show decisions made during a session.

Lists all d...

**E**
- [`vibey session end`](#vibey-session-end) - End the current or specified session.

Marks the s...
- [`vibey session export`](#vibey-session-export) - Export session for continuation.

Exports session ...

**L**
- [`vibey session list`](#vibey-session-list) - List sessions with optional filters.

Shows all se...

**P**
- [`vibey session pause`](#vibey-session-pause) - Pause the current or specified session.

Temporari...

**R**
- [`vibey session report`](#vibey-session-report) - Generate a session report.

Creates a human-readab...
- [`vibey session resume`](#vibey-session-resume) - Resume a paused session.

Continues a previously p...

**S**
- [`vibey session show`](#vibey-session-show) - Show detailed information about a specific session...
- [`vibey session start`](#vibey-session-start) - Start a new coding session.

Creates a new session...
- [`vibey session status`](#vibey-session-status) - Show the current active session status.

Displays ...

**T**
- [`vibey session timeline`](#vibey-session-timeline) - Show session timeline of events.

Displays a chron...

**V**
- [`vibey validate`](#vibey-validate) - 
Validate framework assets and documentation.

Run...

**A**
- [`vibey validate assets`](#vibey-validate-assets) - Validate asset frontmatter (agents, workflows, han...

**D**
- [`vibey validate docs`](#vibey-validate-docs) - Validate documentation organization in roadmap

En...

---

## Command Reference

<a id="vibey-artifact"></a>

### `vibey artifact`

Manage artifacts - first-class file-based entities.

Artifacts are registered files that can be tracked, linked to tickets,
and monitored for staleness. Use these commands to manage the artifact
registry.

**Usage:**
```bash
vibey artifact COMMAND
```

**Examples:**

```bash
vibey artifact list              # List all artifacts
```

```bash
vibey artifact show <id>         # Show artifact details
```

```bash
vibey artifact adopt <path>      # Register a file as artifact
```

```bash
vibey artifact orphans           # Show unreferenced artifacts
```

```bash
vibey artifact stale             # Show stale documentation
```

```bash
vibey artifact impact <files>    # Show affected tickets
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `adopt` | Register an existing file as an artifact. |
| `delete` | Delete an artifact from the registry (does not delete files)... |
| `impact` | Show tickets affected by changes to given files. |
| `list` | List all registered artifacts. |
| `orphans` | Show artifacts not referenced by any ticket. |
| `refresh` | Refresh content hashes for all artifacts. |
| `show` | Show details of a specific artifact. |
| `stale` | Show stale documentation artifacts. |

---

<a id="vibey-artifact-adopt"></a>

#### `vibey artifact adopt`

Register an existing file as an artifact.

**Usage:**
```bash
vibey artifact adopt [OPTIONS] <FILE_PATH>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE_PATH` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['agent', 'code', 'config', 'context', 'data', 'documentation', 'media', 'template', 'test', 'workflow']) | - | Artifact type classification |
| `--name, -n` | TEXT | - | Optional name (defaults to filename) |
| `--subtype, -s` | TEXT | - | Optional subtype for more specific classification |

---

<a id="vibey-artifact-delete"></a>

#### `vibey artifact delete`

Delete an artifact from the registry (does not delete files).

**Usage:**
```bash
vibey artifact delete [OPTIONS] <ARTIFACT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ARTIFACT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force, -f` | flag | `False` | Delete without confirmation |

---

<a id="vibey-artifact-impact"></a>

#### `vibey artifact impact`

Show tickets affected by changes to given files.

**Usage:**
```bash
vibey artifact impact [OPTIONS] [FILES]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILES` | TEXT | No |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['json', 'simple', 'table']) | `table` | Output format |

---

<a id="vibey-artifact-list"></a>

#### `vibey artifact list`

List all registered artifacts.

**Usage:**
```bash
vibey artifact list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | TEXT | - | Filter by artifact type (code, documentation, test, etc.) |
| `--format, -f` | Choice(['json', 'simple', 'table']) | `table` | Output format |

---

<a id="vibey-artifact-orphans"></a>

#### `vibey artifact orphans`

Show artifacts not referenced by any ticket.

**Usage:**
```bash
vibey artifact orphans [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['simple', 'table']) | `table` | Output format |

---

<a id="vibey-artifact-refresh"></a>

#### `vibey artifact refresh`

Refresh content hashes for all artifacts.

**Usage:**
```bash
vibey artifact refresh
```

---

<a id="vibey-artifact-show"></a>

#### `vibey artifact show`

Show details of a specific artifact.

**Usage:**
```bash
vibey artifact show <ARTIFACT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ARTIFACT_ID` | TEXT | Yes |  |

---

<a id="vibey-artifact-stale"></a>

#### `vibey artifact stale`

Show stale documentation artifacts.

**Usage:**
```bash
vibey artifact stale [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['simple', 'table']) | `table` | Output format |

---

<a id="vibey-audit"></a>

### `vibey audit`

Audit and analyze codebase structure, documentation coverage, and file classification.

The audit system provides tools for:
- File inventory generation
- File classification by purpose and type
- Dependency analysis
- Documentation coverage analysis
- Test coverage mapping

**Usage:**
```bash
vibey audit COMMAND
```

**Examples:**

```bash
vibey audit inventory             # Generate file inventory
```

```bash
vibey audit inventory --output FILE  # Save to specific file
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `classify` | Classify files according to taxonomy.

Analyzes files in spe... |
| `inventory` | Generate file inventory for codebase audit.

Scans specified... |

---

<a id="vibey-audit-classify"></a>

#### `vibey audit classify`

Classify files according to taxonomy.

Analyzes files in specified directory and generates a classification
YAML file with category, purpose, dependencies, and coverage info.

**Usage:**
```bash
vibey audit classify [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--directory, -d` | Choice(['all', 'docs', 'tests', 'vibey']) | `vibey` | Directory to classify |
| `--output, -o` | Path(file, dir) | - | Output file path |

**Examples:**

```bash
vibey audit classify                      # Classify vibey/ (default)
```

```bash
vibey audit classify -d docs              # Classify docs/
```

```bash
vibey audit classify -d vibey -o out.yaml # Custom output
```

---

<a id="vibey-audit-inventory"></a>

#### `vibey audit inventory`

Generate file inventory for codebase audit.

Scans specified directories and generates a structured inventory
of all files with metadata (path, type, size, lines, modified time).

**Usage:**
```bash
vibey audit inventory [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Path(file, dir) | - | Output file path (default: .vibey/roadmap/context/.../FILE_INVENTORY.yaml) |
| `--directories, -d` | TEXT | - | Directories to scan (can specify multiple) |
| `--format, -f` | Choice(['json', 'yaml']) | `yaml` | Output format |

**Examples:**

```bash
vibey audit inventory                          # Default directories
```

```bash
vibey audit inventory -d vibey/ -d docs/       # Custom directories
```

```bash
vibey audit inventory --output inventory.yaml  # Custom output path
```

```bash
vibey audit inventory --format json            # JSON output
```

---

<a id="vibey-auth"></a>

### `vibey auth`

Manage authentication keys for roadmap signing.

Set up Ed25519 keypairs for signing activity log entries,
register authorized signers for your project, and manage
signing identity.

Get started:
  vibey auth setup           # Generate your keypair
  vibey auth init-project    # Initialize signing for project
  vibey auth add-signer      # Add team members

**Usage:**
```bash
vibey auth COMMAND
```

**Examples:**

```bash
vibey auth setup --email alice@example.com --name "Alice Smith"
```

```bash
vibey auth list            # List authorized signers
```

```bash
vibey auth export          # Share your public key
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `add-signer` | Add an authorized signer to this project.

Registers a team ... |
| `export` | Export your public key for sharing with project owners.

Dis... |
| `init-project` | Initialize signing for this project.

Sets you up as the fir... |
| `list` | List authorized signers for this project.

Shows all team me... |
| `revoke` | Revoke a signer's authorization.

Marks a signer as inactive... |
| `setup` | Generate Ed25519 keypair for signing roadmap changes.

Creat... |
| `status` | Show current authentication status.

Displays whether you ha... |

---

<a id="vibey-auth-add-signer"></a>

#### `vibey auth add-signer`

Add an authorized signer to this project.

Registers a team member's public key so their changes
can be verified.

Arguments:
  EMAIL       Signer's email address
  NAME        Signer's full name (use quotes)
  PUBLIC_KEY  Public key string (vibey-ed25519 ...)

**Usage:**
```bash
vibey auth add-signer [OPTIONS] <EMAIL> <NAME> <PUBLIC_KEY>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `EMAIL` | TEXT | Yes |  |
| `NAME` | TEXT | Yes |  |
| `PUBLIC_KEY` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--role` | Choice(['admin', 'developer', 'owner']) | `developer` | Signer role |

**Examples:**

```bash
vibey auth add-signer bob@example.com "Bob Jones" "vibey-ed25519 AAAA..."
```

---

<a id="vibey-auth-export"></a>

#### `vibey auth export`

Export your public key for sharing with project owners.

Displays your public key in a format that can be shared
with project owners for authorization.

**Usage:**
```bash
vibey auth export
```

**Examples:**

```bash
vibey auth export | pbcopy  # Copy to clipboard on macOS
```

---

<a id="vibey-auth-init-project"></a>

#### `vibey auth init-project`

Initialize signing for this project.

Sets you up as the first authorized signer (owner).
Requires running 'vibey auth setup' first.

Creates:
  .vibey/authorized-signers/manifest.yaml
  .vibey/authorized-signers/{your-email}.pub

**Usage:**
```bash
vibey auth init-project [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force, -f` | flag | `False` | Reinitialize even if already configured |

**Examples:**

```bash
vibey auth init-project
```

---

<a id="vibey-auth-list"></a>

#### `vibey auth list`

List authorized signers for this project.

Shows all team members who can make signed roadmap changes.

**Usage:**
```bash
vibey auth list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | flag | `False` | Include inactive signers |

**Examples:**

```bash
vibey auth list
```

```bash
vibey auth list --all  # Include revoked signers
```

---

<a id="vibey-auth-revoke"></a>

#### `vibey auth revoke`

Revoke a signer's authorization.

Marks a signer as inactive. Their existing signed changes
remain valid, but new changes won't be accepted.

**Usage:**
```bash
vibey auth revoke [OPTIONS] <EMAIL>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `EMAIL` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--yes, -y` | flag | `False` | Skip confirmation |

**Examples:**

```bash
vibey auth revoke bob@example.com
```

---

<a id="vibey-auth-setup"></a>

#### `vibey auth setup`

Generate Ed25519 keypair for signing roadmap changes.

Creates a keypair in ~/.vibey/ for signing activity log entries.
Your private key never leaves your machine.

**Usage:**
```bash
vibey auth setup [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--email` | TEXT | - | Email for identity |
| `--name` | TEXT | - | Full name for identity |
| `--force, -f` | flag | `False` | Overwrite existing keys |

**Examples:**

```bash
vibey auth setup
```

```bash
vibey auth setup --email alice@example.com --name "Alice Smith"
```

```bash
vibey auth setup --force  # Regenerate keys
```

---

<a id="vibey-auth-status"></a>

#### `vibey auth status`

Show current authentication status.

Displays whether you have keys configured and whether
signing is enabled for the current project.


**Usage:**
```bash
vibey auth status
```

---

<a id="vibey-config"></a>

### `vibey config`

Manage framework configuration.

**Usage:**
```bash
vibey config COMMAND
```

**Examples:**

```bash
vibey config show             # Show current config
```

```bash
vibey config validate         # Validate config files
```

```bash
vibey config migrate          # Migrate old config format
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `migrate` | Migrate legacy config to modular format |
| `platform` | 
Manage platform detection and configuration.

The platform ... |
| `rollback` | Rollback to a previous config backup |
| `show` | Show current configuration |
| `validate` | Validate configuration files |

---

<a id="vibey-config-migrate"></a>

#### `vibey config migrate`

Migrate legacy config to modular format

**Usage:**
```bash
vibey config migrate [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--backup` | flag | `True` | Create backup before migration (default: yes) |
| `--dry-run` | flag | `False` | Show what would be migrated without making changes |
| `--force` | flag | `False` | Overwrite existing modular config if present |

---

<a id="vibey-config-platform"></a>

#### `vibey config platform`

Manage platform detection and configuration.

The platform system automatically detects your AI coding platform
(Claude Code, Goose, Cursor, etc.) and its context window size.

**Usage:**
```bash
vibey config platform COMMAND
```

**Examples:**

```bash
vibey config platform show            # Show current platform
```

```bash
vibey config platform detect          # Force re-detection
```

```bash
vibey config platform set goose       # Set platform manually
```

```bash
vibey config platform set goose --context-window 100000
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `clear` | Clear platform configuration

Removes manual platform config... |
| `detect` | Force platform re-detection

Runs platform detection and sho... |
| `list` | List known platforms

Shows all platforms that Vibey can det... |
| `set` | Set platform configuration manually

Override auto-detection... |
| `show` | Show current platform configuration

Displays the detected p... |

---

<a id="vibey-config-platform-clear"></a>

#### `vibey config platform clear`

Clear platform configuration

Removes manual platform configuration, reverting to auto-detection.

**Usage:**
```bash
vibey config platform clear
```

**Examples:**

```bash
vibey config platform clear
```

---

<a id="vibey-config-platform-detect"></a>

#### `vibey config platform detect`

Force platform re-detection

Runs platform detection and shows results without changing configuration.
Useful for debugging detection issues.

**Usage:**
```bash
vibey config platform detect [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `False` | Show detection details |

**Examples:**

```bash
vibey config platform detect           # Run detection
```

```bash
vibey config platform detect --verbose # Show all detection methods tried
```

---

<a id="vibey-config-platform-list"></a>

#### `vibey config platform list`

List known platforms

Shows all platforms that Vibey can detect and their default context windows.

**Usage:**
```bash
vibey config platform list
```

**Examples:**

```bash
vibey config platform list
```

---

<a id="vibey-config-platform-set"></a>

#### `vibey config platform set`

Set platform configuration manually

Override auto-detection by setting the platform manually.
Useful when detection fails or when using a non-standard configuration.

**Usage:**
```bash
vibey config platform set [OPTIONS] <PLATFORM_NAME>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PLATFORM_NAME` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--context-window, -c` | INTEGER | - | Override context window size (tokens) |

**Examples:**

```bash
vibey config platform set claude-code       # Set to Claude Code
```

```bash
vibey config platform set goose             # Set to Goose
```

```bash
vibey config platform set goose --context-window 100000
```

---

<a id="vibey-config-platform-show"></a>

#### `vibey config platform show`

Show current platform configuration

Displays the detected platform, configured overrides, and effective
platform settings that will be used for compatibility checking.

**Usage:**
```bash
vibey config platform show [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | flag | `False` | Output as JSON |

**Examples:**

```bash
vibey config platform show           # Human-readable output
```

```bash
vibey config platform show --json    # JSON output for scripting
```

---

<a id="vibey-config-rollback"></a>

#### `vibey config rollback`

Rollback to a previous config backup

**Usage:**
```bash
vibey config rollback [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--backup-id` | TEXT | - | Specific backup timestamp to restore (default: latest) |
| `--list` | flag | `False` | List available backups |

---

<a id="vibey-config-show"></a>

#### `vibey config show`

Show current configuration

**Usage:**
```bash
vibey config show
```

---

<a id="vibey-config-validate"></a>

#### `vibey config validate`

Validate configuration files

**Usage:**
```bash
vibey config validate
```

---

<a id="vibey-content"></a>

### `vibey content`

Manage framework content (agents, workflows, templates, handoffs).

Provides CRUD operations for content management with validation,
backups, and search capabilities.

**Usage:**
```bash
vibey content COMMAND
```

**Examples:**

```bash
vibey content list                  # List all content
```

```bash
vibey content list --type agent     # List only agents
```

```bash
vibey content show coordinator      # Show content details
```

```bash
vibey content search "database"     # Search content
```

```bash
vibey content create agent          # Create new agent
```

```bash
vibey content edit coordinator      # Edit existing content
```

```bash
vibey content delete my-agent       # Delete content
```

```bash
vibey content validate              # Validate all content
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `create` | Create new content

Creates a new agent, workflow, template,... |
| `delete` | Delete content (moves to trash)

Removes content by moving i... |
| `edit` | Edit existing content

Updates frontmatter fields in existin... |
| `list` | List all content items

Shows all agents, workflows, templat... |
| `search` | Search content by keywords

Searches content by name, descri... |
| `show` | Show content details

Displays metadata and optionally the f... |
| `validate` | Validate content frontmatter

Checks content for required fi... |

---

<a id="vibey-content-create"></a>

#### `vibey content create`

Create new content

Creates a new agent, workflow, template, or handoff with
validated frontmatter and a starter body.

**Usage:**
```bash
vibey content create [OPTIONS] <CONTENT_TYPE>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTENT_TYPE` | Choice(['agent', 'handoff', 'template', 'workflow']) | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--id` | TEXT | - | Content ID (e.g., my-agent) |
| `--name` | TEXT | - | Display name |
| `--category` | TEXT | - | Category (subdirectory, e.g., core, planning) |
| `--subtype` | TEXT | - | Subtype (e.g., core, planning, development for agents) |
| `--description` | TEXT | `` | Description |
| `--version` | TEXT | `1.0.0` | Version |

**Examples:**

```bash
vibey content create agent --id my-agent --name "My Agent" --category core --subtype core
```

```bash
vibey content create workflow --id my-flow --name "My Workflow" --subtype planning
```

```bash
vibey content create template --id my-template --name "My Template"
```

---

<a id="vibey-content-delete"></a>

#### `vibey content delete`

Delete content (moves to trash)

Removes content by moving it to .vibey/trash/.
Can be restored later if needed.

**Usage:**
```bash
vibey content delete [OPTIONS] <CONTENT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTENT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice(['agent', 'handoff', 'template', 'workflow']) | - | Content type |
| `--force` | flag | `False` | Delete even if referenced by other content |
| `--yes, -y` | flag | `False` | Skip confirmation |

**Examples:**

```bash
vibey content delete my-agent
```

```bash
vibey content delete my-agent --force
```

```bash
vibey content delete my-agent -y
```

---

<a id="vibey-content-edit"></a>

#### `vibey content edit`

Edit existing content

Updates frontmatter fields in existing content.
Creates a backup before making changes.

**Usage:**
```bash
vibey content edit [OPTIONS] <CONTENT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTENT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--set` | TEXT | - | Field=value pairs to update |
| `--type` | Choice(['agent', 'handoff', 'template', 'workflow']) | - | Content type |

**Examples:**

```bash
vibey content edit coordinator --set version=1.1.0
```

```bash
vibey content edit my-agent --set type=core --set "description=New description"
```

---

<a id="vibey-content-list"></a>

#### `vibey content list`

List all content items

Shows all agents, workflows, templates, and other content with
optional filtering by type and category.

**Usage:**
```bash
vibey content list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice(['agent', 'example', 'handoff', 'schema', 'template', 'workflow']) | - | Filter by content type |
| `--category` | TEXT | - | Filter by category (subdirectory) |
| `--format` | Choice(['json', 'simple', 'table']) | `table` | Output format |

**Examples:**

```bash
vibey content list                    # List all content
```

```bash
vibey content list --type agent       # List only agents
```

```bash
vibey content list --type workflow --category planning
```

```bash
vibey content list --format json      # JSON output
```

---

<a id="vibey-content-search"></a>

#### `vibey content search`

Search content by keywords

Searches content by name, description, tags, and body text.
Results are ranked by relevance.

**Usage:**
```bash
vibey content search [OPTIONS] <QUERY>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice(['agent', 'example', 'handoff', 'schema', 'template', 'workflow']) | - | Filter by content type |
| `--category` | TEXT | - | Filter by category |
| `--limit` | INTEGER | `20` | Maximum results |

**Examples:**

```bash
vibey content search "database"
```

```bash
vibey content search "api" --type agent
```

```bash
vibey content search "test" --limit 50
```

---

<a id="vibey-content-show"></a>

#### `vibey content show`

Show content details

Displays metadata and optionally the full body of a content item.

**Usage:**
```bash
vibey content show [OPTIONS] <CONTENT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTENT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice(['agent', 'example', 'handoff', 'schema', 'template', 'workflow']) | - | Content type (speeds up lookup) |
| `--json` | flag | `False` | Output as JSON |
| `--body` | flag | `False` | Include full body text |

**Examples:**

```bash
vibey content show coordinator
```

```bash
vibey content show sprint-planning --type workflow
```

```bash
vibey content show coordinator --body
```

```bash
vibey content show coordinator --json
```

---

<a id="vibey-content-validate"></a>

#### `vibey content validate`

Validate content frontmatter

Checks content for required fields and valid values.

**Usage:**
```bash
vibey content validate [OPTIONS] [CONTENT_ID]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTENT_ID` | TEXT | No |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice(['agent', 'handoff', 'template', 'workflow']) | - | Content type to validate |
| `--all` | flag | `False` | Validate all content |

**Examples:**

```bash
vibey content validate coordinator
```

```bash
vibey content validate --type agent --all
```

```bash
vibey content validate --all
```

---

<a id="vibey-context"></a>

### `vibey context`

Context management - manage session, task, and decision context.

Context provides structured storage for AI-assisted development work:
- Sessions: Track work sessions with goals and artifacts
- Tasks: Capture task execution context with commands and files
- Decisions: Record architectural decisions (ADRs)
- Sprints: Store sprint planning documents and artifacts


**Usage:**
```bash
vibey context COMMAND
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `archive` | Archive context to history.

Moves context from current/acti... |
| `clean` | Clean old archived context.

Removes archived context older ... |
| `export` | Export context to file.

Examples:
  vibey context export 01... |
| `init` | Initialize context directory structure.

Creates the .vibey/... |
| `list` | List context items.

Examples:
  vibey context list
  vibey ... |
| `search` | Search context by content.

Examples:
  vibey context search... |
| `show` | Show context details.

Examples:
  vibey context show 01KC7M... |

---

<a id="vibey-context-archive"></a>

#### `vibey context archive`

Archive context to history.

Moves context from current/active to history directory.

**Usage:**
```bash
vibey context archive [OPTIONS] <CONTEXT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTEXT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['session', 'task']) | - | Context type (required) |

**Examples:**

```bash
vibey context archive 01KC7MN54VXRB3APC5FV5XBDXX --type session
```

```bash
vibey context archive 01KC81GRE7HFXA9J6FYFM7H3BR --type task
```

---

<a id="vibey-context-clean"></a>

#### `vibey context clean`

Clean old archived context.

Removes archived context older than the specified number of days.
Uses --dry-run to preview before deleting.

**Usage:**
```bash
vibey context clean [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['all', 'session', 'task']) | `all` | Context type to clean |
| `--older-than, -d` | INTEGER | `90` | Delete items older than N days |
| `--dry-run` | flag | `False` | Show what would be deleted without deleting |

**Examples:**

```bash
vibey context clean --older-than 90 --dry-run
```

```bash
vibey context clean --type session --older-than 30
```

---

<a id="vibey-context-export"></a>

#### `vibey context export`

Export context to file.

**Usage:**
```bash
vibey context export [OPTIONS] <CONTEXT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTEXT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['decision', 'session', 'sprint', 'task']) | - | Context type |
| `--output, -o` | Path(file, dir) | - | Output file path |

**Examples:**

```bash
vibey context export 01KC7MN54VXRB3APC5FV5XBDXX --type session -o session.yaml
```

```bash
vibey context export user-journey-phase-4-4 --type sprint -o sprint-context.tar.gz
```

---

<a id="vibey-context-init"></a>

#### `vibey context init`

Initialize context directory structure.

Creates the .vibey/context/ directory with proper subdirectories
and initial configuration files.

**Usage:**
```bash
vibey context init
```

**Examples:**

```bash
vibey context init
```

---

<a id="vibey-context-list"></a>

#### `vibey context list`

List context items.

**Usage:**
```bash
vibey context list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['all', 'decision', 'session', 'sprint', 'task']) | `all` | Context type to list |
| `--status, -s` | TEXT | - | Filter by status |
| `--limit, -n` | INTEGER | `20` | Maximum items to show |
| `--format, -f` | Choice(['json', 'table', 'yaml']) | `table` | Output format |

**Examples:**

```bash
vibey context list
```

```bash
vibey context list --type session --status active
```

```bash
vibey context list --type decision --limit 10
```

```bash
vibey context list --format json
```

---

<a id="vibey-context-search"></a>

#### `vibey context search`

Search context by content.

**Usage:**
```bash
vibey context search [OPTIONS] <QUERY>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['all', 'decision', 'session', 'sprint', 'task']) | `all` | Context type to search |
| `--limit, -n` | INTEGER | `20` | Maximum results |

**Examples:**

```bash
vibey context search "ULID naming" --type decision
```

```bash
vibey context search "phase 4" --limit 10
```

---

<a id="vibey-context-show"></a>

#### `vibey context show`

Show context details.

**Usage:**
```bash
vibey context show [OPTIONS] <CONTEXT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CONTEXT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type, -t` | Choice(['decision', 'session', 'sprint', 'task']) | - | Context type (auto-detected if not specified) |
| `--format, -f` | Choice(['json', 'text', 'yaml']) | `yaml` | Output format |

**Examples:**

```bash
vibey context show 01KC7MN54VXRB3APC5FV5XBDXX
```

```bash
vibey context show 0001-adopt-ulid-naming --type decision
```

```bash
vibey context show user-journey-phase-4-4 --type sprint
```

---

<a id="vibey-deploy"></a>

### `vibey deploy`

Deploy framework to target platforms.

Supports multiple AI coding assistant platforms:
- claude-code (Claude Code)
- goose (Goose by Block)
- gemini (Google Gemini Code Assist)
- aider (Aider CLI)
- continue (Continue.dev)
- windsurf (Windsurf/Codeium)
- vscode (VS Code native MCP)
- cursor (Cursor IDE)
- copilot (GitHub Copilot)

**Usage:**
```bash
vibey deploy COMMAND
```

**Examples:**

```bash
vibey deploy run --platform claude-code
```

```bash
vibey deploy run --platform cursor --clean
```

```bash
vibey deploy run --platform copilot
```

```bash
vibey deploy list
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `list` | List available deployment platforms |
| `run` | Deploy framework to specified platform |

---

<a id="vibey-deploy-list"></a>

#### `vibey deploy list`

List available deployment platforms

**Usage:**
```bash
vibey deploy list
```

---

<a id="vibey-deploy-run"></a>

#### `vibey deploy run`

Deploy framework to specified platform

**Usage:**
```bash
vibey deploy run [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform` | Choice(['aider', 'all', 'amazonq', 'claude-code', 'cody', 'continue', 'copilot', 'cursor', 'gemini', 'goose', 'jetbrains', 'replit', 'vscode', 'windsurf']) | - | Target platform (or "all" for all platforms) |
| `--clean` | flag | `False` | Remove existing deployment first |
| `--no-validate` | flag | `False` | Skip post-deployment validation |
| `--no-roadmap-init` | flag | `False` | Skip roadmap initialization after deployment |

---

<a id="vibey-discover"></a>

### `vibey discover`

Project discovery - analyze structure, dependencies, and patterns.

The discover command analyzes your project and generates structured
output about its characteristics. Discovery results are versioned
and can be used for context management and change tracking.

**Usage:**
```bash
vibey discover COMMAND
```

**Examples:**

```bash
vibey discover run              # Run discovery
```

```bash
vibey discover show             # Show current discovery
```

```bash
vibey discover status           # Check if discovery is stale
```

```bash
vibey discover history          # List discovery versions
```

```bash
vibey discover diff             # Compare versions
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `diff` | Compare two discovery versions.

Shows differences between d... |
| `history` | List discovery version history.

Shows previous discovery ru... |
| `refresh` | Refresh discovery if stale.

Re-runs discovery only if the c... |
| `run` | Run project discovery and analyze the codebase.

Analyzes th... |
| `show` | Show current discovery output.

Displays the most recent dis... |
| `status` | Check if current discovery is stale.

Reports whether the di... |

---

<a id="vibey-discover-diff"></a>

#### `vibey discover diff`

Compare two discovery versions.

Shows differences between discovery outputs. By default, compares
the current discovery with the previous version.

**Usage:**
```bash
vibey discover diff [FROM_VERSION] [TO_VERSION]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FROM_VERSION` | TEXT | No |  |
| `TO_VERSION` | TEXT | No |  |

**Examples:**

```bash
vibey discover diff
```

```bash
vibey discover diff 2025-12-13T10-00-00
```

```bash
vibey discover diff 2025-12-13T10-00-00 2025-12-14T10-00-00
```

---

<a id="vibey-discover-history"></a>

#### `vibey discover history`

List discovery version history.

Shows previous discovery runs with timestamps and git commits.

**Usage:**
```bash
vibey discover history [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit, -n` | INTEGER | `10` | Maximum number of versions to show |

**Examples:**

```bash
vibey discover history
```

```bash
vibey discover history --limit 5
```

---

<a id="vibey-discover-refresh"></a>

#### `vibey discover refresh`

Refresh discovery if stale.

Re-runs discovery only if the current discovery is stale,
unless --force is specified.

**Usage:**
```bash
vibey discover refresh [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force, -f` | flag | `False` | Force refresh even if not stale |

**Examples:**

```bash
vibey discover refresh
```

```bash
vibey discover refresh --force
```

---

<a id="vibey-discover-run"></a>

#### `vibey discover run`

Run project discovery and analyze the codebase.

Analyzes the project structure, dependencies, patterns, and conventions.
Results are saved to .vibey/discovery/ by default.

**Usage:**
```bash
vibey discover run [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Choice(['json', 'text', 'yaml']) | `yaml` | Output format |
| `--save` | flag | `True` | Save discovery to history |
| `--project, -p` | TEXT | `.` | Project root directory |

**Examples:**

```bash
vibey discover run
```

```bash
vibey discover run --output json
```

```bash
vibey discover run --no-save
```

```bash
vibey discover run -p /path/to/project
```

---

<a id="vibey-discover-show"></a>

#### `vibey discover show`

Show current discovery output.

Displays the most recent discovery analysis. Use --section to
show only specific parts of the discovery.

**Usage:**
```bash
vibey discover show [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['json', 'text', 'yaml']) | `text` | Output format |
| `--section, -s` | Choice(['all', 'conventions', 'dependencies', 'patterns', 'project', 'quality', 'recommendations', 'structure']) | `all` | Section to display |

**Examples:**

```bash
vibey discover show
```

```bash
vibey discover show --format yaml
```

```bash
vibey discover show --section dependencies
```

---

<a id="vibey-discover-status"></a>

#### `vibey discover status`

Check if current discovery is stale.

Reports whether the discovery should be refreshed based on:
- Age of the discovery
- Git commit changes
- File system changes

**Usage:**
```bash
vibey discover status [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max-age, -a` | INTEGER | `24` | Hours before discovery is considered stale |

**Examples:**

```bash
vibey discover status
```

```bash
vibey discover status --max-age 48
```

---

<a id="vibey-docs"></a>

### `vibey docs`

Generate and manage documentation.

**Usage:**
```bash
vibey docs COMMAND
```

**Examples:**

```bash
vibey docs generate           # Generate all docs
```

```bash
vibey docs generate --overwrite
```

```bash
vibey docs context            # Generate context docs
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `check-drift` | 
Check if CLI documentation has drifted from implementation.... |
| `check-mcp-drift` | 
Check if MCP documentation has drifted from implementation.... |
| `generate` | Generate documentation from configuration |
| `generate-cli` | 
Auto-generate CLI reference documentation from code.

Intro... |
| `generate-mcp` | 
Auto-generate MCP server reference documentation from code.... |
| `introspect` | 
Introspect CLI structure and output documentation data.

Ex... |
| `introspect-mcp` | 
Introspect MCP server structure and output documentation da... |

---

<a id="vibey-docs-check-drift"></a>

#### `vibey docs check-drift`

Check if CLI documentation has drifted from implementation.

Compares the committed CLI reference with freshly generated output.
Use in CI to prevent documentation drift. Returns exit code 1 if
drift is detected (unless --fix is used).

**Usage:**
```bash
vibey docs check-drift [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--path, -p` | Path(exists, file, dir) | `docs/reference/CLI_REFERENCE.md` | Path to existing CLI reference |
| `--fix` | flag | `False` | Regenerate if drift detected |
| `--quiet, -q` | flag | `False` | Only output on drift |

**Examples:**

```bash
vibey docs check-drift                     # Check default path
```

```bash
vibey docs check-drift -p docs/cli.md     # Check specific file
```

```bash
vibey docs check-drift --fix              # Auto-fix if drifted
```

```bash
vibey docs check-drift -q                 # Quiet mode for CI
```

---

<a id="vibey-docs-check-mcp-drift"></a>

#### `vibey docs check-mcp-drift`

Check if MCP documentation has drifted from implementation.

Compares the committed MCP reference with freshly generated output.
Use in CI to prevent documentation drift. Returns exit code 1 if
drift is detected (unless --fix is used).

**Usage:**
```bash
vibey docs check-mcp-drift [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--path, -p` | Path(exists, file, dir) | `docs/reference/MCP_REFERENCE.md` | Path to existing MCP reference |
| `--fix` | flag | `False` | Regenerate if drift detected |
| `--quiet, -q` | flag | `False` | Only output on drift |

**Examples:**

```bash
vibey docs check-mcp-drift                 # Check default path
```

```bash
vibey docs check-mcp-drift -p docs/mcp.md  # Check specific file
```

```bash
vibey docs check-mcp-drift --fix           # Auto-fix if drifted
```

```bash
vibey docs check-mcp-drift -q              # Quiet mode for CI
```

---

<a id="vibey-docs-generate"></a>

#### `vibey docs generate`

Generate documentation from configuration

**Usage:**
```bash
vibey docs generate [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--overwrite` | flag | `False` | Overwrite existing docs |

---

<a id="vibey-docs-generate-cli"></a>

#### `vibey docs generate-cli`

Auto-generate CLI reference documentation from code.

Introspects the Click command tree and generates comprehensive
reference documentation. Output cannot drift from implementation.

**Usage:**
```bash
vibey docs generate-cli [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Path(file, dir) | `docs/reference/CLI_REFERENCE.md` | Output file path |
| `--format, -f` | Choice(['json', 'markdown']) | `markdown` | Output format |
| `--include-hidden` | flag | `False` | Include hidden commands |

**Examples:**

```bash
vibey docs generate-cli                    # Generate CLI_REFERENCE.md
```

```bash
vibey docs generate-cli -o docs/cli.md    # Custom output path
```

```bash
vibey docs generate-cli -f json           # Output as JSON
```

```bash
vibey docs generate-cli --include-hidden  # Include hidden commands
```

---

<a id="vibey-docs-generate-mcp"></a>

#### `vibey docs generate-mcp`

Auto-generate MCP server reference documentation from code.

Introspects the MCP server tools, resources, and prompts to generate
comprehensive reference documentation. Output cannot drift from
implementation.

**Usage:**
```bash
vibey docs generate-mcp [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Path(file, dir) | `docs/reference/MCP_REFERENCE.md` | Output file path |
| `--format, -f` | Choice(['json', 'markdown']) | `markdown` | Output format |

**Examples:**

```bash
vibey docs generate-mcp                    # Generate MCP_REFERENCE.md
```

```bash
vibey docs generate-mcp -o docs/mcp.md    # Custom output path
```

```bash
vibey docs generate-mcp -f json           # Output as JSON
```

---

<a id="vibey-docs-introspect"></a>

#### `vibey docs introspect`

Introspect CLI structure and output documentation data.

Extracts structured data from the Click command tree for use in
documentation generation, tooling, or drift detection.

**Usage:**
```bash
vibey docs introspect [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['json', 'yaml']) | `json` | Output format |
| `--output, -o` | Path(file, dir) | - | Output file (stdout if not specified) |

**Examples:**

```bash
vibey docs introspect                  # JSON to stdout
```

```bash
vibey docs introspect -f yaml          # YAML to stdout
```

```bash
vibey docs introspect -o cli.json     # Save to file
```

---

<a id="vibey-docs-introspect-mcp"></a>

#### `vibey docs introspect-mcp`

Introspect MCP server structure and output documentation data.

Extracts structured data from the MCP server for use in
documentation generation, tooling, or drift detection.

**Usage:**
```bash
vibey docs introspect-mcp [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['json']) | `json` | Output format |
| `--output, -o` | Path(file, dir) | - | Output file (stdout if not specified) |

**Examples:**

```bash
vibey docs introspect-mcp                  # JSON to stdout
```

```bash
vibey docs introspect-mcp -o mcp.json      # Save to file
```

---

<a id="vibey-export"></a>

### `vibey export`

Export Vibey assets to platform-specific formats.

The export system translates Vibey agents, workflows, and handoffs
to platform-native formats using the adapter architecture.

Supported platforms:
- mcp: MCP tools (Claude Code, JetBrains AI)
- goose: Goose recipes + extension manifest

**Usage:**
```bash
vibey export COMMAND
```

**Examples:**

```bash
vibey export --platform goose    # Export to Goose format
```

```bash
vibey export --platform all      # Export to all platforms
```

```bash
vibey export --list              # List available platforms
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `gemini` | Export Vibey to Gemini Code Assist extension format

Generat... |
| `list` | List available export platforms

Shows all platforms that Vi... |
| `run` | Export assets to platform format

Generates platform-specifi... |
| `stats` | Show export statistics

Displays counts of tools, recipes, a... |

---

<a id="vibey-export-gemini"></a>

#### `vibey export gemini`

Export Vibey to Gemini Code Assist extension format

Generates a complete Gemini extension package with:
- GEMINI.md context file (from agent frontmatter)
- TOML custom commands (from workflow frontmatter)
- MCP server configuration
- Extension manifest

ZERO-DRIFT: All artifacts are generated from frontmatter.
If source agents/workflows change, re-run export to update.

**Usage:**
```bash
vibey export gemini [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Path(file, dir) | `./vibey-gemini-extension` | Output directory for extension package |
| `--no-install-script` | flag | `False` | Skip generating install.sh |
| `--no-readme` | flag | `False` | Skip generating README.md |
| `--validate` | flag | `False` | Validate existing export for drift |
| `--dry-run` | flag | `False` | Show what would be generated without writing |

**Examples:**

```bash
vibey export gemini                            # Export to ./vibey-gemini-extension/
```

```bash
vibey export gemini -o ./dist/gemini           # Custom output directory
```

```bash
vibey export gemini --validate                 # Check for manual edits
```

```bash
vibey export gemini --dry-run                  # Preview without writing
```

---

<a id="vibey-export-list"></a>

#### `vibey export list`

List available export platforms

Shows all platforms that Vibey can export to, with their capabilities.

**Usage:**
```bash
vibey export list
```

**Examples:**

```bash
vibey export list
```

---

<a id="vibey-export-run"></a>

#### `vibey export run`

Export assets to platform format

Generates platform-specific files from Vibey assets (agents, workflows).

**Usage:**
```bash
vibey export run [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform, -p` | TEXT | `all` | Platform to export to (mcp, goose, all) |
| `--output, -o` | Path(file, dir) | `./exports` | Output directory |
| `--dry-run` | flag | `False` | Show what would be exported without writing |

**Examples:**

```bash
vibey export run --platform goose           # Export to Goose
```

```bash
vibey export run --platform mcp             # Export MCP tools
```

```bash
vibey export run --platform all             # Export to all platforms
```

```bash
vibey export run --platform goose --dry-run # Preview export
```

---

<a id="vibey-export-stats"></a>

#### `vibey export stats`

Show export statistics

Displays counts of tools, recipes, and other assets for a platform.

**Usage:**
```bash
vibey export stats [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform, -p` | TEXT | `mcp` | Platform to show stats for |

**Examples:**

```bash
vibey export stats                 # Show MCP stats
```

```bash
vibey export stats --platform goose
```

---

<a id="vibey-git"></a>

### `vibey git`

Analyze Git history for roadmap references.

Extract task, sprint, and track references from commit messages,
calculate velocity metrics, and analyze contributor activity.

**Usage:**
```bash
vibey git COMMAND
```

**Examples:**

```bash
vibey git analyze                      # Analyze last 100 commits
```

```bash
vibey git analyze --max 500            # Analyze last 500 commits
```

```bash
vibey git analyze --since "2 weeks ago"
```

```bash
vibey git tasks git-integration-1-task-001
```

```bash
vibey git velocity git-integration-1
```

```bash
vibey git contributors
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `analyze` | 
Analyze Git history for roadmap references.

Parses commit ... |
| `branch` | 
Manage task-branch linking.

Create branches with proper na... |
| `check-merge` | 
Check for task completion conflicts before merging a PR.

D... |
| `contributors` | 
Show contributor activity and statistics.

Analyzes contrib... |
| `history` | 
Show change history for an item.

Tracks how a task, sprint... |
| `hooks` | 
Manage Git hooks for Vibey roadmap integration.

Install, u... |
| `link-commit` | 
Link a commit to a task and optionally update status.

Manu... |
| `mode` | 
Show current source-of-truth mode and reasoning.

Displays ... |
| `pr-description` | 
Generate PR description from task context.

Reads task info... |
| `progress` | 
Show sprint progress over time (burndown chart).

Samples t... |
| `repair` | 
Detect and repair roadmap inconsistencies.

Attempts to fix... |
| `repair-tags` | 
Automatically repair dangling tags.

Searches for commits m... |
| `rollback` | 
Rollback roadmap to state at ref.

Restores all roadmap YAM... |
| `sprint` | 
Manage sprint boundary tags.

Create and manage git tags th... |
| `state-at` | 
Show roadmap state at a specific ref.

Reconstructs the roa... |
| `sync` | 
Sync roadmap YAML from Git state (Git-primary mode).

Deriv... |
| `tag-move` | 
Manually move a tag to a different commit.

Deletes the tag... |
| `tag-range` | 
Get commits between boundary tags.

Retrieves commits betwe... |
| `tags` | 
List Vibey roadmap tags.

Shows all Vibey tags (sprint boun... |
| `tasks` | 
Show commits for a specific task.

Lists all commits that r... |
| `update-status` | 
Update task status based on commit messages.

Parses commit... |
| `validate` | 
Validate git strategy requirements.

Checks that all strate... |
| `validate-roadmap` | 
Validate roadmap YAML files and consistency.

Checks for:
-... |
| `validate-tags` | 
Detect dangling tags (pointing to missing commits).

After ... |
| `velocity` | 
Calculate sprint velocity metrics.

Analyzes commits for a ... |

---

<a id="vibey-git-analyze"></a>

#### `vibey git analyze`

Analyze Git history for roadmap references.

Parses commit messages to extract task, sprint, and track references,
and provides statistics on commit message formats and reference usage.

**Usage:**
```bash
vibey git analyze [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--max` | INTEGER | `100` | Maximum commits to analyze |
| `--since` | TEXT | - | Analyze commits after date (e.g., "2 weeks ago") |
| `--until` | TEXT | - | Analyze commits before date |
| `--ref-range` | TEXT | - | Commit range (e.g., "v1.0..v2.0") |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git analyze                     # Analyze last 100 commits
```

```bash
vibey git analyze --max 500           # Analyze 500 commits
```

```bash
vibey git analyze --since "1 month ago"
```

```bash
vibey git analyze --ref-range "main..develop"
```

```bash
vibey git analyze --format json      # JSON output
```

---

<a id="vibey-git-branch"></a>

#### `vibey git branch`

Manage task-branch linking.

Create branches with proper naming conventions, link branches to tasks,
and track branch lifecycle in roadmap YAML.

Branch Naming Conventions:
  - task/<task-id>       # For task branches
  - sprint/<sprint-id>   # For sprint branches
  - track/<track-id>     # For track branches

**Usage:**
```bash
vibey git branch COMMAND
```

**Examples:**

```bash
vibey git branch create git-integration-2-task-005
```

```bash
vibey git branch link my-feature git-integration-2-task-005
```

```bash
vibey git branch status
```

```bash
vibey git branch list
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `create` | 
Create a branch for a task with proper naming.

Creates a b... |
| `link` | 
Link an existing branch to a task.

Records branch informat... |
| `list` | 
List all branches following Vibey naming conventions.

Show... |
| `status` | 
Show branch-task linkage status.

Displays which tasks have... |
| `unlink` | 
Unlink a branch from a task.

Removes branch metadata from ... |

---

<a id="vibey-git-branch-create"></a>

#### `vibey git branch create`

Create a branch for a task with proper naming.

Creates a branch following the naming convention task/<task-id>
and optionally links it to the task in roadmap YAML.

**Usage:**
```bash
vibey git branch create [OPTIONS] <TASK_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--from` | TEXT | - | Starting point (branch/commit) |
| `--no-link` | flag | `False` | Do not link branch to task in YAML |
| `--dry-run` | flag | `False` | Show what would be created |

**Examples:**

```bash
vibey git branch create git-integration-2-task-005
```

```bash
vibey git branch create task-001 --from main
```

```bash
vibey git branch create task-001 --no-link
```

```bash
vibey git branch create task-001 --dry-run
```

---

<a id="vibey-git-branch-link"></a>

#### `vibey git branch link`

Link an existing branch to a task.

Records branch information in task metadata, including creation time,
merge status, and current status.

**Usage:**
```bash
vibey git branch link [OPTIONS] <BRANCH_NAME> <TASK_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `BRANCH_NAME` | TEXT | Yes |  |
| `TASK_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--dry-run` | flag | `False` | Show what would be linked |

**Examples:**

```bash
vibey git branch link my-feature git-integration-2-task-005
```

```bash
vibey git branch link feature/new-api task-001 --dry-run
```

---

<a id="vibey-git-branch-list"></a>

#### `vibey git branch list`

List all branches following Vibey naming conventions.

Shows branches that follow the task/*, sprint/*, or track/* naming pattern.

**Usage:**
```bash
vibey git branch list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--type` | Choice(['all', 'sprint', 'task', 'track']) | `all` | Filter by branch type |

**Examples:**

```bash
vibey git branch list
```

```bash
vibey git branch list --type task
```

```bash
vibey git branch list --type sprint
```

---

<a id="vibey-git-branch-status"></a>

#### `vibey git branch status`

Show branch-task linkage status.

Displays which tasks have linked branches, their status (current, merged),
and whether the branch still exists.

**Usage:**
```bash
vibey git branch status [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--task` | TEXT | - | Show status for specific task |

**Examples:**

```bash
vibey git branch status
```

```bash
vibey git branch status --task git-integration-2-task-005
```

---

<a id="vibey-git-branch-unlink"></a>

#### `vibey git branch unlink`

Unlink a branch from a task.

Removes branch metadata from the task in roadmap YAML.

**Usage:**
```bash
vibey git branch unlink [OPTIONS] <TASK_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--dry-run` | flag | `False` | Show what would be unlinked |

**Examples:**

```bash
vibey git branch unlink git-integration-2-task-005
```

```bash
vibey git branch unlink task-001 --dry-run
```

---

<a id="vibey-git-check-merge"></a>

#### `vibey git check-merge`

Check for task completion conflicts before merging a PR.

Detects when a task is marked complete in both the PR branch
and target branch, which may indicate duplicate work or conflicts.

**Usage:**
```bash
vibey git check-merge [OPTIONS] <PR_BRANCH>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PR_BRANCH` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target` | TEXT | `main` | Target branch (default: main) |
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git check-merge feature/task-123            # Check against main
```

```bash
vibey git check-merge feature/fix --target dev    # Check against dev
```

```bash
vibey git check-merge my-branch --format detailed # Detailed output
```

---

<a id="vibey-git-contributors"></a>

#### `vibey git contributors`

Show contributor activity and statistics.

Analyzes contributor activity including commit counts, tasks worked,
and code contribution volume.

**Usage:**
```bash
vibey git contributors [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--since` | TEXT | - | Show contributions after date |
| `--until` | TEXT | - | Show contributions before date |
| `--max` | INTEGER | `500` | Maximum commits to analyze |
| `--format` | Choice(['json', 'table']) | `table` | Output format |

**Examples:**

```bash
vibey git contributors
```

```bash
vibey git contributors --since "1 month ago"
```

```bash
vibey git contributors --format json
```

---

<a id="vibey-git-history"></a>

#### `vibey git history`

Show change history for an item.

Tracks how a task, sprint, or track changed over time by analyzing
all commits and reconstructing state at each point.

**Usage:**
```bash
vibey git history [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--type` | Choice(['sprint', 'task', 'track']) | `task` | Type of item |
| `--format` | Choice(['json', 'table']) | `table` | Output format |

**Examples:**

```bash
vibey git history git-integration-1-task-001
```

```bash
vibey git history sprint-1 --type sprint
```

```bash
vibey git history my-track --type track --format json
```

---

<a id="vibey-git-hooks"></a>

#### `vibey git hooks`

Manage Git hooks for Vibey roadmap integration.

Install, uninstall, and check status of pre-commit and commit-msg hooks
that validate roadmap integration and enforce quality standards.

**Usage:**
```bash
vibey git hooks COMMAND
```

**Examples:**

```bash
vibey git hooks install           # Install all hooks
```

```bash
vibey git hooks uninstall         # Remove all hooks
```

```bash
vibey git hooks status            # Check installation status
```

```bash
vibey git hooks update            # Update existing hooks
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `install` | 
Install Git hooks for Vibey roadmap integration.

Installs ... |
| `status` | 
Show Git hooks installation status.

Displays which Vibey h... |
| `uninstall` | 
Uninstall Vibey Git hooks.

Removes pre-commit and commit-m... |
| `update` | 
Update installed Git hooks to latest version.

Reinstalls h... |

---

<a id="vibey-git-hooks-install"></a>

#### `vibey git hooks install`

Install Git hooks for Vibey roadmap integration.

Installs pre-commit and commit-msg hooks that validate:
- YAML syntax in roadmap files
- Commit message format and task references
- Task existence in roadmap

By default, existing hooks are preserved and backed up.

**Usage:**
```bash
vibey git hooks install [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--force` | flag | `False` | Overwrite existing hooks |
| `--pre-commit-only` | flag | `False` | Install only pre-commit hook |
| `--commit-msg-only` | flag | `False` | Install only commit-msg hook |

**Examples:**

```bash
vibey git hooks install                    # Install all hooks
```

```bash
vibey git hooks install --force            # Overwrite existing
```

```bash
vibey git hooks install --pre-commit-only  # Only pre-commit
```

---

<a id="vibey-git-hooks-status"></a>

#### `vibey git hooks status`

Show Git hooks installation status.

Displays which Vibey hooks are installed, their versions,
and configuration settings.

**Usage:**
```bash
vibey git hooks status [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |

**Examples:**

```bash
vibey git hooks status
```

---

<a id="vibey-git-hooks-uninstall"></a>

#### `vibey git hooks uninstall`

Uninstall Vibey Git hooks.

Removes pre-commit and commit-msg hooks installed by Vibey.
Optionally removes backup files created during installation.

**Usage:**
```bash
vibey git hooks uninstall [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--keep-backups` | flag | `False` | Keep backup files |

**Examples:**

```bash
vibey git hooks uninstall                # Remove hooks
```

```bash
vibey git hooks uninstall --keep-backups # Keep backups
```

---

<a id="vibey-git-hooks-update"></a>

#### `vibey git hooks update`

Update installed Git hooks to latest version.

Reinstalls hooks while preserving configuration.
Existing hooks are backed up before updating.

**Usage:**
```bash
vibey git hooks update [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |

**Examples:**

```bash
vibey git hooks update
```

---

<a id="vibey-git-link-commit"></a>

#### `vibey git link-commit`

Link a commit to a task and optionally update status.

Manually records a commit SHA in a task's commits list and
optionally updates the task status.

**Usage:**
```bash
vibey git link-commit [OPTIONS] <TASK_ID> <COMMIT_SHA>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK_ID` | TEXT | Yes |  |
| `COMMIT_SHA` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--status` | Choice(['blocked', 'completed', 'in_progress']) | - | Update task status |
| `--dry-run` | flag | `False` | Show what would be updated |

**Examples:**

```bash
vibey git link-commit task-001 abc1234
```

```bash
vibey git link-commit task-001 abc1234 --status completed
```

```bash
vibey git link-commit task-001 abc1234 --dry-run
```

---

<a id="vibey-git-mode"></a>

#### `vibey git mode`

Show current source-of-truth mode and reasoning.

Displays which mode is active (yaml-only, hybrid, git-primary)
and explains why that mode was chosen.

MODES:
  - yaml-only: YAML files are source of truth, no git integration
  - hybrid: YAML primary, git provides supplementary data
  - git-primary: Git is source of truth, YAML derived from git

**Usage:**
```bash
vibey git mode [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git mode                    # Show current mode
```

```bash
vibey git mode --format detailed  # Show with requirements
```

```bash
vibey git mode --format json      # JSON output
```

---

<a id="vibey-git-pr-description"></a>

#### `vibey git pr-description`

Generate PR description from task context.

Reads task information from roadmap and generates a formatted
PR description including task details, checklist, related tasks,
and quality gates.

Auto-detects task from current branch name if --task not provided.

**Usage:**
```bash
vibey git pr-description [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--task` | TEXT | - | Task ID (auto-detects from branch if not provided) |
| `--output` | Path(file, dir) | - | Output file (prints to stdout if not provided) |
| `--copy` | flag | `False` | Copy to clipboard |

**Examples:**

```bash
vibey git pr-description                           # Auto-detect from branch
```

```bash
vibey git pr-description --task git-integration-2-task-006
```

```bash
vibey git pr-description --output pr-body.md       # Save to file
```

```bash
vibey git pr-description --copy                    # Copy to clipboard
```

---

<a id="vibey-git-progress"></a>

#### `vibey git progress`

Show sprint progress over time (burndown chart).

Samples the sprint state at regular intervals to show how progress
evolved over time. Useful for generating burndown charts.

**Usage:**
```bash
vibey git progress [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--interval` | INTEGER | `10` | Sample every N commits |
| `--format` | Choice(['chart', 'json', 'table']) | `chart` | Output format |

**Examples:**

```bash
vibey git progress git-integration-1
```

```bash
vibey git progress sprint-1 --interval 5  # Sample every 5 commits
```

```bash
vibey git progress sprint-2 --format table
```

```bash
vibey git progress sprint-3 --format json
```

---

<a id="vibey-git-repair"></a>

#### `vibey git repair`

Detect and repair roadmap inconsistencies.

Attempts to fix common issues like:
- YAML syntax errors (restore from git)
- Invalid references
- Orphaned files

**Usage:**
```bash
vibey git repair [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--dry-run` | flag | `False` | Show what would be fixed without making changes |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git repair --dry-run          # Show what would be fixed
```

```bash
vibey git repair                    # Actually perform repairs
```

```bash
vibey git repair --format detailed  # Verbose output
```

---

<a id="vibey-git-repair-tags"></a>

#### `vibey git repair-tags`

Automatically repair dangling tags.

Searches for commits matching the original tag and recreates
the tags on the new commits. By default only repairs roadmap
tags (sprint/task tags).

**Usage:**
```bash
vibey git repair-tags [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--strategy` | Choice(['message_match']) | `message_match` | Repair strategy (default: message_match) |
| `--dry-run` | flag | `False` | Show what would be repaired without making changes |
| `--all-tags` | flag | `False` | Repair all tags, not just roadmap tags |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git repair-tags --dry-run      # Preview repairs
```

```bash
vibey git repair-tags                # Repair roadmap tags
```

```bash
vibey git repair-tags --all-tags     # Repair all dangling tags
```

---

<a id="vibey-git-rollback"></a>

#### `vibey git rollback`

Rollback roadmap to state at ref.

Restores all roadmap YAML files to their state at a specific commit.
By default runs in dry-run mode to show what would change.

**Usage:**
```bash
vibey git rollback [OPTIONS] <REF>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `REF` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--dry-run` | flag | `True` | Show what would be restored (default) |
| `--execute` | flag | `False` | Actually perform the rollback |

**Examples:**

```bash
vibey git rollback HEAD~5                 # Dry-run (default)
```

```bash
vibey git rollback v1.0.0 --execute       # Actually rollback
```

```bash
vibey git rollback abc1234 --execute
```

---

<a id="vibey-git-sprint"></a>

#### `vibey git sprint`

Manage sprint boundary tags.

Create and manage git tags that mark sprint start and end points,
enabling velocity calculations and state reconstruction queries.

**Usage:**
```bash
vibey git sprint COMMAND
```

**Examples:**

```bash
vibey git sprint start git-integration-2         # Tag sprint start at HEAD
```

```bash
vibey git sprint end git-integration-2           # Tag sprint end at HEAD
```

```bash
vibey git sprint list                            # List all sprint tags
```

```bash
vibey git sprint list git-integration-2          # List tags for specific sprint
```

```bash
vibey git sprint range git-integration-2         # Show commit range for sprint
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `delete` | 
Delete a sprint boundary tag.

Removes a sprint start or en... |
| `end` | 
Create sprint end tag at current or specified commit.

Mark... |
| `list` | 
List sprint tags, optionally filtered by sprint ID.

Shows ... |
| `range` | 
Show commit range for a sprint (start tag to end tag).

Dis... |
| `start` | 
Create sprint start tag at current or specified commit.

Ma... |

---

<a id="vibey-git-sprint-delete"></a>

#### `vibey git sprint delete`

Delete a sprint boundary tag.

Removes a sprint start or end tag from the local repository,
and optionally from the remote.

**Usage:**
```bash
vibey git sprint delete [OPTIONS] <SPRINT_ID> <TAG_TYPE>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |
| `TAG_TYPE` | Choice(['end', 'start']) | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--push` | flag | `False` | Delete tag from remote |
| `--remote` | TEXT | `origin` | Remote name (default: origin) |

**Examples:**

```bash
vibey git sprint delete git-integration-2 start
```

```bash
vibey git sprint delete git-integration-2 end --push
```

---

<a id="vibey-git-sprint-end"></a>

#### `vibey git sprint end`

Create sprint end tag at current or specified commit.

Marks the completion of a sprint in git history with an annotated tag
containing sprint completion metrics from the roadmap.

**Usage:**
```bash
vibey git sprint end [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--commit` | TEXT | - | Commit SHA to tag (default: HEAD) |
| `--force` | flag | `False` | Overwrite existing tag |
| `--push` | flag | `False` | Push tag to remote |
| `--remote` | TEXT | `origin` | Remote name (default: origin) |

**Examples:**

```bash
vibey git sprint end git-integration-2
```

```bash
vibey git sprint end git-integration-2 --commit abc1234
```

```bash
vibey git sprint end git-integration-2 --force --push
```

---

<a id="vibey-git-sprint-list"></a>

#### `vibey git sprint list`

List sprint tags, optionally filtered by sprint ID.

Shows all sprint start/end tags with commit info and dates.

**Usage:**
```bash
vibey git sprint list [OPTIONS] [SPRINT_ID]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | No |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['json', 'table']) | `table` | Output format |

**Examples:**

```bash
vibey git sprint list                      # List all sprint tags
```

```bash
vibey git sprint list git-integration-2    # List tags for specific sprint
```

```bash
vibey git sprint list --format json        # JSON output
```

---

<a id="vibey-git-sprint-range"></a>

#### `vibey git sprint range`

Show commit range for a sprint (start tag to end tag).

Displays the start and end commits for a sprint, and optionally
lists all commits in the sprint range.

**Usage:**
```bash
vibey git sprint range [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--commits` | flag | `False` | Show commit list |

**Examples:**

```bash
vibey git sprint range git-integration-2             # Show range endpoints
```

```bash
vibey git sprint range git-integration-2 --commits   # Show all commits
```

---

<a id="vibey-git-sprint-start"></a>

#### `vibey git sprint start`

Create sprint start tag at current or specified commit.

Marks the beginning of a sprint in git history with an annotated tag
containing sprint metadata from the roadmap.

**Usage:**
```bash
vibey git sprint start [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--commit` | TEXT | - | Commit SHA to tag (default: HEAD) |
| `--force` | flag | `False` | Overwrite existing tag |
| `--push` | flag | `False` | Push tag to remote |
| `--remote` | TEXT | `origin` | Remote name (default: origin) |

**Examples:**

```bash
vibey git sprint start git-integration-2
```

```bash
vibey git sprint start git-integration-2 --commit abc1234
```

```bash
vibey git sprint start git-integration-2 --force --push
```

---

<a id="vibey-git-state-at"></a>

#### `vibey git state-at`

Show roadmap state at a specific ref.

Reconstructs the roadmap state at any point in history by reading
YAML files at that commit. Supports commits, tags, branches, and dates.

**Usage:**
```bash
vibey git state-at [OPTIONS] <REF>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `REF` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--item` | TEXT | - | Show specific item (task/sprint/track ID) |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git state-at HEAD~10                # 10 commits ago
```

```bash
vibey git state-at v1.0.0                 # At tag
```

```bash
vibey git state-at 2024-01-15             # At date
```

```bash
vibey git state-at abc1234 --item task-001  # Specific task
```

```bash
vibey git state-at main --format json
```

---

<a id="vibey-git-sync"></a>

#### `vibey git sync`

Sync roadmap YAML from Git state (Git-primary mode).

Derives task and sprint status from git branches, tags, and commits.
In Git-primary mode, Git is the source of truth.

DERIVATION RULES:

Task Status:
  - not_started: no branch AND no commits
  - in_progress: branch exists OR commits exist
  - completed: branch merged with commits

Sprint Status:
  - not_started: no start tag
  - in_progress: start tag exists, no end tag
  - completed: end tag exists

**Usage:**
```bash
vibey git sync [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--task` | TEXT | - | Sync specific task |
| `--sprint` | TEXT | - | Sync specific sprint |
| `--track` | TEXT | - | Sync specific track |
| `--dry-run` | flag | `False` | Show changes without applying |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git sync                         # Sync all tracks
```

```bash
vibey git sync --task task-001         # Sync specific task
```

```bash
vibey git sync --sprint sprint-2       # Sync specific sprint
```

```bash
vibey git sync --track git-integration # Sync specific track
```

```bash
vibey git sync --dry-run               # Preview changes
```

---

<a id="vibey-git-tag-move"></a>

#### `vibey git tag-move`

Manually move a tag to a different commit.

Deletes the tag from its current location and recreates it
on the specified commit. Preserves annotation messages.

**Usage:**
```bash
vibey git tag-move [OPTIONS] <TAG_NAME> <NEW_SHA>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TAG_NAME` | TEXT | Yes |  |
| `NEW_SHA` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--force` | flag | `False` | Force move even if tag exists |

**Examples:**

```bash
vibey git tag-move sprint/my-sprint/start abc1234 --force
```

```bash
vibey git tag-move task/my-task-1 def5678
```

---

<a id="vibey-git-tag-range"></a>

#### `vibey git tag-range`

Get commits between boundary tags.

Retrieves commits between start/end tags for a sprint or task.
This is more efficient than parsing all commit messages.

**Usage:**
```bash
vibey git tag-range [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--type` | Choice(['sprint', 'task']) | `sprint` | Type of item (sprint or task) |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git tag-range git-integration-1 --type sprint
```

```bash
vibey git tag-range git-integration-1-task-001 --type task
```

```bash
vibey git tag-range sprint-1 --format detailed
```

---

<a id="vibey-git-tags"></a>

#### `vibey git tags`

List Vibey roadmap tags.

Shows all Vibey tags (sprint boundaries, task markers) with filtering options.

**Usage:**
```bash
vibey git tags [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--sprint` | TEXT | - | Show tags for specific sprint |
| `--task` | TEXT | - | Show tags for specific task |
| `--track` | TEXT | - | Show tags for specific track |
| `--format` | Choice(['json', 'table']) | `table` | Output format |

**Examples:**

```bash
vibey git tags                                # List all Vibey tags
```

```bash
vibey git tags --sprint git-integration-1     # Sprint tags
```

```bash
vibey git tags --task git-integration-1-task-001  # Task tags
```

```bash
vibey git tags --format json
```

---

<a id="vibey-git-tasks"></a>

#### `vibey git tasks`

Show commits for a specific task.

Lists all commits that reference the specified task ID, including
commit details, contributors, and status changes.

**Usage:**
```bash
vibey git tasks [OPTIONS] <TASK_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['json', 'table']) | `table` | Output format |

**Examples:**

```bash
vibey git tasks git-integration-1-task-001
```

```bash
vibey git tasks task-001 --format json
```

---

<a id="vibey-git-update-status"></a>

#### `vibey git update-status`

Update task status based on commit messages.

Parses commit messages for status indicators (completes, starts, blocks)
and automatically updates task status in roadmap YAML files.

Status Keywords:
  - "completes task-id" → mark task completed
  - "starts task-id" → mark task in_progress
  - "blocks task-id" → mark task blocked

**Usage:**
```bash
vibey git update-status [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--commit` | TEXT | - | Process specific commit SHA |
| `--message` | TEXT | - | Commit message (with --commit) |
| `--recent` | INTEGER | `10` | Process N recent commits |
| `--dry-run` | flag | `False` | Show what would be updated without making changes |
| `--force` | flag | `False` | Allow updates even if task already in target status |

**Examples:**

```bash
vibey git update-status                    # Process last 10 commits
```

```bash
vibey git update-status --recent 50         # Process last 50 commits
```

```bash
vibey git update-status --commit abc1234 --message "completes task-001"
```

```bash
vibey git update-status --dry-run           # Preview changes
```

```bash
vibey git update-status --force             # Update even if already at status
```

---

<a id="vibey-git-validate"></a>

#### `vibey git validate`

Validate git strategy requirements.

Checks that all strategy requirements are satisfied for the current mode.
This includes branch naming conventions, required branches, tags, etc.

**Usage:**
```bash
vibey git validate [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git validate                    # Validate strategy
```

```bash
vibey git validate --format detailed  # Show all violations
```

```bash
vibey git validate --format json      # JSON output
```

---

<a id="vibey-git-validate-roadmap"></a>

#### `vibey git validate-roadmap`

Validate roadmap YAML files and consistency.

Checks for:
- YAML syntax errors
- Invalid task/sprint references
- Git-roadmap consistency
- Orphaned files

**Usage:**
```bash
vibey git validate-roadmap [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git validate-roadmap                    # Validate roadmap
```

```bash
vibey git validate-roadmap --format detailed  # Show all issues
```

```bash
vibey git validate-roadmap --format json      # JSON output
```

---

<a id="vibey-git-validate-tags"></a>

#### `vibey git validate-tags`

Detect dangling tags (pointing to missing commits).

After rebase/squash operations, tags may point to commits that
no longer exist. This command detects such tags.

**Usage:**
```bash
vibey git validate-tags [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git validate-tags                    # Check for dangling tags
```

```bash
vibey git validate-tags --format detailed  # Show all details
```

```bash
vibey git validate-tags --format json      # JSON output
```

---

<a id="vibey-git-velocity"></a>

#### `vibey git velocity`

Calculate sprint velocity metrics.

Analyzes commits for a sprint and calculates velocity metrics including
commit frequency, task completion rate, contributor activity, and code volume.

**Usage:**
```bash
vibey git velocity [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo` | Path(exists, file, dir) | `.` | Path to git repository |
| `--start-ref` | TEXT | - | Starting ref (e.g., tag or commit) |
| `--end-ref` | TEXT | - | Ending ref |
| `--start-date` | TEXT | - | Starting date |
| `--end-date` | TEXT | - | Ending date |
| `--format` | Choice(['detailed', 'json', 'summary']) | `summary` | Output format |

**Examples:**

```bash
vibey git velocity git-integration-1
```

```bash
vibey git velocity sprint-1 --start-ref sprint-1/start --end-ref sprint-1/end
```

```bash
vibey git velocity sprint-2 --start-date "2024-01-01" --end-date "2024-01-15"
```

```bash
vibey git velocity sprint-3 --format json
```

---

<a id="vibey-roadmap"></a>

### `vibey roadmap`

Manage roadmap system - tracks, sprints, tasks, and dependencies.

The roadmap system provides hierarchical project planning with:
- Tracks: Major feature areas or work streams
- Sprints: Time-boxed iterations within tracks
- Tasks: Specific work items within sprints
- Dependencies: Blocker relationships between items

Auto-sync: Database is automatically synced when YAML files are edited
directly. Use --no-sync to skip this check for faster operations.

**Usage:**
```bash
vibey roadmap [OPTIONS] COMMAND
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--backend, -b` | Choice(['auto', 'sqlite', 'yaml']) | - | Storage backend: auto (default), sqlite, or yaml |
| `--no-sync` | flag | `False` | Skip auto-sync check (faster for batch operations) |

**Examples:**

```bash
vibey roadmap init           # Initialize new roadmap
```

```bash
vibey roadmap status         # Show current status
```

```bash
vibey roadmap show sprint-1  # Show sprint details
```

```bash
vibey roadmap start task-001 # Start a task
```

```bash
vibey roadmap --no-sync list # Skip sync check
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `activity` | Show recent roadmap activity in a compact format.

Display r... |
| `add-commit` | Add a git commit to a task

Examples:
  vibey roadmap add-co... |
| `add-context` | Add a context file to a roadmap object

Context files are st... |
| `add-standard` | Add a new standard to roadmap/track/sprint

Creates a new st... |
| `audit` | 
View and analyze roadmap change audit trail.

Track all sta... |
| `auto-progress` | Check or apply automatic status progressions.

Auto-progress... |
| `bulk` | 
Bulk operations on roadmap items.

Commands for performing ... |
| `check-compatibility` | Check if sprint tasks fit in your platform's context window
... |
| `check-hooks` | Check git hook installation status

Shows whether the Vibey ... |
| `check-standards` | Check which standards apply to an item

Validates all standa... |
| `checkpoint` | 
Manage roadmap integrity checkpoints.

Create, restore, ver... |
| `complete` | Complete a track, sprint, or task

For sprints, validates th... |
| `context` | Get AI-optimized context for a task |
| `create-from-plan` | Create roadmap sprint from a plan markdown file

Parses a sp... |
| `create-sprint` | Create a new sprint in a track.

Creates a new sprint YAML f... |
| `create-task` | Create a new task in a sprint.

Creates a new task YAML file... |
| `create-track` | Create a new track in the roadmap.

Creates a new track YAML... |
| `db` | 
Database operations for roadmap state management.

The data... |
| `doc-changelog` | Generate a documentation changelog

Generates a markdown cha... |
| `edit` | 
Safe YAML editing with automatic validation and backups.

A... |
| `extract-embedded` | Extract embedded tasks from sprint files to standalone task ... |
| `init` | Initialize a new roadmap in .vibey/roadmap.yaml |
| `install-hooks` | Install git pre-commit hook for roadmap validation

The pre-... |
| `link-doc` | Link a documentation file to a roadmap object

Creates or up... |
| `list-docs` | List all tracked documentation files

Shows all documentatio... |
| `migrate-docs` | Migrate documentation fields from YAML to markdown files.

T... |
| `migrate-format` | Migrate YAML files from v1 format to v2 format.

V1 format u... |
| `override-standard` | Override a standard for a specific item

Adds an override to... |
| `recalculate` | Recalculate sprint tasks for a different platform

Splits ov... |
| `reconcile` | Detect and fix status inconsistencies in roadmap data.

Chec... |
| `repair` | Auto-repair common roadmap integrity issues

Repairs:
  - Pr... |
| `revert` | Revert a track, sprint, or task to a previous status

Allows... |
| `show` | Show details for a track, sprint, or task

For sprints, also... |
| `start` | Start a sprint or task

When starting a sprint, checks if ta... |
| `status` | Show roadmap status - tracks, sprints, and tasks |
| `summarize` | Summarize a sprint, task, or track |
| `sync` | Sync status from individual files to main roadmap.yaml

Reco... |
| `sync-commits` | Scan git history and link commits to tasks based on commit m... |
| `sync-docs` | Synchronize documentation from .vibey/roadmap/ to docs/roadm... |
| `uninstall-hooks` | Uninstall git pre-commit hook

Removes the Vibey pre-commit ... |
| `validate-advanced` | Advanced validation for complex integrity issues

Detects:
 ... |
| `validate-commits` | Validate that all completed tasks have commit evidence

Chec... |
| `validate-fast` | Fast roadmap validation with caching and parallel loading

V... |
| `validate-structure` | Validate roadmap directory structure is flat (no ULID direct... |
| `verify-change` | Verify a roadmap file change has a matching activity log ent... |
| `verify-commits` | Verify roadmap changes in a commit range have activity log e... |

---

<a id="vibey-roadmap-activity"></a>

#### `vibey roadmap activity`

Show recent roadmap activity in a compact format.

Display recent status changes, completions, and lifecycle events.
This is a convenience command that wraps the audit log.

**Usage:**
```bash
vibey roadmap activity [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--last, -n` | INTEGER | `10` | Number of recent activities to show |
| `--object, -o` | TEXT | - | Filter by object ID |
| `--type, -t` | TEXT | - | Filter by activity type |

**Examples:**

```bash
vibey roadmap activity                   # Show last 10 activities
```

```bash
vibey roadmap activity --last 20         # Show last 20 activities
```

```bash
vibey roadmap activity -o sqlite-backend # Filter by object
```

---

<a id="vibey-roadmap-add-commit"></a>

#### `vibey roadmap add-commit`

Add a git commit to a task

**Usage:**
```bash
vibey roadmap add-commit [OPTIONS] <TASK_ID> [COMMIT_SHA]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK_ID` | TEXT | Yes |  |
| `COMMIT_SHA` | TEXT | No |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--auto` | flag | `False` | Use current HEAD commit |

**Examples:**

```bash
vibey roadmap add-commit task-001 4367bc8
```

```bash
vibey roadmap add-commit task-001 --auto
```

---

<a id="vibey-roadmap-add-context"></a>

#### `vibey roadmap add-context`

Add a context file to a roadmap object

Context files are stored in /context/ directories alongside roadmap objects
and are used to preserve research, analyses, and decisions.

**Usage:**
```bash
vibey roadmap add-context [OPTIONS] <FILE_PATH>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE_PATH` | Path(exists, file, dir) | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--track` | TEXT | - | Add context to track |
| `--sprint` | TEXT | - | Add context to sprint |
| `--task` | TEXT | - | Add context to task |

**Examples:**

```bash
vibey roadmap add-context design.md --track my-track
```

```bash
vibey roadmap add-context analysis.md --sprint sprint-1
```

```bash
vibey roadmap add-context notes.md --task task-001
```

---

<a id="vibey-roadmap-add-standard"></a>

#### `vibey roadmap add-standard`

Add a new standard to roadmap/track/sprint

Creates a new standard that enforces a policy at the specified level.
Standards cascade down the hierarchy (roadmap → track → sprint → task).

VALIDATION is a JSON string with validation config, e.g. '{"min_commits": 1}'

**Usage:**
```bash
vibey roadmap add-standard [OPTIONS] <LEVEL> <STANDARD_ID> <NAME> <DESCRIPTION> <TYPE> <ENFORCEMENT> <VALIDATION>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `LEVEL` | Choice(['roadmap', 'sprint', 'track']) | Yes |  |
| `STANDARD_ID` | TEXT | Yes |  |
| `NAME` | TEXT | Yes |  |
| `DESCRIPTION` | TEXT | Yes |  |
| `TYPE` | Choice(['commit_check', 'custom_script', 'file_check', 'test_run']) | Yes |  |
| `ENFORCEMENT` | Choice(['audit', 'blocking', 'warning']) | Yes |  |
| `VALIDATION` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target-id` | TEXT | - | Track/sprint ID (required for track/sprint level) |

**Examples:**

```bash
vibey roadmap add-standard roadmap commit-req "Commit Required" \
```

```bash
vibey roadmap add-standard track test-cov "Test Coverage" \
```

---

<a id="vibey-roadmap-audit"></a>

#### `vibey roadmap audit`

View and analyze roadmap change audit trail.

Track all status changes with who/when/why for accountability.
Detect suspicious changes and generate audit reports.

**Usage:**
```bash
vibey roadmap audit COMMAND
```

**Examples:**

```bash
vibey roadmap audit log                  # Show recent changes
```

```bash
vibey roadmap audit show track-123       # Show object history
```

```bash
vibey roadmap audit suspicious           # Find suspicious changes
```

```bash
vibey roadmap audit report               # Generate detailed report
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `log` | Show recent audit trail entries

Display the most recent sta... |
| `report` | Generate detailed audit report

Create a comprehensive repor... |
| `show` | Show change history for a specific object

Display all statu... |
| `suspicious` | Detect suspicious changes in audit trail

Find potentially p... |

---

<a id="vibey-roadmap-audit-log"></a>

#### `vibey roadmap audit log`

Show recent audit trail entries

Display the most recent status changes across all roadmap objects.

**Usage:**
```bash
vibey roadmap audit log [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit, -n` | INTEGER | `20` | Number of entries to show |

**Examples:**

```bash
vibey roadmap audit log              # Show last 20 changes
```

```bash
vibey roadmap audit log --limit 50   # Show last 50 changes
```

---

<a id="vibey-roadmap-audit-report"></a>

#### `vibey roadmap audit report`

Generate detailed audit report

Create a comprehensive report of audit trail entries with filters.

**Usage:**
```bash
vibey roadmap audit report [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--object-id` | TEXT | - | Filter by object ID |
| `--start` | TEXT | - | Start date (YYYY-MM-DD) |
| `--end` | TEXT | - | End date (YYYY-MM-DD) |

**Examples:**

```bash
vibey roadmap audit report                           # Full report
```

```bash
vibey roadmap audit report --object-id track-123     # For one object
```

```bash
vibey roadmap audit report --start 2025-01-01        # From date
```

---

<a id="vibey-roadmap-audit-show"></a>

#### `vibey roadmap audit show`

Show change history for a specific object

Display all status changes for a track, sprint, or task.

**Usage:**
```bash
vibey roadmap audit show <OBJECT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `OBJECT_ID` | TEXT | Yes |  |

**Examples:**

```bash
vibey roadmap audit show roadmap-system
```

```bash
vibey roadmap audit show roadmap-system-1
```

```bash
vibey roadmap audit show roadmap-system-1-task-001
```

---

<a id="vibey-roadmap-audit-suspicious"></a>

#### `vibey roadmap audit suspicious`

Detect suspicious changes in audit trail

Find potentially problematic changes like:
- Status rollbacks (completed → not_started)
- Progress decreases
- Manual YAML edits without git commits

**Usage:**
```bash
vibey roadmap audit suspicious
```

**Examples:**

```bash
vibey roadmap audit suspicious
```

---

<a id="vibey-roadmap-auto-progress"></a>

#### `vibey roadmap auto-progress`

Check or apply automatic status progressions.

Auto-progression advances ticket status when criteria are met.
This feature must be enabled in .vibey/config/roadmap.yaml.

**Usage:**
```bash
vibey roadmap auto-progress [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--check` | flag | `check` | Show what would advance (dry-run mode) |
| `--apply` | flag | - | Actually advance eligible tickets |
| `--ticket, -t` | TEXT | - | Check/apply to specific ticket only |
| `--enable` | flag | `False` | Enable auto-progression in config |
| `--disable` | flag | `False` | Disable auto-progression in config |

**Examples:**

```bash
vibey roadmap auto-progress --check     # Show what would advance
```

```bash
vibey roadmap auto-progress --apply     # Actually advance tickets
```

```bash
vibey roadmap auto-progress --enable    # Enable auto-progression
```

```bash
vibey roadmap auto-progress --disable   # Disable auto-progression
```

---

<a id="vibey-roadmap-bulk"></a>

#### `vibey roadmap bulk`

Bulk operations on roadmap items.

Commands for performing operations across multiple items at once,
such as completing all tasks in a sprint.

**Usage:**
```bash
vibey roadmap bulk COMMAND
```

**Examples:**

```bash
vibey roadmap bulk complete-sprint <sprint-id>  # Complete all tasks in sprint
```

```bash
vibey roadmap bulk complete-sprint <id> --yes   # Skip confirmation
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `complete-sprint` | Mark all tasks in a sprint as completed.

Completes all non-... |

---

<a id="vibey-roadmap-bulk-complete-sprint"></a>

#### `vibey roadmap bulk complete-sprint`

Mark all tasks in a sprint as completed.

Completes all non-completed tasks in the specified sprint at once.
Updates sprint progress and creates activity log entries for each task.

**Usage:**
```bash
vibey roadmap bulk complete-sprint [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--yes, -y` | flag | `False` | Skip confirmation prompt |

**Examples:**

```bash
vibey roadmap bulk complete-sprint 01KC7TNS0SC0FX8TPGN9SG4J1B
```

```bash
vibey roadmap bulk complete-sprint dogfooding-bugs-10 --yes
```

---

<a id="vibey-roadmap-check-compatibility"></a>

#### `vibey roadmap check-compatibility`

Check if sprint tasks fit in your platform's context window

Analyzes all incomplete tasks in a sprint and checks if they fit
within your current platform's context window. Oversized tasks
need to be recalculated before starting.

**Usage:**
```bash
vibey roadmap check-compatibility [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform, -p` | TEXT | - | Override platform (auto-detect if not specified) |
| `--context-window, -c` | INTEGER | - | Override context window size (tokens) |
| `--include-completed` | flag | `False` | Include completed tasks in analysis |
| `--verbose, -v` | flag | `False` | Show all tasks, not just problematic ones |
| `--json` | flag | `False` | Output as JSON |

**Examples:**

```bash
vibey roadmap check-compatibility auth-sprint-1
```

```bash
vibey roadmap check-compatibility sprint-1 --platform goose
```

```bash
vibey roadmap check-compatibility sprint-1 --context-window 128000
```

```bash
vibey roadmap check-compatibility sprint-1 --verbose
```

```bash
vibey roadmap check-compatibility sprint-1 --json
```

---

<a id="vibey-roadmap-check-hooks"></a>

#### `vibey roadmap check-hooks`

Check git hook installation status

Shows whether the Vibey pre-commit hook is installed and active.

**Usage:**
```bash
vibey roadmap check-hooks
```

**Examples:**

```bash
vibey roadmap check-hooks
```

---

<a id="vibey-roadmap-check-standards"></a>

#### `vibey roadmap check-standards`

Check which standards apply to an item

Validates all standards that apply to a roadmap item (task/sprint/track)
and displays the results without taking any action.

**Usage:**
```bash
vibey roadmap check-standards [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `False` | Show all standards including passed ones |

**Examples:**

```bash
vibey roadmap check-standards task-001
```

```bash
vibey roadmap check-standards sprint-1 --verbose
```

```bash
vibey roadmap check-standards my-track
```

---

<a id="vibey-roadmap-checkpoint"></a>

#### `vibey roadmap checkpoint`

Manage roadmap integrity checkpoints.

Create, restore, verify, and compare backups of the .vibey/ directory
with SHA-256 checksum verification and YAML validation.

**Usage:**
```bash
vibey roadmap checkpoint COMMAND
```

**Examples:**

```bash
vibey roadmap checkpoint create              # Create timestamped checkpoint
```

```bash
vibey roadmap checkpoint create my-backup    # Create named checkpoint
```

```bash
vibey roadmap checkpoint list                # List all checkpoints
```

```bash
vibey roadmap checkpoint verify my-backup    # Verify checkpoint integrity
```

```bash
vibey roadmap checkpoint restore my-backup   # Restore from checkpoint
```

```bash
vibey roadmap checkpoint compare cp1 cp2     # Compare two checkpoints
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `clean` | Clean old checkpoints

Removes old checkpoints while keeping... |
| `compare` | Compare two checkpoints

Shows files added, removed, and mod... |
| `create` | Create a new integrity checkpoint

Creates a timestamped bac... |
| `list` | List all available checkpoints

Shows checkpoint name, size,... |
| `restore` | Restore from a checkpoint

Restores .vibey/ directory from c... |
| `verify` | Verify checkpoint integrity

Validates all files match SHA-2... |

---

<a id="vibey-roadmap-checkpoint-clean"></a>

#### `vibey roadmap checkpoint clean`

Clean old checkpoints

Removes old checkpoints while keeping the N most recent.
Interactive confirmation required before deletion.

**Usage:**
```bash
vibey roadmap checkpoint clean [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--keep` | INTEGER | `5` | Number of checkpoints to keep (default: 5) |

**Examples:**

```bash
vibey roadmap checkpoint clean            # Keep last 5
```

```bash
vibey roadmap checkpoint clean --keep 10  # Keep last 10
```

---

<a id="vibey-roadmap-checkpoint-compare"></a>

#### `vibey roadmap checkpoint compare`

Compare two checkpoints

Shows files added, removed, and modified between two checkpoints
using SHA-256 checksum comparison.

**Usage:**
```bash
vibey roadmap checkpoint compare <CHECKPOINT1> <CHECKPOINT2>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CHECKPOINT1` | TEXT | Yes |  |
| `CHECKPOINT2` | TEXT | Yes |  |

**Examples:**

```bash
vibey roadmap checkpoint compare old-backup new-backup
```

---

<a id="vibey-roadmap-checkpoint-create"></a>

#### `vibey roadmap checkpoint create`

Create a new integrity checkpoint

Creates a timestamped backup of .vibey/ directory with SHA-256 checksums,
manifest generation, and integrity verification.

**Usage:**
```bash
vibey roadmap checkpoint create [NAME]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME` | TEXT | No |  |

**Examples:**

```bash
vibey roadmap checkpoint create
```

```bash
vibey roadmap checkpoint create pre-refactor
```

---

<a id="vibey-roadmap-checkpoint-list"></a>

#### `vibey roadmap checkpoint list`

List all available checkpoints

Shows checkpoint name, size, creation date, and validation status.


**Usage:**
```bash
vibey roadmap checkpoint list
```

---

<a id="vibey-roadmap-checkpoint-restore"></a>

#### `vibey roadmap checkpoint restore`

Restore from a checkpoint

Restores .vibey/ directory from checkpoint with automatic pre-rollback
backup and verification. Use --verify-only to test without restoring.

**Usage:**
```bash
vibey roadmap checkpoint restore [OPTIONS] <NAME>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verify-only` | flag | `False` | Verify without restoring |

**Examples:**

```bash
vibey roadmap checkpoint restore my-backup --verify-only
```

```bash
vibey roadmap checkpoint restore my-backup
```

---

<a id="vibey-roadmap-checkpoint-verify"></a>

#### `vibey roadmap checkpoint verify`

Verify checkpoint integrity

Validates all files match SHA-256 checksums in manifest and
verifies YAML syntax in all .yaml files.

**Usage:**
```bash
vibey roadmap checkpoint verify <NAME>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME` | TEXT | Yes |  |

**Examples:**

```bash
vibey roadmap checkpoint verify my-backup
```

---

<a id="vibey-roadmap-complete"></a>

#### `vibey roadmap complete`

Complete a track, sprint, or task

For sprints, validates that all tasks are completed before allowing completion.
Use --force to override this check (with warning).

**Usage:**
```bash
vibey roadmap complete [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-commits` | flag | `False` | Skip commit evidence check (for non-code tasks) |
| `--force, -f` | flag | `False` | Force completion even with incomplete tasks (sprints only) |

**Examples:**

```bash
vibey roadmap complete my-track                    # Complete a track
```

```bash
vibey roadmap complete my-track-1                  # Complete a sprint
```

```bash
vibey roadmap complete my-track-1-task-001        # Complete a task
```

```bash
vibey roadmap complete task-001 --no-commits      # Skip commit check
```

```bash
vibey roadmap complete sprint-1 --force           # Force complete with incomplete tasks
```

---

<a id="vibey-roadmap-context"></a>

#### `vibey roadmap context`

Get AI-optimized context for a task

**Usage:**
```bash
vibey roadmap context <TASK_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK_ID` | TEXT | Yes |  |

---

<a id="vibey-roadmap-create-from-plan"></a>

#### `vibey roadmap create-from-plan`

Create roadmap sprint from a plan markdown file

Parses a sprint plan markdown file and creates:
- Sprint YAML in hierarchical structure
- Task YAMLs in hierarchical structure
- Updates track to reference the sprint

The plan file should have a standard format with:
- Header with Sprint ID, Name, Track, Duration
- ## Tasks section with #### Task N: Title blocks
- Each task block can have: Description, Acceptance Criteria, Dependencies

**Usage:**
```bash
vibey roadmap create-from-plan [OPTIONS] <PLAN_FILE>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PLAN_FILE` | Path(exists, file, dir) | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--track` | TEXT | - | Track ID to add sprint to |
| `--sprint` | TEXT | - | Override sprint ID (uses ID from plan if not specified) |
| `--start` | flag | `False` | Mark sprint as started |
| `--dry-run` | flag | `False` | Show what would be created without creating |

**Examples:**

```bash
vibey roadmap create-from-plan sprint-plan.md --track main
```

```bash
vibey roadmap create-from-plan sprint-plan.md --track backend --start
```

```bash
vibey roadmap create-from-plan sprint-plan.md --track api --sprint sprint-5 --dry-run
```

---

<a id="vibey-roadmap-create-sprint"></a>

#### `vibey roadmap create-sprint`

Create a new sprint in a track.

Creates a new sprint YAML file using ULID-based naming in the flat structure.
The sprint is automatically linked to the parent track.

**Usage:**
```bash
vibey roadmap create-sprint [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--track, -t` | TEXT | - | Track ID or slug to add sprint to |
| `--name, -n` | TEXT | - | Sprint name |
| `--goal, -g` | TEXT | `` | Sprint goal |
| `--description, -d` | TEXT | `` | Sprint description |
| `--start` | flag | `False` | Mark sprint as started immediately |

**Examples:**

```bash
vibey roadmap create-sprint --track my-track --name "Sprint 1"
```

```bash
vibey roadmap create-sprint -t auth-system -n "Authentication MVP" -g "Basic login working"
```

```bash
vibey roadmap create-sprint --track 01KC2D0JK06MN77ZHAGAHF5VKD --name "Sprint 1" --start
```

---

<a id="vibey-roadmap-create-task"></a>

#### `vibey roadmap create-task`

Create a new task in a sprint.

Creates a new task YAML file using ULID-based naming in the flat structure.
The task is automatically linked to the parent sprint.

**Usage:**
```bash
vibey roadmap create-task [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--sprint, -s` | TEXT | - | Sprint ID or slug to add task to |
| `--title, -t` | TEXT | - | Task title |
| `--description, -d` | TEXT | `` | Task description |
| `--type` | Choice(['design', 'development', 'documentation', 'infrastructure', 'research', 'review', 'testing']) | `development` | Task type |
| `--priority, -p` | Choice(['critical', 'high', 'low', 'medium']) | `medium` | Task priority |
| `--complexity, -c` | Choice(['complex', 'medium', 'simple']) | `medium` | Task complexity (simple/medium/complex) |

**Examples:**

```bash
vibey roadmap create-task --sprint sprint-1 --title "Add login form"
```

```bash
vibey roadmap create-task -s 01KC2D0JKM9HQR5VHRQ5SX5EQY -t "Write unit tests" --type testing
```

```bash
vibey roadmap create-task --sprint auth-sprint-1 --title "Design auth flow" -p high -c medium
```

---

<a id="vibey-roadmap-create-track"></a>

#### `vibey roadmap create-track`

Create a new track in the roadmap.

Creates a new track YAML file using ULID-based naming in the flat structure.
The track is automatically added to roadmap.yaml's track list.

**Usage:**
```bash
vibey roadmap create-track [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name, -n` | TEXT | - | Track name |
| `--slug, -s` | TEXT | - | URL-friendly slug (generated from name if not provided) |
| `--description, -d` | TEXT | `` | Track description |
| `--priority, -p` | Choice(['critical', 'high', 'low', 'medium']) | `medium` | Track priority |
| `--start` | flag | `False` | Mark track as started immediately |

**Examples:**

```bash
vibey roadmap create-track --name "Authentication System"
```

```bash
vibey roadmap create-track -n "Performance Optimization" -p high
```

```bash
vibey roadmap create-track --name "Bug Fixes" --slug bug-fixes --start
```

---

<a id="vibey-roadmap-db"></a>

#### `vibey roadmap db`

Database operations for roadmap state management.

The database backend provides faster queries and automatic integrity
enforcement via SQLite. Use these commands to manage the database.

**Usage:**
```bash
vibey roadmap db COMMAND
```

**Examples:**

```bash
vibey roadmap db init       # Initialize database from YAML
```

```bash
vibey roadmap db status     # Show database status
```

```bash
vibey roadmap db rebuild    # Rebuild database from YAML
```

```bash
vibey roadmap db backup     # Create database backup
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `backup` | Create a backup of the database.

Creates a timestamped copy... |
| `config` | Show current backend configuration.

Displays the effective ... |
| `dump` | Dump database state to YAML files.

Exports the current data... |
| `init` | Initialize SQLite database from YAML files.

Creates .vibey/... |
| `query` | Query the database for roadmap insights.

These commands lev... |
| `rebuild` | Rebuild database from YAML files.

Drops all tables and relo... |
| `status` | Show database status and health.

Displays:
- Database exist... |
| `validate` | Validate database integrity and consistency.

Validation lev... |

---

<a id="vibey-roadmap-db-backup"></a>

#### `vibey roadmap db backup`

Create a backup of the database.

Creates a timestamped copy of .vibey/roadmap.db for safekeeping.

**Usage:**
```bash
vibey roadmap db backup [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Path(file, dir) | - | Custom backup path |

**Examples:**

```bash
vibey roadmap db backup
```

```bash
vibey roadmap db backup -o ./my-backup.db
```

---

<a id="vibey-roadmap-db-config"></a>

#### `vibey roadmap db config`

Show current backend configuration.

Displays the effective backend mode, database path, and validation settings.

**Usage:**
```bash
vibey roadmap db config
```

**Examples:**

```bash
vibey roadmap db config
```

---

<a id="vibey-roadmap-db-dump"></a>

#### `vibey roadmap db dump`

Dump database state to YAML files.

Exports the current database state to hierarchical YAML files
for version control. This is the reverse of 'db rebuild'.

Safety checks:
- Detects if YAML files were modified externally since last load
- Use --force to overwrite external changes

After dump:
- YAML files updated with database state
- Database marked as clean (is_dirty = 0)
- Checksums stored for change detection

**Usage:**
```bash
vibey roadmap db dump [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force, -f` | flag | `False` | Overwrite YAML even if modified externally |
| `--verbose, -v` | flag | `False` | Show detailed output |

**Examples:**

```bash
vibey roadmap db dump
```

```bash
vibey roadmap db dump --force  # Overwrite external changes
```

```bash
vibey roadmap db dump -v       # Verbose output
```

---

<a id="vibey-roadmap-db-init"></a>

#### `vibey roadmap db init`

Initialize SQLite database from YAML files.

Creates .vibey/roadmap.db with all roadmap data loaded from YAML.
Computes checksums for change detection and sets up triggers.

**Usage:**
```bash
vibey roadmap db init [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force, -f` | flag | `False` | Overwrite existing database |

**Examples:**

```bash
vibey roadmap db init
```

```bash
vibey roadmap db init --force  # Overwrite existing
```

---

<a id="vibey-roadmap-db-query"></a>

#### `vibey roadmap db query`

Query the database for roadmap insights.

These commands leverage SQLite's power to provide
fast queries that would be expensive with YAML parsing.


**Usage:**
```bash
vibey roadmap db query COMMAND
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `blocked` | List all blocked tasks with blocker information.

Shows task... |
| `deps` | Show dependency chain for a task, sprint, or track.

Example... |
| `progress` | Show progress summary grouped by track, sprint, or status.

... |
| `stats` | Show overall roadmap statistics.

Displays completion rates,... |

---

<a id="vibey-roadmap-db-query-blocked"></a>

#### `vibey roadmap db query blocked`

List all blocked tasks with blocker information.

Shows tasks that are blocked by dependencies and what they're waiting for.

**Usage:**
```bash
vibey roadmap db query blocked [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--track, -t` | TEXT | - | Filter by track ID |
| `--verbose, -v` | flag | `False` | Show detailed blocker info |

**Examples:**

```bash
vibey roadmap db query blocked
```

```bash
vibey roadmap db query blocked -t sqlite-backend
```

```bash
vibey roadmap db query blocked -v
```

---

<a id="vibey-roadmap-db-query-deps"></a>

#### `vibey roadmap db query deps`

Show dependency chain for a task, sprint, or track.

**Usage:**
```bash
vibey roadmap db query deps [OPTIONS] <ENTITY_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ENTITY_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--direction` | Choice(['both', 'down', 'up']) | `both` | Show dependencies (up), dependents (down), or both |

**Examples:**

```bash
vibey roadmap db query deps 01KC2D0JK7READW9KAK1HBX4B8
```

```bash
vibey roadmap db query deps 01KC2D0JK9JKQXGQW6MQEB0JZP --direction up
```

---

<a id="vibey-roadmap-db-query-progress"></a>

#### `vibey roadmap db query progress`

Show progress summary grouped by track, sprint, or status.

**Usage:**
```bash
vibey roadmap db query progress [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--by` | Choice(['sprint', 'status', 'track']) | `track` | Group progress by |

**Examples:**

```bash
vibey roadmap db query progress
```

```bash
vibey roadmap db query progress --by sprint
```

```bash
vibey roadmap db query progress --by status
```

---

<a id="vibey-roadmap-db-query-stats"></a>

#### `vibey roadmap db query stats`

Show overall roadmap statistics.

Displays completion rates, task counts by status, and other metrics.

**Usage:**
```bash
vibey roadmap db query stats
```

**Examples:**

```bash
vibey roadmap db query stats
```

---

<a id="vibey-roadmap-db-rebuild"></a>

#### `vibey roadmap db rebuild`

Rebuild database from YAML files.

Drops all tables and reloads from YAML. Use after pulling changes
or to fix database corruption.

WARNING: Uncommitted database changes will be lost!

**Usage:**
```bash
vibey roadmap db rebuild [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force, -f` | flag | `False` | Force rebuild even with uncommitted changes |

**Examples:**

```bash
vibey roadmap db rebuild
```

```bash
vibey roadmap db rebuild --force  # Skip dirty check
```

---

<a id="vibey-roadmap-db-status"></a>

#### `vibey roadmap db status`

Show database status and health.

Displays:
- Database existence and location
- Dirty flag (uncommitted changes)
- Row counts vs YAML file counts
- Schema version and integrity
- Checksum mismatches (if any)

**Usage:**
```bash
vibey roadmap db status [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `False` | Show detailed information |

**Examples:**

```bash
vibey roadmap db status
```

```bash
vibey roadmap db status -v  # Detailed view
```

---

<a id="vibey-roadmap-db-validate"></a>

#### `vibey roadmap db validate`

Validate database integrity and consistency.

Validation levels:
  schema     - Check tables, indexes, and constraints exist
  references - Check foreign key relationships are valid
  computed   - Verify computed values match (progress, counts)
  full       - Run all validation checks (default)

The --compare flag adds DB vs YAML comparison to detect drift.

**Usage:**
```bash
vibey roadmap db validate [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--level` | Choice(['computed', 'full', 'references', 'schema']) | `full` | Validation level |
| `--compare` | flag | `False` | Compare database with YAML files |
| `--verbose, -v` | flag | `False` | Show detailed output |

**Examples:**

```bash
vibey roadmap db validate
```

```bash
vibey roadmap db validate --level schema
```

```bash
vibey roadmap db validate --compare
```

```bash
vibey roadmap db validate --compare --verbose
```

---

<a id="vibey-roadmap-doc-changelog"></a>

#### `vibey roadmap doc-changelog`

Generate a documentation changelog

Generates a markdown changelog showing which roadmap objects have
impacted which documentation files.

**Usage:**
```bash
vibey roadmap doc-changelog [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--object` | TEXT | - | Filter to specific roadmap object |
| `--start-date` | TEXT | - | Start date filter (YYYY-MM-DD) |
| `--end-date` | TEXT | - | End date filter (YYYY-MM-DD) |
| `--group-by` | Choice(['object', 'time']) | `object` | How to group changes |
| `--output, -o` | TEXT | - | Output file path (default: stdout) |

**Examples:**

```bash
vibey roadmap doc-changelog                        # Full changelog
```

```bash
vibey roadmap doc-changelog --object feature-1    # Filter to feature
```

```bash
vibey roadmap doc-changelog --group-by time       # Group by date
```

```bash
vibey roadmap doc-changelog -o CHANGELOG.md       # Write to file
```

---

<a id="vibey-roadmap-edit"></a>

#### `vibey roadmap edit`

Safe YAML editing with automatic validation and backups.

All edit commands create automatic backups before modifying files and
validate YAML syntax and schema. Bulk edits use transaction semantics
(all-or-nothing).

**Usage:**
```bash
vibey roadmap edit COMMAND
```

**Examples:**

```bash
vibey roadmap edit file task.yaml --set status=completed
```

```bash
vibey roadmap edit bulk "**/task.yaml" --set status=completed
```

```bash
vibey roadmap edit validate task.yaml
```

```bash
vibey roadmap edit rollback
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `bulk` | Bulk edit multiple YAML files with transaction semantics

Us... |
| `file` | Edit a single YAML file safely

Modifies fields using dot no... |
| `rollback` | Rollback recent edit operations

Restores files from automat... |
| `validate` | Validate YAML file(s)

Validates YAML syntax, schema, and bu... |

---

<a id="vibey-roadmap-edit-bulk"></a>

#### `vibey roadmap edit bulk`

Bulk edit multiple YAML files with transaction semantics

Uses all-or-nothing transaction: if ANY file fails validation,
ALL changes are rolled back.

**Usage:**
```bash
vibey roadmap edit bulk [OPTIONS] <FILE_PATTERN>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE_PATTERN` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--set` | TEXT | - | Field=value pairs to modify |
| `--dry-run` | flag | `False` | Preview changes without applying |

**Examples:**

```bash
vibey roadmap edit bulk "sprint-2/**/task.yaml" --set status=completed
```

```bash
vibey roadmap edit bulk "**/sprint.yaml" --set sprint.status=in_progress --dry-run
```

---

<a id="vibey-roadmap-edit-file"></a>

#### `vibey roadmap edit file`

Edit a single YAML file safely

Modifies fields using dot notation (e.g., task.status, task.priority).
Creates automatic backup before editing.

**Usage:**
```bash
vibey roadmap edit file [OPTIONS] <FILE_PATH>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE_PATH` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--set` | TEXT | - | Field=value pairs to modify |
| `--dry-run` | flag | `False` | Preview changes without applying |

**Examples:**

```bash
vibey roadmap edit file task.yaml --set status=completed
```

```bash
vibey roadmap edit file task.yaml --set task.priority=high --dry-run
```

```bash
vibey roadmap edit file sprint.yaml --set sprint.status=completed
```

---

<a id="vibey-roadmap-edit-rollback"></a>

#### `vibey roadmap edit rollback`

Rollback recent edit operations

Restores files from automatic backups.

**Usage:**
```bash
vibey roadmap edit rollback [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--last-n` | INTEGER | `1` | Number of edits to rollback (default: 1) |

**Examples:**

```bash
vibey roadmap edit rollback
```

```bash
vibey roadmap edit rollback --last-n 3
```

---

<a id="vibey-roadmap-edit-validate"></a>

#### `vibey roadmap edit validate`

Validate YAML file(s)

Validates YAML syntax, schema, and business logic.

**Usage:**
```bash
vibey roadmap edit validate [OPTIONS] [FILE_PATH]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE_PATH` | TEXT | No |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | flag | `False` | Validate all YAML files in roadmap |

**Examples:**

```bash
vibey roadmap edit validate task.yaml
```

```bash
vibey roadmap edit validate --all
```

---

<a id="vibey-roadmap-extract-embedded"></a>

#### `vibey roadmap extract-embedded`

Extract embedded tasks from sprint files to standalone task files.

Scans all sprint YAML files for embedded tasks[] arrays and creates
individual task files in the flat .vibey/roadmap/tasks/ directory.

By default, runs in dry-run mode to show what would be extracted.
Use --execute to actually create the task files.

**Usage:**
```bash
vibey roadmap extract-embedded [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--execute` | flag | `False` | Execute extraction (default is dry-run) |
| `--quiet` | flag | `False` | Reduce output verbosity |

**Examples:**

```bash
vibey roadmap extract-embedded            # Dry run (show what would be extracted)
```

```bash
vibey roadmap extract-embedded --execute  # Create task files
```

```bash
vibey roadmap extract-embedded --quiet    # Less verbose output
```

---

<a id="vibey-roadmap-init"></a>

#### `vibey roadmap init`

Initialize a new roadmap in .vibey/roadmap.yaml

**Usage:**
```bash
vibey roadmap init [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | TEXT | - | Name of the roadmap |
| `--version` | TEXT | `1.0.0` | Initial version |

---

<a id="vibey-roadmap-install-hooks"></a>

#### `vibey roadmap install-hooks`

Install git pre-commit hook for roadmap validation

The pre-commit hook automatically validates roadmap data before
allowing commits. This prevents corrupted or invalid data from
being committed.

The hook runs when .vibey/roadmap/ files are modified and:
  - Validates YAML syntax
  - Checks data integrity
  - Verifies schema compliance

Bypass (emergency only):
  git commit --no-verify

**Usage:**
```bash
vibey roadmap install-hooks [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | flag | `False` | Overwrite existing pre-commit hook |

**Examples:**

```bash
vibey roadmap install-hooks           # Install hook
```

```bash
vibey roadmap install-hooks --force   # Overwrite existing hook
```

---

<a id="vibey-roadmap-link-doc"></a>

#### `vibey roadmap link-doc`

Link a documentation file to a roadmap object

Creates or updates a .meta.json sidecar file that tracks which roadmap
objects have impacted this documentation.

**Usage:**
```bash
vibey roadmap link-doc [OPTIONS] <DOC_PATH> <ROADMAP_OBJECT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `DOC_PATH` | TEXT | Yes |  |
| `ROADMAP_OBJECT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--change-type, -t` | Choice(['added_section', 'created', 'fixed', 'refactored', 'removed', 'updated']) | `updated` | Type of documentation change |
| `--section, -s` | TEXT | - | Specific section that was changed |
| `--description, -d` | TEXT | - | Description of the change |

**Examples:**

```bash
vibey roadmap link-doc docs/API.md feature-1-task-003 -t added_section -s "Authentication"
```

```bash
vibey roadmap link-doc README.md infrastructure-fixes -t updated -d "Updated install steps"
```

---

<a id="vibey-roadmap-list-docs"></a>

#### `vibey roadmap list-docs`

List all tracked documentation files

Shows all documentation files that have .meta.json tracking files,
along with their recent impacts.

**Usage:**
```bash
vibey roadmap list-docs [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--object` | TEXT | - | Filter to docs linked to this roadmap object |

**Examples:**

```bash
vibey roadmap list-docs                    # List all tracked docs
```

```bash
vibey roadmap list-docs --object task-001  # List docs linked to task-001
```

---

<a id="vibey-roadmap-migrate-docs"></a>

#### `vibey roadmap migrate-docs`

Migrate documentation fields from YAML to markdown files.

This command migrates documentation-like fields from YAML to markdown:


- version_strategy → VERSIONING_POLICY.md (roadmap directory)
- version_history → CHANGELOG.md (repository root)
- metadata.notes → NOTES.md (per-entity directories)

Benefits of markdown:
- Rich formatting (headings, tables, code blocks)
- Git-diffable content
- Searchable with grep/ripgrep
- Human readable without tooling

**Usage:**
```bash
vibey roadmap migrate-docs [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | `False` | Show what would be created without making changes |
| `--path, -p` | Path(exists, file, dir) | - | Path to roadmap directory |
| `--verbose, -v` | flag | `False` | Show detailed progress |

**Examples:**

*Preview changes:*
```bash
vibey roadmap migrate-docs --dry-run
```

*Run migration:*
```bash
vibey roadmap migrate-docs
```

*Verbose output:*
```bash
vibey roadmap migrate-docs --verbose
```

---

<a id="vibey-roadmap-migrate-format"></a>

#### `vibey roadmap migrate-format`

Migrate YAML files from v1 format to v2 format.

V1 format uses legacy field names (created, assigned_agent, title).
V2 format uses unified ticket architecture (created_at, assigned_agents, name).

This command:
- Scans all YAML files in the roadmap directory
- Detects which files are v1 format
- Transforms v1 fields to v2 format
- Creates backups before modification (unless --no-backup)
- Validates migrated files

**Usage:**
```bash
vibey roadmap migrate-format [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | `False` | Show what would change without modifying files |
| `--backup` | flag | `True` | Create .v1.bak backup files (default: yes) |
| `--path, -p` | Path(exists, file, dir) | - | Path to roadmap directory |
| `--force, -f` | flag | `False` | Skip confirmation prompt |
| `--verbose, -v` | flag | `False` | Show detailed progress |

**Examples:**

*Preview changes:*
```bash
vibey roadmap migrate-format --dry-run
```

*Migrate with backups (interactive):*
```bash
vibey roadmap migrate-format
```

*Force migrate without confirmation:*
```bash
vibey roadmap migrate-format --force
```

*Verbose output:*
```bash
vibey roadmap migrate-format --verbose --dry-run
```

---

<a id="vibey-roadmap-override-standard"></a>

#### `vibey roadmap override-standard`

Override a standard for a specific item

Adds an override to a standard, allowing completion even if the standard
would normally block it. The override is tracked with reason and author.

**Usage:**
```bash
vibey roadmap override-standard [OPTIONS] <STANDARD_ID> <ITEM_ID> <REASON>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `STANDARD_ID` | TEXT | Yes |  |
| `ITEM_ID` | TEXT | Yes |  |
| `REASON` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--overridden-by` | TEXT | `system` | Who is overriding (default: system) |

**Examples:**

```bash
vibey roadmap override-standard commit-required task-001 \
```

```bash
vibey roadmap override-standard test-coverage sprint-1 \
```

---

<a id="vibey-roadmap-recalculate"></a>

#### `vibey roadmap recalculate`

Recalculate sprint tasks for a different platform

Splits oversized tasks into subtasks that fit within the target
platform's context window. Preserves dependencies, success criteria,
and agent assignments.

**Usage:**
```bash
vibey roadmap recalculate [OPTIONS] <SPRINT_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SPRINT_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform, -p` | TEXT | - | Target platform (auto-detect if not specified) |
| `--context-window, -c` | INTEGER | - | Target context window size (tokens) |
| `--dry-run` | flag | `False` | Show plan without applying changes |
| `--verbose, -v` | flag | `False` | Show detailed output |
| `--yes, -y` | flag | `False` | Skip confirmation prompt |

**Examples:**

```bash
vibey roadmap recalculate auth-sprint-1
```

```bash
vibey roadmap recalculate sprint-1 --platform goose
```

```bash
vibey roadmap recalculate sprint-1 --context-window 128000
```

```bash
vibey roadmap recalculate sprint-1 --dry-run
```

---

<a id="vibey-roadmap-reconcile"></a>

#### `vibey roadmap reconcile`

Detect and fix status inconsistencies in roadmap data.

Checks for status mismatches between parent/child objects:
- Sprints marked completed but with incomplete tasks
- Tracks marked completed but with incomplete sprints
- Tasks marked completed but with null dates
- Progress counts that don't match actual task counts

By default, runs in dry-run mode (report only). Use --fix to apply corrections.

**Usage:**
```bash
vibey roadmap reconcile [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--fix` | flag | `False` | Auto-fix detected issues |
| `--dry-run` | flag | `False` | Show issues without fixing (default) |
| `--verbose, -v` | flag | `False` | Show detailed information |

**Examples:**

```bash
vibey roadmap reconcile                  # Report issues (dry-run)
```

```bash
vibey roadmap reconcile --fix            # Fix detected issues
```

```bash
vibey roadmap reconcile --verbose        # Detailed report
```

---

<a id="vibey-roadmap-repair"></a>

#### `vibey roadmap repair`

Auto-repair common roadmap integrity issues

Repairs:
  - Progress counter mismatches (safe, auto-fixable)
  - Broken task references (removes invalid references)

**Usage:**
```bash
vibey roadmap repair [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--progress` | flag | `False` | Fix progress counter mismatches (safe) |
| `--references` | flag | `False` | Remove broken references (requires caution) |
| `--all` | flag | `False` | Fix all auto-repairable issues |
| `--dry-run` | flag | `False` | Preview repairs without applying changes |
| `--verbose, -v` | flag | `False` | Show detailed repair information |

**Examples:**

```bash
vibey roadmap repair --all --dry-run          # Preview all repairs
```

```bash
vibey roadmap repair --progress               # Fix progress counters only
```

```bash
vibey roadmap repair --all                    # Apply all repairs
```

```bash
vibey roadmap repair --references --verbose   # Remove broken refs (verbose)
```

---

<a id="vibey-roadmap-revert"></a>

#### `vibey roadmap revert`

Revert a track, sprint, or task to a previous status

Allows undoing premature completions or status changes.
Only backward transitions are allowed (completed → in_progress → not_started).

**Usage:**
```bash
vibey roadmap revert [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--to` | Choice(['in_progress', 'not_started']) | - | Target status to revert to |
| `--yes, -y` | flag | `False` | Skip confirmation prompt |

**Examples:**

```bash
vibey roadmap revert my-sprint --to in_progress     # Revert completed sprint
```

```bash
vibey roadmap revert my-task --to not_started       # Reset task to not started
```

```bash
vibey roadmap revert my-track --to in_progress -y   # Skip confirmation
```

---

<a id="vibey-roadmap-show"></a>

#### `vibey roadmap show`

Show details for a track, sprint, or task

For sprints, also shows platform compatibility status to help
you understand if tasks fit in your context window.

**Usage:**
```bash
vibey roadmap show [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-compatibility` | flag | `False` | Skip compatibility status display |

**Examples:**

```bash
vibey roadmap show sprint-1
```

```bash
vibey roadmap show task-001
```

```bash
vibey roadmap show my-track
```

---

<a id="vibey-roadmap-start"></a>

#### `vibey roadmap start`

Start a sprint or task

When starting a sprint, checks if tasks fit in your platform's context
window. If compatibility issues are found, you'll be prompted to
recalculate before proceeding.

**Usage:**
```bash
vibey roadmap start [OPTIONS] <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--skip-compatibility` | flag | `False` | Skip compatibility check (not recommended) |
| `--force, -f` | flag | `False` | Force start without prompts |

**Examples:**

```bash
vibey roadmap start sprint-1
```

```bash
vibey roadmap start task-001
```

```bash
vibey roadmap start sprint-1 --skip-compatibility
```

---

<a id="vibey-roadmap-status"></a>

#### `vibey roadmap status`

Show roadmap status - tracks, sprints, and tasks

**Usage:**
```bash
vibey roadmap status [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--track` | TEXT | - | Show status for specific track |
| `--sprint` | TEXT | - | Show status for specific sprint |

---

<a id="vibey-roadmap-summarize"></a>

#### `vibey roadmap summarize`

Summarize a sprint, task, or track

**Usage:**
```bash
vibey roadmap summarize <ITEM_TYPE> <ITEM_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `ITEM_TYPE` | Choice(['sprint', 'task', 'track']) | Yes |  |
| `ITEM_ID` | TEXT | Yes |  |

---

<a id="vibey-roadmap-sync"></a>

#### `vibey roadmap sync`

Sync status from individual files to main roadmap.yaml

Reconciles track/sprint/task status from individual YAML files
back to the main .vibey/roadmap.yaml file. Use this after manual
YAML edits or to fix status inconsistencies.

**Usage:**
```bash
vibey roadmap sync [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `False` | Show detailed sync information |

**Examples:**

```bash
vibey roadmap sync           # Sync all status
```

```bash
vibey roadmap sync -v        # Sync with verbose output
```

---

<a id="vibey-roadmap-sync-commits"></a>

#### `vibey roadmap sync-commits`

Scan git history and link commits to tasks based on commit messages

Automatically finds commits that reference task IDs and links them
to the corresponding tasks in the roadmap.

**Usage:**
```bash
vibey roadmap sync-commits [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | `False` | Show what would be linked without making changes |

**Examples:**

```bash
vibey roadmap sync-commits
```

```bash
vibey roadmap sync-commits --dry-run
```

---

<a id="vibey-roadmap-sync-docs"></a>

#### `vibey roadmap sync-docs`

Synchronize documentation from .vibey/roadmap/ to docs/roadmap/

Copies markdown documentation from the roadmap source of truth to the
user-facing docs directory, respecting include/exclude patterns.

**Usage:**
```bash
vibey roadmap sync-docs [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | flag | `False` | Sync all documentation |
| `--track` | TEXT | - | Sync specific track only |
| `--sprint` | TEXT | - | Sync specific sprint only |
| `--summaries-only` | flag | `False` | Only sync summary/completion files |
| `--dry-run` | flag | `False` | Preview changes without syncing |
| `--delete-orphaned` | flag | `False` | Delete files in target not in source |

**Examples:**

```bash
vibey roadmap sync-docs --all              # Sync all documentation
```

```bash
vibey roadmap sync-docs --track my-track   # Sync specific track
```

```bash
vibey roadmap sync-docs --dry-run          # Preview changes
```

```bash
vibey roadmap sync-docs --delete-orphaned  # Clean up old files
```

---

<a id="vibey-roadmap-uninstall-hooks"></a>

#### `vibey roadmap uninstall-hooks`

Uninstall git pre-commit hook

Removes the Vibey pre-commit validation hook from the repository.
Only removes Vibey hooks - other hooks are left untouched.

**Usage:**
```bash
vibey roadmap uninstall-hooks
```

**Examples:**

```bash
vibey roadmap uninstall-hooks
```

---

<a id="vibey-roadmap-validate-advanced"></a>

#### `vibey roadmap validate-advanced`

Advanced validation for complex integrity issues

Detects:
  - Circular dependencies between tasks
  - Orphaned tasks (missing sprint references)
  - Broken task references
  - Progress counter mismatches

**Usage:**
```bash
vibey roadmap validate-advanced [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `False` | Show detailed information |
| `--check` | Choice(['all', 'circular', 'orphans', 'progress', 'references']) | `all` | Type of check to run |

**Examples:**

```bash
vibey roadmap validate-advanced
```

```bash
vibey roadmap validate-advanced --verbose
```

```bash
vibey roadmap validate-advanced --check circular
```

```bash
vibey roadmap validate-advanced --check orphans
```

---

<a id="vibey-roadmap-validate-commits"></a>

#### `vibey roadmap validate-commits`

Validate that all completed tasks have commit evidence

Checks all completed tasks and reports any that are missing commits.

**Usage:**
```bash
vibey roadmap validate-commits
```

**Examples:**

```bash
vibey roadmap validate-commits
```

---

<a id="vibey-roadmap-validate-fast"></a>

#### `vibey roadmap validate-fast`

Fast roadmap validation with caching and parallel loading

Validation profiles:
  quick: <3s - Syntax only
  standard: <10s - Full validation (default)
  thorough: <20s - With git integration

**Usage:**
```bash
vibey roadmap validate-fast [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--profile` | Choice(['quick', 'standard', 'thorough']) | `standard` | Validation profile (default: standard) |
| `--incremental` | flag | `False` | Only validate changed files (requires git) |
| `--verbose, -v` | flag | `False` | Show all errors |
| `--benchmark` | flag | `False` | Run performance benchmark |

**Examples:**

```bash
vibey roadmap validate-fast
```

```bash
vibey roadmap validate-fast --profile quick
```

```bash
vibey roadmap validate-fast --incremental
```

```bash
vibey roadmap validate-fast --benchmark
```

---

<a id="vibey-roadmap-validate-structure"></a>

#### `vibey roadmap validate-structure`

Validate roadmap directory structure is flat (no ULID directories).

Ensures the roadmap uses the flat ULID-based structure:
  .vibey/roadmap/tracks/{ulid}.yaml
  .vibey/roadmap/sprints/{ulid}.yaml
  .vibey/roadmap/tasks/{ulid}.yaml

Fails if legacy hierarchical directories exist (01KC.../01KC.../...).

Use --fix to automatically delete hierarchical directories after
verifying data exists in the flat structure.

**Usage:**
```bash
vibey roadmap validate-structure [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--fix` | flag | `False` | Automatically delete hierarchical ULID directories |

**Examples:**

```bash
vibey roadmap validate-structure         # Check structure
```

```bash
vibey roadmap validate-structure --fix   # Auto-fix issues
```

---

<a id="vibey-roadmap-verify-change"></a>

#### `vibey roadmap verify-change`

Verify a roadmap file change has a matching activity log entry

Checks if the file's current content hash matches a file_hash_after
in the activity log. This proves the change was made through the CLI.

Exit codes:
  0 - File is verified (has matching activity log entry)
  1 - File is unverified (no matching entry found)
  2 - Error occurred

**Usage:**
```bash
vibey roadmap verify-change [OPTIONS] <FILE_PATH>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE_PATH` | Path(exists, file, dir) | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | flag | `False` | Output JSON format |

**Examples:**

```bash
vibey roadmap verify-change .vibey/roadmap/tasks/01KC...yaml
```

```bash
vibey roadmap verify-change .vibey/roadmap/sprints/01KC...yaml --json
```

---

<a id="vibey-roadmap-verify-commits"></a>

#### `vibey roadmap verify-commits`

Verify roadmap changes in a commit range have activity log entries.

Verifies all roadmap file changes in the specified commit range.
Designed for CI/CD pipelines to enforce roadmap integrity.

COMMIT_RANGE: Git revision range (e.g., main..HEAD, abc123..def456)

Exit codes:
  0 - All commits verified
  1 - Some commits have unverified changes
  2 - Error occurred

**Usage:**
```bash
vibey roadmap verify-commits [OPTIONS] <COMMIT_RANGE>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `COMMIT_RANGE` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | flag | `False` | Output JSON format for CI parsing |

**Examples:**

```bash
vibey roadmap verify-commits main..HEAD
```

```bash
vibey roadmap verify-commits origin/main..HEAD --json
```

```bash
vibey roadmap verify-commits abc123..def456
```

---

<a id="vibey-session"></a>

### `vibey session`

Manage AI-assisted coding sessions.

Track session lifecycle, log events and decisions, associate commits,
and maintain context for session reconstruction.

**Usage:**
```bash
vibey session COMMAND
```

**Examples:**

```bash
vibey session start                        # Start new session
```

```bash
vibey session start "Feature work"         # Start with name
```

```bash
vibey session status                       # Show active session
```

```bash
vibey session end --summary "Completed X"  # End session
```

```bash
vibey session list                         # List all sessions
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `decisions` | Show decisions made during a session.

Lists all decisions r... |
| `end` | End the current or specified session.

Marks the session as ... |
| `export` | Export session for continuation.

Exports session state incl... |
| `list` | List sessions with optional filters.

Shows all sessions mat... |
| `pause` | Pause the current or specified session.

Temporarily stops t... |
| `report` | Generate a session report.

Creates a human-readable report ... |
| `resume` | Resume a paused session.

Continues a previously paused sess... |
| `show` | Show detailed information about a specific session.

Display... |
| `start` | Start a new coding session.

Creates a new session to track ... |
| `status` | Show the current active session status.

Displays informatio... |
| `timeline` | Show session timeline of events.

Displays a chronological l... |

---

<a id="vibey-session-decisions"></a>

#### `vibey session decisions`

Show decisions made during a session.

Lists all decisions recorded during the session with their rationale,
alternatives considered, and whether they need revisiting.

**Usage:**
```bash
vibey session decisions <SESSION_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SESSION_ID` | TEXT | Yes |  |

**Examples:**

```bash
vibey session decisions 01ABC123...
```

---

<a id="vibey-session-end"></a>

#### `vibey session end`

End the current or specified session.

Marks the session as completed or abandoned, captures final git state,
and calculates session statistics.

**Usage:**
```bash
vibey session end [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--summary, -s` | TEXT | - | Session summary |
| `--status` | Choice(['abandoned', 'completed']) | `completed` | End status |
| `--session-id` | TEXT | - | Specific session ID to end (default: active) |

**Examples:**

```bash
vibey session end                                    # End active session
```

```bash
vibey session end --summary "Completed feature X"    # With summary
```

```bash
vibey session end --status abandoned                 # Mark as abandoned
```

```bash
vibey session end --session-id 01ABC123...          # End specific session
```

---

<a id="vibey-session-export"></a>

#### `vibey session export`

Export session for continuation.

Exports session state including incomplete tasks, goals, and decisions
that need revisiting. Useful for resuming work in a new session.

**Usage:**
```bash
vibey session export [OPTIONS] <SESSION_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SESSION_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | Path(file, dir) | - | Write export to file |

**Examples:**

```bash
vibey session export 01ABC123...               # Print to console
```

```bash
vibey session export 01ABC123... -o state.json # Save to file
```

---

<a id="vibey-session-list"></a>

#### `vibey session list`

List sessions with optional filters.

Shows all sessions matching the specified filters, sorted by creation date.

**Usage:**
```bash
vibey session list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--status` | Choice(['abandoned', 'active', 'completed', 'paused']) | - | Filter by status |
| `--track, -t` | TEXT | - | Filter by track ID |
| `--sprint, -s` | TEXT | - | Filter by sprint ID |
| `--since` | TEXT | - | Filter by date (ISO format or relative: 7d, 2w, 1m) |
| `--limit, -n` | INTEGER | `20` | Maximum sessions to show |

**Examples:**

```bash
vibey session list                      # List all sessions
```

```bash
vibey session list --status completed   # Only completed sessions
```

```bash
vibey session list --track my-track     # Filter by track
```

```bash
vibey session list --since 7d -n 10     # Last 7 days, max 10
```

---

<a id="vibey-session-pause"></a>

#### `vibey session pause`

Pause the current or specified session.

Temporarily stops tracking while preserving state. Use 'resume' to continue.

**Usage:**
```bash
vibey session pause [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--session-id` | TEXT | - | Specific session ID to pause (default: active) |

**Examples:**

```bash
vibey session pause                       # Pause active session
```

```bash
vibey session pause --session-id 01ABC... # Pause specific session
```

---

<a id="vibey-session-report"></a>

#### `vibey session report`

Generate a session report.

Creates a human-readable report of the session including summary,
goals, tasks, commits, decisions, and timeline.

**Usage:**
```bash
vibey session report [OPTIONS] <SESSION_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SESSION_ID` | TEXT | Yes |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | Choice(['markdown', 'text']) | `markdown` | Output format |
| `--output, -o` | Path(file, dir) | - | Write report to file |

**Examples:**

```bash
vibey session report 01ABC123...              # Print to console
```

```bash
vibey session report 01ABC123... -o report.md # Save to file
```

```bash
vibey session report 01ABC123... -f text      # Plain text format
```

---

<a id="vibey-session-resume"></a>

#### `vibey session resume`

Resume a paused session.

Continues a previously paused session, restoring it as the active session.

**Usage:**
```bash
vibey session resume <SESSION_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SESSION_ID` | TEXT | Yes |  |

**Examples:**

```bash
vibey session resume 01ABC123DEF456GHI789JKL012
```

---

<a id="vibey-session-show"></a>

#### `vibey session show`

Show detailed information about a specific session.

Displays comprehensive session details including events, decisions,
commits, and statistics.

**Usage:**
```bash
vibey session show <SESSION_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SESSION_ID` | TEXT | Yes |  |

**Examples:**

```bash
vibey session show 01ABC123DEF456GHI789JKL012
```

---

<a id="vibey-session-start"></a>

#### `vibey session start`

Start a new coding session.

Creates a new session to track work, decisions, and commits. Only one
session can be active at a time.

**Usage:**
```bash
vibey session start [OPTIONS] [NAME]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME` | TEXT | No |  |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--goal, -g` | TEXT | - | Session goal (can specify multiple) |
| `--track, -t` | TEXT | - | Associate with track ID |
| `--sprint, -s` | TEXT | - | Associate with sprint ID |
| `--task, -T` | TEXT | - | Associate with task ID (can specify multiple) |

**Examples:**

```bash
vibey session start                              # Auto-generated name
```

```bash
vibey session start "Implement auth"             # Custom name
```

```bash
vibey session start -g "Fix login bug" -g "Add tests"  # With goals
```

```bash
vibey session start --track my-track --sprint sprint-1  # With associations
```

---

<a id="vibey-session-status"></a>

#### `vibey session status`

Show the current active session status.

Displays information about the currently active session, including
goals, associations, and event/decision counts.

**Usage:**
```bash
vibey session status
```

**Examples:**

```bash
vibey session status
```

---

<a id="vibey-session-timeline"></a>

#### `vibey session timeline`

Show session timeline of events.

Displays a chronological list of all events that occurred during
the session with timestamps and details.

**Usage:**
```bash
vibey session timeline <SESSION_ID>
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SESSION_ID` | TEXT | Yes |  |

**Examples:**

```bash
vibey session timeline 01ABC123...
```

---

<a id="vibey-validate"></a>

### `vibey validate`

Validate framework assets and documentation.

Run validation checks on roadmap documentation organization
and asset frontmatter (agents, workflows, handoffs).

**Usage:**
```bash
vibey validate COMMAND
```

**Examples:**

```bash
vibey validate docs       # Validate roadmap doc organization
```

```bash
vibey validate assets     # Validate all asset frontmatter
```

```bash
vibey validate assets --type agents  # Validate only agents
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `assets` | Validate asset frontmatter (agents, workflows, handoffs)

Ch... |
| `docs` | Validate documentation organization in roadmap

Ensures all ... |

---

<a id="vibey-validate-assets"></a>

#### `vibey validate assets`

Validate asset frontmatter (agents, workflows, handoffs)

Checks that all markdown assets have valid YAML frontmatter
required for MCP server dynamic tool discovery.

Validates:
- Required fields (id, name, type, version)
- Valid enum values (agent types, priorities)
- Input/output definitions
- Step definitions for workflows

**Usage:**
```bash
vibey validate assets [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice(['agents', 'all', 'handoffs', 'workflows']) | `all` | Type of assets to validate |
| `--verbose, -v` | flag | `False` | Show detailed output |

**Examples:**

```bash
vibey validate assets
```

```bash
vibey validate assets --type agents
```

```bash
vibey validate assets --type workflows --verbose
```

---

<a id="vibey-validate-docs"></a>

#### `vibey validate docs`

Validate documentation organization in roadmap

Ensures all documentation follows organization standards:
- Only core files (track.yaml, sprint.yaml, task.yaml) at their levels
- Analysis files must be in context/ subdirectories
- No loose files at track or sprint levels

**Usage:**
```bash
vibey validate docs [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `False` | Show detailed output |

**Examples:**

```bash
vibey validate docs
```

```bash
vibey validate docs --verbose
```

---

---

*This documentation was auto-generated from the CLI source code.*

*Generated at: 2025-12-15T23:21:29.641766+00:00*