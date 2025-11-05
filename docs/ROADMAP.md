# Vibey Framework Roadmap

**Version:** 1.1
**Last Updated:** 2025-11-04

---

## Current Status

**Framework State:** ✅ Production Ready (Claude Code)
- 12 specialized agents
- 16 structured workflows
- 22 handoff templates
- 3 orchestration modes
- ~50,600 lines across 68 components

---

## Near-Term Roadmap (Next 3 Months)

### 1. Default CLAUDE.md File
**Status:** Planned
**Priority:** High
**Description:** Create a default CLAUDE.md that gets deployed with framework for immediate use before customization.

**Tasks:**
- [ ] Design generic CLAUDE.md template with placeholders
- [ ] Include essential agent/workflow references
- [ ] Add quick-start instructions
- [ ] Test with greenfield projects

### 2. Migrate from Config-Driven to Docs-Driven
**Status:** Planned
**Priority:** Medium
**Description:** Reduce reliance on project-config.yaml, increase use of documentation files for project context.

**Tasks:**
- [ ] Define docs-driven architecture
- [ ] Identify what stays in config vs. moves to docs
- [ ] Update workflows to read from docs
- [ ] Migration guide for existing projects

---

## Platform Compatibility Assessment

**Date Completed:** 2025-11-04
**Scope:** Evaluate Vibey framework compatibility with Goose and Cursor agentic workflows

### Executive Summary

The Vibey framework's core concepts (specialized agents, structured workflows, quality gates) are **platform-agnostic** and translate well to other agentic systems. However, the implementation is tightly coupled to Claude Code's specific features, requiring adaptation work.

**Compatibility Ratings:**
- **Goose**: ✅ **75-85% Compatible** (Moderate effort, HIGH confidence)
- **Cursor**: ⚠️ **50-65% Compatible** (High effort, MEDIUM confidence)

---

## Claude Code Dependencies

### Hard Dependencies (Must Be Replaced)

| Feature | Usage in Vibey | Impact |
|---------|----------------|--------|
| **Slash Commands** (`/vibey`) | Primary entry point | CRITICAL |
| **`.claude/` Directory** | Framework storage with IDE recognition | HIGH |
| **Task Tool** | Subagent launching mechanism | CRITICAL |
| **CLAUDE.md** | Session context auto-read | HIGH |
| **Agent Markdown Files** | Instruction format | MEDIUM |

### Soft Dependencies (Portable)

- ✅ Conversational discovery (Q&A)
- ✅ Jinja2 templates (rendering)
- ✅ Python scripts (validation, rendering)
- ✅ Git integration
- ✅ Quality gates (concept)
- ✅ Workflow structure (concept)

---

## Goose Compatibility Analysis

### Natural Mappings

| Vibey Concept | Goose Equivalent | Compatibility |
|---------------|------------------|---------------|
| Workflows (15) | Recipes | ✅ Direct mapping |
| Specialized Agents (12) | Extensions/Tools | ✅ Direct mapping |
| Coordinator Agent | Recipe orchestration | ✅ Built-in |
| Quality Gates | Recipe validation steps | ✅ Can implement |
| Handoff Templates | Structured outputs | ✅ Can implement |
| CLAUDE.md | Recipe context/setup | ✅ Can adapt |

### Goose Strengths

- ✅ MCP ecosystem access (1000+ tools)
- ✅ LLM agnostic (Claude, GPT-4, Gemini)
- ✅ Multi-agent orchestration proven
- ✅ Recipe sharing capability
- ✅ Platform independent (CLI + desktop)
- ✅ Open source community

### Required Adaptations

**1. Recipe Conversion**
- Convert 15 workflows → 15 Goose recipes
- Estimated: 40-60 hours (2-4 hours per workflow)

**2. Extension Development**
- Convert 12 agents → 12 Goose extensions
- Tool definitions, orchestration, context passing
- Estimated: 80-120 hours (7-10 hours per agent)

**3. Initialization System**
- Replace `/vibey` with `goose recipe run vibey-init`
- Create setup recipes
- Estimated: 20-30 hours

**4. Context System**
- Replace CLAUDE.md auto-read with recipe parameters
- Estimated: 10-15 hours

**Total Effort: 150-225 hours (4-6 weeks with 2-3 developers)**

---

## Cursor Compatibility Analysis

### Cursor Capabilities

- ✅ Multi-agent workflows (up to 8 agents in parallel)
- ✅ Git worktree isolation
- ✅ Native tool access (file, terminal, browser, search)
- ✅ Multiple LLM support
- ✅ Composer model (4× faster)
- ✅ Voice mode

### Fundamental Challenges

| Vibey Feature | Cursor Challenge | Severity |
|---------------|------------------|----------|
| Sequential workflows | Optimized for parallel agents | MEDIUM |
| Specialized agent instructions | System prompts per agent | MEDIUM |
| Conversational setup | IDE-first, not chat-first | HIGH |
| Framework initialization | No slash command equivalent | HIGH |
| Agent coordination | Different coordination model | MEDIUM |
| Quality gates | No built-in concept | MEDIUM |

### Required Adaptations

**1. Agent Reimplementation**
- Convert 12 agents → Cursor agent configurations
- Work within parallel agent model
- Estimated: 100-140 hours (8-12 hours per agent)

**2. Workflow Restructuring**
- Redesign 15 workflows for parallel execution
- Identify parallelizable vs. sequential steps
- Estimated: 60-90 hours (4-6 hours per workflow)

**3. Initialization System**
- Options: Extension, CLI tool, or manual process
- Estimated: 40-80 hours

**4. Context System**
- Replace CLAUDE.md with Cursor workspace settings
- Configure per-agent contexts
- Estimated: 25-35 hours

**5. Quality Gates Integration**
- Build custom quality gate agents
- Integrate with Cursor tools
- Estimated: 40-60 hours

**Total Effort: 265-405 hours (7-10 weeks with 3-4 developers)**

### Paradigm Differences

- ❌ **Parallel-first vs. Sequential-first** - Fundamental mismatch
- ❌ **IDE-integrated vs. Standalone** - Different UX models
- ⚠️ **Composer model** - May not follow instructions as precisely as Claude
- ✅ **Speed** - 4× faster could offset other challenges
- ✅ **IDE integration** - Native file operations advantage

---

## Recommended Paths Forward

### Option 1: Goose Port (RECOMMENDED)

**Priority:** HIGH
**Confidence:** HIGH
**Timeline:** 2.5-3.5 months

**Phase 1: MVP (6-8 weeks)**
- Convert 5-7 core agents to Goose extensions
- Convert 3-5 high-value workflows to recipes
- Build initialization recipe
- Test with real projects

**Phase 2: Complete Port (4-6 weeks)**
- Convert remaining 5-7 agents
- Convert remaining 10-12 workflows
- Polish and optimize
- Documentation and distribution

**Why Goose First:**
1. Architectural alignment (Recipes ≈ Workflows)
2. Proven multi-agent orchestration
3. MCP ecosystem access
4. Lower risk, higher success probability
5. Open source community engagement

**Expected Outcomes:**
- ✅ Vibey concepts validated on non-Claude platform
- ✅ Access to broader user base (not just Claude Code users)
- ✅ Recipe sharing in Goose ecosystem
- ✅ Learning for future ports

---

### Option 2: Multi-Platform Framework (BEST LONG-TERM)

**Priority:** MEDIUM
**Confidence:** HIGH
**Timeline:** 5-7 months

**Phase 1: Platform-Agnostic Core (6-8 weeks)**
- Extract core concepts into abstract definitions
- Define platform adapter interface
- Build shared libraries (Python, templates, schemas)

**Phase 2: Platform Adapters (Parallel Development)**
- **Claude Code adapter** - Refactor existing (2-3 weeks)
- **Goose adapter** - Recipe/extension system (8-10 weeks)
- **Cursor adapter** - Agent/workflow system (12-15 weeks)

**Phase 3: Unified CLI (4-5 weeks)**
- Build `vibey` CLI tool working across platforms
- Commands: `vibey init --platform=goose|cursor|claude`
- Platform detection and adapter selection

**Expected Outcomes:**
- ✅ Single framework, multiple platforms
- ✅ Unified user experience
- ✅ Maximum market reach
- ✅ Future-proof architecture

---

### Option 3: Cursor POC (VALIDATE FIRST)

**Priority:** LOW
**Confidence:** MEDIUM
**Timeline:** 4 weeks for POC, then reassess

**POC Scope:**
- Convert 2-3 simple workflows
- Test parallel execution model
- Validate Composer instruction-following
- Assess UX challenges

**Decision Criteria:**
- ✅ Composer follows agent instructions accurately
- ✅ Parallel model works for Vibey use cases
- ✅ Benefits justify 50-70% more effort than Goose
- ✅ Clear path to initialization UX

**If POC Succeeds:** Continue to full port (15-20 weeks)
**If POC Fails:** Focus resources on Goose + Multi-platform

---

## Risk Assessment

### Goose Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MCP complexity | Medium | Medium | Start simple, iterate |
| Recipe adoption | Medium | Low | Strong documentation |
| Goose evolution | Medium | Medium | Community engagement |
| Performance | Low | Medium | Profile and optimize |

**Overall Risk: LOW-MEDIUM** ✅

### Cursor Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Paradigm mismatch | High | High | POC before commitment |
| Composer limitations | Medium | High | Test thoroughly |
| UX friction | High | Medium | CLI supplement |
| Maintenance burden | Medium | High | Modular architecture |
| Cursor API changes | Medium | High | Abstract adapters |

**Overall Risk: MEDIUM-HIGH** ⚠️

---

## Long-Term Vision (12-24 Months)

### Platform Support Matrix

| Platform | Status | Timeline | Priority |
|----------|--------|----------|----------|
| **Claude Code** | ✅ Production | Current | Maintain |
| **Goose** | 📋 Planned | 3 months | HIGH |
| **Cursor** | 🔬 Research | 6 months | MEDIUM |
| **GitHub Copilot** | 🔮 Future | 12+ months | LOW |
| **Aider** | 🔮 Future | 12+ months | LOW |

### Unified Framework Architecture

```
vibey-core/
├── concepts/              # Abstract definitions
│   ├── agents.yaml       # Agent specifications
│   ├── workflows.yaml    # Workflow specifications
│   └── quality-gates.yaml
├── adapters/             # Platform implementations
│   ├── claude-code/      # Current implementation
│   ├── goose/           # Recipe + extension system
│   ├── cursor/          # Agent + parallel system
│   └── adapter-api.py   # Common interface
├── shared/              # Platform-agnostic code
│   ├── templates/       # Jinja2 templates
│   ├── scripts/        # Validation, rendering
│   └── schemas/        # Configuration schemas
└── cli/                # Unified command-line interface
    └── vibey.py        # Platform-agnostic CLI
```

### Feature Roadmap

**Q1 2025 (Months 1-3)**
- ✅ Complete Goose MVP (5-7 agents, 3-5 workflows)
- ✅ Default CLAUDE.md implementation
- ✅ Docs-driven migration planning

**Q2 2025 (Months 4-6)**
- ✅ Complete Goose port (all agents/workflows)
- ✅ Cursor POC and evaluation
- ✅ Extract platform-agnostic core
- ✅ Begin multi-platform architecture

**Q3 2025 (Months 7-9)**
- ✅ Unified `vibey` CLI tool
- ✅ Claude Code refactor to adapter pattern
- ✅ Complete Cursor port (if POC successful)
- ✅ Community beta testing

**Q4 2025 (Months 10-12)**
- ✅ Production releases for all platforms
- ✅ Documentation and tutorials
- ✅ Recipe/extension marketplace
- ✅ Community contributions

---

## Success Metrics

### Technical Metrics
- **Port Completion:** All 12 agents, 16 workflows ported to Goose
- **Test Coverage:** ≥80% for adapter code
- **Performance:** Recipe execution within 2× Claude Code times
- **Reliability:** ≥95% success rate for standard workflows

### Adoption Metrics
- **Goose Users:** 100+ projects using Vibey recipes (6 months)
- **Recipe Stars:** 500+ GitHub stars on Goose recipes (12 months)
- **Community Contributions:** 10+ external contributors (12 months)
- **Platform Reach:** 3+ platforms supported (18 months)

### Quality Metrics
- **User Satisfaction:** ≥4.5/5 rating across platforms
- **Bug Rate:** <5 critical bugs per month
- **Documentation:** 100% coverage of agents/workflows
- **Support Response:** <48 hours for issues

---

## Open Questions

### Technical
1. **MCP Integration:** How deeply should we integrate with MCP ecosystem?
2. **Recipe Distribution:** Should we create a separate Goose recipe repo or keep in main repo?
3. **LLM Optimization:** Should we create model-specific agent instructions (Claude vs. GPT-4)?
4. **State Management:** How to handle long-running workflows across platforms?

### Strategic
1. **Resource Allocation:** Focus on depth (Claude Code polish) or breadth (multi-platform)?
2. **Open Source Model:** Should adapters live in main repo or separate repos?
3. **Community Engagement:** How to build contributor community for each platform?
4. **Commercial Model:** Should there be a premium tier for enterprise features?

### Product
1. **User Experience:** What's the minimum viable UX for each platform?
2. **Migration Path:** How do users migrate projects between platforms?
3. **Interoperability:** Should projects be portable across platforms?
4. **Documentation Strategy:** Separate docs per platform or unified docs?

---

## Next Steps (Immediate)

### Week 1-2: Planning & Design
- [ ] Review this assessment with stakeholders
- [ ] Choose: Goose-first OR Multi-platform approach
- [ ] Create detailed project plan with milestones
- [ ] Set up development environment for chosen platform

### Week 3-4: Spike/POC
- [ ] Spike: Convert 1 simple agent to Goose extension
- [ ] Spike: Convert 1 simple workflow to Goose recipe
- [ ] Test: Validate orchestration works
- [ ] Document: Learnings and approach refinement

### Month 2: MVP Development
- [ ] Implement 5-7 core agents
- [ ] Implement 3-5 key workflows
- [ ] Build initialization system
- [ ] Test with sample project

### Month 3: Validation & Iteration
- [ ] Beta test with real projects
- [ ] Gather feedback and iterate
- [ ] Polish and optimize
- [ ] Documentation and launch preparation

---

## Conclusion

The Vibey framework has strong potential for multi-platform support. The core concepts are sound and portable. The main work is adapting Claude Code-specific implementation details to each platform's paradigms.

**Recommended Immediate Action:**
Start with **Goose port** (Option 1) to validate platform-agnostic concepts with lower risk, then build toward **Multi-platform framework** (Option 2) for long-term sustainability.

**Expected Timeline to Multi-Platform:**
- **3 months:** Goose MVP validated
- **6 months:** Complete Goose port + platform-agnostic core extracted
- **9 months:** Unified CLI + Claude Code adapter refactored
- **12 months:** Production-ready multi-platform framework

**Key Success Factor:** Maintain focus on **core value proposition** (specialized agents, structured workflows, quality gates) while adapting to platform-specific constraints.

---

**Status:** Assessment Complete - Ready for Decision & Planning Phase
**Next Review:** After Goose MVP completion (3 months)
