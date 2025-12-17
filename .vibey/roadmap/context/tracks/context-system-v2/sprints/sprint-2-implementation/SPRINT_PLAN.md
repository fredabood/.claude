# Sprint 2: Context Implementation

## Overview
- **Track:** Context System V2
- **Sprint ID:** 01KCMTY669JGT3WYPZB78ATWBT
- **Tasks:** 9
- **Focus:** Implement context management features, MCP tools, and documentation

## Success Criteria
- [ ] Context integrated into ticket data structure
- [ ] Timestamp-based git commit linking working
- [ ] Post-mortem generation functional
- [ ] MCP tools for context management
- [ ] Token budget enforcement implemented
- [ ] Complete user documentation

---

## Task 1: Integrate Context into Ticket-Level Data Structure
**ID:** `01KCMNCZS970T6MSXDY2CZA2YH`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Context management is currently separate from tickets. Needs to become first-class ticket attribute.

### Implementation Steps
1. Extend ticket model:
   ```python
   # vibey/roadmap/models/ticket.py

   from typing import Optional
   from .context import PlanContext, RuntimeContext, PostMortemContext

   class Ticket(BaseModel):
       # ... existing fields

       # Context (new fields)
       plan_context: Optional[PlanContext] = None
       runtime_context: Optional[RuntimeContext] = None
       post_mortem: Optional[PostMortemContext] = None

       def has_plan(self) -> bool:
           """Check if ticket has planning context."""
           return self.plan_context is not None

       def is_contextually_complete(self) -> bool:
           """Check if ticket has post-mortem context."""
           return self.post_mortem is not None
   ```

2. Create context models:
   ```python
   # vibey/roadmap/models/context.py

   from pydantic import BaseModel
   from datetime import datetime
   from typing import List, Optional

   class PlanContext(BaseModel):
       """Pre-work planning context."""
       goals: List[str] = []
       approach: str = ""
       references: List[str] = []
       constraints: List[str] = []
       success_criteria: List[str] = []
       created_at: datetime
       approved: bool = False

   class RuntimeContext(BaseModel):
       """Active execution context."""
       active_files: List[str] = []
       decisions: List[str] = []
       discoveries: List[str] = []
       blockers: List[str] = []
       token_usage: int = 0
       last_updated: datetime

   class PostMortemContext(BaseModel):
       """Completion summary."""
       summary: str
       files_changed: List[str] = []
       key_decisions: List[str] = []
       lessons_learned: List[str] = []
       follow_up_items: List[str] = []
       completed_at: datetime
       duration_hours: float = 0.0
   ```

3. Update YAML serialization:
   ```python
   # vibey/roadmap/serialization/yaml_loader.py

   def load_task(path: Path) -> Task:
       data = yaml.safe_load(path.read_text())
       task_data = data['task']

       # Load inline context if present
       if 'plan_context' in task_data:
           task_data['plan_context'] = PlanContext(**task_data['plan_context'])
       if 'runtime_context' in task_data:
           task_data['runtime_context'] = RuntimeContext(**task_data['runtime_context'])
       if 'post_mortem' in task_data:
           task_data['post_mortem'] = PostMortemContext(**task_data['post_mortem'])

       return Task(**task_data)
   ```

4. Add context operations:
   ```python
   # vibey/operations/roadmap/context_ops.py

   def set_plan_context(ticket_id: str, context: PlanContext) -> None:
       """Set planning context for ticket."""
       ticket = load_ticket(ticket_id)
       ticket.plan_context = context
       save_ticket(ticket)

   def update_runtime_context(ticket_id: str, **updates) -> None:
       """Update runtime context during work."""
       ticket = load_ticket(ticket_id)
       if ticket.runtime_context is None:
           ticket.runtime_context = RuntimeContext(last_updated=datetime.now())
       for key, value in updates.items():
           setattr(ticket.runtime_context, key, value)
       ticket.runtime_context.last_updated = datetime.now()
       save_ticket(ticket)

   def save_post_mortem(ticket_id: str, summary: str, **details) -> None:
       """Save post-mortem for completed ticket."""
       ticket = load_ticket(ticket_id)
       ticket.post_mortem = PostMortemContext(
           summary=summary,
           completed_at=datetime.now(),
           **details
       )
       save_ticket(ticket)
   ```

### Acceptance Criteria
- [ ] Context fields added to ticket model
- [ ] YAML serialization handles context
- [ ] Context operations implemented
- [ ] Tests for context CRUD

---

## Task 2: Implement Timestamp-Based Context Linking with Git Commits
**ID:** `01KCMNDFWS0C2N2FJJBZRR3FC8`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Need automatic association between context and tickets via timestamp + file matching.

### Implementation Steps
1. Create commit link model:
   ```python
   # vibey/roadmap/models/commit_link.py

   class CommitLink(BaseModel):
       """Links git commit to ticket."""
       commit_sha: str
       timestamp: datetime
       files_changed: List[str]
       message: str
       link_type: str  # 'timestamp' | 'file_match' | 'manual'
       confidence: float  # 0.0 - 1.0
   ```

2. Implement auto-linking algorithm:
   ```python
   # vibey/operations/git/commit_linker.py

   import subprocess
   from datetime import datetime
   from typing import List

   def get_commits_in_range(start: datetime, end: datetime) -> List[dict]:
       """Get git commits between timestamps."""
       result = subprocess.run([
           'git', 'log',
           f'--since={start.isoformat()}',
           f'--until={end.isoformat()}',
           '--format=%H|%ai|%s',
           '--name-only'
       ], capture_output=True, text=True)

       commits = []
       for entry in result.stdout.strip().split('\n\n'):
           if not entry:
               continue
           lines = entry.split('\n')
           header = lines[0].split('|')
           commits.append({
               'sha': header[0],
               'timestamp': datetime.fromisoformat(header[1].replace(' ', 'T')),
               'message': header[2],
               'files': lines[1:] if len(lines) > 1 else []
           })
       return commits

   def link_commits_to_ticket(ticket: Ticket) -> List[CommitLink]:
       """Auto-link commits to ticket based on timestamp and files."""
       if not ticket.started:
           return []

       end_time = ticket.completed or datetime.now()
       commits = get_commits_in_range(ticket.started, end_time)

       links = []
       for commit in commits:
           # Check file overlap if ticket has known files
           if ticket.known_files:
               overlap = set(commit['files']) & set(ticket.known_files)
               if overlap:
                   links.append(CommitLink(
                       commit_sha=commit['sha'],
                       timestamp=commit['timestamp'],
                       files_changed=commit['files'],
                       message=commit['message'],
                       link_type='file_match',
                       confidence=len(overlap) / len(commit['files'])
                   ))
           else:
               # Timestamp-only linking (lower confidence)
               links.append(CommitLink(
                   commit_sha=commit['sha'],
                   timestamp=commit['timestamp'],
                   files_changed=commit['files'],
                   message=commit['message'],
                   link_type='timestamp',
                   confidence=0.5
               ))

       return links
   ```

3. Add CLI command for commit linking:
   ```python
   @ticket.command('link-commits')
   @click.argument('ticket_id')
   @click.option('--auto/--manual', default=True)
   def link_commits(ticket_id, auto):
       """Link git commits to ticket."""
       ticket = ticket_ops.get_ticket(ticket_id)

       if auto:
           links = link_commits_to_ticket(ticket)
           for link in links:
               click.echo(f"Linked: {link.commit_sha[:8]} ({link.link_type}, {link.confidence:.0%})")
       else:
           # Manual linking
           sha = click.prompt("Commit SHA")
           ticket_ops.manual_link_commit(ticket_id, sha)
   ```

### Acceptance Criteria
- [ ] Commit linking algorithm works
- [ ] File overlap detection functional
- [ ] CLI command for linking
- [ ] Links persisted with ticket

---

## Task 3: Add Post-Mortem Generation for Completed Tasks
**ID:** `01KCMNEG4CXW4NK7W55VDMBXXM`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Need automatic or prompted post-mortem generation when tasks complete.

### Implementation Steps
1. Create post-mortem generator:
   ```python
   # vibey/operations/roadmap/post_mortem.py

   from datetime import datetime
   from typing import Optional

   def generate_post_mortem_prompt(ticket: Ticket) -> str:
       """Generate prompt for AI to create post-mortem."""
       return f"""
       Please provide a post-mortem summary for this completed task:

       Task: {ticket.title}
       Description: {ticket.description}
       Started: {ticket.started}
       Completed: {ticket.completed}

       Please summarize:
       1. What was accomplished
       2. Key decisions made
       3. Lessons learned
       4. Any follow-up items

       Format as structured JSON.
       """

   def create_post_mortem_from_commits(ticket: Ticket) -> PostMortemContext:
       """Create post-mortem from linked commits."""
       links = ticket.commit_links or []

       files_changed = set()
       for link in links:
           files_changed.update(link.files_changed)

       messages = [link.message for link in links]

       return PostMortemContext(
           summary=f"Completed {ticket.title}. {len(links)} commits, {len(files_changed)} files changed.",
           files_changed=list(files_changed),
           key_decisions=messages[:5],  # First 5 commit messages as decisions
           lessons_learned=[],
           follow_up_items=[],
           completed_at=ticket.completed or datetime.now(),
           duration_hours=calculate_duration(ticket.started, ticket.completed)
       )
   ```

2. Hook into task completion:
   ```python
   # vibey/operations/roadmap/update.py

   def complete_task(task_id: str, generate_postmortem: bool = True) -> Task:
       """Mark task as complete with optional post-mortem."""
       task = load_task(task_id)
       task.status = Status.COMPLETED
       task.completed = datetime.now()

       if generate_postmortem:
           # Auto-generate from commits
           task.post_mortem = create_post_mortem_from_commits(task)

       save_task(task)
       return task
   ```

3. Add CLI options:
   ```python
   @ticket.command('complete')
   @click.argument('id')
   @click.option('--summary', help='Post-mortem summary')
   @click.option('--no-postmortem', is_flag=True, help='Skip post-mortem generation')
   def complete_ticket(id, summary, no_postmortem):
       """Complete ticket with optional post-mortem."""
       if not no_postmortem:
           if summary:
               ticket_ops.complete_with_summary(id, summary)
           else:
               # Auto-generate
               ticket_ops.complete_with_auto_postmortem(id)
       else:
           ticket_ops.complete(id)
   ```

### Acceptance Criteria
- [ ] Post-mortem auto-generation works
- [ ] Manual summary option available
- [ ] Hooks into completion workflow
- [ ] Files changed extracted from commits

---

## Task 4: Add Context Management MCP Tools
**ID:** `01KCMGXG7BMKQNSFY2HS4G14XK`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
AI assistants need MCP tools to manage their own context.

### Implementation Steps
1. Create context MCP tools:
   ```python
   # vibey/mcp/tools/context_tools.py

   @mcp_tool
   def context_get_plan(ticket_id: str) -> dict:
       """Get planning context for a ticket."""
       ticket = ticket_ops.get_ticket(ticket_id)
       if not ticket.plan_context:
           return {"error": "No planning context found"}
       return ticket.plan_context.model_dump()

   @mcp_tool
   def context_set_plan(
       ticket_id: str,
       goals: List[str],
       approach: str,
       references: List[str] = None,
       constraints: List[str] = None,
       success_criteria: List[str] = None
   ) -> dict:
       """Set planning context for a ticket."""
       context = PlanContext(
           goals=goals,
           approach=approach,
           references=references or [],
           constraints=constraints or [],
           success_criteria=success_criteria or [],
           created_at=datetime.now()
       )
       context_ops.set_plan_context(ticket_id, context)
       return {"status": "success", "ticket_id": ticket_id}

   @mcp_tool
   def context_update_runtime(
       ticket_id: str,
       active_files: List[str] = None,
       decisions: List[str] = None,
       discoveries: List[str] = None,
       blockers: List[str] = None
   ) -> dict:
       """Update runtime context during task execution."""
       updates = {}
       if active_files:
           updates['active_files'] = active_files
       if decisions:
           updates['decisions'] = decisions
       if discoveries:
           updates['discoveries'] = discoveries
       if blockers:
           updates['blockers'] = blockers

       context_ops.update_runtime_context(ticket_id, **updates)
       return {"status": "success", "ticket_id": ticket_id}

   @mcp_tool
   def context_get_runtime(ticket_id: str) -> dict:
       """Get current runtime context for a ticket."""
       ticket = ticket_ops.get_ticket(ticket_id)
       if not ticket.runtime_context:
           return {"error": "No runtime context found"}
       return ticket.runtime_context.model_dump()

   @mcp_tool
   def context_save_postmortem(
       ticket_id: str,
       summary: str,
       key_decisions: List[str] = None,
       lessons_learned: List[str] = None,
       follow_up_items: List[str] = None
   ) -> dict:
       """Save post-mortem context after task completion."""
       context_ops.save_post_mortem(
           ticket_id,
           summary=summary,
           key_decisions=key_decisions or [],
           lessons_learned=lessons_learned or [],
           follow_up_items=follow_up_items or []
       )
       return {"status": "success", "ticket_id": ticket_id}

   @mcp_tool
   def context_link_commits(ticket_id: str, auto: bool = True) -> dict:
       """Link git commits to ticket context."""
       if auto:
           links = commit_linker.link_commits_to_ticket(ticket_id)
           return {
               "status": "success",
               "links_created": len(links),
               "commits": [l.commit_sha[:8] for l in links]
           }
       else:
           return {"error": "Manual linking not supported via MCP"}
   ```

2. Register tools in MCP server:
   ```python
   # vibey/mcp/server.py

   from .tools.context_tools import (
       context_get_plan,
       context_set_plan,
       context_update_runtime,
       context_get_runtime,
       context_save_postmortem,
       context_link_commits,
   )

   CONTEXT_TOOLS = [
       context_get_plan,
       context_set_plan,
       context_update_runtime,
       context_get_runtime,
       context_save_postmortem,
       context_link_commits,
   ]
   ```

### Acceptance Criteria
- [ ] All 6 context MCP tools implemented
- [ ] Tools registered in MCP server
- [ ] AI can manage its own context
- [ ] Tests for each tool

---

## Task 5: Implement Token Budget Enforcement
**ID:** `01KCMGX8J70XCDJH51SYHVC6H4`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Context operations need explicit token budget parameters for model token limit management.

### Implementation Steps
1. Add token counting utility:
   ```python
   # vibey/common/tokens.py

   import tiktoken

   def count_tokens(text: str, model: str = "gpt-4") -> int:
       """Count tokens in text for given model."""
       try:
           encoding = tiktoken.encoding_for_model(model)
       except KeyError:
           encoding = tiktoken.get_encoding("cl100k_base")
       return len(encoding.encode(text))

   def estimate_context_tokens(context: dict) -> int:
       """Estimate tokens for context dictionary."""
       import json
       text = json.dumps(context, indent=2)
       return count_tokens(text)
   ```

2. Add budget enforcement to context operations:
   ```python
   # vibey/operations/roadmap/context_ops.py

   class TokenBudgetExceeded(Exception):
       """Raised when token budget would be exceeded."""
       pass

   def get_context_within_budget(
       ticket_id: str,
       token_budget: int = 4000,
       prioritize: List[str] = None
   ) -> dict:
       """Get context within token budget."""
       ticket = load_ticket(ticket_id)
       context = {}

       # Priority order: plan > runtime > post_mortem
       sections = prioritize or ['plan_context', 'runtime_context', 'post_mortem']

       total_tokens = 0
       for section in sections:
           section_data = getattr(ticket, section, None)
           if section_data:
               section_dict = section_data.model_dump()
               section_tokens = estimate_context_tokens(section_dict)

               if total_tokens + section_tokens <= token_budget:
                   context[section] = section_dict
                   total_tokens += section_tokens
               else:
                   # Truncate section to fit budget
                   remaining = token_budget - total_tokens
                   context[section] = truncate_to_tokens(section_dict, remaining)
                   break

       context['_meta'] = {
           'tokens_used': total_tokens,
           'budget': token_budget,
           'sections_included': list(context.keys())
       }
       return context

   def truncate_to_tokens(data: dict, max_tokens: int) -> dict:
       """Truncate dict content to fit token limit."""
       # Simplified: remove items until within budget
       result = dict(data)
       while estimate_context_tokens(result) > max_tokens:
           # Remove least important key
           if 'follow_up_items' in result:
               result.pop('follow_up_items')
           elif 'lessons_learned' in result:
               result.pop('lessons_learned')
           elif 'discoveries' in result:
               result.pop('discoveries')
           else:
               break
       return result
   ```

3. Add CLI option:
   ```python
   @context.command('get')
   @click.argument('ticket_id')
   @click.option('--budget', type=int, default=4000, help='Token budget')
   def get_context(ticket_id, budget):
       """Get context within token budget."""
       ctx = context_ops.get_context_within_budget(ticket_id, budget)
       click.echo(json.dumps(ctx, indent=2))
   ```

### Acceptance Criteria
- [ ] Token counting implemented
- [ ] Budget enforcement working
- [ ] Context truncation functional
- [ ] CLI supports budget parameter

---

## Task 6: Add Context Freshness Tracking
**ID:** `01KCMGXCCH84MG5BWK8MY8ZT83`
**Priority:** Medium | **Complexity:** Medium | **Type:** Development

### Problem
Need to track context age and prompt refresh for stale context.

### Implementation Steps
1. Add freshness metadata:
   ```python
   # Add to context models
   class RuntimeContext(BaseModel):
       # ... existing fields
       last_updated: datetime
       refresh_after: Optional[datetime] = None  # Suggested refresh time
   ```

2. Implement staleness detection:
   ```python
   # vibey/operations/roadmap/context_freshness.py

   from datetime import datetime, timedelta

   DEFAULT_FRESHNESS_HOURS = 24

   def is_context_stale(context: RuntimeContext, max_age_hours: int = DEFAULT_FRESHNESS_HOURS) -> bool:
       """Check if context is stale."""
       if not context or not context.last_updated:
           return True

       age = datetime.now() - context.last_updated
       return age > timedelta(hours=max_age_hours)

   def get_context_age(context: RuntimeContext) -> timedelta:
       """Get age of context."""
       if not context or not context.last_updated:
           return timedelta.max
       return datetime.now() - context.last_updated

   def suggest_refresh(ticket_id: str) -> Optional[str]:
       """Suggest context refresh if stale."""
       ticket = load_ticket(ticket_id)
       if not ticket.runtime_context:
           return "No runtime context - consider initializing"

       if is_context_stale(ticket.runtime_context):
           age = get_context_age(ticket.runtime_context)
           return f"Context is {age.days}d {age.seconds//3600}h old - consider refreshing"

       return None
   ```

3. Add MCP tool for freshness:
   ```python
   @mcp_tool
   def context_check_freshness(ticket_id: str) -> dict:
       """Check if context needs refresh."""
       ticket = ticket_ops.get_ticket(ticket_id)
       suggestion = suggest_refresh(ticket_id)

       return {
           "ticket_id": ticket_id,
           "is_stale": suggestion is not None,
           "suggestion": suggestion,
           "last_updated": ticket.runtime_context.last_updated.isoformat() if ticket.runtime_context else None
       }
   ```

### Acceptance Criteria
- [ ] Freshness tracking implemented
- [ ] Staleness detection working
- [ ] Refresh suggestions available
- [ ] MCP tool for freshness check

---

## Task 7: Test and Document Context CLI Commands
**ID:** `01KCMGX4QAG1SNWA7J7AVGH3NP`
**Priority:** Medium | **Complexity:** Medium | **Type:** Testing

### Problem
Context commands need testing and documentation.

### Implementation Steps
1. Test all context commands:
   ```python
   # tests/cli/test_context_commands.py

   def test_context_init(cli_runner, roadmap_env):
       result = cli_runner.invoke(['context', 'init', '--ticket', TEST_TICKET_ID])
       assert result.exit_code == 0

   def test_context_list(cli_runner, roadmap_env):
       result = cli_runner.invoke(['context', 'list'])
       assert result.exit_code == 0

   def test_context_show(cli_runner, roadmap_env, sample_context):
       result = cli_runner.invoke(['context', 'show', sample_context.ticket_id])
       assert result.exit_code == 0
       assert sample_context.ticket_id in result.output

   def test_context_export(cli_runner, roadmap_env, sample_context):
       result = cli_runner.invoke(['context', 'export', '--format', 'json'])
       assert result.exit_code == 0

   def test_context_sync(cli_runner, roadmap_env):
       result = cli_runner.invoke(['context', 'sync'])
       assert result.exit_code == 0

   def test_context_archive(cli_runner, roadmap_env, completed_ticket):
       result = cli_runner.invoke(['context', 'archive', completed_ticket.id])
       assert result.exit_code == 0

   def test_context_clean(cli_runner, roadmap_env):
       result = cli_runner.invoke(['context', 'clean', '--dry-run'])
       assert result.exit_code == 0
   ```

2. Document each command:
   ```markdown
   ## Context Commands

   ### context init
   Initialize context for a ticket.
   ```bash
   vibey context init --ticket <ticket_id>
   ```

   ### context list
   List all context entries.
   ```bash
   vibey context list [--stale] [--format json|table]
   ```

   ### context show
   Show context details.
   ```bash
   vibey context show <ticket_id> [--section plan|runtime|postmortem]
   ```

   ### context export
   Export context in various formats.
   ```bash
   vibey context export --format json|yaml|markdown [--budget 4000]
   ```
   ```

### Acceptance Criteria
- [ ] All commands tested
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Edge cases handled

---

## Task 8: Create Context Engineering User Guide
**ID:** `01KCMJPG8YZKCRSXQDDY7KMW0P`
**Priority:** Medium | **Complexity:** Medium | **Type:** Documentation

### Problem
Users need comprehensive guide for context system usage.

### Implementation Steps
Create `docs/guides/CONTEXT_USER_GUIDE.md`:

```markdown
# Context Engineering User Guide

## Introduction
The context system helps AI assistants maintain understanding
across sessions and task boundaries.

## Core Concepts

### Three-Phase Context Model
1. **Plan Context**: Preparation before work begins
2. **Runtime Context**: Active state during work
3. **Post-Mortem Context**: Summary after completion

### Context Lifecycle
```
Plan → Runtime → Post-Mortem
  │       │          │
  └───────┴──────────┴── Git commits
```

## Getting Started

### 1. Initialize Context for a Task
```bash
vibey context init --ticket 01KC2D0JK9JKQX...
```

### 2. Set Planning Context
```bash
vibey context plan set 01KC2D0JK9JK \
  --goals "Implement feature X" \
  --approach "Use pattern Y" \
  --references "docs/design.md"
```

### 3. Update Runtime Context (during work)
```bash
vibey context runtime update 01KC2D0JK9JK \
  --active-files "src/feature.py" \
  --decision "Chose approach A over B because..."
```

### 4. Complete with Post-Mortem
```bash
vibey task complete 01KC2D0JK9JK \
  --summary "Implemented feature X with pattern Y"
```

## Best Practices

1. **Initialize early**: Set up context before starting work
2. **Update frequently**: Keep runtime context current
3. **Be specific**: Include file paths and decision rationale
4. **Review post-mortems**: Learn from completed work

## MCP Integration

AI assistants can manage context via MCP tools:
- `context_set_plan` - Set planning context
- `context_update_runtime` - Update during work
- `context_save_postmortem` - Save completion summary
```

### Acceptance Criteria
- [ ] User guide complete
- [ ] Examples for all workflows
- [ ] Best practices documented
- [ ] MCP integration explained

---

## Task 9: Document All Context Output Formats
**ID:** `01KCMJNWJYZFK331MSDEKJN7FJ`
**Priority:** Low | **Complexity:** Simple | **Type:** Documentation

### Problem
Users may not know available context output formats.

### Implementation Steps
Create `docs/reference/CONTEXT_FORMATS.md`:

```markdown
# Context Output Formats

## JSON Format
```json
{
  "plan_context": {
    "goals": ["..."],
    "approach": "...",
    "references": ["..."]
  },
  "runtime_context": {
    "active_files": ["..."],
    "decisions": ["..."]
  },
  "post_mortem": {
    "summary": "...",
    "files_changed": ["..."]
  }
}
```

## YAML Format
```yaml
plan_context:
  goals:
    - "..."
  approach: "..."
  references:
    - "..."
runtime_context:
  active_files:
    - "..."
```

## Markdown Format
```markdown
# Context for Task: {title}

## Planning
**Goals:**
- ...

**Approach:** ...

## Runtime
**Active Files:** ...
**Decisions:** ...

## Post-Mortem
**Summary:** ...
```

## Usage
```bash
vibey context export --format json
vibey context export --format yaml
vibey context export --format markdown
```
```

### Acceptance Criteria
- [ ] All formats documented
- [ ] Examples provided
- [ ] Usage commands shown

---

## Sprint Completion Checklist
- [ ] Context integrated into ticket model
- [ ] Git commit linking working
- [ ] Post-mortem generation functional
- [ ] MCP context tools implemented
- [ ] Token budget enforcement working
- [ ] Freshness tracking operational
- [ ] CLI commands tested
- [ ] User guide complete
- [ ] Format documentation done
