#!/usr/bin/env python3
"""
Validate Vibey Configuration Files

Validates .vibey/config/ files against their JSON schemas.

Usage:
    python3 framework/scripts/validate-vibey-config.py
    python3 framework/scripts/validate-vibey-config.py --file .vibey/config/project.yaml
    python3 framework/scripts/validate-vibey-config.py --strict

Created: 2025-11-09
Sprint: core-framework-2, Task 2
"""

import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Try to import jsonschema, provide helpful error if missing
try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("❌ Error: jsonschema package not installed")
    print("Install with: pip install jsonschema")
    sys.exit(1)


class VibeyConfigValidator:
    """Validate Vibey configuration files against schemas"""

    def __init__(self, vibey_dir: Path = None):
        self.vibey_dir = vibey_dir or self.find_vibey_dir()
        self.config_dir = self.vibey_dir / "config"
        self.schema_dir = self.vibey_dir.parent / "framework" / "schemas" / "config"

        self.schema_map = {
            "project.yaml": "project_config.schema.yaml",
            "framework.yaml": "framework_config.schema.yaml",
            "quality-gates.yaml": "quality_gates.schema.yaml",
        }

        self.errors: List[str] = []
        self.warnings: List[str] = []

    @staticmethod
    def find_vibey_dir() -> Path:
        """Find .vibey directory"""
        current = Path.cwd()
        while current != current.parent:
            vibey_dir = current / ".vibey"
            if vibey_dir.exists() and vibey_dir.is_dir():
                return vibey_dir
            current = current.parent

        raise FileNotFoundError("❌ .vibey directory not found")

    def load_yaml(self, file_path: Path) -> Dict:
        """Load YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")

    def load_schema(self, schema_file: str) -> Dict:
        """Load JSON schema from YAML file"""
        schema_path = self.schema_dir / schema_file
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        schema = self.load_yaml(schema_path)

        # Remove $schema field for jsonschema validation
        if '$schema' in schema:
            del schema['$schema']

        return schema

    def validate_file(self, config_file: Path, schema_file: str) -> Tuple[bool, List[str]]:
        """
        Validate a config file against its schema

        Returns:
            (is_valid, errors)
        """
        errors = []

        try:
            # Load config and schema
            config = self.load_yaml(config_file)
            schema = self.load_schema(schema_file)

            # Validate
            validate(instance=config, schema=schema)

            return True, []

        except FileNotFoundError as e:
            errors.append(f"File not found: {e}")
            return False, errors

        except ValueError as e:
            errors.append(f"YAML parsing error: {e}")
            return False, errors

        except ValidationError as e:
            # Format validation error nicely
            error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            errors.append(f"Validation error at {error_path}: {e.message}")
            return False, errors

        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            return False, errors

    def validate_agent(self, agent_file: Path) -> Tuple[bool, List[str]]:
        """Validate agent config"""
        return self.validate_file(agent_file, "agent_config.schema.yaml")

    def validate_workflow(self, workflow_file: Path) -> Tuple[bool, List[str]]:
        """Validate workflow config"""
        return self.validate_file(workflow_file, "workflow_config.schema.yaml")

    def validate_all(self, strict: bool = False) -> bool:
        """
        Validate all config files

        Args:
            strict: Fail on warnings

        Returns:
            True if all valid, False otherwise
        """
        print("🔍 Validating Vibey configuration files...\n")

        all_valid = True

        # Validate main config files
        for config_file, schema_file in self.schema_map.items():
            config_path = self.config_dir / config_file

            if not config_path.exists():
                self.warnings.append(f"⚠️  {config_file} not found (optional)")
                continue

            print(f"Validating {config_file}...", end=" ")

            is_valid, errors = self.validate_file(config_path, schema_file)

            if is_valid:
                print("✅")
            else:
                print("❌")
                all_valid = False
                for error in errors:
                    print(f"  ❌ {error}")
                print()

        # Validate agents
        agents_dir = self.config_dir / "agents"
        if agents_dir.exists():
            agent_files = list(agents_dir.glob("*.yaml"))
            if agent_files:
                print(f"\nValidating {len(agent_files)} agent(s)...")
                for agent_file in agent_files:
                    print(f"  {agent_file.name}...", end=" ")
                    is_valid, errors = self.validate_agent(agent_file)

                    if is_valid:
                        print("✅")
                    else:
                        print("❌")
                        all_valid = False
                        for error in errors:
                            print(f"    ❌ {error}")

        # Validate workflows
        workflows_dir = self.config_dir / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yaml"))
            if workflow_files:
                print(f"\nValidating {len(workflow_files)} workflow(s)...")
                for workflow_file in workflow_files:
                    print(f"  {workflow_file.name}...", end=" ")
                    is_valid, errors = self.validate_workflow(workflow_file)

                    if is_valid:
                        print("✅")
                    else:
                        print("❌")
                        all_valid = False
                        for error in errors:
                            print(f"    ❌ {error}")

        # Print warnings
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

        # Summary
        print("\n" + "=" * 60)
        if all_valid and (not strict or not self.warnings):
            print("✅ All configuration files are valid!")
            return True
        elif all_valid and strict and self.warnings:
            print("❌ Validation failed (strict mode with warnings)")
            return False
        else:
            print("❌ Validation failed - please fix errors above")
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Vibey configuration files"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Validate specific file only"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Vibey directory (default: auto-detect)"
    )

    args = parser.parse_args()

    try:
        vibey_dir = Path(args.dir) if args.dir else None
        validator = VibeyConfigValidator(vibey_dir)

        if args.file:
            # Validate single file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                sys.exit(1)

            # Determine schema
            file_name = file_path.name
            if file_name in validator.schema_map:
                schema_file = validator.schema_map[file_name]
            elif file_path.parent.name == "agents":
                schema_file = "agent_config.schema.yaml"
            elif file_path.parent.name == "workflows":
                schema_file = "workflow_config.schema.yaml"
            else:
                print(f"❌ Unknown config file type: {file_name}")
                sys.exit(1)

            print(f"🔍 Validating {file_path}...")
            is_valid, errors = validator.validate_file(file_path, schema_file)

            if is_valid:
                print("✅ Configuration is valid!")
                sys.exit(0)
            else:
                print("❌ Validation failed:")
                for error in errors:
                    print(f"  ❌ {error}")
                sys.exit(1)
        else:
            # Validate all
            is_valid = validator.validate_all(strict=args.strict)
            sys.exit(0 if is_valid else 1)

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
