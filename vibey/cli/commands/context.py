"""
Context management commands.

Provides context creation, listing, archival, and search functionality.
"""

from typing import Optional

from vibey.cli.formatters import format_error


def context_init_cmd() -> int:
    """Initialize context directory structure."""
    from pathlib import Path

    from vibey.operations.context import ContextManager

    context_dir = Path.cwd() / ".vibey" / "context"

    if context_dir.exists():
        print(f"✅ Context directory already exists: {context_dir}")
        return 0

    try:
        manager = ContextManager(context_dir)
        manager.init_config()
        manager.update_index()

        print(f"✅ Context directory initialized: {context_dir}")
        print("   Created subdirectories:")
        print("   - sessions/current, sessions/history")
        print("   - tasks/current, tasks/completed")
        print("   - decisions/")
        print("   - sprints/")
        print("   - agents/")
        print("   - exports/")
        return 0
    except Exception as e:
        print(format_error(f"Failed to initialize context: {e}"))
        return 1


def context_list_cmd(
    context_type: str = "all",
    status: Optional[str] = None,
    limit: int = 20,
    output_format: str = "table",
) -> int:
    """List context items."""
    import json
    from pathlib import Path

    import yaml

    from vibey.operations.context import ContextLoader

    context_dir = Path.cwd() / ".vibey" / "context"
    if not context_dir.exists():
        print(format_error("Context directory not initialized. Run 'vibey context init' first."))
        return 1

    loader = ContextLoader(context_dir)

    results = []

    types_to_list = (
        ["session", "task", "decision", "sprint"]
        if context_type == "all"
        else [context_type]
    )

    for ctx_type in types_to_list:
        filters = {"status": status} if status else None

        if ctx_type == "session":
            items = loader.sessions.list(filters=filters, limit=limit)
            for item in items:
                results.append({
                    "type": "session",
                    "id": item.id,
                    "status": item.status,
                    "title": f"{item.type} session",
                    "info": item.started[:10] if item.started else "",
                })
        elif ctx_type == "task":
            items = loader.tasks.list(filters=filters, limit=limit)
            for item in items:
                results.append({
                    "type": "task",
                    "id": item.task_id,
                    "status": "active",
                    "title": item.title,
                    "info": item.sprint_id[:8] if item.sprint_id else "",
                })
        elif ctx_type == "decision":
            items = loader.decisions.list(filters=filters, limit=limit)
            for item in items:
                results.append({
                    "type": "decision",
                    "id": item.id,
                    "status": item.status,
                    "title": item.title,
                    "info": item.date,
                })
        elif ctx_type == "sprint":
            sprint_ids = loader.sprints._get_writer().list_current()
            for sprint_id in sprint_ids[:limit]:
                results.append({
                    "type": "sprint",
                    "id": sprint_id,
                    "status": "active",
                    "title": sprint_id,
                    "info": "",
                })

    if not results:
        print("No context items found.")
        return 0

    if output_format == "json":
        print(json.dumps(results, indent=2))
    elif output_format == "yaml":
        print(yaml.dump(results, default_flow_style=False))
    else:
        # Table format
        print(f"{'Type':<10} {'ID':<30} {'Status':<12} {'Title':<30}")
        print("-" * 82)
        for r in results[:limit]:
            title = r["title"][:28] + ".." if len(r["title"]) > 30 else r["title"]
            id_str = r["id"][:28] + ".." if len(r["id"]) > 30 else r["id"]
            print(f"{r['type']:<10} {id_str:<30} {r['status']:<12} {title:<30}")

    print(f"\nTotal: {len(results)} items")
    return 0


def context_show_cmd(
    context_id: str,
    context_type: Optional[str] = None,
    output_format: str = "yaml",
) -> int:
    """Show context details."""
    import json
    from dataclasses import asdict
    from pathlib import Path

    import yaml

    from vibey.operations.context import ContextLoader

    context_dir = Path.cwd() / ".vibey" / "context"
    if not context_dir.exists():
        print(format_error("Context directory not initialized. Run 'vibey context init' first."))
        return 1

    loader = ContextLoader(context_dir)

    # Auto-detect type if not specified
    types_to_try = (
        [context_type]
        if context_type
        else ["session", "task", "decision", "sprint"]
    )

    context = None
    found_type = None

    for ctx_type in types_to_try:
        result = loader.load(ctx_type, context_id)
        if result:
            context = result
            found_type = ctx_type
            break

    if context is None:
        print(format_error(f"Context not found: {context_id}"))
        return 1

    data = asdict(context)

    if output_format == "json":
        print(json.dumps(data, indent=2, default=str))
    elif output_format == "yaml":
        print(yaml.dump(data, default_flow_style=False, sort_keys=False))
    else:
        # Text format
        print(f"📋 Context: {context_id}")
        print(f"   Type: {found_type}")
        print("=" * 60)
        for k, v in data.items():
            if v:
                print(f"   {k}: {v}")

    return 0


def context_archive_cmd(context_id: str, context_type: Optional[str] = None) -> int:
    """Archive context to history."""
    from pathlib import Path

    from vibey.operations.context import ContextManager

    if not context_type:
        print(format_error("--type is required for archive command"))
        return 1

    context_dir = Path.cwd() / ".vibey" / "context"
    if not context_dir.exists():
        print(format_error("Context directory not initialized. Run 'vibey context init' first."))
        return 1

    manager = ContextManager(context_dir)

    try:
        if context_type == "session":
            result = manager.sessions.archive(context_id)
        elif context_type == "task":
            result = manager.tasks.archive(context_id)
        else:
            print(format_error(f"Cannot archive {context_type} context (only session, task)"))
            return 1

        if result:
            print(f"✅ Archived {context_type} context: {context_id}")
            print(f"   Moved to: {result}")
            return 0
        else:
            print(format_error(f"Context not found: {context_id}"))
            return 1
    except Exception as e:
        print(format_error(f"Failed to archive: {e}"))
        return 1


def context_clean_cmd(
    context_type: str = "all",
    older_than_days: int = 90,
    dry_run: bool = False,
) -> int:
    """Clean old archived context."""
    import os
    import time
    from pathlib import Path

    context_dir = Path.cwd() / ".vibey" / "context"
    if not context_dir.exists():
        print(format_error("Context directory not initialized."))
        return 1

    cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
    types_to_clean = (
        ["session", "task"]
        if context_type == "all"
        else [context_type]
    )

    files_to_remove = []

    for ctx_type in types_to_clean:
        if ctx_type == "session":
            history_dir = context_dir / "sessions" / "history"
        elif ctx_type == "task":
            history_dir = context_dir / "tasks" / "completed"
        else:
            continue

        if not history_dir.exists():
            continue

        # Search monthly buckets
        for bucket in history_dir.iterdir():
            if bucket.is_dir():
                for f in bucket.glob("*.yaml"):
                    if f.stat().st_mtime < cutoff_time:
                        files_to_remove.append(f)

    if not files_to_remove:
        print(f"No files older than {older_than_days} days found.")
        return 0

    print(f"Found {len(files_to_remove)} files older than {older_than_days} days:")
    for f in files_to_remove[:10]:
        print(f"   - {f.relative_to(context_dir)}")
    if len(files_to_remove) > 10:
        print(f"   ... and {len(files_to_remove) - 10} more")

    if dry_run:
        print("\n[dry-run] No files deleted.")
        return 0

    deleted = 0
    for f in files_to_remove:
        try:
            os.unlink(f)
            deleted += 1
        except Exception as e:
            print(f"   Failed to delete {f.name}: {e}")

    print(f"\n✅ Deleted {deleted} files.")
    return 0


def context_export_cmd(
    context_id: str,
    context_type: Optional[str] = None,
    output_path: Optional[str] = None,
) -> int:
    """Export context to file."""
    import json
    from dataclasses import asdict
    from pathlib import Path

    import yaml

    from vibey.operations.context import ContextLoader

    context_dir = Path.cwd() / ".vibey" / "context"
    if not context_dir.exists():
        print(format_error("Context directory not initialized."))
        return 1

    loader = ContextLoader(context_dir)

    # Find context
    types_to_try = (
        [context_type]
        if context_type
        else ["session", "task", "decision", "sprint"]
    )

    context = None
    found_type = None

    for ctx_type in types_to_try:
        result = loader.load(ctx_type, context_id)
        if result:
            context = result
            found_type = ctx_type
            break

    if context is None:
        print(format_error(f"Context not found: {context_id}"))
        return 1

    # Determine output path
    if output_path is None:
        output_path = f"{context_id}-{found_type}.yaml"

    output_file = Path(output_path)
    data = asdict(context)

    try:
        if output_file.suffix == ".json":
            content = json.dumps(data, indent=2, default=str)
        else:
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)

        with open(output_file, "w") as f:
            f.write(content)

        print(f"✅ Exported {found_type} context to: {output_file}")
        return 0
    except Exception as e:
        print(format_error(f"Failed to export: {e}"))
        return 1


def context_search_cmd(
    query: str,
    context_type: str = "all",
    limit: int = 20,
) -> int:
    """Search context by content."""
    from pathlib import Path

    from vibey.operations.context import ContextLoader

    context_dir = Path.cwd() / ".vibey" / "context"
    if not context_dir.exists():
        print(format_error("Context directory not initialized."))
        return 1

    loader = ContextLoader(context_dir)
    query_lower = query.lower()

    results = []

    types_to_search = (
        ["session", "task", "decision", "sprint"]
        if context_type == "all"
        else [context_type]
    )

    for ctx_type in types_to_search:
        if ctx_type == "session":
            items = loader.sessions.list(limit=100)
            for item in items:
                if (
                    query_lower in item.id.lower()
                    or query_lower in item.type.lower()
                    or any(query_lower in g.lower() for g in item.goals)
                    or (item.summary and query_lower in item.summary.lower())
                ):
                    results.append({
                        "type": "session",
                        "id": item.id,
                        "match": item.type,
                    })

        elif ctx_type == "task":
            items = loader.tasks.list(limit=100)
            for item in items:
                if (
                    query_lower in item.task_id.lower()
                    or query_lower in item.title.lower()
                    or query_lower in item.description.lower()
                    or (item.notes and query_lower in item.notes.lower())
                ):
                    results.append({
                        "type": "task",
                        "id": item.task_id,
                        "match": item.title,
                    })

        elif ctx_type == "decision":
            items = loader.decisions.list(limit=100)
            for item in items:
                if (
                    query_lower in item.id.lower()
                    or query_lower in item.title.lower()
                    or query_lower in item.context.lower()
                    or query_lower in item.decision.lower()
                ):
                    results.append({
                        "type": "decision",
                        "id": item.id,
                        "match": item.title,
                    })

        elif ctx_type == "sprint":
            sprint_ids = loader.sprints._get_writer().list_current()
            for sprint_id in sprint_ids:
                if query_lower in sprint_id.lower():
                    results.append({
                        "type": "sprint",
                        "id": sprint_id,
                        "match": sprint_id,
                    })

    if not results:
        print(f"No results found for: '{query}'")
        return 0

    print(f"🔍 Search results for '{query}':")
    print("-" * 60)
    for r in results[:limit]:
        print(f"   [{r['type']}] {r['id']}: {r['match']}")

    print(f"\nFound {len(results)} matches")
    return 0


def context_freshness_cmd(
    ticket_id: str,
    fresh_hours: int = 24,
    stale_hours: int = 72,
    output_format: str = "text",
) -> int:
    """Check freshness of context files for a ticket.

    Args:
        ticket_id: ULID of the ticket to check
        fresh_hours: Hours within which context is considered fresh
        stale_hours: Hours within which context is considered stale
        output_format: Output format (text, json, yaml)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import json
    from pathlib import Path

    import yaml

    from vibey.operations.context.freshness import (
        FreshnessConfig,
        check_context_freshness,
        format_freshness_report,
        get_overall_freshness,
    )

    # Validate ticket_id format (26-character ULID)
    if len(ticket_id) != 26:
        print(format_error(f"Invalid ticket ID: {ticket_id}. Expected 26-character ULID."))
        return 1

    # Check for valid ULID characters
    valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZabcdefghjkmnpqrstvwxyz")
    if not all(c in valid_chars for c in ticket_id):
        print(format_error(f"Invalid ticket ID: {ticket_id}. Contains invalid characters."))
        return 1

    roadmap_dir = Path.cwd() / ".vibey" / "roadmap"
    if not roadmap_dir.exists():
        print(format_error("Roadmap directory not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        config = FreshnessConfig(fresh_hours=fresh_hours, stale_hours=stale_hours)
        results = check_context_freshness(ticket_id, roadmap_dir, config)

        if output_format == "json":
            # Convert to JSON-serializable format
            json_results = {}
            for ctx_type, info in results.items():
                json_results[ctx_type] = {
                    "level": info.level.value,
                    "last_modified": info.last_modified.isoformat() if info.last_modified else None,
                    "age_hours": info.age_hours,
                    "message": info.message,
                }
            output = {
                "ticket_id": ticket_id,
                "overall": get_overall_freshness(results).value,
                "contexts": json_results,
            }
            print(json.dumps(output, indent=2))

        elif output_format == "yaml":
            # Convert to YAML-serializable format
            yaml_results = {}
            for ctx_type, info in results.items():
                yaml_results[ctx_type] = {
                    "level": info.level.value,
                    "last_modified": info.last_modified.isoformat() if info.last_modified else None,
                    "age_hours": round(info.age_hours, 2) if info.age_hours else None,
                    "message": info.message,
                }
            output = {
                "ticket_id": ticket_id,
                "overall": get_overall_freshness(results).value,
                "contexts": yaml_results,
            }
            print(yaml.dump(output, default_flow_style=False, sort_keys=False))

        else:
            # Text format
            print(format_freshness_report(ticket_id, results))

        return 0

    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to check context freshness: {e}"))
        return 1


def context_budget_cmd(
    ticket_id: Optional[str] = None,
    max_tokens: int = 100000,
    show_artifacts: bool = False,
    output_format: str = "text",
) -> int:
    """Show token budget status for context loading.

    Displays current token usage and remaining budget for context loading.
    Can show budget for a specific ticket or the default configuration.

    Args:
        ticket_id: Optional ticket ID to show budget for
        max_tokens: Maximum token budget (default 100000)
        show_artifacts: Show individual artifact token counts
        output_format: Output format (text, json, yaml)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import json
    from pathlib import Path

    import yaml

    from vibey.operations.context import (
        TokenBudget,
        TokenUsageTracker,
        format_budget_status,
        check_budget,
        estimate_file_tokens,
    )

    # Create budget configuration
    budget = TokenBudget(max_tokens=max_tokens)

    # Create usage tracker
    usage = TokenUsageTracker()

    # If ticket_id provided, try to load actual context data
    if ticket_id:
        context_dir = Path.cwd() / ".vibey" / "roadmap" / "context"

        # Check for plan context
        plan_dir = context_dir / "plans" / ticket_id
        if plan_dir.exists():
            plan_file = plan_dir / "plan.yaml"
            if plan_file.exists():
                usage.plan_context = estimate_file_tokens(plan_file)

            # Count artifact files in plan directory
            for artifact_file in plan_dir.glob("*.md"):
                tokens = estimate_file_tokens(artifact_file)
                usage.add_artifact(artifact_file.name, tokens)

        # Check for runtime context
        runtime_file = context_dir / "runtime" / f"{ticket_id}.yaml"
        if runtime_file.exists():
            usage.runtime_context = estimate_file_tokens(runtime_file)

    # Generate output based on format
    if output_format == "json":
        result = check_budget(usage, budget)
        data = {
            "budget": {
                "max_tokens": budget.max_tokens,
                "reserved_tokens": budget.reserved_tokens,
                "available_tokens": budget.available_tokens,
                "warning_threshold": budget.warning_threshold,
            },
            "usage": usage.to_dict(),
            "status": {
                "within_budget": result.within_budget,
                "remaining_tokens": result.remaining_tokens,
                "usage_percent": result.usage_percent,
                "warning": result.warning,
                "message": result.message,
            },
        }
        if show_artifacts and usage.artifact_breakdown:
            data["artifacts"] = usage.artifact_breakdown
        print(json.dumps(data, indent=2))

    elif output_format == "yaml":
        result = check_budget(usage, budget)
        data = {
            "budget": {
                "max_tokens": budget.max_tokens,
                "reserved_tokens": budget.reserved_tokens,
                "available_tokens": budget.available_tokens,
                "warning_threshold": budget.warning_threshold,
            },
            "usage": usage.to_dict(),
            "status": {
                "within_budget": result.within_budget,
                "remaining_tokens": result.remaining_tokens,
                "usage_percent": round(result.usage_percent, 4),
                "warning": result.warning,
                "message": result.message,
            },
        }
        if show_artifacts and usage.artifact_breakdown:
            data["artifacts"] = usage.artifact_breakdown
        print(yaml.dump(data, default_flow_style=False, sort_keys=False))

    else:
        # Text format
        output = format_budget_status(usage, budget)
        print(output)

        if ticket_id:
            print(f"\nContext for ticket: {ticket_id}")

    return 0
