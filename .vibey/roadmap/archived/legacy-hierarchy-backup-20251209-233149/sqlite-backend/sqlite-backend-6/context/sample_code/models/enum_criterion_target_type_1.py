class CriterionTargetType(str, Enum):
    COMPLETABLE = "completable"
    FILE_EXISTS = "file_exists"
    TEST_PASSES = "test_passes"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    EXTERNAL = "external"
    ARTIFACT = "artifact"
    SYMBOL_EXISTS = "symbol_exists"      # Sprint 10
    COMMAND_EXISTS = "command_exists"    # Sprint 10
    MCP_TOOL_EXISTS = "mcp_tool_exists"  # Sprint 10
