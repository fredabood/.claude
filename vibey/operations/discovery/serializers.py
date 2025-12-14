"""Discovery output serializers for YAML and JSON formats.

This module provides serialization and deserialization utilities
for DiscoveryOutput objects.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .schema import DiscoveryOutput


def _datetime_representer(dumper: yaml.Dumper, data: datetime) -> yaml.Node:
    """Custom YAML representer for datetime objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", data.isoformat())


def _enum_representer(dumper: yaml.Dumper, data: Any) -> yaml.Node:
    """Custom YAML representer for Enum objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.value)


# Register custom representers
yaml.add_representer(datetime, _datetime_representer)


class DiscoverySerializer:
    """Serializer for DiscoveryOutput objects."""

    @staticmethod
    def to_dict(
        discovery: DiscoveryOutput,
        exclude_none: bool = True,
        by_alias: bool = False,
    ) -> Dict[str, Any]:
        """Convert DiscoveryOutput to dictionary.

        Args:
            discovery: The discovery output to convert
            exclude_none: Whether to exclude None values
            by_alias: Whether to use field aliases

        Returns:
            Dictionary representation
        """
        return discovery.model_dump(
            mode="json",
            exclude_none=exclude_none,
            by_alias=by_alias,
        )

    @staticmethod
    def to_yaml(
        discovery: DiscoveryOutput,
        exclude_none: bool = True,
        indent: int = 2,
    ) -> str:
        """Serialize DiscoveryOutput to YAML string.

        Args:
            discovery: The discovery output to serialize
            exclude_none: Whether to exclude None values
            indent: YAML indentation level

        Returns:
            YAML string representation
        """
        data = DiscoverySerializer.to_dict(discovery, exclude_none=exclude_none)
        return yaml.dump(
            data,
            default_flow_style=False,
            indent=indent,
            sort_keys=False,
            allow_unicode=True,
        )

    @staticmethod
    def to_json(
        discovery: DiscoveryOutput,
        exclude_none: bool = True,
        indent: Optional[int] = 2,
    ) -> str:
        """Serialize DiscoveryOutput to JSON string.

        Args:
            discovery: The discovery output to serialize
            exclude_none: Whether to exclude None values
            indent: JSON indentation level (None for compact)

        Returns:
            JSON string representation
        """
        data = DiscoverySerializer.to_dict(discovery, exclude_none=exclude_none)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> DiscoveryOutput:
        """Create DiscoveryOutput from dictionary.

        Args:
            data: Dictionary with discovery data

        Returns:
            DiscoveryOutput instance

        Raises:
            ValidationError: If data doesn't match schema
        """
        return DiscoveryOutput.model_validate(data)

    @staticmethod
    def from_yaml(yaml_str: str) -> DiscoveryOutput:
        """Deserialize DiscoveryOutput from YAML string.

        Args:
            yaml_str: YAML string to parse

        Returns:
            DiscoveryOutput instance

        Raises:
            ValidationError: If data doesn't match schema
            yaml.YAMLError: If YAML is invalid
        """
        data = yaml.safe_load(yaml_str)
        return DiscoverySerializer.from_dict(data)

    @staticmethod
    def from_json(json_str: str) -> DiscoveryOutput:
        """Deserialize DiscoveryOutput from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            DiscoveryOutput instance

        Raises:
            ValidationError: If data doesn't match schema
            json.JSONDecodeError: If JSON is invalid
        """
        data = json.loads(json_str)
        return DiscoverySerializer.from_dict(data)

    @staticmethod
    def save_yaml(
        discovery: DiscoveryOutput,
        path: Union[str, Path],
        exclude_none: bool = True,
    ) -> None:
        """Save DiscoveryOutput to YAML file.

        Args:
            discovery: The discovery output to save
            path: File path to save to
            exclude_none: Whether to exclude None values
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        yaml_str = DiscoverySerializer.to_yaml(discovery, exclude_none=exclude_none)
        path.write_text(yaml_str, encoding="utf-8")

    @staticmethod
    def save_json(
        discovery: DiscoveryOutput,
        path: Union[str, Path],
        exclude_none: bool = True,
        indent: Optional[int] = 2,
    ) -> None:
        """Save DiscoveryOutput to JSON file.

        Args:
            discovery: The discovery output to save
            path: File path to save to
            exclude_none: Whether to exclude None values
            indent: JSON indentation level
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        json_str = DiscoverySerializer.to_json(
            discovery, exclude_none=exclude_none, indent=indent
        )
        path.write_text(json_str, encoding="utf-8")

    @staticmethod
    def load_yaml(path: Union[str, Path]) -> DiscoveryOutput:
        """Load DiscoveryOutput from YAML file.

        Args:
            path: File path to load from

        Returns:
            DiscoveryOutput instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If data doesn't match schema
        """
        path = Path(path)
        yaml_str = path.read_text(encoding="utf-8")
        return DiscoverySerializer.from_yaml(yaml_str)

    @staticmethod
    def load_json(path: Union[str, Path]) -> DiscoveryOutput:
        """Load DiscoveryOutput from JSON file.

        Args:
            path: File path to load from

        Returns:
            DiscoveryOutput instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If data doesn't match schema
        """
        path = Path(path)
        json_str = path.read_text(encoding="utf-8")
        return DiscoverySerializer.from_json(json_str)


# Convenience functions for direct use
to_yaml = DiscoverySerializer.to_yaml
to_json = DiscoverySerializer.to_json
from_yaml = DiscoverySerializer.from_yaml
from_json = DiscoverySerializer.from_json
save_yaml = DiscoverySerializer.save_yaml
save_json = DiscoverySerializer.save_json
load_yaml = DiscoverySerializer.load_yaml
load_json = DiscoverySerializer.load_json
