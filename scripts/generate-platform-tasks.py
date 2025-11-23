#!/usr/bin/env python3
"""Generate task YAML files for platform port tracks."""

import os
from datetime import datetime, timezone

ROADMAP_DIR = ".vibey/roadmap"

TASKS = {
    "aider-port": {
        "aider-port-1": [
            ("001", "Create AiderAdapter class", "Extend PlatformAdapter base class, implement platform-specific methods, handle config generation", "web-developer", "high", "medium"),
            ("002", "Generate aider.conf.yml template", "Model selection, API key management, custom commit prompt template", "web-developer", "high", "low"),
            ("003", "Agent prompt template system", "Convert agent instructions to Aider system prompts, store in .aider/agents/, inject via --system flag", "web-developer", "high", "medium"),
            ("004", "Workflow script generation", "Simple workflows to Bash scripts, complex workflows to Python API scripts, store in .aider/workflows/", "web-developer", "high", "medium"),
            ("005", "Git hook integration", "Pre-commit hooks for quality gate validation, post-commit hooks for handoff metadata tracking", "web-developer", "medium", "low"),
            ("006", "Handoff metadata in commits", "Custom commit prompt template with handoff metadata, git commit message structure for agent tracking", "web-developer", "medium", "low"),
            ("007", "Integration testing", "Test with real Aider installation, verify git commits work, ensure multi-file workflows execute correctly", "test-engineer", "high", "medium"),
            ("008", "Documentation", "User guide for terminal users, developer guide for customization, example projects", "docs-writer", "medium", "low"),
        ]
    },
    "continue-port": {
        "continue-port-1": [
            ("001", "Create ContinueAdapter class", "Extend PlatformAdapter base class, implement deployment to .continue/ directory, generate config.yaml", "web-developer", "high", "medium"),
            ("002", "Agent to Slash Command conversion", "Convert all 12 agents to slash commands, create prompt templates with Jinja2, handle agent parameters", "web-developer", "high", "medium"),
            ("003", "Workflow to Command sequence mapping", "Map workflow steps to prompt templates, implement command chaining logic", "web-developer", "high", "medium"),
            ("004", "config.yaml template", "Jinja2 template for main config, model configuration, slash command definitions, context provider setup", "web-developer", "medium", "low"),
            ("005", "Unit tests", "Test adapter deployment logic, validate config generation, verify slash command syntax", "test-engineer", "high", "medium"),
            ("006", "VS Code integration testing", "Deploy to test project, verify commands appear in VS Code, test command execution", "test-engineer", "high", "medium"),
            ("007", "Documentation start", "Architecture overview, configuration reference", "docs-writer", "medium", "low"),
        ],
        "continue-port-2": [
            ("001", "Vibey context provider implementation", "Workflow context provider, quality gates provider, sprint/task context provider", "web-developer", "high", "medium"),
            ("002", "JetBrains integration testing", "Test in IntelliJ IDEA, PyCharm, verify feature parity with VS Code", "test-engineer", "high", "medium"),
            ("003", "MCP server integration", "Configure Vibey MCP server in Continue, test tool discovery, verify agent invocation", "web-developer", "medium", "medium"),
            ("004", "Integration examples", "Web-app project example, API project example, ML project example", "docs-writer", "medium", "low"),
            ("005", "Complete documentation", "User guide with screenshots, multi-IDE setup instructions, troubleshooting guide", "docs-writer", "medium", "medium"),
        ]
    },
    "windsurf-port": {
        "windsurf-port-1": [
            ("001", "Create WindsurfAdapter class", "Extend PlatformAdapter base class, implement deployment to .windsurf/ directory, handle file generation", "web-developer", "high", "medium"),
            ("002", ".windsurfrules generation", "Template for project context, tech stack extraction, code standards integration, character limit handling (6KB)", "web-developer", "high", "medium"),
            ("003", "Workflow to Markdown conversion", "Convert Vibey workflows to Cascade workflow format, handle multi-step instructions, workflow composition", "web-developer", "high", "medium"),
            ("004", "Agent rules generation", "Convert agents to .windsurf/rules/*.md, activation mode configuration, glob pattern support", "web-developer", "medium", "low"),
            ("005", "Settings and MCP config", "settings.json template, mcp_config.json template (optional)", "web-developer", "medium", "low"),
            ("006", "Unit tests", "Test deployment logic, validate markdown generation, verify character limits", "test-engineer", "high", "medium"),
            ("007", "Manual testing with Windsurf", "Deploy to real Windsurf IDE, execute workflows in Cascade, verify context preservation", "test-engineer", "high", "medium"),
        ],
        "windsurf-port-2": [
            ("001", "Advanced Cascade integration", "Multi-step workflow optimization, state passing between workflow steps, quality gate checkpoints", "web-developer", "high", "high"),
            ("002", "MCP tool wrapper", "Wrap select Vibey agents as MCP tools, return structured results to Cascade, test tool invocation", "web-developer", "medium", "medium"),
            ("003", "VS Code compatibility testing", "Verify VS Code extension compatibility, test with VS Code settings import, document differences", "test-engineer", "medium", "medium"),
            ("004", "Integration tests", "End-to-end deployment tests, workflow execution tests, MCP integration tests", "test-engineer", "high", "medium"),
            ("005", "Documentation", "Windsurf adapter guide, workflow best practices for Cascade, migration guide (VS Code to Windsurf)", "docs-writer", "medium", "medium"),
            ("006", "Example projects", "Web-app example with Windsurf, API project example, full workflow demonstration", "docs-writer", "medium", "low"),
        ]
    },
    "jetbrains-port": {
        "jetbrains-port-1": [
            ("001", "Research JetBrains AI MCP format", "Document MCP server registration format, identify configuration file locations, understand AI Assistant vs Junie differences", "web-developer", "high", "low"),
            ("002", "Create .junie/ directory structure template", "mcp.json template with Jinja2, guidelines.md template, project-level mcp/vibey-server.json", "web-developer", "high", "medium"),
            ("003", "Create .idea/ai/ configuration", "vibey-config.xml template, AI settings integration", "web-developer", "medium", "low"),
            ("004", "JetBrainsAdapter class", "Extend PlatformAdapter base class, generate all configuration files, handle multi-IDE differences", "web-developer", "high", "medium"),
            ("005", "Test MCP server connection", "Test in IntelliJ IDEA, verify tool discovery works, debug connection issues", "test-engineer", "high", "medium"),
            ("006", "Verify Vibey tools appear", "All agents visible as tools, all workflows visible as tools, quality gates accessible", "test-engineer", "high", "low"),
        ],
        "jetbrains-port-2": [
            ("001", "Test in PyCharm", "Python-specific workflows, verify tool execution, document any differences", "test-engineer", "high", "low"),
            ("002", "Test in WebStorm", "JavaScript/TypeScript workflows, frontend agent testing, document any differences", "test-engineer", "high", "low"),
            ("003", "Test in GoLand", "Go-specific workflows, backend agent testing, document any differences", "test-engineer", "high", "low"),
            ("004", "Test multi-agent coordination", "Junie + Vibey agents, Claude Agent + Vibey agents, coordination patterns", "test-engineer", "medium", "medium"),
            ("005", "Create JetBrains integration guide", "Setup instructions for each IDE, configuration reference, troubleshooting guide", "docs-writer", "high", "medium"),
            ("006", "Create IDE-specific examples", "IntelliJ/Java example, PyCharm/Python example, WebStorm/TypeScript example", "docs-writer", "medium", "low"),
        ]
    }
}


def generate_task_yaml(track_id: str, sprint_id: str, task_num: str, title: str, description: str, agent: str, priority: str, complexity: str) -> str:
    task_id = f"{sprint_id}-task-{task_num}"
    now = datetime.now(timezone.utc).isoformat()

    return f'''task:
  id: {task_id}
  sprint_id: {sprint_id}
  track_id: {track_id}
  roadmap_id: vibey-framework-v2
  task_type: development
  title: {title}
  description: |
    {description}
  status: not_started
  blocked: false
  created: '{now}'
  started: null
  completed: null
  assigned_agent: {agent}
  priority: {priority}
  phase_label: null
  estimated_tokens: 5000
  actual_tokens: null
  complexity: {complexity}
  gate_info: null
  audit_results: null
  dependencies: []
  blocks: []
  blocked_by: []
  depends_on: []
  depended_on_by: []
  deliverables: []
  commits: []
  metadata:
    last_updated: '{now}'
    token_efficiency: null
    duration_hours: null
'''


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    roadmap_path = os.path.join(base_dir, ROADMAP_DIR)

    for track_id, sprints in TASKS.items():
        for sprint_id, tasks in sprints.items():
            for task_num, title, description, agent, priority, complexity in tasks:
                task_id = f"{sprint_id}-task-{task_num}"
                task_dir = os.path.join(roadmap_path, track_id, sprint_id, task_id)
                task_file = os.path.join(task_dir, "task.yaml")

                os.makedirs(task_dir, exist_ok=True)

                content = generate_task_yaml(track_id, sprint_id, task_num, title, description, agent, priority, complexity)

                with open(task_file, 'w') as f:
                    f.write(content)

                print(f"Created: {task_file}")

    print(f"\nTotal tasks created: {sum(len(tasks) for sprints in TASKS.values() for tasks in sprints.values())}")


if __name__ == "__main__":
    main()
