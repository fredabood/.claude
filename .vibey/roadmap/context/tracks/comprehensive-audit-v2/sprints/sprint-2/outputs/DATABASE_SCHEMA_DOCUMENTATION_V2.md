# Database Schema Documentation (Updated)

**Generated:** 2025-12-28
**Sprint:** Comprehensive Audit V2 - Sprint 2
**Database:** SQLite 3.x
**Previous Version:** 2025-12-12 (27 tables, 21 views)

---

## Overview

| Component | Previous (Dec 12) | Current | Change |
|-----------|-------------------|---------|--------|
| Tables | 27 | 38 | +11 |
| Views | 21 | 25 | +4 |
| Indices | 77 | 77 | - |

---

## Tables (38 Total)

### Core Entities
| Table | Purpose | New? |
|-------|---------|------|
| roadmaps | Top-level roadmap definitions | - |
| tracks | Development tracks | - |
| sprints | Sprint containers | - |
| tasks | Individual work items | - |

### Relationship Tables
| Table | Purpose | New? |
|-------|---------|------|
| entity_blocks | Entity blocking relationships | - |
| entity_blocked_by | Reverse blocking | - |
| entity_depends_on | Dependency tracking | - |
| entity_commits | Commit associations | - |
| entity_deliverables | Deliverable associations | - |
| linked_task_pairs | Task linking | NEW |
| external_blockers | External blocking refs | - |
| external_dependencies | External deps | - |
| submodule_references | Git submodule refs | NEW |

### Session/Activity Tables
| Table | Purpose | New? |
|-------|---------|------|
| sessions | Work session tracking | NEW |
| session_events | Session event log | NEW |
| session_tasks | Tasks within sessions | NEW |
| session_commits | Commits within sessions | NEW |
| session_snapshots | Session state snapshots | NEW |
| activity_log | Activity history | - |
| audit_trail | Change audit log | - |

### Artifact Tables
| Table | Purpose | New? |
|-------|---------|------|
| artifacts | Generated artifacts | - |
| commits | Git commit links | - |
| commit_artifact_changes | Artifact changes per commit | NEW |
| ticket_artifact_associations | Ticket-artifact links | NEW |
| ticket_commit_links | Ticket-commit links | NEW |
| deliverables | Task deliverables | - |

### Configuration Tables
| Table | Purpose | New? |
|-------|---------|------|
| assigned_agents | Agent assignments | - |
| quality_gates | Sprint quality gates | - |
| development_gates | Dev phase gates | - |
| standards | Quality standards | - |
| strategic_value | Track strategic value | - |

### Summary/Cache Tables
| Table | Purpose | New? |
|-------|---------|------|
| track_summaries | Track progress summaries | - |
| sprint_summaries | Sprint progress summaries | - |
| task_summaries | Task progress summaries | - |

### Operational Tables
| Table | Purpose | New? |
|-------|---------|------|
| sync_conflicts | YAML sync tracking | - |
| yaml_checksums | File checksums | - |
| database_state | DB state tracking | NEW |
| version_history | Schema versions | NEW |

---

## Views (25 Total)

### Progress Views
| View | Purpose |
|------|---------|
| v_roadmap_progress | Overall roadmap progress |
| v_track_progress | Per-track progress |
| v_sprint_progress | Per-sprint progress |
| v_velocity_metrics | Velocity calculations |

### Session Views
| View | Purpose | New? |
|------|---------|------|
| v_active_sessions | Currently active sessions | NEW |
| v_session_summary | Session overview | NEW |
| v_session_decisions | Decisions made in sessions | NEW |
| v_session_timeline | Session event timeline | NEW |

### Entity Views
| View | Purpose |
|------|---------|
| v_blocked_entities | All blocked entities |
| v_unblocked_tasks | Ready-to-work tasks |
| v_dependency_chain | Full dependency graph |

### Aggregate Views
| View | Purpose |
|------|---------|
| v_track_summary_data | Track aggregates |
| v_sprint_summary_data | Sprint aggregates |
| v_task_summary_data | Task aggregates |
| v_track_sprint_summaries | Track-sprint joins |
| v_sprint_assigned_agents | Sprint agents |
| v_sprint_commits | Sprint commits |
| v_sprint_deliverables | Sprint deliverables |
| v_sprint_estimated_duration | Duration estimates |
| v_track_assigned_agents | Track agents |
| v_track_commits | Track commits |
| v_track_deliverables | Track deliverables |

### Quality Views
| View | Purpose |
|------|---------|
| v_quality_gate_summary | Gate status summary |
| v_failing_quality_gates | Gates currently failing |

### Activity Views
| View | Purpose |
|------|---------|
| v_recent_activity | Recent activity feed |

---

## New Tables Since Dec 12 (11 Total)

1. **sessions** - Work session tracking
2. **session_events** - Events within sessions
3. **session_tasks** - Tasks worked on per session
4. **session_commits** - Commits made per session
5. **session_snapshots** - Session state snapshots
6. **linked_task_pairs** - Task-to-task linking
7. **submodule_references** - Git submodule references
8. **commit_artifact_changes** - Artifact changes per commit
9. **ticket_artifact_associations** - Ticket-artifact links
10. **ticket_commit_links** - Ticket-commit links
11. **database_state** - Database state tracking

---

## New Views Since Dec 12 (4 Total)

1. **v_active_sessions** - Currently active work sessions
2. **v_session_summary** - Session overview data
3. **v_session_decisions** - Decisions made during sessions
4. **v_session_timeline** - Timeline of session events

---

*Documentation updated: 2025-12-28T21:00:00+00:00*
