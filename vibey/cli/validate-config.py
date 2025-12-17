#!/usr/bin/env python3
"""
Config Validator for Vibey Framework

Validates project-config.yaml against schema.yaml
Provides helpful error messages and suggestions

Usage:
    python scripts/validate-config.py project-config.yaml
    python scripts/validate-config.py --config my-config.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


class ConfigValidator:
    """Validates project config against schema"""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _load_schema(self) -> Dict[str, Any]:
        """Load the schema.yaml file"""
        if not self.schema_path.exists():
            print(f"Error: Schema file not found at {self.schema_path}")
            sys.exit(1)

        with open(self.schema_path) as f:
            return yaml.safe_load(f)

    def validate_config(self, config_path: Path) -> bool:
        """Validate a config file against the schema"""
        if not config_path.exists():
            self.errors.append(f"Config file not found: {config_path}")
            return False

        with open(config_path) as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                self.errors.append(f"Invalid YAML syntax: {e}")
                return False

        if config is None:
            self.errors.append("Config file is empty")
            return False

        # Validate project section
        self._validate_project(config.get("project", {}))

        # Validate technology_stack section
        self._validate_technology_stack(config.get("technology_stack", {}))

        # Validate project-type specific sections
        project_type = config.get("project", {}).get("type")
        if project_type == "web-app":
            self._validate_web_framework(config.get("web_framework", {}))
        elif project_type == "ml":
            self._validate_ml_platform(config.get("ml_platform", {}))
        elif project_type == "infrastructure":
            self._validate_infrastructure(config)

        # Validate optional sections
        if "database" in config:
            self._validate_database(config["database"])

        if "quality_gates" in config:
            self._validate_quality_gates(config["quality_gates"])

        return len(self.errors) == 0

    def _validate_project(self, project: Dict[str, Any]):
        """Validate project section"""
        if not project:
            self.errors.append("Missing required section: project")
            return

        # Required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in project:
                self.errors.append(f"Missing required field: project.{field}")

        # Validate type
        valid_types = ["web-app", "api", "data-platform", "ml", "infrastructure"]
        if "type" in project and project["type"] not in valid_types:
            self.errors.append(
                f"Invalid project.type: '{project['type']}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        # Validate name
        if "name" in project:
            name = project["name"]
            if not isinstance(name, str) or len(name) == 0:
                self.errors.append("project.name must be a non-empty string")
            elif " " in name:
                self.warnings.append(
                    "project.name contains spaces. Consider using kebab-case or snake_case"
                )

    def _validate_technology_stack(self, tech_stack: Dict[str, Any]):
        """Validate technology_stack section"""
        if not tech_stack:
            self.warnings.append("Missing section: technology_stack (recommended)")
            return

        # Validate backend
        if "backend" in tech_stack:
            backend = tech_stack["backend"]
            valid_languages = ["python", "typescript", "javascript", "java", "go", "rust"]

            if "language" in backend:
                if backend["language"] not in valid_languages:
                    self.warnings.append(
                        f"Uncommon backend language: '{backend['language']}'. "
                        f"Supported: {', '.join(valid_languages)}"
                    )

            if "framework" in backend:
                # Map languages to common frameworks
                framework_suggestions = {
                    "python": ["fastapi", "django", "flask"],
                    "typescript": ["express", "nestjs", "fastify"],
                    "javascript": ["express", "koa", "fastify"],
                    "java": ["spring-boot", "quarkus", "micronaut"],
                    "go": ["gin", "echo", "fiber"],
                }

                lang = backend.get("language")
                framework = backend["framework"]

                if lang in framework_suggestions:
                    if framework not in framework_suggestions[lang]:
                        self.warnings.append(
                            f"Uncommon {lang} framework: '{framework}'. "
                            f"Common choices: {', '.join(framework_suggestions[lang])}"
                        )

        # Validate frontend
        if "frontend" in tech_stack:
            frontend = tech_stack["frontend"]
            valid_languages = ["typescript", "javascript"]
            valid_frameworks = ["react", "vue", "angular", "svelte"]

            if "language" in frontend and frontend["language"] not in valid_languages:
                self.warnings.append(
                    f"Uncommon frontend language: '{frontend['language']}'. "
                    f"Supported: {', '.join(valid_languages)}"
                )

            if "framework" in frontend and frontend["framework"] not in valid_frameworks:
                self.warnings.append(
                    f"Uncommon frontend framework: '{frontend['framework']}'. "
                    f"Supported: {', '.join(valid_frameworks)}"
                )

    def _validate_web_framework(self, web_framework: Dict[str, Any]):
        """Validate web_framework section (for web-app projects)"""
        if not web_framework:
            self.warnings.append(
                "Missing section: web_framework (recommended for web-app projects)"
            )
            return

        # Validate frontend framework
        valid_frontend = ["react", "vue", "angular", "svelte"]
        if "frontend" in web_framework and web_framework["frontend"] not in valid_frontend:
            self.warnings.append(
                f"Uncommon frontend framework: '{web_framework['frontend']}'. "
                f"Supported: {', '.join(valid_frontend)}"
            )

        # Validate UI library
        valid_ui_libs = [
            "material-ui",
            "ant-design",
            "chakra-ui",
            "blueprint",
            "tailwind",
            "bootstrap",
        ]
        if "ui_library" in web_framework:
            ui_lib = web_framework["ui_library"]
            if ui_lib not in valid_ui_libs:
                self.warnings.append(
                    f"Uncommon UI library: '{ui_lib}'. "
                    f"Supported: {', '.join(valid_ui_libs)}"
                )

        # Validate state management
        if "state_management" in web_framework:
            state_mgmt = web_framework["state_management"]
            if isinstance(state_mgmt, dict) and "library" in state_mgmt:
                valid_state = ["redux", "zustand", "pinia", "ngrx", "context-api", "jotai"]
                if state_mgmt["library"] not in valid_state:
                    self.warnings.append(
                        f"Uncommon state management: '{state_mgmt['library']}'. "
                        f"Supported: {', '.join(valid_state)}"
                    )

    def _validate_ml_platform(self, ml_platform: Dict[str, Any]):
        """Validate ml_platform section (for ML projects)"""
        if not ml_platform:
            self.warnings.append(
                "Missing section: ml_platform (recommended for ml projects)"
            )
            return

        valid_tracking = ["mlflow", "wandb", "tensorboard", "sagemaker"]
        if "experiment_tracking" in ml_platform:
            tracking = ml_platform["experiment_tracking"]
            if tracking not in valid_tracking:
                self.warnings.append(
                    f"Uncommon experiment tracking: '{tracking}'. "
                    f"Supported: {', '.join(valid_tracking)}"
                )

        valid_feature_stores = ["feast", "tecton", "hopsworks"]
        if "feature_store" in ml_platform:
            fs = ml_platform["feature_store"]
            if fs not in valid_feature_stores:
                self.warnings.append(
                    f"Uncommon feature store: '{fs}'. "
                    f"Supported: {', '.join(valid_feature_stores)}"
                )

    def _validate_infrastructure(self, config: Dict[str, Any]):
        """Validate infrastructure configuration"""
        valid_clouds = ["aws", "azure", "gcp"]
        if "cloud_provider" in config:
            cloud = config["cloud_provider"]
            if cloud not in valid_clouds:
                self.warnings.append(
                    f"Uncommon cloud provider: '{cloud}'. "
                    f"Supported: {', '.join(valid_clouds)}"
                )

        valid_iac = ["terraform", "pulumi", "cloudformation"]
        if "iac_tool" in config:
            iac = config["iac_tool"]
            if iac not in valid_iac:
                self.warnings.append(
                    f"Uncommon IaC tool: '{iac}'. " f"Supported: {', '.join(valid_iac)}"
                )

    def _validate_database(self, database: Dict[str, Any]):
        """Validate database section"""
        valid_types = ["relational", "document", "graph", "time-series", "key-value"]
        if "type" in database and database["type"] not in valid_types:
            self.warnings.append(
                f"Uncommon database type: '{database['type']}'. "
                f"Supported: {', '.join(valid_types)}"
            )

        # Map types to engines
        engine_suggestions = {
            "relational": ["postgresql", "mysql", "sqlite"],
            "document": ["mongodb", "couchdb"],
            "graph": ["neo4j", "arangodb"],
            "time-series": ["influxdb", "timescaledb"],
            "key-value": ["redis", "dynamodb"],
        }

        if "engine" in database and "type" in database:
            db_type = database["type"]
            engine = database["engine"]

            if db_type in engine_suggestions:
                if engine not in engine_suggestions[db_type]:
                    self.warnings.append(
                        f"Uncommon {db_type} engine: '{engine}'. "
                        f"Common choices: {', '.join(engine_suggestions[db_type])}"
                    )

    def _validate_quality_gates(self, quality_gates: Dict[str, Any]):
        """Validate quality_gates section"""
        if "test_coverage_minimum" in quality_gates:
            coverage = quality_gates["test_coverage_minimum"]
            if not isinstance(coverage, (int, float)):
                self.errors.append("quality_gates.test_coverage_minimum must be a number")
            elif coverage < 0 or coverage > 100:
                self.errors.append(
                    "quality_gates.test_coverage_minimum must be between 0 and 100"
                )
            elif coverage < 80:
                self.warnings.append(
                    f"Low test coverage minimum: {coverage}%. Recommended: 90%+"
                )

        if "security_score_minimum" in quality_gates:
            score = quality_gates["security_score_minimum"]
            if not isinstance(score, (int, float)):
                self.errors.append("quality_gates.security_score_minimum must be a number")
            elif score < 0 or score > 100:
                self.errors.append(
                    "quality_gates.security_score_minimum must be between 0 and 100"
                )

    def print_results(self):
        """Print validation results"""
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ Config is valid!")
        elif not self.errors:
            print("✅ Config is valid (with warnings)")
        else:
            print("❌ Config validation failed")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Vibey project config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate-config.py project-config.yaml
  python scripts/validate-config.py --config my-config.yaml
  python scripts/validate-config.py --schema custom-schema.yaml my-config.yaml
        """,
    )

    parser.add_argument(
        "config_file",
        nargs="?",
        default="project-config.yaml",
        help="Path to config file (default: project-config.yaml)",
    )

    parser.add_argument(
        "--config",
        "-c",
        dest="config_file_alt",
        help="Alternative way to specify config file",
    )

    parser.add_argument(
        "--schema",
        "-s",
        default="config/schema.yaml",
        help="Path to schema file (default: config/schema.yaml)",
    )

    args = parser.parse_args()

    # Determine config file path
    config_file = args.config_file_alt if args.config_file_alt else args.config_file
    config_path = Path(config_file)
    schema_path = Path(args.schema)

    print(f"Validating: {config_path}")
    print(f"Schema: {schema_path}")
    print()

    validator = ConfigValidator(schema_path)
    is_valid = validator.validate_config(config_path)
    validator.print_results()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
