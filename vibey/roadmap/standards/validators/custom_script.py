"""
Custom script validator for roadmap standards.

Executes custom validation scripts and interprets their results.
"""

import subprocess
from pathlib import Path

from ..validator_base import ValidatorBase, ValidationResult, ValidationIssue
from ...models import Standard, StandardType


class CustomScriptValidator(ValidatorBase):
    """
    Validator that executes custom validation scripts.

    Configuration format in standard.validation:
    {
        "script": str,           # Path to script (relative to root_dir or absolute)
        "args": List[str]        # Optional additional arguments
    }

    Script behavior:
    - Receives item_id as first argument
    - Must exit with code 0 for pass, non-zero for fail
    - stdout/stderr captured for issues
    - Lines starting with "ERROR:" or "WARNING:" are parsed as issues

    Example:
        Standard(
            id="custom-validation",
            type=StandardType.CUSTOM_SCRIPT,
            validation={
                "script": "scripts/validate-task.sh",
                "args": ["--strict"]
            }
        )
    """

    def can_validate(self, standard: Standard) -> bool:
        """Check if this validator can validate the given standard."""
        return standard.type == StandardType.CUSTOM_SCRIPT

    def validate(self, standard: Standard, item_id: str) -> ValidationResult:
        """
        Execute custom validation script.

        Args:
            standard: Standard configuration
            item_id: ID of item being validated

        Returns:
            ValidationResult with pass/fail based on script exit code
        """
        try:
            # Get script path from validation config
            script_path = standard.validation.get("script")
            if not script_path:
                return self._create_error_result(
                    standard.id,
                    "Script path not specified in validation config"
                )

            # Resolve script path (relative to root_dir or absolute)
            script_path_obj = Path(script_path)
            if not script_path_obj.is_absolute():
                script_path_obj = Path(self.root_dir) / script_path

            # Check if script exists and is executable
            if not script_path_obj.exists():
                return self._create_error_result(
                    standard.id,
                    f"Script not found: {script_path_obj}"
                )

            if not script_path_obj.is_file():
                return self._create_error_result(
                    standard.id,
                    f"Script path is not a file: {script_path_obj}"
                )

            # Build command with arguments
            command = [str(script_path_obj), item_id]

            # Add optional arguments
            additional_args = standard.validation.get("args", [])
            if additional_args:
                command.extend(additional_args)

            # Execute script
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=self.root_dir
                )
            except subprocess.TimeoutExpired:
                return self._create_error_result(
                    standard.id,
                    "Script execution timed out (5 minute limit)"
                )
            except Exception as e:
                return self._create_error_result(
                    standard.id,
                    f"Failed to execute script: {e}",
                    error=e
                )

            # Parse output for issues
            issues = self._parse_output(result.stdout, result.stderr)

            # Check exit code
            if result.returncode == 0:
                # Script passed
                message = f"Custom validation passed: {script_path}"
                metadata = {
                    "script": str(script_path_obj),
                    "exit_code": result.returncode,
                    "item_id": item_id
                }

                # Include stdout if present (might have useful info even on pass)
                if result.stdout.strip():
                    metadata["output"] = result.stdout.strip()

                return self._create_passed_result(
                    standard.id,
                    message,
                    metadata=metadata
                )
            else:
                # Script failed
                message = f"Custom validation failed: {script_path} (exit code: {result.returncode})"

                # If no issues parsed from output, create a generic one
                if not issues:
                    issues.append(ValidationIssue(
                        severity="error",
                        message=f"Script exited with code {result.returncode}",
                        details={
                            "stdout": result.stdout.strip() if result.stdout.strip() else None,
                            "stderr": result.stderr.strip() if result.stderr.strip() else None
                        }
                    ))

                metadata = {
                    "script": str(script_path_obj),
                    "exit_code": result.returncode,
                    "item_id": item_id
                }

                return self._create_failed_result(
                    standard.id,
                    message,
                    issues=issues,
                    metadata=metadata
                )

        except Exception as e:
            return self._create_error_result(
                standard.id,
                "Unexpected error during custom validation",
                error=e
            )

    def _parse_output(self, stdout: str, stderr: str) -> list[ValidationIssue]:
        """
        Parse script output for structured issues.

        Lines starting with:
        - "ERROR:" are treated as error-level issues
        - "WARNING:" are treated as warning-level issues
        - "INFO:" are treated as info-level issues

        Args:
            stdout: Standard output from script
            stderr: Standard error from script

        Returns:
            List of ValidationIssue objects
        """
        issues = []

        # Parse stdout
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("ERROR:"):
                issues.append(ValidationIssue(
                    severity="error",
                    message=line[6:].strip(),
                    details={"source": "stdout"}
                ))
            elif line.startswith("WARNING:"):
                issues.append(ValidationIssue(
                    severity="warning",
                    message=line[8:].strip(),
                    details={"source": "stdout"}
                ))
            elif line.startswith("INFO:"):
                issues.append(ValidationIssue(
                    severity="info",
                    message=line[5:].strip(),
                    details={"source": "stdout"}
                ))

        # Parse stderr (treat all as errors unless prefixed)
        for line in stderr.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("WARNING:"):
                issues.append(ValidationIssue(
                    severity="warning",
                    message=line[8:].strip(),
                    details={"source": "stderr"}
                ))
            elif line.startswith("INFO:"):
                issues.append(ValidationIssue(
                    severity="info",
                    message=line[5:].strip(),
                    details={"source": "stderr"}
                ))
            else:
                # Treat unprefixed stderr as error
                issues.append(ValidationIssue(
                    severity="error",
                    message=line,
                    details={"source": "stderr"}
                ))

        return issues
