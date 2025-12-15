# Reference Guide Friction Analysis

## Overview

Analysis of CLI_REFERENCE.md and MCP_REFERENCE.md for friction points affecting user experience.

**Analyzed**: 2025-12-16
**CLI Reference**: 200 commands documented
**MCP Reference**: 76 tools, 8 resources, 4 prompts documented

---

## CLI Reference Friction Points

### High Impact Issues

#### 1. Command Index Organization
**Location**: Lines 99-200+
**Issue**: The Command Index section uses an awkward alphabetical organization that restarts the alphabet for each command group. Users see "A" multiple times as they scroll.
**Impact**: 4/5 - Confuses users trying to find commands
**Complexity**: 2/5 - Auto-generation needs template update
**Recommendation**: Use continuous alphabetical order or organize by command group

#### 2. Truncated Descriptions
**Location**: Throughout document
**Issue**: Many descriptions end with "..." indicating truncation
**Example**: `vibey artifact - Manage artifacts - first-class file-based entitie...`
**Impact**: 3/5 - Users don't get full context
**Complexity**: 1/5 - Increase description length limit in generator
**Recommendation**: Increase max description length or show full description in detail section

#### 3. Missing Cross-References
**Location**: Individual command documentation
**Issue**: Related commands don't reference each other
**Example**: `roadmap start` doesn't mention `roadmap complete` or `roadmap show`
**Impact**: 3/5 - Users miss related functionality
**Complexity**: 3/5 - Requires analyzing command relationships
**Recommendation**: Add "Related Commands" or "See Also" sections

### Medium Impact Issues

#### 4. No Quick Start Section
**Location**: Missing
**Issue**: Users must scroll through entire doc to find common operations
**Impact**: 3/5 - Slows down new users
**Complexity**: 2/5 - Create curated quick start section
**Recommendation**: Add "Common Workflows" or "Quick Start" section at top

#### 5. Missing Option Defaults
**Location**: Command options
**Issue**: Many options don't show their default values
**Impact**: 2/5 - Users unsure of default behavior
**Complexity**: 2/5 - Extract from Click decorators
**Recommendation**: Show default values for all options

#### 6. Inconsistent Example Formats
**Location**: Throughout
**Issue**: Some commands have rich examples, others have minimal or none
**Impact**: 2/5 - Uneven documentation quality
**Complexity**: 3/5 - Need to add examples to all commands
**Recommendation**: Ensure every command has at least one example

### Low Impact Issues

#### 7. No Error Reference
**Location**: Missing
**Issue**: Common errors and their solutions not documented
**Impact**: 2/5 - Users must figure out errors themselves
**Complexity**: 4/5 - Requires cataloging all error codes
**Recommendation**: Add common errors section per command group

#### 8. Version History Missing
**Location**: Missing
**Issue**: Users can't see what changed between versions
**Impact**: 1/5 - Mostly affects upgrading users
**Complexity**: 4/5 - Need change tracking system
**Recommendation**: Add changelog or version notes

---

## MCP Reference Friction Points

### High Impact Issues

#### 1. No When-to-Use Guidance
**Location**: Missing
**Issue**: Users don't know when to use MCP tools vs CLI commands
**Example**: Both have `start_task` - which should be used when?
**Impact**: 4/5 - Confuses AI assistant configuration
**Complexity**: 2/5 - Add usage context section
**Recommendation**: Add "When to Use" section explaining MCP vs CLI

#### 2. Missing Error Responses
**Location**: Tool documentation
**Issue**: No documentation of error responses or codes
**Impact**: 3/5 - AI assistants can't handle errors gracefully
**Complexity**: 3/5 - Document all error scenarios
**Recommendation**: Add "Error Responses" section per tool

### Medium Impact Issues

#### 3. No Workflow Examples
**Location**: Missing
**Issue**: Tools documented individually but not as workflows
**Example**: How to start task → make changes → complete task
**Impact**: 3/5 - Users must figure out tool chains
**Complexity**: 2/5 - Create workflow documentation
**Recommendation**: Add "Common Workflows" showing tool sequences

#### 4. Schema Without Explanation
**Location**: Parameter tables
**Issue**: Complex schemas (arrays, objects) lack explanation
**Impact**: 2/5 - Users struggle with complex inputs
**Complexity**: 2/5 - Add schema explanations
**Recommendation**: Add inline schema documentation for complex types

### Low Impact Issues

#### 5. No Rate Limiting Info
**Location**: Missing
**Issue**: No guidance on rate limits or batching
**Impact**: 2/5 - Could affect heavy automation
**Complexity**: 2/5 - Document limits if any exist
**Recommendation**: Add rate limiting section if applicable

---

## Summary Statistics

| Category | High | Medium | Low | Total |
|----------|------|--------|-----|-------|
| CLI Reference | 3 | 3 | 2 | 8 |
| MCP Reference | 2 | 2 | 1 | 5 |
| **Total** | **5** | **5** | **3** | **13** |

## Priority Matrix

| Issue | Impact | Complexity | Priority Score |
|-------|--------|------------|----------------|
| Command Index Organization | 4 | 2 | 8.0 |
| No When-to-Use Guidance | 4 | 2 | 8.0 |
| Missing Cross-References | 3 | 3 | 3.0 |
| No Quick Start Section | 3 | 2 | 4.5 |
| Truncated Descriptions | 3 | 1 | 9.0 |
| Missing Error Responses | 3 | 3 | 3.0 |
| No Workflow Examples | 3 | 2 | 4.5 |

*Priority Score = Impact * 3 / Complexity*

## Recommended Actions

### Immediate (Quick Wins)
1. Fix truncated descriptions (High impact, low complexity)
2. Fix command index organization (High impact, low complexity)
3. Add MCP when-to-use guidance (High impact, low complexity)

### Short-term
4. Add CLI quick start section
5. Add MCP workflow examples
6. Add cross-references between related commands

### Medium-term
7. Add error documentation for both guides
8. Ensure all commands have examples
9. Add schema explanations for complex MCP parameters
