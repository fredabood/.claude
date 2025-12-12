"""File classification tooling for codebase auditing.

This module provides automated classification of files based on the
taxonomy defined in CLASSIFICATION_TAXONOMY.md.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# Subcategory mapping for vibey/ directory
VIBEY_SUBCATEGORY_MAP = {
    "vibey/roadmap/models": ("1.1", "models"),
    "vibey/operations": ("1.2", "operations"),
    "vibey/roadmap/serialization": ("1.3", "serialization"),
    "vibey/cli": ("1.4", "cli"),
    "vibey/mcp": ("1.5", "mcp"),
    "vibey/adapters": ("1.6", "adapters"),
    "vibey/common": ("1.7", "common"),
    "vibey/config": ("1.8", "config"),
    "vibey/operations/config": ("1.8", "config"),
    "vibey/content": ("1.9", "content"),
    "vibey/operations/content": ("1.9", "content"),
    "vibey/platform": ("1.10", "platform"),
    "vibey/operations/audit": ("1.12", "audit"),
}

# Subcategory mapping for docs/ directory
DOCS_SUBCATEGORY_MAP = {
    "docs/getting-started": ("2.1", "getting-started"),
    "docs/guides": ("2.2", "guides"),
    "docs/reference": ("2.3", "reference"),
    "docs/development": ("2.4", "development"),
    "docs/examples": ("2.5", "examples"),
    "docs/sprints": ("2.6", "sprints"),
    "docs/validation": ("2.7", "validation"),
    "docs/testing": ("2.8", "testing"),
    "docs/roadmap": ("2.9", "roadmap"),
}

# Subcategory mapping for tests/ directory
TESTS_SUBCATEGORY_MAP = {
    "tests/roadmap": ("3.1", "roadmap"),
    "tests/roadmap/serialization": ("3.1.1", "serialization"),
    "tests/roadmap/models": ("3.1.2", "models"),
    "tests/operations": ("3.2", "operations"),
    "tests/operations/roadmap": ("3.2.1", "roadmap-ops"),
    "tests/operations/config": ("3.2.2", "config-ops"),
    "tests/operations/git": ("3.2.3", "git-ops"),
    "tests/cli": ("3.3", "cli"),
    "tests/mcp": ("3.4", "mcp"),
    "tests/adapters": ("3.5", "adapters"),
    "tests/common": ("3.6", "common"),
    "tests/config": ("3.7", "config"),
    "tests/fixtures": ("3.8", "fixtures"),
    "tests/integration": ("3.9", "integration"),
}

# Root files in vibey/
VIBEY_ROOT_FILES = {"__init__.py", "__main__.py", "py.typed"}


@dataclass
class FileClassification:
    """Classification result for a single file."""

    path: str
    category: str
    subcategory_id: str
    subcategory_name: str
    purpose: str
    module: str | None = None
    exports: list[str] = field(default_factory=list)
    dependencies_internal: list[str] = field(default_factory=list)
    dependencies_external: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    test_coverage: bool = False
    test_files: list[str] = field(default_factory=list)
    doc_coverage: bool = False
    doc_files: list[str] = field(default_factory=list)
    size_bytes: int = 0
    lines: int | None = None
    last_modified: str = ""


def _get_vibey_subcategory(path: str) -> tuple[str, str]:
    """Determine subcategory for a vibey/ file based on path."""
    # Check for root files
    filename = os.path.basename(path)
    if filename in VIBEY_ROOT_FILES and path.count("/") == 1:
        return ("1.11", "root")

    # Check path prefixes (most specific first)
    sorted_prefixes = sorted(VIBEY_SUBCATEGORY_MAP.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if path.startswith(prefix):
            return VIBEY_SUBCATEGORY_MAP[prefix]

    # Default based on directory
    parts = path.split("/")
    if len(parts) >= 2:
        subdir = parts[1]
        # Check if it matches any known subdirectory
        for prefix, (sub_id, sub_name) in VIBEY_SUBCATEGORY_MAP.items():
            if f"vibey/{subdir}" == prefix:
                return (sub_id, sub_name)

    return ("1.11", "root")


def _extract_python_imports(file_path: Path) -> tuple[list[str], list[str]]:
    """Extract import statements from a Python file.

    Returns:
        Tuple of (internal_imports, external_imports)
    """
    internal = []
    external = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return internal, external

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name == "vibey" or alias.name.startswith("vibey."):
                    internal.append(alias.name)
                else:
                    external.append(name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                name = node.module.split(".")[0]
                if name == "vibey" or node.module.startswith("vibey."):
                    internal.append(node.module)
                else:
                    external.append(name)

    return sorted(set(internal)), sorted(set(external))


def _extract_python_exports(file_path: Path) -> list[str]:
    """Extract exported names from a Python file (classes, functions, __all__)."""
    exports = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return exports

    # Check for __all__
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                exports.append(elt.value)
                    return exports

    # No __all__, get top-level classes and functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                exports.append(node.name)

    return exports


def _get_purpose_from_docstring(file_path: Path) -> str:
    """Extract module docstring as purpose description."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return ""

    docstring = ast.get_docstring(tree)
    if docstring:
        # Get first sentence/line
        first_line = docstring.split("\n")[0].strip()
        if first_line:
            # Truncate if too long
            if len(first_line) > 150:
                first_line = first_line[:147] + "..."
            return first_line

    return ""


def _count_lines(file_path: Path) -> int | None:
    """Count lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except (UnicodeDecodeError, OSError):
        return None


def _find_test_files(source_path: str, tests_dir: Path) -> list[str]:
    """Find test files that might cover a source file."""
    test_files = []

    # Convert source path to expected test path patterns
    # e.g., vibey/cli/main.py -> tests/cli/test_main.py
    parts = source_path.split("/")
    if len(parts) >= 2:
        subpath = "/".join(parts[1:])  # Remove 'vibey/'
        base_name = os.path.splitext(os.path.basename(subpath))[0]

        # Check various test file patterns
        patterns = [
            f"tests/{os.path.dirname(subpath)}/test_{base_name}.py",
            f"tests/test_{base_name}.py",
            f"tests/{parts[1]}/test_{base_name}.py",
        ]

        for pattern in patterns:
            test_path = tests_dir.parent / pattern
            if test_path.exists():
                test_files.append(pattern)

    return test_files


def classify_vibey_files(
    root_path: Path,
    include_dependencies: bool = True,
) -> dict[str, Any]:
    """Classify all files in the vibey/ directory.

    Args:
        root_path: Repository root path
        include_dependencies: Whether to extract import dependencies

    Returns:
        Classification dictionary in the expected YAML format
    """
    vibey_dir = root_path / "vibey"
    tests_dir = root_path / "tests"

    if not vibey_dir.exists():
        raise ValueError(f"vibey/ directory not found at {vibey_dir}")

    classifications: list[FileClassification] = []
    subcategory_counts: dict[str, int] = {}

    # Scan all Python files
    for py_file in vibey_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(root_path))

        # Skip __pycache__
        if "__pycache__" in rel_path:
            continue

        # Get subcategory
        sub_id, sub_name = _get_vibey_subcategory(rel_path)
        subcategory_counts[sub_name] = subcategory_counts.get(sub_name, 0) + 1

        # Get module path
        module = rel_path.replace("/", ".").replace(".py", "")
        if module.endswith(".__init__"):
            module = module[:-9]

        # Extract metadata
        purpose = _get_purpose_from_docstring(py_file)
        exports = _extract_python_exports(py_file)

        internal_deps, external_deps = [], []
        if include_dependencies:
            internal_deps, external_deps = _extract_python_imports(py_file)

        # Check test coverage
        test_files = _find_test_files(rel_path, tests_dir)

        # Get file stats
        stat = py_file.stat()
        size_bytes = stat.st_size
        lines = _count_lines(py_file)
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        classification = FileClassification(
            path=rel_path,
            category="core-lib",
            subcategory_id=sub_id,
            subcategory_name=sub_name,
            purpose=purpose or f"Part of {module} module",
            module=module,
            exports=exports,
            dependencies_internal=internal_deps,
            dependencies_external=external_deps,
            test_coverage=bool(test_files),
            test_files=test_files,
            doc_coverage=bool(purpose),  # Has docstring
            size_bytes=size_bytes,
            lines=lines,
            last_modified=mtime,
        )
        classifications.append(classification)

    # Sort by path
    classifications.sort(key=lambda c: c.path)

    # Build output structure
    output = {
        "classification": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "taxonomy_version": "1.0",
            "directory": "vibey/",
            "summary": {
                "total_files": len(classifications),
                "by_subcategory": dict(sorted(subcategory_counts.items())),
            },
            "files": [
                {
                    "path": c.path,
                    "category": c.category,
                    "subcategory": c.subcategory_name,
                    "subcategory_id": c.subcategory_id,
                    "purpose": c.purpose,
                    "module": c.module,
                    "exports": c.exports,
                    "dependencies": {
                        "internal": c.dependencies_internal,
                        "external": c.dependencies_external,
                    },
                    "test_coverage": {
                        "has_tests": c.test_coverage,
                        "test_files": c.test_files,
                    },
                    "doc_coverage": c.doc_coverage,
                    "size_bytes": c.size_bytes,
                    "lines": c.lines,
                    "last_modified": c.last_modified,
                }
                for c in classifications
            ],
        }
    }

    return output


def _get_docs_subcategory(path: str) -> tuple[str, str]:
    """Determine subcategory for a docs/ file based on path."""
    # Check path prefixes (most specific first)
    sorted_prefixes = sorted(DOCS_SUBCATEGORY_MAP.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if path.startswith(prefix):
            return DOCS_SUBCATEGORY_MAP[prefix]

    # Root docs/ files
    return ("2.10", "root")


def _get_doc_purpose_from_content(file_path: Path) -> str:
    """Extract purpose from markdown file's first heading or paragraph."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(2000)  # Read first 2000 chars
    except (UnicodeDecodeError, OSError):
        return ""

    lines = content.split("\n")

    # Look for first heading
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("## "):
            return line[3:].strip()

    # Fall back to first non-empty line
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
            if len(stripped) > 150:
                stripped = stripped[:147] + "..."
            return stripped

    return ""


def _extract_doc_references(file_path: Path) -> list[str]:
    """Extract references to other docs from markdown file."""
    references = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError):
        return references

    # Find markdown links to other docs
    # Patterns: [text](path.md), [text](../path.md), [text](docs/path.md)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)')
    for match in link_pattern.finditer(content):
        ref_path = match.group(2)
        # Normalize relative paths
        if not ref_path.startswith("http"):
            references.append(ref_path)

    return sorted(set(references))


def classify_docs_files(
    root_path: Path,
    include_references: bool = True,
) -> dict[str, Any]:
    """Classify all files in the docs/ directory.

    Args:
        root_path: Repository root path
        include_references: Whether to extract doc references

    Returns:
        Classification dictionary in the expected YAML format
    """
    docs_dir = root_path / "docs"

    if not docs_dir.exists():
        raise ValueError(f"docs/ directory not found at {docs_dir}")

    classifications: list[dict[str, Any]] = []
    subcategory_counts: dict[str, int] = {}
    doc_types: dict[str, int] = {}

    # Scan all markdown and yaml files
    for doc_file in docs_dir.rglob("*"):
        if doc_file.is_dir():
            continue

        rel_path = str(doc_file.relative_to(root_path))

        # Skip hidden files and common non-doc files
        if "/." in rel_path or doc_file.name.startswith("."):
            continue

        # Determine file type
        ext = doc_file.suffix.lower()
        if ext not in {".md", ".yaml", ".yml", ".json"}:
            continue

        doc_types[ext] = doc_types.get(ext, 0) + 1

        # Get subcategory
        sub_id, sub_name = _get_docs_subcategory(rel_path)
        subcategory_counts[sub_name] = subcategory_counts.get(sub_name, 0) + 1

        # Extract metadata
        purpose = ""
        references = []

        if ext == ".md":
            purpose = _get_doc_purpose_from_content(doc_file)
            if include_references:
                references = _extract_doc_references(doc_file)

        # Classify doc type based on filename patterns
        filename = doc_file.name.upper()
        doc_type = "documentation"
        if "README" in filename:
            doc_type = "index"
        elif "GUIDE" in filename or "TUTORIAL" in filename:
            doc_type = "guide"
        elif "REFERENCE" in filename or "API" in filename:
            doc_type = "reference"
        elif "EXAMPLE" in filename:
            doc_type = "example"
        elif "PLAN" in filename or "SPRINT" in filename:
            doc_type = "planning"
        elif "VALIDATION" in filename or "AUDIT" in filename or "REPORT" in filename:
            doc_type = "validation"
        elif "DESIGN" in filename or "ARCHITECTURE" in filename:
            doc_type = "architecture"
        elif ext in {".yaml", ".yml"}:
            doc_type = "config-example"

        # Get file stats
        stat = doc_file.stat()
        size_bytes = stat.st_size
        lines = _count_lines(doc_file)
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        classification = {
            "path": rel_path,
            "category": "documentation",
            "subcategory": sub_name,
            "subcategory_id": sub_id,
            "doc_type": doc_type,
            "purpose": purpose or f"Documentation in {sub_name}",
            "file_format": ext,
            "references": references,
            "size_bytes": size_bytes,
            "lines": lines,
            "last_modified": mtime,
        }
        classifications.append(classification)

    # Sort by path
    classifications.sort(key=lambda c: c["path"])

    # Build output structure
    output = {
        "classification": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "taxonomy_version": "1.0",
            "directory": "docs/",
            "summary": {
                "total_files": len(classifications),
                "by_subcategory": dict(sorted(subcategory_counts.items())),
                "by_file_type": dict(sorted(doc_types.items())),
            },
            "files": classifications,
        }
    }

    return output


def _get_tests_subcategory(path: str) -> tuple[str, str]:
    """Determine subcategory for a tests/ file based on path."""
    # Check path prefixes (most specific first)
    sorted_prefixes = sorted(TESTS_SUBCATEGORY_MAP.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if path.startswith(prefix):
            return TESTS_SUBCATEGORY_MAP[prefix]

    # Root tests/ files
    return ("3.10", "root")


def _get_test_subject(file_path: Path, rel_path: str) -> str:
    """Determine what module/component this test file tests."""
    filename = file_path.stem  # e.g., "test_yaml_loader"

    # Remove test_ prefix
    if filename.startswith("test_"):
        subject = filename[5:]
    else:
        subject = filename

    # Try to find corresponding source file
    # tests/roadmap/test_models.py -> vibey/roadmap/models.py
    parts = rel_path.split("/")
    if len(parts) >= 2:
        # Remove 'tests/' prefix and reconstruct
        test_path_parts = parts[1:]  # e.g., ['roadmap', 'test_models.py']
        if test_path_parts:
            potential_module = "vibey/" + "/".join(test_path_parts[:-1])
            if potential_module != "vibey/":
                potential_module = potential_module + "/" + subject + ".py"
            else:
                potential_module = "vibey/" + subject + ".py"
            return potential_module

    return subject


def classify_tests_files(
    root_path: Path,
    include_dependencies: bool = True,
) -> dict[str, Any]:
    """Classify all files in the tests/ directory.

    Args:
        root_path: Repository root path
        include_dependencies: Whether to extract import dependencies

    Returns:
        Classification dictionary in the expected YAML format
    """
    tests_dir = root_path / "tests"

    if not tests_dir.exists():
        raise ValueError(f"tests/ directory not found at {tests_dir}")

    classifications: list[dict[str, Any]] = []
    subcategory_counts: dict[str, int] = {}
    test_types: dict[str, int] = {}

    # Scan all Python files
    for test_file in tests_dir.rglob("*.py"):
        rel_path = str(test_file.relative_to(root_path))

        # Skip __pycache__
        if "__pycache__" in rel_path:
            continue

        # Get subcategory
        sub_id, sub_name = _get_tests_subcategory(rel_path)
        subcategory_counts[sub_name] = subcategory_counts.get(sub_name, 0) + 1

        # Get module path
        module = rel_path.replace("/", ".").replace(".py", "")
        if module.endswith(".__init__"):
            module = module[:-9]

        # Determine test type
        filename = test_file.name
        test_type = "unit"
        if "integration" in rel_path.lower():
            test_type = "integration"
        elif "conftest" in filename:
            test_type = "fixture"
        elif filename == "__init__.py":
            test_type = "package-init"
        elif "fixture" in filename.lower() or "fixtures" in rel_path.lower():
            test_type = "fixture"

        test_types[test_type] = test_types.get(test_type, 0) + 1

        # Extract metadata
        purpose = _get_purpose_from_docstring(test_file)
        test_subject = _get_test_subject(test_file, rel_path)

        internal_deps, external_deps = [], []
        if include_dependencies and test_file.suffix == ".py":
            internal_deps, external_deps = _extract_python_imports(test_file)

        # Get file stats
        stat = test_file.stat()
        size_bytes = stat.st_size
        lines = _count_lines(test_file)
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        classification = {
            "path": rel_path,
            "category": "tests",
            "subcategory": sub_name,
            "subcategory_id": sub_id,
            "test_type": test_type,
            "purpose": purpose or f"Tests for {test_subject}",
            "module": module,
            "tests_subject": test_subject,
            "dependencies": {
                "internal": internal_deps,
                "external": external_deps,
            },
            "size_bytes": size_bytes,
            "lines": lines,
            "last_modified": mtime,
        }
        classifications.append(classification)

    # Sort by path
    classifications.sort(key=lambda c: c["path"])

    # Build output structure
    output = {
        "classification": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "taxonomy_version": "1.0",
            "directory": "tests/",
            "summary": {
                "total_files": len(classifications),
                "by_subcategory": dict(sorted(subcategory_counts.items())),
                "by_test_type": dict(sorted(test_types.items())),
            },
            "files": classifications,
        }
    }

    return output


def build_dependency_graph(
    root_path: Path,
    include_external: bool = False,
) -> dict[str, Any]:
    """Build a dependency graph showing which files depend on which others.

    Args:
        root_path: Repository root path
        include_external: Whether to include external dependencies

    Returns:
        Dependency graph dictionary in YAML format
    """
    vibey_dir = root_path / "vibey"
    tests_dir = root_path / "tests"

    # Maps module name to file path
    module_to_file: dict[str, str] = {}
    # Maps file path to its dependencies
    file_deps: dict[str, dict[str, Any]] = {}
    # Maps file path to files that depend on it
    dependents: dict[str, list[str]] = {}

    def process_directory(directory: Path, base_module: str) -> None:
        """Process a directory for dependencies."""
        if not directory.exists():
            return

        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            rel_path = str(py_file.relative_to(root_path))
            module = rel_path.replace("/", ".").replace(".py", "")
            if module.endswith(".__init__"):
                module = module[:-9]

            module_to_file[module] = rel_path

            # Extract imports
            internal_deps, external_deps = _extract_python_imports(py_file)

            file_deps[rel_path] = {
                "module": module,
                "imports_internal": internal_deps,
                "imports_external": external_deps if include_external else [],
            }

    # Process vibey/ and tests/
    process_directory(vibey_dir, "vibey")
    process_directory(tests_dir, "tests")

    # Build reverse dependency map (who depends on me)
    for file_path, deps in file_deps.items():
        for imp in deps["imports_internal"]:
            # Find the best matching file for this import
            # Sort by length descending to match most specific module first
            best_match = None
            best_match_len = 0
            for mod, mod_file in module_to_file.items():
                # Check if import matches or is a submodule of this module
                if imp == mod or imp.startswith(mod + ".") or mod.startswith(imp + "."):
                    if len(mod) > best_match_len:
                        best_match = mod_file
                        best_match_len = len(mod)
                # Also check if the module is what's being imported
                if mod == imp:
                    best_match = mod_file
                    break

            if best_match and best_match != file_path:
                if best_match not in dependents:
                    dependents[best_match] = []
                if file_path not in dependents[best_match]:
                    dependents[best_match].append(file_path)

    # Build edges list for graph representation
    edges: list[dict[str, str]] = []
    for file_path, deps in file_deps.items():
        for imp in deps["imports_internal"]:
            # Find the best matching file
            best_match = None
            best_match_len = 0
            for mod, mod_file in module_to_file.items():
                if imp == mod or imp.startswith(mod + ".") or mod.startswith(imp + "."):
                    if len(mod) > best_match_len:
                        best_match = mod_file
                        best_match_len = len(mod)
                if mod == imp:
                    best_match = mod_file
                    break

            if best_match and best_match != file_path:
                edges.append({
                    "from": file_path,
                    "to": best_match,
                    "import": imp,
                })

    # Calculate statistics
    total_files = len(file_deps)
    total_edges = len(edges)
    files_with_deps = sum(1 for d in file_deps.values() if d["imports_internal"])
    files_depended_on = len(dependents)

    # Find most depended-on files
    most_depended = sorted(
        [(f, len(d)) for f, d in dependents.items()],
        key=lambda x: x[1],
        reverse=True,
    )[:20]

    # Find files with most dependencies
    most_deps = sorted(
        [(f, len(d["imports_internal"])) for f, d in file_deps.items()],
        key=lambda x: x[1],
        reverse=True,
    )[:20]

    # Build output
    output = {
        "dependency_graph": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_files": total_files,
                "total_edges": total_edges,
                "files_with_dependencies": files_with_deps,
                "files_depended_on": files_depended_on,
                "most_depended_on": [
                    {"file": f, "dependent_count": c} for f, c in most_depended
                ],
                "most_dependencies": [
                    {"file": f, "dependency_count": c} for f, c in most_deps
                ],
            },
            "files": {
                path: {
                    "module": deps["module"],
                    "depends_on": deps["imports_internal"],
                    "depended_on_by": dependents.get(path, []),
                }
                for path, deps in sorted(file_deps.items())
            },
            "edges": edges,
        }
    }

    return output


def generate_consolidated_registry(
    root_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate a consolidated file registry from all classification outputs.

    Args:
        root_path: Repository root path
        output_dir: Directory containing classification outputs (defaults to
                   .vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/)

    Returns:
        Consolidated registry dictionary
    """
    if output_dir is None:
        output_dir = root_path / ".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1"

    # Load existing classification files
    vibey_class_file = output_dir / "VIBEY_FILE_CLASSIFICATION.yaml"
    docs_class_file = output_dir / "DOCS_FILE_CLASSIFICATION.yaml"
    tests_class_file = output_dir / "TESTS_FILE_CLASSIFICATION.yaml"
    dep_graph_file = output_dir / "FILE_DEPENDENCY_GRAPH.yaml"

    vibey_class = {}
    docs_class = {}
    tests_class = {}
    dep_graph = {}

    if vibey_class_file.exists():
        with open(vibey_class_file) as f:
            vibey_class = yaml.safe_load(f) or {}

    if docs_class_file.exists():
        with open(docs_class_file) as f:
            docs_class = yaml.safe_load(f) or {}

    if tests_class_file.exists():
        with open(tests_class_file) as f:
            tests_class = yaml.safe_load(f) or {}

    if dep_graph_file.exists():
        with open(dep_graph_file) as f:
            dep_graph = yaml.safe_load(f) or {}

    # Extract file counts
    vibey_count = len(vibey_class.get("classification", {}).get("files", []))
    docs_count = len(docs_class.get("classification", {}).get("files", []))
    tests_count = len(tests_class.get("classification", {}).get("files", []))
    total_count = vibey_count + docs_count + tests_count

    # Build consolidated file list
    all_files: list[dict[str, Any]] = []

    # Add vibey files
    for f in vibey_class.get("classification", {}).get("files", []):
        all_files.append({
            "path": f["path"],
            "category": f["category"],
            "subcategory": f["subcategory"],
            "purpose": f.get("purpose", ""),
            "size_bytes": f.get("size_bytes", 0),
            "lines": f.get("lines"),
            "has_tests": f.get("test_coverage", {}).get("has_tests", False),
            "has_docs": f.get("doc_coverage", False),
        })

    # Add docs files
    for f in docs_class.get("classification", {}).get("files", []):
        all_files.append({
            "path": f["path"],
            "category": f["category"],
            "subcategory": f["subcategory"],
            "purpose": f.get("purpose", ""),
            "size_bytes": f.get("size_bytes", 0),
            "lines": f.get("lines"),
            "doc_type": f.get("doc_type", ""),
        })

    # Add tests files
    for f in tests_class.get("classification", {}).get("files", []):
        all_files.append({
            "path": f["path"],
            "category": f["category"],
            "subcategory": f["subcategory"],
            "purpose": f.get("purpose", ""),
            "size_bytes": f.get("size_bytes", 0),
            "lines": f.get("lines"),
            "test_type": f.get("test_type", ""),
            "tests_subject": f.get("tests_subject", ""),
        })

    # Calculate overall statistics
    total_size = sum(f.get("size_bytes", 0) for f in all_files)
    total_lines = sum(f.get("lines", 0) or 0 for f in all_files)

    # Category breakdown
    category_stats: dict[str, dict[str, int]] = {}
    for f in all_files:
        cat = f["category"]
        if cat not in category_stats:
            category_stats[cat] = {"count": 0, "size_bytes": 0, "lines": 0}
        category_stats[cat]["count"] += 1
        category_stats[cat]["size_bytes"] += f.get("size_bytes", 0)
        category_stats[cat]["lines"] += f.get("lines", 0) or 0

    # Subcategory breakdown
    subcategory_stats: dict[str, int] = {}
    for f in all_files:
        sub = f.get("subcategory", "unknown")
        subcategory_stats[sub] = subcategory_stats.get(sub, 0) + 1

    # Dependency stats
    dep_summary = dep_graph.get("dependency_graph", {}).get("summary", {})

    # Build output
    output = {
        "file_registry": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "summary": {
                "total_files": total_count,
                "total_size_bytes": total_size,
                "total_lines": total_lines,
                "by_category": {
                    cat: stats for cat, stats in sorted(category_stats.items())
                },
                "by_subcategory": dict(sorted(subcategory_stats.items())),
            },
            "component_summaries": {
                "vibey_package": {
                    "file_count": vibey_count,
                    "subcategories": vibey_class.get("classification", {}).get("summary", {}).get("by_subcategory", {}),
                },
                "documentation": {
                    "file_count": docs_count,
                    "subcategories": docs_class.get("classification", {}).get("summary", {}).get("by_subcategory", {}),
                    "file_types": docs_class.get("classification", {}).get("summary", {}).get("by_file_type", {}),
                },
                "tests": {
                    "file_count": tests_count,
                    "subcategories": tests_class.get("classification", {}).get("summary", {}).get("by_subcategory", {}),
                    "test_types": tests_class.get("classification", {}).get("summary", {}).get("by_test_type", {}),
                },
                "dependencies": {
                    "total_edges": dep_summary.get("total_edges", 0),
                    "files_with_dependencies": dep_summary.get("files_with_dependencies", 0),
                    "files_depended_on": dep_summary.get("files_depended_on", 0),
                    "most_depended_on": dep_summary.get("most_depended_on", [])[:10],
                    "most_dependencies": dep_summary.get("most_dependencies", [])[:10],
                },
            },
            "source_files": {
                "vibey_classification": str(vibey_class_file.relative_to(root_path)) if vibey_class_file.exists() else None,
                "docs_classification": str(docs_class_file.relative_to(root_path)) if docs_class_file.exists() else None,
                "tests_classification": str(tests_class_file.relative_to(root_path)) if tests_class_file.exists() else None,
                "dependency_graph": str(dep_graph_file.relative_to(root_path)) if dep_graph_file.exists() else None,
            },
            "files": sorted(all_files, key=lambda x: x["path"]),
        }
    }

    return output


def save_classification(classification: dict[str, Any], output_path: Path) -> None:
    """Save classification to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            classification,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )


def main() -> None:
    """CLI entry point for file classification."""
    import argparse

    parser = argparse.ArgumentParser(description="Classify files in vibey/ directory")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(
            ".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/VIBEY_FILE_CLASSIFICATION.yaml"
        ),
        help="Output file path",
    )
    parser.add_argument(
        "--root",
        "-r",
        type=Path,
        default=Path.cwd(),
        help="Repository root path",
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="Skip dependency extraction",
    )

    args = parser.parse_args()

    print(f"Classifying files in vibey/ directory...")
    classification = classify_vibey_files(
        args.root,
        include_dependencies=not args.no_deps,
    )

    summary = classification["classification"]["summary"]
    print(f"Classified {summary['total_files']} files")
    print(f"By subcategory: {summary['by_subcategory']}")

    save_classification(classification, args.output)
    print(f"Classification saved to: {args.output}")


if __name__ == "__main__":
    main()
