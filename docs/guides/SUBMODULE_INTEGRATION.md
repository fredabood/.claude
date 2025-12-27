# Git Submodule Integration Guide

This guide covers how to use Vibey with git submodules. Vibey provides tools for managing roadmaps across multiple repositories that are linked via git submodules.

## Overview

Vibey's submodule integration follows a key isolation principle:

> **Submodules have NO knowledge of parent repos.** All cross-repo data lives in the PARENT repo only.

This means:
- A submodule works identically whether accessed directly or as part of a larger project
- Cross-repo relationships are tracked only in the parent repository
- Parent repos can "pull up" progress from submodules
- Parent repos can "push down" requirements to submodules

## Quick Start

### 1. Discover Submodules

```bash
# List all git submodules
vibey submodule list

# Discover submodules with Vibey roadmaps
vibey submodule discover

# Auto-register discovered submodules
vibey submodule discover --register
```

### 2. View Submodule Status

```bash
# Show aggregated progress across all submodules
vibey submodule status

# Show details for a specific submodule
vibey submodule show libs/core
```

### 3. Push Requirements to Submodules

```bash
# Create a linked task (in both parent and submodule)
vibey submodule push libs/core --title "Add logging feature" --mode linked

# Create task in parent only (external dependency)
vibey submodule push libs/core --title "Needs API v2" --mode parent_only
```

## Commands Reference

### Discovery & Registry

| Command | Description |
|---------|-------------|
| `vibey submodule list` | List all detected submodules with Vibey status |
| `vibey submodule discover` | Auto-discover from .gitmodules |
| `vibey submodule show <path>` | Show details for specific submodule |

### Push-down Operations

| Command | Description |
|---------|-------------|
| `vibey submodule push <path> --title <title>` | Push task to submodule |
| `vibey submodule requirements` | List cross-repo requirements |
| `vibey submodule link <parent_id> <sub_id>` | Link existing tasks |
| `vibey submodule unlink <parent_id>` | Remove task link |

### Aggregation Operations

| Command | Description |
|---------|-------------|
| `vibey submodule status` | Show aggregated progress |
| `vibey submodule aggregate` | Pull progress and sync blockers |
| `vibey submodule blockers` | List blockers from submodules |
| `vibey submodule refresh <path>` | Force refresh single submodule |

### Dependency Management

| Command | Description |
|---------|-------------|
| `vibey submodule add-dep <ticket> <ref>` | Add cross-repo dependency |
| `vibey submodule deps <ticket>` | List dependencies for a ticket |
| `vibey submodule validate-deps` | Check for cycles and broken links |
| `vibey submodule dep-graph` | Visualize dependency graph |

### Configuration

| Command | Description |
|---------|-------------|
| `vibey submodule config` | View configuration |
| `vibey submodule config --edit` | Edit configuration in $EDITOR |

## Push Modes

When pushing tasks to submodules, you can choose from three modes:

### Linked (Default)

Creates a task in BOTH the parent and submodule repositories. The task IDs are linked together for tracking.

```bash
vibey submodule push libs/core --title "Add feature" --mode linked
```

Use when:
- The submodule team should work on this independently
- You want to track progress from the parent

### Parent Only

Creates an external dependency reference in the parent only. No task is created in the submodule.

```bash
vibey submodule push libs/core --title "Needs API v2" --mode parent_only
```

Use when:
- You're waiting for existing submodule work to complete
- The submodule team manages their own roadmap

### Submodule Only

Creates a task only in the submodule. No reference in the parent.

```bash
vibey submodule push libs/core --title "Internal fix" --mode submodule_only
```

Use when:
- The task is internal to the submodule
- You don't need to track it from the parent

## Configuration

Configuration is stored in `.vibey/config/submodules.yaml`:

```yaml
submodules:
  - path: libs/core
    roadmap_id: core-v1
    aggregate: true
    track_filter: []  # Empty = include all tracks
    detection_source: gitmodules

default_push_mode: linked
aggregate_on_status: true
stale_threshold_minutes: 60
```

### Options

| Option | Description |
|--------|-------------|
| `path` | Relative path to submodule |
| `roadmap_id` | ID from submodule's roadmap.yaml |
| `aggregate` | Include in aggregated progress |
| `track_filter` | Only include specific tracks |
| `default_push_mode` | Default mode for push operations |
| `aggregate_on_status` | Auto-aggregate when checking status |
| `stale_threshold_minutes` | When to consider progress data stale |

## MCP Tools

For AI integration, Vibey provides 14 MCP tools for submodule operations:

### Discovery Tools
- `vibey_submodule_list` - List all submodules
- `vibey_submodule_discover` - Run discovery
- `vibey_submodule_roadmap` - Get submodule roadmap summary

### Push-down Tools
- `vibey_submodule_push_requirement` - Push task to submodule
- `vibey_submodule_requirements` - List requirements
- `vibey_submodule_accept_requirement` - Accept incoming requirement

### Pull-up Tools
- `vibey_submodule_status` - Get aggregated progress
- `vibey_submodule_blockers` - List blockers
- `vibey_submodule_refresh` - Force refresh

### Dependency Tools
- `vibey_task_add_cross_dep` - Add cross-repo dependency
- `vibey_task_cross_deps` - List dependencies
- `vibey_submodule_dep_graph` - Get dependency graph
- `vibey_submodule_validate_deps` - Validate dependencies

### Sync Tools
- `vibey_submodule_sync` - Trigger full sync

## Best Practices

### 1. Keep Submodules Independent

Design submodule roadmaps to be self-contained. They should make sense and be usable whether accessed directly or as part of a larger project.

### 2. Use Track Filters

If a submodule has many tracks, use `track_filter` to only aggregate relevant ones:

```yaml
submodules:
  - path: libs/core
    track_filter: ["api", "sdk"]  # Only these tracks
```

### 3. Regular Sync

Run `vibey submodule aggregate` regularly to keep progress data fresh and update blocked_by statuses.

### 4. Validate Dependencies

Before major releases, run `vibey submodule validate-deps` to check for:
- Circular dependencies
- Missing targets
- Stale references

## Troubleshooting

### Submodule Not Detected

```bash
# Check if submodule has .vibey/roadmap
ls <submodule_path>/.vibey/roadmap/

# Try different detection methods
vibey submodule discover
```

### Stale Progress Data

```bash
# Force refresh all submodules
vibey submodule aggregate

# Force refresh single submodule
vibey submodule refresh libs/core
```

### Dependency Validation Fails

```bash
# See detailed validation output
vibey submodule validate-deps

# Check specific ticket dependencies
vibey submodule deps <ticket_id> --direction both
```

## Architecture

```
Parent Repository
├── .vibey/
│   ├── config/
│   │   └── submodules.yaml    # Submodule registry
│   └── roadmap/
│       ├── tasks/             # Parent tasks (may link to submodule tasks)
│       └── ...
├── libs/
│   ├── core/                  # Git submodule
│   │   └── .vibey/roadmap/    # Independent roadmap
│   └── utils/                 # Git submodule
│       └── .vibey/roadmap/    # Independent roadmap
└── .gitmodules                # Git submodule definitions
```

Key points:
- Cross-repo data is stored ONLY in the parent's `.vibey/config/`
- Submodules contain their own independent roadmaps
- Parent aggregates progress by reading (not writing) submodule data
