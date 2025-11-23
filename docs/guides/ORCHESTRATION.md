# Vibey Framework Orchestration Modes

⚠️ **DEPRECATED - Framework v2.0**

**This document describes v1.0 orchestration modes (Simple/Balanced/Tiered) which have been replaced by Sprint-Driven Orchestration in v2.0.**

**See instead:** [`SPRINT_DRIVEN_ORCHESTRATION.md`](SPRINT_DRIVEN_ORCHESTRATION.md)

---

## Migration Notice

Vibey Framework v2.0 introduces **Sprint-Driven Orchestration**, replacing the three-mode system:

**v1.0 (Deprecated):**
- Simple Mode → Explicit keyword rules
- Balanced Mode → Rules + agent triggers
- Tiered Mode → Fast/Coordinator/Explicit paths

**v2.0 (Current):**
- Sprint Mode → Phase-specific orchestration from sprint plans
- Ad-Hoc Mode → Flexible, autonomous decisions

**Why the change?**
- Simpler (1 approach vs 3 modes)
- More adaptive (context-aware orchestration)
- Cleaner CLAUDE.md (rules in sprint plans)
- Better quality (orchestration designed per sprint)

**Migration:** Update `project-config.yaml`:
```yaml
# OLD (v1.0)
framework:
  orchestration_mode: "balanced"  # or simple/tiered

# NEW (v2.0)
framework:
  sprint_driven_orchestration:
    enabled: true
```

---

## Original Documentation (v1.0 - For Reference Only)

---

## Overview

The Vibey framework includes 12 specialized agents and 15 workflows. Rather than manually specifying which to use, Claude can **automatically orchestrate** the right agents for your task.

**You have three orchestration modes to choose from:**
- **Simple & Transparent** - Explicit rules
- **Balanced & Discoverable** (Recommended) - Rules + pattern matching
- **Intelligent & Adaptive** - Smart routing with fast/slow paths

Your orchestration mode is configured in `.claude/project-config.yaml`:

```yaml
framework:
  orchestration_mode: "balanced"  # simple, balanced, or tiered
  auto_agent_launch: true
  require_quality_gates: true
```

---

## Mode A: Simple & Transparent

### How It Works

Claude follows **explicit orchestration rules** documented in your `.claude/CLAUDE.md` file.

Example rules:
```markdown
## Agent Orchestration Rules

When user mentions:
- "security", "vulnerability", "OWASP" → Use Security Reviewer agent
- "API", "endpoint", "REST" → Use API Specialist agent
- "database", "schema", "migration" → Use Database Specialist agent
- "test", "coverage", "pytest" → Use Test Engineer agent
```

Claude reads these rules at the start of every session and follows them.

### When to Use

**✅ Choose Simple Mode If:**
- You want **maximum transparency** - see exactly how orchestration works
- You have a **small team** learning the framework
- You prefer **explicit control** over which agents are used
- Your project is **straightforward** without complex orchestration needs
- You want to **customize** orchestration rules per project easily

**❌ Avoid Simple Mode If:**
- You have **complex orchestration needs** (multi-step workflows, conditional logic)
- You want Claude to be **more intelligent** about agent selection
- You don't want to maintain orchestration rules manually

### Pros & Cons

**Pros:**
- ✅ **Transparent** - All rules visible in .claude/CLAUDE.md
- ✅ **Fast** - No overhead, Claude just follows instructions
- ✅ **Simple** - Easy to understand and debug
- ✅ **Customizable** - Modify rules directly in .claude/CLAUDE.md
- ✅ **Predictable** - Same input always triggers same agents

**Cons:**
- ❌ **Less intelligent** - Relies on keyword matching
- ❌ **Maintenance burden** - Adding agents requires updating rules
- ❌ **Can miss opportunities** - May not use agents when you'd benefit from them
- ❌ **No context awareness** - Doesn't adapt based on sprint phase or project state
- ❌ **CLAUDE.md bloat** - Rules can make .claude/CLAUDE.md very long

### Example Workflow

**User:** "I need to implement user authentication"

**Claude's Process:**
1. Reads .claude/CLAUDE.md orchestration rules
2. Matches "authentication" → Security-related, use API Specialist
3. Launches API Specialist agent
4. Follows single feature development workflow

**No dynamic decisions** - just rule following.

---

## Mode D: Balanced & Discoverable [RECOMMENDED]

### How It Works

Two-layer orchestration:

1. **High-level structure** in .claude/CLAUDE.md (sprint phases, quality gates)
2. **Agent trigger patterns** embedded in each agent file

Each agent advertises when it should be used:

```markdown
# Security Reviewer Agent

**Trigger Patterns:**
- Keywords: security, vulnerability, authentication, authorization, OWASP, XSS, SQL injection
- Contexts: quality gate phase, pre-deployment, compliance audit, auth implementation
- File patterns: */auth/*, */security/*, *login*, *password*, *token*
- Priority: High (always run before deployment)

---

[Agent content...]
```

Claude pattern-matches your request against all agent triggers and launches relevant ones.

### When to Use

**✅ Choose Balanced Mode If:**
- You want **smart automation** without complexity (most teams)
- You want agents to be **self-documenting** and discoverable
- You're building a **medium to large project** with multiple concerns
- You want **good performance** (no coordinator overhead)
- You want the framework to **scale** as you add more agents

**❌ Avoid Balanced Mode If:**
- You need **very simple, explicit** rules only (use Simple mode)
- You need **complex multi-step orchestration** with conditional logic (use Tiered mode)

### Pros & Cons

**Pros:**
- ✅ **Balanced intelligence** - Smarter than Simple, simpler than Tiered
- ✅ **Self-contained agents** - Adding new agents makes them auto-discoverable
- ✅ **Scales well** - Can handle 50+ agents without breaking
- ✅ **No overhead** - No coordinator agent needed
- ✅ **Multi-agent support** - Can launch multiple agents for complex requests
- ✅ **Maintainable** - Update agent file to change triggers

**Cons:**
- ❌ **Two systems** - .claude/CLAUDE.md + agent triggers to maintain
- ❌ **Pattern limitations** - May miss nuanced requests
- ❌ **No sequencing** - Can't express "do A, then B, then C" easily
- ❌ **Overlap issues** - Poorly designed patterns could trigger wrong agents

### Example Workflow

**User:** "I need to implement user authentication with JWT tokens"

**Claude's Process:**
1. Reads .claude/CLAUDE.md for high-level structure (we're in development phase)
2. Scans agent trigger patterns for matches:
   - API Specialist: Matches "authentication", "JWT", "tokens"
   - Security Reviewer: Matches "authentication", "tokens"
   - Test Engineer: Implied by development phase
3. Launches agents in priority order:
   - API Specialist (develop endpoints)
   - Security Reviewer (audit security)
   - Test Engineer (write tests)
4. Follows single feature development workflow

**Dynamic but structured** - uses triggers to make smart decisions.

---

## Mode F: Intelligent & Adaptive

### How It Works

**Tiered routing system:**

1. **Fast Path** - Simple requests handled directly
   - "Fix this typo"
   - "Add a comment here"
   - "Rename this variable"

2. **Smart Path** - Complex requests routed through Coordinator agent
   - "Implement user authentication with OAuth, JWT, and refresh tokens"
   - "Refactor the payment processing module for better performance and security"
   - "Plan sprint 3 with multiple interdependent features"

3. **Explicit Path** - User names specific agent
   - "Run security review"
   - "Use the observability engineer to audit logging"

The **Coordinator Agent** analyzes complex requests and:
- Understands project context (reads docs, configs, recent work)
- Determines which agents are needed
- Launches agents in the correct sequence
- Handles dependencies between agents
- Provides reasoning for routing decisions

### When to Use

**✅ Choose Tiered Mode If:**
- You have a **large, complex project** with many concerns
- You need **intelligent sequencing** of multi-step workflows
- You're an **enterprise team** with sophisticated needs
- You want **context-aware** orchestration (considers sprint phase, recent work, etc.)
- You have **frequent complex requests** that benefit from smart routing

**❌ Avoid Tiered Mode If:**
- Your project is **small or simple** (coordinator adds unnecessary overhead)
- You want **maximum speed** for all requests (coordinator adds latency)
- You prefer **transparent, simple** orchestration (coordinator decisions less visible)

### Pros & Cons

**Pros:**
- ✅ **Most intelligent** - Best orchestration decisions
- ✅ **Handles complexity** - Multi-step workflows with dependencies
- ✅ **Context-aware** - Considers project state, sprint phase, recent work
- ✅ **Optimized paths** - Fast for simple, smart for complex
- ✅ **Reasoning** - Coordinator explains routing decisions
- ✅ **Future-proof** - Scales to arbitrary complexity

**Cons:**
- ❌ **Most complex** - Three paths to understand and maintain
- ❌ **Coordinator overhead** - Adds latency for complex requests
- ❌ **Less transparent** - Routing logic hidden in coordinator
- ❌ **Overkill for simple projects** - Unnecessary sophistication
- ❌ **Debugging harder** - More moving parts

### Example Workflow

**User:** "I need to implement user authentication with OAuth, JWT, password reset, email verification, and 2FA"

**Claude's Process:**
1. Recognizes this is a **complex request** → Route to Coordinator
2. Coordinator agent launches and analyzes:
   - Multiple concerns: auth, security, email, testing
   - Project context: FastAPI backend, PostgreSQL, Redis cache
   - Sprint state: Sprint 2, development phase
3. Coordinator determines agent sequence:
   - Architecture Specialist (design auth architecture)
   - API Specialist (implement endpoints)
   - Database Specialist (schema for users, tokens, 2FA)
   - Security Reviewer (audit implementation)
   - Test Engineer (comprehensive tests)
   - Documentation Engineer (update docs)
4. Coordinator launches agents **in sequence**, passing context between them
5. Each agent fills handoff templates for the next agent

**Result:** Coordinated, context-aware orchestration for complex tasks.

---

## Comparison Table

| Feature | Simple | Balanced | Tiered |
|---------|--------|----------|--------|
| **Intelligence** | Low | Medium | High |
| **Speed** | Fast | Fast | Fast (simple) / Slower (complex) |
| **Transparency** | High | Medium | Low |
| **Complexity** | Low | Medium | High |
| **Maintenance** | Manual rules | Agent triggers | Coordinator logic |
| **Context Awareness** | None | Limited | High |
| **Best For** | Small teams, learning | Most projects | Enterprise, complex projects |
| **Overhead** | None | None | Coordinator for complex requests |

---

## Changing Orchestration Mode

You can switch modes at any time.

### In a Claude Code Session

**Tell Claude:**
```
"I'd like to switch to [simple/balanced/tiered] orchestration mode"
```

**Claude will:**
1. Update `.claude/project-config.yaml`
2. Regenerate `.claude/CLAUDE.md` with new orchestration instructions
3. Confirm the change

### Manually

**Edit `.claude/project-config.yaml`:**
```yaml
framework:
  orchestration_mode: "balanced"  # Change to: simple, balanced, or tiered
```

**Then regenerate .claude/CLAUDE.md:**
```bash
python3 scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

---

## Orchestration Best Practices

### For All Modes

1. **Trust the system** - Let Claude orchestrate, don't micromanage
2. **Provide context** - More details = better agent selection
3. **Review quality gates** - Orchestration ensures quality checks run
4. **Update .claude/CLAUDE.md** - Keep project context current

### Mode-Specific Tips

**Simple Mode:**
- Keep rules focused and unambiguous
- Update rules when adding new agents
- Document edge cases

**Balanced Mode:**
- Ensure agent trigger patterns are comprehensive
- Avoid overlapping patterns between similar agents
- Test pattern matching with diverse requests

**Tiered Mode:**
- Trust the coordinator for complex requests
- Use explicit agent names when you know exactly what you want
- Review coordinator reasoning to understand decisions

---

## Agent Trigger Pattern Reference

When using **Balanced** or **Tiered** mode, each agent includes trigger patterns.

### Pattern Structure

```markdown
**Trigger Patterns:**
- Keywords: [words/phrases that trigger this agent]
- Contexts: [situations when this agent is relevant]
- File patterns: [file paths/patterns that indicate this agent's domain]
- Priority: [Low/Medium/High - determines launch order]
```

### Pattern Matching Rules

Claude uses **fuzzy matching** - variations and synonyms work:
- "auth" matches "authentication", "authorize", "OAuth"
- "DB" matches "database", "schema", "migration"
- "secure" matches "security", "vulnerability", "OWASP"

**Multiple matches** - If multiple agents match, all relevant ones launch:
- "Secure the API endpoints" → API Specialist + Security Reviewer

**Priority** - Agents launch in priority order:
- High priority: Security Reviewer, Architecture Specialist
- Medium priority: Most development agents
- Low priority: Documentation Engineer

---

## Troubleshooting

### Claude Isn't Using Agents

**Check:**
1. `framework.auto_agent_launch` is `true` in config
2. .claude/CLAUDE.md is current (regenerate if needed)
3. Your request is specific enough for pattern matching

**Solution:**
- Be more specific: "Implement auth" → "Implement JWT authentication endpoints"
- Mention agent domain: "Review security of this code"
- Explicitly name agent if needed: "Use the security reviewer agent"

### Wrong Agents Are Being Used

**Simple Mode:**
- Review orchestration rules in .claude/CLAUDE.md
- Make rules more specific

**Balanced Mode:**
- Check agent trigger patterns for overlap
- Refine patterns in agent files

**Tiered Mode:**
- Review coordinator reasoning (Claude explains decisions)
- Provide more context in your request

### Too Many Agents Launching

**Balanced Mode:**
- Tighten trigger patterns (make them more specific)
- Add exclusion conditions

**Tiered Mode:**
- Coordinator may be over-cautious
- Provide more focused requests

---

## Advanced: Custom Orchestration

### Adding New Agents

**Simple Mode:**
1. Create new agent file
2. Add orchestration rule to .claude/CLAUDE.md template
3. Regenerate .claude/CLAUDE.md

**Balanced Mode:**
1. Create new agent file with trigger patterns
2. Agent is automatically discoverable
3. No .claude/CLAUDE.md changes needed

**Tiered Mode:**
1. Create new agent file with trigger patterns
2. Coordinator automatically considers new agent
3. No additional configuration needed

### Project-Specific Rules

All modes support **custom rules** in .claude/CLAUDE.md:

```markdown
## Project-Specific Orchestration Rules

For this project:
- Always run security review before database changes
- Use ML engineer for any model-related changes
- Documentation engineer reviews all API changes
```

---

## Frequently Asked Questions

### Can I mix modes?

No. Choose one mode per project. However, you can:
- Use explicit agent names in any mode
- Customize orchestration rules in .claude/CLAUDE.md for any mode

### Which mode do you recommend?

**Balanced (Mode D)** for 90% of projects. It's smart enough to be helpful, simple enough to understand, and fast enough not to slow you down.

Use **Simple** if you're learning or have a very small project.
Use **Tiered** if you have enterprise-scale complexity.

### Does mode affect quality gates?

No. Quality gates (security, tests, logging, docs) are enforced regardless of orchestration mode. Mode only affects **how** agents are selected, not **which quality standards** apply.

### Can I change modes mid-project?

Yes! You can switch modes anytime. Claude will adapt to the new orchestration approach immediately.

### What if I don't want automatic orchestration?

Set `framework.auto_agent_launch: false` in config. Then you must explicitly name agents:

```
"Use the security reviewer agent to audit this code"
```

---

## Summary

**Choose your orchestration mode based on project needs:**

- **Simple (A):** Small projects, learning, maximum transparency
- **Balanced (D):** Most projects, smart automation, good performance ← **Recommended**
- **Tiered (F):** Large/complex projects, enterprise teams, maximum intelligence

**Configure in `.claude/project-config.yaml`:**
```yaml
framework:
  orchestration_mode: "balanced"
```

**Change anytime** - Just tell Claude or update the config.

Happy building! 🚀
