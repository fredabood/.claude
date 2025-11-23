"""
Frontmatter Validator

Validates YAML frontmatter in agents, workflows, and handoffs
for MCP server dynamic tool discovery.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import yaml


# Required fields by asset type
REQUIRED_FIELDS = {
    'agents': ['id', 'name', 'type', 'version'],
    'workflows': ['id', 'name', 'type', 'version'],
    'handoffs': ['id', 'name', 'version'],
}

# Valid enum values
VALID_AGENT_TYPES = ['core', 'planning', 'development', 'quality', 'documentation', 'architecture']
VALID_WORKFLOW_TYPES = ['planning', 'development', 'quality', 'documentation', 'deployment']
VALID_PRIORITIES = ['high', 'medium', 'low']
VALID_INPUT_TYPES = ['string', 'integer', 'boolean', 'array', 'object']


@dataclass
class AssetValidationResult:
    """Result of validating a single asset."""
    filepath: Path
    asset_type: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class FrontmatterValidationReport:
    """Report of frontmatter validation."""
    assets_checked: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    results: List[AssetValidationResult] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.invalid_count == 0

    def add_result(self, result: AssetValidationResult):
        self.assets_checked += 1
        if result.is_valid:
            self.valid_count += 1
        else:
            self.invalid_count += 1
        self.results.append(result)


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.strip().startswith('---'):
        return None, content

    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not match:
        return None, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]
        return frontmatter, body
    except yaml.YAMLError as e:
        return {'_error': str(e)}, content


def validate_agent(frontmatter: Dict[str, Any]) -> List[str]:
    """Validate agent frontmatter."""
    errors = []

    for field in REQUIRED_FIELDS['agents']:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    if 'type' in frontmatter and frontmatter['type'] not in VALID_AGENT_TYPES:
        errors.append(f"Invalid agent type: {frontmatter['type']} (valid: {VALID_AGENT_TYPES})")

    if 'triggers' in frontmatter:
        triggers = frontmatter['triggers']
        if 'priority' in triggers and triggers['priority'] not in VALID_PRIORITIES:
            errors.append(f"Invalid priority: {triggers['priority']} (valid: {VALID_PRIORITIES})")

    if 'inputs' in frontmatter:
        for i, inp in enumerate(frontmatter['inputs']):
            if 'name' not in inp:
                errors.append(f"Input {i} missing 'name' field")
            if 'type' in inp and inp['type'] not in VALID_INPUT_TYPES:
                errors.append(f"Input {inp.get('name', i)} has invalid type: {inp['type']}")

    if 'outputs' in frontmatter:
        for i, out in enumerate(frontmatter['outputs']):
            if 'name' not in out:
                errors.append(f"Output {i} missing 'name' field")

    return errors


def validate_workflow(frontmatter: Dict[str, Any]) -> List[str]:
    """Validate workflow frontmatter."""
    errors = []

    for field in REQUIRED_FIELDS['workflows']:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    if 'type' in frontmatter and frontmatter['type'] not in VALID_WORKFLOW_TYPES:
        errors.append(f"Invalid workflow type: {frontmatter['type']} (valid: {VALID_WORKFLOW_TYPES})")

    if 'steps' in frontmatter:
        for i, step in enumerate(frontmatter['steps']):
            if 'order' not in step:
                errors.append(f"Step {i} missing 'order' field")
            if 'name' not in step:
                errors.append(f"Step {i} missing 'name' field")

    if 'inputs' in frontmatter:
        for i, inp in enumerate(frontmatter['inputs']):
            if 'name' not in inp:
                errors.append(f"Input {i} missing 'name' field")

    return errors


def validate_handoff(frontmatter: Dict[str, Any]) -> List[str]:
    """Validate handoff template frontmatter."""
    errors = []

    for field in REQUIRED_FIELDS['handoffs']:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    if 'variables' in frontmatter:
        for i, var in enumerate(frontmatter['variables']):
            if 'name' not in var:
                errors.append(f"Variable {i} missing 'name' field")

    return errors


class FrontmatterValidator:
    """Validates frontmatter in Vibey assets."""

    def __init__(self, root_dir: Path, verbose: bool = False):
        self.root_dir = root_dir
        self.verbose = verbose
        self.report = FrontmatterValidationReport()

    def validate_file(self, filepath: Path, asset_type: str) -> AssetValidationResult:
        """Validate a single file's frontmatter."""
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            return AssetValidationResult(
                filepath=filepath,
                asset_type=asset_type,
                is_valid=False,
                errors=[f"Cannot read file: {e}"]
            )

        frontmatter, _ = extract_frontmatter(content)

        if frontmatter is None:
            return AssetValidationResult(
                filepath=filepath,
                asset_type=asset_type,
                is_valid=False,
                errors=["No frontmatter found"]
            )

        if '_error' in frontmatter:
            return AssetValidationResult(
                filepath=filepath,
                asset_type=asset_type,
                is_valid=False,
                errors=[f"YAML parse error: {frontmatter['_error']}"]
            )

        # Validate based on type
        if asset_type == 'agents':
            errors = validate_agent(frontmatter)
        elif asset_type == 'workflows':
            errors = validate_workflow(frontmatter)
        elif asset_type == 'handoffs':
            errors = validate_handoff(frontmatter)
        else:
            errors = [f"Unknown asset type: {asset_type}"]

        return AssetValidationResult(
            filepath=filepath,
            asset_type=asset_type,
            is_valid=len(errors) == 0,
            errors=errors
        )

    def validate_assets(self, asset_type: str) -> FrontmatterValidationReport:
        """Validate all assets of a given type."""
        if asset_type == 'agents':
            search_dir = self.root_dir / 'framework' / 'agents'
        elif asset_type == 'workflows':
            search_dir = self.root_dir / 'framework' / 'workflows'
        elif asset_type == 'handoffs':
            search_dir = self.root_dir / 'framework' / 'templates' / 'handoffs'
        else:
            return self.report

        if not search_dir.exists():
            return self.report

        for filepath in search_dir.rglob('*.md'):
            if filepath.name.lower() == 'readme.md':
                continue

            result = self.validate_file(filepath, asset_type)
            self.report.add_result(result)

        return self.report

    def validate_all(self) -> FrontmatterValidationReport:
        """Validate all asset types."""
        for asset_type in ['agents', 'workflows', 'handoffs']:
            self.validate_assets(asset_type)
        return self.report


def validate_assets(root_dir: Path, asset_type: str = 'all', verbose: bool = False) -> FrontmatterValidationReport:
    """Convenience function to validate assets."""
    validator = FrontmatterValidator(root_dir, verbose)
    if asset_type == 'all':
        return validator.validate_all()
    return validator.validate_assets(asset_type)
