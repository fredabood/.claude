"""
YAML synchronization for roadmap database.

This subpackage provides bidirectional synchronization between
the SQLite database and YAML files:

- dump: Export database state to YAML files
- rebuild: Import YAML files into database
- checksums: Track file changes for conflict detection
- hooks: Git hook integration

Synchronization will be implemented in sprint-3.
"""

__all__: list[str] = []
