# G3: Agent Workflow A/B Testing Design Review

**Task ID:** 01KFXJ95JGNAG1RN6022NZVETK
**Phase:** G3: Planned Features
**Date:** 2026-01-29

## Executive Summary

Review of the Agent Workflow A/B Testing design within the "Agent Workflow & Handoff Architecture Review" track (01KD617KB2XD77QC428SZ2Q5RW) covering 6 sprints and 25 planned tasks. The track includes Model Experiments (Sprint 2) and Prompt Experiments (Sprint 3) with metrics collection and analysis. Key finding: Distributed experimentation requires centralized experiment assignment and metrics collection via MLflow on Databricks.

## Methodology

**Files Analyzed:**
- `.vibey/roadmap/tracks/01KD617KB2XD77QC428SZ2Q5RW.yaml` - Track definition
- Sprint definitions for experiment-related sprints

## Findings

### 2. Experiment Framework Table

| Component | Definition Format | Configuration | Lifecycle |
|-----------|-------------------|---------------|-----------|
| Experiment Definition | YAML | `.vibey/experiments/{name}.yaml` | Create → Configure → Run → Analyze → Archive |
| Variant Definition | YAML (nested) | Within experiment file | Defined → Active → Stopped |
| Allocation Rules | YAML (nested) | Percentage or hash-based | Set at creation, immutable during run |
| Metrics Definition | YAML | `.vibey/experiments/metrics/` | Defined → Collecting → Analyzed |
| Analysis Config | YAML | Statistical parameters | Set at creation |

### 3. Model Experiments Table

| Experiment Type | Variants | Metrics | Cost Tracking |
|-----------------|----------|---------|---------------|
| Model Selection | Claude Sonnet, Opus, Haiku | Completion rate, quality score | Token count × model rate |
| Temperature Tuning | 0.0, 0.3, 0.7, 1.0 | Creativity score, correctness | Same model cost |
| Max Tokens | 4K, 8K, 16K, 32K | Truncation rate, completion | Token count |
| Provider A/B | Anthropic, OpenAI, Google | Quality, latency, cost | Provider-specific |
| Agent Assignment | Specialist vs Generalist | Success rate, tokens used | Agent-specific |

### 4. Prompt Experiments Table

| Experiment Type | Template Variants | Quality Metrics | Split Method |
|-----------------|-------------------|-----------------|--------------|
| System Prompt | Detailed vs Concise | Task completion, error rate | User hash |
| Context Format | Markdown vs Structured | Comprehension score | Random |
| Few-Shot Examples | 0, 1, 3, 5 examples | Accuracy, consistency | Round-robin |
| Chain-of-Thought | Enabled vs Disabled | Reasoning quality | Random |
| Persona | Technical vs Friendly | User satisfaction | User preference |

### 5. Metrics Collection Table

| Metric | Collection Method | Storage | Analysis |
|--------|-------------------|---------|----------|
| Token Usage | API response parsing | Delta Lake | Sum, mean, p95 |
| Latency | Request timing | Delta Lake | Mean, p50, p95, p99 |
| Success Rate | Completion detection | Delta Lake | Binomial proportion |
| Quality Score | LLM evaluation | Delta Lake | Mean, distribution |
| Cost | Token × rate calculation | Delta Lake | Sum, trend |
| Error Rate | Exception counting | Delta Lake | Rate, categorization |
| User Satisfaction | Explicit feedback | Delta Lake | NPS, CSAT |

### 6. Distributed Considerations Table

| Concern | Challenge | Solution | Databricks Integration |
|---------|-----------|----------|------------------------|
| Experiment Assignment | Consistent across workers | Deterministic hash | Unity Catalog lookup |
| Metrics Aggregation | Multiple sources | Central collection | Delta Lake streaming |
| Statistical Validity | Sample size, bias | Proper randomization | MLflow experiments |
| Configuration Sync | Experiment state | Central config | Unity Catalog / Delta |
| Cost Allocation | Per-experiment tracking | Tagged requests | Cost tags in MLflow |
| Concurrent Experiments | Interaction effects | Isolation rules | Experiment namespaces |
| Result Analysis | Statistical significance | Proper tests | MLflow + notebooks |

### 7. Experiment Lifecycle Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXPERIMENT LIFECYCLE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌─────────────────────────────────────────────────────────────┐
         │                                                             │
         ▼                                                             │
┌─────────────────┐                                                    │
│ 1. DEFINE       │                                                    │
│ - Hypothesis    │                                                    │
│ - Variants      │                                                    │
│ - Metrics       │                                                    │
│ - Sample size   │                                                    │
└────────┬────────┘                                                    │
         │                                                             │
         ▼                                                             │
┌─────────────────┐                                                    │
│ 2. CONFIGURE    │                                                    │
│ - Allocation %  │                                                    │
│ - Duration      │                                                    │
│ - Stop criteria │                                                    │
└────────┬────────┘                                                    │
         │                                                             │
         ▼                                                             │
┌─────────────────┐       ┌─────────────────┐                         │
│ 3. RUN          │──────▶│ Metrics         │                         │
│ - Random assign │       │ Collection      │                         │
│ - Track metrics │       │ (streaming)     │                         │
│ - Monitor       │       └────────┬────────┘                         │
└────────┬────────┘                │                                   │
         │                         │                                   │
         ▼                         ▼                                   │
┌─────────────────┐       ┌─────────────────┐                         │
│ 4. ANALYZE      │◀──────│ MLflow          │                         │
│ - Statistical   │       │ Dashboard       │                         │
│ - Winner        │       └─────────────────┘                         │
│ - Confidence    │                                                    │
└────────┬────────┘                                                    │
         │                                                             │
         ▼                                                             │
┌─────────────────┐       ┌─────────────────┐                         │
│ 5. DECIDE       │──────▶│ 6. ARCHIVE      │─────────────────────────┘
│ - Roll out?     │       │ or iterate      │
│ - Iterate?      │       │                 │
│ - Stop?         │       │                 │
└─────────────────┘       └─────────────────┘
```

**Distributed Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DISTRIBUTED EXPERIMENTATION                             │
└─────────────────────────────────────────────────────────────────────────────┘

  LOCAL WORKERS                              DATABRICKS CENTRAL
  ─────────────                              ──────────────────

┌─────────────────┐                       ┌─────────────────┐
│ Worker A        │                       │ Experiment      │
│ (Databricks)    │───── Get Assignment ─▶│ Config          │
└────────┬────────┘                       │ (Unity Catalog) │
         │                                └─────────────────┘
         │ Execute with variant                    │
         ▼                                         │
┌─────────────────┐                                │
│ Task Execution  │                                │
│ + Metrics       │                                │
└────────┬────────┘                                │
         │                                         │
         │ Stream metrics                          │
         ▼                                         ▼
┌─────────────────┐                       ┌─────────────────┐
│ Worker B        │───── Metrics ────────▶│ MLflow Tracking │
│ (Databricks)    │                       │ (Delta Lake)    │
└─────────────────┘                       └────────┬────────┘
                                                   │
                                                   │ Analysis
                                                   ▼
                                          ┌─────────────────┐
                                          │ MLflow UI       │
                                          │ Notebooks       │
                                          └─────────────────┘
```

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Experiment tracking planned | Use MLflow on Databricks | M | High |
| Model experiments need coordination | Central assignment service | M | Critical |
| Metrics need aggregation | Stream to Delta Lake | M | High |
| 6 sprints planned | Can start with model experiments | L | Medium |
| Cost tracking important | Tag experiments in MLflow | S | Medium |
| Statistical analysis needed | Use Databricks notebooks | S | Medium |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Experiment framework table documents lifecycle: PASS
- [x] Model experiments table lists >= 2 experiment types: PASS (5 types)
- [x] Metrics collection table lists >= 4 metrics: PASS (7 metrics)
- [x] Distributed considerations address MLflow integration: PASS

## References

- `.vibey/roadmap/tracks/01KD617KB2XD77QC428SZ2Q5RW.yaml:1-72` - Track definition
- Track progress: 0% complete, 6 sprints, 25 tasks
- Sprint 2: Model Experiments, Sprint 3: Prompt Experiments
