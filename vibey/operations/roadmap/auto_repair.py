"""
Auto-Repair Module for Roadmap Issues

Automatically fixes common roadmap integrity issues:
- Progress counter mismatches
- Broken references (with confirmation)
- Orphaned tasks (with suggestions)

Author: Vibey Framework
Created: 2025-11-21
Sprint: Post-Sprint 1 Enhancement
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any

from vibey.operations.roadmap.advanced_validator import (
    ProgressMismatch,
    BrokenReference,
    AdvancedValidationReport
)


# ============================================================================
# Auto-Repair Functions
# ============================================================================

def repair_progress_counters(
    mismatches: List[ProgressMismatch],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Auto-repair progress counter mismatches.

    Args:
        mismatches: List of ProgressMismatch objects to fix
        dry_run: If True, show what would be fixed without applying changes

    Returns:
        Dictionary with repair results
    """
    results = {
        'total': len(mismatches),
        'repaired': 0,
        'failed': 0,
        'errors': []
    }

    for mismatch in mismatches:
        if not mismatch.can_auto_fix:
            results['failed'] += 1
            results['errors'].append(f"Cannot auto-fix {mismatch.entity_id}")
            continue

        try:
            # Load the file
            file_path = Path(mismatch.entity_file)

            if not file_path.exists():
                results['failed'] += 1
                results['errors'].append(f"File not found: {file_path}")
                continue

            with open(file_path) as f:
                data = yaml.safe_load(f)

            # Update progress counters based on entity type
            if mismatch.entity_type == 'sprint':
                if 'sprint' in data and 'progress' in data['sprint']:
                    data['sprint']['progress']['tasks_completed'] = mismatch.actual_completed
                    data['sprint']['progress']['tasks_total'] = mismatch.actual_total

            elif mismatch.entity_type == 'track':
                if 'track' in data and 'progress' in data['track']:
                    data['track']['progress']['sprints_completed'] = mismatch.actual_completed
                    data['track']['progress']['sprints_total'] = mismatch.actual_total

            if not dry_run:
                # Write back to file
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

            results['repaired'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Error fixing {mismatch.entity_id}: {e}")

    return results


def remove_broken_references(
    broken_refs: List[BrokenReference],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Remove broken task references.

    Args:
        broken_refs: List of BrokenReference objects to fix
        dry_run: If True, show what would be fixed without applying changes

    Returns:
        Dictionary with repair results
    """
    results = {
        'total': len(broken_refs),
        'removed': 0,
        'failed': 0,
        'errors': []
    }

    # Group by task file to minimize I/O
    refs_by_file: Dict[str, List[BrokenReference]] = {}
    for ref in broken_refs:
        if ref.task_file not in refs_by_file:
            refs_by_file[ref.task_file] = []
        refs_by_file[ref.task_file].append(ref)

    for task_file, refs in refs_by_file.items():
        try:
            file_path = Path(task_file)

            if not file_path.exists():
                results['failed'] += len(refs)
                results['errors'].append(f"File not found: {file_path}")
                continue

            with open(file_path) as f:
                data = yaml.safe_load(f)

            if 'task' not in data:
                results['failed'] += len(refs)
                results['errors'].append(f"Invalid task file: {file_path}")
                continue

            task = data['task']
            modified = False

            # Remove broken references from each field
            for ref in refs:
                field = ref.field
                missing_id = ref.missing_id

                if field == 'blocks':
                    blocks = task.get('blocks', [])
                    original_len = len(blocks)
                    task['blocks'] = [
                        b for b in blocks
                        if not (isinstance(b, dict) and b.get('target_id') == missing_id)
                    ]
                    if len(task['blocks']) < original_len:
                        modified = True
                        results['removed'] += 1

                elif field in ['depends_on', 'blocked_by', 'depended_on_by']:
                    field_list = task.get(field, [])
                    if missing_id in field_list:
                        task[field] = [x for x in field_list if x != missing_id]
                        modified = True
                        results['removed'] += 1

            if modified and not dry_run:
                # Write back to file
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

        except Exception as e:
            results['failed'] += len(refs)
            results['errors'].append(f"Error fixing {task_file}: {e}")

    return results


# ============================================================================
# Batch Repair
# ============================================================================

def auto_repair_all(
    report: AdvancedValidationReport,
    fix_progress: bool = True,
    fix_references: bool = False,  # Requires confirmation
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Auto-repair all fixable issues in the report.

    Args:
        report: AdvancedValidationReport with detected issues
        fix_progress: Fix progress counter mismatches (safe)
        fix_references: Remove broken references (requires caution)
        dry_run: If True, show what would be fixed without applying

    Returns:
        Dictionary with overall repair results
    """
    results = {
        'progress_counters': None,
        'broken_references': None,
        'total_fixed': 0,
        'total_failed': 0
    }

    # Fix progress counters (safe operation)
    if fix_progress and report.progress_mismatches:
        print(f"Repairing {len(report.progress_mismatches)} progress counter mismatches...")
        progress_results = repair_progress_counters(report.progress_mismatches, dry_run=dry_run)
        results['progress_counters'] = progress_results
        results['total_fixed'] += progress_results['repaired']
        results['total_failed'] += progress_results['failed']

        if not dry_run:
            print(f"  ✅ Repaired: {progress_results['repaired']}")
            if progress_results['failed'] > 0:
                print(f"  ❌ Failed: {progress_results['failed']}")

    # Remove broken references (requires caution)
    if fix_references and report.broken_references:
        print(f"Removing {len(report.broken_references)} broken references...")
        ref_results = remove_broken_references(report.broken_references, dry_run=dry_run)
        results['broken_references'] = ref_results
        results['total_fixed'] += ref_results['removed']
        results['total_failed'] += ref_results['failed']

        if not dry_run:
            print(f"  ✅ Removed: {ref_results['removed']}")
            if ref_results['failed'] > 0:
                print(f"  ❌ Failed: {ref_results['failed']}")

    return results
