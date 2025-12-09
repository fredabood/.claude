# Source of Truth Reference

## Git Tag

**Tag:** `source-of-truth-sprint4`
**Commit:** `ef7270a`
**Date:** 2025-11-27

## Purpose

This tag marks the commit that serves as the source of truth for Sprint 4 (Data Validation & Integrity Audit) work. All validation and comparison should reference this state.

## What This Commit Contains

### YAML Remediation
- 862 task files merged
- 172 sprint files merged
- 36 track files merged

### Merge Strategy
- **Status fields** (status, blocked, started, completed, progress) taken from session backup
- **Content fields** (description, assigned_agent, notes, title, name) taken from git HEAD

### Code Fixes
- Changed Status enum WONT_DO value from `"won't_do"` to `"wont_do"` to match database schema
- Updated all references in CLI commands and validator

## Initial Audit Findings

The db dump command caused 98% data loss during SQLite round-trip:

| Field | Tasks Affected |
|-------|----------------|
| started | 615 |
| description | 288 |
| completed (precision) | 269 |
| complexity | 224 |
| assigned_agent | 222 |
| commits | 114 |
| deliverables | 108 |

## How to Access

```bash
# View the tagged commit
git show source-of-truth-sprint4

# Checkout the source of truth state
git checkout source-of-truth-sprint4

# Compare current state to source of truth
git diff source-of-truth-sprint4
```

## Backup Location

A filesystem backup was also created at:
- **Path:** `/tmp/yaml_original/roadmap`
- **Created:** 2025-11-27T21:13:59+00:00
- **Files:** 1,097 YAML files

Note: This backup contains status updates but has data loss from earlier db operations. The git tag is the authoritative source of truth.
