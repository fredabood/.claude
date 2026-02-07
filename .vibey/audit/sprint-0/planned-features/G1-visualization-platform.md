# G1: Roadmap Visualization Platform Review

**Task ID:** 01KFXJ5D7NTJC1TD14A2QSXW5J
**Phase:** G1: Planned Features
**Date:** 2026-01-29

## Executive Summary

Review of the planned Roadmap Visualization Platform track (01KC2D0JKWWW8WMS7PPGDQ42HB) covering 20 sprints and 120 planned tasks. The platform will provide web and VS Code interfaces for roadmap visualization including Tree View, Kanban Board, Gantt/Timeline, and Chat Interface. Key finding: All components require a backend API that could be deployed as Databricks REST API endpoints, enabling remote visualization while maintaining local CLI interoperability.

## Methodology

**Files Analyzed:**
- `.vibey/roadmap/tracks/01KC2D0JKWWW8WMS7PPGDQ42HB.yaml` - Track definition
- Sprint definitions within track (20 sprints)

## Findings

### 2. Planned Components Table

| Component | Architecture | Status | Track Location |
|-----------|--------------|--------|----------------|
| Tree View | React/TypeScript | Planned | Sprint 4, Sprint 2 (VS Code) |
| Kanban Board | React/TypeScript | Planned | Sprint 5 |
| Gantt/Timeline | React/TypeScript | Planned | Sprint 6 |
| Doc Viewer | Markdown rendering | Planned | Sprint 7 |
| Chat Interface | Backend + Frontend | Planned | Sprint 8-9 |
| VS Code Extension | TypeScript/VS Code API | Planned | Sprint 10-11 |
| Roadmap API Backend | REST API | Planned | Sprint 2 |
| Core UI Layout | React | Planned | Sprint 3 |

### 3. API Requirements Table

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/roadmap/status` | GET | Get overall roadmap status | Yes |
| `/api/tracks` | GET | List all tracks | Yes |
| `/api/tracks/{id}` | GET | Get track details | Yes |
| `/api/sprints/{id}` | GET | Get sprint details | Yes |
| `/api/tasks/{id}` | GET | Get task details | Yes |
| `/api/tasks/{id}/start` | POST | Start a task | Yes |
| `/api/tasks/{id}/complete` | POST | Complete a task | Yes |
| `/api/chat/message` | POST | Send chat message | Yes |
| `/api/search` | GET | Search roadmap | Yes |
| `/api/export/{format}` | GET | Export roadmap | Yes |

### 4. Data Access Patterns Table

| Pattern | Operations | Frequency | Caching |
|---------|------------|-----------|---------|
| Read Status | roadmap_status, list_blockers | High (polling) | 30s TTL |
| Read Details | query_task, query_sprint, query_track | Medium | 5min TTL |
| Mutations | start_task, complete_task | Low | Invalidate on change |
| Search | Full-text search | Medium | No caching |
| Batch Read | List all tracks, sprints | Low | 5min TTL |
| Subscribe | WebSocket status updates | Continuous | Event-driven |

### 5. Real-Time Requirements Table

| Feature | Protocol | Update Frequency | Fallback |
|---------|----------|------------------|----------|
| Task Status | WebSocket | Real-time push | 30s polling |
| Progress Bars | WebSocket | On change | 60s polling |
| Notifications | WebSocket | Immediate | 30s polling |
| Chat Messages | WebSocket | Immediate | Long polling |
| Blocker Alerts | WebSocket | On change | 60s polling |
| Kanban Updates | WebSocket | On change | Manual refresh |

### 6. Remote Backend Architecture

| Component | Databricks Service | Scaling | Latency Target |
|-----------|-------------------|---------|----------------|
| REST API | Jobs + Delta Lake | Horizontal | <200ms |
| WebSocket | Streaming compute | Connection-based | <50ms |
| Search | Delta Lake full-text | Query-optimized | <500ms |
| Chat Backend | LLM endpoint | Model serving | <2s |
| File Storage | Unity Catalog | Distributed | <100ms |
| Cache Layer | Delta Cache | Automatic | <10ms |

**Remote Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VISUALIZATION PLATFORM ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────────────┘

  CLIENT TIER                              DATABRICKS TIER
  ────────────                              ───────────────

┌─────────────────┐                       ┌─────────────────┐
│ Web UI          │                       │ REST API        │
│ (React/TS)      │───── HTTPS ──────────▶│ (Jobs API)      │
└─────────────────┘                       └────────┬────────┘
                                                   │
┌─────────────────┐                                │
│ VS Code Ext     │───── HTTPS ──────────▶        │
│ (TypeScript)    │                                ▼
└─────────────────┘                       ┌─────────────────┐
                                          │ Delta Lake      │
┌─────────────────┐                       │ (roadmap data)  │
│ CLI             │───── Local ──────────▶└─────────────────┘
│ (Python)        │       or                       │
└─────────────────┘       HTTPS                    │
                                                   │
                   ┌───────────────────────────────┼───────────────┐
                   │                               │               │
                   ▼                               ▼               ▼
          ┌─────────────────┐         ┌─────────────────┐ ┌─────────────────┐
          │ WebSocket       │         │ Chat Backend    │ │ Search Index    │
          │ (Streaming)     │         │ (LLM Serving)   │ │ (Delta FT)      │
          └─────────────────┘         └─────────────────┘ └─────────────────┘
```

### 7. Integration Points Table

| Integration | Protocol | Data Flow | Authentication |
|-------------|----------|-----------|----------------|
| CLI → Backend | REST/Local | Bidirectional | Token/None |
| Web UI → Backend | REST + WS | Read-heavy | OAuth/Token |
| VS Code → Backend | REST + WS | Bidirectional | Token |
| MCP → Backend | REST | Read-heavy | Service Account |
| Git Hooks → Backend | Webhook | Push | Webhook secret |
| CI/CD → Backend | REST | Push | Service Account |

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| 20 sprints of UI work planned | Reuse for remote dashboard | L | Medium |
| REST API required | Deploy to Databricks Jobs | M | High |
| WebSocket for real-time | Use Databricks Streaming | M | High |
| Chat requires LLM | Use Model Serving | M | Medium |
| VS Code extension planned | Keep local, connect to remote | S | Medium |
| Search needed | Use Delta Lake full-text | S | Medium |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Planned components table lists >= 4 components: PASS (8 components)
- [x] API requirements table lists >= 6 endpoints: PASS (10 endpoints)
- [x] Remote backend architecture addresses Databricks: PASS
- [x] Integration points include CLI and MCP: PASS

## References

- `.vibey/roadmap/tracks/01KC2D0JKWWW8WMS7PPGDQ42HB.yaml:1-156` - Full track definition
- Track progress: 0% complete, 20 sprints, 120 tasks planned
