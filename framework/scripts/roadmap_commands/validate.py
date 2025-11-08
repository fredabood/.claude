"""
'roadmap validate' command - Validate roadmap structure and health.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

# Add roadmap-lib to path
roadmap_lib_path = Path(__file__).parent.parent / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_path))

from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from roadmap.validation import Validator
from filesystem import FileSystemManager, find_roadmap_root
from dependencies import DependencyResolver
from blockers import BlockerComputer


class RoadmapHealthChecker:
    """Performs health checks on roadmap."""

    def __init__(self, fs: FileSystemManager):
        self.fs = fs
        self.issues = []
        self.warnings = []

    def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        self.issues = []
        self.warnings = []

        # Check roadmap exists
        if not self.fs.roadmap_exists():
            self.issues.append({
                "severity": "error",
                "type": "missing_roadmap",
                "message": "Roadmap file not found",
            })
            return self._build_report()

        # Load roadmap
        roadmap = load_roadmap(self.fs.get_roadmap_path())

        # Run checks
        self._check_circular_dependencies()
        self._check_orphaned_files()
        self._check_invalid_references(roadmap)
        self._check_progress_consistency(roadmap)
        self._check_blockers(roadmap)
        self._check_schema_validation()

        return self._build_report()

    def _check_circular_dependencies(self):
        """Check for circular dependencies."""
        resolver = DependencyResolver(self.fs.root_dir)
        resolver.build_dependency_graph()
        cycles = resolver.detect_circular_dependencies()

        if cycles:
            for cycle in cycles:
                self.issues.append({
                    "severity": "error",
                    "type": "circular_dependency",
                    "message": f"Circular dependency detected: {' → '.join(cycle)}",
                    "cycle": cycle,
                })

    def _check_orphaned_files(self):
        """Check for orphaned sprint/task files."""
        roadmap = load_roadmap(self.fs.get_roadmap_path())

        # Get all expected sprint IDs from tracks
        expected_sprints = set()
        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if track_path.exists():
                track = load_track(track_path)
                for sprint_summary in track.sprints:
                    expected_sprints.add(sprint_summary.id)

        # Check for orphaned sprint files
        actual_sprints = set(self.fs.list_sprints())
        orphaned_sprints = actual_sprints - expected_sprints

        for sprint_id in orphaned_sprints:
            self.warnings.append({
                "severity": "warning",
                "type": "orphaned_sprint",
                "message": f"Orphaned sprint file: {sprint_id}",
                "sprint_id": sprint_id,
            })

        # Check for orphaned task files
        expected_task_files = expected_sprints
        actual_task_files = set(self.fs.list_sprint_tasks())
        orphaned_tasks = actual_task_files - expected_task_files

        for sprint_id in orphaned_tasks:
            self.warnings.append({
                "severity": "warning",
                "type": "orphaned_tasks",
                "message": f"Orphaned task file: {sprint_id}-tasks.yaml",
                "sprint_id": sprint_id,
            })

    def _check_invalid_references(self, roadmap):
        """Check for invalid object references."""
        # Check track references
        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if not track_path.exists():
                self.issues.append({
                    "severity": "error",
                    "type": "missing_track",
                    "message": f"Track file not found: {track_summary.id}",
                    "track_id": track_summary.id,
                })
                continue

            track = load_track(track_path)

            # Check sprint references
            for sprint_summary in track.sprints:
                sprint_path = self.fs.get_sprint_path(sprint_summary.id)
                if not sprint_path.exists():
                    self.issues.append({
                        "severity": "error",
                        "type": "missing_sprint",
                        "message": f"Sprint file not found: {sprint_summary.id}",
                        "sprint_id": sprint_summary.id,
                        "track_id": track.id,
                    })

    def _check_progress_consistency(self, roadmap):
        """Check for progress calculation inconsistencies."""
        # Load all tracks and check totals
        actual_sprints_total = 0
        actual_tasks_total = 0

        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if track_path.exists():
                track = load_track(track_path)
                actual_sprints_total += len(track.sprints)

                for sprint_summary in track.sprints:
                    tasks_path = self.fs.get_tasks_path(sprint_summary.id)
                    if tasks_path.exists():
                        tasks = load_tasks(tasks_path)
                        # Only count development tasks
                        dev_tasks = [t for t in tasks if not t.is_quality_gate()]
                        actual_tasks_total += len(dev_tasks)

        # Check if roadmap totals match
        if roadmap.progress.sprints_total != actual_sprints_total:
            self.warnings.append({
                "severity": "warning",
                "type": "progress_mismatch",
                "message": f"Roadmap sprint count mismatch: expected {actual_sprints_total}, got {roadmap.progress.sprints_total}",
            })

        if roadmap.progress.tasks_total != actual_tasks_total:
            self.warnings.append({
                "severity": "warning",
                "type": "progress_mismatch",
                "message": f"Roadmap task count mismatch: expected {actual_tasks_total}, got {roadmap.progress.tasks_total}",
            })

    def _check_blockers(self, roadmap):
        """Check for blocking issues."""
        computer = BlockerComputer(self.fs.root_dir)

        # Check roadmap blockers
        roadmap_blockers = computer.compute_roadmap_blockers(roadmap)
        if roadmap_blockers:
            for blocker in roadmap_blockers:
                self.warnings.append({
                    "severity": "info",
                    "type": "roadmap_blocked",
                    "message": f"Roadmap blocked by external dependency: {blocker.dependency_id}",
                    "dependency_id": blocker.dependency_id,
                    "current_status": blocker.current_status,
                    "required_status": blocker.required_status,
                })

    def _check_schema_validation(self):
        """Validate YAML files against schemas."""
        validator = Validator()

        # Validate roadmap
        roadmap_path = self.fs.get_roadmap_path()
        result = validator.validate_file(roadmap_path, "roadmap")

        if not result.valid:
            for error in result.errors:
                self.issues.append({
                    "severity": "error",
                    "type": "schema_validation",
                    "message": f"Roadmap validation error: {error}",
                    "file": str(roadmap_path),
                })

        # Validate tracks
        for track_id in self.fs.list_tracks():
            track_path = self.fs.get_track_path(track_id)
            result = validator.validate_file(track_path, "track")

            if not result.valid:
                for error in result.errors:
                    self.issues.append({
                        "severity": "error",
                        "type": "schema_validation",
                        "message": f"Track validation error ({track_id}): {error}",
                        "file": str(track_path),
                    })

        # Validate sprints
        for sprint_id in self.fs.list_sprints():
            sprint_path = self.fs.get_sprint_path(sprint_id)
            result = validator.validate_file(sprint_path, "sprint")

            if not result.valid:
                for error in result.errors:
                    self.issues.append({
                        "severity": "error",
                        "type": "schema_validation",
                        "message": f"Sprint validation error ({sprint_id}): {error}",
                        "file": str(sprint_path),
                    })

    def _build_report(self) -> Dict[str, Any]:
        """Build health check report."""
        return {
            "healthy": len(self.issues) == 0,
            "error_count": len([i for i in self.issues if i["severity"] == "error"]),
            "warning_count": len([i for i in self.issues + self.warnings if i["severity"] == "warning"]),
            "info_count": len([i for i in self.warnings if i["severity"] == "info"]),
            "issues": self.issues,
            "warnings": self.warnings,
        }


def print_report(report: Dict[str, Any], verbose: bool = False):
    """Pretty print health check report."""
    print("\n" + "="*80)
    print("🏥 Roadmap Health Check")
    print("="*80)

    if report["healthy"]:
        print("\n✅ Roadmap is healthy!")
    else:
        print(f"\n⚠️  Issues found:")
        print(f"  Errors:   {report['error_count']}")
        print(f"  Warnings: {report['warning_count']}")
        print(f"  Info:     {report['info_count']}")

    # Print errors
    if report["issues"]:
        print(f"\n❌ Errors ({len(report['issues'])}):")
        for issue in report["issues"]:
            print(f"\n  [{issue['type']}] {issue['message']}")
            if verbose and "file" in issue:
                print(f"    File: {issue['file']}")

    # Print warnings
    if report["warnings"] and (verbose or not report["healthy"]):
        print(f"\n⚠️  Warnings ({len(report['warnings'])}):")
        for warning in report["warnings"]:
            print(f"\n  [{warning['type']}] {warning['message']}")

    if not report["healthy"]:
        print("\n💡 Recommendations:")
        if report["error_count"] > 0:
            print("  - Fix errors before continuing development")
            print("  - Run 'roadmap progress --refresh' to recalculate progress")
        if any(i["type"] == "circular_dependency" for i in report["issues"]):
            print("  - Break circular dependencies by removing or reordering dependencies")
        if any(i["type"] == "orphaned_sprint" for i in report["warnings"]):
            print("  - Remove orphaned files or add them to track definitions")

    print("="*80 + "\n")


def handle_validate(args):
    """Handle 'roadmap validate' command."""
    # Find root directory
    if args.dir:
        root_dir = args.dir
    else:
        root_dir = find_roadmap_root()
        if not root_dir:
            print("❌ No roadmap found. Run 'roadmap init' first.")
            sys.exit(1)

    fs = FileSystemManager(root_dir)

    # Run health check
    print("🔍 Running health checks...")
    checker = RoadmapHealthChecker(fs)
    report = checker.check_all()

    # Print report
    print_report(report, verbose=args.verbose)

    # Fix issues if requested
    if args.fix and not report["healthy"]:
        print("\n🔧 Attempting to fix issues...")

        # Fix progress inconsistencies
        if any(i["type"] == "progress_mismatch" for i in report["warnings"]):
            print("  - Recalculating progress...")
            import subprocess
            result = subprocess.run(
                ["python3", str(Path(__file__).parent.parent / "roadmap-update.py"),
                 "--dir", str(root_dir), "--refresh-progress"],
                capture_output=True
            )
            if result.returncode == 0:
                print("    ✅ Progress recalculated")
            else:
                print("    ❌ Failed to recalculate progress")

        print("\n💡 Some issues may require manual intervention")

    # Exit with error code if issues found
    if not report["healthy"]:
        sys.exit(1)
