# Add agent management functionality to Vibey Manager

**ID:** `core-framework-3-task-006`  
**Sprint:** `core-framework-3`  
**Type:** development  
**Status:** ✅ Completed  
**Priority:** 🟡 Medium  

## Description

Extend Vibey Manager agent with comprehensive agent management capabilities.

New Capabilities:
1. List Available Agents
   - Show all 12 specialized agents
   - Display agent specialties and capabilities
   - Show trigger patterns for orchestration

2. View Agent Workload
   - Show tasks assigned to each agent
   - Display workload by status (not_started, in_progress, completed)
   - Show agent capacity and availability

3. Agent Assignment
   - Assign tasks to specific agents
   - Reassign tasks between agents
   - Batch assignment operations

4. Agent Recommendations
   - Recommend best agent for a given task
   - Recommend next tasks for a given agent
   - Show confidence scores and reasoning

5. Agent Capabilities
   - View detailed agent capabilities
   - Show task types each agent handles
   - Display keyword matching for orchestration

Commands to Add:
- "Show me agent workload"
- "Which agents are available?"
- "Assign task X to agent Y"
- "Which agent should handle task X?"
- "What tasks should the web-developer work on?"
- "Show me all security agent capabilities"

Integration:
- Use roadmap agents command (roadmap-lib/agents.py)
- Use roadmap recommend command
- Use roadmap assign command
- Add conversational wrappers for CLI commands

Files to Modify:
- framework/agents/core/vibey-manager.md (add Agent Management section)
- Add examples and usage patterns


## Details

- **Estimated Tokens:** 1
- **Complexity:** medium

## Timeline

- **Created:** 2025-11-08 10:10 UTC
- **Started:** 2025-11-08 15:16 UTC
- **Completed:** 2025-11-08 15:17 UTC

---

*Generated from task.yaml on 2025-11-09 19:14 UTC*
