"""
Context Management Tools.

MCP tools for managing ticket-artifact-commit relationships
(Triangle Model - Context System V2).

These tools enable AI assistants to:
- Associate artifacts with tickets
- Query artifact and commit relationships
- Log runtime file activity during work

Task: 01KCMGXG7BMKQNSFY2HS4G14XK
Sprint: Sprint 2 - Context Implementation
Track: Context System V2
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.errors import VibeyMCPError


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================


def get_context_tools() -> List[Dict[str, Any]]:
    """
    Get context management tool definitions.

    Returns:
        List of tool definition dicts following MCP spec
    """
    return [
        {
            "name": "vibey_associate_artifact",
            "title": "Associate Artifact",
            "description": (
                "Associate an artifact with a ticket. "
                "Use to link code files, documents, or other artifacts "
                "to the ticket being worked on."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID (ULID, e.g., '01KCMGXG7BMKQNSFY2HS4G14XK')"
                    },
                    "artifact_id_or_path": {
                        "type": "string",
                        "description": (
                            "Either artifact ULID or file path relative to repo root. "
                            "If a path is provided, it will be resolved to an artifact."
                        )
                    },
                    "source": {
                        "type": "string",
                        "description": (
                            "Association source: "
                            "plan_reference | runtime_tracking | commit_bootstrap | manual"
                        ),
                        "enum": [
                            "plan_reference",
                            "runtime_tracking",
                            "commit_bootstrap",
                            "manual"
                        ],
                        "default": "runtime_tracking"
                    }
                },
                "required": ["ticket_id", "artifact_id_or_path"]
            }
        },
        {
            "name": "vibey_get_ticket_artifacts",
            "title": "Get Ticket Artifacts",
            "description": (
                "Get all artifacts associated with a ticket. "
                "Shows files, documents, and other artifacts linked to the ticket."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID (ULID)"
                    }
                },
                "required": ["ticket_id"]
            }
        },
        {
            "name": "vibey_get_ticket_commits",
            "title": "Get Ticket Commits",
            "description": (
                "Get all commits linked to a ticket. "
                "Shows commits that reference or complete the ticket."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID (ULID)"
                    }
                },
                "required": ["ticket_id"]
            }
        },
        {
            "name": "vibey_get_artifact_history",
            "title": "Get Artifact History",
            "description": (
                "Get commit history for an artifact. "
                "Shows all commits that have modified this artifact."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "Artifact ID (ULID)"
                    }
                },
                "required": ["artifact_id"]
            }
        },
        {
            "name": "vibey_log_runtime_file",
            "title": "Log Runtime File",
            "description": (
                "Log a file as being actively worked on for a ticket. "
                "Use to track files touched during the current session."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID (ULID)"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "File path relative to repo root"
                    }
                },
                "required": ["ticket_id", "file_path"]
            }
        }
    ]


# =============================================================================
# TOOL HANDLERS
# =============================================================================


async def handle_context_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    root_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Handle context tool invocation.

    Routes to appropriate handler based on tool name.

    Args:
        tool_name: Name of tool being invoked
        arguments: Tool input arguments
        root_dir: Root directory for operations (defaults to cwd)

    Returns:
        MCP tool response dict with content and isError flag
    """
    if root_dir is None:
        root_dir = Path.cwd()

    try:
        if tool_name == "vibey_associate_artifact":
            return await handle_associate_artifact(arguments, root_dir)
        elif tool_name == "vibey_get_ticket_artifacts":
            return await handle_get_ticket_artifacts(arguments, root_dir)
        elif tool_name == "vibey_get_ticket_commits":
            return await handle_get_ticket_commits(arguments, root_dir)
        elif tool_name == "vibey_get_artifact_history":
            return await handle_get_artifact_history(arguments, root_dir)
        elif tool_name == "vibey_log_runtime_file":
            return await handle_log_runtime_file(arguments, root_dir)
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown context tool: {tool_name}"
                    }
                ],
                "isError": True
            }
    except VibeyMCPError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {e.message}"
                }
            ],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unexpected error: {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_associate_artifact(
    arguments: Dict[str, Any],
    root_dir: Path
) -> Dict[str, Any]:
    """
    Handle vibey_associate_artifact tool invocation.

    Associates an artifact with a ticket, creating a TicketArtifactAssociation.

    Args:
        arguments: Tool arguments with ticket_id, artifact_id_or_path, source
        root_dir: Root directory for operations

    Returns:
        MCP tool response
    """
    ticket_id = arguments["ticket_id"]
    artifact_id_or_path = arguments["artifact_id_or_path"]
    source = arguments.get("source", "runtime_tracking")

    # Import operations
    from vibey.operations.roadmap.artifacts import (
        show_artifact,
        link_artifact_to_ticket,
        adopt_artifact,
    )
    from vibey.roadmap.models.ticket import ArtifactType

    # Determine if this is an artifact ID or file path
    artifact_id = None

    # Check if it looks like a ULID (26 uppercase alphanumeric chars)
    if len(artifact_id_or_path) == 26 and artifact_id_or_path.isalnum():
        # Try to find existing artifact
        artifact = show_artifact(artifact_id_or_path, root_dir)
        if artifact:
            artifact_id = artifact_id_or_path
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Artifact not found: {artifact_id_or_path}"
                    }
                ],
                "isError": True
            }
    else:
        # It's a file path - try to find or adopt as artifact
        file_path = root_dir / artifact_id_or_path
        if not file_path.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"File not found: {artifact_id_or_path}"
                    }
                ],
                "isError": True
            }

        # Try to find existing artifact for this path
        from vibey.operations.roadmap.artifacts import list_artifacts
        existing_artifacts = list_artifacts(root_dir)
        for art in existing_artifacts:
            if artifact_id_or_path in art.paths:
                artifact_id = art.id
                break

        # If not found, adopt the file as an artifact
        if artifact_id is None:
            # Determine artifact type from file extension
            ext = file_path.suffix.lower()
            if ext in ['.py', '.js', '.ts', '.go', '.rs', '.java', '.c', '.cpp', '.h']:
                artifact_type = ArtifactType.SOURCE_CODE
            elif ext in ['.md', '.txt', '.rst', '.adoc']:
                artifact_type = ArtifactType.DOCUMENTATION
            elif ext in ['.yaml', '.yml', '.json', '.toml']:
                artifact_type = ArtifactType.CONFIGURATION
            elif ext in ['.sql']:
                artifact_type = ArtifactType.DATABASE
            else:
                artifact_type = ArtifactType.SOURCE_CODE  # Default

            try:
                new_artifact = adopt_artifact(
                    artifact_id_or_path,
                    artifact_type,
                    root_dir,
                    name=file_path.stem
                )
                artifact_id = new_artifact.id
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to adopt file as artifact: {str(e)}"
                        }
                    ],
                    "isError": True
                }

    # Link artifact to ticket
    success = link_artifact_to_ticket(artifact_id, ticket_id, root_dir)

    if success:
        # Also try to save the association to the relationship tables
        # (if they exist - gracefully degrade if not)
        try:
            _save_ticket_artifact_association(
                ticket_id=ticket_id,
                artifact_id=artifact_id,
                source=source,
                root_dir=root_dir
            )
        except Exception:
            pass  # Graceful degradation if tables don't exist yet

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Associated artifact with ticket\n\n"
                        f"**Ticket:** {ticket_id}\n"
                        f"**Artifact:** {artifact_id}\n"
                        f"**Source:** {source}"
                    )
                }
            ],
            "isError": False
        }
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Failed to associate artifact {artifact_id} with ticket {ticket_id}"
                }
            ],
            "isError": True
        }


async def handle_get_ticket_artifacts(
    arguments: Dict[str, Any],
    root_dir: Path
) -> Dict[str, Any]:
    """
    Handle vibey_get_ticket_artifacts tool invocation.

    Gets all artifacts associated with a ticket.

    Args:
        arguments: Tool arguments with ticket_id
        root_dir: Root directory for operations

    Returns:
        MCP tool response
    """
    ticket_id = arguments["ticket_id"]

    # Import operations
    from vibey.operations.roadmap.artifacts import list_artifacts, show_artifact

    # Get all artifacts and filter by ticket
    all_artifacts = list_artifacts(root_dir)
    ticket_artifacts = [
        art for art in all_artifacts
        if ticket_id in art.referenced_by
    ]

    if not ticket_artifacts:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"No artifacts found for ticket: {ticket_id}"
                }
            ],
            "isError": False
        }

    # Format response
    lines = [f"## Artifacts for Ticket {ticket_id}", "", f"Found {len(ticket_artifacts)} artifacts:", ""]

    for art in ticket_artifacts:
        lines.append(f"### {art.name}")
        lines.append(f"- **ID:** {art.id}")
        lines.append(f"- **Type:** {art.artifact_type.value}")
        if art.paths:
            lines.append(f"- **Paths:** {', '.join(art.paths)}")
        if art.artifact_subtype:
            lines.append(f"- **Subtype:** {art.artifact_subtype}")
        lines.append("")

    return {
        "content": [
            {
                "type": "text",
                "text": "\n".join(lines)
            }
        ],
        "isError": False
    }


async def handle_get_ticket_commits(
    arguments: Dict[str, Any],
    root_dir: Path
) -> Dict[str, Any]:
    """
    Handle vibey_get_ticket_commits tool invocation.

    Gets all commits linked to a ticket.

    Args:
        arguments: Tool arguments with ticket_id
        root_dir: Root directory for operations

    Returns:
        MCP tool response
    """
    ticket_id = arguments["ticket_id"]

    # Try to query from relationship tables (if available)
    commits = _query_ticket_commits(ticket_id, root_dir)

    if commits is None:
        # Fallback: use git log to find commits mentioning the ticket
        commits = await _find_commits_by_git_log(ticket_id, root_dir)

    if not commits:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"No commits found for ticket: {ticket_id}"
                }
            ],
            "isError": False
        }

    # Format response
    lines = [f"## Commits for Ticket {ticket_id}", "", f"Found {len(commits)} commits:", ""]

    for commit in commits:
        sha = commit.get("sha", "unknown")[:8]
        ref_type = commit.get("reference_type", "unknown")
        confidence = commit.get("confidence", 1.0)
        message = commit.get("message", "")[:50]

        lines.append(f"- `{sha}` ({ref_type}, confidence: {confidence:.0%})")
        if message:
            lines.append(f"  {message}")

    return {
        "content": [
            {
                "type": "text",
                "text": "\n".join(lines)
            }
        ],
        "isError": False
    }


async def handle_get_artifact_history(
    arguments: Dict[str, Any],
    root_dir: Path
) -> Dict[str, Any]:
    """
    Handle vibey_get_artifact_history tool invocation.

    Gets commit history for an artifact.

    Args:
        arguments: Tool arguments with artifact_id
        root_dir: Root directory for operations

    Returns:
        MCP tool response
    """
    artifact_id = arguments["artifact_id"]

    # Import operations
    from vibey.operations.roadmap.artifacts import show_artifact

    # Get artifact to find its paths
    artifact = show_artifact(artifact_id, root_dir)
    if not artifact:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Artifact not found: {artifact_id}"
                }
            ],
            "isError": True
        }

    # Try to query from relationship tables (if available)
    changes = _query_artifact_changes(artifact_id, root_dir)

    if changes is None and artifact.paths:
        # Fallback: use git log on the artifact paths
        changes = await _find_changes_by_git_log(artifact.paths, root_dir)

    if not changes:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"No commit history found for artifact: {artifact_id}\n"
                        f"Paths: {', '.join(artifact.paths)}"
                    )
                }
            ],
            "isError": False
        }

    # Format response
    lines = [
        f"## Commit History for Artifact",
        f"**ID:** {artifact_id}",
        f"**Name:** {artifact.name}",
        f"**Paths:** {', '.join(artifact.paths)}",
        "",
        f"Found {len(changes)} changes:",
        ""
    ]

    for change in changes:
        sha = change.get("sha", "unknown")[:8]
        change_type = change.get("change_type", "modified")
        recorded_at = change.get("recorded_at", "")
        lines.append(f"- `{sha}` - {change_type} ({recorded_at})")

    return {
        "content": [
            {
                "type": "text",
                "text": "\n".join(lines)
            }
        ],
        "isError": False
    }


async def handle_log_runtime_file(
    arguments: Dict[str, Any],
    root_dir: Path
) -> Dict[str, Any]:
    """
    Handle vibey_log_runtime_file tool invocation.

    Logs a file as being actively worked on for a ticket.
    Creates an artifact association with source=runtime_tracking.

    Args:
        arguments: Tool arguments with ticket_id, file_path
        root_dir: Root directory for operations

    Returns:
        MCP tool response
    """
    ticket_id = arguments["ticket_id"]
    file_path = arguments["file_path"]

    # Verify file exists
    full_path = root_dir / file_path
    if not full_path.exists():
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"File not found: {file_path}"
                }
            ],
            "isError": True
        }

    # Try to load or create runtime context
    try:
        _log_file_to_runtime_context(ticket_id, file_path, root_dir)
    except Exception:
        pass  # Graceful degradation

    # Also associate as artifact (reuse associate_artifact logic)
    result = await handle_associate_artifact(
        {
            "ticket_id": ticket_id,
            "artifact_id_or_path": file_path,
            "source": "runtime_tracking"
        },
        root_dir
    )

    if result.get("isError"):
        return result

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Logged runtime file\n\n"
                    f"**Ticket:** {ticket_id}\n"
                    f"**File:** {file_path}\n"
                    f"**Status:** Tracked as runtime_tracking"
                )
            }
        ],
        "isError": False
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _save_ticket_artifact_association(
    ticket_id: str,
    artifact_id: str,
    source: str,
    root_dir: Path
) -> None:
    """
    Save a TicketArtifactAssociation to the SQLite database (if available).

    This creates records in the ticket_artifact_associations table
    as defined by the Context System V2 schema.
    """
    # Try to use the relationship model
    try:
        from vibey.roadmap.models.relationships import (
            TicketArtifactAssociation,
            AssociationSource,
        )

        # Create association model
        assoc = TicketArtifactAssociation.create(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            source=AssociationSource(source),
            added_by="mcp_context_tool"
        )

        # TODO: Save to database when schema is implemented
        # For now, the artifact registry link is sufficient
        pass

    except ImportError:
        # Models not available yet
        pass


def _query_ticket_commits(
    ticket_id: str,
    root_dir: Path
) -> Optional[List[Dict[str, Any]]]:
    """
    Query commits linked to a ticket from the database.

    Returns None if the relationship tables don't exist yet.
    """
    try:
        # TODO: Implement when SQLite schema is created
        # For now, return None to trigger fallback
        return None
    except Exception:
        return None


def _query_artifact_changes(
    artifact_id: str,
    root_dir: Path
) -> Optional[List[Dict[str, Any]]]:
    """
    Query commit changes for an artifact from the database.

    Returns None if the relationship tables don't exist yet.
    """
    try:
        # TODO: Implement when SQLite schema is created
        # For now, return None to trigger fallback
        return None
    except Exception:
        return None


async def _find_commits_by_git_log(
    ticket_id: str,
    root_dir: Path
) -> List[Dict[str, Any]]:
    """
    Find commits mentioning a ticket by searching git log.

    Searches for both Task: and Completes: markers.
    """
    import subprocess

    commits = []

    try:
        # Search git log for commits mentioning the ticket ID
        result = subprocess.run(
            [
                "git", "log",
                "--all",
                f"--grep={ticket_id}",
                "--format=%H|%s",
                "-n", "50"  # Limit results
            ],
            cwd=root_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    sha, message = line.split("|", 1)

                    # Determine reference type
                    if f"Completes: {ticket_id}" in message or f"Completes:{ticket_id}" in message:
                        ref_type = "completion_claim"
                    elif f"Task: {ticket_id}" in message or f"Task:{ticket_id}" in message:
                        ref_type = "task_reference"
                    else:
                        ref_type = "mention"

                    commits.append({
                        "sha": sha,
                        "message": message,
                        "reference_type": ref_type,
                        "confidence": 1.0
                    })
    except Exception:
        pass

    return commits


async def _find_changes_by_git_log(
    paths: List[str],
    root_dir: Path
) -> List[Dict[str, Any]]:
    """
    Find commits that changed specific files using git log.
    """
    import subprocess

    changes = []

    try:
        for path in paths:
            result = subprocess.run(
                [
                    "git", "log",
                    "--format=%H|%aI|%s",
                    "-n", "20",  # Limit results per file
                    "--",
                    path
                ],
                cwd=root_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|", 2)
                        if len(parts) >= 2:
                            sha = parts[0]
                            recorded_at = parts[1]

                            # Check if we already have this commit
                            if not any(c["sha"] == sha for c in changes):
                                changes.append({
                                    "sha": sha,
                                    "recorded_at": recorded_at,
                                    "change_type": "modified",
                                    "path": path
                                })
    except Exception:
        pass

    # Sort by date (most recent first)
    changes.sort(key=lambda x: x.get("recorded_at", ""), reverse=True)
    return changes


def _log_file_to_runtime_context(
    ticket_id: str,
    file_path: str,
    root_dir: Path
) -> None:
    """
    Log a file to the runtime context for a ticket.

    Updates the runtime context YAML file to include this file
    in the active_files list.
    """
    import yaml

    runtime_dir = root_dir / ".vibey" / "roadmap" / "context" / "runtime"
    runtime_file = runtime_dir / f"{ticket_id}.yaml"

    # Ensure directory exists
    runtime_dir.mkdir(parents=True, exist_ok=True)

    # Load existing context or create new
    context_data = {}
    if runtime_file.exists():
        try:
            with open(runtime_file) as f:
                context_data = yaml.safe_load(f) or {}
        except Exception:
            context_data = {}

    # Initialize active_files if not present
    if "active_files" not in context_data:
        context_data["active_files"] = []

    # Add file if not already present
    existing_paths = [f.get("path") for f in context_data["active_files"]]
    if file_path not in existing_paths:
        context_data["active_files"].append({
            "path": file_path,
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "status": "opened"
        })

    # Update timestamp
    context_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    context_data["ticket_id"] = ticket_id

    # Save
    with open(runtime_file, "w") as f:
        yaml.dump(context_data, f, default_flow_style=False, sort_keys=False)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "get_context_tools",
    "handle_context_tool",
]
