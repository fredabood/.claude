---
globs: ["**/*"]
description: Shared conventions for agent structure, registration, evaluation, and deterministic routing
---

# Agent Management — Structure, Registration, Evaluation, and Routing

Canonical conventions for building, graduating, evaluating, and routing agents across LAB and DRTY projects.
All agent work must conform to these standards.

> Design rationale: `submodules/memory/homelab/decisions/` (agent architecture decisions)
> Runtime context: `project_agent_architecture.md` (auto-memory)

---

## Agent Code Pattern

Stage 3+ agents must follow this directory structure:

```
internal/agent-runtime/{project}/{agent-name}/
  agent.py          # Entry point — agent loop, tool dispatch
  tools.py          # Tool definitions (typed, logged, validated)
  schemas.py        # Pydantic input/output schemas
  evaluate.py       # Evaluation harness (T1-T4 as applicable)
  requirements.txt  # Pinned dependencies
  tests/            # Unit + integration tests
```

**Rules:**
- `agent.py` must expose a standard entry point callable by the runtime (DeepAgents for LAB, mlflow.pyfunc for DRTY)
- `tools.py` must define typed interfaces for every external mutation — no raw API calls outside registered tools
- `schemas.py` must use Pydantic models for all inputs and outputs
- `evaluate.py` must implement at least the evaluation tiers required by the agent's graduation stage
- `requirements.txt` must pin all dependencies (no floating versions)
- `tests/` must include tests covering happy path, error paths, and tool interface contracts

---

## Graduation Stages

Agents progress through five stages. Each stage adds capabilities and requirements.

| Stage | Name | Artifact Location | Runtime | Registration |
|---|---|---|---|---|
| 0 | Prompt template | `internal/agents/{name}/prompt.md` | Manual copy-paste | Git only |
| 1 | Claude Code primitive | `.claude/agents/` or `.claude/skills/` | Claude Code harness | Git only |
| 2 | n8n workflow agent | `internal/n8n/workflows/` + MLflow registered | n8n execution | MLflow LoggedModel |
| 3 | Container agent | Docker service (`internal/agent-runtime/`) | Docker container | MLflow LoggedModel |
| 4 | Autonomous fleet | Same as Stage 3 + continuous eval | Docker container + scheduler | MLflow LoggedModel |

### Stage transitions

```
Stage 0 → 1: Agent proves useful in manual sessions
Stage 1 → 2: Agent needs scheduling or external triggers
Stage 2 → 3: Agent needs persistent state, custom dependencies, or isolation
Stage 3 → 4: Agent passes T1+T2+T3 evaluation and operates without human oversight
```

**Promotion is gated** — an agent cannot advance to the next stage without meeting all requirements of the target stage (evaluation tiers, registration, code structure).

---

## MLflow Registration Requirements

| Stage | Registration | Required Tags |
|---|---|---|
| 0-1 | Not registered (versioned in git only) | N/A |
| 2+ | Registered as MLflow LoggedModel | `stage`, `project`, `prompt_hash` |
| 3+ | Must pass T1+T2 evaluation before deployment | `stage`, `project`, `prompt_hash`, `t1_score`, `t2_score` |
| 4 | Must have T3 continuous evaluation active | All above + `t3_score`, `t3_sample_rate`, `eval_last_run` |

### Registration format

MLflow model name follows the pattern: `{project}/{agent-name}`

Examples:
- `lab/email-triage`
- `lab/infra-review`
- `drty/deal-scorer`
- `drty/comp-analyzer`

### Required MLflow tags

| Tag | Type | Description |
|---|---|---|
| `stage` | int | Current graduation stage (0-4) |
| `project` | string | Jira project key (LAB, DRTY, REAL, GAME, FOOD) |
| `prompt_hash` | string | SHA-256 of the prompt template content |
| `t1_score` | float | Latest T1 evaluation score (Stage 2+) |
| `t2_score` | float | Latest T2 evaluation score (Stage 3+) |
| `t3_score` | float | Latest T3 evaluation score (Stage 4) |
| `t3_sample_rate` | float | Fraction of executions evaluated by T3 (Stage 4) |
| `eval_last_run` | string | ISO timestamp of last evaluation run |

---

## Evaluation Tier Requirements

Four tiers of evaluation, each progressively more expensive and comprehensive.

### T1 — Schema Validation

- **Required at:** Stage 2+
- **What it checks:** Output conforms to declared Pydantic schema
- **Scoring:** `1.0` if valid, `0.0` if not (binary)
- **Implementation:** Automated — runs on every execution
- **Minimum threshold:** `1.0` (no invalid outputs allowed)

### T2 — Rule-Based Checks

- **Required at:** Stage 3+
- **What it checks:** Business rules, safety constraints, deterministic correctness conditions
- **Scoring:** Fraction of rules passing (e.g., 8/10 = 0.8)
- **Implementation:** Automated — runs on every execution alongside T1
- **Minimum threshold:** `0.8`

### T3 — LLM-as-Judge (Sampled)

- **Required at:** Stage 4
- **What it checks:** Quality, relevance, reasoning coherence, style compliance
- **Scoring:** LLM judge score normalized to 0.0-1.0
- **Implementation:** Runs on 10% of executions (configurable via `t3_sample_rate`)
- **Minimum threshold:** `0.7`
- **Judge model:** Ollama for LAB automated agents; Claude for DRTY production agents

### T4 — Human Review (Periodic)

- **Required at:** Recommended at Stage 4
- **What it checks:** Overall quality, edge cases, alignment with business intent
- **Scoring:** Human rating (pass/fail + qualitative notes)
- **Implementation:** Quarterly review cycle
- **Minimum threshold:** N/A (qualitative — informs improvement, does not gate)

### Quality threshold summary

| Tier | Min Score | Gate Behavior |
|---|---|---|
| T1 | 1.0 | Below threshold blocks deployment and promotion |
| T2 | 0.8 | Below threshold blocks promotion to Stage 4 |
| T3 | 0.7 | Below threshold blocks continued autonomous operation |
| T4 | N/A | Informs improvement loop, does not block |

---

## Deterministic Routing Requirement

All external mutations performed by autonomous agents (Stage 3+) must go through **registered tools** that provide:

1. **Typed interface** — Pydantic input/output schemas in `schemas.py`
2. **Logging** — Every tool invocation is logged with timestamp, input, output, and latency
3. **Validation** — Input validation before execution, output validation after
4. **Idempotency** — Tools that create or modify external state must be idempotent where possible

**No raw API calls outside registered tools.** If an agent needs a new external capability, define it as a tool in `tools.py` first.

**Routing for Claude Code primitives (Stage 1):**
- Agents in `.claude/agents/` are routed by the label-taxonomy agent routing table (see `label-taxonomy.md`)
- Skills in `.claude/skills/` are invoked by name via the Skill tool

**Routing for n8n workflow agents (Stage 2):**
- Triggered by n8n schedule, webhook, or CDC event
- Workflow ID registered in `homelab-services.md` known workflow IDs section

**Routing for container agents (Stage 3-4):**
- Invoked via HTTP API or message queue
- Registered in MLflow with endpoint metadata
- Health check exposed for Uptime Kuma monitoring

---

## Databricks Portability Checklist (DRTY only)

DRTY agents that will graduate to Databricks must satisfy these constraints:

- [ ] **No filesystem/shell dependencies** — no `os.system()`, `subprocess`, or local file I/O
- [ ] **All I/O through parameters** — function inputs and outputs only, no side-channel state
- [ ] **mlflow.pyfunc.PythonModel wrapper** — agent must implement `predict()` method
- [ ] **Pydantic schemas** — all inputs and outputs defined as Pydantic models
- [ ] **Compatible requirements.txt** — all dependencies available on Databricks Runtime
- [ ] **No Ollama dependency** — DRTY production agents use Databricks Model Serving, not local Ollama

LAB agents do NOT need to satisfy this checklist — they run on homelab infrastructure permanently.

---

## Cross-References

| Topic | Location |
|---|---|
| Agent routing by work pattern | `.claude/rules/label-taxonomy.md` → Agent Routing section |
| Runtime architecture decisions | `submodules/memory/homelab/decisions/` |
| MLflow service details | `.claude/rules/homelab-services.md` → Service Catalog |
| Agent tracking Jira fields | `.claude/rules/custom-fields.md` → Agent Tracking Fields |
| Evaluation infrastructure | MLflow at `mlflow.dirtydata.studio` |
