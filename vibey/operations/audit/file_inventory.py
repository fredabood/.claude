"""File inventory generation for codebase auditing.

This module provides tooling to recursively scan directories and generate
a structured YAML inventory of all files with metadata.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FileInventoryConfig:
    """Configuration for file inventory generation."""

    directories: list[str] = field(default_factory=lambda: ["vibey/", "docs/", "tests/", "scripts/"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "__pycache__",
            "*.pyc",
            ".git",
            "node_modules",
            ".venv",
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.so",
            "*.dylib",
            ".DS_Store",
            "*.db",
            "*.db-shm",
            "*.db-wal",
            "*.bak",
        ]
    )
    root_path: Path = field(default_factory=Path.cwd)


@dataclass
class FileInfo:
    """Information about a single file."""

    path: str
    file_type: str
    size_bytes: int
    last_modified: str
    lines: int | None


def _get_file_type(path: Path) -> str:
    """Determine file type from extension."""
    suffix = path.suffix.lower()
    type_map = {
        ".py": "python",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".txt": "text",
        ".rst": "restructuredtext",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".cfg": "config",
        ".ini": "config",
        ".gitignore": "gitignore",
    }
    return type_map.get(suffix, "other")


def _should_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    """Check if path should be excluded based on patterns."""
    path_str = str(path)
    name = path.name

    for pattern in exclude_patterns:
        # Directory patterns (no *)
        if "*" not in pattern:
            if pattern in path_str.split(os.sep):
                return True
            if name == pattern:
                return True
        # Glob patterns with *
        elif pattern.startswith("*."):
            ext = pattern[1:]  # e.g., ".pyc"
            if path_str.endswith(ext):
                return True
        elif pattern.endswith("*"):
            prefix = pattern[:-1]
            if name.startswith(prefix):
                return True

    return False


def _count_lines(path: Path) -> int | None:
    """Count lines in a text file, return None for binary files."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except (UnicodeDecodeError, OSError):
        return None


def _scan_directory(
    directory: Path, root_path: Path, exclude_patterns: list[str]
) -> tuple[list[FileInfo], int]:
    """Recursively scan a directory and collect file information.

    Returns:
        Tuple of (list of FileInfo, directory count)
    """
    files: list[FileInfo] = []
    dir_count = 0

    if not directory.exists():
        return files, dir_count

    for item in directory.rglob("*"):
        if _should_exclude(item, exclude_patterns):
            continue

        if item.is_dir():
            dir_count += 1
            continue

        if item.is_file():
            try:
                stat = item.stat()
                rel_path = str(item.relative_to(root_path))

                # Get modification time as ISO string
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                mtime_str = mtime.isoformat()

                # Count lines for text files
                lines = _count_lines(item)

                files.append(
                    FileInfo(
                        path=rel_path,
                        file_type=_get_file_type(item),
                        size_bytes=stat.st_size,
                        last_modified=mtime_str,
                        lines=lines,
                    )
                )
            except OSError:
                # Skip files we can't access
                continue

    return files, dir_count


def generate_file_inventory(config: FileInventoryConfig | None = None) -> dict[str, Any]:
    """Generate a complete file inventory for specified directories.

    Args:
        config: Configuration for inventory generation. Uses defaults if not provided.

    Returns:
        Dictionary containing the complete inventory in the specified format.
    """
    if config is None:
        config = FileInventoryConfig()

    root_path = config.root_path
    all_files: list[FileInfo] = []
    total_dirs = 0

    # Scan each configured directory
    for dir_name in config.directories:
        dir_path = root_path / dir_name.rstrip("/")
        files, dirs = _scan_directory(dir_path, root_path, config.exclude_patterns)
        all_files.extend(files)
        total_dirs += dirs

    # Calculate extension statistics
    ext_counts: dict[str, int] = {}
    for file_info in all_files:
        ext = Path(file_info.path).suffix.lower() or "(none)"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    # Sort extensions by count
    sorted_exts = dict(sorted(ext_counts.items(), key=lambda x: -x[1]))

    # Build output structure
    inventory = {
        "inventory": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "directories_scanned": config.directories,
            "summary": {
                "total_files": len(all_files),
                "total_directories": total_dirs,
                "by_extension": sorted_exts,
            },
            "files": [
                {
                    "path": f.path,
                    "type": f.file_type,
                    "size_bytes": f.size_bytes,
                    "last_modified": f.last_modified,
                    "lines": f.lines,
                }
                for f in sorted(all_files, key=lambda x: x.path)
            ],
        }
    }

    return inventory


def save_inventory(inventory: dict[str, Any], output_path: Path) -> None:
    """Save inventory to a YAML file.

    Args:
        inventory: The inventory dictionary to save.
        output_path: Path to write the YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def main() -> None:
    """CLI entry point for file inventory generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate file inventory for codebase audit")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(".vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml"),
        help="Output file path",
    )
    parser.add_argument(
        "--directories",
        "-d",
        nargs="+",
        default=["vibey/", "docs/", "tests/", "scripts/"],
        help="Directories to scan",
    )
    parser.add_argument(
        "--root",
        "-r",
        type=Path,
        default=Path.cwd(),
        help="Root path for relative paths",
    )

    args = parser.parse_args()

    config = FileInventoryConfig(
        directories=args.directories,
        root_path=args.root,
    )

    print(f"Generating file inventory for: {config.directories}")
    inventory = generate_file_inventory(config)

    summary = inventory["inventory"]["summary"]
    print(f"Found {summary['total_files']} files in {summary['total_directories']} directories")
    print(f"Extensions: {summary['by_extension']}")

    save_inventory(inventory, args.output)
    print(f"Inventory saved to: {args.output}")


if __name__ == "__main__":
    main()
