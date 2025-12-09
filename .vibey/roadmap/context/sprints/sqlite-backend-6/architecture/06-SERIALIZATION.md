# Serialization & Migration

## YAML Format

### Task YAML Example

**Code:** [`sample_code/yaml/example_task.yaml`](../sample_code/yaml/example_task.yaml)

### Sprint YAML Example

**Code:** [`sample_code/yaml/example_sprint.yaml`](../sample_code/yaml/example_sprint.yaml)

---

## Migration Overview

**YAML File Types:** 4 (roadmap.yaml, track.yaml, sprint.yaml, task.yaml)
**Total Unique Fields:** ~85 across all types
**Fields with Direct Mapping:** ~60 (71%)
**Fields Now Computed (no storage):** ~10 (12%)
**Fields Migrated to Markdown:** ~10 (12%)
**Fields with Transformation Required:** ~5 (5%)
**Fields at Risk of Data Loss:** 0

---

## Field Mapping Tables

### Roadmap YAML → RoadmapTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `roadmap.id` | `RoadmapTicket.id` | Direct |
| `roadmap.name` | `RoadmapTicket.name` | Direct |
| `roadmap.version` | `RoadmapTicket.version` | Direct |
| `roadmap.status` | `RoadmapTicket.status` | Enum mapping |
| `roadmap.blocked` | Computed from `criteria` | No longer stored |
| `roadmap.created` | `RoadmapTicket.created_at` | Rename |
| `roadmap.tracks[]` | `criteria` with `CompletableTarget` | Children become criteria |
| `roadmap.dependencies` | `criteria` with `blocks_transition_to: in_progress` | Deps become criteria |
| `roadmap.progress` | Computed from `criteria` | No longer stored |
| `roadmap.standards` | `requirements_local[]` | Transformation |

### Track YAML → TrackTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `track.id` | `TrackTicket.id` | Direct |
| `track.name` | `TrackTicket.name` | Direct |
| `track.roadmap_id` | `TrackTicket.parent_ref` | Rename |
| `track.status` | `TrackTicket.status` | Enum mapping |
| `track.blocked` | Computed from `criteria` | No longer stored |
| `track.priority` | `TrackTicket.priority` | Direct |
| `track.sprints[]` | `criteria` with `CompletableTarget` | Children become criteria |
| `track.dependencies` | `criteria` with `blocks_transition_to: in_progress` | Deps become criteria |
| `track.blocks[]` | `v_reverse_dependencies` view | Computed |
| `track.quality_gates[]` | `criteria` with `ThresholdTarget` | Gates become criteria |
| `track.deliverables[]` | `criteria` with `FileExistsTarget` | Deliverables become criteria |

### Sprint YAML → SprintTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `sprint.id` | `SprintTicket.id` | Direct |
| `sprint.name` | `SprintTicket.name` | Direct |
| `sprint.track_id` | `SprintTicket.parent_ref` | Rename |
| `sprint.status` | `SprintTicket.status` | Enum mapping |
| `sprint.blocked` | Computed from `criteria` | No longer stored |
| `sprint.plan_file` | `SprintTicket.plan_file` | Direct |
| `sprint.tasks[]` | `criteria` with `CompletableTarget` | Children become criteria |
| `sprint.development_gates[]` | `criteria` with `blocks_transition_to: in_progress` | Gates become criteria |
| `sprint.deliverables[]` | `criteria` with `FileExistsTarget` | Deliverables become criteria |

### Task YAML → TaskTicket

| Legacy YAML Field | Unified Model | Notes |
|-------------------|---------------|-------|
| `task.id` | `TaskTicket.id` | Direct |
| `task.title` | `TaskTicket.name` | Rename |
| `task.description` | `TaskTicket.description` | Direct |
| `task.sprint_id` | `TaskTicket.parent_ref` | Rename |
| `task.task_type` | `TaskTicket.task_type` | Direct |
| `task.status` | `TaskTicket.status` | Enum mapping |
| `task.blocked` | Computed from `criteria` | No longer stored |
| `task.priority` | `TaskTicket.priority` | Direct |
| `task.estimated_tokens` | `TaskTicket.estimated_tokens` | Direct |
| `task.complexity` | `TaskTicket.complexity` | Direct |
| `task.dependencies[]` | `criteria` with `CompletableTarget`, `blocks_transition_to: in_progress` | Deps become criteria |
| `task.deliverables[]` | `criteria` with `FileExistsTarget` | Deliverables become criteria |

---

## Computed Fields (No Storage)

The following fields are computed and NOT stored:

| Legacy Field | Computed From |
|--------------|---------------|
| `*.blocked` | `criteria` where `is_met=false` |
| `*.progress` | `criteria` completion ratio |
| `*.blocks[]` | `v_reverse_dependencies` SQL view |
| `*.depended_on_by[]` | `v_reverse_dependencies` SQL view |

---

## Standards → Requirements Transformation

| Legacy Standard | Unified Requirement |
|-----------------|---------------------|
| `Standard.id` | `Requirement.id` |
| `Standard.name` | `Requirement.name` |
| `Standard.type` | `CriterionTemplate.target_type` |
| `Standard.enforcement` | `Criterion.required` + behavior |
| `Standard.validation` | `CriterionTemplate.target_config` |

**EnforcementMode → Unified Behavior:**

| EnforcementMode | Unified Behavior |
|-----------------|------------------|
| `BLOCKING` | `Criterion.required = True` |
| `WARNING` | `Criterion.required = False` + log warning |
| `AUDIT` | `Criterion.required = False` + log to activity_log |

---

## Migration Script Template

**Code:** [`sample_code/models/func_migrate_legacy_yaml_to_unified.py`](../sample_code/models/func_migrate_legacy_yaml_to_unified.py)
