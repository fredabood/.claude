# E5: Agent Integration Points Audit

**Task ID:** 01KFXGQX7B3EFC7DWKJCSC4RHN
**Phase:** E5: Advanced
**Date:** 2026-01-29

## Executive Summary

Vibey integrates AI agents through three mechanisms: (1) Agent Discovery via frontmatter parsing, (2) Agent Context loading for task execution, and (3) Agent Routing for intelligent task assignment. The `AgentDiscovery` class discovers agents from markdown files, while `AgentRouter` recommends agents based on task characteristics and keywords. Key finding: Agent integration translates cleanly to remote mode - agent definitions can be stored in Delta Lake, context can be fetched remotely, and routing can be performed server-side.

**Key Statistics:**
- 8+ built-in agent types with capabilities mapping
- 19 agent tools via MCP discovery
- 4 required frontmatter fields (id, name, type, version)
- Confidence-based agent recommendation

## Agent Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   AGENT INTEGRATION ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────┘

  AGENT DEFINITION                     AGENT INVOCATION
  ────────────────                     ────────────────

┌─────────────────┐                 ┌─────────────────┐
│ vibey/content/  │                 │ MCP Tool Call   │
│ agents/*.md     │                 │ vibey_agent_... │
└────────┬────────┘                 └────────┬────────┘
         │                                   │
         │ Discovery                         │ Route
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ AgentDiscovery  │                 │ VibeyMCPServer  │
│ - parse frontm. │                 │ _execute_agent_ │
│ - validate      │                 │ tool()          │
└────────┬────────┘                 └────────┬────────┘
         │                                   │
         │ AgentDefinition                   │ Context
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ ToolDiscovery   │                 │ AgentContext    │
│ - generate tools │                │ Loader          │
│ - cache 60s     │                 │ - task context  │
└─────────────────┘                 │ - sprint plan   │
                                    │ - decisions     │
                                    │ - discovery     │
                                    └─────────────────┘
```

## Agent Discovery

### AgentDiscovery Class

| Method | Purpose | Parameters |
|--------|---------|------------|
| `__init__()` | Initialize with root_dir | root_dir: Optional[Path] |
| `discover()` | Find all agents in agents_dir | None |
| `_parse_agent_file()` | Parse single agent file | filepath: Path |
| `get_agent_by_id()` | Get agent by ID or alias | agent_id: str |
| `get_agents_by_type()` | Filter agents by type | agent_type: str |

### AgentDefinition Dataclass

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Unique agent identifier |
| `name` | str | Yes | Human-readable name |
| `type` | str | Yes | Agent type (core, planning, development, etc.) |
| `version` | str | Yes | Semantic version |
| `description` | str | No | Agent description |
| `triggers` | Dict | No | Conditions that trigger this agent |
| `inputs` | List | No | Expected input parameters |
| `outputs` | List | No | Expected outputs |
| `aliases` | List | No | Alternative identifiers |
| `filepath` | Path | No | Source file path |

### Agent Frontmatter Format

```yaml
---
id: web-developer
name: Web Developer Agent
type: development
version: "1.0.0"
description: Full-stack web development agent
triggers:
  keywords: [api, endpoint, route, frontend, backend]
  task_types: [development]
inputs:
  - name: task_id
    type: string
    required: true
outputs:
  - name: code
    type: file
  - name: tests
    type: file
aliases:
  - fullstack
  - frontend-dev
  - backend-dev
---

# Web Developer Agent Instructions

[Agent instructions here...]
```

## Agent Routing

### AGENT_CAPABILITIES Mapping

| Agent | Keywords | Task Types | Specialties |
|-------|----------|------------|-------------|
| `web-developer` | api, endpoint, route, controller, middleware, auth, backend, frontend, react, vue, angular | development | web development, API design, full-stack |
| `ml-engineer` | model, training, dataset, inference, ml, ai, neural, pytorch, tensorflow | development | machine learning, data science |
| `security-auditor` | security, vulnerability, auth, encryption, xss, sql injection, csrf | completion_gate, production_gate | security auditing, penetration testing |
| `test-engineer` | test, unit test, integration test, e2e, coverage, qa | completion_gate, production_gate | testing, quality assurance |
| `docs-writer` | documentation, docs, readme, guide, tutorial, api docs | completion_gate | technical writing, documentation |
| `performance-optimizer` | performance, optimization, latency, throughput, caching, profiling | production_gate | performance optimization, profiling |
| `devops-engineer` | deployment, ci/cd, docker, kubernetes, infrastructure, pipeline | production_gate | DevOps, infrastructure, deployment |
| `observability-engineer` | logging, monitoring, metrics, tracing, observability, alerting | production_gate | observability, monitoring, logging |

### AgentRouter Class

| Method | Purpose | Parameters |
|--------|---------|------------|
| `recommend_agent_for_task()` | Get agent recommendations with scores | task: Task |
| `auto_assign_task()` | Auto-assign if confidence >= threshold | task: Task, min_confidence: float |
| `get_agent_workload()` | Get workload per agent | None |
| `recommend_next_task()` | Recommend next task for agent | agent: str, max_recommendations: int |

### Recommendation Scoring

```python
def recommend_agent_for_task(task: Task) -> List[Tuple[str, float]]:
    """
    Score calculation:
    - Task type match: +0.5
    - Keyword matches: +0.1 per keyword (max 0.5)
    - Total possible: 1.0
    """
```

## Agent Context Loading

### AgentContextLoader Class

| Method | Purpose | Returns |
|--------|---------|---------|
| `load_for_task()` | Load context for specific task | EnhancedAgentContext |
| `load_for_session()` | Load context for current session | EnhancedAgentContext |

### EnhancedAgentContext

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| `task` | TaskContext | Current task file | Task details |
| `sprint_plan` | str | Sprint context | Sprint planning doc |
| `recent_sessions` | List[Session] | Sessions dir | Recent work history |
| `recent_decisions` | List[Decision] | Decisions dir | Recent decisions |
| `discovery` | Dict | Project discovery | Project metadata |
| `command_history` | List[Dict] | Context captures | Recent commands |
| `files_modified` | List[str] | Context captures | Modified files |
| `blockers` | List[Dict] | Task/sprint data | Current blockers |
| `dependencies` | List[str] | Task data | Task dependencies |
| `recommendations` | List[str] | Generated | Next action suggestions |

### Context Format Methods

| Method | Purpose | Size |
|--------|---------|------|
| `format_for_claude()` | Full markdown context | ~5000 chars |
| `format_compact()` | Compact summary | ~1000 chars |

## MCP Agent Tool Execution

### _execute_agent_tool() Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT TOOL EXECUTION FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

1. MCP Tool Call: vibey_agent_web_developer({task_id: "..."})

2. VibeyMCPServer.handle_tool_call()
   └── Route to _handle_dynamic_tool()
       └── metadata.asset_type == 'agent'
           └── _execute_agent_tool()

3. _execute_agent_tool(agent_id, arguments, metadata)
   ├── tool_discovery.agent_discovery.get_agent_by_id(agent_id)
   ├── Load agent markdown content
   ├── Load context for task (if task_id provided)
   └── Return {content: [agent_instructions + context]}

4. AI Assistant receives:
   ├── Agent instructions (from markdown)
   ├── Task context (from context loader)
   ├── Sprint plan (from context)
   └── Recommendations
```

## Agent Integration Points Table

| Integration Point | Module | Mechanism | Remote Requirement |
|-------------------|--------|-----------|-------------------|
| **Agent Discovery** | `mcp/discovery/agents.py` | Frontmatter parsing | Delta Lake agent table |
| **Agent Routing** | `cli/roadmap_lib/agents.py` | Keyword matching | Remote query support |
| **Agent Context** | `operations/context/agent_context.py` | Context aggregation | Remote context fetch |
| **MCP Tools** | `mcp/server.py` | Dynamic tool generation | Remote tool registry |
| **Task Assignment** | `roadmap_lib/agents.py` | Auto-assignment | Remote assignment API |
| **Workload Tracking** | `roadmap_lib/agents.py` | Task aggregation | Remote workload view |

## Remote Mode Translation Table

| Local Concept | Remote Equivalent | Transformation |
|---------------|-------------------|----------------|
| Agent markdown files | Delta Lake agent table | Store content as CLOB |
| Agent discovery | Remote agent registry | Query agent table |
| Agent routing | Server-side routing | Remote recommendation API |
| Agent context | Remote context fetch | Delta Lake + REST |
| Workload tracking | Delta Lake view | Aggregation view |
| Auto-assignment | Remote assignment | API with confidence |

## Remote Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REMOTE AGENT ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

  LOCAL                                REMOTE (DATABRICKS)
  ─────                                ───────────────────

┌─────────────────┐                 ┌─────────────────┐
│ Agent Tool Call │────── HTTPS ───▶│ /api/agents     │
│                 │                 │                 │
└─────────────────┘                 └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ agents table    │
                                    │ (Delta Lake)    │
                                    │ - id, name      │
                                    │ - type, version │
                                    │ - content       │
                                    │ - frontmatter   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Context Fetch   │
                                    │ - task details  │
                                    │ - sprint plan   │
                                    │ - recent work   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Return to Local │
                                    │ - instructions  │
                                    │ - context       │
                                    └─────────────────┘
```

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Agent discovery documented: PASS
- [x] Agent routing with capabilities: PASS (8 agents)
- [x] Agent context loading documented: PASS
- [x] MCP agent execution documented: PASS
- [x] Remote mode translation documented: PASS

## References

- `vibey/mcp/discovery/agents.py` - Agent discovery
- `vibey/cli/roadmap_lib/agents.py` - Agent routing
- `vibey/operations/context/agent_context.py` - Agent context loading
- `vibey/mcp/server.py:370-399` - Agent tool execution
- `.vibey/audit/sprint-0/advanced/E1-implementation-mode.md` - Implementation mode
