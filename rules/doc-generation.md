# Auto-Doc Generation — Conventions

When `/workflow` reaches Phase 8 (Doc Review), automatically generate documentation
and memory update summaries from the session's work context.

## Documentation Summary (customfield_10185)

Auto-generate from:
1. **Plan comment** (Phase 3) — extract documentation plan section
2. **Files changed** — `git diff --name-only` against branch start
3. **docs/ changes** — any files in `docs/` that were created or modified
4. **Rule changes** — any `.claude/rules/` files modified
5. **Skill changes** — any `.claude/skills/` files modified

Format:
```
Documentation updated:
- <file>: <what changed and why>
- <file>: <what changed and why>

No documentation needed for: <files that don't affect operational docs>
```

## Memory Update Summary (customfield_10186)

Auto-generate from:
1. **Post-mortem lessons** (Phase 7) — extract actionable insights
2. **Memory files written** — any files in `~/.claude/projects/.../memory/`
3. **Vault notes created** — any files in `submodules/memory/`
4. **Feedback corrections** — any user corrections during the session

Format:
```
Memory updates:
- <type>: <file> — <what was persisted>
- <type>: <file> — <what was persisted>

Vault notes:
- <path> — <decision/knowledge/research documented>
```

## When to skip

If a session produces no documentation or memory updates (e.g., pure investigation
or planning with no implementation), set both fields to "No updates — <reason>".
