class CriterionTargetType(str, Enum):
    """All criterion target types."""

    # ═══════════════════════════════════════════════════════════════
    # EXISTING TYPES (from Part 2)
    # ═══════════════════════════════════════════════════════════════
    COMPLETABLE = "completable"    # References another ticket
    FILE_EXISTS = "file_exists"    # Raw file existence (no artifact entity)
    TEST_PASSES = "test_passes"    # Test execution
    THRESHOLD = "threshold"        # Metric threshold
    MANUAL = "manual"              # Human assessment
    EXTERNAL = "external"          # External system check

    # ═══════════════════════════════════════════════════════════════
    # NEW: ARTIFACT-BASED TYPES
    # ═══════════════════════════════════════════════════════════════
    ARTIFACT = "artifact"          # References an Artifact entity

    # ═══════════════════════════════════════════════════════════════
    # NEW: CODE VERIFICATION TYPES (Sprint 10)
    # ═══════════════════════════════════════════════════════════════
    SYMBOL_EXISTS = "symbol_exists"      # Verify code symbol (class, function)
    COMMAND_EXISTS = "command_exists"    # Verify CLI command
    MCP_TOOL_EXISTS = "mcp_tool_exists"  # Verify MCP tool
