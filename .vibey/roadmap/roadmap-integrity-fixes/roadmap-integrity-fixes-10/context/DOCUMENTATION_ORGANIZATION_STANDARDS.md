# Documentation Organization Standards

**Sprint:** roadmap-integrity-fixes-10
**Task:** 002 - Define documentation organization standards
**Date:** 2025-11-22
**Status:** Complete

---

## Purpose

This document defines the standards for organizing documentation within the Vibey roadmap system. Following these standards ensures:

1. **Consistency** - Predictable file locations
2. **Discoverability** - Easy to find relevant documentation
3. **Maintainability** - Clear ownership and lifecycle
4. **Scalability** - Works as roadmap grows

---

## Directory Structure Standard

```
.vibey/roadmap/
├── roadmap.yaml              # Root roadmap state (machine-readable)
├── roadmap.md                # Root roadmap documentation (human-readable)
├── archived/                 # Historical archives (by date)
│   └── YYYY-MM-DD/
│
└── {track}/
    ├── track.yaml            # Track state
    ├── track.md              # Track documentation
    ├── context/              # Track-level context documents
    │   ├── audits/           # Audit reports
    │   ├── remediation/      # Fix/correction documentation
    │   ├── planning/         # Planning documents
    │   └── analysis/         # Analysis and reports
    │
    └── {sprint}/
        ├── sprint.yaml       # Sprint state
        ├── sprint.md         # Sprint documentation (optional)
        ├── context/          # Sprint-level context documents
        │
        └── {task}/
            ├── task.yaml     # Task state
            └── task.md       # Task documentation (optional)
```

---

## File Types

### Core Structure Files (Required)

| File | Level | Purpose | Format |
|------|-------|---------|--------|
| `roadmap.yaml` | Root | Roadmap configuration | YAML |
| `track.yaml` | Track | Track state & metadata | YAML |
| `sprint.yaml` | Sprint | Sprint state & progress | YAML |
| `task.yaml` | Task | Task state & details | YAML |

### Documentation Files (Optional)

| File | Level | Purpose | Format |
|------|-------|---------|--------|
| `roadmap.md` | Root | Roadmap overview | Markdown |
| `track.md` | Track | Track context & strategy | Markdown |
| `sprint.md` | Sprint | Sprint goals & learnings | Markdown |
| `task.md` | Task | Task details & notes | Markdown |

### Context Files (Variable)

All analysis, reports, and supplementary documentation goes in `context/` directories.

---

## Context Directory Categories

### Track-Level Context (`{track}/context/`)

| Category | Directory | Contents |
|----------|-----------|----------|
| Audits | `audits/` | Track audit reports, validation results |
| Remediation | `remediation/` | Fix documentation, corrections |
| Planning | `planning/` | Sprint plans, roadmaps |
| Analysis | `analysis/` | Gap analysis, forensic reports |
| Summaries | `summaries/` | Executive summaries, overviews |

### Sprint-Level Context (`{sprint}/context/`)

| Category | Directory | Contents |
|----------|-----------|----------|
| Completion | `completion/` | Task completion reports |
| Implementation | `implementation/` | Implementation details |
| Testing | `testing/` | Test results, verification |

---

## Naming Conventions

### File Names

```
CATEGORY_DESCRIPTION[_DATE].md
```

**Examples:**
- `AUDIT_REPORT_2025-11-15.md`
- `REMEDIATION_SUMMARY.md`
- `SPRINT_COMPLETION_2025-11-20.md`
- `GAP_ANALYSIS.md`

**Rules:**
1. Use UPPERCASE for category prefix
2. Use underscores between words
3. Include date suffix for time-sensitive documents (YYYY-MM-DD)
4. Use `.md` extension for all documentation
5. Use `.yaml` extension for state/config files

### Directory Names

```
lowercase-with-dashes/
```

**Examples:**
- `context/`
- `audits/`
- `gap-analysis/`
- `forensic-reports/`

---

## Document Templates

### Audit Report Template

```markdown
# [Track/Sprint] Audit Report

**Date:** YYYY-MM-DD
**Auditor:** [Agent/Human]
**Scope:** [What was audited]

## Summary
[Brief findings]

## Findings
[Detailed findings]

## Recommendations
[Action items]

## Appendix
[Supporting data]
```

### Completion Report Template

```markdown
# [Task/Sprint] Completion Report

**Date:** YYYY-MM-DD
**Status:** Complete

## Summary
[What was completed]

## Deliverables
- [List of deliverables]

## Commits
- [Associated commits]

## Notes
[Additional context]
```

### Remediation Report Template

```markdown
# Remediation Report

**Date:** YYYY-MM-DD
**Issue:** [What was fixed]
**Resolution:** [How it was fixed]

## Changes Made
[List of changes]

## Verification
[How fix was verified]
```

---

## Lifecycle Rules

### Creation

1. Core files (`*.yaml`) created when entity is initialized
2. Documentation files (`*.md`) created when context is needed
3. Context files created during work, never during planning

### Updates

1. `*.yaml` files updated automatically by tooling
2. `*.md` files updated manually during work
3. Context files append-only (create new, don't modify old)

### Archival

1. Superseded tracks: Move to `archived/{date}/`
2. Incorrect reports: Move to `archived/corrections/{date}/`
3. Preserve file structure in archives

### Deletion

1. **Never delete** core structure files without migration
2. **Never delete** context files - archive instead
3. Test files may be deleted after validation

---

## Validation Rules

### Required Structure

```
✓ Every track has track.yaml
✓ Every sprint has sprint.yaml
✓ Every task has task.yaml
✓ Context files are in context/ directories
✓ No loose files at track/sprint level (except *.yaml, *.md)
```

### File Placement Rules

| If file is... | It belongs in... |
|---------------|------------------|
| Track state/config | `{track}/track.yaml` |
| Track documentation | `{track}/track.md` |
| Track analysis | `{track}/context/{category}/` |
| Sprint state | `{sprint}/sprint.yaml` |
| Sprint documentation | `{sprint}/sprint.md` |
| Sprint analysis | `{sprint}/context/` |
| Task state | `{task}/task.yaml` |
| Task documentation | `{task}/task.md` |

### Naming Validation

```
✓ YAML files: lowercase with hyphens
✓ MD files: UPPERCASE_WITH_UNDERSCORES
✓ Directories: lowercase-with-dashes
✓ Dates in format: YYYY-MM-DD
```

---

## Migration Guide

### Moving Existing Files

**From:** `{track}/AUDIT_REPORT_*.md`
**To:** `{track}/context/audits/AUDIT_REPORT_*.md`

**From:** `{track}/REMEDIATION_*.md`
**To:** `{track}/context/remediation/REMEDIATION_*.md`

**From:** `{sprint}/TASK_*_COMPLETE.md`
**To:** `{sprint}/context/completion/TASK_*_COMPLETE.md`

### Updating References

After migration, update any cross-references in:
1. Track notes (in `track.yaml`)
2. Sprint documentation
3. Task documentation

---

## Enforcement

### Automated Checks

The following should be validated by CI/pre-commit hooks:

1. No loose `.md` files at track level (except `track.md`)
2. No loose `.md` files at sprint level (except `sprint.md`)
3. All context files are in `context/` directories
4. File naming follows conventions

### Manual Reviews

During sprint reviews, verify:

1. New context files are properly categorized
2. Documentation is up-to-date
3. Archives are properly organized

---

## Examples

### Good Structure

```
.vibey/roadmap/roadmap-integrity-fixes/
├── track.yaml
├── track.md
├── context/
│   ├── audits/
│   │   ├── TRACK_AUDIT_REPORT_2025-11-15.md
│   │   └── TRACK_AUDIT_REPORT_2025-11-16.md
│   ├── forensic-agents/
│   │   ├── FORENSIC_AGENT_1_TIMELINE.md
│   │   └── CONSOLIDATED_5_AGENT_REPORT.md
│   └── qa-reports/
│       └── QA_AGENT_1_TRACK_VALIDATION.md
└── roadmap-integrity-fixes-10/
    ├── sprint.yaml
    ├── sprint.md
    └── context/
        └── DOCUMENTATION_AUDIT_REPORT.md
```

### Bad Structure (Before Migration)

```
.vibey/roadmap/roadmap-integrity-fixes/
├── track.yaml
├── track.md
├── TRACK_AUDIT_REPORT_2025-11-15.md      ← Should be in context/audits/
├── FORENSIC_AGENT_1_TIMELINE.md          ← Should be in context/forensic-agents/
├── QA_AGENT_1_TRACK_VALIDATION.md        ← Should be in context/qa-reports/
└── roadmap-integrity-fixes-10/
    ├── sprint.yaml
    └── TASK_001_COMPLETE.md              ← Should be in context/completion/
```

---

## Summary

| Rule | Enforcement |
|------|-------------|
| Core files at entity level | Required |
| Analysis in `context/` | Required |
| Subdirectories by category | Recommended |
| Naming conventions | Required |
| Date suffixes for time-sensitive | Recommended |
| Archive don't delete | Required |

---

**Standards Document Complete**

Generated by: Sprint 10 Task 002
