"""
YAML dumper for roadmap objects.

Saves Python dataclass objects to YAML files.

Supports both nested (v1) and flat (v2) directory structures:
- Nested: .vibey/roadmap/{track}/{sprint}/{task}/task.yaml
- Flat: .vibey/roadmap/tracks/{ulid}.yaml, sprints/{ulid}.yaml, tasks/{ulid}.yaml
"""

from datetime import datetime
from pathlib import Path
from typing import Union, Optional, TYPE_CHECKING

import yaml

from ..models import (
    Roadmap,
    Track,
    Sprint,
    Task,
)

if TYPE_CHECKING:
    from ...cli.roadmap_lib.filesystem import FileSystemManager


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

    # Add gate_info if present (handle both dict and object)
    if task.gate_info:
        if isinstance(task.gate_info, dict):
            task_data['gate_info'] = task.gate_info
        else:
            task_data['gate_info'] = {
                'blocks_status': task.gate_info.blocks_status,
                'threshold': task.gate_info.threshold,
                'is_blocking': task.gate_info.is_blocking,
                'score': getattr(task.gate_info, 'score', None),
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
                    'gate_info': t.gate_info if isinstance(t.gate_info, dict) else ({
                        'blocks_status': t.gate_info.blocks_status,
                        'threshold': t.gate_info.threshold,
                        'is_blocking': t.gate_info.is_blocking,
                        'score': getattr(t.gate_info, 'score', None),
                    } if t.gate_info else None),
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


def save_task(task: Task, file_path: Union[str, Path]):
    """
    Save a single task to YAML file (supports nested and flat structures).

    This function only writes the specified task, avoiding reformatting
    sibling task files when used with hierarchical directory structure.

    Args:
        task: Task object to save
        file_path: Path to save task
            - Directory: saves to {file_path}/{task.id}/task.yaml (nested)
            - File named task.yaml: saves single task (nested)
            - File in tasks/ directory: saves single task (flat)
            - Other file: legacy multi-task format
    """
    file_path = Path(file_path)

    # If path is a directory (sprint dir), save to task subdirectory (nested structure)
    if file_path.is_dir():
        _save_task_hierarchical(task, file_path)
        return

    # If path is a file, determine format based on location and name
    # Flat structure: tasks/{ulid}.yaml or tasks/{slug}.yaml
    if file_path.parent.name == 'tasks' and file_path.suffix == '.yaml':
        _save_single_task_file(task, file_path)
    # Nested structure: {track}/{sprint}/{task}/task.yaml
    elif file_path.name == 'task.yaml':
        # Direct task.yaml path - save the single task
        _save_single_task_file(task, file_path)
    else:
        # Legacy format - load all tasks, update this one, save all
        # This maintains backward compatibility with flat task files
        from .yaml_loader import load_tasks as _load_tasks
        tasks = _load_tasks(file_path)
        for i, t in enumerate(tasks):
            if t.id == task.id:
                tasks[i] = task
                break
        save_tasks(tasks, file_path)


def _save_single_task_file(task: Task, file_path: Path):
    """
    Save a single task to a specific task.yaml file.

    Args:
        task: Task object to save
        file_path: Path to task.yaml file
    """
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
        if isinstance(task.gate_info, dict):
            task_data['gate_info'] = task.gate_info
        else:
            task_data['gate_info'] = {
                'blocks_status': task.gate_info.blocks_status,
                'threshold': task.gate_info.threshold,
                'is_blocking': task.gate_info.is_blocking,
                'score': getattr(task.gate_info, 'score', None),
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

    # Add blocked_by
    task_data['blocked_by'] = [
        {
            'type': bb.blocker_type.value,
            'blocker_id': bb.blocker_id,
            'required_status': bb.required_status.value,
        }
        for bb in task.blocked_by
    ]

    # Add depends_on (handles both Dependency and DependencyStatus objects)
    task_data['depends_on'] = [
        {
            'blocker_type': getattr(d, 'blocker_type', None) or getattr(d, 'entity_type', {}).value if hasattr(getattr(d, 'entity_type', None), 'value') else getattr(d, 'blocker_type', 'task'),
            'blocker_id': getattr(d, 'blocker_id', None) or getattr(d, 'entity_id', ''),
            'required_status': d.required_status if isinstance(d.required_status, str) else d.required_status.value if hasattr(d.required_status, 'value') else str(d.required_status),
            'current_status': getattr(d, 'current_status', None),
            'blocks_transition_to': getattr(d, 'blocks_transition_to', None),
        }
        for d in task.depends_on
    ]

    # Add depended_on_by (empty list stored for consistency)
    task_data['depended_on_by'] = []

    # Add deliverables
    task_data['deliverables'] = []

    # Add commits
    task_data['commits'] = []

    # Add metadata
    task_data['metadata'] = {
        'last_updated': _format_datetime(task.metadata.last_updated) if hasattr(task.metadata, 'last_updated') else None,
        'token_efficiency': task.metadata.token_efficiency if hasattr(task.metadata, 'token_efficiency') else None,
        'duration_hours': task.metadata.duration_hours if hasattr(task.metadata, 'duration_hours') else None,
    }

    data = {'task': task_data}

    file_path.parent.mkdir(parents=True, exist_ok=True)
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

        # Add gate_info if present (handle both dict and object)
        if task.gate_info:
            if isinstance(task.gate_info, dict):
                task_data['gate_info'] = task.gate_info
            else:
                task_data['gate_info'] = {
                    'blocks_status': task.gate_info.blocks_status,
                    'threshold': task.gate_info.threshold,
                    'is_blocking': task.gate_info.is_blocking,
                    'score': getattr(task.gate_info, 'score', None),
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


# =============================================================================
# V2 PYDANTIC MODEL DUMPERS
# =============================================================================
# These functions serialize the new Pydantic ticket models (TaskTicket, SprintTicket,
# TrackTicket, RoadmapTicket) to YAML format.
#
# Key differences from v1 dumpers:
# 1. Use _local suffix for local content fields (commits_local, not commits)
# 2. Serialize criteria (unified blocking approach)
# 3. Exclude computed/aggregated fields
# 4. Always output v2 format (gradual migration)
# =============================================================================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.ticket.domain import (
        RoadmapTicket,
        TrackTicket,
        SprintTicket,
        TaskTicket,
    )
    from ..models.ticket.completable import Criterion
    from ..models.ticket.ticket import GitCommit


def _dump_git_commit(commit: "GitCommit") -> dict:
    """
    Serialize a GitCommit to dict for YAML output.

    Args:
        commit: GitCommit Pydantic model

    Returns:
        Dictionary suitable for YAML serialization
    """
    return {
        'sha': commit.sha,
        'message': commit.message,
        'date': _format_datetime(commit.date),
        'author': commit.author,
        'platform': commit.platform,
        'submitted_at': _format_datetime(commit.submitted_at),
        'completes_tickets': sorted(commit.completes_tickets) if commit.completes_tickets else [],
        'files_added': sorted(commit.files_added) if commit.files_added else [],
        'files_modified': sorted(commit.files_modified) if commit.files_modified else [],
        'files_deleted': sorted(commit.files_deleted) if commit.files_deleted else [],
        'creates_artifacts': sorted(commit.creates_artifacts) if commit.creates_artifacts else [],
        'modifies_artifacts': sorted(commit.modifies_artifacts) if commit.modifies_artifacts else [],
        'deletes_artifacts': sorted(commit.deletes_artifacts) if commit.deletes_artifacts else [],
    }


def _dump_criterion(criterion: "Criterion") -> dict:
    """
    Serialize a Criterion to dict for YAML output.

    Args:
        criterion: Criterion Pydantic model

    Returns:
        Dictionary suitable for YAML serialization
    """
    target = criterion.target
    target_data = {
        'type': target.type.value,
    }

    # Serialize target-specific fields based on type
    if hasattr(target, 'completable_id'):
        # CompletableTarget
        target_data['completable_id'] = target.completable_id
        target_data['required_status'] = target.required_status.value
    elif hasattr(target, 'paths'):
        # FileExistsTarget
        target_data['paths'] = sorted(target.paths)
        target_data['all_required'] = target.all_required
        target_data['deliverable_type'] = target.deliverable_type.value
    elif hasattr(target, 'metric_name'):
        # ThresholdTarget
        target_data['metric_name'] = target.metric_name
        target_data['threshold'] = target.threshold
        target_data['comparison'] = target.comparison.value
        if hasattr(target, 'current_value') and target.current_value is not None:
            target_data['current_value'] = target.current_value
    elif hasattr(target, 'verified_by'):
        # ManualTarget
        target_data['verified_by'] = target.verified_by
        if hasattr(target, 'verified_at') and target.verified_at:
            target_data['verified_at'] = _format_datetime(target.verified_at)

    return {
        'id': criterion.id,
        'description': criterion.description,
        'blocks_transition_to': criterion.blocks_transition_to.value,
        'target': target_data,
        'required': criterion.required,
    }


def dump_task_ticket(task: "TaskTicket") -> dict:
    """
    Serialize a TaskTicket to dict for YAML output (v2 format).

    Args:
        task: TaskTicket Pydantic model

    Returns:
        Dictionary with 'task' root key, suitable for YAML serialization
    """
    # Import here to avoid circular imports
    from ..models.ticket.domain import TaskTicket

    task_data = {
        # Identity
        'id': task.id,
        'name': task.name,
        'description': task.description,

        # Format marker
        'format_version': 'v2',
        'ticket_type': 'task',

        # Hierarchy
        'parent_ref': task.parent_ref,

        # Lifecycle
        'status': task.status.value,
        'created_at': _format_datetime(task.created_at),
        'started_at': _format_datetime(task.started_at),
        'completed_at': _format_datetime(task.completed_at),
        'updated_at': _format_datetime(task.updated_at),

        # Assignment
        'assigned_agents': sorted(task.assigned_agents) if task.assigned_agents else [],
        'priority': task.priority.value,

        # Criteria (unified blocking)
        'criteria': [_dump_criterion(c) for c in task.criteria],

        # Local content (use _local suffix to be explicit)
        'commits_local': [_dump_git_commit(c) for c in task.commits],
        'requirements_local': [
            {
                'id': r.id,
                'description': r.description,
                'validation': r.validation,
                'source_ticket_id': r.source_ticket_id,
            }
            for r in task.requirements_local
        ],

        # Estimation
        'estimated_duration': task.estimated_duration,
        'deferred': task.deferred,

        # Task-specific fields
        'task_type_detail': task.task_type_detail.value if task.task_type_detail else None,
        'estimated_tokens': task.estimated_tokens,
        'actual_tokens': task.actual_tokens,
        'complexity': task.complexity.value if task.complexity else None,
        'phase_label': task.phase_label,
    }

    # Add gate_info if present (handle both dict and object)
    if task.gate_info:
        if isinstance(task.gate_info, dict):
            task_data['gate_info'] = task.gate_info
        else:
            blocks_status = task.gate_info.blocks_status
            task_data['gate_info'] = {
                'is_blocking': task.gate_info.is_blocking,
                'threshold': task.gate_info.threshold,
                'score': getattr(task.gate_info, 'score', None),
                'blocks_status': blocks_status.value if hasattr(blocks_status, 'value') else blocks_status,
            }
    else:
        task_data['gate_info'] = None

    # Add audit_results if present
    if task.audit_results:
        if isinstance(task.audit_results, dict):
            task_data['audit_results'] = task.audit_results
        else:
            task_data['audit_results'] = {
                'issues_found': task.audit_results.issues_found,
                'issues_fixed': task.audit_results.issues_fixed,
                'recommendations': task.audit_results.recommendations,
            }
    else:
        task_data['audit_results'] = None

    # Metadata
    task_data['metadata'] = task.metadata if task.metadata else {}

    return {'task': task_data}


def dump_sprint_ticket(sprint: "SprintTicket") -> dict:
    """
    Serialize a SprintTicket to dict for YAML output (v2 format).

    Args:
        sprint: SprintTicket Pydantic model

    Returns:
        Dictionary with 'sprint' root key, suitable for YAML serialization
    """
    from ..models.ticket.domain import SprintTicket

    sprint_data = {
        # Identity
        'id': sprint.id,
        'name': sprint.name,
        'description': sprint.description,

        # Format marker
        'format_version': 'v2',
        'ticket_type': 'sprint',

        # Hierarchy
        'parent_ref': sprint.parent_ref,

        # Lifecycle
        'status': sprint.status.value,
        'created_at': _format_datetime(sprint.created_at),
        'started_at': _format_datetime(sprint.started_at),
        'completed_at': _format_datetime(sprint.completed_at),
        'updated_at': _format_datetime(sprint.updated_at),

        # Assignment
        'assigned_agents': sorted(sprint.assigned_agents) if sprint.assigned_agents else [],
        'priority': sprint.priority.value,

        # Criteria (unified blocking)
        'criteria': [_dump_criterion(c) for c in sprint.criteria],

        # Local content
        'commits_local': [_dump_git_commit(c) for c in sprint.commits],
        'requirements_local': [
            {
                'id': r.id,
                'description': r.description,
                'validation': r.validation,
                'source_ticket_id': r.source_ticket_id,
            }
            for r in sprint.requirements_local
        ],

        # Estimation
        'estimated_duration': sprint.estimated_duration,
        'deferred': sprint.deferred,

        # Sprint-specific fields
        'plan_file': sprint.plan_file,
        'goal': sprint.goal,
        'success_criteria': sprint.success_criteria_text if sprint.success_criteria_text else [],
        'development_gates': [
            {
                'name': g.name,
                'description': g.description,
                'status': g.status.value,
                'checked_at': _format_datetime(g.checked_at),
            }
            for g in sprint.development_gates
        ] if sprint.development_gates else [],
    }

    # Metadata
    sprint_data['metadata'] = sprint.metadata if sprint.metadata else {}

    return {'sprint': sprint_data}


def dump_track_ticket(track: "TrackTicket") -> dict:
    """
    Serialize a TrackTicket to dict for YAML output (v2 format).

    Args:
        track: TrackTicket Pydantic model

    Returns:
        Dictionary with 'track' root key, suitable for YAML serialization
    """
    from ..models.ticket.domain import TrackTicket

    track_data = {
        # Identity
        'id': track.id,
        'name': track.name,
        'description': track.description,

        # Format marker
        'format_version': 'v2',
        'ticket_type': 'track',

        # Hierarchy
        'parent_ref': track.parent_ref,

        # Lifecycle
        'status': track.status.value,
        'created_at': _format_datetime(track.created_at),
        'started_at': _format_datetime(track.started_at),
        'completed_at': _format_datetime(track.completed_at),
        'updated_at': _format_datetime(track.updated_at),

        # Assignment
        'assigned_agents': sorted(track.assigned_agents) if track.assigned_agents else [],
        'priority': track.priority.value,

        # Criteria (unified blocking)
        'criteria': [_dump_criterion(c) for c in track.criteria],

        # Local content
        'commits_local': [_dump_git_commit(c) for c in track.commits],
        'requirements_local': [
            {
                'id': r.id,
                'description': r.description,
                'validation': r.validation,
                'source_ticket_id': r.source_ticket_id,
            }
            for r in track.requirements_local
        ],

        # Estimation
        'estimated_duration': track.estimated_duration,
        'deferred': track.deferred,

        # Track-specific fields
        'strategic_value': track.strategic_value if track.strategic_value else [],
    }

    # Metadata
    track_data['metadata'] = track.metadata if track.metadata else {}

    return {'track': track_data}


def dump_roadmap_ticket(roadmap: "RoadmapTicket") -> dict:
    """
    Serialize a RoadmapTicket to dict for YAML output (v2 format).

    Args:
        roadmap: RoadmapTicket Pydantic model

    Returns:
        Dictionary with 'roadmap' root key, suitable for YAML serialization
    """
    from ..models.ticket.domain import RoadmapTicket

    roadmap_data = {
        # Identity
        'id': roadmap.id,
        'name': roadmap.name,
        'description': roadmap.description,

        # Format marker
        'format_version': 'v2',
        'ticket_type': 'roadmap',

        # Hierarchy (roadmap has no parent)
        'parent_ref': None,

        # Lifecycle
        'status': roadmap.status.value,
        'created_at': _format_datetime(roadmap.created_at),
        'started_at': _format_datetime(roadmap.started_at),
        'completed_at': _format_datetime(roadmap.completed_at),
        'updated_at': _format_datetime(roadmap.updated_at),

        # Assignment
        'assigned_agents': sorted(roadmap.assigned_agents) if roadmap.assigned_agents else [],
        'priority': roadmap.priority.value,

        # Criteria (unified blocking)
        'criteria': [_dump_criterion(c) for c in roadmap.criteria],

        # Local content
        'commits_local': [_dump_git_commit(c) for c in roadmap.commits],
        'requirements_local': [
            {
                'id': r.id,
                'description': r.description,
                'validation': r.validation,
                'source_ticket_id': r.source_ticket_id,
            }
            for r in roadmap.requirements_local
        ],

        # Estimation
        'estimated_duration': roadmap.estimated_duration,
        'deferred': roadmap.deferred,

        # Roadmap-specific fields
        'version': roadmap.version,
        'target_completion': _format_datetime(roadmap.target_completion),
        'deployed_at': _format_datetime(roadmap.deployed_at),
    }

    # Version strategy
    if roadmap.version_strategy:
        roadmap_data['version_strategy'] = {
            'scheme': roadmap.version_strategy.scheme,
            'auto_bump': roadmap.version_strategy.auto_bump,
            'major_triggers': roadmap.version_strategy.major_triggers,
            'minor_triggers': roadmap.version_strategy.minor_triggers,
            'patch_triggers': roadmap.version_strategy.patch_triggers,
        }
    else:
        roadmap_data['version_strategy'] = None

    # Version history
    roadmap_data['version_history'] = [
        {
            'version': vh.version,
            'released_at': _format_datetime(vh.released_at),
            'milestone': vh.milestone,
            'notes': vh.notes,
        }
        for vh in roadmap.version_history
    ] if roadmap.version_history else []

    # Deployed platforms
    roadmap_data['deployed_platforms'] = [
        {
            'platform': p.platform,
            'context_window': p.context_window,
            'deployed_at': _format_datetime(p.deployed_at),
            'primary': p.primary,
            'version': p.version,
        }
        for p in roadmap.deployed_platforms
    ] if roadmap.deployed_platforms else []

    # Activity log
    roadmap_data['activity_log'] = [
        {
            'timestamp': _format_datetime(a.timestamp),
            'action': a.action.value,
            'ticket_id': a.ticket_id,
            'actor': a.actor,
            'details': a.details,
            'context': a.context,
        }
        for a in roadmap.activity_log
    ] if roadmap.activity_log else []

    # Metadata
    roadmap_data['metadata'] = roadmap.metadata if roadmap.metadata else {}

    return {'roadmap': roadmap_data}


def save_task_ticket(task: "TaskTicket", file_path: Union[str, Path]):
    """
    Save a TaskTicket to YAML file (v2 format).

    Args:
        task: TaskTicket Pydantic model
        file_path: Path to save task.yaml
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = dump_task_ticket(task)

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_sprint_ticket(sprint: "SprintTicket", file_path: Union[str, Path]):
    """
    Save a SprintTicket to YAML file (v2 format).

    Args:
        sprint: SprintTicket Pydantic model
        file_path: Path to save sprint.yaml
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = dump_sprint_ticket(sprint)

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_track_ticket(track: "TrackTicket", file_path: Union[str, Path]):
    """
    Save a TrackTicket to YAML file (v2 format).

    Args:
        track: TrackTicket Pydantic model
        file_path: Path to save track.yaml
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = dump_track_ticket(track)

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def save_roadmap_ticket(roadmap: "RoadmapTicket", file_path: Union[str, Path]):
    """
    Save a RoadmapTicket to YAML file (v2 format).

    Args:
        roadmap: RoadmapTicket Pydantic model
        file_path: Path to save roadmap.yaml
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = dump_roadmap_ticket(roadmap)

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

# ============================================================================
# Helper Functions for Automatic Path Resolution
# ============================================================================

def save_track_auto(track: Track, fs: "FileSystemManager"):
    """
    Save track with automatic path resolution (supports both structures).

    Args:
        track: Track object to save
        fs: FileSystemManager instance (detects structure automatically)
    """
    track_path = fs.get_track_path(track.id)
    save_track(track, track_path)


def save_sprint_auto(sprint: Sprint, fs: "FileSystemManager"):
    """
    Save sprint with automatic path resolution (supports both structures).

    Args:
        sprint: Sprint object to save
        fs: FileSystemManager instance (detects structure automatically)
    """
    sprint_path = fs.get_sprint_path(sprint.id)
    save_sprint(sprint, sprint_path)


def save_task_auto(task: Task, fs: "FileSystemManager"):
    """
    Save task with automatic path resolution (supports both structures).

    For nested structure: Uses sprint directory, saves to task subdirectory
    For flat structure: Uses tasks/{task_id}.yaml path directly

    Args:
        task: Task object to save
        fs: FileSystemManager instance (detects structure automatically)
    """
    if fs.structure_format == "flat":
        # Flat structure: get direct task file path
        task_path = fs.get_task_path(task.id)
        save_task(task, task_path)
    else:
        # Nested structure: get sprint directory, let save_task create subdirectory
        sprint_dir = fs.get_tasks_path(task.sprint_id)
        save_task(task, sprint_dir)


def save_roadmap_auto(roadmap: Roadmap, fs: "FileSystemManager"):
    """
    Save roadmap with automatic path resolution.

    Args:
        roadmap: Roadmap object to save
        fs: FileSystemManager instance
    """
    roadmap_path = fs.get_roadmap_path()
    save_roadmap(roadmap, roadmap_path)
