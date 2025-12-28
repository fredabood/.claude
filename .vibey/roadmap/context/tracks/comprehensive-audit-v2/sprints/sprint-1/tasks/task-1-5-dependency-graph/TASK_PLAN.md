# Task 1.5: Update FILE_DEPENDENCY_GRAPH.yaml - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34433 |
| Sprint | Sprint 1: File Inventory Refresh |
| Type | documentation |
| Complexity | **complex** |
| Priority | medium |
| Estimated Tokens | 4,000 |
| Dependencies | Task 1.1 (file scan) |

## Objective

Update the import/dependency graph to reflect all new files and their relationships. This graph is critical for understanding module coupling and identifying architectural issues.

## Source File

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/FILE_DEPENDENCY_GRAPH.yaml
```

## Expected Graph Structure

```yaml
dependency_graph:
  nodes:
    - id: vibey/cli/main.py
      type: python
      module: vibey.cli.main
      imports: [...]
      imported_by: [...]

  edges:
    - from: vibey/cli/main.py
      to: vibey/cli/commands.py
      type: import

  metrics:
    total_nodes: 365
    total_edges: 1247
    avg_imports_per_file: 3.4
    max_imports: 15
    circular_dependencies: []
    orphaned_modules: []
```

## Implementation Steps

### Step 1: Extract All Imports from Python Files

```python
import ast
import os
from pathlib import Path

def extract_imports(filepath: str) -> dict:
    """Extract all imports from a Python file."""
    with open(filepath) as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return {"error": "syntax_error", "imports": []}

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "type": "import"
                })
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append({
                    "module": node.module,
                    "names": [a.name for a in node.names],
                    "type": "from_import",
                    "level": node.level  # relative import level
                })

    return {"imports": imports}

# Process all Python files
for py_file in Path("vibey").rglob("*.py"):
    result = extract_imports(str(py_file))
    # Store in graph structure
```

### Step 2: Resolve Import Paths to File Paths

```python
def resolve_import_to_file(import_module: str, source_file: str) -> str | None:
    """Convert import like 'vibey.cli.main' to 'vibey/cli/main.py'."""

    # Handle relative imports
    if import_module.startswith("."):
        # Resolve relative to source file location
        pass

    # Handle absolute imports
    parts = import_module.split(".")

    # Check if it's a vibey internal import
    if parts[0] == "vibey":
        potential_path = "/".join(parts) + ".py"
        if os.path.exists(potential_path):
            return potential_path

        # Check for package __init__.py
        potential_package = "/".join(parts) + "/__init__.py"
        if os.path.exists(potential_package):
            return potential_package

    # External dependency
    return None
```

### Step 3: Build Dependency Graph

```python
from collections import defaultdict

class DependencyGraph:
    def __init__(self):
        self.nodes = {}  # file -> metadata
        self.edges = []  # (from, to, type)
        self.imports = defaultdict(list)  # file -> [imported files]
        self.imported_by = defaultdict(list)  # file -> [importing files]

    def add_node(self, filepath: str, metadata: dict):
        self.nodes[filepath] = metadata

    def add_edge(self, from_file: str, to_file: str, import_type: str):
        self.edges.append({
            "from": from_file,
            "to": to_file,
            "type": import_type
        })
        self.imports[from_file].append(to_file)
        self.imported_by[to_file].append(from_file)

    def find_circular_dependencies(self) -> list:
        """Detect circular import chains."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.imports.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for node in self.nodes:
            if node not in visited:
                dfs(node, [])

        return cycles

    def find_orphaned_modules(self) -> list:
        """Find modules with no dependents (not imported by anyone)."""
        orphans = []
        for node in self.nodes:
            if not self.imported_by[node]:
                # Check if it's an entry point (main.py, __init__.py, etc.)
                if not self._is_entry_point(node):
                    orphans.append(node)
        return orphans

    def _is_entry_point(self, filepath: str) -> bool:
        """Check if file is a known entry point."""
        entry_patterns = [
            "__init__.py",
            "__main__.py",
            "main.py",
            "conftest.py",
            "setup.py",
        ]
        return any(filepath.endswith(p) for p in entry_patterns)

    def calculate_metrics(self) -> dict:
        """Calculate graph metrics."""
        import_counts = [len(self.imports[n]) for n in self.nodes]
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "avg_imports_per_file": sum(import_counts) / len(import_counts) if import_counts else 0,
            "max_imports": max(import_counts) if import_counts else 0,
            "min_imports": min(import_counts) if import_counts else 0,
        }
```

### Step 4: Generate Updated YAML

```python
import yaml

def export_graph(graph: DependencyGraph, output_path: str):
    """Export graph to YAML format."""

    data = {
        "dependency_graph": {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "source_commit": get_current_commit(),
                "python_files_analyzed": len(graph.nodes),
            },
            "metrics": graph.calculate_metrics(),
            "circular_dependencies": graph.find_circular_dependencies(),
            "orphaned_modules": graph.find_orphaned_modules(),
            "nodes": [
                {
                    "path": path,
                    "imports": graph.imports[path],
                    "imported_by": graph.imported_by[path],
                    "import_count": len(graph.imports[path]),
                    "dependent_count": len(graph.imported_by[path]),
                }
                for path in sorted(graph.nodes.keys())
            ],
            "edges": graph.edges,
        }
    }

    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

### Step 5: Analyze and Document Findings

Create `DEPENDENCY_ANALYSIS.md` with:

```markdown
# Dependency Analysis Report

## Summary
- Total files analyzed: X
- Total import relationships: Y
- Average imports per file: Z

## Circular Dependencies
[List any circular import chains found]

## Orphaned Modules
[List modules not imported by any other module]

## High Coupling Modules
[List modules with >10 dependents - potential refactoring candidates]

## Low Cohesion Areas
[Areas where unrelated modules import each other]

## Recommendations
1. [Specific refactoring recommendations]
2. [Dependency injection opportunities]
3. [Module consolidation suggestions]
```

## Validation Checklist

- [ ] All Python files in vibey/ have nodes in the graph
- [ ] All imports resolved to file paths where possible
- [ ] External dependencies clearly marked
- [ ] Circular dependencies detected and documented
- [ ] Orphaned modules identified
- [ ] Metrics calculated and recorded
- [ ] YAML validates without errors
- [ ] Graph is internally consistent (edges match node imports)

## Deliverables

1. **Updated FILE_DEPENDENCY_GRAPH.yaml**
   - Location: `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/`
   - Or new location in comprehensive-audit-v2 outputs

2. **DEPENDENCY_ANALYSIS.md**
   - Circular dependencies report
   - Orphaned modules list
   - Coupling metrics
   - Recommendations

3. **dependency_graph_visualization.png** (optional)
   - Visual representation using graphviz or similar

## Edge Cases

1. **Relative imports**
   ```python
   from . import sibling_module
   from .. import parent_module
   ```
   - Resolve relative to source file location

2. **Conditional imports**
   ```python
   if TYPE_CHECKING:
       from heavy_module import HeavyClass
   ```
   - Include in graph but mark as "type_checking_only"

3. **Dynamic imports**
   ```python
   module = importlib.import_module(module_name)
   ```
   - Cannot be statically analyzed; note in metadata

4. **Star imports**
   ```python
   from module import *
   ```
   - Flag as antipattern; list in analysis

## Estimated Time

- Import extraction: ~5 minutes (automated)
- Path resolution: ~10 minutes (automated with manual review)
- Graph building: ~5 minutes (automated)
- Circular dependency analysis: ~5 minutes
- Documentation: ~30 minutes
- **Total: ~1 hour**

## Tools

- Python `ast` module for parsing
- `networkx` for graph algorithms (optional)
- `graphviz` for visualization (optional)
- Custom scripts in `scripts/audit/`
