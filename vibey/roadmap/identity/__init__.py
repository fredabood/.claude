"""
Identity System - ULID-based identifiers and slug mappings.

This module provides identity management for roadmap objects:
- ULID generation and validation (id_generator)
- .id file format for slug ↔ ULID bidirectional mapping (id_file)
"""

from vibey.roadmap.id_generator import (
    generate_id,
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
    generate_id_from_timestamp,
    extract_timestamp,
    extract_prefix,
    is_valid_id,
    is_ulid_format,
    compare_ids_by_timestamp,
)

from vibey.roadmap.identity.id_file import (
    IdMappingFile,
    load_id_mapping,
    get_ulid_for_slug,
    get_slug_for_ulid,
)

__all__ = [
    # ID generation
    "generate_id",
    "generate_track_id",
    "generate_sprint_id",
    "generate_task_id",
    "generate_id_from_timestamp",
    "extract_timestamp",
    "extract_prefix",
    "is_valid_id",
    "is_ulid_format",
    "compare_ids_by_timestamp",
    # ID file handling
    "IdMappingFile",
    "load_id_mapping",
    "get_ulid_for_slug",
    "get_slug_for_ulid",
]
