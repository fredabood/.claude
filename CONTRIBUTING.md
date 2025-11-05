# Contributing to Vibey Agent Framework

Thank you for your interest in contributing to the Vibey Agent Framework! This document provides guidelines and instructions for contributing.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

---

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to make Vibey better.

---

## Getting Started

### Prerequisites

- Python 3.7 or later
- Git
- A text editor or IDE
- Basic understanding of:
  - AI agent frameworks
  - YAML configuration
  - Jinja2 templates
  - Markdown documentation

### Understanding the Framework

Before contributing, familiarize yourself with:

1. **[CLAUDE.md](CLAUDE.md)** - Repository context and development guidelines
2. **[docs/ROADMAP.md](docs/ROADMAP.md)** - Strategic direction and future plans
3. **[CHANGELOG.md](CHANGELOG.md)** - Version history and recent changes
4. **[framework/docs/](framework/docs/)** - User-facing documentation

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/vibey.git
cd vibey
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install pyyaml jinja2

# Optional: Install development tools
pip install pytest black flake8
```

### 3. Verify Setup

```bash
# Validate existing configs
python3 framework/scripts/validate-config.py framework/config/config-templates/web-application-fullstack.yaml

# Render a template
python3 framework/scripts/render-template.py \
  -c framework/config/config-templates/web-application-fullstack.yaml \
  -t framework/templates/CLAUDE.md.template \
  -o /tmp/test-claude.md
```

---

## How to Contribute

### Types of Contributions

We welcome:

1. **Bug fixes** - Fix issues in agents, workflows, scripts
2. **New agents** - Add specialized agents for new domains
3. **New workflows** - Add structured processes for common tasks
4. **New templates** - Add handoff templates for agent communication
5. **Documentation** - Improve guides, references, examples
6. **Scripts** - Add utilities for framework management
7. **Config templates** - Add project type templates
8. **Platform ports** - Port framework to Goose, Cursor, etc.

### Finding Work

- **Good First Issues** - Look for `good-first-issue` label
- **Help Wanted** - Check `help-wanted` label
- **Roadmap Items** - See [docs/ROADMAP.md](docs/ROADMAP.md)
- **Your Ideas** - Propose new features via issues

---

## Development Guidelines

### File Organization

```
vibey/
├── framework/               # Framework source (gets deployed)
│   ├── agents/             # Specialized agents
│   ├── workflows/          # Structured workflows
│   ├── templates/          # Jinja2 templates
│   ├── config/             # Config schema and templates
│   ├── commands/           # Slash commands
│   ├── scripts/            # Python utilities
│   └── docs/               # User documentation
├── docs/                   # Framework development docs
├── CLAUDE.md               # Repository context
├── README.md               # Main documentation
├── CHANGELOG.md            # Version history
└── CONTRIBUTING.md         # This file
```

### Design Principles

1. **Config-Driven** - Use `{{ config.* }}` for all tech-specific references
2. **Self-Documenting** - Clear, descriptive names and inline documentation
3. **Platform-Agnostic** - Core concepts portable across AI platforms
4. **Quality-First** - Quality gates prevent shipping incomplete work
5. **User-Friendly** - Conversational, natural language interaction

---

## Adding Components

### Adding a New Agent

1. **Choose Location**
   ```
   framework/agents/
   ├── planning/         # Strategic planning and research
   ├── development/      # Code implementation
   ├── quality/          # Testing, security, performance
   ├── documentation/    # Docs, diagrams, commits
   ├── core/             # Framework coordination
   └── architecture/     # Architecture review
   ```

2. **Create Agent File**
   ```markdown
   # [Agent Name]

   **Role:** [One-line description]

   ## Responsibilities
   - [Responsibility 1]
   - [Responsibility 2]

   ## Trigger Patterns (for Balanced/Tiered modes)
   **Keywords:** [list of keywords]
   **Contexts:** [list of contexts]
   **File Patterns:** [list of file patterns]

   ## Process
   ### Step 1: [Step name]
   [Instructions using {{ config.* }} for tech references]

   ### Step 2: [Step name]
   [More instructions]

   ## Quality Standards
   - [Standard 1]
   - [Standard 2]

   ## Outputs
   **Handoff Template:** `templates/handoffs/[template-name].md`
   **Deliverables:** [List of artifacts]

   ## Examples
   [Example usage scenarios]
   ```

3. **Use Config Variables**
   ```markdown
   ❌ BAD: Run `pytest` to test your code
   ✅ GOOD: Run `{{ config.testing.backend.command }}` to test your code

   ❌ BAD: Use React for the frontend
   ✅ GOOD: Use {{ config.technology_stack.frontend.framework }} for the frontend
   ```

4. **Add to Documentation**
   - Update agent count in README
   - Add to reference documentation
   - Add example usage

### Adding a New Workflow

1. **Choose Location**
   ```
   framework/workflows/
   ├── planning/         # Planning and design workflows
   ├── development/      # Development workflows
   ├── quality/          # Quality assurance workflows
   └── operations/       # Operational workflows
   ```

2. **Create Workflow File**
   ```markdown
   # [Workflow Name]

   **Purpose:** [One-line description]
   **Duration:** [Estimated time]
   **Project Types:** [Applicable project types]

   ## Prerequisites
   - [Prerequisite 1]
   - [Prerequisite 2]

   ## Phases

   ### Phase 1: [Phase Name] ([Duration])
   **Agent:** [Primary agent]
   **Inputs:** [Required inputs]
   **Process:** [Step-by-step instructions]
   **Outputs:** [Deliverables]

   ### Phase 2: [Phase Name] ([Duration])
   [Same structure]

   ## Success Criteria
   - [Criterion 1]
   - [Criterion 2]

   ## Variations
   ### For Web Apps
   [Specific instructions]

   ### For APIs
   [Specific instructions]
   ```

3. **Update Workflow Selection Guide**
   - Add to `framework/docs/guides/WORKFLOW_SELECTION_GUIDE.md`

### Adding a New Template

1. **Create Template File**
   ```
   framework/templates/handoffs/[name].md
   ```

2. **Use Jinja2 Syntax**
   ```jinja2
   # {{ title }}

   **Date:** {{ date }}
   **Project:** {{ config.project.name }}

   ## Summary
   {{ summary }}

   {% if optional_section %}
   ## Optional Section
   {{ optional_section }}
   {% endif %}

   {% for item in items %}
   - {{ item.name }}: {{ item.description }}
   {% endfor %}
   ```

3. **Reference in Agents**
   - Update agents that use this template
   - Add examples of usage

### Adding a New Script

1. **Create Script**
   ```python
   #!/usr/bin/env python3
   """
   Script Name - Brief description

   Longer description of what this script does.

   Usage:
       python3 script-name.py [arguments]
   """

   import sys
   import argparse
   from pathlib import Path
   from typing import Optional

   def main():
       parser = argparse.ArgumentParser(
           description="Script description"
       )
       parser.add_argument('--arg', help='Argument help')
       args = parser.parse_args()

       # Script logic

       return 0

   if __name__ == '__main__':
       sys.exit(main())
   ```

2. **Make Executable**
   ```bash
   chmod +x framework/scripts/script-name.py
   ```

3. **Add Error Handling**
   ```python
   try:
       import yaml
   except ImportError:
       print("Error: PyYAML not installed", file=sys.stderr)
       print("Install: pip install pyyaml", file=sys.stderr)
       sys.exit(1)
   ```

4. **Test the Script**
   ```bash
   python3 framework/scripts/script-name.py --help
   python3 framework/scripts/script-name.py [test arguments]
   ```

---

## Testing

### Manual Testing

1. **Test in Isolation**
   ```bash
   # Validate config
   python3 framework/scripts/validate-config.py [config-file]

   # Render template
   python3 framework/scripts/render-template.py -c [config] -t [template] -o [output]
   ```

2. **Test Deployment**
   ```bash
   # Create test project
   mkdir /tmp/test-vibey-project
   cd /tmp/test-vibey-project

   # Copy framework
   cp -r /path/to/vibey/framework .

   # Test deployment (simulated)
   cp -r framework/agents .claude/
   cp -r framework/workflows .claude/
   # etc.
   ```

3. **Test with Claude Code**
   - Deploy to actual project
   - Run `/vibey` command
   - Test workflows end-to-end

### Automated Testing

```python
# Coming soon - automated test suite
# framework/tests/test_agents.py
# framework/tests/test_workflows.py
# framework/tests/test_scripts.py
```

---

## Documentation

### Types of Documentation

1. **User Documentation** (`framework/docs/`) - Gets deployed to user projects
   - Getting started guides
   - Usage guides
   - Reference documentation

2. **Development Documentation** (`docs/`) - For framework contributors
   - Architecture decisions
   - Development history
   - Roadmap and strategy

3. **Code Documentation** - Inline in agents, workflows, scripts
   - Clear comments
   - Usage examples
   - Config variable references

### Documentation Standards

- **Clear headings** - Use descriptive section titles
- **Examples** - Show, don't just tell
- **Config references** - Use `{{ config.* }}` consistently
- **Links** - Link to related docs
- **Keep updated** - Update docs when changing code

---

## Submitting Changes

### Git Workflow

1. **Create Branch**
   ```bash
   git checkout -b feature/description
   # or
   git checkout -b bugfix/description
   ```

2. **Make Changes**
   - Follow file organization
   - Use config-driven approach
   - Add documentation
   - Test your changes

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "type: description

   Longer explanation of changes

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

   **Commit types:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `refactor:` - Code restructuring
   - `test:` - Test additions
   - `chore:` - Maintenance tasks

4. **Push Changes**
   ```bash
   git push origin feature/description
   ```

5. **Create Pull Request**
   - Go to GitHub
   - Create PR from your branch
   - Fill in PR template
   - Link related issues

### Pull Request Guidelines

**PR Title:** `type: Brief description`

**PR Description:**
```markdown
## Summary
[What does this PR do?]

## Changes
- [Change 1]
- [Change 2]

## Testing
[How was this tested?]

## Documentation
[What docs were updated?]

## Screenshots (if applicable)
[Visual changes]

Closes #[issue-number]
```

### Code Review Process

1. **Automated Checks** - Will run (when implemented)
2. **Maintainer Review** - Review for quality and fit
3. **Feedback** - Address review comments
4. **Approval** - Maintainer approves
5. **Merge** - PR is merged

---

## Release Process

### Version Numbering

Format: `MAJOR.MINOR.PATCH`

- **MAJOR** - Breaking changes (config schema, API)
- **MINOR** - New features (agents, workflows, scripts)
- **PATCH** - Bug fixes, documentation

### Pre-Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Examples tested
- [ ] README.md current

### Creating a Release

1. **Update Version**
   - `framework/scripts/check-version.py` - Update FRAMEWORK_VERSION
   - `CHANGELOG.md` - Add release notes
   - `README.md` - Update version if shown

2. **Create Release Branch**
   ```bash
   git checkout -b release/v1.x.0
   ```

3. **Final Testing**
   - Test deployment
   - Verify docs
   - Check examples

4. **Merge to Main**
   ```bash
   git checkout main
   git merge release/v1.x.0
   ```

5. **Tag Release**
   ```bash
   git tag -a v1.x.0 -m "Release v1.x.0"
   git push origin v1.x.0
   ```

6. **GitHub Release**
   - Create release on GitHub
   - Add release notes from CHANGELOG
   - Attach any artifacts

---

## Questions?

- **Issues** - Open a GitHub issue
- **Discussions** - Use GitHub discussions
- **Email** - [contact email if applicable]

---

## Attribution

This contributing guide was created for the Vibey Agent Framework.

Thank you for contributing! 🎉
