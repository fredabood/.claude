# Context Retrieval & Selection Design

**Sprint:** 3.1 - Context Engineering Research & Landscape
**Task:** 5 - Context Retrieval & Selection Design
**Date:** 2025-12-12

---

## Executive Summary

This document designs how vibey selects and retrieves relevant context for AI-assisted coding sessions. The recommended approach uses a **Layered Context Pipeline** with configurable selection strategies, automatic token budget management, and user override capabilities.

**Key Design Decisions:**
1. Layered context with clear priority ordering
2. Task-aware context selection (roadmap integration)
3. Automatic token budget management with configurable limits
4. User control via include/exclude directives
5. Progressive disclosure (summary → detail)

---

## Design Goals

| Goal | Priority | Rationale |
|------|----------|-----------|
| **Relevance** | P0 | Include context that helps AI make good decisions |
| **Efficiency** | P0 | Stay within token budget without losing critical info |
| **User control** | P0 | Users must be able to influence what's included |
| **Transparency** | P1 | Users should know what context was provided |
| **Performance** | P1 | Context assembly should be fast |
| **Adaptability** | P2 | System should improve context selection over time |

---

## Context Source Taxonomy

### Layer 1: Foundation Context (Always Included)

| Source | Description | Est. Tokens | Priority |
|--------|-------------|-------------|----------|
| CLAUDE.md | Project instructions, patterns, conventions | 3,000-5,000 | Highest |
| Active Session | Current session goal and recent events | 200-500 | Highest |
| Git State | Branch, uncommitted changes, recent commits | 100-300 | High |

**Characteristics:**
- Always loaded first
- Cannot be excluded
- Sets baseline understanding

### Layer 2: Task Context (Loaded When Active)

| Source | Description | Est. Tokens | Priority |
|--------|-------------|-------------|----------|
| Active Task | Task description, requirements, acceptance criteria | 200-500 | High |
| Active Sprint | Sprint goal, context files, related tasks | 500-1,500 | High |
| Sprint Plan | Detailed task breakdown (SPRINT_PLAN.md) | 1,000-3,000 | Medium |
| Active Track | Track goal, completion state | 100-300 | Medium |

**Characteristics:**
- Loaded when roadmap items are active
- Provides work context
- Can be summarized if budget is tight

### Layer 3: Reference Context (Loaded On Demand)

| Source | Description | Est. Tokens | Priority |
|--------|-------------|-------------|----------|
| Configuration | Relevant config files (.vibey/config/) | 200-800 | Medium |
| Related Decisions | Past decisions relevant to current work | 200-500 | Medium |
| Recent Sessions | Summary of related past sessions | 300-800 | Low |
| Code Dependencies | Imports, called functions from codebase | Variable | Low |

**Characteristics:**
- Loaded based on relevance scoring
- May be summarized or truncated
- User can explicitly include/exclude

### Layer 4: Extended Context (Explicit Request Only)

| Source | Description | Est. Tokens | Priority |
|--------|-------------|-------------|----------|
| Full Sprint History | All tasks in sprint with decisions | 2,000-5,000 | Low |
| Track Context | All sprints in track | 3,000-10,000 | Low |
| Codebase Search | Semantic search results | Variable | Low |
| External Docs | Fetched documentation | Variable | Low |

**Characteristics:**
- Only loaded when explicitly requested
- May consume significant budget
- Should warn user about token cost

---

## Context Selection Algorithm

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Context Selection Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │ User Query  │                                                │
│  │ / Session   │                                                │
│  │   Start     │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              1. Load Foundation Context                  │   │
│  │  - CLAUDE.md (always)                                   │   │
│  │  - Session state (always)                               │   │
│  │  - Git state (always)                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              2. Load Task Context                        │   │
│  │  - Detect active roadmap items                          │   │
│  │  - Load task/sprint/track context                       │   │
│  │  - Summarize if over budget                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              3. Score Reference Context                  │   │
│  │  - Compute relevance scores                             │   │
│  │  - Rank by priority × relevance                         │   │
│  │  - Select within remaining budget                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              4. Apply User Overrides                     │   │
│  │  - Honor explicit includes                              │   │
│  │  - Honor explicit excludes                              │   │
│  │  - Warn if budget exceeded                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              5. Assemble Final Context                   │   │
│  │  - Order by priority                                    │   │
│  │  - Format for AI consumption                            │   │
│  │  - Generate context manifest                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │   Final     │                                                │
│  │  Context    │                                                │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pseudocode

```python
def select_context(
    session: Session,
    budget: TokenBudget,
    overrides: ContextOverrides
) -> ContextResult:
    """Select and assemble context for AI session."""

    result = ContextResult()

    # Layer 1: Foundation (always included, never truncated)
    result.add(load_claude_md(), priority=100, layer="foundation")
    result.add(session.to_context(), priority=100, layer="foundation")
    result.add(get_git_state(), priority=90, layer="foundation")

    remaining = budget.total - result.tokens_used

    # Layer 2: Task context (included if active)
    if session.active_task:
        task_context = load_task_context(session.active_task)

        if task_context.tokens > remaining * 0.5:
            # Summarize if too large
            task_context = summarize_context(task_context, remaining * 0.4)

        result.add(task_context, priority=80, layer="task")
        remaining = budget.total - result.tokens_used

    # Layer 3: Reference context (scored and ranked)
    candidates = []

    # Gather candidates with relevance scores
    for decision in get_related_decisions(session):
        score = compute_relevance(decision, session)
        candidates.append(ContextCandidate(decision, score, priority=50))

    for config in get_relevant_configs(session):
        score = compute_relevance(config, session)
        candidates.append(ContextCandidate(config, score, priority=40))

    # Sort by priority × relevance
    candidates.sort(key=lambda c: c.priority * c.relevance, reverse=True)

    # Add candidates within budget
    for candidate in candidates:
        if result.tokens_used + candidate.tokens <= budget.total:
            result.add(candidate)
        elif candidate.can_summarize:
            summary = summarize_context(candidate, remaining * 0.2)
            if result.tokens_used + summary.tokens <= budget.total:
                result.add(summary)

    # Layer 4: Apply user overrides
    for include in overrides.includes:
        content = load_explicit_context(include)
        if result.tokens_used + content.tokens > budget.total:
            result.add_warning(f"Including {include} exceeds budget")
        result.add(content, priority=60, layer="explicit")

    for exclude in overrides.excludes:
        result.remove(exclude)

    # Generate manifest
    result.manifest = generate_manifest(result)

    return result
```

---

## Token Budget Management

### Budget Allocation Strategy

```
Total Budget: 100,000 tokens (example, configurable)

┌─────────────────────────────────────────────────────────────────┐
│                    Token Budget Allocation                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Foundation Context (15-20%)                                    │
│  ├── CLAUDE.md:        5,000 tokens (5%)                        │
│  ├── Session State:      500 tokens (0.5%)                      │
│  └── Git State:          300 tokens (0.3%)                      │
│                                                                  │
│  Task Context (20-30%)                                          │
│  ├── Active Task:        500 tokens (0.5%)                      │
│  ├── Sprint Context:   2,000 tokens (2%)                        │
│  └── Sprint Plan:      5,000 tokens (5%)                        │
│                                                                  │
│  Reference Context (10-20%)                                     │
│  ├── Decisions:        1,000 tokens (1%)                        │
│  ├── Config:             500 tokens (0.5%)                      │
│  └── Related Sessions: 1,000 tokens (1%)                        │
│                                                                  │
│  Reserved for Conversation (40-50%)                             │
│  ├── User messages                                              │
│  ├── AI responses                                               │
│  └── Code context (file reads, etc.)                            │
│                                                                  │
│  Buffer (5-10%)                                                 │
│  └── Safety margin for overruns                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Budget Configuration

```yaml
# .vibey/config/context.yaml
context:
  budget:
    # Total tokens to use for initial context loading
    # (remainder reserved for conversation)
    total_tokens: 50000

    # Layer allocations (percentages)
    allocations:
      foundation: 20        # Foundation always gets this much
      task: 30              # Task context allocation
      reference: 20         # Reference context allocation
      explicit: 20          # User-requested context
      buffer: 10            # Safety buffer

    # Minimum guarantees
    minimums:
      claude_md: 5000       # Never truncate below this
      session_state: 200    # Always include session
      git_state: 100        # Always include git

    # Maximum limits
    maximums:
      single_file: 10000    # Max tokens for any single file
      sprint_plan: 5000     # Max for sprint plan
      decisions: 2000       # Max for decision history
```

### Truncation Strategies

When content exceeds budget, use these strategies:

| Strategy | When to Use | How It Works |
|----------|-------------|--------------|
| **Summarize** | Long documents | Extract key points, reduce to summary |
| **Head-truncate** | Recent matters more | Keep end, remove beginning |
| **Tail-truncate** | Beginning matters more | Keep beginning, remove end |
| **Smart-truncate** | Mixed importance | Keep sections with keywords/relevance |
| **Skip** | Low priority | Exclude entirely |

```python
def truncate_context(content: str, max_tokens: int, strategy: str) -> str:
    """Truncate content to fit within token budget."""

    current_tokens = count_tokens(content)
    if current_tokens <= max_tokens:
        return content

    if strategy == "summarize":
        return generate_summary(content, max_tokens)

    elif strategy == "head_truncate":
        # Keep the last N tokens
        lines = content.split('\n')
        result = []
        tokens = 0
        for line in reversed(lines):
            line_tokens = count_tokens(line)
            if tokens + line_tokens > max_tokens:
                break
            result.insert(0, line)
            tokens += line_tokens
        return '\n'.join(result)

    elif strategy == "tail_truncate":
        # Keep the first N tokens
        lines = content.split('\n')
        result = []
        tokens = 0
        for line in lines:
            line_tokens = count_tokens(line)
            if tokens + line_tokens > max_tokens:
                result.append("... [truncated]")
                break
            result.append(line)
            tokens += line_tokens
        return '\n'.join(result)

    elif strategy == "smart_truncate":
        # Keep high-relevance sections
        sections = parse_sections(content)
        scored = [(s, score_relevance(s)) for s in sections]
        scored.sort(key=lambda x: x[1], reverse=True)

        result = []
        tokens = 0
        for section, _ in scored:
            section_tokens = count_tokens(section)
            if tokens + section_tokens <= max_tokens:
                result.append(section)
                tokens += section_tokens
        return '\n'.join(result)
```

---

## Relevance Scoring

### Scoring Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| **Keyword match** | 0.3 | Matches keywords in current task/goal |
| **Recency** | 0.2 | More recent = more relevant |
| **Relationship** | 0.2 | Same task/sprint/track = more relevant |
| **Type match** | 0.15 | Same type of work = more relevant |
| **User signal** | 0.15 | User accessed/referenced = more relevant |

### Scoring Algorithm

```python
def compute_relevance(candidate: ContextCandidate, session: Session) -> float:
    """Compute relevance score for a context candidate."""

    score = 0.0

    # Keyword matching (0-0.3)
    keywords = extract_keywords(session.goal, session.active_task)
    keyword_matches = count_keyword_matches(candidate.content, keywords)
    score += min(keyword_matches / len(keywords), 1.0) * 0.3

    # Recency (0-0.2)
    age_days = (now() - candidate.timestamp).days
    recency = max(0, 1 - (age_days / 30))  # Decay over 30 days
    score += recency * 0.2

    # Relationship (0-0.2)
    if candidate.task_id == session.active_task.id:
        score += 0.2
    elif candidate.sprint_id == session.active_sprint.id:
        score += 0.15
    elif candidate.track_id == session.active_track.id:
        score += 0.1

    # Type match (0-0.15)
    if candidate.type == session.active_task.type:
        score += 0.15
    elif candidate.type in get_related_types(session.active_task.type):
        score += 0.07

    # User signal (0-0.15)
    if candidate.id in session.accessed_items:
        score += 0.15
    elif candidate.id in get_recently_viewed(session.user):
        score += 0.07

    return score
```

---

## Caching & Performance

### Cache Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      Context Cache Layers                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  L1: In-Memory Cache (Session Lifetime)                         │
│  ├── Loaded context files                                       │
│  ├── Token counts                                               │
│  └── Relevance scores                                           │
│  TTL: Session duration                                          │
│                                                                  │
│  L2: File Cache (.vibey/cache/)                                 │
│  ├── Summarized contexts                                        │
│  ├── Token count lookups                                        │
│  └── Relevance pre-computations                                 │
│  TTL: 24 hours or until source changes                          │
│                                                                  │
│  L3: SQLite Index (.vibey/context.db)                           │
│  ├── Context metadata                                           │
│  ├── Full-text search index                                     │
│  └── Relationship graph                                         │
│  TTL: Persistent, invalidated on source change                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cache Invalidation

| Trigger | Invalidation Action |
|---------|---------------------|
| File modified | Invalidate file's cache entries |
| Config changed | Invalidate all cached context |
| Session ended | Clear L1 cache |
| Git commit | Re-index modified files |
| Manual refresh | Clear all caches |

### Pre-computation Strategy

Run these in background during idle time:

1. **Token counts** - Pre-count tokens for all context files
2. **Summaries** - Pre-generate summaries for large files
3. **Embeddings** - Generate embeddings for semantic search
4. **Relevance matrix** - Pre-compute task-to-context relevance

```python
async def precompute_context(project: Project):
    """Background task to pre-compute context artifacts."""

    # Token counts
    for file in project.context_files:
        if not cache.has_token_count(file):
            cache.store_token_count(file, count_tokens(file.content))

    # Summaries for large files
    for file in project.context_files:
        if file.tokens > 5000 and not cache.has_summary(file):
            summary = generate_summary(file.content, 1000)
            cache.store_summary(file, summary)

    # Embeddings for semantic search
    for file in project.context_files:
        if not cache.has_embedding(file):
            embedding = embed(file.content)
            cache.store_embedding(file, embedding)
```

---

## User Control Interface

### CLI Commands

```bash
# View current context selection
$ vibey context show
Foundation Context (5,800 tokens):
  - CLAUDE.md: 5,200 tokens
  - Session: 350 tokens
  - Git state: 250 tokens

Task Context (7,500 tokens):
  - Task: Add session tracking (450 tokens)
  - Sprint: Phase 3.1 - Context Engineering (2,050 tokens)
  - Sprint Plan: SPRINT_PLAN.md (5,000 tokens)

Reference Context (2,200 tokens):
  - Decision: Use YAML+SQLite hybrid (350 tokens)
  - Config: roadmap.yaml (450 tokens)
  - Related session: 01KC7... (1,400 tokens)

Total: 15,500 / 50,000 tokens (31%)
Budget: 34,500 tokens remaining for conversation

# Include additional context
$ vibey context include .vibey/roadmap/context/sprints/phase-3-2/SPRINT_PLAN.md
Added: SPRINT_PLAN.md (3,200 tokens)
Total: 18,700 / 50,000 tokens (37%)

# Exclude context
$ vibey context exclude decisions
Removed: All decisions (350 tokens)
Total: 18,350 / 50,000 tokens (37%)

# Set context budget
$ vibey context budget 30000
Context budget set to 30,000 tokens
Warning: Current context (18,350) will be truncated if budget exceeded

# Search context history
$ vibey context search "authentication"
Found 3 relevant items:
  1. Decision: Use JWT for auth (session 01KC5...)
  2. Sprint plan: User auth sprint (sprint 01KC3...)
  3. CLAUDE.md section: "Authentication Patterns"

# Add search result to context
$ vibey context add 1
Added: Decision: Use JWT for auth (450 tokens)
```

### MCP Tools

```yaml
# MCP tool definitions
tools:
  - name: vibey_context_show
    description: Show current context selection and budget
    parameters: {}
    returns: ContextSummary

  - name: vibey_context_include
    description: Add a file or resource to context
    parameters:
      path:
        type: string
        description: Path to file or resource ID

  - name: vibey_context_exclude
    description: Remove a source from context
    parameters:
      source:
        type: string
        description: Source identifier to exclude

  - name: vibey_context_search
    description: Search for relevant context
    parameters:
      query:
        type: string
        description: Search query
```

### Configuration Overrides

```yaml
# .vibey/config/context.yaml
context:
  # Always include these
  always_include:
    - ".vibey/config/roadmap.yaml"
    - ".vibey/roadmap/context/sprints/${active_sprint}/SPRINT_PLAN.md"

  # Never include these
  always_exclude:
    - "**/*.pyc"
    - "**/__pycache__/**"
    - ".git/**"
    - "node_modules/**"

  # Custom relevance boosts
  relevance_boosts:
    - pattern: "**/test_*.py"
      boost: 0.2
      reason: "Tests are highly relevant for development"

    - pattern: "**/models/*.py"
      boost: 0.15
      reason: "Models define core abstractions"

  # Source priorities (override defaults)
  priorities:
    decisions: 70    # Boost decision priority
    config: 30       # Lower config priority
```

---

## Context Manifest

Every context assembly produces a manifest for auditing:

```yaml
# Generated manifest
context_manifest:
  generated_at: "2025-12-12T10:30:00Z"
  session_id: "01KC8..."
  budget:
    total: 50000
    used: 15500
    remaining: 34500

  sources:
    - id: "claude_md"
      path: "CLAUDE.md"
      layer: "foundation"
      priority: 100
      tokens: 5200
      truncated: false

    - id: "session"
      path: null
      layer: "foundation"
      priority: 100
      tokens: 350
      truncated: false

    - id: "task_01KC..."
      path: ".vibey/roadmap/tasks/01KC....yaml"
      layer: "task"
      priority: 80
      tokens: 450
      truncated: false

    - id: "sprint_plan"
      path: ".vibey/roadmap/context/sprints/phase-3-1/SPRINT_PLAN.md"
      layer: "task"
      priority: 70
      tokens: 5000
      truncated: true
      original_tokens: 8500
      truncation_strategy: "tail_truncate"

    - id: "decision_01KC..."
      path: ".vibey/sessions/01KC.../decisions.yaml#01KC..."
      layer: "reference"
      priority: 50
      relevance_score: 0.85
      tokens: 350
      truncated: false

  user_overrides:
    includes: []
    excludes: []

  warnings:
    - "Sprint plan truncated from 8,500 to 5,000 tokens"
```

---

## Progressive Disclosure

For large contexts, use progressive disclosure:

### Level 1: Summary Only

```markdown
## Active Sprint: Phase 3.1 - Context Engineering Research
Goal: Comprehensive understanding of context engineering landscape
Progress: 4/6 tasks complete (67%)
Current Task: Context Retrieval Design

[Use `vibey context expand sprint` for full details]
```

### Level 2: Key Details

```markdown
## Active Sprint: Phase 3.1 - Context Engineering Research

**Goal:** Comprehensive understanding of context engineering landscape with design for vibey's approach.

**Tasks:**
1. [x] Context Engineering Landscape Research
2. [x] Current Context State Audit
3. [x] Session Context Requirements
4. [x] Context Versioning Strategy Design
5. [ ] Context Retrieval & Selection Design (current)
6. [ ] Synthesis & Recommendations

**Key Decisions:**
- Session-Anchored Versioning selected
- YAML + SQLite hybrid storage

[Use `vibey context expand sprint --full` for complete sprint plan]
```

### Level 3: Full Details

```markdown
[Full SPRINT_PLAN.md content]
```

---

## Implementation Phases

### Phase 1: Basic Selection (Sprint 3.2)

- Implement layered context loading
- Add token counting
- Basic truncation strategies
- CLI `context show` command

### Phase 2: Intelligent Selection (Sprint 3.2)

- Relevance scoring algorithm
- Budget management
- Include/exclude directives
- Context manifest generation

### Phase 3: Caching & Performance (Sprint 3.3)

- L1 in-memory cache
- L2 file cache
- Pre-computation tasks
- Cache invalidation

### Phase 4: Advanced Features (Future)

- Semantic search
- Embedding-based retrieval
- Learning from user feedback
- Cross-session context sharing

---

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Context assembly time | < 500ms | Performance benchmarks |
| Token budget accuracy | Within 5% | Compare estimate vs actual |
| User satisfaction | > 80% "context was helpful" | User survey |
| Relevance precision | > 70% of included content used | Session analysis |
| Cache hit rate | > 80% | Cache metrics |

---

## Open Questions

1. **Semantic Search Integration**
   - When to use keyword vs semantic search?
   - What embedding model to use?
   - Local vs API-based embedding?

2. **Learning from Feedback**
   - How to track which context was actually useful?
   - How to adjust relevance scoring based on feedback?

3. **Cross-Session Context**
   - Should context learned in one session help another?
   - How to handle context divergence across branches?

4. **Team Context Sharing**
   - How to share context discoveries with team members?
   - Privacy implications of shared context?

---

## Conclusion

The Layered Context Pipeline provides:

1. **Structured organization** - Clear hierarchy of context sources
2. **Intelligent selection** - Relevance scoring ensures useful context
3. **Budget management** - Automatic token management with user visibility
4. **User control** - Override capabilities without complexity
5. **Transparency** - Manifests explain what context was used

This design enables vibey to answer:
- "What context is currently loaded and why?"
- "How can I add relevant context without exceeding budget?"
- "What context was used when a decision was made?"

---

## References

- Task 1: Context Engineering Landscape Research (competitor analysis)
- Task 2: Current Context State Audit (vibey's current state)
- Task 3: Session Context Requirements (requirements foundation)
- Task 4: Context Versioning Strategy Design (versioning approach)
