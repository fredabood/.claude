# Cross-Module Dependency Analysis

**Audit Version:** comprehensive-audit-v2
**Generated:** 2025-12-28

## Executive Summary

This analysis examines how the 7 primary modules in the vibey package depend on each other. High coupling between modules can indicate architectural issues and maintenance challenges.

## Module Inventory

| Module | Files | Lines | Primary Purpose |
|--------|-------|-------|-----------------|
| CLI | 123 | 52,159 | Command-line interface |
| Operations | 115 | 52,236 | Business logic |
| Roadmap | 100 | 55,298 | Data layer |
| Services | 46 | 28,649 | Implementation mode |
| Adapters | 44 | 10,184 | Platform integrations |
| MCP | 41 | 11,613 | Model Context Protocol |
| Common | 3 | 1,047 | Shared utilities |

**Total:** 472 files, 211,186 lines

## Cross-Module Dependency Matrix

| Source → | cli | ops | roadmap | mcp | adapters | common | services |
|----------|-----|-----|---------|-----|----------|--------|----------|
| **cli** | - | 214 | 93 | 2 | 6 | 5 | 13 |
| **operations** | 26 | - | 66 | 1 | 2 | 0 | 2 |
| **roadmap** | 1 | 0 | - | 0 | 0 | 0 | 0 |
| **mcp** | 0 | 22 | 4 | - | 0 | 0 | 2 |
| **adapters** | 0 | 0 | 0 | 27 | - | 0 | 0 |
| **common** | 0 | 0 | 0 | 0 | 0 | - | 0 |
| **services** | 0 | 3 | 48 | 0 | 2 | 0 | - |

**Total cross-module edges:** 539

## Module Coupling Metrics

| Module | Incoming | Outgoing | Total Coupling | Classification |
|--------|----------|----------|----------------|----------------|
| CLI | 27 | 333 | 360 | **Very High** (Controller) |
| Operations | 239 | 97 | 336 | **Very High** (Service) |
| Roadmap | 211 | 1 | 212 | **High** (Data Layer) |
| Services | 17 | 53 | 70 | Medium |
| MCP | 30 | 28 | 58 | Medium |
| Adapters | 10 | 27 | 37 | Low |
| Common | 5 | 0 | 5 | **Ideal** (Utility) |

## Dependency Flow

```
┌─────────────────────────────────────────────────────────┐
│                         CLI                              │
│  (Entry Point - 333 outgoing dependencies)              │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Ops     │ │ Services│ │ MCP     │
   │ (336)   │ │ (70)    │ │ (58)    │
   └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │
        └─────┬─────┴───────────┘
              ▼
        ┌───────────┐
        │ Roadmap   │
        │ (Data)    │
        └───────────┘
              ▲
              │
        ┌───────────┐     ┌───────────┐
        │ Adapters  │────▶│ MCP       │
        └───────────┘     └───────────┘
```

## Key Findings

### Healthy Patterns

1. **Common module** - Zero outgoing dependencies (utility layer)
2. **Roadmap module** - Only 1 outgoing dependency (data layer)
3. **Adapters** - Isolated, only depends on MCP
4. **Clear layering** - CLI → Ops → Roadmap

### Concerning Patterns

1. **CLI is too coupled** - 333 outgoing dependencies
   - Directly imports from operations (214 times)
   - Should go through service layer

2. **Operations ↔ CLI cycle** - Ops imports CLI 26 times
   - Creates circular dependency risk
   - CLI should not be imported by business logic

3. **Roadmap imports CLI** - 1 import detected
   - Data layer should never import presentation layer

## Recommendations

### High Priority

1. **Break CLI → Operations tight coupling**
   - Introduce facade pattern
   - CLI should call high-level operations, not individual functions

2. **Remove Ops → CLI imports (26)**
   - Move shared utilities to common/
   - Use dependency injection

3. **Remove Roadmap → CLI import (1)**
   - Identify and refactor

### Medium Priority

1. **Create service layer abstraction**
   - Services module is growing
   - Could mediate CLI → Operations

2. **Standardize MCP dependencies**
   - MCP imports from 4 modules
   - Consider unified interface

## Coupling Score Card

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Max outgoing (CLI) | 333 | <100 | Needs work |
| Circular deps | 2 | 0 | Needs work |
| Data layer coupling | 1 | 0 | Almost good |
| Utility isolation | 0 | 0 | Perfect |

**Overall Architecture Health: B-**

## Module Coupling Table (Detailed)

```
Module          Afferent  Efferent  Instability  Abstractness
                (Ca)      (Ce)      I=Ce/(Ca+Ce) A
────────────────────────────────────────────────────────────
cli             27        333       0.93         Low
operations      239       97        0.29         Medium
roadmap         211       1         0.00         High (stable)
services        17        53        0.76         Medium
mcp             30        28        0.48         Medium
adapters        10        27        0.73         Low
common          5         0         0.00         High (stable)
```

**Legend:**
- Afferent (Ca): Incoming dependencies
- Efferent (Ce): Outgoing dependencies
- Instability: Higher = more likely to change
- Abstractness: Ratio of abstract to concrete

---

*Analysis completed: 2025-12-28*
*Recommendations should be addressed in Architecture Modernization track*
