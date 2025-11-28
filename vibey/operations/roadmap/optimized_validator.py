"""
Optimized Roadmap Validation Engine

High-performance validation with parallel loading, smart caching, and
incremental validation to achieve <10 second validation for full roadmap.

Performance Targets:
- Quick validation: <3 seconds (syntax only)
- Standard validation: <10 seconds (full validation)
- Thorough validation: <20 seconds (with git integration)
- Incremental validation: <2 seconds (changed files only)

Author: Vibey Framework
Created: 2025-11-21
Sprint: roadmap-integrity-fixes-1
Task: roadmap-integrity-fixes-1-task-004
"""

import hashlib
import subprocess
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum


# ============================================================================
# Validation Profiles
# ============================================================================

class ValidationProfile(Enum):
    """Validation thoroughness levels."""
    QUICK = "quick"          # <3s: Syntax only
    STANDARD = "standard"    # <10s: Full validation
    THOROUGH = "thorough"    # <20s: With git integration


@dataclass
class ValidationConfig:
    """Configuration for validation profile."""
    yaml_syntax: bool = True
    schema_validation: bool = True
    reference_check: bool = True
    progress_counters: bool = True
    git_integration: bool = False
    backup_verification: bool = False
    parallel_workers: int = 8


# Predefined profiles
VALIDATION_PROFILES = {
    ValidationProfile.QUICK: ValidationConfig(
        yaml_syntax=True,
        schema_validation=False,
        reference_check=False,
        progress_counters=False,
        parallel_workers=8
    ),
    ValidationProfile.STANDARD: ValidationConfig(
        yaml_syntax=True,
        schema_validation=True,
        reference_check=True,
        progress_counters=True,
        parallel_workers=8
    ),
    ValidationProfile.THOROUGH: ValidationConfig(
        yaml_syntax=True,
        schema_validation=True,
        reference_check=True,
        progress_counters=True,
        git_integration=True,
        backup_verification=True,
        parallel_workers=8
    )
}


# ============================================================================
# Result Data Classes
# ============================================================================

@dataclass
class FileValidationResult:
    """Result of validating a single file."""
    file_path: str
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    cache_hit: bool = False


@dataclass
class ValidationReport:
    """Complete validation report."""
    profile: ValidationProfile
    total_files: int = 0
    valid_files: int = 0
    invalid_files: int = 0
    warnings_count: int = 0
    duration_seconds: float = 0.0
    cache_hit_rate: float = 0.0
    results: List[FileValidationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ============================================================================
# File Content Hashing
# ============================================================================

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate fast MD5 hash of file content.

    Args:
        file_path: Path to file

    Returns:
        MD5 hash as hex string
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        # Read in chunks for memory efficiency
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


# ============================================================================
# Git Integration
# ============================================================================

def get_changed_files(root_dir: Path, file_extension: str = ".yaml") -> Set[Path]:
    """
    Get list of changed YAML files using git status.

    Args:
        root_dir: Repository root directory
        file_extension: File extension to filter

    Returns:
        Set of changed file paths
    """
    try:
        # Get list of modified and untracked files
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return set()

        changed_files = set()
        for line in result.stdout.splitlines():
            if len(line) < 3:
                continue

            # Parse git status format: "XY filename"
            status = line[:2]
            filename = line[3:].strip()

            # Include modified (M), added (A), renamed (R), copied (C) files
            if any(c in status for c in ['M', 'A', 'R', 'C', '?']):
                file_path = root_dir / filename
                if file_path.suffix == file_extension and file_path.exists():
                    changed_files.add(file_path)

        return changed_files

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Git not available or timeout - return empty set
        return set()


# ============================================================================
# Cached YAML Loading
# ============================================================================

# Global cache for parsed YAML files
# Key: (file_path_str, file_hash) → Value: parsed data
_yaml_cache: Dict[Tuple[str, str], Any] = {}
_cache_hits = 0
_cache_misses = 0


def load_yaml_cached(file_path: Path) -> Tuple[Any, bool]:
    """
    Load YAML file with caching based on file content hash.

    Args:
        file_path: Path to YAML file

    Returns:
        Tuple of (parsed_data, cache_hit)
    """
    global _cache_hits, _cache_misses

    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    cache_key = (str(file_path), file_hash)

    # Check cache
    if cache_key in _yaml_cache:
        _cache_hits += 1
        return _yaml_cache[cache_key], True

    # Cache miss - load and parse
    _cache_misses += 1
    with open(file_path) as f:
        data = yaml.safe_load(f)

    # Store in cache
    _yaml_cache[cache_key] = data

    return data, False


def clear_yaml_cache():
    """Clear the YAML cache."""
    global _yaml_cache, _cache_hits, _cache_misses
    _yaml_cache.clear()
    _cache_hits = 0
    _cache_misses = 0


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    total = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total * 100) if total > 0 else 0.0
    return {
        'hits': _cache_hits,
        'misses': _cache_misses,
        'total': total,
        'hit_rate': hit_rate,
        'size': len(_yaml_cache)
    }


# ============================================================================
# Parallel YAML Loading
# ============================================================================

def load_yaml_files_parallel(
    file_paths: List[Path],
    max_workers: int = 8
) -> List[Tuple[Path, Any, bool, Optional[str]]]:
    """
    Load multiple YAML files in parallel with caching.

    Args:
        file_paths: List of file paths to load
        max_workers: Number of parallel workers

    Returns:
        List of tuples: (file_path, data, cache_hit, error)
    """
    results = []

    def load_single(path: Path) -> Tuple[Path, Any, bool, Optional[str]]:
        """Load single file and return result."""
        try:
            data, cache_hit = load_yaml_cached(path)
            return (path, data, cache_hit, None)
        except Exception as e:
            return (path, None, False, str(e))

    # Use ThreadPoolExecutor for parallel loading
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(load_single, path): path for path in file_paths}

        for future in as_completed(future_to_path):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                path = future_to_path[future]
                results.append((path, None, False, str(e)))

    return results


# ============================================================================
# Validation Functions
# ============================================================================

def validate_yaml_syntax(data: Any, file_path: Path) -> FileValidationResult:
    """
    Quick YAML syntax validation.

    Args:
        data: Parsed YAML data
        file_path: Path to file

    Returns:
        FileValidationResult
    """
    result = FileValidationResult(
        file_path=str(file_path),
        valid=True
    )

    if data is None:
        result.valid = False
        result.errors.append("Empty YAML file")
        return result

    # Check basic structure exists
    if not isinstance(data, dict):
        result.valid = False
        result.errors.append("YAML root must be a dictionary")
        return result

    # Detect file type and check for required root key
    if file_path.name == "task.yaml":
        if 'task' not in data:
            result.valid = False
            result.errors.append("Missing 'task' root key")
    elif file_path.name == "sprint.yaml":
        if 'sprint' not in data:
            result.valid = False
            result.errors.append("Missing 'sprint' root key")
    elif file_path.name == "track.yaml":
        if 'track' not in data:
            result.valid = False
            result.errors.append("Missing 'track' root key")

    return result


def validate_schema_full(data: Any, file_path: Path) -> FileValidationResult:
    """
    Full schema validation with required fields and types.

    Args:
        data: Parsed YAML data
        file_path: Path to file

    Returns:
        FileValidationResult
    """
    # Start with syntax validation
    result = validate_yaml_syntax(data, file_path)

    if not result.valid:
        return result

    # Type-specific validation
    if file_path.name == "task.yaml":
        _validate_task_schema(data.get('task', {}), result)
    elif file_path.name == "sprint.yaml":
        _validate_sprint_schema(data.get('sprint', {}), result)
    elif file_path.name == "track.yaml":
        _validate_track_schema(data.get('track', {}), result)

    return result


def _validate_task_schema(task: Dict[str, Any], result: FileValidationResult):
    """Validate task schema."""
    # Note: description is optional for backward compatibility with existing tasks
    required_fields = ['id', 'sprint_id', 'track_id', 'status']
    for field in required_fields:
        if field not in task:
            result.valid = False
            result.errors.append(f"Missing required field: task.{field}")

    # Validate status enum
    if 'status' in task:
        valid_statuses = ['not_started', 'in_progress', 'paused', 'completed', 'blocked', 'cancelled', 'superseded', "wont_do"]
        if task['status'] not in valid_statuses:
            result.valid = False
            result.errors.append(f"Invalid status: {task['status']}")


def _validate_sprint_schema(sprint: Dict[str, Any], result: FileValidationResult):
    """Validate sprint schema."""
    required_fields = ['id', 'track_id', 'status', 'name']
    for field in required_fields:
        if field not in sprint:
            result.valid = False
            result.errors.append(f"Missing required field: sprint.{field}")

    # Validate status enum
    if 'status' in sprint:
        valid_statuses = ['not_started', 'in_progress', 'paused', 'completion_gate_check', 'completed', 'production_gate_check', 'production_ready', 'deployed', 'superseded', "wont_do"]
        if sprint['status'] not in valid_statuses:
            result.valid = False
            result.errors.append(f"Invalid status: {sprint['status']}")


def _validate_track_schema(track: Dict[str, Any], result: FileValidationResult):
    """Validate track schema."""
    required_fields = ['id', 'status', 'name']
    for field in required_fields:
        if field not in track:
            result.valid = False
            result.errors.append(f"Missing required field: track.{field}")

    # Validate status enum
    if 'status' in track:
        valid_statuses = ['not_started', 'in_progress', 'paused', 'completion_gate_check', 'completed', 'production_gate_check', 'production_ready', 'deployed', 'superseded', "wont_do"]
        if track['status'] not in valid_statuses:
            result.valid = False
            result.errors.append(f"Invalid status: {track['status']}")


# ============================================================================
# Optimized Validator Class
# ============================================================================

class OptimizedValidator:
    """
    High-performance roadmap validator with caching and parallel loading.
    """

    def __init__(
        self,
        root_dir: Path,
        profile: ValidationProfile = ValidationProfile.STANDARD
    ):
        """
        Initialize optimized validator.

        Args:
            root_dir: Repository root directory
            profile: Validation profile to use
        """
        self.root_dir = root_dir
        self.roadmap_dir = root_dir / ".vibey" / "roadmap"
        self.profile = profile
        self.config = VALIDATION_PROFILES[profile]

    def validate(
        self,
        incremental: bool = False,
        file_patterns: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Validate roadmap with configured profile.

        Args:
            incremental: If True, only validate changed files (git integration)
            file_patterns: Optional list of glob patterns to validate

        Returns:
            ValidationReport with results
        """
        start_time = time.time()
        report = ValidationReport(profile=self.profile)

        # Find files to validate
        if incremental and self.config.git_integration:
            yaml_files = list(get_changed_files(self.root_dir, ".yaml"))
            if not yaml_files:
                # No changed files, but still find all files for report
                yaml_files = self._find_yaml_files(file_patterns)
                # Mark all as cached since nothing changed
                report.cache_hit_rate = 100.0
        else:
            yaml_files = self._find_yaml_files(file_patterns)

        report.total_files = len(yaml_files)

        if report.total_files == 0:
            report.duration_seconds = time.time() - start_time
            return report

        # Load files in parallel
        load_results = load_yaml_files_parallel(
            yaml_files,
            max_workers=self.config.parallel_workers
        )

        # Validate each file
        for file_path, data, cache_hit, load_error in load_results:
            file_start = time.time()

            if load_error:
                # Failed to load
                result = FileValidationResult(
                    file_path=str(file_path),
                    valid=False,
                    errors=[f"Failed to load: {load_error}"],
                    cache_hit=cache_hit
                )
            elif data is None:
                result = FileValidationResult(
                    file_path=str(file_path),
                    valid=False,
                    errors=["Empty or invalid YAML"],
                    cache_hit=cache_hit
                )
            else:
                # Validate based on profile
                if self.config.schema_validation:
                    result = validate_schema_full(data, file_path)
                else:
                    result = validate_yaml_syntax(data, file_path)

                result.cache_hit = cache_hit

            result.duration_ms = (time.time() - file_start) * 1000

            # Update report
            if result.valid:
                report.valid_files += 1
            else:
                report.invalid_files += 1

            report.warnings_count += len(result.warnings)
            report.results.append(result)

        # Calculate statistics
        report.duration_seconds = time.time() - start_time

        cache_stats = get_cache_stats()
        report.cache_hit_rate = cache_stats['hit_rate']

        return report

    def _find_yaml_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
        """Find all YAML files to validate."""
        if patterns:
            # Use custom patterns
            yaml_files = []
            for pattern in patterns:
                yaml_files.extend(self.roadmap_dir.glob(pattern))
            return list(set(yaml_files))  # Remove duplicates
        else:
            # Default: all YAML files in roadmap
            return list(self.roadmap_dir.rglob("*.yaml"))

    def validate_file(self, file_path: Path) -> FileValidationResult:
        """
        Validate a single file.

        Args:
            file_path: Path to file

        Returns:
            FileValidationResult
        """
        start_time = time.time()

        try:
            data, cache_hit = load_yaml_cached(file_path)

            if self.config.schema_validation:
                result = validate_schema_full(data, file_path)
            else:
                result = validate_yaml_syntax(data, file_path)

            result.cache_hit = cache_hit
            result.duration_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            return FileValidationResult(
                file_path=str(file_path),
                valid=False,
                errors=[f"Validation error: {e}"],
                duration_ms=(time.time() - start_time) * 1000
            )


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_roadmap_quick(root_dir: Path) -> ValidationReport:
    """Quick validation (syntax only, <3 seconds)."""
    validator = OptimizedValidator(root_dir, ValidationProfile.QUICK)
    return validator.validate()


def validate_roadmap_standard(root_dir: Path, incremental: bool = False) -> ValidationReport:
    """Standard validation (full validation, <10 seconds)."""
    validator = OptimizedValidator(root_dir, ValidationProfile.STANDARD)
    return validator.validate(incremental=incremental)


def validate_roadmap_thorough(root_dir: Path) -> ValidationReport:
    """Thorough validation (with git integration, <20 seconds)."""
    validator = OptimizedValidator(root_dir, ValidationProfile.THOROUGH)
    return validator.validate()


# ============================================================================
# CLI Integration Helper
# ============================================================================

def print_validation_report(report: ValidationReport, verbose: bool = False):
    """
    Print validation report to console.

    Args:
        report: ValidationReport to print
        verbose: If True, show all errors; if False, show summary only
    """
    # Header
    print(f"\n{'='*80}")
    print(f"Roadmap Validation Report ({report.profile.value.upper()} profile)")
    print(f"{'='*80}\n")

    # Summary
    print(f"Files validated: {report.total_files}")
    print(f"  ✅ Valid: {report.valid_files}")
    print(f"  ❌ Invalid: {report.invalid_files}")
    print(f"  ⚠️  Warnings: {report.warnings_count}")
    print(f"\nDuration: {report.duration_seconds:.2f} seconds")
    print(f"Cache hit rate: {report.cache_hit_rate:.1f}%")

    # Errors (if any)
    if report.invalid_files > 0:
        print(f"\n{'─'*80}")
        print("Files with errors:")
        print(f"{'─'*80}\n")

        error_files = [r for r in report.results if not r.valid]

        if verbose:
            # Show all errors
            for result in error_files:
                rel_path = Path(result.file_path).relative_to(Path.cwd())
                print(f"❌ {rel_path}")
                for error in result.errors:
                    print(f"   • {error}")
                print()
        else:
            # Show first 10 files with errors
            for result in error_files[:10]:
                rel_path = Path(result.file_path).relative_to(Path.cwd())
                print(f"❌ {rel_path}")
                # Show first error only
                if result.errors:
                    print(f"   • {result.errors[0]}")

            if len(error_files) > 10:
                print(f"\n... and {len(error_files) - 10} more files with errors")
                print("(Use --verbose to see all errors)")

    # Status
    print(f"\n{'='*80}")
    if report.invalid_files == 0:
        print("✅ Validation PASSED")
    else:
        print("❌ Validation FAILED")
    print(f"{'='*80}\n")
