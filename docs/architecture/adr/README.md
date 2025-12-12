# Architectural Decision Records

This directory contains Architectural Decision Records (ADRs) documenting key technical decisions in the Vibey project.

## What is an ADR?

An Architectural Decision Record captures a significant architectural decision along with its context and consequences. ADRs help:

- Document why decisions were made
- Onboard new contributors
- Avoid revisiting settled decisions
- Understand trade-offs

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [0001](./0001-ulid-identifiers.md) | Use ULIDs for Entity Identifiers | Accepted | 2025-12 |
| [0002](./0002-flat-directory-structure.md) | Flat Directory Structure for Roadmap | Accepted | 2025-12 |
| [0003](./0003-dual-storage-sqlite-yaml.md) | SQLite + YAML Dual Storage | Accepted | 2025-12 |
| [0004](./0004-click-cli-framework.md) | Click for CLI Implementation | Accepted | 2025-12 |
| [0005](./0005-mcp-integration.md) | MCP Protocol for AI Integration | Accepted | 2025-12 |

## ADR Template

New ADRs should follow the template in [0000-template.md](./0000-template.md).

## Status Definitions

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion |
| **Accepted** | Decision made and in effect |
| **Deprecated** | No longer applies |
| **Superseded** | Replaced by another ADR |

## Creating a New ADR

1. Copy `0000-template.md` to a new file with next ID
2. Fill in all sections
3. Update this README index
4. Submit PR for review
