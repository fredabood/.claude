"""
YAML dumper for roadmap objects.

Saves Python dataclass objects to YAML files.
"""

from datetime import datetime
from pathlib import Path
from typing import Union

import yaml

from ..models import (
    Roadmap,
    Track,
    Sprint,
    Task,
)


def _format_datetime(dt: Union[datetime, None]) -> Union[str, None]:
    """Format datetime to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat() + 'Z' if dt.tzinfo is None else dt.isoformat()


def _create_slug(name: str) -> str:
    """Create a URL-friendly slug from a name."""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:100]  # Max length


def _save_task_hierarchical(task: Task, sprint_dir: Path):
    """
    Save a task to its own directory in hierarchical structure.

    Args:
        task: Task object to save
        sprint_dir: Parent sprint directory
    """
    # Create task directory (use task ID as slug for now)
    task_slug = task.id  # Simple: use ID as directory name
    task_dir = sprint_dir / task_slug
    task_dir.mkdir(parents=True, exist_ok=True)

    # Create task.yaml file
    task_file = task_dir / "task.yaml"

    # Build task data (same format as legacy, but wrapped in {'task': ...})
    task_data = {
        'id': task.id,
        'sprint_id': task.sprint_id,
        'track_id': task.track_id,
        'roadmap_id': task.roadmap_id,
        'task_type': task.task_type.value,
        'title': task.title,
        'description': task.description,
        'status': task.status.value,
        'blocked': task.blocked,
        'created': _format_datetime(task.created),
        'started': _format_datetime(task.started),
        'completed': _format_datetime(task.completed),
        'assigned_agent': task.assigned_agent,
        'priority': task.priority.value,
        'phase_label': task.phase_label,
        'estimated_tokens': task.estimated_tokens,
        'actual_tokens': task.actual_tokens,
        'complexity': task.complexity.value,
    }

    # Add gate_info if present
    if task.gate_info:
        task_data['gate_info'] = {
            'blocks_status': task.gate_info.blocks_status,
            'threshold': task.gate_info.threshold,
            'is_blocking': task.gate_info.is_blocking,
            'score': task.gate_info.score,
        }
    else:
        task_data['gate_info'] = None

    # Add audit_results if present
    if task.audit_results:
        task_data['audit_results'] = {
            'issues_found': task.audit_results.issues_found,
            'issues_fixed': task.audit_results.issues_fixed,
            'recommendations': task.audit_results.recommendations,
        }
    else:
        task_data['audit_results'] = None

    # Add dependencies
    task_data['dependencies'] = [
        {
            'type': d.type.value,
            'target_id': d.target_id,
            'target_status': d.target_status,
            'reason': d.reason,
        }
        for d in task.dependencies
    ]

    # Add blocks
    task_data['blocks'] = [
        {
            'type': b.type.value,
            'target_id': b.target_id,
            'at_status': b.target_status,
            'reason': b.reason,
        }
        for b in task.blocks
    ]

    # Add blockers
    task_data['blocked_by'] = [
        {
            'dependency_id': b.dependency_id,
            'dependency_type': b.dependency_type,
            'current_status': b.current_status.value if hasattr(b.current_status, 'value') else b.current_status,
            'required_status': b.required_status.value if hasattr(b.required_status, 'value') else b.required_status,
            'blocking_since': _format_datetime(b.blocking_since),
            'estimated_resolution': _format_datetime(b.estimated_resolution),
        }
        for b in task.blocked_by
    ]

    # Add depends_on (cached dependency status)
    task_data['depends_on'] = [
        {
            'blocker_id': d.blocker_id,
            'blocker_type': d.blocker_type,
            'required_status': d.required_status.value if hasattr(d.required_status, 'value') else d.required_status,
            'current_status': d.current_status.value if hasattr(d.current_status, 'value') else d.current_status,
            'blocks_transition_to': d.blocks_transition_to,
            'last_checked': _format_datetime(d.last_checked),
        }
        for d in task.depends_on
    ]

    # Add depended_on_by (reverse index)
    task_data['depended_on_by'] = task.depended_on_by

    # Add deliverables
    task_data['deliverables'] = [
        {
            'type': d.type.value,
            'paths': d.paths,
        }
        for d in task.deliverables
    ]

    # Add commits
    task_data['commits'] = [
        {
            'sha': c.sha,
            'message': c.message,
            'date': _format_datetime(c.date),
            'author': c.author,
        }
        for c in task.commits
    ]

    # Add metadata
    task_data['metadata'] = {
        'last_updated': _format_datetime(task.metadata.last_updated),
        'token_efficiency': task.metadata.token_efficiency,
        'duration_hours': task.metadata.duration_hours,
    }

    # Write to file (wrapped in {'task': ...})
    data = {'task': task_data}
    with open(task_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_roadmap(roadmap: Roadmap, file_path: Union[str, Path]):
    """
    Save a roadmap to YAML file.

    Args:
        roadmap: Roadmap object
        file_path: Path to save roadmap.yaml
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'roadmap': {
            'id': roadmap.id,
            'name': roadmap.name,
            'version': roadmap.version,
            'version_strategy': {
                'major_on': roadmap.version_strategy.major_on.value,
                'minor_on': roadmap.version_strategy.minor_on.value,
                'patch_on': roadmap.version_strategy.patch_on.value,
            },
            'status': roadmap.status.value,
            'blocked': roadmap.blocked,
            'created': _format_datetime(roadmap.created),
            'started': _format_datetime(roadmap.started),
            'target_completion': _format_datetime(roadmap.target_completion),
            'completed': _format_datetime(roadmap.completed),
            'deployed': _format_datetime(roadmap.deployed),
            'progress': {
                'tracks_total': roadmap.progress.tracks_total,
                'tracks_completed': roadmap.progress.tracks_completed,
                'sprints_total': roadmap.progress.sprints_total,
                'sprints_completed': roadmap.progress.sprints_completed,
                'tasks_total': roadmap.progress.tasks_total,
                'tasks_completed': roadmap.progress.tasks_completed,
                'completion_percent': roadmap.progress.completion_percent,
            },
            'tracks': [
                {
                    'id': t.id,
                    'name': t.name,
                    'status': t.status.value,
                    'priority': t.priority.value,
                }
                for t in roadmap.tracks
            ],
            'dependencies': [
                {
                    'type': d.type,
                    'name': d.name,
                    'status': d.status,
                    'required_for': d.required_for,
                }
                for d in roadmap.dependencies
            ],
            'blocked_by': [
                {
                    'dependency_id': b.dependency_id,
                    'dependency_type': b.dependency_type,
                    'current_status': b.current_status.value if hasattr(b.current_status, 'value') else b.current_status,
                    'required_status': b.required_status.value if hasattr(b.required_status, 'value') else b.required_status,
                    'blocking_since': _format_datetime(b.blocking_since),
                    'estimated_resolution': _format_datetime(b.estimated_resolution),
                }
                for b in roadmap.blocked_by
            ],
            'version_history': [
                {
                    'version': vh.version,
                    'date': _format_datetime(vh.date),
                    'milestone': vh.milestone,
                    'git_tag': vh.git_tag,
                    'description': vh.description,
                }
                for vh in roadmap.version_history
            ],
            'deployed_platforms': [
                {
                    'platform': p.platform,
                    'context_window': p.context_window,
                    'deployed_at': p.deployed_at,  # Unix timestamp (integer)
                    'deployed_by': p.deployed_by,
                    'primary': p.primary,
                }
                for p in roadmap.deployed_platforms
            ],
            'standards': [
                {
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'type': s.type.value,
                    'enforcement': s.enforcement.value,
                    'validation': s.validation,
                    'enabled': s.enabled,
                    'created': _format_datetime(s.created),
                    'overrides': [
                        {
                            'overridden_at': _format_datetime(o.overridden_at),
                            'overridden_by': o.overridden_by,
                            'reason': o.reason,
                            'target_id': o.target_id,
                            'expires_at': _format_datetime(o.expires_at),
                        }
                        for o in s.overrides
                    ],
                }
                for s in roadmap.standards
            ],
            'activity_log': [
                {
                    'timestamp': _format_datetime(al.timestamp),
                    'type': al.type.value,
                    'description': al.description,
                    'context': al.context,
                }
                for al in roadmap.activity_log
            ],
            'metadata': {
                'created_by': roadmap.metadata.created_by,
                'framework_version': roadmap.metadata.framework_version,
                'schema_version': roadmap.metadata.schema_version,
                'last_updated': _format_datetime(roadmap.metadata.last_updated),
                'purpose': roadmap.metadata.purpose,
                'description': roadmap.metadata.description,
            },
        }
    }

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_track(track: Track, file_path: Union[str, Path]):
    """
    Save a track to YAML file.

    Args:
        track: Track object
        file_path: Path to save track YAML file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'track': {
            'id': track.id,
            'name': track.name,
            'roadmap_id': track.roadmap_id,
            'status': track.status.value,
            'blocked': track.blocked,
            'priority': track.priority.value,
            'created': _format_datetime(track.created),
            'started': _format_datetime(track.started),
            'completed': _format_datetime(track.completed),
            'estimated_duration': track.estimated_duration,
            'progress': {
                'sprints_total': track.progress.sprints_total,
                'sprints_completed': track.progress.sprints_completed,
                'tasks_total': track.progress.tasks_total,
                'tasks_completed': track.progress.tasks_completed,
                'completion_percent': track.progress.completion_percent,
            },
            'sprints': [
                {
                    'id': s.id,
                    'name': s.name,
                    'status': s.status.value,
                    'estimated_duration': s.estimated_duration,
                    'tasks_count': s.tasks_count,
                    'started': _format_datetime(s.started),
                }
                for s in track.sprints
            ],
            'dependencies': [
                {
                    'type': d.type.value,
                    'target_id': d.target_id,
                    'target_status': d.target_status,
                    'reason': d.reason,
                    'optional': d.optional,
                }
                for d in track.dependencies
            ],
            'blocks': [
                {
                    'type': b.type.value,
                    'target_id': b.target_id,
                    'at_status': b.target_status,
                    'reason': b.reason,
                }
                for b in track.blocks
            ],
            'blocked_by': [
                {
                    'dependency_id': b.dependency_id,
                    'dependency_type': b.dependency_type,
                    'current_status': b.current_status.value if hasattr(b.current_status, 'value') else b.current_status,
                    'required_status': b.required_status.value if hasattr(b.required_status, 'value') else b.required_status,
                    'blocking_since': _format_datetime(b.blocking_since),
                    'estimated_resolution': _format_datetime(b.estimated_resolution),
                }
                for b in track.blocked_by
            ],
            'depends_on': [
                {
                    'blocker_id': d.blocker_id,
                    'blocker_type': d.blocker_type,
                    'required_status': d.required_status.value if hasattr(d.required_status, 'value') else d.required_status,
                    'current_status': d.current_status.value if hasattr(d.current_status, 'value') else d.current_status,
                    'blocks_transition_to': d.blocks_transition_to,
                    'last_checked': _format_datetime(d.last_checked),
                }
                for d in track.depends_on
            ],
            'depended_on_by': track.depended_on_by,
            'quality_gates': [
                {
                    'name': qg.name,
                    'threshold': qg.threshold,
                    'blocking': qg.blocking,
                    'status': qg.status.value,
                    'description': qg.description,
                    'score': qg.score,
                }
                for qg in track.quality_gates
            ],
            'assigned_agents': track.assigned_agents,
            'deliverables': track.deliverables,
            'strategic_value': track.strategic_value,
            'commits': [
                {
                    'sprint_id': c.sprint_id,
                    'sha': c.sha,
                    'message': c.message,
                    'date': _format_datetime(c.date),
                    'author': c.author,
                }
                for c in track.commits
            ],
            'standards': [
                {
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'type': s.type.value,
                    'enforcement': s.enforcement.value,
                    'validation': s.validation,
                    'enabled': s.enabled,
                    'created': _format_datetime(s.created),
                    'overrides': [
                        {
                            'overridden_at': _format_datetime(o.overridden_at),
                            'overridden_by': o.overridden_by,
                            'reason': o.reason,
                            'target_id': o.target_id,
                            'expires_at': _format_datetime(o.expires_at),
                        }
                        for o in s.overrides
                    ],
                }
                for s in track.standards
            ],
            'metadata': {
                'created_by': track.metadata.created_by,
                'last_updated': _format_datetime(track.metadata.last_updated),
                'design_doc': track.metadata.design_doc,
                'implementation_plan': track.metadata.implementation_plan,
                'notes': track.metadata.notes,
            },
        }
    }

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_sprint(sprint: Sprint, file_path: Union[str, Path]):
    """
    Save a sprint to YAML file.

    Args:
        sprint: Sprint object
        file_path: Path to save sprint YAML file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'sprint': {
            'id': sprint.id,
            'name': sprint.name,
            'track_id': sprint.track_id,
            'roadmap_id': sprint.roadmap_id,
            'status': sprint.status.value,
            'blocked': sprint.blocked,
            'blocked_reason': sprint.blocked_reason,
            'created': _format_datetime(sprint.created),
            'started': _format_datetime(sprint.started),
            'completion_gate_check_at': _format_datetime(sprint.completion_gate_check_at),
            'completed': _format_datetime(sprint.completed),
            'production_gate_check_at': _format_datetime(sprint.production_gate_check_at),
            'production_ready_at': _format_datetime(sprint.production_ready_at),
            'deployed_at': _format_datetime(sprint.deployed_at),
            'progress': {
                'development_tasks_total': sprint.progress.development_tasks_total,
                'development_tasks_completed': sprint.progress.development_tasks_completed,
                'completion_gate_tasks_total': sprint.progress.completion_gate_tasks_total,
                'completion_gate_tasks_completed': sprint.progress.completion_gate_tasks_completed,
                'production_gate_tasks_total': sprint.progress.production_gate_tasks_total,
                'production_gate_tasks_completed': sprint.progress.production_gate_tasks_completed,
                'tasks_total': sprint.progress.tasks_total,
                'tasks_completed': sprint.progress.tasks_completed,
                'completion_percent': sprint.progress.completion_percent,
            },
            'tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'status': t.status.value,
                    'task_type': t.task_type.value,
                    'gate_info': {
                        'blocks_status': t.gate_info.blocks_status,
                        'threshold': t.gate_info.threshold,
                        'is_blocking': t.gate_info.is_blocking,
                        'score': t.gate_info.score,
                    } if t.gate_info else None,
                }
                for t in sprint.tasks
            ],
            'development_gates': [
                {
                    'type': dg.type.value,
                    'target_id': dg.target_id,
                    'target_status': dg.target_status,
                    'reason': dg.reason,
                }
                for dg in sprint.development_gates
            ],
            'blocks': [
                {
                    'type': b.type.value,
                    'target_id': b.target_id,
                    'at_status': b.target_status,
                    'reason': b.reason,
                }
                for b in sprint.blocks
            ],
            'blocked_by': [
                {
                    'dependency_id': b.dependency_id,
                    'dependency_type': b.dependency_type,
                    'current_status': b.current_status.value if hasattr(b.current_status, 'value') else b.current_status,
                    'required_status': b.required_status.value if hasattr(b.required_status, 'value') else b.required_status,
                    'blocking_since': _format_datetime(b.blocking_since),
                    'estimated_resolution': _format_datetime(b.estimated_resolution),
                }
                for b in sprint.blocked_by
            ],
            'depends_on': [
                {
                    'blocker_id': d.blocker_id,
                    'blocker_type': d.blocker_type,
                    'required_status': d.required_status.value if hasattr(d.required_status, 'value') else d.required_status,
                    'current_status': d.current_status.value if hasattr(d.current_status, 'value') else d.current_status,
                    'blocks_transition_to': d.blocks_transition_to,
                    'last_checked': _format_datetime(d.last_checked),
                }
                for d in sprint.depends_on
            ],
            'depended_on_by': sprint.depended_on_by,
            'plan_file': sprint.plan_file,
            'deliverables': sprint.deliverables,
            'description': sprint.description,
            'goal': sprint.goal,
            'success_criteria': sprint.success_criteria,
            'risks': sprint.risks,
            'notes': sprint.notes,
            'assigned_agents': sprint.assigned_agents,
            'quality_gates': sprint.quality_gates,
            'commits': [
                {
                    'task_id': c.task_id,
                    'sha': c.sha,
                    'message': c.message,
                    'date': _format_datetime(c.date),
                    'author': c.author,
                }
                for c in sprint.commits
            ],
            'standards': [
                {
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'type': s.type.value,
                    'enforcement': s.enforcement.value,
                    'validation': s.validation,
                    'enabled': s.enabled,
                    'created': _format_datetime(s.created),
                    'overrides': [
                        {
                            'overridden_at': _format_datetime(o.overridden_at),
                            'overridden_by': o.overridden_by,
                            'reason': o.reason,
                            'target_id': o.target_id,
                            'expires_at': _format_datetime(o.expires_at),
                        }
                        for o in s.overrides
                    ],
                }
                for s in sprint.standards
            ],
            'metadata': {
                'last_updated': _format_datetime(sprint.metadata.last_updated),
                'estimated_duration': sprint.metadata.estimated_duration,
                'actual_duration': sprint.metadata.actual_duration,
                'estimated_tokens': sprint.metadata.estimated_tokens,
                'actual_tokens': sprint.metadata.actual_tokens,
                'agents_used': sprint.metadata.agents_used,
            },
        }
    }

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_tasks(tasks: list[Task], file_path: Union[str, Path]):
    """
    Save tasks to YAML file or hierarchical directory structure.

    Supports both formats:
    - Legacy: single file with {'tasks': [...]} (when file_path is a file)
    - Hierarchical: individual task.yaml files in task subdirectories (when file_path is a directory)

    Args:
        tasks: List of Task objects
        file_path: Path to save tasks YAML file or sprint directory
    """
    file_path = Path(file_path)

    # Detect format based on whether file_path is/should be a directory
    # If it exists and is a directory, use hierarchical format
    # Otherwise use legacy format
    is_hierarchical = file_path.exists() and file_path.is_dir()

    if is_hierarchical:
        # Save each task to its own directory
        for task in tasks:
            _save_task_hierarchical(task, file_path)
        return

    # Legacy flat format
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'tasks': []
    }

    for task in tasks:
        task_data = {
            'id': task.id,
            'sprint_id': task.sprint_id,
            'track_id': task.track_id,
            'roadmap_id': task.roadmap_id,
            'task_type': task.task_type.value,
            'title': task.title,
            'description': task.description,
            'status': task.status.value,
            'blocked': task.blocked,
            'created': _format_datetime(task.created),
            'started': _format_datetime(task.started),
            'completed': _format_datetime(task.completed),
            'assigned_agent': task.assigned_agent,
            'priority': task.priority.value,
            'phase_label': task.phase_label,
            'estimated_tokens': task.estimated_tokens,
            'actual_tokens': task.actual_tokens,
            'complexity': task.complexity.value,
        }

        # Add gate_info if present
        if task.gate_info:
            task_data['gate_info'] = {
                'blocks_status': task.gate_info.blocks_status,
                'threshold': task.gate_info.threshold,
                'is_blocking': task.gate_info.is_blocking,
                'score': task.gate_info.score,
            }
        else:
            task_data['gate_info'] = None

        # Add audit_results if present
        if task.audit_results:
            task_data['audit_results'] = {
                'issues_found': task.audit_results.issues_found,
                'issues_fixed': task.audit_results.issues_fixed,
                'recommendations': task.audit_results.recommendations,
            }
        else:
            task_data['audit_results'] = None

        # Add dependencies
        task_data['dependencies'] = [
            {
                'type': d.type.value,
                'target_id': d.target_id,
                'target_status': d.target_status,
                'reason': d.reason,
            }
            for d in task.dependencies
        ]

        # Add blocks
        task_data['blocks'] = [
            {
                'type': b.type.value,
                'target_id': b.target_id,
                'at_status': b.target_status,
                'reason': b.reason,
            }
            for b in task.blocks
        ]

        # Add blockers
        task_data['blocked_by'] = [
            {
                'dependency_id': b.dependency_id,
                'dependency_type': b.dependency_type,
                'current_status': b.current_status.value if hasattr(b.current_status, 'value') else b.current_status,
                'required_status': b.required_status.value if hasattr(b.required_status, 'value') else b.required_status,
                'blocking_since': _format_datetime(b.blocking_since),
                'estimated_resolution': _format_datetime(b.estimated_resolution),
            }
            for b in task.blocked_by
        ]

        # Add depends_on (cached dependency status)
        task_data['depends_on'] = [
            {
                'blocker_id': d.blocker_id,
                'blocker_type': d.blocker_type,
                'required_status': d.required_status.value if hasattr(d.required_status, 'value') else d.required_status,
                'current_status': d.current_status.value if hasattr(d.current_status, 'value') else d.current_status,
                'blocks_transition_to': d.blocks_transition_to,
                'last_checked': _format_datetime(d.last_checked),
            }
            for d in task.depends_on
        ]

        # Add depended_on_by (reverse index)
        task_data['depended_on_by'] = task.depended_on_by

        # Add deliverables
        task_data['deliverables'] = [
            {
                'type': d.type.value,
                'paths': d.paths,
            }
            for d in task.deliverables
        ]

        # Add commits
        commits_data = []
        for c in task.commits:
            commit_dict = {
                'sha': c.sha,
                'message': c.message,
                'date': _format_datetime(c.date),
                'author': c.author,
                'platform': c.platform,  # REQUIRED field
                'submitted_at': c.submitted_at,  # Unix timestamp (integer)
            }
            commits_data.append(commit_dict)
        task_data['commits'] = commits_data

        # Add metadata
        task_data['metadata'] = {
            'last_updated': _format_datetime(task.metadata.last_updated),
            'token_efficiency': task.metadata.token_efficiency,
            'duration_hours': task.metadata.duration_hours,
        }

        data['tasks'].append(task_data)

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


# =============================================================================
# AUDIT TRAIL DUMPER
# =============================================================================

def save_audit_trail(
    entries: List[dict],
    file_path: Union[str, Path],
    metadata: Optional[dict] = None,
):
    """
    Save audit trail to YAML file.

    Args:
        entries: List of audit trail entry dictionaries
        file_path: Path to save audit-trail.yaml file
        metadata: Optional metadata dictionary (if None, will be computed)
    """
    from datetime import datetime, timezone

    file_path = Path(file_path)

    # Compute metadata if not provided
    if metadata is None:
        metadata = {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'total_entries': len(entries),
        }

    data = {
        'audit_log': [
            {
                'timestamp': e['timestamp'],
                'object_type': e['object_type'],
                'object_id': e['object_id'],
                'field': e['field'],
                'old_value': e.get('old_value'),
                'new_value': e.get('new_value'),
                'changed_by': e['changed_by'],
                'reason': e['reason'],
                'commit': e.get('commit'),
                'source': e.get('source', 'cli'),
            }
            for e in entries
        ],
        'metadata': metadata,
    }

    with open(file_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
