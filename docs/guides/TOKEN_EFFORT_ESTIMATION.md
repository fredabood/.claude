# Token-Based Effort Estimation Guide

**Version:** 1.0
**Created:** 2025-11-22
**Status:** Active

## Overview

Token-based effort estimation replaces traditional time-based estimates (hours, days, weeks) with token consumption metrics. This approach better reflects the reality of AI-assisted development where the same task can vary wildly in wall-clock time but has predictable token usage patterns.

## Why Tokens Instead of Time?

### Problems with Time-Based Estimates

1. **Inconsistency**: Same task may take 5 minutes or 5 hours depending on context
2. **No correlation**: Time spent doesn't reflect actual work complexity
3. **No budgeting**: Can't allocate resources based on time estimates
4. **No efficiency tracking**: Can't measure improvement over time

### Benefits of Token-Based Estimates

1. **Predictability**: Tokens correlate directly with actual effort
2. **Budgeting**: Can allocate token budgets per sprint/track
3. **Efficiency**: Track tokens/task to measure improvement
4. **Cost**: Direct correlation with API costs
5. **Planning**: Know if sprint fits within context window limits

## Size Categories

Tasks are categorized into five size buckets based on expected token consumption:

| Category | Token Range | Description | Examples |
|----------|-------------|-------------|----------|
| **S** (Small) | <10K tokens | Quick fixes, simple changes | Typo fixes, config updates, simple renames |
| **M** (Medium) | 10K-30K tokens | Feature additions, moderate refactors | Add a new API endpoint, refactor a function |
| **L** (Large) | 30K-75K tokens | Complex features, significant changes | New feature with tests, multi-file refactor |
| **XL** (X-Large) | 75K-150K tokens | Major features, architectural changes | New subsystem, major migration |
| **XXL** (XX-Large) | 150K+ tokens | Should be split into multiple tasks | Full rewrites, massive refactors |

### When to Split Tasks

If a task is estimated at XXL (150K+ tokens), consider splitting it:

- Break into logical phases (design, implement, test)
- Split by component or module
- Separate refactoring from feature work
- Create separate tasks for documentation

## Estimation Factors

Token estimates are derived from multiple factors:

### 1. Complexity Rating

| Complexity | Base Tokens | Description |
|------------|-------------|-------------|
| Simple | 5,000 | Straightforward changes, well-defined scope |
| Medium | 20,000 | Some exploration needed, moderate iteration |
| Complex | 50,000 | Significant exploration, multiple iterations |

### 2. Task Type Multipliers

| Task Type | Multiplier | Rationale |
|-----------|------------|-----------|
| Development | 1.0x | Standard implementation work |
| Testing | 0.8x | Tests are more structured |
| Documentation | 0.6x | Less iteration required |
| Refactoring | 1.2x | Requires understanding existing code |
| Bug Fix | 0.7x | Usually focused scope |
| Feature | 1.3x | More exploration and iteration |
| Migration | 1.5x | Context-heavy work |
| Investigation | 0.5x | Mostly reading/searching |

### 3. Description Analysis

The task description is analyzed for:

- **Length**: Longer descriptions often indicate more complex tasks
- **High-complexity keywords**: "complex", "refactor", "architecture", "migration", "comprehensive"
- **Low-complexity keywords**: "simple", "quick", "minor", "trivial", "fix"

## Using Token Estimates

### In Task Definitions

```yaml
task:
  id: myproject-sprint1-task-001
  title: Implement user authentication
  estimated_tokens: 45000
  size_category: L
  actual_tokens: null  # Updated after completion
```

### In Sprint Planning

```yaml
sprint:
  id: myproject-sprint1
  metadata:
    estimated_tokens: 180000  # Sum of task estimates
    token_budget: 200000      # Max allowed for sprint
```

### CLI Commands

```bash
# Estimate tokens for a task
vibey roadmap estimate-tokens --task myproject-sprint1-task-001

# View token budget status
vibey roadmap show myproject-sprint1 --tokens

# Analyze token efficiency
vibey roadmap analyze-tokens --sprint myproject-sprint1
```

## Converting Time Estimates to Tokens

For backward compatibility, time estimates can be converted:

| Time | Tokens | Rationale |
|------|--------|-----------|
| 30 min | 5,000 | Quick task |
| 1 hour | 10,000 | Small task |
| 2 hours | 20,000 | Medium task |
| 4 hours | 40,000 | Larger task |
| 1 day | 60,000 | Full day's work |
| 1 week | 300,000 | Major effort |

The formula: `tokens = hours * 10,000`

This assumes roughly 10K tokens per productive hour of AI-assisted development.

## Tracking Actual Usage

After completing a task, record actual token usage:

```yaml
task:
  id: myproject-sprint1-task-001
  estimated_tokens: 45000
  actual_tokens: 52000
  metadata:
    token_efficiency: 1.16  # actual/estimated
```

### Efficiency Analysis

- **< 0.8**: Task was over-estimated, or very efficient
- **0.8 - 1.2**: Good estimate
- **1.2 - 1.5**: Slight under-estimate, acceptable
- **> 1.5**: Significant under-estimate, investigate root cause

## Best Practices

### 1. Start with Size Categories

Don't try to guess exact tokens. Pick a size category first:
- "This feels like a Medium task (10K-30K)"
- Use the category midpoint as the estimate

### 2. Use Historical Data

Track actual token usage and use it to improve estimates:
- What did similar tasks actually consume?
- Are certain task types consistently over/under?

### 3. Include Buffer for Complexity

For complex or uncertain tasks:
- Add 20-30% buffer
- Or size up to the next category

### 4. Review Post-Sprint

After each sprint:
- Compare estimated vs actual
- Identify systematic over/under estimates
- Adjust estimation factors accordingly

### 5. Split Large Tasks

If estimated > 100K tokens:
- Consider breaking into smaller pieces
- Each sub-task should be completable in a reasonable context window
- Linked tasks can reference each other

## Programmatic Usage

```python
from vibey.roadmap.token_estimation import (
    TokenEstimator,
    convert_time_to_tokens,
    analyze_token_efficiency,
)
from vibey.roadmap.models.common import Complexity, SizeCategory

# Create estimator
estimator = TokenEstimator()

# Estimate from task details
estimate = estimator.estimate_from_task(
    title="Implement OAuth2 authentication",
    description="Add OAuth2 support with Google and GitHub providers",
    complexity=Complexity.COMPLEX,
    task_type="feature",
)
print(f"Estimated: {estimate.estimated_tokens:,} tokens ({estimate.size_category.value})")

# Convert time-based estimate
tokens = convert_time_to_tokens("4-6 hours")
print(f"4-6 hours = {tokens:,} tokens")

# Get size category from tokens
category = SizeCategory.from_tokens(50000)
print(f"50K tokens = Size {category.value}")
```

## FAQ

### Why 10K tokens/hour?

This is a rough heuristic based on observed AI-assisted development patterns:
- Reading code: ~2-3K tokens
- Writing code: ~3-5K tokens
- Iterations/refinements: ~2-3K tokens
- Context loading: ~2K tokens

Total: ~10K per productive hour

### What if I don't know the token usage?

Start with size categories and refine over time. The estimation utilities provide reasonable defaults based on task complexity and type.

### How do I measure actual tokens?

Token usage is tracked per conversation/session. Many AI coding assistants report token usage in their responses or billing.

### Can I still use time estimates?

Yes! The system maintains backward compatibility. Time estimates are auto-converted to tokens using the 10K/hour formula.

## Related Documentation

- [Roadmap User Guide](./ROADMAP_USER_GUIDE.md)
- [Roadmap CLI Reference](./ROADMAP_CLI_REFERENCE.md)
- [Schema Migration Guide](./SCHEMA_MIGRATION.md)
