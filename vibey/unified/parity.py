"""
CLI/MCP Parity Checker.

Verifies that commands registered with @unified_command maintain
parity across CLI and MCP interfaces, and generates reports.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .command import CommandSpec, Interface
from .registry import COMMAND_REGISTRY


@dataclass
class ParityViolation:
    """
    A parity violation between CLI and MCP interfaces.

    Attributes:
        command_name: Name of the command with the violation
        violation_type: Type of violation (missing, param_mismatch, etc.)
        description: Human-readable description of the violation
        severity: Severity level (error, warning)
    """

    command_name: str
    violation_type: str
    description: str
    severity: str = "error"


@dataclass
class ParityReport:
    """
    Complete parity report for CLI/MCP commands.

    Attributes:
        total_commands: Total number of unified commands
        cli_only_commands: Commands only in CLI
        mcp_only_commands: Commands only in MCP
        both_interfaces_commands: Commands in both interfaces
        violations: List of parity violations
        excluded_commands: Commands intentionally excluded with reasons
    """

    total_commands: int = 0
    cli_only_commands: List[str] = field(default_factory=list)
    mcp_only_commands: List[str] = field(default_factory=list)
    both_interfaces_commands: List[str] = field(default_factory=list)
    violations: List[ParityViolation] = field(default_factory=list)
    excluded_commands: Dict[str, str] = field(default_factory=dict)

    @property
    def is_passing(self) -> bool:
        """Check if parity check passes (no errors)."""
        return not any(v.severity == "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return sum(1 for v in self.violations if v.severity == "warning")

    def format_report(self, verbose: bool = False) -> str:
        """
        Format the report as a human-readable string.

        Args:
            verbose: Include additional details

        Returns:
            Formatted report string
        """
        lines = [
            "CLI/MCP Parity Report",
            "=====================",
            f"Total unified commands: {self.total_commands}",
            f"  - Both interfaces: {len(self.both_interfaces_commands)}",
            f"  - CLI only: {len(self.cli_only_commands)}",
            f"  - MCP only: {len(self.mcp_only_commands)}",
            "",
        ]

        # Status
        if self.is_passing:
            lines.append("Parity Status: PASS")
        else:
            lines.append(f"Parity Status: FAIL ({self.error_count} errors)")

        # Violations
        if self.violations:
            lines.append("")
            lines.append("Violations:")
            for v in self.violations:
                marker = "[ERROR]" if v.severity == "error" else "[WARN]"
                lines.append(f"  {marker} {v.command_name}: {v.description}")

        # Excluded commands (if verbose or any exclusions)
        if self.excluded_commands and (verbose or len(self.excluded_commands) > 0):
            lines.append("")
            lines.append("Commands intentionally excluded:")
            for cmd_name, reason in sorted(self.excluded_commands.items()):
                interface = self._get_excluded_interface(cmd_name)
                lines.append(f"  - {cmd_name} ({interface}): {reason}")

        if verbose:
            lines.append("")
            lines.append("Detailed command list:")
            if self.both_interfaces_commands:
                lines.append("  Both interfaces:")
                for cmd in sorted(self.both_interfaces_commands):
                    lines.append(f"    - {cmd}")
            if self.cli_only_commands:
                lines.append("  CLI only:")
                for cmd in sorted(self.cli_only_commands):
                    lines.append(f"    - {cmd}")
            if self.mcp_only_commands:
                lines.append("  MCP only:")
                for cmd in sorted(self.mcp_only_commands):
                    lines.append(f"    - {cmd}")

        return "\n".join(lines)

    def _get_excluded_interface(self, cmd_name: str) -> str:
        """Get which interface a command is excluded from."""
        if cmd_name in self.cli_only_commands:
            return "MCP excluded"
        elif cmd_name in self.mcp_only_commands:
            return "CLI excluded"
        return "unknown"


class ParityChecker:
    """
    Checks CLI/MCP parity for unified commands.

    Verifies that:
    - All commands intended for both interfaces are present in both
    - Parameter definitions match between interfaces
    - Descriptions are consistent
    - All exclusions have documented reasons
    """

    def __init__(self) -> None:
        """Initialize the parity checker."""
        pass

    def check(self) -> ParityReport:
        """
        Run a complete parity check.

        Returns:
            ParityReport with check results
        """
        report = ParityReport()

        all_commands = COMMAND_REGISTRY.list_all()
        report.total_commands = len(all_commands)

        for spec in all_commands:
            in_cli = spec.is_available_in(Interface.CLI)
            in_mcp = spec.is_available_in(Interface.MCP)

            if in_cli and in_mcp:
                report.both_interfaces_commands.append(spec.name)
                # Check for parameter/description mismatches
                self._check_consistency(spec, report)
            elif in_cli:
                report.cli_only_commands.append(spec.name)
                self._check_exclusion_documented(spec, Interface.MCP, report)
            elif in_mcp:
                report.mcp_only_commands.append(spec.name)
                self._check_exclusion_documented(spec, Interface.CLI, report)

            # Record exclusion reason if present
            if spec.exclusion_reason:
                report.excluded_commands[spec.name] = spec.exclusion_reason

        return report

    def _check_consistency(self, spec: CommandSpec, report: ParityReport) -> None:
        """
        Check that a dual-interface command is consistent.

        Args:
            spec: Command specification
            report: Report to add violations to
        """
        # Currently, unified commands are inherently consistent since they
        # share the same definition. This method is a placeholder for
        # future checks like:
        # - CLI-specific params that should be in MCP
        # - MCP-specific params that should be in CLI
        # - Description drift (if we add interface-specific descriptions)
        pass

    def _check_exclusion_documented(
        self,
        spec: CommandSpec,
        excluded_interface: Interface,
        report: ParityReport,
    ) -> None:
        """
        Check that an interface exclusion is documented.

        Args:
            spec: Command specification
            excluded_interface: The interface the command is excluded from
            report: Report to add violations to
        """
        if not spec.exclusion_reason:
            report.violations.append(
                ParityViolation(
                    command_name=spec.name,
                    violation_type="undocumented_exclusion",
                    description=(
                        f"Command excluded from {excluded_interface.value} "
                        "without exclusion_reason"
                    ),
                    severity="warning",
                )
            )


def check_parity() -> ParityReport:
    """
    Run a parity check on the unified command registry.

    Convenience function that creates a checker and runs the check.

    Returns:
        ParityReport with check results
    """
    checker = ParityChecker()
    return checker.check()


def format_parity_report(verbose: bool = False) -> str:
    """
    Run a parity check and return a formatted report.

    Args:
        verbose: Include detailed command lists

    Returns:
        Formatted report string
    """
    report = check_parity()
    return report.format_report(verbose=verbose)
