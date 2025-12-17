"""
V1 to V2 YAML Format Migration Script.

Converts roadmap YAML files from v1 format (blocked_by, depends_on, deliverables)
to v2 format (unified criteria array).

Usage:
    python -m vibey.roadmap.serialization.v1_to_v2

See: .vibey/roadmap/context/sprints/unified-arch-4/V2_YAML_SCHEMA.md
"""

import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


logger = logging.getLogger(__name__)


# =============================================================================
# FORMAT DETECTION
# =============================================================================


def is_v1_format(data: Dict[str, Any]) -> bool:
    """
    Detect if YAML data uses v1 format.

    V1 indicators:
    - Has blocked_by array
    - Has depends_on array with blocker_id format
    - Has deliverables array
    - Has blocked field stored
    - Does NOT have criteria array

    Args:
        data: Entity data (roadmap/track/sprint/task contents)

    Returns:
        True if v1 format, False if already v2
    """
    # V2 has criteria - already migrated
    if 'criteria' in data:
        return False

    # V1 indicators
    v1_fields = ['blocked_by', 'depends_on', 'deliverables', 'development_gates']
    for field in v1_fields:
        if field in data and isinstance(data.get(field), list) and len(data[field]) > 0:
            return True

    # Has blocked field stored (v2 computes it)
    if 'blocked' in data:
        return True

    return False


def is_v2_format(data: Dict[str, Any]) -> bool:
    """Check if already in v2 format."""
    return 'criteria' in data


# =============================================================================
# CRITERION GENERATION
# =============================================================================


def _generate_criterion_id(prefix: str, index: int) -> str:
    """Generate a human-readable criterion ID."""
    return f"{prefix}-{index:03d}"


def convert_dependency_to_criterion(
    dep: Dict[str, Any],
    entity_id: str,
    index: int
) -> Dict[str, Any]:
    """
    Convert a depends_on entry to a criterion.

    V1 format:
        - blocker_id: sqlite-backend-6
          blocker_type: track
          required_status: completed
          description: Requires sqlite-backend model classes
          status: resolved

    V2 format:
        - id: dep-001
          description: Requires sqlite-backend model classes
          required: true
          blocks_transition_to: in_progress
          target:
            type: completable
            completable_id: <ULID>
            required_status: completed
    """
    blocker_id = dep.get('blocker_id', '')
    description = dep.get('description') or f"Depends on {blocker_id}"

    # Determine if this is a start blocker or completion blocker
    # By default, dependencies block starting (in_progress)
    blocks_transition = 'in_progress'

    criterion = {
        'id': _generate_criterion_id('dep', index),
        'description': description,
        'required': True,
        'blocks_transition_to': blocks_transition,
        'target': {
            'type': 'completable',
            'completable_id': blocker_id,  # Will be resolved to ULID during migration
            'required_status': dep.get('required_status', 'completed'),
        }
    }

    # Preserve resolution status
    if dep.get('status') == 'resolved':
        criterion['is_met'] = True
        criterion['last_checked'] = datetime.now(timezone.utc).isoformat()

    return criterion


def convert_blocker_to_criterion(
    blocker: Dict[str, Any],
    entity_id: str,
    index: int
) -> Dict[str, Any]:
    """
    Convert a blocked_by entry to a criterion.

    V1 format:
        - target_id: sqlite-backend-6-task-003
          reason: Must complete first

    V2 format:
        - id: blk-001
          description: Must complete first
          required: true
          blocks_transition_to: in_progress
          target:
            type: completable
            completable_id: <ULID>
            required_status: completed
    """
    # Handle both string blockers and dict blockers
    if isinstance(blocker, str):
        target_id = blocker
        reason = f"Blocked by {blocker}"
    else:
        target_id = blocker.get('target_id', blocker.get('blocker_id', ''))
        reason = blocker.get('reason', blocker.get('description', f"Blocked by {target_id}"))

    return {
        'id': _generate_criterion_id('blk', index),
        'description': reason,
        'required': True,
        'blocks_transition_to': 'in_progress',
        'target': {
            'type': 'completable',
            'completable_id': target_id,
            'required_status': 'completed',
        }
    }


def convert_deliverable_to_criterion(
    deliverable: Dict[str, Any],
    entity_id: str,
    index: int
) -> Dict[str, Any]:
    """
    Convert a deliverables entry to a criterion.

    V1 format:
        - path: vibey/roadmap/models/ticket.py
          type: code
          description: Ticket model implementation

    V2 format:
        - id: del-001
          description: Ticket model implementation
          required: true
          blocks_transition_to: completed
          target:
            type: file_exists
            paths:
              - vibey/roadmap/models/ticket.py
            deliverable_type: code
    """
    path = deliverable.get('path', '')
    description = deliverable.get('description') or f"Deliverable: {path}"
    del_type = deliverable.get('type', 'code')

    return {
        'id': _generate_criterion_id('del', index),
        'description': description,
        'required': True,
        'blocks_transition_to': 'completed',
        'target': {
            'type': 'file_exists',
            'paths': [path] if path else [],
            'all_required': True,
            'deliverable_type': del_type,
        }
    }


def convert_gate_to_criterion(
    gate: Dict[str, Any],
    entity_id: str,
    index: int
) -> Dict[str, Any]:
    """
    Convert a development_gates/quality_gates entry to a criterion.

    V1 format:
        - name: unit_tests
          description: All unit tests must pass
          command: pytest tests/unit/
          status: pending

    V2 format:
        - id: gate-001
          description: All unit tests must pass
          required: true
          blocks_transition_to: completed
          target:
            type: test_passes
            test_command: pytest tests/unit/
            pass_threshold: 100
    """
    name = gate.get('name', f'gate-{index}')
    description = gate.get('description') or f"Quality gate: {name}"
    command = gate.get('command', gate.get('test_command', ''))

    return {
        'id': _generate_criterion_id('gate', index),
        'description': description,
        'required': True,
        'blocks_transition_to': 'completed',
        'target': {
            'type': 'test_passes',
            'test_command': command,
            'pass_threshold': 100,
        }
    }


# =============================================================================
# ENTITY CONVERSION
# =============================================================================


def convert_entity_to_v2(data: Dict[str, Any], entity_type: str) -> Tuple[Dict[str, Any], int]:
    """
    Convert a single entity from v1 to v2 format.

    Args:
        data: Entity data dictionary
        entity_type: 'roadmap', 'track', 'sprint', or 'task'

    Returns:
        Tuple of (converted data, number of criteria created)
    """
    if is_v2_format(data):
        return data, 0

    converted = dict(data)
    criteria = []
    criterion_counts = {'dep': 0, 'blk': 0, 'del': 0, 'gate': 0}
    entity_id = data.get('id', 'unknown')

    # Convert depends_on to criteria
    for dep in data.get('depends_on', []):
        if isinstance(dep, dict) and dep:
            criterion_counts['dep'] += 1
            criteria.append(convert_dependency_to_criterion(
                dep, entity_id, criterion_counts['dep']
            ))

    # Convert blocked_by to criteria
    for blocker in data.get('blocked_by', []):
        if blocker:  # Skip empty strings
            criterion_counts['blk'] += 1
            criteria.append(convert_blocker_to_criterion(
                blocker, entity_id, criterion_counts['blk']
            ))

    # Convert deliverables to criteria
    for deliverable in data.get('deliverables', []):
        if isinstance(deliverable, dict) and deliverable.get('path'):
            criterion_counts['del'] += 1
            criteria.append(convert_deliverable_to_criterion(
                deliverable, entity_id, criterion_counts['del']
            ))

    # Convert development_gates to criteria
    for gate in data.get('development_gates', []):
        if isinstance(gate, dict) and gate:
            criterion_counts['gate'] += 1
            criteria.append(convert_gate_to_criterion(
                gate, entity_id, criterion_counts['gate']
            ))

    # Convert quality_gates to criteria (if present)
    for gate in data.get('quality_gates', []):
        if isinstance(gate, dict) and gate:
            criterion_counts['gate'] += 1
            criteria.append(convert_gate_to_criterion(
                gate, entity_id, criterion_counts['gate']
            ))

    # Add criteria array (even if empty - signals v2 format)
    converted['criteria'] = criteria

    # Remove v1 fields
    v1_fields_to_remove = [
        'blocked',  # Now computed
        'blocked_by',  # Converted to criteria
        'depends_on',  # Converted to criteria (but keep for now as reference)
        'deliverables',  # Converted to criteria (but keep for now as reference)
        'development_gates',  # Converted to criteria
        'quality_gates',  # Converted to criteria
        'blocks',  # Computed from reverse lookup
        'depended_on_by',  # Computed from reverse lookup
    ]

    # For now, keep depends_on and deliverables for debugging/rollback
    # They'll be removed in a later cleanup phase
    for field in ['blocked', 'development_gates', 'quality_gates', 'blocks', 'depended_on_by']:
        converted.pop(field, None)

    # Add sequence field if not present
    if 'sequence' not in converted:
        # Extract sequence from slug if possible (e.g., "task-003" -> 3)
        slug = data.get('slug', '')
        match = re.search(r'(\d+)$', slug.replace('-', ''))
        if match:
            converted['sequence'] = int(match.group(1))

    return converted, len(criteria)


def convert_file_to_v2(file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Convert a single YAML file from v1 to v2 format.

    Args:
        file_path: Path to YAML file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (was_converted, criteria_count)
    """
    try:
        with open(file_path, 'r') as f:
            raw_data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return False, 0

    if not raw_data or not isinstance(raw_data, dict):
        return False, 0

    # Get the entity key and data
    entity_key = next(iter(raw_data.keys()), None)
    if entity_key not in ('roadmap', 'track', 'sprint', 'task'):
        return False, 0

    entity_data = raw_data[entity_key]

    # Check if already v2
    if is_v2_format(entity_data):
        return False, 0

    # Check if needs conversion
    if not is_v1_format(entity_data):
        return False, 0

    # Convert
    converted_data, criteria_count = convert_entity_to_v2(entity_data, entity_key)

    if dry_run:
        logger.info(f"Would convert {file_path}: {criteria_count} criteria")
        return True, criteria_count

    # Write back
    try:
        raw_data[entity_key] = converted_data
        with open(file_path, 'w') as f:
            yaml.dump(raw_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Converted {file_path}: {criteria_count} criteria")
        return True, criteria_count
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        return False, 0


# =============================================================================
# MIGRATION RUNNER
# =============================================================================


def migrate_roadmap_directory(
    roadmap_dir: Path,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate all YAML files in a roadmap directory to v2 format.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        dry_run: If True, don't write changes

    Returns:
        Migration statistics
    """
    stats = {
        'files_scanned': 0,
        'files_converted': 0,
        'criteria_created': 0,
        'errors': [],
        'by_type': {
            'roadmap': {'scanned': 0, 'converted': 0},
            'track': {'scanned': 0, 'converted': 0},
            'sprint': {'scanned': 0, 'converted': 0},
            'task': {'scanned': 0, 'converted': 0},
        }
    }

    # Find all YAML files
    yaml_files = list(roadmap_dir.glob('**/*.yaml'))

    for file_path in yaml_files:
        # Skip backup directories
        if 'backup' in str(file_path).lower():
            continue

        # Skip sample_code directories
        if 'sample_code' in str(file_path) or 'context' in str(file_path):
            continue

        stats['files_scanned'] += 1

        # Determine entity type from file contents
        try:
            with open(file_path, 'r') as f:
                raw_data = yaml.safe_load(f)
            if not raw_data:
                continue

            entity_key = next(iter(raw_data.keys()), None)
            if entity_key in stats['by_type']:
                stats['by_type'][entity_key]['scanned'] += 1
        except Exception:
            continue

        # Convert file
        was_converted, criteria_count = convert_file_to_v2(file_path, dry_run)

        if was_converted:
            stats['files_converted'] += 1
            stats['criteria_created'] += criteria_count
            if entity_key in stats['by_type']:
                stats['by_type'][entity_key]['converted'] += 1

    return stats


def main():
    """Main entry point for v1 to v2 migration."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate roadmap YAML files from v1 to v2 format')
    parser.add_argument('--roadmap-dir', '-d', type=Path, default=Path('.vibey/roadmap'),
                        help='Path to roadmap directory')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    roadmap_dir = args.roadmap_dir
    if not roadmap_dir.exists():
        logger.error(f"Roadmap directory not found: {roadmap_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"V1 to V2 YAML Format Migration")
    print(f"{'='*60}")
    print(f"Directory: {roadmap_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    stats = migrate_roadmap_directory(roadmap_dir, args.dry_run)

    print(f"\n{'='*60}")
    print("Migration Summary")
    print(f"{'='*60}")
    print(f"Files scanned:    {stats['files_scanned']}")
    print(f"Files converted:  {stats['files_converted']}")
    print(f"Criteria created: {stats['criteria_created']}")
    print()
    print("By entity type:")
    for entity_type, counts in stats['by_type'].items():
        print(f"  {entity_type:8s}: {counts['scanned']:4d} scanned, {counts['converted']:4d} converted")

    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN - No changes were made")
        print("Run without --dry-run to apply changes")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
