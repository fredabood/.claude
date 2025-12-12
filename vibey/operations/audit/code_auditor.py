"""Code auditor for comprehensive file quality assessment.

This module provides automated code auditing capabilities based on the
audit criteria defined in CORE_LIB_AUDIT_CRITERIA.md.
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


@dataclass
class AuditResult:
    """Result of auditing a single file."""

    path: str
    purpose: str
    lines: int
    size_bytes: int
    last_modified: str

    # Scores
    architectural_relevance_score: int = 0
    documentation_status_score: int = 0
    test_coverage_score: int = 0
    best_practices_score: int = 0

    # Details
    architectural_relevance: dict = field(default_factory=dict)
    documentation_status: dict = field(default_factory=dict)
    test_coverage: dict = field(default_factory=dict)
    access_patterns: dict = field(default_factory=dict)
    best_practices: dict = field(default_factory=dict)
    complexity_metrics: dict = field(default_factory=dict)

    findings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    @property
    def total_score(self) -> int:
        return (
            self.architectural_relevance_score
            + self.documentation_status_score
            + self.test_coverage_score
            + self.best_practices_score
        )

    @property
    def grade(self) -> str:
        score = self.total_score
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


def _get_module_docstring(file_path: Path) -> str | None:
    """Extract module docstring from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        return ast.get_docstring(tree)
    except (SyntaxError, UnicodeDecodeError):
        return None


def _count_docstrings(file_path: Path) -> dict[str, Any]:
    """Count classes and functions with/without docstrings."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return {"classes": {"total": 0, "documented": 0}, "functions": {"total": 0, "documented": 0}}

    class_total = 0
    class_documented = 0
    func_total = 0
    func_documented = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_total += 1
            if ast.get_docstring(node):
                class_documented += 1
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Skip private functions for docstring count
            if not node.name.startswith("_") or node.name.startswith("__"):
                func_total += 1
                if ast.get_docstring(node):
                    func_documented += 1

    return {
        "classes": {"total": class_total, "documented": class_documented},
        "functions": {"total": func_total, "documented": func_documented},
    }


def _check_type_hints(file_path: Path) -> dict[str, Any]:
    """Check type hint coverage in a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return {"present": False, "coverage": "none"}

    total_functions = 0
    annotated_functions = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total_functions += 1
            # Check if function has return annotation or any arg annotations
            has_annotation = node.returns is not None
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.annotation is not None:
                    has_annotation = True
                    break
            if has_annotation:
                annotated_functions += 1

    if total_functions == 0:
        return {"present": False, "coverage": "none"}

    ratio = annotated_functions / total_functions
    if ratio >= 0.9:
        coverage = "full"
    elif ratio >= 0.5:
        coverage = "partial"
    else:
        coverage = "none"

    return {"present": ratio > 0, "coverage": coverage}


def _find_test_files(source_path: str, tests_dir: Path) -> list[str]:
    """Find test files that might test a source file."""
    test_files = []

    # Extract filename without extension
    parts = source_path.split("/")
    if len(parts) < 2:
        return test_files

    base_name = os.path.splitext(os.path.basename(source_path))[0]
    subpath = "/".join(parts[1:])  # Remove 'vibey/'

    # Check various test file patterns
    patterns = [
        f"tests/{os.path.dirname(subpath)}/test_{base_name}.py",
        f"tests/test_{base_name}.py",
        f"tests/{parts[1]}/test_{base_name}.py" if len(parts) > 1 else None,
    ]

    for pattern in patterns:
        if pattern:
            test_path = tests_dir.parent / pattern
            if test_path.exists():
                test_files.append(pattern)

    return test_files


def _calculate_complexity(file_path: Path) -> dict[str, Any]:
    """Calculate basic complexity metrics."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return {"functions": 0, "classes": 0}

    functions = 0
    classes = 0

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1

    return {"functions": functions, "classes": classes}


def _check_error_handling(file_path: Path) -> str:
    """Assess error handling quality."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return "poor"

    has_try = False
    has_specific_except = False
    has_bare_except = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            has_try = True
            for handler in node.handlers:
                if handler.type is None:
                    has_bare_except = True
                else:
                    has_specific_except = True

    if not has_try:
        # Check if file is small/simple - no error handling needed
        if len(content.split("\n")) < 50:
            return "adequate"
        return "missing"

    if has_bare_except and not has_specific_except:
        return "poor"
    if has_specific_except:
        return "good"
    return "adequate"


def _check_logging(file_path: Path) -> str:
    """Check logging practices."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError):
        return "missing"

    # Check for logging imports and usage
    has_logging_import = "import logging" in content or "from logging" in content
    has_logger = "logger" in content.lower() or "logging." in content

    if has_logging_import and has_logger:
        return "appropriate"
    elif has_logger:
        return "appropriate"
    else:
        return "missing"


def audit_python_file(
    file_path: Path,
    root_path: Path,
    module_context: dict[str, Any] | None = None,
) -> AuditResult:
    """Audit a single Python file according to criteria.

    Args:
        file_path: Path to the Python file
        root_path: Repository root path
        module_context: Optional context about the module (alignment, layer, etc.)

    Returns:
        AuditResult with all audit data
    """
    rel_path = str(file_path.relative_to(root_path))
    stat = file_path.stat()

    # Get purpose from docstring
    docstring = _get_module_docstring(file_path)
    purpose = ""
    if docstring:
        purpose = docstring.split("\n")[0].strip()

    # Count lines
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = sum(1 for _ in f)
    except (UnicodeDecodeError, OSError):
        lines = 0

    result = AuditResult(
        path=rel_path,
        purpose=purpose or f"Part of {os.path.dirname(rel_path)} module",
        lines=lines,
        size_bytes=stat.st_size,
        last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    )

    # Complexity metrics
    result.complexity_metrics = _calculate_complexity(file_path)

    # 1. Architectural Relevance
    alignment = module_context.get("alignment", "aligned") if module_context else "aligned"
    placement = module_context.get("placement_correct", True) if module_context else True
    layer = module_context.get("layer", "business_logic") if module_context else "business_logic"

    result.architectural_relevance = {
        "alignment": alignment,
        "placement_correct": placement,
        "single_responsibility": True,  # Assume true, override in context
        "layer": layer,
        "notes": "",
    }

    # Score architectural relevance
    if alignment == "aligned" and placement:
        result.architectural_relevance_score = 25
    elif alignment == "aligned":
        result.architectural_relevance_score = 20
    elif alignment == "partial":
        result.architectural_relevance_score = 15
    elif alignment == "deprecated":
        result.architectural_relevance_score = 5
    else:
        result.architectural_relevance_score = 10

    # 2. Documentation Status
    doc_counts = _count_docstrings(file_path)
    type_hints = _check_type_hints(file_path)

    class_coverage = 0
    if doc_counts["classes"]["total"] > 0:
        class_coverage = (doc_counts["classes"]["documented"] / doc_counts["classes"]["total"]) * 100

    func_coverage = 0
    if doc_counts["functions"]["total"] > 0:
        func_coverage = (doc_counts["functions"]["documented"] / doc_counts["functions"]["total"]) * 100

    result.documentation_status = {
        "module_docstring": "present" if docstring else "missing",
        "class_docstrings": {
            "total": doc_counts["classes"]["total"],
            "documented": doc_counts["classes"]["documented"],
            "coverage_percent": round(class_coverage, 1),
        },
        "function_docstrings": {
            "total": doc_counts["functions"]["total"],
            "documented": doc_counts["functions"]["documented"],
            "coverage_percent": round(func_coverage, 1),
        },
        "type_hints": type_hints,
        "inline_comments": "sparse",  # Default, would need more analysis
    }

    # Score documentation
    avg_coverage = (class_coverage + func_coverage) / 2 if (doc_counts["classes"]["total"] + doc_counts["functions"]["total"]) > 0 else 0
    has_module_doc = docstring is not None

    if has_module_doc and avg_coverage >= 80 and type_hints["coverage"] in ("full", "partial"):
        result.documentation_status_score = 25 if avg_coverage >= 95 else 20
    elif has_module_doc and avg_coverage >= 60:
        result.documentation_status_score = 15
    elif has_module_doc or avg_coverage >= 40:
        result.documentation_status_score = 10
    else:
        result.documentation_status_score = 5

    # 3. Test Coverage
    tests_dir = root_path / "tests"
    test_files = _find_test_files(rel_path, tests_dir)

    result.test_coverage = {
        "has_tests": bool(test_files),
        "test_files": test_files,
        "line_coverage_percent": None,  # Would need coverage.py
        "branch_coverage_percent": None,
        "critical_paths_tested": "unknown",
        "gaps": [],
    }

    # Score test coverage (simplified - we don't have actual coverage data)
    if test_files:
        result.test_coverage_score = 15  # Has tests but unknown coverage
    else:
        result.test_coverage_score = 0
        result.findings.append({
            "type": "major",
            "description": "No test file found",
            "location": rel_path,
            "recommendation": f"Create test file: tests/{'/'.join(rel_path.split('/')[1:])}",
        })

    # 4. Access Patterns (informational, not scored)
    result.access_patterns = {
        "cli_accessible": "cli" in rel_path.lower(),
        "cli_commands": [],
        "mcp_accessible": "mcp" in rel_path.lower(),
        "mcp_tools": [],
        "internal_only": "__" in os.path.basename(rel_path) and rel_path.endswith("__.py") is False,
        "entry_points": [],
    }

    # 5. Best Practices
    error_handling = _check_error_handling(file_path)
    logging_status = _check_logging(file_path)

    result.best_practices = {
        "error_handling": error_handling,
        "logging": logging_status,
        "security_issues": [],
        "performance_concerns": [],
        "code_style_compliant": True,  # Assume compliant
        "violations": [],
    }

    # Score best practices
    bp_score = 25
    if error_handling == "poor":
        bp_score -= 10
        result.findings.append({
            "type": "minor",
            "description": "Error handling could be improved",
            "location": rel_path,
            "recommendation": "Use specific exception types instead of bare except",
        })
    elif error_handling == "missing" and lines > 50:
        bp_score -= 5

    result.best_practices_score = bp_score

    # Generate recommendations
    if not docstring:
        result.recommendations.append("Add module-level docstring")
    if not test_files:
        result.recommendations.append("Add unit tests")
    if type_hints["coverage"] == "none":
        result.recommendations.append("Add type hints to function signatures")

    return result


def audit_module(
    module_path: Path,
    root_path: Path,
    module_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit all Python files in a module directory.

    Args:
        module_path: Path to the module directory
        root_path: Repository root path
        module_context: Optional context about the module

    Returns:
        Module audit dictionary with all file audits and summary
    """
    if not module_path.exists():
        raise ValueError(f"Module path does not exist: {module_path}")

    audits: list[AuditResult] = []

    for py_file in module_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        audit = audit_python_file(py_file, root_path, module_context)
        audits.append(audit)

    # Calculate summary statistics
    total_files = len(audits)
    if total_files == 0:
        return {"module": str(module_path.relative_to(root_path)), "total_files": 0}

    scores = [a.total_score for a in audits]
    grades = [a.grade for a in audits]

    total_lines = sum(a.lines for a in audits)

    grade_dist = {g: grades.count(g) for g in "ABCDF"}

    # Files with tests
    files_with_tests = sum(1 for a in audits if a.test_coverage["has_tests"])

    # Documentation coverage
    module_docs_count = sum(1 for a in audits if a.documentation_status["module_docstring"] == "present")

    # Collect all findings
    all_findings = []
    for a in audits:
        all_findings.extend(a.findings)

    critical_findings = [f for f in all_findings if f.get("type") == "critical"]

    return {
        "module": str(module_path.relative_to(root_path)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "criteria_version": "1.0",
        "total_files": total_files,
        "total_lines": total_lines,
        "scores": {
            "average_quality": round(sum(scores) / total_files, 1),
            "min_quality": min(scores),
            "max_quality": max(scores),
        },
        "grade_distribution": grade_dist,
        "documentation_coverage": {
            "module_docstrings_percent": round((module_docs_count / total_files) * 100, 1),
        },
        "test_coverage": {
            "files_with_tests": f"{files_with_tests}/{total_files}",
            "files_needing_tests": [a.path for a in audits if not a.test_coverage["has_tests"]],
        },
        "critical_findings": critical_findings,
        "files": [
            {
                "path": a.path,
                "purpose": a.purpose,
                "lines": a.lines,
                "quality_score": {
                    "architectural_relevance": a.architectural_relevance_score,
                    "documentation_status": a.documentation_status_score,
                    "test_coverage": a.test_coverage_score,
                    "best_practices": a.best_practices_score,
                    "total": a.total_score,
                    "grade": a.grade,
                },
                "architectural_relevance": a.architectural_relevance,
                "documentation_status": a.documentation_status,
                "test_coverage": a.test_coverage,
                "access_patterns": a.access_patterns,
                "best_practices": a.best_practices,
                "findings": a.findings,
                "recommendations": a.recommendations,
            }
            for a in sorted(audits, key=lambda x: x.path)
        ],
    }


def save_audit(audit: dict[str, Any], output_path: Path) -> None:
    """Save audit results to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            {"audit": audit},
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )
