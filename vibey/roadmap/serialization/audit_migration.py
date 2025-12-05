"""
Audit fields migration to ThresholdTarget criteria and markdown reports.

Migrates audit-specific fields from YAML to:
- ThresholdTarget criteria (for scores like integrity_score)
- Markdown report files + FileExistsTarget (for audit_results)
- Standard timestamps (audit_completed → completed_at)

Aggregates like average_integrity_score become computed SQL queries.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


# ==============================================================================
# Templates
# ==============================================================================

AUDIT_REPORT_TEMPLATE = """# Audit Report: {entity_id}

**Date:** {date}
**Integrity Score:** {score}/100

## Summary

{summary}

## Findings

{findings}

## Issues

{issues}

## Recommendations

{recommendations}
"""


# ==============================================================================
# Migration Functions
# ==============================================================================

def migrate_integrity_score(
    legacy_data: Dict[str, Any],
    entity_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Migrate integrity_score to ThresholdTarget criterion.

    Args:
        legacy_data: Dict containing integrity_score field
        entity_id: ID of the entity for criterion ID generation

    Returns:
        Criterion dict or None if no integrity_score
    """
    score = legacy_data.get('integrity_score')
    if score is None:
        return None

    # Convert to float to ensure numeric type
    try:
        score_value = float(score)
    except (TypeError, ValueError):
        logger.warning(f"Invalid integrity_score value: {score}")
        return None

    criterion = {
        'id': f'{entity_id}-integrity',
        'description': 'Integrity score meets threshold (>= 90%)',
        'target': {
            'type': 'threshold',
            'metric_name': 'integrity_score',
            'threshold': 90,
            'current_value': score_value,
            'comparison': 'gte',
        },
        'blocks_transition_to': 'completed',
        'required': True,
        'met': score_value >= 90,
    }

    return criterion


def migrate_audit_results(
    legacy_data: Dict[str, Any],
    entity_id: str,
    entity_dir: Path,
    dry_run: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Migrate audit_results to markdown file + FileExistsTarget criterion.

    Args:
        legacy_data: Dict containing audit_results field
        entity_id: ID of the entity
        entity_dir: Path to entity directory
        dry_run: If True, only report what would happen

    Returns:
        Tuple of (criterion dict or None, report file path or None)
    """
    results = legacy_data.get('audit_results')
    if results is None:
        return None, None

    # Determine report file path
    report_dir = entity_dir / 'context' / 'audits'
    report_file = report_dir / f'{entity_id}-audit.md'

    # Generate report content
    content = render_audit_report(entity_id, results)

    if not dry_run:
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file.write_text(content)
        logger.info(f"Created audit report: {report_file}")

    # Create criterion
    criterion = {
        'id': f'{entity_id}-audit-report',
        'description': 'Audit report generated',
        'target': {
            'type': 'file_exists',
            'paths': [str(report_file)],
            'deliverable_type': 'documentation',
        },
        'blocks_transition_to': 'completed',
        'required': True,
        'met': report_file.exists() if not dry_run else False,
    }

    return criterion, str(report_file)


def render_audit_report(entity_id: str, results: Any) -> str:
    """
    Render audit results to markdown format.

    Args:
        entity_id: ID of the entity being audited
        results: Audit results (dict, list, or string)

    Returns:
        Markdown-formatted audit report
    """
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Extract structured data if available
    if isinstance(results, dict):
        score = results.get('score', results.get('integrity_score', 'N/A'))
        summary = results.get('summary', 'Audit completed.')
        findings = results.get('findings', [])
        issues = results.get('issues', [])
        recommendations = results.get('recommendations', [])

        # Format findings
        if isinstance(findings, list):
            findings_str = '\n'.join(f'- {f}' for f in findings) or '- No findings'
        else:
            findings_str = str(findings)

        # Format issues
        if isinstance(issues, list):
            issues_str = '\n'.join(f'{i+1}. {issue}' for i, issue in enumerate(issues)) or 'No issues found.'
        else:
            issues_str = str(issues) if issues else 'No issues found.'

        # Format recommendations
        if isinstance(recommendations, list):
            recs_str = '\n'.join(f'- {r}' for r in recommendations) or '- None'
        else:
            recs_str = str(recommendations) if recommendations else '- None'

    elif isinstance(results, list):
        score = 'N/A'
        summary = 'Audit completed with findings.'
        findings_str = '\n'.join(f'- {r}' for r in results)
        issues_str = 'See findings above.'
        recs_str = '- Review and address findings'

    else:
        score = 'N/A'
        summary = str(results) if results else 'Audit completed.'
        findings_str = '- No structured findings available'
        issues_str = 'No issues documented.'
        recs_str = '- None'

    return AUDIT_REPORT_TEMPLATE.format(
        entity_id=entity_id,
        date=date_str,
        score=score,
        summary=summary,
        findings=findings_str,
        issues=issues_str,
        recommendations=recs_str,
    )


def migrate_audit_completed(
    legacy_data: Dict[str, Any],
) -> Optional[datetime]:
    """
    Migrate audit_completed to standard completed_at timestamp.

    Args:
        legacy_data: Dict containing audit_completed field

    Returns:
        datetime or None if no audit_completed
    """
    audit_completed = legacy_data.get('audit_completed')
    if audit_completed is None:
        return None

    # Handle datetime objects
    if isinstance(audit_completed, datetime):
        return audit_completed

    # Handle string timestamps
    if isinstance(audit_completed, str):
        try:
            # Try ISO format first
            if 'T' in audit_completed:
                return datetime.fromisoformat(audit_completed.replace('Z', '+00:00'))
            # Try date-only format
            return datetime.strptime(audit_completed, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning(f"Invalid audit_completed timestamp: {audit_completed}")
            return None

    return None


# ==============================================================================
# Batch Migration
# ==============================================================================

class AuditMigrationResult:
    """Result of audit field migration."""

    def __init__(self):
        self.criteria_added: List[Dict[str, Any]] = []
        self.reports_created: List[str] = []
        self.timestamps_migrated: List[str] = []
        self.errors: List[Tuple[str, str]] = []

    @property
    def total_criteria(self) -> int:
        return len(self.criteria_added)

    @property
    def total_reports(self) -> int:
        return len(self.reports_created)

    @property
    def total_timestamps(self) -> int:
        return len(self.timestamps_migrated)

    @property
    def total_errors(self) -> int:
        return len(self.errors)

    def add_criterion(self, criterion: Dict[str, Any]) -> None:
        self.criteria_added.append(criterion)

    def add_report(self, path: str) -> None:
        self.reports_created.append(path)

    def add_timestamp(self, entity_id: str) -> None:
        self.timestamps_migrated.append(entity_id)

    def add_error(self, entity_id: str, error: str) -> None:
        self.errors.append((entity_id, error))


def migrate_audit_fields(
    legacy_data: Dict[str, Any],
    entity_id: str,
    entity_dir: Path,
    dry_run: bool = False,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Migrate all audit-related fields for a single entity.

    Args:
        legacy_data: Dict containing audit fields
        entity_id: ID of the entity
        entity_dir: Path to entity directory
        dry_run: If True, only report what would happen

    Returns:
        Tuple of (list of criteria dicts, report path or None)
    """
    criteria = []
    report_path = None

    # Migrate integrity_score
    integrity_criterion = migrate_integrity_score(legacy_data, entity_id)
    if integrity_criterion:
        criteria.append(integrity_criterion)

    # Migrate audit_results
    audit_criterion, report_path = migrate_audit_results(
        legacy_data, entity_id, entity_dir, dry_run
    )
    if audit_criterion:
        criteria.append(audit_criterion)

    return criteria, report_path


def migrate_roadmap_audit_fields(
    roadmap_dir: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> AuditMigrationResult:
    """
    Migrate all audit fields from YAML files in the roadmap.

    Scans all YAML files and migrates:
    - integrity_score → ThresholdTarget criterion
    - audit_results → FileExistsTarget + markdown report
    - audit_completed → completed_at timestamp

    Args:
        roadmap_dir: Path to roadmap directory
        dry_run: If True, only report what would happen
        verbose: If True, log detailed progress

    Returns:
        AuditMigrationResult with migration details
    """
    import yaml

    result = AuditMigrationResult()

    # Find all task.yaml files (most likely to have audit fields)
    task_files = list(roadmap_dir.glob('*/*/*/task.yaml'))

    for task_file in task_files:
        try:
            with open(task_file, 'r') as f:
                data = yaml.safe_load(f)

            if not data or 'task' not in data:
                continue

            task_data = data['task']
            entity_id = task_data.get('id', task_file.parent.name)
            entity_dir = task_file.parent

            # Check if any audit fields exist
            has_audit_fields = (
                task_data.get('integrity_score') is not None or
                task_data.get('audit_results') is not None or
                task_data.get('audit_completed') is not None
            )

            if not has_audit_fields:
                continue

            # Migrate audit fields
            criteria, report_path = migrate_audit_fields(
                task_data, entity_id, entity_dir, dry_run
            )

            for criterion in criteria:
                result.add_criterion(criterion)

            if report_path:
                result.add_report(report_path)

            # Check for audit_completed
            if task_data.get('audit_completed'):
                result.add_timestamp(entity_id)

            if verbose:
                logger.info(f"Migrated audit fields for {entity_id}")

        except Exception as e:
            result.add_error(str(task_file), str(e))

    # Also check sprint.yaml files
    sprint_files = list(roadmap_dir.glob('*/*/sprint.yaml'))

    for sprint_file in sprint_files:
        try:
            with open(sprint_file, 'r') as f:
                data = yaml.safe_load(f)

            if not data or 'sprint' not in data:
                continue

            sprint_data = data['sprint']
            entity_id = sprint_data.get('id', sprint_file.parent.name)
            entity_dir = sprint_file.parent

            # Check if integrity_score exists
            if sprint_data.get('integrity_score') is not None:
                criterion = migrate_integrity_score(sprint_data, entity_id)
                if criterion:
                    result.add_criterion(criterion)

        except Exception as e:
            result.add_error(str(sprint_file), str(e))

    return result


def format_audit_migration_report(result: AuditMigrationResult, verbose: bool = False) -> str:
    """Format audit migration result for CLI output."""
    lines = []

    lines.append("\nAudit Migration Summary")
    lines.append("=" * 50)
    lines.append(f"Criteria added:      {result.total_criteria}")
    lines.append(f"Reports created:     {result.total_reports}")
    lines.append(f"Timestamps migrated: {result.total_timestamps}")
    lines.append(f"Errors:              {result.total_errors}")

    if verbose and result.criteria_added:
        lines.append("\nCriteria Added:")
        for c in result.criteria_added:
            lines.append(f"  + {c['id']}: {c['description']}")

    if verbose and result.reports_created:
        lines.append("\nReports Created:")
        for r in result.reports_created:
            lines.append(f"  + {r}")

    if result.errors:
        lines.append("\nErrors:")
        for entity_id, error in result.errors:
            lines.append(f"  ! {entity_id}: {error}")

    return '\n'.join(lines)
