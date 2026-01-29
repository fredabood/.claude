# D3: CLI Output Formats Audit

**Task ID:** 01KFXJX5ZCCCTFTDGYJ27BTV5H
**Phase:** D3: Interfaces
**Date:** 2026-01-29

## Executive Summary

Complete audit of the Vibey CLI output formatting system covering supported formats, formatting utilities, and command output patterns. The CLI uses the Rich library for styled terminal output and supports multiple output formats (text, JSON, YAML, CSV) via `--format` flags. Key finding: Default output is styled text with emojis and progress bars; machine-readable formats (JSON, CSV) are available for programmatic use. Remote mode requires adding notebook-compatible HTML/Markdown rendering.

## Methodology

**Files Analyzed:**
- `vibey/cli/formatters.py:1-452` - CLI output formatters
- `vibey/cli/main.py:1-50` - Rich console setup
- `vibey/cli/roadmap_commands/status.py:1-80` - JSON output example
- `vibey/cli/main.py:604-650` - Format flag patterns
- Various command files for output patterns

## Findings

### 2. Output Formats Table

| Format | Flag | Use Case | Serialization |
|--------|------|----------|---------------|
| Styled Text | (default) | Human terminal output | Rich Console print |
| JSON | `--format json` | API integration, scripting | `json.dumps(data, indent=2)` |
| YAML | `--format yaml` | Config export, debugging | `yaml.dump(data)` |
| CSV | `--format csv` | Spreadsheet export, reports | Python csv module |
| Markdown | `--format markdown` | Documentation, notebooks | String templates |
| Plain Text | `--quiet` or no Rich | Non-terminal environments | Simple print() |

### 3. Formatting Utilities Table

| Utility | Library | Purpose | Location |
|---------|---------|---------|----------|
| `Console` | Rich | Styled terminal output | `vibey/cli/main.py:20` |
| `Table` | Rich | Tabular data display | Various commands |
| `Panel` | Rich | Boxed content display | `vibey/cli/main.py:36` |
| `Text` | Rich | Styled text assembly | `vibey/cli/main.py:33` |
| `format_roadmap_summary()` | Custom | Roadmap overview | `vibey/cli/formatters.py:14` |
| `format_track_details()` | Custom | Track display | `vibey/cli/formatters.py:204` |
| `format_sprint_details()` | Custom | Sprint display | `vibey/cli/formatters.py:239` |
| `format_task_details()` | Custom | Task display | `vibey/cli/formatters.py:306` |
| `format_error()` | Custom | Error messages | `vibey/cli/formatters.py:339` |
| `format_success()` | Custom | Success messages | `vibey/cli/formatters.py:344` |
| `format_warning()` | Custom | Warning messages | `vibey/cli/formatters.py:349` |
| `_get_status_icon()` | Custom | Status emoji mapping | `vibey/cli/formatters.py:431` |
| `_render_progress_bar()` | Custom | Text progress bar | `vibey/cli/formatters.py:446` |
| `handle_cli_error` | Custom | Error decorator | `vibey/cli/formatters.py:398` |

### 4. Command Output Patterns Table

| Command Type | Default Format | Supports JSON | Supports YAML | Supports CSV |
|--------------|----------------|---------------|---------------|--------------|
| `roadmap status` | Styled text | Yes | No | No |
| `roadmap show` | Styled text | Yes | No | No |
| `roadmap list` | Styled text | Yes | No | No |
| `roadmap tokens report` | Styled text | Yes | No | Yes |
| `roadmap tokens budget` | Styled text | Yes | No | Yes |
| `roadmap context` | Plain text | Yes | No | No |
| `roadmap summarize` | Plain text | Yes | No | No |
| `roadmap db query *` | Styled table | Yes | No | No |
| `roadmap deps` | Styled text | Yes | No | No |
| `roadmap find` | Styled text | Yes | No | No |
| `session list` | Styled table | Yes | Yes | No |
| `session show` | Styled text | Yes | Yes | No |
| `git analyze` | Styled text | Yes | No | No |
| `git velocity` | Styled table | Yes | No | No |
| `discover show` | Markdown | Yes | No | No |
| `docs introspect` | JSON only | Yes | Yes | No |

### 5. Output Configuration Table

| Option | Flag | Default | Description |
|--------|------|---------|-------------|
| Verbose | `--verbose`, `-v` | False | Show detailed output |
| Quiet | `--quiet`, `-q` | False | Suppress non-essential output |
| Format | `--format`, `-f` | text | Output format selection |
| No Color | `NO_COLOR` env | False | Disable colored output |
| Force Color | `FORCE_COLOR` env | False | Force colored output |
| Width | `COLUMNS` env | auto | Terminal width override |
| JSON Indent | Hardcoded | 2 | JSON indentation spaces |

### 6. Status Icon Mapping

| Status | Icon | Used In |
|--------|------|---------|
| `not_started` | `⚪` | All entity displays |
| `in_progress` | `🔵` | All entity displays |
| `completed` | `✅` | All entity displays |
| `production_ready` | `✅` | All entity displays |
| `production_gate_check` | `🔍` | Sprint/task displays |
| `blocked` | `🔴` | All entity displays |
| `paused` | `⏸️` | All entity displays |
| `wont_do` | `⛔` | Track/sprint displays |
| Unknown | `❓` | Fallback |

### 7. Remote Display Strategy Table

| Context | Format | Rendering | Compatibility |
|---------|--------|-----------|---------------|
| Terminal (local) | Styled text | Rich Console | Full support |
| CI/CD Logs | Plain text | `--quiet` or env | No Rich styling |
| API Response | JSON | `--format json` | Full serialization |
| Databricks Notebook | HTML/Markdown | New renderer needed | Requires displayHTML() |
| Jupyter Notebook | HTML/Markdown | Rich HTML export | IPython.display |
| Web Dashboard | JSON + React | `--format json` | Frontend rendering |
| Streaming | JSONL | New format needed | Line-by-line updates |
| Email/Slack | Markdown | New renderer needed | Platform-specific |

**Remote Output Implementation:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     REMOTE OUTPUT ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ CLI Command     │────▶│ Format Selector │────▶│ Output Renderer │
│ (operations)    │     │ (--format flag) │     │ (Rich/JSON/etc) │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
        ┌────────────────────────┼───────────────────────┼────────────────┐
        │                        │                       │                │
        ▼                        ▼                       ▼                ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐  ┌───────────────┐
│ text          │      │ json          │      │ notebook      │  │ streaming     │
│ (Rich)        │      │ (json.dumps)  │      │ (NEW)         │  │ (NEW)         │
└───────────────┘      └───────────────┘      └───────────────┘  └───────────────┘
        │                        │                       │                │
        ▼                        ▼                       ▼                ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐  ┌───────────────┐
│ Terminal      │      │ API Response  │      │ Databricks    │  │ Real-time     │
│ stdout        │      │ HTTP Body     │      │ displayHTML() │  │ WebSocket     │
└───────────────┘      └───────────────┘      └───────────────┘  └───────────────┘
```

**New Format Requirements for Remote Mode:**

| Format | Purpose | Implementation |
|--------|---------|----------------|
| `notebook` | Databricks/Jupyter rendering | HTML tables with CSS |
| `html` | Web dashboard embedding | Full HTML document |
| `markdown` | Documentation/Slack | Markdown tables |
| `streaming` | Real-time updates | JSONL with timestamps |
| `widget` | Interactive notebooks | ipywidgets components |

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Rich library is terminal-only | Add notebook renderer | M | High |
| JSON format exists | Reuse for API responses | S | High |
| No HTML output format | Add HTML table renderer | M | Medium |
| No streaming format | Add JSONL streaming | M | Medium |
| Emojis may not render | Add text-only fallback | S | Medium |
| Progress bars are ASCII | Add HTML progress bars | S | Low |
| Error handling is CLI-specific | Add structured errors | M | High |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Output formats table lists >= 4 formats: PASS (6 formats)
- [x] Command output patterns table covers list/show/status commands: PASS (16 commands)
- [x] Remote display strategy addresses Databricks notebooks: PASS

## References

- `vibey/cli/formatters.py:14-201` - Roadmap formatting functions
- `vibey/cli/formatters.py:339-396` - Error/success/warning formatters
- `vibey/cli/formatters.py:431-452` - Status icons and progress bar
- `vibey/cli/main.py:12-20` - Rich Console setup
- `vibey/cli/main.py:604-650` - Format flag examples
- `vibey/cli/roadmap_commands/status.py:193` - JSON output example
