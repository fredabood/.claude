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
