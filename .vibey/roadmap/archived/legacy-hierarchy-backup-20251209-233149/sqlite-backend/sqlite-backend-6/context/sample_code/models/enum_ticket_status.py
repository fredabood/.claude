class TicketStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETION_GATE_CHECK = "completion_gate_check"
    COMPLETED = "completed"
    PRODUCTION_GATE_CHECK = "production_gate_check"
    PRODUCTION_READY = "production_ready"
    DEPLOYED = "deployed"
    WONT_DO = "wont_do"
    SUPERSEDED = "superseded"


class CriterionTargetType(str, Enum):
    COMPLETABLE = "completable"
    FILE_EXISTS = "file_exists"
    TEST_PASSES = "test_passes"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    EXTERNAL = "external"


class InheritMode(str, Enum):
    INHERIT = "inherit"
    OVERRIDE = "override"
    SKIP = "skip"


class ThresholdComparison(str, Enum):
    GTE = "gte"
    GT = "gt"
    EQ = "eq"
    LTE = "lte"
    LT = "lt"


class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    GATE = "gate"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
