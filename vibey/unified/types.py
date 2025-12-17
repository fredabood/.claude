"""
Unified type system for CLI/MCP parity.

Maps unified parameter types to both Click types and JSON Schema types,
enabling single-source command definitions that work across both interfaces.
"""

from enum import Enum
from typing import Any, Dict, TYPE_CHECKING

import click

if TYPE_CHECKING:
    from .param import ParamSpec


class ParamType(Enum):
    """Unified parameter types that map to both Click and JSON Schema."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    CHOICE = "choice"
    LIST = "list"


# Click type mapping
CLICK_TYPE_MAP: Dict[ParamType, Any] = {
    ParamType.STRING: click.STRING,
    ParamType.INTEGER: click.INT,
    ParamType.FLOAT: click.FLOAT,
    ParamType.BOOLEAN: click.BOOL,
    ParamType.PATH: click.Path(exists=False),
}

# JSON Schema type mapping
JSON_SCHEMA_TYPE_MAP: Dict[ParamType, Dict[str, Any]] = {
    ParamType.STRING: {"type": "string"},
    ParamType.INTEGER: {"type": "integer"},
    ParamType.FLOAT: {"type": "number"},
    ParamType.BOOLEAN: {"type": "boolean"},
    ParamType.PATH: {"type": "string"},
    ParamType.LIST: {"type": "array"},
    ParamType.CHOICE: {"type": "string"},
}


def param_to_click_type(param: "ParamSpec") -> Any:
    """
    Convert ParamSpec to Click type.

    Args:
        param: The parameter specification

    Returns:
        Click type object suitable for use with click.option/argument
    """
    if param.type == ParamType.CHOICE and param.choices:
        return click.Choice(param.choices, case_sensitive=False)
    return CLICK_TYPE_MAP.get(param.type, click.STRING)


def param_to_json_schema(param: "ParamSpec") -> Dict[str, Any]:
    """
    Convert ParamSpec to JSON Schema property definition.

    Args:
        param: The parameter specification

    Returns:
        JSON Schema property definition dict
    """
    schema = JSON_SCHEMA_TYPE_MAP.get(param.type, {"type": "string"}).copy()

    if param.help:
        schema["description"] = param.help
    if param.default is not None:
        schema["default"] = param.default
    if param.type == ParamType.CHOICE and param.choices:
        schema["enum"] = param.choices
    if param.type == ParamType.LIST and param.item_type:
        item_schema = JSON_SCHEMA_TYPE_MAP.get(param.item_type, {"type": "string"})
        schema["items"] = item_schema

    return schema
