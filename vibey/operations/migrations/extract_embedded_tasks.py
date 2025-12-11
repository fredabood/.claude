"""
Extract Embedded Tasks to Standalone Files

Scans sprint YAML files for embedded tasks[] arrays and creates
standalone task files in .vibey/roadmap/tasks/{ulid}.yaml

This is the FLAT STRUCTURE extraction - each task gets its own file,
named by its ULID, in the tasks/ directory.

Created: 2025-12-11
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timezone
import yaml
import shutil
import json
import re


def is_ulid(value: str) -> bool:
    """Check if a string is a valid ULID (26 chars, alphanumeric)."""
    if not value or len(value) != 26:
        return False
    return bool(re.match(r'^[0-9A-Z]{26}$', value, re.IGNORECASE))


class EmbeddedTaskExtractor:
    """Extract embedded tasks from sprint files to standalone task files."""

    def __init__(self, roadmap_dir: Path, dry_run: bool = True, verbose: bool = True):
        """
        Initialize extractor.

        Args:
            roadmap_dir: Path to .vibey/roadmap directory
            dry_run: If True, don't create files
            verbose: If True, print detailed output
        """
        self.roadmap_dir = Path(roadmap_dir)
        self.sprints_dir = self.roadmap_dir / "sprints"
        self.tasks_dir = self.roadmap_dir / "tasks"
        self.dry_run = dry_run
        self.verbose = verbose

        # Mappings
        self.slug_to_ulid: Dict[str, str] = {}
        self.existing_task_ids: Set[str] = set()

        # Stats
        self.stats = {
            "sprints_scanned": 0,
            "sprints_with_embedded": 0,
            "tasks_extracted": 0,
            "tasks_skipped_existing": 0,
            "tasks_skipped_no_id": 0,
            "errors": [],
        }

    def load_existing_mappings(self) -> None:
        """Load existing task files to build slug->ULID mappings and detect duplicates."""
        if not self.tasks_dir.exists():
            return

        for task_file in self.tasks_dir.glob("*.yaml"):
            if task_file.name.startswith('.'):
                continue

            try:
                with open(task_file) as f:
                    data = yaml.safe_load(f)

                task = data.get('task', {})
                task_id = task.get('id', '')
                slug = task.get('slug', '')

                if task_id:
                    self.existing_task_ids.add(task_id)

                if slug:
                    self.slug_to_ulid[slug] = task_id

            except Exception as e:
                self.stats["errors"].append(f"Error reading {task_file}: {e}")

        if self.verbose:
            print(f"Loaded {len(self.existing_task_ids)} existing tasks")
            print(f"Loaded {len(self.slug_to_ulid)} slug->ULID mappings")

    def _standalone_exists(self, task_id: str) -> bool:
        """Check if a standalone task file already exists."""
        if task_id in self.existing_task_ids:
            return True

        # Also check by file existence
        task_file = self.tasks_dir / f"{task_id}.yaml"
        return task_file.exists()

    def convert_to_standalone(
        self,
        embedded: Dict,
        sprint_id: str,
        track_id: str,
        roadmap_id: str,
        new_ulid: str,
        slug: Optional[str]
    ) -> Dict:
        """
        Convert embedded task format to standalone format.

        Args:
            embedded: Embedded task dict from sprint file
            sprint_id: Sprint ULID
            track_id: Track ULID
            roadmap_id: Roadmap ID
            new_ulid: ULID for the task (may be same as original or newly generated)
            slug: Original slug ID if applicable
        """
        # Handle estimated effort -> estimated_tokens conversion
        estimated_tokens = embedded.get('estimated_tokens', 10000)
        if isinstance(estimated_tokens, str):
            effort_str = estimated_tokens.lower()
            if 'day' in effort_str:
                try:
                    days = int(effort_str.split()[0])
                    estimated_tokens = days * 1000
                except:
                    estimated_tokens = 10000
            else:
                estimated_tokens = 10000

        # Get title from various possible fields
        title = embedded.get('title') or embedded.get('name', 'Untitled Task')

        # Get timestamps
        created = embedded.get('created')
        if not created:
            created = datetime.now(timezone.utc).isoformat()

        completed = embedded.get('completed')
        started = embedded.get('started')
        status = embedded.get('status', 'not_started')

        # If status is completed but no completed timestamp, set one
        if status == 'completed' and not completed:
            completed = datetime.now(timezone.utc).isoformat()

        # Build standalone task structure
        standalone = {
            'id': new_ulid,
            'sprint_id': sprint_id,
            'track_id': track_id,
            'roadmap_id': roadmap_id,
            'task_type': embedded.get('task_type', 'development'),
            'title': title,
            'description': embedded.get('description', ''),
            'status': status,
            'blocked': embedded.get('blocked', False),
            'created': created,
            'started': started,
            'completed': completed,
            'assigned_agent': embedded.get('assigned_agent'),
            'priority': embedded.get('priority', 'medium'),
            'phase_label': embedded.get('phase_label'),
            'estimated_tokens': estimated_tokens,
            'actual_tokens': embedded.get('actual_tokens'),
            'complexity': embedded.get('complexity', 'medium'),
            'gate_info': embedded.get('gate_info'),
            'audit_results': embedded.get('audit_results'),
            'dependencies': [],
            'blocked_by': embedded.get('blocked_by', []),
            'depends_on': embedded.get('depends_on', []),
            'depended_on_by': [],
            'deliverables': embedded.get('deliverables', []),
            'commits': embedded.get('commits', []),
            'metadata': {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'token_efficiency': None,
                'duration_hours': None
            },
            'criteria': embedded.get('criteria', []),
            'sequence': embedded.get('sequence', 1),
        }

        # Add slug if we have one
        if slug:
            standalone['slug'] = slug

        # Add parent_ref pointing to sprint
        standalone['parent_ref'] = sprint_id

        return standalone

    def extract_from_sprint(self, sprint_file: Path) -> int:
        """
        Extract tasks from a single sprint file.

        Args:
            sprint_file: Path to sprint YAML file

        Returns:
            Number of tasks extracted
        """
        try:
            with open(sprint_file) as f:
                data = yaml.safe_load(f)
        except Exception as e:
            self.stats["errors"].append(f"Error reading {sprint_file}: {e}")
            return 0

        sprint = data.get('sprint', {})
        embedded_tasks = sprint.get('tasks', [])

        if not embedded_tasks:
            return 0

        sprint_id = sprint.get('id', '')
        track_id = sprint.get('track_id', '')
        roadmap_id = sprint.get('roadmap_id', 'vibey-framework-v2')

        if not sprint_id:
            self.stats["errors"].append(f"Sprint {sprint_file} has no ID")
            return 0

        extracted = 0

        for task in embedded_tasks:
            task_id = task.get('id', '')

            if not task_id:
                self.stats["tasks_skipped_no_id"] += 1
                continue

            # Check if already exists as standalone
            if self._standalone_exists(task_id):
                self.stats["tasks_skipped_existing"] += 1
                continue

            # Determine ULID and slug
            if is_ulid(task_id):
                new_ulid = task_id
                slug = task.get('slug')
            else:
                # Legacy slug ID - need to generate ULID
                # First check if we have an existing mapping
                if task_id in self.slug_to_ulid:
                    new_ulid = self.slug_to_ulid[task_id]
                else:
                    # Generate new ULID
                    try:
                        from ulid import ULID
                        new_ulid = str(ULID())
                    except ImportError:
                        # Fallback - use timestamp-based ID
                        import time
                        new_ulid = f"01{int(time.time() * 1000):024X}"[:26]

                    self.slug_to_ulid[task_id] = new_ulid
                slug = task_id

            # Convert to standalone format
            standalone = self.convert_to_standalone(
                task, sprint_id, track_id, roadmap_id, new_ulid, slug
            )

            if not self.dry_run:
                # Ensure tasks directory exists
                self.tasks_dir.mkdir(parents=True, exist_ok=True)

                # Write task file
                task_file = self.tasks_dir / f"{new_ulid}.yaml"
                with open(task_file, 'w') as f:
                    yaml.dump({'task': standalone}, f, default_flow_style=False,
                              sort_keys=False, allow_unicode=True)

                if self.verbose:
                    print(f"  Created: {task_file.name}")

            extracted += 1

        return extracted

    def extract_all(self) -> Dict:
        """
        Extract all embedded tasks from all sprint files.

        Returns:
            Stats dictionary
        """
        print("=" * 70)
        print("Embedded Task Extractor")
        print("=" * 70)
        print()

        if self.dry_run:
            print("DRY RUN MODE - No files will be created")
        else:
            print("EXECUTION MODE - Files will be created")
        print()

        # Load existing mappings
        print("Loading existing task mappings...")
        self.load_existing_mappings()
        print()

        # Scan all sprint files
        print(f"Scanning sprints in: {self.sprints_dir}")

        if not self.sprints_dir.exists():
            print(f"ERROR: Sprints directory not found: {self.sprints_dir}")
            return self.stats

        for sprint_file in sorted(self.sprints_dir.glob("*.yaml")):
            if sprint_file.name.startswith('.'):
                continue

            self.stats["sprints_scanned"] += 1

            # Check if has embedded tasks
            try:
                with open(sprint_file) as f:
                    data = yaml.safe_load(f)
                embedded = data.get('sprint', {}).get('tasks', [])
            except:
                embedded = []

            if embedded:
                self.stats["sprints_with_embedded"] += 1

                if self.verbose:
                    print(f"\n{sprint_file.name}: {len(embedded)} embedded tasks")

                extracted = self.extract_from_sprint(sprint_file)
                self.stats["tasks_extracted"] += extracted

        # Save slug mapping
        if not self.dry_run and self.slug_to_ulid:
            mapping_file = self.roadmap_dir / "context" / "task_slug_mapping.json"
            mapping_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_file, 'w') as f:
                json.dump(self.slug_to_ulid, f, indent=2, sort_keys=True)
            print(f"\nSaved slug mapping to: {mapping_file}")

        # Print summary
        print()
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"  Sprints scanned: {self.stats['sprints_scanned']}")
        print(f"  Sprints with embedded tasks: {self.stats['sprints_with_embedded']}")
        print(f"  Tasks extracted: {self.stats['tasks_extracted']}")
        print(f"  Tasks skipped (already exist): {self.stats['tasks_skipped_existing']}")
        print(f"  Tasks skipped (no ID): {self.stats['tasks_skipped_no_id']}")

        if self.stats["errors"]:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for err in self.stats["errors"][:10]:
                print(f"  - {err}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print()

        return self.stats


def extract_embedded_tasks(
    roadmap_dir: Path,
    dry_run: bool = True,
    verbose: bool = True
) -> Dict:
    """
    Main entry point for extracting embedded tasks.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        dry_run: If True, don't create files
        verbose: If True, print detailed output

    Returns:
        Stats dictionary
    """
    extractor = EmbeddedTaskExtractor(
        roadmap_dir=roadmap_dir,
        dry_run=dry_run,
        verbose=verbose
    )
    return extractor.extract_all()
