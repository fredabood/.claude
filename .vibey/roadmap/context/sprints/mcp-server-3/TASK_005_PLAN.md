# Task 005: Implement MCP Prompts for Quality Gates

**Task ID:** 01KC79XW0348EJZBAJ6YPW09FJ
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** High
**Type:** Development

## Problem Statement

Quality gates are a core concept in the Vibey framework - they ensure code meets standards before moving forward. Currently, quality gate checks are embedded in workflow definitions. This task implements MCP Prompts that provide structured guidance for running quality gate checks, making them accessible through the MCP protocol.

## Current State

### Quality Gates in Workflows
Quality gates are defined in workflow YAML frontmatter:
```yaml
quality_gates:
  - name: Security Audit
    type: security
    threshold: 100
    blocking: true
  - name: Test Coverage
    type: testing
    threshold: 80
    blocking: true
  - name: Documentation Coverage
    type: documentation
    threshold: 70
    blocking: false
```

### Quality Gate Types
| Type | Purpose | Typical Checks |
|------|---------|----------------|
| security | Security vulnerabilities | OWASP, secrets, injection |
| testing | Test coverage | Unit, integration, e2e |
| logging | Observability | Structured logging, metrics |
| documentation | Code documentation | Docstrings, README, API docs |
| performance | Performance | Load tests, profiling |

## Implementation Plan

### Phase 1: QualityGatePromptProvider

**1.1 Create Provider Implementation**
```python
# vibey/mcp/prompts/quality_gates.py
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .provider import PromptProvider, PromptDefinition, PromptArgument, PromptResult, PromptMessage

@dataclass
class QualityGateDefinition:
    """Quality gate definition from workflow."""
    name: str
    type: str
    threshold: int
    blocking: bool
    description: Optional[str] = None
    checks: List[str] = None

class QualityGatePromptProvider(PromptProvider):
    """Provides MCP Prompts for quality gate checks."""

    GATE_TYPES = ["security", "testing", "logging", "documentation", "performance"]

    def __init__(self, content_root: Path):
        self.content_root = content_root
        self._gate_templates = self._load_gate_templates()

    def get_prompts(self) -> List[PromptDefinition]:
        """Return all quality gate prompts."""
        prompts = [
            # Main quality gate check prompt
            PromptDefinition(
                name="vibey_quality_gate_check",
                description="Run a comprehensive quality gate check on code or documentation",
                arguments=[
                    PromptArgument(
                        name="gate_type",
                        description="Type of gate: security, testing, logging, documentation, performance",
                        required=True
                    ),
                    PromptArgument(
                        name="threshold",
                        description="Pass threshold percentage (default: 80)"
                    ),
                    PromptArgument(
                        name="file_path",
                        description="Specific file or directory to check"
                    ),
                    PromptArgument(
                        name="severity",
                        description="Minimum severity to report: critical, high, medium, low"
                    )
                ]
            ),
            # Quick security scan prompt
            PromptDefinition(
                name="vibey_security_scan",
                description="Quick security vulnerability scan",
                arguments=[
                    PromptArgument(
                        name="target",
                        description="File, directory, or 'all' to scan",
                        required=True
                    ),
                    PromptArgument(
                        name="focus",
                        description="Focus area: injection, auth, secrets, dependencies"
                    )
                ]
            ),
            # Test coverage prompt
            PromptDefinition(
                name="vibey_test_coverage",
                description="Analyze test coverage and suggest improvements",
                arguments=[
                    PromptArgument(
                        name="target",
                        description="Module or file to analyze",
                        required=True
                    ),
                    PromptArgument(
                        name="coverage_type",
                        description="Coverage type: line, branch, function"
                    )
                ]
            ),
            # Documentation check prompt
            PromptDefinition(
                name="vibey_doc_check",
                description="Check documentation completeness",
                arguments=[
                    PromptArgument(
                        name="target",
                        description="File or module to check",
                        required=True
                    ),
                    PromptArgument(
                        name="doc_type",
                        description="Documentation type: docstrings, readme, api, all"
                    )
                ]
            ),
        ]
        return prompts

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None
    ) -> PromptResult:
        """Generate prompt messages for quality gate check."""
        arguments = arguments or {}

        if name == "vibey_quality_gate_check":
            return await self._build_quality_gate_prompt(arguments)
        elif name == "vibey_security_scan":
            return await self._build_security_prompt(arguments)
        elif name == "vibey_test_coverage":
            return await self._build_coverage_prompt(arguments)
        elif name == "vibey_doc_check":
            return await self._build_doc_prompt(arguments)
        else:
            raise ValueError(f"Unknown prompt: {name}")

    async def _build_quality_gate_prompt(self, args: Dict[str, str]) -> PromptResult:
        """Build comprehensive quality gate check prompt."""
        gate_type = args.get("gate_type", "all")
        threshold = int(args.get("threshold", "80"))
        file_path = args.get("file_path", "current context")
        severity = args.get("severity", "medium")

        # Build checklist based on gate type
        checklist = self._get_checklist(gate_type)

        user_message = f"""Please perform a {gate_type} quality gate check on: {file_path}

## Quality Gate Parameters
- **Gate Type:** {gate_type}
- **Pass Threshold:** {threshold}%
- **Minimum Severity:** {severity}
- **Target:** {file_path}

## Checklist
{checklist}

## Instructions
1. Review the target code/content against each checklist item
2. Rate each item as: ✅ Pass, ⚠️ Warning, ❌ Fail
3. Calculate overall pass percentage
4. Determine if gate passes (>= {threshold}%)
5. Provide specific recommendations for any failures

## Output Format
Provide a structured report with:
- Overall Score: X/Y items passed (Z%)
- Gate Status: PASS/FAIL
- Detailed findings for each category
- Priority recommendations"""

        assistant_message = f"""I'll perform a comprehensive {gate_type} quality gate check. Let me analyze the code systematically against each checklist item.

## Quality Gate: {gate_type.title()}
**Threshold:** {threshold}%
**Target:** {file_path}

I'll check each item and provide a detailed report with findings and recommendations."""

        return PromptResult(
            description=f"{gate_type.title()} quality gate check with {threshold}% threshold",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content=assistant_message)
            ]
        )

    async def _build_security_prompt(self, args: Dict[str, str]) -> PromptResult:
        """Build security scan prompt."""
        target = args.get("target", "current file")
        focus = args.get("focus", "all")

        user_message = f"""Perform a security vulnerability scan on: {target}

## Focus Area: {focus if focus != "all" else "Comprehensive scan"}

## Security Checklist
### Injection Vulnerabilities
- [ ] SQL injection risks
- [ ] Command injection risks
- [ ] XSS vulnerabilities
- [ ] Path traversal risks

### Authentication & Authorization
- [ ] Hardcoded credentials
- [ ] Weak authentication patterns
- [ ] Missing authorization checks
- [ ] Session management issues

### Secrets & Sensitive Data
- [ ] API keys in code
- [ ] Passwords in configuration
- [ ] Sensitive data exposure
- [ ] Improper error messages

### Dependencies
- [ ] Known vulnerable packages
- [ ] Outdated dependencies
- [ ] Unnecessary permissions

## Instructions
1. Scan for each vulnerability type
2. Rate severity: Critical, High, Medium, Low
3. Provide specific line numbers and code snippets
4. Suggest remediation steps"""

        return PromptResult(
            description=f"Security scan focusing on {focus}",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content="I'll perform a thorough security analysis. Let me scan for vulnerabilities systematically...")
            ]
        )

    async def _build_coverage_prompt(self, args: Dict[str, str]) -> PromptResult:
        """Build test coverage analysis prompt."""
        target = args.get("target", "current module")
        coverage_type = args.get("coverage_type", "all")

        user_message = f"""Analyze test coverage for: {target}

## Coverage Analysis Type: {coverage_type}

## Analysis Steps
1. Identify all functions/methods in the target
2. Check which have corresponding tests
3. Identify edge cases not covered
4. Suggest additional test cases

## Output Format
- **Coverage Summary:** X/Y functions tested
- **Uncovered Functions:** List with reasons
- **Missing Edge Cases:** Prioritized list
- **Suggested Test Cases:** With code examples"""

        return PromptResult(
            description=f"Test coverage analysis for {target}",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content="I'll analyze the test coverage comprehensively...")
            ]
        )

    async def _build_doc_prompt(self, args: Dict[str, str]) -> PromptResult:
        """Build documentation check prompt."""
        target = args.get("target", "current file")
        doc_type = args.get("doc_type", "all")

        user_message = f"""Check documentation completeness for: {target}

## Documentation Type: {doc_type}

## Checklist
### Docstrings
- [ ] Module docstring present
- [ ] All public functions documented
- [ ] Parameters documented with types
- [ ] Return values documented
- [ ] Examples provided for complex functions

### README
- [ ] Project description
- [ ] Installation instructions
- [ ] Usage examples
- [ ] API documentation links

### API Documentation
- [ ] Endpoint descriptions
- [ ] Request/response schemas
- [ ] Error codes documented
- [ ] Authentication requirements

## Output Format
- **Coverage Score:** X%
- **Missing Documentation:** Itemized list
- **Quality Issues:** Style, clarity, completeness
- **Priority Fixes:** Most impactful improvements"""

        return PromptResult(
            description=f"Documentation check for {target}",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content="I'll review the documentation systematically...")
            ]
        )

    def _get_checklist(self, gate_type: str) -> str:
        """Get checklist for specific gate type."""
        checklists = {
            "security": """
### Security Checklist
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] Output encoding for XSS prevention
- [ ] Parameterized queries (no SQL injection)
- [ ] Secure authentication implementation
- [ ] Proper authorization checks
- [ ] Secure session management
- [ ] No sensitive data in logs
- [ ] Dependencies up to date
- [ ] HTTPS/TLS properly configured""",

            "testing": """
### Testing Checklist
- [ ] Unit tests for all public functions
- [ ] Integration tests for APIs
- [ ] Edge cases covered
- [ ] Error conditions tested
- [ ] Mocking used appropriately
- [ ] Test data representative
- [ ] Tests are deterministic
- [ ] Coverage meets threshold
- [ ] Tests run in isolation
- [ ] CI pipeline includes tests""",

            "logging": """
### Logging Checklist
- [ ] Structured logging format (JSON)
- [ ] Appropriate log levels used
- [ ] Request correlation IDs
- [ ] Error stack traces captured
- [ ] No sensitive data logged
- [ ] Performance metrics tracked
- [ ] Health check endpoints
- [ ] Alerting configured
- [ ] Log rotation configured
- [ ] Centralized log aggregation""",

            "documentation": """
### Documentation Checklist
- [ ] README.md complete
- [ ] API documentation current
- [ ] Code comments for complex logic
- [ ] Docstrings on public functions
- [ ] Architecture diagrams updated
- [ ] Setup instructions work
- [ ] Examples are runnable
- [ ] Changelog maintained
- [ ] Contributing guidelines
- [ ] License file present""",

            "performance": """
### Performance Checklist
- [ ] Database queries optimized
- [ ] N+1 query problems resolved
- [ ] Caching implemented where needed
- [ ] Pagination for large datasets
- [ ] Async operations used correctly
- [ ] Connection pooling configured
- [ ] Memory leaks addressed
- [ ] CPU-intensive operations optimized
- [ ] Load testing performed
- [ ] Performance budgets defined"""
        }

        if gate_type == "all":
            return "\n".join(checklists.values())
        return checklists.get(gate_type, checklists["security"])

    def _load_gate_templates(self) -> Dict[str, str]:
        """Load quality gate templates from content."""
        # Could load from files if needed
        return {}
```

### Phase 2: Integration with PromptManager

**2.1 Register Provider**
```python
# In vibey/mcp/prompts/manager.py
from .quality_gates import QualityGatePromptProvider

class PromptManager:
    def _register_providers(self):
        self.providers['quality-gates'] = QualityGatePromptProvider(self.content_root)
        # ... other providers
```

### Phase 3: Server Integration

**3.1 Update Server**
```python
# In VibeyMCPServer.__init__:
self.prompt_manager = PromptManager(self.content_root, self.roadmap_root)

# Add handlers:
def list_prompts(self) -> List[Dict]:
    return self.prompt_manager.list_prompts()

async def get_prompt(self, name: str, arguments: Optional[Dict[str, str]] = None) -> Dict:
    return await self.prompt_manager.get_prompt(name, arguments)
```

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/mcp/prompts/quality_gates.py` | QualityGatePromptProvider implementation |

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/mcp/prompts/manager.py` | Register QualityGatePromptProvider |
| `vibey/mcp/prompts/__init__.py` | Export QualityGatePromptProvider |
| `vibey/mcp/server.py` | Add prompt manager and handlers |

## Testing Strategy

### Unit Tests
```python
# tests/mcp/prompts/test_quality_gates.py
class TestQualityGatePromptProvider:
    def test_get_prompts(self, provider):
        prompts = provider.get_prompts()
        assert len(prompts) >= 4
        names = [p.name for p in prompts]
        assert "vibey_quality_gate_check" in names
        assert "vibey_security_scan" in names

    @pytest.mark.asyncio
    async def test_quality_gate_prompt(self, provider):
        result = await provider.get_prompt(
            "vibey_quality_gate_check",
            {"gate_type": "security", "threshold": "90"}
        )
        assert result.messages
        assert any("security" in m.content.lower() for m in result.messages)

    @pytest.mark.asyncio
    async def test_security_scan_prompt(self, provider):
        result = await provider.get_prompt(
            "vibey_security_scan",
            {"target": "src/auth.py", "focus": "injection"}
        )
        assert result.messages
        assert any("injection" in m.content.lower() for m in result.messages)
```

## Success Criteria

1. [ ] QualityGatePromptProvider implements 4+ prompt types
2. [ ] Checklists comprehensive for each gate type
3. [ ] Prompts generate actionable guidance
4. [ ] Arguments properly validated
5. [ ] Integration with server complete
6. [ ] Unit tests passing

## Dependencies

- Task 004 (Prompts architecture) must be complete

## Deliverables

1. QualityGatePromptProvider implementation
2. Quality gate checklists
3. 4 prompt definitions with arguments
4. Unit test suite
5. Server integration
