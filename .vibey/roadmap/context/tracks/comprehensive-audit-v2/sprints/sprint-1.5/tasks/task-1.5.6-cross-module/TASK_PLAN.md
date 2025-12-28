# Task 1.5.6: Generate Cross-Module Dependency Analysis - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QT9 |
| Sprint | Sprint 1.5: Module Quality Re-Audit |
| Type | research |
| Complexity | **complex** |
| Priority | medium |
| Estimated Tokens | 3,000 |
| Dependencies | Tasks 1.5.1-1.5.5 (module audits) |

## Objective

Generate an updated cross-module dependency analysis showing how the 7 primary modules depend on each other. Create a coupling matrix, identify circular dependencies, and compare with the original Dec 12 analysis if available.

## Module Definitions

| Module | Path | Primary Responsibility |
|--------|------|------------------------|
| CLI | `vibey/cli/` | Command-line interface |
| Operations | `vibey/operations/` | Business logic layer |
| Roadmap | `vibey/roadmap/` | Data models, persistence |
| MCP | `vibey/mcp/` | Model Context Protocol |
| Adapters | `vibey/adapters/` | Platform integrations |
| Common | `vibey/common/` | Shared utilities |
| Services | `vibey/services/` | Service implementations |

## Analysis Process

### Step 1: Extract Inter-Module Imports

```python
import ast
from pathlib import Path
from collections import defaultdict

MODULES = {
    'cli': 'vibey/cli',
    'operations': 'vibey/operations',
    'roadmap': 'vibey/roadmap',
    'mcp': 'vibey/mcp',
    'adapters': 'vibey/adapters',
    'common': 'vibey/common',
    'services': 'vibey/services',
}

def get_module_for_import(import_name: str) -> str | None:
    """Determine which module an import belongs to."""
    if not import_name.startswith('vibey.'):
        return None  # External import

    parts = import_name.split('.')
    if len(parts) < 2:
        return None

    module_name = parts[1]
    return module_name if module_name in MODULES else None

def analyze_file_imports(filepath: Path) -> dict:
    """Extract imports from a Python file."""
    with open(filepath) as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return {}

    imports = defaultdict(int)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = get_module_for_import(alias.name)
                if module:
                    imports[module] += 1
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = get_module_for_import(node.module)
                if module:
                    imports[module] += 1

    return dict(imports)

def analyze_module(module_path: str) -> dict:
    """Analyze all imports for a module."""
    all_imports = defaultdict(int)

    for py_file in Path(module_path).rglob('*.py'):
        file_imports = analyze_file_imports(py_file)
        for module, count in file_imports.items():
            all_imports[module] += count

    return dict(all_imports)

# Build coupling matrix
coupling = {}
for module_name, module_path in MODULES.items():
    coupling[module_name] = analyze_module(module_path)
```

### Step 2: Build Coupling Matrix

```python
import pandas as pd

def build_coupling_matrix(coupling: dict) -> pd.DataFrame:
    """Create coupling matrix DataFrame."""
    modules = list(MODULES.keys())
    matrix = pd.DataFrame(0, index=modules, columns=modules)

    for source, targets in coupling.items():
        for target, count in targets.items():
            if target in modules:
                matrix.loc[source, target] = count

    return matrix

# Generate matrix
matrix = build_coupling_matrix(coupling)
print(matrix)
```

### Step 3: Classify Coupling Levels

```python
def classify_coupling(count: int) -> str:
    """Classify coupling level."""
    if count == 0:
        return '-'
    elif count < 5:
        return 'L'  # Low
    elif count < 15:
        return 'M'  # Medium
    else:
        return 'H'  # High

# Apply classification
classified = matrix.applymap(classify_coupling)
print(classified)
```

### Step 4: Detect Circular Dependencies

```python
def find_circular_dependencies(coupling: dict) -> list:
    """Find circular dependency chains between modules."""
    cycles = []

    for source in coupling:
        for target in coupling.get(source, {}):
            if source in coupling.get(target, {}):
                cycle = (source, target)
                if cycle not in cycles and (target, source) not in cycles:
                    cycles.append(cycle)

    return cycles

circles = find_circular_dependencies(coupling)
print(f"Circular dependencies: {circles}")
```

### Step 5: Identify Layering Violations

Expected layering (top to bottom):
```
CLI → Operations → Roadmap → Common
           ↓
         Services
           ↓
          MCP → Adapters
```

Violations to check:
- Common importing anything except stdlib
- Roadmap importing CLI or MCP
- Operations importing CLI
- Adapters importing Operations directly

```python
LAYER_RULES = {
    'common': [],  # Should not import other vibey modules
    'roadmap': ['common'],  # Only common
    'operations': ['roadmap', 'common'],  # roadmap and common
    'services': ['operations', 'roadmap', 'common'],
    'mcp': ['operations', 'roadmap', 'common', 'services'],
    'adapters': ['common'],  # Only common ideally
    'cli': ['operations', 'roadmap', 'common', 'mcp', 'services'],
}

def find_layering_violations(coupling: dict) -> list:
    """Find imports that violate layering rules."""
    violations = []

    for source, targets in coupling.items():
        allowed = LAYER_RULES.get(source, [])
        for target in targets:
            if target != source and target not in allowed:
                violations.append({
                    'source': source,
                    'target': target,
                    'count': targets[target],
                    'severity': 'high' if targets[target] > 5 else 'medium'
                })

    return violations
```

### Step 6: Calculate Metrics

```python
def calculate_metrics(matrix: pd.DataFrame) -> dict:
    """Calculate coupling metrics."""
    return {
        'total_connections': int(matrix.sum().sum()),
        'avg_outgoing': float(matrix.sum(axis=1).mean()),
        'avg_incoming': float(matrix.sum(axis=0).mean()),
        'most_depended_on': matrix.sum(axis=0).idxmax(),
        'most_dependent': matrix.sum(axis=1).idxmax(),
        'isolated_modules': list(matrix.index[matrix.sum(axis=1) == 0]),
    }
```

## Output Format

### CROSS_MODULE_DEPENDENCY_ANALYSIS.md

```markdown
# Cross-Module Dependency Analysis
**Generated:** December 28, 2024
**Baseline:** December 12, 2024

## Executive Summary

The vibey package consists of 7 primary modules with [X] total
inter-module import relationships...

## Coupling Matrix

### Import Counts
|           | cli | operations | roadmap | mcp | adapters | common | services |
|-----------|-----|------------|---------|-----|----------|--------|----------|
| cli       | -   | 45         | 32      | 5   | 2        | 18     | 8        |
| operations| 0   | -          | 67      | 3   | 0        | 42     | 12       |
| roadmap   | 0   | 5          | -       | 0   | 0        | 38     | 0        |
| mcp       | 2   | 28         | 15      | -   | 0        | 12     | 3        |
| adapters  | 0   | 0          | 0       | 0   | -        | 8      | 0        |
| common    | 0   | 0          | 0       | 0   | 0        | -      | 0        |
| services  | 3   | 22         | 18      | 0   | 0        | 15     | -        |

### Coupling Levels (L=Low<5, M=Medium<15, H=High≥15)
|           | cli | operations | roadmap | mcp | adapters | common | services |
|-----------|-----|------------|---------|-----|----------|--------|----------|
| cli       | -   | H          | H       | L   | L        | H      | M        |
| operations| -   | -          | H       | L   | -        | H      | M        |
| roadmap   | -   | L          | -       | -   | -        | H      | -        |
| mcp       | L   | H          | M       | -   | -        | M      | L        |
| adapters  | -   | -          | -       | -   | -        | M      | -        |
| common    | -   | -          | -       | -   | -        | -      | -        |
| services  | L   | H          | H       | -   | -        | M      | -        |

## Dependency Graph

```
                    ┌─────────────┐
                    │     CLI     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Operations│ │ Services │ │   MCP    │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┼────────────┘
                          ▼
                    ┌──────────┐
                    │ Roadmap  │
                    └────┬─────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
              ┌──────────┐ ┌──────────┐
              │ Adapters │ │  Common  │
              └──────────┘ └──────────┘
```

## Circular Dependencies

| Modules | Import Count A→B | Import Count B→A | Severity |
|---------|------------------|------------------|----------|
| operations ↔ services | 12 | 22 | Medium |
| [Others if any] |

## Layering Violations

| Source | Target | Count | Expected | Severity |
|--------|--------|-------|----------|----------|
| mcp | cli | 2 | No | Medium |
| [Others] |

## Metrics

| Metric | Value |
|--------|-------|
| Total inter-module connections | X |
| Average outgoing imports | Y |
| Average incoming imports | Z |
| Most depended-on module | common |
| Most dependent module | cli |
| Isolated modules | None |

## Comparison with Dec 12 Baseline

| Metric | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| Total connections | X | Y | +Z |
| Circular dependencies | 1 | 2 | +1 |
| Layering violations | 3 | 4 | +1 |

## Recommendations

### High Priority
1. Reduce cli → operations coupling (currently 45 imports)
2. Address circular dependency between operations and services

### Medium Priority
1. Extract shared utilities from operations to common
2. Consider facade pattern for mcp → operations

### Architecture Improvements
1. Introduce interface layer between CLI and Operations
2. Consider dependency injection for service layer
```

## Deliverables

1. **CROSS_MODULE_DEPENDENCY_ANALYSIS.md**
   - Full analysis report

2. **coupling_matrix.csv**
   - Raw coupling data

3. **dependency_graph.png** (optional)
   - Visual representation

## Estimated Time

- Import extraction: 15 minutes (scripted)
- Matrix generation: 10 minutes
- Violation detection: 10 minutes
- Report generation: 30 minutes
- Comparison with baseline: 15 minutes
- **Total: ~1.5 hours**
