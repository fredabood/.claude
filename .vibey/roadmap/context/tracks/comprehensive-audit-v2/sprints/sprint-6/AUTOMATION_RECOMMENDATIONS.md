# Audit Automation Recommendations

## Overview

This document provides recommendations for automating audit maintenance to reduce manual effort and ensure ongoing accuracy. Recommendations are categorized by automation feasibility.

**Date**: 2025-12-29
**Track**: Comprehensive Repository Audit V2
**Sprint**: Sprint 6 - Friction & Progress Tracking

---

## Automation Categories

### Fully Automatable (No Manual Review Required)

These outputs can be completely auto-generated with high confidence:

| Output | Current Manual Effort | Automation Approach | Priority |
|--------|----------------------|---------------------|----------|
| File counts | Low | `find` + Python script | High |
| File inventory | Medium | Git + Python scan | High |
| Dependency graph | Medium | AST analysis | Medium |
| Dead code detection | High | Static analysis tools | Medium |
| Test coverage metrics | Low | pytest-cov integration | High |
| CLI command list | Low | Click introspection | High |
| MCP tool list | Low | MCP introspection | High |

### Semi-Automatable (Requires Manual Review)

These outputs can be auto-generated but need human verification:

| Output | Auto-Generate | Review Required | Priority |
|--------|---------------|-----------------|----------|
| File classifications | Category guessing from path/content | Verify accuracy | Medium |
| Quality metrics | Aggregate from tools | Interpret meaning | Low |
| Documentation accuracy | Link checking | Content verification | Medium |
| Architecture diagrams | Generate from code | Validate completeness | Low |

### Manual Only

These outputs require human judgment and cannot be automated:

| Output | Reason | Mitigation |
|--------|--------|------------|
| Friction analysis | Subjective experience | Structured templates |
| Remediation priorities | Business context | Scoring rubrics |
| Strategic recommendations | Domain knowledge | Decision frameworks |

---

## Proposed CI/CD Integration

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml additions
repos:
  - repo: local
    hooks:
      - id: roadmap-validate
        name: Validate Roadmap YAML
        entry: vibey roadmap validate-fast
        language: system
        files: \.vibey/roadmap/.*\.yaml$

      - id: check-doc-drift
        name: Check Documentation Drift
        entry: vibey docs check-drift
        language: system
        files: (docs/|vibey/).*\.(py|md)$
```

### GitHub Actions Workflow

```yaml
# .github/workflows/audit-checks.yml
name: Audit Integrity Checks

on:
  push:
    paths:
      - '.vibey/roadmap/**'
      - 'vibey/**'
      - 'docs/**'

jobs:
  audit-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install vibey
        run: pip install -e .

      - name: Validate Roadmap Structure
        run: vibey roadmap validate-structure

      - name: Check File Inventory Drift
        run: |
          python scripts/check_file_inventory.py

      - name: Verify Progress Counters
        run: vibey roadmap validate-progress

      - name: Check Documentation Accuracy
        run: vibey docs check-drift --fail-on-drift
```

### Scheduled Audits

```yaml
# .github/workflows/scheduled-audit.yml
name: Weekly Audit Refresh

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  refresh-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Regenerate File Inventory
        run: python scripts/generate_file_inventory.py

      - name: Regenerate Dependency Graph
        run: python scripts/generate_dependency_graph.py

      - name: Update Quality Metrics
        run: python scripts/update_quality_metrics.py

      - name: Create PR if Changes
        run: |
          if [[ -n $(git status --porcelain) ]]; then
            git checkout -b audit-refresh-$(date +%Y%m%d)
            git add .
            git commit -m "chore: Weekly audit refresh"
            gh pr create --title "Weekly Audit Refresh" --body "Automated audit data refresh"
          fi
```

---

## Recommended Automation Scripts

### 1. File Inventory Generator

**Location**: `scripts/generate_file_inventory.py`

```python
#!/usr/bin/env python3
"""Generate FILE_INVENTORY.yaml from current repository state."""

import yaml
from pathlib import Path
from datetime import datetime

def scan_repository():
    """Scan repository and generate inventory."""
    inventory = {
        'generated': datetime.utcnow().isoformat(),
        'files': {}
    }

    for path in Path('.').rglob('*'):
        if path.is_file() and not should_ignore(path):
            inventory['files'][str(path)] = {
                'size': path.stat().st_size,
                'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }

    return inventory

def should_ignore(path):
    """Check if path should be ignored."""
    ignore_patterns = ['.git', '__pycache__', '.venv', 'node_modules']
    return any(p in path.parts for p in ignore_patterns)

if __name__ == '__main__':
    inventory = scan_repository()
    with open('.vibey/roadmap/context/FILE_INVENTORY.yaml', 'w') as f:
        yaml.dump(inventory, f, default_flow_style=False)
```

### 2. Progress Counter Validator

**Location**: `scripts/validate_progress.py`

```python
#!/usr/bin/env python3
"""Validate progress counters match actual task states."""

import yaml
from pathlib import Path
from collections import Counter
import sys

def validate_track_progress(track_id):
    """Validate track progress counters."""
    # Read track file
    track_file = Path(f'.vibey/roadmap/tracks/{track_id}.yaml')
    with open(track_file) as f:
        track = yaml.safe_load(f).get('track', {})

    # Count actual task states
    tasks_dir = Path('.vibey/roadmap/tasks')
    status_counts = Counter()

    for task_file in tasks_dir.glob('*.yaml'):
        with open(task_file) as f:
            task = yaml.safe_load(f).get('task', {})
            if task.get('track_id') == track_id:
                status_counts[task.get('status')] += 1

    # Compare
    yaml_completed = track.get('progress', {}).get('tasks_completed', 0)
    actual_completed = status_counts.get('completed', 0)

    if yaml_completed != actual_completed:
        print(f"MISMATCH: YAML={yaml_completed}, Actual={actual_completed}")
        return False
    return True

if __name__ == '__main__':
    if not validate_track_progress(sys.argv[1]):
        sys.exit(1)
```

### 3. Documentation Drift Checker

**Location**: `scripts/check_doc_drift.py`

```python
#!/usr/bin/env python3
"""Check for documentation drift from code reality."""

import subprocess
import re
from pathlib import Path

def get_cli_commands():
    """Get actual CLI commands from code."""
    result = subprocess.run(
        ['python', '-m', 'vibey', '--help'],
        capture_output=True, text=True
    )
    # Parse commands from help output
    return set(re.findall(r'^\s+(\w+)\s', result.stdout, re.MULTILINE))

def get_documented_commands():
    """Get commands documented in CLI reference."""
    ref_file = Path('docs/reference/CLI_REFERENCE.md')
    content = ref_file.read_text()
    return set(re.findall(r'^## `vibey (\w+)`', content, re.MULTILINE))

def check_drift():
    """Check for undocumented or obsolete commands."""
    actual = get_cli_commands()
    documented = get_documented_commands()

    undocumented = actual - documented
    obsolete = documented - actual

    if undocumented:
        print(f"Undocumented commands: {undocumented}")
    if obsolete:
        print(f"Obsolete in docs: {obsolete}")

    return len(undocumented) + len(obsolete) == 0

if __name__ == '__main__':
    import sys
    sys.exit(0 if check_drift() else 1)
```

---

## Implementation Priority

### Phase 1: High-Impact Quick Wins

1. **Add pre-commit hook for YAML validation** (1 hour)
2. **Create file inventory generator script** (2 hours)
3. **Add GitHub Action for PR validation** (2 hours)

### Phase 2: Core Automation

1. **Implement progress counter validator** (4 hours)
2. **Create documentation drift checker** (4 hours)
3. **Set up scheduled audit workflow** (2 hours)

### Phase 3: Advanced Features

1. **Integrate static analysis tools** (8 hours)
2. **Build dependency graph generator** (8 hours)
3. **Create quality metrics dashboard** (16 hours)

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Manual audit hours/month | ~8 | <2 | Time tracking |
| Drift detection latency | Days | Minutes | PR check timing |
| Audit accuracy | Manual verification | 95%+ automated | Validation passes |
| False positive rate | N/A | <5% | Manual overrides |

---

## Dependencies

- Python 3.9+
- PyYAML
- Click (for CLI introspection)
- pytest-cov (for test coverage)
- AST module (built-in, for code analysis)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Automation breaks on edge cases | Medium | Comprehensive test suite |
| False positives cause noise | Low | Tunable thresholds |
| Maintenance burden | Medium | Clear documentation |
| Security concerns in CI | Low | Minimal permissions, audit logs |

---

## Conclusion

Approximately 60% of audit maintenance can be fully automated, with another 25% being semi-automatable with human review. The remaining 15% requires human judgment.

**Recommended First Step**: Implement the pre-commit hook for YAML validation and the file inventory generator to establish the automation foundation.
