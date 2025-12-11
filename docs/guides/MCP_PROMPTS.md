# MCP Prompts User Guide

This guide explains how to use Vibey's MCP Prompts feature to access pre-configured prompts for quality gates, security scanning, and documentation checks.

## Overview

Vibey provides MCP Prompts that guide AI assistants through structured quality assurance tasks:

- **Quality Gate Checks** - Comprehensive audits for security, testing, logging, documentation, and performance
- **Security Scans** - Targeted security analysis with focus areas
- **Test Coverage Analysis** - Coverage assessment and gap identification
- **Documentation Checks** - Documentation quality and completeness audits

Prompts return structured multi-message conversations with expert system prompts and detailed checklists.

## Available Prompts

| Prompt Name | Description | Required Arguments |
|-------------|-------------|-------------------|
| `vibey_quality_gate_check` | Run a quality gate audit | `gate_type` |
| `vibey_security_scan` | Perform security analysis | `target` |
| `vibey_test_coverage` | Analyze test coverage | `target` |
| `vibey_doc_check` | Check documentation quality | `target` |

## Usage Examples

### Quality Gate Check

Run a comprehensive quality gate audit:

```json
{
  "jsonrpc": "2.0",
  "method": "prompts/get",
  "params": {
    "name": "vibey_quality_gate_check",
    "arguments": {
      "gate_type": "security",
      "threshold": "90"
    }
  },
  "id": 1
}
```

**Arguments:**
- `gate_type` (required): Type of quality gate - `security`, `testing`, `logging`, `documentation`, `performance`, or `all`
- `threshold` (optional): Pass threshold percentage (default: 80)

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "messages": [
      {
        "role": "user",
        "content": "Please perform a security quality gate check...\n\n## Security Checklist\n- [ ] Input validation...\n- [ ] Authentication checks...\n\nThreshold: 90%"
      },
      {
        "role": "assistant",
        "content": "I'll perform a comprehensive security quality gate check..."
      }
    ]
  },
  "id": 1
}
```

### Security Scan

Perform targeted security analysis:

```json
{
  "jsonrpc": "2.0",
  "method": "prompts/get",
  "params": {
    "name": "vibey_security_scan",
    "arguments": {
      "target": "src/auth/login.py",
      "focus": "injection"
    }
  },
  "id": 2
}
```

**Arguments:**
- `target` (required): File, directory, or module to scan
- `focus` (optional): Focus area - `injection`, `authentication`, `authorization`, `cryptography`, `secrets`, or `all`

### Test Coverage Analysis

Analyze test coverage:

```json
{
  "jsonrpc": "2.0",
  "method": "prompts/get",
  "params": {
    "name": "vibey_test_coverage",
    "arguments": {
      "target": "vibey.mcp",
      "coverage_type": "line"
    }
  },
  "id": 3
}
```

**Arguments:**
- `target` (required): Module or path to analyze
- `coverage_type` (optional): Type of coverage - `line`, `branch`, `function`, or `all`

### Documentation Check

Check documentation quality:

```json
{
  "jsonrpc": "2.0",
  "method": "prompts/get",
  "params": {
    "name": "vibey_doc_check",
    "arguments": {
      "target": "vibey/mcp/server.py",
      "doc_type": "docstrings"
    }
  },
  "id": 4
}
```

**Arguments:**
- `target` (required): File or module to check
- `doc_type` (optional): Documentation type - `docstrings`, `readme`, `api`, `comments`, or `all`

## Quality Gate Types

### Security Gate

Checks for:
- [ ] Input validation and sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Authentication mechanisms
- [ ] Authorization checks
- [ ] Secure password handling
- [ ] Secrets management
- [ ] Cryptographic best practices
- [ ] Dependency vulnerabilities

### Testing Gate

Checks for:
- [ ] Unit test coverage
- [ ] Integration test coverage
- [ ] Edge case handling
- [ ] Error path testing
- [ ] Mock usage appropriateness
- [ ] Test isolation
- [ ] Assertion quality
- [ ] Test naming conventions

### Logging Gate

Checks for:
- [ ] Appropriate log levels
- [ ] Structured logging
- [ ] Sensitive data exclusion
- [ ] Error context preservation
- [ ] Performance impact
- [ ] Log rotation considerations
- [ ] Audit trail compliance

### Documentation Gate

Checks for:
- [ ] Module docstrings
- [ ] Function/method docstrings
- [ ] Parameter documentation
- [ ] Return value documentation
- [ ] Exception documentation
- [ ] Usage examples
- [ ] README completeness
- [ ] API documentation

### Performance Gate

Checks for:
- [ ] Algorithm efficiency
- [ ] Database query optimization
- [ ] Memory usage
- [ ] Resource cleanup
- [ ] Caching appropriateness
- [ ] Async/await usage
- [ ] Connection pooling
- [ ] Batch processing opportunities

## Listing Prompts

Get all available prompts:

```json
{
  "jsonrpc": "2.0",
  "method": "prompts/list",
  "id": 5
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "prompts": [
      {
        "name": "vibey_quality_gate_check",
        "description": "Run a quality gate audit for security, testing, logging, documentation, or performance",
        "arguments": [
          {
            "name": "gate_type",
            "description": "Type of quality gate",
            "required": true
          },
          {
            "name": "threshold",
            "description": "Pass threshold percentage",
            "required": false
          }
        ]
      },
      {
        "name": "vibey_security_scan",
        "description": "Perform targeted security analysis",
        "arguments": [
          {
            "name": "target",
            "description": "File or module to scan",
            "required": true
          },
          {
            "name": "focus",
            "description": "Security focus area",
            "required": false
          }
        ]
      }
    ]
  },
  "id": 5
}
```

## Integration with AI Assistants

### Claude Code Integration

When using with Claude Code, prompts can be accessed through MCP:

```
// List available prompts
MCP: prompts/list

// Run security quality gate
MCP: prompts/get {"name": "vibey_quality_gate_check", "arguments": {"gate_type": "security"}}

// Security scan on specific file
MCP: prompts/get {"name": "vibey_security_scan", "arguments": {"target": "src/api/endpoints.py", "focus": "injection"}}
```

### Workflow Integration

Prompts can be used at quality gate checkpoints in workflows:

1. **Before Code Review**
   - Run `vibey_security_scan` on changed files
   - Run `vibey_test_coverage` to verify coverage

2. **Before Merge**
   - Run `vibey_quality_gate_check` with `gate_type: all`

3. **Documentation Updates**
   - Run `vibey_doc_check` on new/modified modules

## Response Structure

All prompts return a conversation with:

1. **User Message**: Detailed instructions with checklist
2. **Assistant Message**: Acknowledgment and approach explanation

This structure allows AI assistants to:
- Understand the task requirements
- Follow structured checklists
- Provide consistent, thorough responses

## Server Capabilities

The Vibey MCP server announces these prompt capabilities:

```json
{
  "prompts": {
    "listChanged": true
  }
}
```

- **listChanged**: Server will notify when prompt list changes

## Error Handling

### Prompt Not Found

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Prompt not found: unknown_prompt"
  },
  "id": 1
}
```

### Missing Required Argument

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Missing required argument: gate_type"
  },
  "id": 1
}
```

## Best Practices

1. **Start with specific gates**: Run individual gate types before `all`
2. **Set appropriate thresholds**: Adjust based on project maturity
3. **Target specific files**: More focused scans are more actionable
4. **Integrate into workflows**: Use prompts at defined quality checkpoints
5. **Track results over time**: Monitor quality improvements

## Extending Prompts

The prompt system is extensible. New prompt providers can be added for:

- Custom quality gates
- Project-specific checks
- Domain-specific audits
- Integration checks

See the developer documentation for details on creating custom prompt providers.
