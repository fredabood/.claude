# Task 1.5.4: Re-audit MCP and Adapters Modules - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QT7 |
| Sprint | Sprint 1.5: Module Quality Re-Audit |
| Type | research |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 3,000 |
| Dependencies | Sprint 1 (File Inventory Refresh) |

## Objective

Re-audit the MCP server module and platform adapters. Inventory all tools, resources, and prompts. Verify adapter implementations are consistent across all 9+ platforms. Compare findings with Dec 12 baseline.

## Module Scope

### MCP Module

```
vibey/mcp/                           # 41 Python files total
├── __init__.py                      # Module exports
├── server.py                        # Main MCP server (~24KB)
├── README.md                        # MCP documentation
│
├── adapters/                        # MCP-specific adapters (3 files)
│   ├── __init__.py
│   └── [adapter files]
│
├── discovery/                       # Discovery tools (8 files)
│   ├── __init__.py
│   └── [discovery files]
│
├── prompts/                         # MCP prompts (7 files)
│   ├── __init__.py
│   └── [prompt definitions]
│
├── resources/                       # MCP resources (8 files)
│   ├── __init__.py
│   └── [resource definitions]
│
├── tools/                           # MCP tools (9 files)
│   ├── __init__.py
│   ├── content_tools.py             # Content tools (~20KB)
│   ├── context_tools.py             # Context tools (~27KB)
│   ├── query_tools.py               # Query tools (~19KB)
│   ├── sprint_tools.py              # Sprint tools (~11KB)
│   ├── submodule_tools.py           # Submodule tools (~31KB)
│   ├── task_tools.py                # Task tools (~10KB)
│   └── token_tools.py               # Token tools (~47KB)
│
├── utils/                           # MCP utilities (4 files)
│   ├── __init__.py
│   └── [utility files]
│
└── tests/                           # MCP tests (8 files)
```

### Adapters Module

```
vibey/adapters/                      # 44 Python files total
├── __init__.py                      # Module exports (~2KB)
├── base.py                          # Base adapter (~9KB)
├── registry.py                      # Adapter registry (~6KB)
├── types.py                         # Adapter types (~2KB)
│
├── aider.py                         # Aider adapter (~19KB)
├── claude_code.py                   # Claude Code adapter (~11KB)
├── goose.py                         # Goose adapter (~11KB)
│
├── amazonq/                         # Amazon Q adapter (3 files)
│   ├── __init__.py
│   └── [amazon q files]
│
├── cody/                            # Cody adapter (3 files)
│   ├── __init__.py
│   └── [cody files]
│
├── continuedev/                     # Continue adapter (5 files)
│   ├── __init__.py
│   └── [continue files]
│
├── copilot/                         # Copilot adapter (3 files)
│   ├── __init__.py
│   └── [copilot files]
│
├── cursor/                          # Cursor adapter (3 files)
│   ├── __init__.py
│   └── [cursor files]
│
├── gemini/                          # Gemini adapter (10 files)
│   ├── __init__.py
│   └── [gemini files]
│
├── jetbrains/                       # JetBrains adapter (3 files)
│   ├── __init__.py
│   └── [jetbrains files]
│
├── pm/                              # PM adapter (5 files)
│   ├── __init__.py
│   └── [pm files]
│
├── replit/                          # Replit adapter (3 files)
│   ├── __init__.py
│   └── [replit files]
│
├── vscode/                          # VS Code adapter (3 files)
│   ├── __init__.py
│   └── [vscode files]
│
└── windsurf/                        # Windsurf adapter (3 files)
    ├── __init__.py
    └── [windsurf files]
```

## Key Changes Since Dec 12

| Change | Description |
|--------|-------------|
| New token_tools.py | Token management tools (~47KB, largest) |
| New submodule_tools.py | Submodule management tools (~31KB) |
| New context_tools.py | Context system tools (~27KB) |
| New pm/ adapter | PM adapter subdirectory |
| Expanded gemini/ | More Gemini adapter files |

## Audit Checklist

### Part A: MCP Module Audit

#### 1. Tool Inventory

**Current Tool Files:**
| File | Size | Expected Tools |
|------|------|----------------|
| content_tools.py | ~20KB | Content access tools |
| context_tools.py | ~27KB | Context management tools |
| query_tools.py | ~19KB | Query/search tools |
| sprint_tools.py | ~11KB | Sprint management tools |
| submodule_tools.py | ~31KB | Submodule tools |
| task_tools.py | ~10KB | Task CRUD tools |
| token_tools.py | ~47KB | Token estimation tools |

**Tool Analysis:**
```bash
# Count tools defined
grep -r "@mcp.tool\|def.*tool" vibey/mcp/tools --include="*.py"

# List tool names
grep -r "name=" vibey/mcp/tools --include="*.py" | grep -v "__pycache__"
```

**Checklist:**
- [ ] Total tool count (expected: ~76)
- [ ] New tools since Dec 12
- [ ] Tool documentation completeness
- [ ] Tool input/output schema validation
- [ ] Tool error handling consistency

#### 2. Resource Inventory

**Resource Analysis:**
```bash
# Count resources
grep -r "@mcp.resource\|def.*resource" vibey/mcp/resources --include="*.py"
```

**Checklist:**
- [ ] Total resource count (expected: ~8)
- [ ] Resource content accuracy
- [ ] Resource versioning
- [ ] New resources since Dec 12

#### 3. Prompt Inventory

**Prompt Analysis:**
```bash
# Count prompts
grep -r "@mcp.prompt\|def.*prompt" vibey/mcp/prompts --include="*.py"
```

**Checklist:**
- [ ] Total prompt count (expected: ~4)
- [ ] Prompt quality review
- [ ] Prompt documentation
- [ ] New prompts since Dec 12

#### 4. MCP Server Quality

**server.py Analysis:**
- [ ] Server initialization
- [ ] Tool registration
- [ ] Resource registration
- [ ] Prompt registration
- [ ] Error handling
- [ ] Logging

#### 5. MCP Tests

```bash
# Run MCP tests
pytest vibey/mcp/tests/ -v
```

### Part B: Adapters Module Audit

#### 1. Adapter Inventory

**Expected Adapters (9+):**
| Adapter | Directory/File | Status |
|---------|----------------|--------|
| Claude Code | claude_code.py | Active |
| Cursor | cursor/ | Active |
| Copilot | copilot/ | Active |
| VS Code | vscode/ | Active |
| Goose | goose.py | Active |
| Gemini | gemini/ | Active |
| Aider | aider.py | Active |
| Continue | continuedev/ | Active |
| Windsurf | windsurf/ | Active |
| Amazon Q | amazonq/ | Active |
| Cody | cody/ | Active |
| JetBrains | jetbrains/ | Active |
| Replit | replit/ | Active |
| PM | pm/ | New? |

**Verification:**
```bash
# List all adapters
ls -la vibey/adapters/
ls -la vibey/adapters/*/
```

#### 2. Base Adapter Compliance

**base.py Review:**
- [ ] Abstract methods defined
- [ ] Interface complete
- [ ] Documentation adequate

**Adapter Implementation Check:**
```bash
# Check each adapter implements base
for adapter in vibey/adapters/*.py vibey/adapters/*/__init__.py; do
    grep -l "BaseAdapter\|Adapter" "$adapter" 2>/dev/null
done
```

**Checklist per Adapter:**
- [ ] Inherits from BaseAdapter
- [ ] Implements all required methods
- [ ] Proper error handling
- [ ] Configuration handling
- [ ] Output format consistent

#### 3. Adapter Consistency Analysis

**Method Signatures:**
```bash
# Check deploy method signatures
grep -r "def deploy" vibey/adapters --include="*.py"

# Check config method signatures
grep -r "def get_config\|def set_config" vibey/adapters --include="*.py"
```

**Consistency Checks:**
- [ ] Consistent method names
- [ ] Consistent return types
- [ ] Consistent error handling
- [ ] Consistent configuration format

#### 4. Registry Verification

**registry.py Review:**
- [ ] All adapters registered
- [ ] Lookup mechanism working
- [ ] Platform detection accurate

```bash
# Check registry
grep -r "register\|ADAPTERS" vibey/adapters/registry.py
```

## Quality Metrics to Collect

```python
mcp_metrics = {
    "tools": {
        "total": 0,              # Count
        "per_file": {},          # Per file counts
        "documented": 0,         # With docstrings
        "with_schema": 0,        # With input/output schemas
    },
    "resources": {
        "total": 0,
        "documented": 0,
    },
    "prompts": {
        "total": 0,
        "documented": 0,
    },
    "server": {
        "lines": 0,
        "complexity": 0,
    },
    "tests": {
        "count": 0,
        "coverage": 0,
    },
}

adapters_metrics = {
    "adapters": {
        "total": 14,             # Expected count
        "standalone_files": 3,   # aider.py, claude_code.py, goose.py
        "subdirectories": 11,
    },
    "compliance": {
        "implements_base": 0,
        "all_methods_implemented": 0,
        "consistent_signatures": 0,
    },
    "quality": {
        "docstring_coverage": 0,
        "type_hint_coverage": 0,
        "test_coverage": 0,
    },
}
```

## Commands for Analysis

```bash
# === MCP Analysis ===
echo "=== MCP File Counts ==="
find vibey/mcp -name "*.py" | wc -l
find vibey/mcp/tools -name "*.py" | wc -l
find vibey/mcp/resources -name "*.py" | wc -l
find vibey/mcp/prompts -name "*.py" | wc -l

echo "=== MCP Tool Count ==="
grep -r "def " vibey/mcp/tools --include="*.py" | grep -v "__" | wc -l

echo "=== MCP Lines of Code ==="
find vibey/mcp -name "*.py" -exec cat {} + | wc -l

echo "=== Largest MCP Files ==="
find vibey/mcp -name "*.py" -exec wc -l {} + | sort -rn | head -10

# === Adapters Analysis ===
echo "=== Adapter Counts ==="
find vibey/adapters -name "*.py" | wc -l
ls -d vibey/adapters/*/ 2>/dev/null | wc -l

echo "=== Adapters List ==="
ls vibey/adapters/

echo "=== Adapter LoC ==="
find vibey/adapters -name "*.py" -exec cat {} + | wc -l

echo "=== Largest Adapter Files ==="
find vibey/adapters -name "*.py" -exec wc -l {} + | sort -rn | head -10

# === Interface Compliance ===
echo "=== BaseAdapter References ==="
grep -r "BaseAdapter" vibey/adapters --include="*.py" | grep -v "__pycache__"

# === Tests ===
echo "=== MCP Tests ==="
pytest vibey/mcp/tests/ -v --collect-only 2>&1 | tail -20
```

## Deliverables

1. **MODULE_QUALITY_AUDIT_MCP.md**
   - Complete MCP module audit
   - Tool/resource/prompt inventory
   - Quality metrics
   - Comparison with Dec 12

2. **MODULE_QUALITY_AUDIT_ADAPTERS.md**
   - Complete adapters module audit
   - Adapter inventory
   - Compliance analysis
   - Quality metrics

3. **MCP_TOOL_INVENTORY.yaml**
   - Machine-readable tool list
   - Tool metadata

4. **ADAPTER_COMPLIANCE_MATRIX.md**
   - Adapter vs required methods matrix
   - Compliance scores

## Output Template

### MCP Audit Output

```markdown
# MCP Module Quality Audit
**Date:** December 28, 2024
**Baseline:** December 12, 2024

## Executive Summary

The MCP module provides 76 tools, 8 resources, and 4 prompts for AI assistant
integration via the Model Context Protocol...

## Tool Inventory

### Summary
| Category | Count | Dec 12 | Change |
|----------|-------|--------|--------|
| Total tools | X | 76 | +Y |
| Content tools | X | Y | +Z |
| Context tools | X | Y | +Z |
| Query tools | X | Y | +Z |
| Sprint tools | X | Y | +Z |
| Task tools | X | Y | +Z |
| Token tools | X | 0 | +X |
| Submodule tools | X | 0 | +X |

### New Tools Since Dec 12
1. [tool_name] - Description
2. [tool_name] - Description

### Tool Documentation Status
| File | Tools | Documented | Coverage |
|------|-------|------------|----------|
| content_tools.py | X | Y | Z% |
| context_tools.py | X | Y | Z% |
| ... | | | |

## Resource Inventory

| Resource | Purpose | Status |
|----------|---------|--------|
| [resource_1] | [purpose] | Active |
| ... | | |

## Prompt Inventory

| Prompt | Purpose | Quality |
|--------|---------|---------|
| [prompt_1] | [purpose] | Good/Needs Work |
| ... | | |

## Quality Metrics

### Code Quality
| Metric | Value |
|--------|-------|
| Total files | 41 |
| Total LoC | X |
| Docstring coverage | X% |
| Type hint coverage | X% |

### Test Coverage
| Component | Coverage |
|-----------|----------|
| tools/ | X% |
| server.py | X% |
| Overall | X% |

## Issues Found

### Critical
- [None or list]

### High Priority
1. [Issue]

### Medium Priority
1. [Issue]

## Recommendations

1. [Recommendation]
```

### Adapters Audit Output

```markdown
# Adapters Module Quality Audit
**Date:** December 28, 2024
**Baseline:** December 12, 2024

## Executive Summary

The adapters module provides 14 platform adapters for deploying Vibey
configurations to various AI coding assistants...

## Adapter Inventory

### Active Adapters (14)
| Adapter | Type | Files | Status |
|---------|------|-------|--------|
| Claude Code | File | 1 | Active |
| Cursor | Directory | 3 | Active |
| Copilot | Directory | 3 | Active |
| VS Code | Directory | 3 | Active |
| Goose | File | 1 | Active |
| Gemini | Directory | 10 | Active |
| Aider | File | 1 | Active |
| Continue | Directory | 5 | Active |
| Windsurf | Directory | 3 | Active |
| Amazon Q | Directory | 3 | Active |
| Cody | Directory | 3 | Active |
| JetBrains | Directory | 3 | Active |
| Replit | Directory | 3 | Active |
| PM | Directory | 5 | New |

### New Since Dec 12
- pm/ adapter (project management)

## Compliance Matrix

| Adapter | Inherits Base | Deploy | Config | Format | Score |
|---------|---------------|--------|--------|--------|-------|
| claude_code | Yes | Yes | Yes | Yes | 100% |
| cursor | Yes | Yes | Yes | Yes | 100% |
| ... | | | | | |

## Quality Metrics

### Code Quality
| Metric | Value |
|--------|-------|
| Total files | 44 |
| Total LoC | X |
| Docstring coverage | X% |
| Type hint coverage | X% |

### Consistency Score
| Aspect | Score |
|--------|-------|
| Method signatures | X% |
| Error handling | X% |
| Configuration format | X% |
| Overall | X% |

## Issues Found

1. [Issue]

## Recommendations

1. [Recommendation]
```

## Acceptance Criteria

- [ ] All 41 MCP Python files audited
- [ ] All 76+ tools inventoried
- [ ] All 8 resources inventoried
- [ ] All 4 prompts inventoried
- [ ] All 44 adapter Python files audited
- [ ] All 14 adapters verified
- [ ] Compliance matrix complete
- [ ] Dec 12 comparison documented
- [ ] MODULE_QUALITY_AUDIT_MCP.md updated
- [ ] MODULE_QUALITY_AUDIT_ADAPTERS.md updated

## Estimated Time

- MCP tool inventory: 25 minutes
- MCP resource/prompt inventory: 15 minutes
- MCP quality analysis: 15 minutes
- Adapter inventory: 20 minutes
- Adapter compliance check: 20 minutes
- Documentation: 25 minutes
- **Total: ~2 hours**
