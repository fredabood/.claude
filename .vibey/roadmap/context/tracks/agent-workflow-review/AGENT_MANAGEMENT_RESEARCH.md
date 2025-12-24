# Agent Management Research Document

**Track:** Agent Workflow & Handoff Architecture Review (01KD617KB2XD77QC428SZ2Q5RW)
**Date:** 2024-12-24
**Status:** Complete

---

## 1. Executive Summary

This document provides a comprehensive audit of vibey's agent management capabilities within the implementation mode subsystem. The research identifies current architecture, hardcoded values, extension points, and gaps that must be addressed to enable A/B testing of models, prompts, ticket templates, and execution strategies.

### Key Findings

1. **Mature Agent Infrastructure**: The implementation mode has a well-designed agent spawning and execution system with 35+ Python modules.
2. **Significant Hardcoding**: Model names, system prompts, and configuration defaults are hardcoded across 8+ files.
3. **Limited Experimentation Support**: No infrastructure exists for experiment tracking, variant assignment, or metrics collection.
4. **Strong Extension Points**: The existing configuration system provides good injection points for A/B testing.
5. **Parallel Execution Ready**: The codebase already supports parallel agent execution, which can facilitate experiment throughput.

---

## 2. Current Architecture Overview

### 2.1 Implementation Mode Module Structure

```
vibey/services/implementation/
├── __init__.py          # Module exports (440 lines)
├── config.py            # Configuration system (643 lines)
├── loop.py              # Main execution loop (850 lines)
├── executor.py          # Task executor (546 lines)
├── spawner.py           # Agent spawning (816 lines)
├── selector.py          # Task selection (414 lines)
├── context.py           # Context building (473 lines)
├── result.py            # Execution results (337 lines)
├── state.py             # Loop state tracking (591 lines)
├── parallel.py          # Parallel execution groups (692 lines)
├── aggregator.py        # Result aggregation
├── checkpoint.py        # Git checkpoints
├── recovery.py          # Error recovery
├── budget.py            # Token budget tracking
├── approval.py          # Human approval gates
├── regression.py        # Regression detection
├── git/                 # Git integration
│   ├── branch_manager.py  # Branch lifecycle (844 lines)
│   ├── commit_enforcer.py # Commit policies
│   ├── requirements.py    # Git requirements
│   └── context_dumper.py  # Context export
└── versioning/          # Content versioning
    ├── core.py
    ├── execution.py
    └── plan.py
```

### 2.2 Key Components and Responsibilities

| Component | File | Responsibility |
|-----------|------|---------------|
| ImplementConfig | config.py:178-478 | Configuration loading, merging, validation |
| AgentConfig | config.py:156-169 | Model, turns, permissions settings |
| ImplementationLoop | loop.py:232-797 | Main execution orchestration |
| ClaudeTaskExecutor | executor.py:57-541 | Task execution via Claude CLI |
| AgentSpawner | spawner.py:276-799 | Parallel agent process management |
| TaskSelector | selector.py:62-406 | Task selection and prioritization |
| TaskContextBuilder | context.py:108-463 | Context assembly for agents |

---

## 3. Agent Spawning Analysis

### 3.1 Spawner Architecture

**File:** `vibey/services/implementation/spawner.py`

The AgentSpawner class manages parallel agent execution:

```python
class AgentSpawner:
    AGENT_BINARY = "claude"           # Line 298 - Hardcoded
    DEFAULT_MAX_CONCURRENT = 3        # Line 301 - Hardcoded
    DEFAULT_TIMEOUT = 600             # Line 302 - Hardcoded (10 minutes)
```

#### Spawning Flow
1. `spawn_agents(group: ParallelGroup)` - Entry point for parallel spawning
2. `spawn_agent(task, context)` - Single agent spawning
3. `_build_command(context)` - CLI command construction
4. `_build_context(task)` - Execution context assembly
5. `_build_system_prompt(task)` - System prompt generation (lines 537-552)
6. `_build_task_prompt(task)` - User prompt generation (lines 554-570)

### 3.2 Hardcoded System Prompt

**Location:** spawner.py:537-552

```python
def _build_system_prompt(self, task: "HierarchicalTicket") -> str:
    """Build system prompt for the agent."""
    lines = [
        "You are an autonomous coding agent executing a development task.",
        "Follow the task instructions precisely.",
        "Make incremental commits for significant changes.",
        "Report any blockers or issues clearly.",
        "",
        f"Task ID: {task.id}",
        f"Task Name: {task.name}",
    ]
    # ...
```

**Gap for A/B Testing:** This prompt is entirely hardcoded with no mechanism for:
- Prompt variants
- Template selection
- Dynamic prompt composition
- Persona or style variations

### 3.3 Command Construction

**Location:** spawner.py:477-508

```python
def _build_command(self, context: TaskContext) -> List[str]:
    cmd = [
        self.AGENT_BINARY,
        "--print",
        "--dangerously-skip-permissions",
    ]

    if context.system_prompt:
        cmd.extend(["--system-prompt", context.system_prompt])

    # Model from config if available
    if hasattr(self.config, "agent") and hasattr(self.config.agent, "model"):
        cmd.extend(["--model", self.config.agent.model])

    # Max turns if configured
    if hasattr(self.config, "agent") and hasattr(self.config.agent, "max_turns"):
        cmd.extend(["--max-turns", str(self.config.agent.max_turns)])
```

**Extension Points:**
- Model is configurable via `AgentConfig.model`
- Max turns is configurable via `AgentConfig.max_turns`
- System prompt is passed through from context

---

## 4. Execution Flow Analysis

### 4.1 Main Execution Loop

**File:** `vibey/services/implementation/loop.py`

```
┌─────────────────────────────────────────────────────────────────┐
│                    ImplementationLoop.run()                      │
│                                                                  │
│  1. Load/create state                                           │
│  2. Install signal handlers                                      │
│  3. While not stopped:                                          │
│     a. Check stop conditions                                    │
│     b. selector.get_next_task() → HierarchicalTicket            │
│     c. Capture regression snapshot (if detector)                │
│     d. executor.execute(task) → ExecutionResult                 │
│     e. _handle_result(task, result)                             │
│     f. Check regressions                                        │
│     g. Auto-save state                                          │
│  4. Return LoopResult                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Task Executor

**File:** `vibey/services/implementation/executor.py`

The `ClaudeTaskExecutor` class provides the concrete implementation:

```python
class ClaudeTaskExecutor:
    AGENT_BINARY = "claude"           # Line 79 - Duplicated
    DEFAULT_TIMEOUT = 600             # Line 82 - Duplicated
```

**Gap:** The executor has its own hardcoded values that duplicate spawner settings.

### 4.3 Context Building

**File:** `vibey/services/implementation/context.py`

The `TaskContextBuilder` assembles execution context:

1. Task description and name
2. Acceptance criteria from ticket
3. Relevant files from plan/description
4. Parent context (sprint/track goals)
5. System prompt with detailed instructions

**Hardcoded System Prompt Template:** lines 273-317

```python
prompt = f"""You are implementing a development task.

## Task Information
**Task ID:** {task.id}
...
## Instructions
1. Read and understand the task requirements
2. Examine the relevant files listed above
3. Implement the changes needed to satisfy all acceptance criteria
...
"""
```

---

## 5. Gap Analysis for A/B Testing

### 5.1 Model Experimentation

**Current State:**
- Default model: `claude-sonnet-4-20250514` (config.py:166)
- Configurable via YAML or CLI override
- No experiment assignment mechanism

**Gaps:**
1. No model selection based on task characteristics
2. No A/B experiment framework for model comparison
3. No metrics collection per model variant
4. No automatic model fallback on failure

**Locations to Modify:**
- `vibey/services/implementation/config.py:166` - AgentConfig.model default
- `vibey/services/implementation/spawner.py:498-499` - Model command injection
- `vibey/services/implementation/executor.py:279-290` - Agent spawning

### 5.2 Prompt Experimentation

**Current State:**
- System prompt hardcoded in spawner.py:537-552
- Context builder has separate hardcoded prompt (context.py:273-317)
- Executor has fallback prompt (executor.py:239-258)
- Three different prompt templates with no unified management

**Gaps:**
1. No prompt template registry
2. No variant selection mechanism
3. No prompt versioning
4. No A/B testing for prompt effectiveness
5. Inconsistent prompt patterns across components

**Files with Hardcoded Prompts:**
| File | Lines | Description |
|------|-------|-------------|
| spawner.py | 537-570 | Basic system/task prompts |
| context.py | 273-317 | Full execution prompt |
| executor.py | 239-258 | Fallback prompt |

### 5.3 Ticket Template Experimentation

**Current State:**
- Task criteria defined in HierarchicalTicket
- Requirements system with inheritance modes
- No template variant system

**Gaps:**
1. No task template variants for A/B testing
2. No criteria generation experiments
3. No automatic complexity adjustment experiments

### 5.4 Execution Strategy Experimentation

**Current State:**
- Sequential execution via ImplementationLoop
- Parallel execution via AgentSpawner/IndependentTaskIdentifier
- Wave-based execution grouping

**Gaps:**
1. No strategy selection mechanism
2. No A/B testing for execution order
3. No comparison of sequential vs parallel approaches
4. No adaptive strategy based on task characteristics

---

## 6. Hardcoded Values Inventory

### 6.1 Model Names

| File | Line | Value | Context |
|------|------|-------|---------|
| config.py | 166 | `claude-sonnet-4-20250514` | AgentConfig default |
| config.py | 365 | `claude-sonnet-4-20250514` | YAML parsing fallback |
| result.py | 145 | `claude-sonnet-4-20250514` | ExecutionResult default |
| result.py | 307-308 | `claude-sonnet-4-20250514` | Deserialization fallback |
| templates/implement.yaml | 89 | `claude-sonnet-4-20250514` | Template default |

### 6.2 Timeouts and Limits

| File | Line | Value | Description |
|------|------|-------|-------------|
| executor.py | 82 | 600 | DEFAULT_TIMEOUT (10 min) |
| spawner.py | 302 | 600 | DEFAULT_TIMEOUT (10 min) |
| spawner.py | 301 | 3 | DEFAULT_MAX_CONCURRENT |
| commit_enforcer.py | 50 | 15 | DEFAULT_MAX_MINUTES_BETWEEN_COMMITS |
| commit_enforcer.py | 53 | 10 | DEFAULT_MAX_FILES_CHANGED |
| commit_enforcer.py | 56 | 500 | DEFAULT_MAX_LINES_CHANGED |
| approval.py | 100 | 300 | DEFAULT_APPROVAL_TIMEOUT (5 min) |
| checkpoint.py | 60 | 10 | DEFAULT_KEEP_CHECKPOINTS |
| compactor.py | 57 | 8000 | DEFAULT_MAX_CONTEXT_TOKENS |
| recovery.py | 64 | 3 | DEFAULT_MAX_RETRIES |
| recovery.py | 67 | 60 | DEFAULT_RATE_LIMIT_WAIT_SECONDS |
| acknowledgment.py | 76 | 90 | DEFAULT_ACKNOWLEDGMENT_EXPIRY_DAYS |

### 6.3 Prompts and Templates

| File | Lines | Type | Description |
|------|-------|------|-------------|
| spawner.py | 539-545 | String | System prompt template |
| spawner.py | 556-569 | String | Task prompt template |
| context.py | 274-316 | f-string | Full system prompt |
| executor.py | 241-258 | String | Fallback system prompt |

### 6.4 Git Branch Naming

| File | Line | Value | Description |
|------|------|-------|-------------|
| branch_manager.py | 59 | `implement` | DEFAULT_BRANCH_PREFIX |
| spawner.py | 430 | `implement/{task.id}` | Branch name format |

---

## 7. Extension Points for A/B Testing

### 7.1 Existing Configuration System

The `ImplementConfig` class already provides good extension points:

```python
@dataclass
class ImplementConfig:
    max_tasks_per_session: Optional[int] = 10
    max_tokens_per_session: Optional[int] = 100000
    max_tokens_per_task: int = 25000
    timeout_per_task: int = 600
    retry: RetryConfig = field(default_factory=RetryConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
```

**Extension:** Add `experiment: ExperimentConfig` field for A/B settings.

### 7.2 Context Building Pipeline

The `TaskContextBuilder.build_context()` method is a good injection point:

```python
def build_context(self, task: HierarchicalTicket) -> TaskContext:
    system_prompt = self.build_system_prompt(task)  # ← Override point
    ...
```

**Extension:** Add prompt template selection based on experiment variant.

### 7.3 Agent Spawning Command

The `AgentSpawner._build_command()` method:

```python
if hasattr(self.config, "agent") and hasattr(self.config.agent, "model"):
    cmd.extend(["--model", self.config.agent.model])
```

**Extension:** Model selection could be variant-aware.

### 7.4 Task Selection

The `TaskSelector.get_next_task()` method:

```python
def get_next_task(self, track_id=None, sprint_id=None) -> Optional[HierarchicalTicket]:
    candidates = self._query_candidate_tasks(...)
    for task_data in candidates:
        if self._is_task_planned(task_data["id"]):
            return self._load_task_as_ticket(task_data)
```

**Extension:** Task selection could consider experiment assignment.

---

## 8. Recommended Sprint Tasks

### Sprint 1: Experiment Infrastructure Foundation

| Priority | Task | Complexity | Dependencies |
|----------|------|------------|--------------|
| P0 | Design ExperimentConfig dataclass | Simple | None |
| P0 | Create ExperimentRegistry for variant tracking | Moderate | ExperimentConfig |
| P0 | Add experiment_id to ExecutionResult | Simple | None |
| P1 | Implement variant assignment logic | Moderate | ExperimentRegistry |
| P1 | Add experiment field to ImplementConfig | Simple | ExperimentConfig |

### Sprint 2: Model A/B Testing

| Priority | Task | Complexity | Dependencies |
|----------|------|------------|--------------|
| P0 | Create ModelExperiment variant type | Simple | Sprint 1 |
| P0 | Modify spawner for variant-aware model selection | Moderate | ModelExperiment |
| P1 | Add model_variant to ExecutionResult | Simple | None |
| P1 | Create model comparison metrics | Moderate | ExecutionResult |
| P2 | Implement model fallback chain | Complex | ModelExperiment |

### Sprint 3: Prompt A/B Testing

| Priority | Task | Complexity | Dependencies |
|----------|------|------------|--------------|
| P0 | Create PromptTemplate registry | Moderate | Sprint 1 |
| P0 | Refactor hardcoded prompts to templates | Complex | PromptTemplate |
| P1 | Implement PromptExperiment variant type | Simple | PromptTemplate |
| P1 | Modify context builder for template selection | Moderate | PromptExperiment |
| P2 | Add prompt versioning support | Moderate | PromptTemplate |

### Sprint 4: Metrics and Analysis

| Priority | Task | Complexity | Dependencies |
|----------|------|------------|--------------|
| P0 | Design experiment metrics schema | Moderate | Sprints 1-3 |
| P0 | Create ExperimentMetricsCollector | Moderate | Schema |
| P1 | Add MCP tools for experiment management | Moderate | ExperimentRegistry |
| P1 | Create experiment results aggregation | Complex | MetricsCollector |
| P2 | Build analysis dashboard CLI | Complex | Aggregation |

### Sprint 5: Ticket Template and Strategy Experiments

| Priority | Task | Complexity | Dependencies |
|----------|------|------------|--------------|
| P0 | Create TicketTemplateExperiment | Moderate | Sprint 1 |
| P1 | Implement ExecutionStrategyExperiment | Complex | Sprint 1 |
| P1 | Add strategy comparison metrics | Moderate | StrategyExperiment |
| P2 | Build adaptive strategy selector | Very Complex | All experiments |

---

## 9. Implementation Priority Matrix

```
                        Business Impact
                    Low          High
              ┌────────────┬────────────┐
    Complex   │ P4: Later  │ P2: Should │
              │            │    Have    │
    Effort    ├────────────┼────────────┤
              │ P3: Maybe  │ P0/P1:Must │
    Simple    │            │    Have    │
              └────────────┴────────────┘
```

### Priority 0 (Must Have - Sprint 1)
1. ExperimentConfig dataclass
2. ExperimentRegistry
3. Variant assignment logic

### Priority 1 (Should Have - Sprints 2-3)
1. Model experiment support
2. Prompt template registry
3. Basic metrics collection

### Priority 2 (Nice to Have - Sprints 4-5)
1. Advanced metrics
2. Strategy experiments
3. Adaptive selection

---

## 10. Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Prompt changes break existing behavior | Medium | High | Add comprehensive test suite |
| Model cost increases from experiments | High | Medium | Set budget limits per experiment |
| Parallel execution race conditions | Low | High | Use existing synchronization patterns |
| Configuration complexity | Medium | Medium | Provide sensible defaults |

### Architectural Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scattered experiment logic | Medium | High | Centralize in experiment module |
| Metrics storage growth | Medium | Medium | Implement retention policies |
| Breaking existing CLI | Low | High | Maintain backward compatibility |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Invalid experiment configurations | Medium | Medium | Add validation layer |
| Experiment cross-contamination | Low | High | Ensure proper variant isolation |
| Analysis paralysis | Medium | Low | Define clear success metrics upfront |

---

## 11. Appendix: File Reference Quick Lookup

### Core Implementation Files

| Purpose | File Path | Key Lines |
|---------|-----------|-----------|
| Main config | `vibey/services/implementation/config.py` | 156-169, 178-478 |
| Execution loop | `vibey/services/implementation/loop.py` | 232-797 |
| Task executor | `vibey/services/implementation/executor.py` | 57-541 |
| Agent spawner | `vibey/services/implementation/spawner.py` | 276-799 |
| Context builder | `vibey/services/implementation/context.py` | 108-463 |
| Task selector | `vibey/services/implementation/selector.py` | 62-406 |
| Execution result | `vibey/services/implementation/result.py` | 76-327 |
| Loop state | `vibey/services/implementation/state.py` | 165-580 |
| Parallel groups | `vibey/services/implementation/parallel.py` | 139-682 |

### Git Integration Files

| Purpose | File Path | Key Lines |
|---------|-----------|-----------|
| Branch management | `vibey/services/implementation/git/branch_manager.py` | 164-823 |
| Commit enforcement | `vibey/services/implementation/git/commit_enforcer.py` | 50-830 |
| Git requirements | `vibey/services/implementation/git/requirements.py` | 58-1056 |

### Template Files

| Purpose | File Path |
|---------|-----------|
| Default config | `vibey/services/implementation/templates/implement.yaml` |

---

*Document generated by deep research analysis for Track 01KD617KB2XD77QC428SZ2Q5RW*
