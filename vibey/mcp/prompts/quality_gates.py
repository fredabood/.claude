"""
MCP Prompt Provider for Quality Gates.

Provides structured prompts for running quality gate checks
including security, testing, logging, documentation, and performance.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .provider import PromptProvider
from .types import (
    PromptArgument,
    PromptDefinition,
    PromptMessage,
    PromptResult,
    PROMPT_CATEGORY_QUALITY_GATES,
    PROMPT_PREFIX,
)
from .exceptions import PromptNotFoundError

logger = logging.getLogger(__name__)


class QualityGatePromptProvider(PromptProvider):
    """
    Provides MCP Prompts for quality gate checks.

    Implements prompts for:
    - Comprehensive quality gate checks
    - Security vulnerability scans
    - Test coverage analysis
    - Documentation completeness checks

    Example:
        >>> provider = QualityGatePromptProvider(Path("/path/to/vibey"))
        >>> prompts = provider.get_prompts()
        >>> result = await provider.get_prompt(
        ...     "vibey_quality_gate_check",
        ...     {"gate_type": "security", "threshold": "90"}
        ... )
    """

    CATEGORY = PROMPT_CATEGORY_QUALITY_GATES

    # Supported gate types
    GATE_TYPES = ["security", "testing", "logging", "documentation", "performance"]

    def __init__(self, content_root: Path):
        """
        Initialize quality gate prompt provider.

        Args:
            content_root: Root directory for content access
        """
        super().__init__(content_root)

    def get_prompts(self) -> List[PromptDefinition]:
        """
        Return all quality gate prompts.

        Returns:
            List of PromptDefinition objects for quality gates
        """
        return [
            # Main quality gate check prompt
            PromptDefinition(
                name=f"{PROMPT_PREFIX}quality_gate_check",
                description="Run a comprehensive quality gate check on code or documentation",
                arguments=[
                    PromptArgument(
                        name="gate_type",
                        description="Type of gate: security, testing, logging, documentation, performance, or all",
                        required=True,
                    ),
                    PromptArgument(
                        name="threshold",
                        description="Pass threshold percentage (default: 80)",
                        required=False,
                    ),
                    PromptArgument(
                        name="file_path",
                        description="Specific file or directory to check",
                        required=False,
                    ),
                    PromptArgument(
                        name="severity",
                        description="Minimum severity to report: critical, high, medium, low",
                        required=False,
                    ),
                ],
                metadata={"category": self.CATEGORY},
            ),
            # Quick security scan prompt
            PromptDefinition(
                name=f"{PROMPT_PREFIX}security_scan",
                description="Quick security vulnerability scan",
                arguments=[
                    PromptArgument(
                        name="target",
                        description="File, directory, or 'all' to scan",
                        required=True,
                    ),
                    PromptArgument(
                        name="focus",
                        description="Focus area: injection, auth, secrets, dependencies, or all",
                        required=False,
                    ),
                ],
                metadata={"category": self.CATEGORY},
            ),
            # Test coverage prompt
            PromptDefinition(
                name=f"{PROMPT_PREFIX}test_coverage",
                description="Analyze test coverage and suggest improvements",
                arguments=[
                    PromptArgument(
                        name="target",
                        description="Module or file to analyze",
                        required=True,
                    ),
                    PromptArgument(
                        name="coverage_type",
                        description="Coverage type: line, branch, function, or all",
                        required=False,
                    ),
                ],
                metadata={"category": self.CATEGORY},
            ),
            # Documentation check prompt
            PromptDefinition(
                name=f"{PROMPT_PREFIX}doc_check",
                description="Check documentation completeness",
                arguments=[
                    PromptArgument(
                        name="target",
                        description="File or module to check",
                        required=True,
                    ),
                    PromptArgument(
                        name="doc_type",
                        description="Documentation type: docstrings, readme, api, or all",
                        required=False,
                    ),
                ],
                metadata={"category": self.CATEGORY},
            ),
        ]

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None,
    ) -> PromptResult:
        """
        Generate prompt messages for quality gate check.

        Args:
            name: Prompt name to generate
            arguments: Optional arguments to parameterize the prompt

        Returns:
            PromptResult with generated messages

        Raises:
            PromptNotFoundError: If prompt name not supported
        """
        args = arguments or {}

        if name == f"{PROMPT_PREFIX}quality_gate_check":
            return await self._build_quality_gate_prompt(args)
        elif name == f"{PROMPT_PREFIX}security_scan":
            return await self._build_security_prompt(args)
        elif name == f"{PROMPT_PREFIX}test_coverage":
            return await self._build_coverage_prompt(args)
        elif name == f"{PROMPT_PREFIX}doc_check":
            return await self._build_doc_prompt(args)
        else:
            raise PromptNotFoundError(name)

    async def _build_quality_gate_prompt(
        self, args: Dict[str, str]
    ) -> PromptResult:
        """
        Build comprehensive quality gate check prompt.

        Args:
            args: Prompt arguments

        Returns:
            PromptResult with quality gate check guidance
        """
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
                PromptMessage(role="assistant", content=assistant_message),
            ],
        )

    async def _build_security_prompt(self, args: Dict[str, str]) -> PromptResult:
        """
        Build security scan prompt.

        Args:
            args: Prompt arguments

        Returns:
            PromptResult with security scan guidance
        """
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
- [ ] Template injection

### Authentication & Authorization
- [ ] Hardcoded credentials
- [ ] Weak authentication patterns
- [ ] Missing authorization checks
- [ ] Session management issues
- [ ] Insecure direct object references

### Secrets & Sensitive Data
- [ ] API keys in code
- [ ] Passwords in configuration
- [ ] Sensitive data exposure
- [ ] Improper error messages
- [ ] PII handling issues

### Dependencies
- [ ] Known vulnerable packages
- [ ] Outdated dependencies
- [ ] Unnecessary permissions
- [ ] Unverified sources

## Instructions
1. Scan for each vulnerability type
2. Rate severity: Critical, High, Medium, Low
3. Provide specific line numbers and code snippets
4. Suggest remediation steps

## Output Format
- **Severity Summary:** X Critical, Y High, Z Medium
- **Findings:** Detailed per-vulnerability
- **Remediation:** Priority-ordered fixes"""

        assistant_message = """I'll perform a thorough security analysis. Let me scan for vulnerabilities systematically...

## Security Scan
I'll check for each category of security issues and provide severity ratings with specific remediation steps."""

        return PromptResult(
            description=f"Security scan focusing on {focus}",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content=assistant_message),
            ],
        )

    async def _build_coverage_prompt(self, args: Dict[str, str]) -> PromptResult:
        """
        Build test coverage analysis prompt.

        Args:
            args: Prompt arguments

        Returns:
            PromptResult with coverage analysis guidance
        """
        target = args.get("target", "current module")
        coverage_type = args.get("coverage_type", "all")

        user_message = f"""Analyze test coverage for: {target}

## Coverage Analysis Type: {coverage_type}

## Analysis Steps
1. Identify all functions/methods in the target
2. Check which have corresponding tests
3. Identify edge cases not covered
4. Suggest additional test cases

## Coverage Categories

### Line Coverage
- Which lines of code are executed by tests?
- What percentage of lines are covered?

### Branch Coverage
- Are all conditional branches tested?
- Are both true and false paths covered?

### Function Coverage
- Which functions have tests?
- Which functions are untested?

### Edge Cases
- Boundary conditions
- Error handling paths
- Empty/null inputs
- Maximum/minimum values

## Output Format
- **Coverage Summary:** X/Y functions tested (Z%)
- **Uncovered Functions:** List with reasons
- **Missing Edge Cases:** Prioritized list
- **Suggested Test Cases:** With code examples"""

        assistant_message = """I'll analyze the test coverage comprehensively...

## Test Coverage Analysis
Let me identify all testable units and check which have adequate test coverage."""

        return PromptResult(
            description=f"Test coverage analysis for {target}",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content=assistant_message),
            ],
        )

    async def _build_doc_prompt(self, args: Dict[str, str]) -> PromptResult:
        """
        Build documentation check prompt.

        Args:
            args: Prompt arguments

        Returns:
            PromptResult with documentation check guidance
        """
        target = args.get("target", "current file")
        doc_type = args.get("doc_type", "all")

        user_message = f"""Check documentation completeness for: {target}

## Documentation Type: {doc_type}

## Checklist

### Docstrings
- [ ] Module docstring present and descriptive
- [ ] All public functions documented
- [ ] Parameters documented with types
- [ ] Return values documented
- [ ] Examples provided for complex functions
- [ ] Exceptions documented

### README
- [ ] Project description clear
- [ ] Installation instructions complete
- [ ] Usage examples provided
- [ ] API documentation links
- [ ] Contributing guidelines

### API Documentation
- [ ] Endpoint descriptions
- [ ] Request/response schemas
- [ ] Error codes documented
- [ ] Authentication requirements
- [ ] Rate limiting info

### Code Comments
- [ ] Complex logic explained
- [ ] TODO items tracked
- [ ] Workarounds documented
- [ ] Algorithm explanations

## Output Format
- **Coverage Score:** X%
- **Missing Documentation:** Itemized list
- **Quality Issues:** Style, clarity, completeness
- **Priority Fixes:** Most impactful improvements"""

        assistant_message = """I'll review the documentation systematically...

## Documentation Check
Let me analyze the documentation completeness and quality for each category."""

        return PromptResult(
            description=f"Documentation check for {target}",
            messages=[
                PromptMessage(role="user", content=user_message),
                PromptMessage(role="assistant", content=assistant_message),
            ],
        )

    def _get_checklist(self, gate_type: str) -> str:
        """
        Get checklist for specific gate type.

        Args:
            gate_type: Type of quality gate

        Returns:
            Markdown checklist string
        """
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
- [ ] Performance budgets defined""",
        }

        if gate_type == "all":
            return "\n".join(checklists.values())
        return checklists.get(gate_type, checklists["security"])
