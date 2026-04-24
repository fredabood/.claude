---
description: "Search O'Reilly Learning for a topic, summarize the top results, and optionally post to the active Jira ticket"
user_invocable: true
---

# /oreilly

Query the O'Reilly Learning platform for a topic and return a ranked, summarized digest.
Output lands in the current conversation by default, or as a comment on the active Jira
ticket when `--jira` is passed.

Requires the `oreilly` MCP server to be connected (LAB-282 wired this; see
`submodules/memory/homelab/knowledge/integrations/oreilly-mcp-runbook.md`).

## Usage

```
/oreilly <topic>
/oreilly <topic> --n 10
/oreilly <topic> --format books
/oreilly <topic> --jira
/oreilly <topic> --format books --order popularity --jira
```

Examples:
- `/oreilly kubernetes patterns` — top 5 across all formats, output to conversation
- `/oreilly "event-driven architectures" --n 10` — top 10
- `/oreilly postgres indexes --format books --order popularity` — books only, popularity-ranked
- `/oreilly "LLM evaluation" --jira` — digest, posted as a comment on the active ticket

## Argument parsing

Parse the user input after `/oreilly`:

- **topic** (required): everything before the first flag. Preserve quoted phrases verbatim;
  otherwise join tokens with spaces. If no topic is given, stop and tell the user
  `/oreilly` requires a topic argument.
- `--n <int>` (optional, default 5): number of results. Clamp to 1..20.
- `--format <value>` (optional, default `all`): maps to `content_types` in the upstream
  tool. Accept values: `books`, `videos`, `audiobooks`, `live-events`, `articles`,
  `scenarios`, `playlists`, `learning-plans`, `all`. Pass `all` as an empty filter
  (omit `content_types`).
- `--order <value>` (optional): maps to `order_by`. Accept values: `relevance`, `rating`,
  `popularity`, `date_published`, `date_added`, `last_updated`, `upcoming_events`.
  Omit when not provided (server default weighted mix).
- `--jira` (optional, default off): post the digest as a comment on the active ticket
  instead of rendering it in the conversation.

If any flag value is invalid, stop and show the user the allowed values — do not silently
substitute a default.

## Steps

### Step 1: Write execution context marker

Write `.skill-execution-context.json` with:
`{"skill": "oreilly", "started_at": "<ISO8601>", "ticket_key": null}`

If `--jira` is set, resolve the active ticket (same logic as `/complete-task` etc. — check
`.skill-execution-context.json` from a previous skill, a prior `/start-task` marker, or
the most recent commit's `KEY-###` prefix on the current branch). Populate `ticket_key`
in the marker once known.

If `--jira` is set but no active ticket can be resolved, stop and ask the user for the key
rather than posting to the wrong place.

### Step 2: Verify the oreilly MCP is available

Confirm `mcp__oreilly__search-oreilly-content` is callable in this session. If it is not
(MCP not connected), stop and tell the user to restart Claude Code after sourcing `.env`,
then re-run the skill. Point them at the runbook. Do not try to call the O'Reilly HTTPS
endpoint directly — the skill's contract is via the MCP.

### Step 3: Call the upstream search tool

Invoke `mcp__oreilly__search-oreilly-content` with:

- `query`: the parsed topic
- `n_items`: parsed `--n` (default 5)
- `content_types`: set only if `--format` was provided and is not `all` — pass an array
  with the single mapped value (e.g. `["books"]`). Do not pass when `--format=all`.
- `order_by`: parsed `--order` if provided; otherwise omit.

The upstream returns a `result.content[0].text` payload whose JSON body has a
`search_results` object keyed by URN. Each value carries `title`, `authors`,
`publisher_names`, `display_format`, `marketing_type`, `url`, `image_url`,
`publication_date`, and format-dependent fields (`page_count`, `duration`,
`live_event_start_dates`).

### Step 4: Summarize each result

For each result, produce a **2-3 sentence orientation summary** based on title + authors
+ format + publication date + any snippet the upstream returns. The summary should answer:
"what is this resource and who would it be useful for?" Do not fabricate claims about
contents that aren't in the metadata — keep it to orientation, not a review.

Summarize using the agent's own reasoning (you are an LLM; do not spawn a separate Ollama
call — that would be a redundant round-trip). If you cannot confidently summarize from the
metadata, say "metadata-only" and skip embellishment.

### Step 5a: Render to conversation (default)

```
## O'Reilly: <topic>

**Filters:** format=<format>, order=<order>, n=<n>

### Results

1. **[<title>](<url>)** — <format>, <publication_date>
   <authors> · <publisher>
   <2-3 sentence summary>

2. **[<title>](<url>)** — <format>, <publication_date>
   ...
```

Use the `url` field verbatim — no URL construction on your part. Show authors as a
comma-joined string; if empty, show `—`. For live-events, include the next
`live_event_start_dates` entry after the publication date when present.

### Step 5b: Render to Jira (--jira)

If `--jira` is set, post the same digest as a comment on the active ticket via
`mcp__claude_ai_Atlassian__addCommentToJiraIssue`:

- cloudId: `fredabood.atlassian.net`
- issueIdOrKey: the resolved ticket key
- contentFormat: `markdown`
- commentBody: the formatted digest, prefixed with `## O'Reilly research: <topic>` and
  a line noting `Skill: /oreilly · <ISO8601 timestamp>`.

After posting, report the Jira comment URL in the conversation so the user can confirm
it landed.

### Step 6: Cleanup

Delete `.skill-execution-context.json`.

## Design notes

- **Why agent-side summarization, not an Ollama round-trip:** the skill runs inside a
  Claude Code session where the agent is already an LLM. Routing summary generation to
  ollama.dirtydata.studio adds latency and a failure mode (Ollama down) without improving
  quality. The original LAB-284 description suggested Ollama; this is an intentional
  deviation documented here.
- **Why no caching:** O'Reilly's upstream is fast (<500ms end-to-end through
  mcp-remote) and results are context-sensitive to the query phrasing. Caching would
  trade freshness for negligible latency gains.
- **Why no `--n` > 20:** the upstream accepts more, but digests beyond 20 items stop
  being useful as orientation — user wants a reading shortlist, not a dump.
- **No video/audio-duration formatting logic here:** the metadata includes `duration` in
  seconds for videos/audiobooks. Future enhancement is to show `HH:MM:SS` inline; for v1,
  keep output minimal and rely on the URL for anyone who cares.

## Required MCP Tools

- `mcp__oreilly__search-oreilly-content` (query, n_items, content_types, order_by, …)
- `mcp__claude_ai_Atlassian__addCommentToJiraIssue` (only when `--jira`)

## CloudId

Use `fredabood.atlassian.net` as the Jira cloudId.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "oreilly MCP not connected" | `.env` not sourced before Claude Code launch, or token missing | Run `./internal/scripts/inject-secrets.sh`; restart Claude Code |
| 401 from upstream | Token expired/revoked | Regenerate at https://learning.oreilly.com/access-tokens/ and update the `O'Reilly Publishing` 1P item |
| Empty results | Topic too narrow or account entitlement gap | Widen the query; try `--format all` |
| Jira comment didn't post | Ticket key didn't resolve | Pass `--jira` only when a ticket is active (post-`/start-task`) |
