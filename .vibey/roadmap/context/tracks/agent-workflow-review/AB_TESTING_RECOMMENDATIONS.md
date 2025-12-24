# A/B Testing Recommendations

**Track:** Agent Workflow & Handoff Architecture Review (01KD617KB2XD77QC428SZ2Q5RW)
**Date:** 2024-12-24
**Status:** Complete

---

## 1. Proposed A/B Testing Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         A/B Testing Architecture                             │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Experiment  │    │   Variant    │    │   Metrics    │                   │
│  │   Registry   │───▶│  Assigner    │───▶│  Collector   │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                    Experiment Context                             │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │       │
│  │  │    Model    │  │   Prompt    │  │  Strategy   │               │       │
│  │  │   Variant   │  │   Variant   │  │   Variant   │               │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                   Implementation Mode                             │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │       │
│  │  │TaskSelector │  │  Executor   │  │  Spawner    │               │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                    Results & Analysis                             │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │       │
│  │  │  Execution  │  │  Aggregated │  │  Experiment │               │       │
│  │  │   Results   │──▶│   Metrics   │──▶│   Report   │               │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │       │
│  └──────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Principles

1. **Non-Intrusive**: Experiments should be opt-in and not affect default behavior
2. **Isolated**: Each experiment variant is cleanly separated
3. **Measurable**: All experiments produce quantifiable metrics
4. **Reproducible**: Experiment results can be verified and replicated
5. **Backward Compatible**: Existing configurations continue to work

---

## 2. Required New Components

### 2.1 ExperimentConfig Dataclass

**File:** `vibey/services/implementation/experiment/config.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path


class ExperimentStatus(str, Enum):
    """Status of an experiment."""
    DRAFT = "draft"           # Being configured
    ACTIVE = "active"         # Currently running
    PAUSED = "paused"         # Temporarily stopped
    COMPLETED = "completed"   # Finished running
    CANCELLED = "cancelled"   # Stopped early


class VariantType(str, Enum):
    """Types of experiment variants."""
    MODEL = "model"           # Different LLM models
    PROMPT = "prompt"         # Different system prompts
    TEMPLATE = "template"     # Different ticket templates
    STRATEGY = "strategy"     # Different execution strategies
    CONFIG = "config"         # Different config parameters


@dataclass
class Variant:
    """
    Single variant in an experiment.

    Attributes:
        id: Unique variant identifier
        name: Human-readable name
        type: Type of variant
        weight: Traffic allocation weight (0.0-1.0)
        config: Variant-specific configuration
        is_control: Whether this is the control group
    """
    id: str
    name: str
    type: VariantType
    weight: float = 0.5
    config: Dict[str, Any] = field(default_factory=dict)
    is_control: bool = False

    def __post_init__(self):
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Variant weight must be 0.0-1.0, got {self.weight}")


@dataclass
class Experiment:
    """
    A/B test experiment definition.

    Attributes:
        id: Unique experiment identifier (ULID)
        name: Human-readable name
        description: Detailed description
        status: Current experiment status
        variants: List of experiment variants
        metrics: Metrics to track
        started_at: When experiment started
        ended_at: When experiment ended
        target_sample_size: Desired sample size per variant
        filters: Optional task filters (track, sprint, complexity)
    """
    id: str
    name: str
    description: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: List[Variant] = field(default_factory=list)
    metrics: List[str] = field(default_factory=lambda: [
        "success_rate",
        "tokens_total",
        "duration_seconds",
        "commits_count",
    ])
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    target_sample_size: int = 100
    filters: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if experiment is currently active."""
        return self.status == ExperimentStatus.ACTIVE

    @property
    def control_variant(self) -> Optional[Variant]:
        """Get the control variant."""
        for v in self.variants:
            if v.is_control:
                return v
        return None

    def get_variant_by_id(self, variant_id: str) -> Optional[Variant]:
        """Get variant by ID."""
        for v in self.variants:
            if v.id == variant_id:
                return v
        return None


@dataclass
class ExperimentConfig:
    """
    Configuration for A/B testing in implementation mode.

    Added to ImplementConfig as an optional experiment field.
    """
    enabled: bool = False
    experiment_id: Optional[str] = None
    auto_assign: bool = True
    storage_path: Path = field(
        default_factory=lambda: Path(".vibey/experiments")
    )
    metrics_retention_days: int = 90
```

### 2.2 ExperimentRegistry

**File:** `vibey/services/implementation/experiment/registry.py`

```python
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from ulid import ULID

from .config import (
    Experiment,
    ExperimentConfig,
    ExperimentStatus,
    Variant,
    VariantType,
)

logger = logging.getLogger(__name__)


class ExperimentRegistry:
    """
    Registry for managing A/B experiments.

    Provides CRUD operations for experiments and their variants,
    with YAML-based persistence.

    Example:
        >>> registry = ExperimentRegistry(Path(".vibey/experiments"))
        >>> experiment = registry.create_experiment(
        ...     name="Model Comparison",
        ...     variants=[
        ...         Variant(id="control", name="Sonnet", type=VariantType.MODEL,
        ...                 config={"model": "claude-sonnet-4-20250514"},
        ...                 is_control=True),
        ...         Variant(id="treatment", name="Opus", type=VariantType.MODEL,
        ...                 config={"model": "claude-opus-4-20250514"}),
        ...     ]
        ... )
        >>> registry.activate_experiment(experiment.id)
    """

    def __init__(self, storage_path: Path):
        """
        Initialize the registry.

        Args:
            storage_path: Directory for experiment storage
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Experiment] = {}
        self._load_experiments()

    def _load_experiments(self) -> None:
        """Load all experiments from storage."""
        for file in self.storage_path.glob("*.yaml"):
            try:
                experiment = self._load_experiment_file(file)
                if experiment:
                    self._cache[experiment.id] = experiment
            except Exception as e:
                logger.warning(f"Failed to load experiment {file}: {e}")

    def _load_experiment_file(self, path: Path) -> Optional[Experiment]:
        """Load single experiment from file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Parse variants
        variants = []
        for v_data in data.get("variants", []):
            variants.append(Variant(
                id=v_data["id"],
                name=v_data["name"],
                type=VariantType(v_data["type"]),
                weight=v_data.get("weight", 0.5),
                config=v_data.get("config", {}),
                is_control=v_data.get("is_control", False),
            ))

        return Experiment(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            status=ExperimentStatus(data.get("status", "draft")),
            variants=variants,
            metrics=data.get("metrics", []),
            started_at=self._parse_datetime(data.get("started_at")),
            ended_at=self._parse_datetime(data.get("ended_at")),
            target_sample_size=data.get("target_sample_size", 100),
            filters=data.get("filters", {}),
        )

    def _save_experiment(self, experiment: Experiment) -> None:
        """Save experiment to file."""
        path = self.storage_path / f"{experiment.id}.yaml"

        data = {
            "id": experiment.id,
            "name": experiment.name,
            "description": experiment.description,
            "status": experiment.status.value,
            "variants": [
                {
                    "id": v.id,
                    "name": v.name,
                    "type": v.type.value,
                    "weight": v.weight,
                    "config": v.config,
                    "is_control": v.is_control,
                }
                for v in experiment.variants
            ],
            "metrics": experiment.metrics,
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
            "ended_at": experiment.ended_at.isoformat() if experiment.ended_at else None,
            "target_sample_size": experiment.target_sample_size,
            "filters": experiment.filters,
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    # CRUD Operations

    def create_experiment(
        self,
        name: str,
        variants: List[Variant],
        description: str = "",
        metrics: Optional[List[str]] = None,
        target_sample_size: int = 100,
        filters: Optional[Dict] = None,
    ) -> Experiment:
        """Create a new experiment."""
        experiment = Experiment(
            id=str(ULID()),
            name=name,
            description=description,
            status=ExperimentStatus.DRAFT,
            variants=variants,
            metrics=metrics or ["success_rate", "tokens_total", "duration_seconds"],
            target_sample_size=target_sample_size,
            filters=filters or {},
        )

        self._cache[experiment.id] = experiment
        self._save_experiment(experiment)
        logger.info(f"Created experiment: {experiment.id} - {name}")
        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self._cache.get(experiment_id)

    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
    ) -> List[Experiment]:
        """List experiments, optionally filtered by status."""
        experiments = list(self._cache.values())
        if status:
            experiments = [e for e in experiments if e.status == status]
        return sorted(experiments, key=lambda e: e.id, reverse=True)

    def get_active_experiments(self) -> List[Experiment]:
        """Get all currently active experiments."""
        return self.list_experiments(status=ExperimentStatus.ACTIVE)

    def activate_experiment(self, experiment_id: str) -> bool:
        """Activate an experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False

        if experiment.status not in (ExperimentStatus.DRAFT, ExperimentStatus.PAUSED):
            logger.warning(f"Cannot activate experiment in {experiment.status} status")
            return False

        experiment.status = ExperimentStatus.ACTIVE
        experiment.started_at = experiment.started_at or datetime.now(timezone.utc)
        self._save_experiment(experiment)
        logger.info(f"Activated experiment: {experiment_id}")
        return True

    def pause_experiment(self, experiment_id: str) -> bool:
        """Pause an active experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.ACTIVE:
            return False

        experiment.status = ExperimentStatus.PAUSED
        self._save_experiment(experiment)
        logger.info(f"Paused experiment: {experiment_id}")
        return True

    def complete_experiment(self, experiment_id: str) -> bool:
        """Mark experiment as completed."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False

        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now(timezone.utc)
        self._save_experiment(experiment)
        logger.info(f"Completed experiment: {experiment_id}")
        return True
```

### 2.3 VariantAssigner

**File:** `vibey/services/implementation/experiment/assigner.py`

```python
import hashlib
import random
from typing import Optional, TYPE_CHECKING

from .config import Experiment, Variant

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket


class VariantAssigner:
    """
    Assigns tasks to experiment variants.

    Supports multiple assignment strategies:
    - Deterministic: Hash-based assignment for reproducibility
    - Random: Pure random assignment
    - Round-robin: Sequential assignment

    Example:
        >>> assigner = VariantAssigner(experiment, strategy="deterministic")
        >>> variant = assigner.assign(task)
        >>> print(f"Task {task.id} assigned to {variant.name}")
    """

    def __init__(
        self,
        experiment: Experiment,
        strategy: str = "deterministic",
        seed: Optional[int] = None,
    ):
        """
        Initialize variant assigner.

        Args:
            experiment: Experiment to assign variants for
            strategy: Assignment strategy (deterministic, random, round_robin)
            seed: Random seed for reproducibility
        """
        self.experiment = experiment
        self.strategy = strategy
        self._rng = random.Random(seed)
        self._round_robin_index = 0

        # Precompute cumulative weights for weighted selection
        self._cumulative_weights = []
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.weight
            self._cumulative_weights.append(cumulative)

        # Normalize weights
        if cumulative > 0:
            self._cumulative_weights = [
                w / cumulative for w in self._cumulative_weights
            ]

    def assign(self, task: "HierarchicalTicket") -> Variant:
        """
        Assign a variant to a task.

        Args:
            task: The task to assign a variant to

        Returns:
            Assigned Variant
        """
        if not self.experiment.variants:
            raise ValueError("Experiment has no variants")

        if self.strategy == "deterministic":
            return self._assign_deterministic(task)
        elif self.strategy == "random":
            return self._assign_random()
        elif self.strategy == "round_robin":
            return self._assign_round_robin()
        else:
            raise ValueError(f"Unknown assignment strategy: {self.strategy}")

    def _assign_deterministic(self, task: "HierarchicalTicket") -> Variant:
        """
        Deterministic hash-based assignment.

        Uses task ID and experiment ID to ensure consistent assignment.
        Same task always gets same variant in same experiment.
        """
        # Create deterministic hash
        hash_input = f"{self.experiment.id}:{task.id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        # Normalize to 0-1 range
        normalized = (hash_value % 10000) / 10000.0

        # Select variant based on cumulative weights
        for i, threshold in enumerate(self._cumulative_weights):
            if normalized < threshold:
                return self.experiment.variants[i]

        return self.experiment.variants[-1]

    def _assign_random(self) -> Variant:
        """Pure random assignment with weights."""
        r = self._rng.random()
        for i, threshold in enumerate(self._cumulative_weights):
            if r < threshold:
                return self.experiment.variants[i]
        return self.experiment.variants[-1]

    def _assign_round_robin(self) -> Variant:
        """Round-robin sequential assignment."""
        variant = self.experiment.variants[
            self._round_robin_index % len(self.experiment.variants)
        ]
        self._round_robin_index += 1
        return variant
```

### 2.4 MetricsCollector

**File:** `vibey/services/implementation/experiment/metrics.py`

```python
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Experiment, Variant

logger = logging.getLogger(__name__)


@dataclass
class ExperimentMetric:
    """
    Single metric observation for an experiment.

    Attributes:
        experiment_id: ID of the experiment
        variant_id: ID of the variant
        task_id: ID of the task
        metric_name: Name of the metric
        value: Metric value (float for compatibility)
        timestamp: When the metric was recorded
        metadata: Additional context
    """
    experiment_id: str
    variant_id: str
    task_id: str
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "experiment_id": self.experiment_id,
            "variant_id": self.variant_id,
            "task_id": self.task_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class VariantMetricsSummary:
    """Summary statistics for a variant."""
    variant_id: str
    variant_name: str
    sample_count: int
    metrics: Dict[str, Dict[str, float]]  # metric_name -> {mean, std, min, max}


@dataclass
class ExperimentReport:
    """Full experiment report with all variant summaries."""
    experiment_id: str
    experiment_name: str
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    total_samples: int
    variant_summaries: List[VariantMetricsSummary]
    winner: Optional[str]  # variant_id of winning variant
    confidence: Optional[float]  # Statistical confidence


class MetricsCollector:
    """
    Collects and stores experiment metrics.

    Uses JSONL format for efficient append-only storage.

    Example:
        >>> collector = MetricsCollector(Path(".vibey/experiments/metrics"))
        >>> collector.record(experiment, variant, task, result)
        >>> summary = collector.get_summary(experiment.id)
    """

    def __init__(self, storage_path: Path):
        """Initialize metrics collector."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_metrics_file(self, experiment_id: str) -> Path:
        """Get path to metrics file for experiment."""
        return self.storage_path / f"{experiment_id}.jsonl"

    def record(
        self,
        experiment: Experiment,
        variant: Variant,
        task_id: str,
        metrics: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record metrics for a task execution.

        Args:
            experiment: The experiment
            variant: The variant used
            task_id: ID of the task
            metrics: Dictionary of metric name -> value
            metadata: Optional additional context
        """
        metrics_file = self._get_metrics_file(experiment.id)
        timestamp = datetime.now(timezone.utc)

        with open(metrics_file, "a") as f:
            for name, value in metrics.items():
                metric = ExperimentMetric(
                    experiment_id=experiment.id,
                    variant_id=variant.id,
                    task_id=task_id,
                    metric_name=name,
                    value=float(value),
                    timestamp=timestamp,
                    metadata=metadata or {},
                )
                f.write(json.dumps(metric.to_dict()) + "\n")

        logger.debug(f"Recorded {len(metrics)} metrics for {task_id}")

    def record_from_result(
        self,
        experiment: Experiment,
        variant: Variant,
        task_id: str,
        result: "ExecutionResult",
    ) -> None:
        """
        Record metrics from an ExecutionResult.

        Extracts standard metrics:
        - success (0 or 1)
        - tokens_input
        - tokens_output
        - tokens_total
        - duration_seconds
        - commits_count
        """
        metrics = {
            "success": 1.0 if result.success else 0.0,
            "tokens_input": float(result.tokens_input),
            "tokens_output": float(result.tokens_output),
            "tokens_total": float(result.tokens_input + result.tokens_output),
        }

        # Add duration if available
        if hasattr(result, "duration_seconds"):
            metrics["duration_seconds"] = float(result.duration_seconds)

        # Add commits count if available
        if hasattr(result, "commits"):
            metrics["commits_count"] = float(len(result.commits))

        metadata = {
            "error_message": result.error_message if hasattr(result, "error_message") else None,
        }

        self.record(experiment, variant, task_id, metrics, metadata)

    def get_metrics(self, experiment_id: str) -> List[ExperimentMetric]:
        """Load all metrics for an experiment."""
        metrics_file = self._get_metrics_file(experiment_id)

        if not metrics_file.exists():
            return []

        metrics = []
        with open(metrics_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    metrics.append(ExperimentMetric(
                        experiment_id=data["experiment_id"],
                        variant_id=data["variant_id"],
                        task_id=data["task_id"],
                        metric_name=data["metric_name"],
                        value=data["value"],
                        timestamp=datetime.fromisoformat(
                            data["timestamp"].replace("Z", "+00:00")
                        ),
                        metadata=data.get("metadata", {}),
                    ))

        return metrics

    def get_summary(self, experiment_id: str) -> Dict[str, VariantMetricsSummary]:
        """
        Get summary statistics for each variant.

        Returns:
            Dictionary of variant_id -> VariantMetricsSummary
        """
        import statistics

        metrics = self.get_metrics(experiment_id)

        # Group by variant and metric
        by_variant: Dict[str, Dict[str, List[float]]] = {}
        variant_names: Dict[str, str] = {}

        for m in metrics:
            if m.variant_id not in by_variant:
                by_variant[m.variant_id] = {}
            if m.metric_name not in by_variant[m.variant_id]:
                by_variant[m.variant_id][m.metric_name] = []
            by_variant[m.variant_id][m.metric_name].append(m.value)

        # Calculate statistics
        summaries = {}
        for variant_id, metrics_dict in by_variant.items():
            metric_stats = {}
            sample_count = 0

            for metric_name, values in metrics_dict.items():
                if metric_name == "success":
                    sample_count = len(values)

                metric_stats[metric_name] = {
                    "mean": statistics.mean(values) if values else 0,
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "count": len(values),
                }

            summaries[variant_id] = VariantMetricsSummary(
                variant_id=variant_id,
                variant_name=variant_names.get(variant_id, variant_id),
                sample_count=sample_count,
                metrics=metric_stats,
            )

        return summaries
```

---

## 3. Configuration Schema Design

### 3.1 Extended ImplementConfig

**File:** `vibey/services/implementation/config.py` (modifications)

```yaml
# .vibey/config/implement.yaml (extended)
implement:
  defaults:
    max_tasks_per_session: 10
    max_tokens_per_session: 100000
    max_tokens_per_task: 25000
    timeout_per_task: 600

  agent:
    model: claude-sonnet-4-20250514
    dangerously_skip_permissions: true
    print_output: true
    max_turns: 50

  # NEW: Experiment configuration
  experiment:
    enabled: true
    experiment_id: "01KD..."  # Active experiment ID (optional)
    auto_assign: true         # Automatically assign variants to tasks
    storage_path: .vibey/experiments
    metrics_retention_days: 90

  # NEW: Prompt templates configuration
  prompts:
    template_dir: .vibey/config/prompts
    default_template: default
    fallback_enabled: true
```

### 3.2 Experiment Definition Schema

**File:** `.vibey/experiments/01KD_MODEL_COMPARISON.yaml`

```yaml
# Experiment: Model Comparison
id: 01KD617KB2XD77QC428SZ2Q5RW
name: "Sonnet vs Opus for Complex Tasks"
description: |
  Compare Claude Sonnet 4 and Claude Opus 4 for complex implementation tasks
  to determine optimal model selection by complexity.

status: active
started_at: "2024-12-24T00:00:00Z"

variants:
  - id: control
    name: "Claude Sonnet 4"
    type: model
    weight: 0.5
    is_control: true
    config:
      model: claude-sonnet-4-20250514
      max_turns: 50

  - id: treatment
    name: "Claude Opus 4"
    type: model
    weight: 0.5
    config:
      model: claude-opus-4-20250514
      max_turns: 75  # Allow more turns for complex reasoning

metrics:
  - success_rate
  - tokens_total
  - duration_seconds
  - commits_count
  - code_quality_score  # Custom metric

target_sample_size: 200

filters:
  complexity:
    - complex
    - very_complex
  track_ids: []  # Empty = all tracks
```

### 3.3 Prompt Template Schema

**File:** `.vibey/config/prompts/default.yaml`

```yaml
# Prompt Template: Default
id: default
name: "Default Implementation Prompt"
version: "1.0.0"

system_prompt: |
  You are implementing a development task.

  ## Task Information
  **Task ID:** {{ task.id }}
  **Task Name:** {{ task.name }}
  **Status:** {{ task.status }}
  **Priority:** {{ task.priority }}

  ## Task Description
  {{ task.description }}

  {% if plan %}
  ## Implementation Plan
  {{ plan }}
  {% endif %}

  {% if relevant_files %}
  ## Relevant Files
  {% for file in relevant_files %}
  - `{{ file }}`
  {% endfor %}
  {% endif %}

  {% if criteria %}
  ## Acceptance Criteria
  {% for c in criteria %}
  - [ ] {{ c }}
  {% endfor %}
  {% endif %}

  ## Instructions
  1. Read and understand the task requirements
  2. Examine the relevant files listed above
  3. Implement the changes needed to satisfy all acceptance criteria
  4. Ensure your implementation follows project coding standards
  5. Create commits with clear messages referencing this task

task_prompt: |
  Execute task: {{ task.name }}

  {{ task.description }}

variables:
  - task
  - plan
  - relevant_files
  - criteria
  - parent_context
```

---

## 4. Metrics and Analysis Requirements

### 4.1 Core Metrics

| Metric | Type | Description | Aggregation |
|--------|------|-------------|-------------|
| success_rate | Float | Tasks completed successfully / total | Mean |
| tokens_input | Integer | Input tokens consumed | Sum, Mean |
| tokens_output | Integer | Output tokens generated | Sum, Mean |
| tokens_total | Integer | Total tokens (input + output) | Sum, Mean |
| duration_seconds | Float | Execution time | Mean, P50, P95 |
| commits_count | Integer | Git commits created | Sum, Mean |
| retries_count | Integer | Retry attempts | Sum, Mean |
| error_rate | Float | Tasks with errors / total | Mean |

### 4.2 Derived Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| efficiency | success_rate / tokens_total | Success per token |
| speed_score | 1 / duration_seconds | Inverse of time |
| cost_effectiveness | success_rate / (tokens_total * cost_per_token) | Value per dollar |
| reliability | 1 - error_rate | Task reliability |

### 4.3 Statistical Analysis

```python
@dataclass
class StatisticalTest:
    """Results of statistical comparison between variants."""

    test_name: str              # "two_proportion_z_test", "t_test", etc.
    metric_name: str
    control_value: float
    treatment_value: float
    difference: float
    relative_difference: float  # Percentage change
    p_value: float
    confidence_interval: tuple[float, float]
    is_significant: bool        # p_value < alpha
    alpha: float = 0.05

    @property
    def winner(self) -> Optional[str]:
        """Determine winner based on significance and direction."""
        if not self.is_significant:
            return None
        return "treatment" if self.difference > 0 else "control"
```

---

## 5. MCP Tool Additions Needed

### 5.1 Experiment Management Tools

```python
# New MCP tools for experiment management

def get_experiment_tools() -> List[Dict[str, Any]]:
    """Get experiment management MCP tools."""
    return [
        {
            "name": "vibey_create_experiment",
            "description": "Create a new A/B testing experiment",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Experiment name"},
                    "description": {"type": "string", "description": "Experiment description"},
                    "variant_type": {
                        "type": "string",
                        "enum": ["model", "prompt", "template", "strategy"],
                        "description": "Type of experiment"
                    },
                    "variants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "config": {"type": "object"},
                                "weight": {"type": "number"},
                                "is_control": {"type": "boolean"}
                            }
                        }
                    },
                    "target_sample_size": {"type": "integer", "default": 100}
                },
                "required": ["name", "variant_type", "variants"]
            }
        },
        {
            "name": "vibey_list_experiments",
            "description": "List all A/B experiments",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["draft", "active", "paused", "completed", "cancelled"],
                        "description": "Filter by status"
                    }
                }
            }
        },
        {
            "name": "vibey_get_experiment",
            "description": "Get details of an experiment",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string", "description": "Experiment ULID"}
                },
                "required": ["experiment_id"]
            }
        },
        {
            "name": "vibey_activate_experiment",
            "description": "Activate a draft or paused experiment",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"}
                },
                "required": ["experiment_id"]
            }
        },
        {
            "name": "vibey_pause_experiment",
            "description": "Pause an active experiment",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"}
                },
                "required": ["experiment_id"]
            }
        },
        {
            "name": "vibey_complete_experiment",
            "description": "Mark an experiment as completed",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"}
                },
                "required": ["experiment_id"]
            }
        },
        {
            "name": "vibey_get_experiment_results",
            "description": "Get results and analysis for an experiment",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"},
                    "include_raw_metrics": {"type": "boolean", "default": False}
                },
                "required": ["experiment_id"]
            }
        },
        {
            "name": "vibey_compare_variants",
            "description": "Statistical comparison between variants",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "string"},
                    "metric": {"type": "string", "description": "Metric to compare"},
                    "alpha": {"type": "number", "default": 0.05}
                },
                "required": ["experiment_id", "metric"]
            }
        }
    ]
```

### 5.2 Prompt Template Tools

```python
def get_prompt_template_tools() -> List[Dict[str, Any]]:
    """Get prompt template management MCP tools."""
    return [
        {
            "name": "vibey_list_prompt_templates",
            "description": "List available prompt templates",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "vibey_get_prompt_template",
            "description": "Get a specific prompt template",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "template_id": {"type": "string"}
                },
                "required": ["template_id"]
            }
        },
        {
            "name": "vibey_preview_prompt",
            "description": "Preview a rendered prompt for a task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "template_id": {"type": "string"}
                },
                "required": ["task_id"]
            }
        }
    ]
```

---

## 6. Timeline and Dependencies

### 6.1 Sprint Timeline

```
Sprint 1 (Weeks 1-2): Foundation
├── ExperimentConfig dataclass
├── ExperimentRegistry
├── VariantAssigner
├── Integration with ImplementConfig
└── Basic CLI commands

Sprint 2 (Weeks 3-4): Model Experiments
├── ModelExperiment variant type
├── Spawner modification for variant-aware model selection
├── Model metrics collection
├── Model comparison analysis
└── MCP tools for model experiments

Sprint 3 (Weeks 5-6): Prompt Experiments
├── PromptTemplateRegistry
├── Jinja2 template engine integration
├── Refactor hardcoded prompts to templates
├── PromptExperiment variant type
├── Context builder modification
└── MCP tools for prompt templates

Sprint 4 (Weeks 7-8): Metrics & Analysis
├── MetricsCollector implementation
├── Statistical analysis functions
├── ExperimentReport generation
├── CLI analysis commands
├── MCP tools for results
└── Dashboard visualization

Sprint 5 (Weeks 9-10): Advanced Experiments
├── TicketTemplateExperiment
├── ExecutionStrategyExperiment
├── Strategy comparison metrics
├── Adaptive selection (if time permits)
└── Documentation and guides
```

### 6.2 Dependency Graph

```
                    Sprint 1
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
      Sprint 2     Sprint 3     (Sprint 4 depends on 2,3)
          │            │            │
          └────────────┴────────────┘
                       │
                       ▼
                   Sprint 4
                       │
                       ▼
                   Sprint 5
```

### 6.3 Risk-Adjusted Timeline

| Sprint | Optimistic | Expected | Pessimistic |
|--------|------------|----------|-------------|
| Sprint 1 | 1 week | 2 weeks | 3 weeks |
| Sprint 2 | 1 week | 2 weeks | 3 weeks |
| Sprint 3 | 2 weeks | 2 weeks | 4 weeks |
| Sprint 4 | 1 week | 2 weeks | 3 weeks |
| Sprint 5 | 1 week | 2 weeks | 4 weeks |
| **Total** | **6 weeks** | **10 weeks** | **17 weeks** |

---

## 7. Implementation Checklist

### Sprint 1: Foundation

- [ ] Create `vibey/services/implementation/experiment/` module
- [ ] Implement `ExperimentConfig` dataclass
- [ ] Implement `Variant` and `VariantType`
- [ ] Implement `Experiment` dataclass
- [ ] Implement `ExperimentRegistry` with YAML persistence
- [ ] Implement `VariantAssigner` with deterministic, random, round-robin strategies
- [ ] Add `experiment` field to `ImplementConfig`
- [ ] Add experiment loading to `ImplementConfig.load()`
- [ ] Add experiment merging to `ImplementConfig.merge_cli_options()`
- [ ] Create `vibey experiment` CLI command group
- [ ] Add `vibey experiment create` command
- [ ] Add `vibey experiment list` command
- [ ] Add `vibey experiment show` command
- [ ] Add `vibey experiment activate` command
- [ ] Add `vibey experiment pause` command
- [ ] Write unit tests for all components
- [ ] Write integration tests

### Sprint 2: Model Experiments

- [ ] Define `MODEL` variant type behavior
- [ ] Modify `AgentSpawner._build_command()` for variant-aware model selection
- [ ] Modify `ClaudeTaskExecutor.spawn_agent()` for variant model
- [ ] Add `experiment_id` field to `ExecutionResult`
- [ ] Add `variant_id` field to `ExecutionResult`
- [ ] Implement basic model metrics (tokens, success, duration)
- [ ] Create model comparison functions
- [ ] Add `vibey experiment compare` command
- [ ] Register experiment MCP tools in server
- [ ] Write tests for model experiments

### Sprint 3: Prompt Experiments

- [ ] Create `PromptTemplate` dataclass
- [ ] Create `PromptTemplateRegistry`
- [ ] Integrate Jinja2 for template rendering
- [ ] Create default prompt template file
- [ ] Refactor `spawner._build_system_prompt()` to use templates
- [ ] Refactor `spawner._build_task_prompt()` to use templates
- [ ] Refactor `context.build_system_prompt()` to use templates
- [ ] Refactor `executor._build_fallback_system_prompt()` to use templates
- [ ] Define `PROMPT` variant type behavior
- [ ] Modify context builder for variant-aware template selection
- [ ] Add prompt template MCP tools
- [ ] Create sample prompt variant templates
- [ ] Write tests for prompt experiments

### Sprint 4: Metrics & Analysis

- [ ] Implement `ExperimentMetric` dataclass
- [ ] Implement `MetricsCollector` with JSONL storage
- [ ] Implement `record_from_result()` helper
- [ ] Implement `VariantMetricsSummary`
- [ ] Implement `ExperimentReport`
- [ ] Add metrics collection to `ImplementationLoop._handle_result()`
- [ ] Implement statistical comparison functions (t-test, z-test)
- [ ] Implement confidence interval calculation
- [ ] Add `vibey experiment results` command
- [ ] Add `vibey experiment analyze` command
- [ ] Register analysis MCP tools
- [ ] Create metrics retention policy
- [ ] Write tests for metrics and analysis

### Sprint 5: Advanced Experiments

- [ ] Define `TEMPLATE` variant type for ticket templates
- [ ] Define `STRATEGY` variant type for execution strategies
- [ ] Implement strategy selection mechanism
- [ ] Add strategy metrics (parallelism, throughput)
- [ ] Implement multi-metric optimization
- [ ] (Stretch) Implement adaptive strategy selector
- [ ] Create comprehensive documentation
- [ ] Create experiment design guide
- [ ] Write end-to-end experiment scenario tests

---

*Document generated by deep research analysis for Track 01KD617KB2XD77QC428SZ2Q5RW*
