# Release Notes: Vibey v1.3.0 - Config-to-Docs Architecture

**Release Date:** November 9, 2025
**Codename:** Platform-Agnostic Core
**Sprint:** core-framework-2 (Config-to-Docs Architecture)

---

## 🎯 Overview

Vibey v1.3.0 represents a major architectural evolution, transforming the framework from a Claude Code-specific tool into a **platform-agnostic orchestration system**. This release introduces the **Config-to-Docs Architecture**, enabling deployment to multiple AI coding platforms from a single source of truth.

**Key Achievement:** Separation of source (`.vibey/`) from deployment (`.claude/`, `.goose/`, `.cursor/`)

---

## 🚀 What's New

### Platform-Agnostic Architecture

The framework now uses a **source → deployment** model:

```
.vibey/ (SOURCE - committed to git)
  ├── config/          → Platform-agnostic configuration
  ├── roadmap/         → Project state (YAML)
  ├── sprint_docs/     → Rich context (Markdown)
  └── templates/       → Custom templates

                ↓ Generate via Adapters

.claude/ (DEPLOYMENT - gitignored)
  ├── CLAUDE.md        → Generated instructions
  ├── agents/          → Generated agent files
  └── workflows/       → Generated workflow files
```

**Benefits:**
- 🎯 **Single Source of Truth** - One config, multiple platforms
- 🔄 **Multi-Platform** - Deploy to Claude Code, Goose, Cursor
- ⚡ **Fast Regeneration** - Recreate deployments instantly
- 🛡️ **Version Control** - Source committed, deployments temporary
- 🔌 **Extensible** - Easy to add new platforms

### Unified CLI

New `vibey` command replaces multiple scattered scripts:

```bash
# Deploy to any platform
./vibey deploy --platform claude-code
./vibey deploy --list-platforms

# Generate documentation
./vibey docs generate

# Manage roadmaps
./vibey roadmap summarize sprint core-framework-2
./vibey roadmap context task-id
```

**Features:**
- ✅ Colored output for better UX
- ✅ Comprehensive help system
- ✅ Command-specific help
- ✅ Consistent interface across all operations

### Platform Adapter System

Extensible architecture for supporting multiple AI platforms:

```python
# Base adapter interface
class PlatformAdapter(ABC):
    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    @abstractmethod
    def generate_instructions_file(self) -> str:
        pass

    @abstractmethod
    def generate_agent_file(self, agent_config: Dict) -> str:
        pass
```

**Current Adapters:**
- ✅ **Claude Code** - Production ready
- 🚧 **Goose** - Coming Q2 2025
- 🔬 **Cursor** - Research phase

**Why It Matters:**
- Each platform has unique requirements (file formats, naming conventions)
- Adapter pattern handles platform-specific details
- Core framework remains platform-agnostic
- Easy to add new platforms

### Permanent .vibey/ Directory

The `.vibey/` directory is now **permanent** and contains:

**Structure:**
```
.vibey/
├── config/              # Platform-agnostic configuration
│   ├── project.yaml
│   ├── framework.yaml
│   ├── agents/          # Agent configs (YAML metadata)
│   ├── workflows/       # Workflow configs (YAML metadata)
│   └── quality-gates.yaml
├── roadmap/             # Roadmap state (YAML)
│   ├── roadmap.yaml
│   ├── tracks/
│   ├── sprints/
│   └── tasks/
├── sprint_docs/         # Sprint documentation (Markdown)
│   └── {sprint-id}/
│       ├── plan.md
│       ├── architecture.md
│       └── retrospective.md
├── summaries/           # Auto-generated (gitignored)
│   ├── dependency_summaries/
│   └── task_summaries/
├── templates/           # Custom templates
├── backups/             # Deployment backups (gitignored)
└── vibey                # CLI command
```

**Key Points:**
- ✅ **Committed to Git** - Team sees framework configuration
- ✅ **Never Deleted** - Persistent across sessions
- ✅ **Self-Contained** - All framework state in one place
- ✅ **User-Customizable** - Override templates, add configs

### Modular Config System

Separated configuration into focused files:

**project.yaml** - Project metadata:
```yaml
project:
  name: "MyProject"
  type: "web-app"
  description: "..."
  version: "1.0.0"

tech_stack:
  languages: [python, typescript]
  frameworks: [fastapi, react]
  databases: [postgresql]
```

**framework.yaml** - Framework behavior:
```yaml
orchestration:
  mode: "balanced"
  auto_agent_launch: true

context_loading:
  strategy: "distance_based"
  max_distance: 2
  mode: "summary"
```

**agents/*.yaml** - Agent metadata:
```yaml
agent:
  id: "web-developer"
  name: "Web Developer"
  description: "Full-stack web development"
  triggers:
    keywords: ["frontend", "backend", "api"]
  capabilities:
    - React development
    - API design
```

**Benefits:**
- 🎯 **Focused Concerns** - Each file has single responsibility
- 📦 **Easy to Manage** - Smaller, targeted configs
- 🔄 **Reusable** - Share configs across projects
- ✅ **Validated** - Schema-based validation

---

## 📦 New Components

### Platform Adapters (3 files)

1. **base.py** (456 lines)
   - Abstract base class for all adapters
   - Config loading utilities
   - Template rendering
   - Deployment generation
   - Validation logic

2. **claude_adapter.py** (338 lines)
   - Claude Code-specific implementation
   - Generates CLAUDE.md
   - Generates agents/*.md
   - Generates workflows/*.md
   - Fallback content when templates missing

3. **registry.py** (224 lines)
   - Factory pattern for adapter management
   - Auto-registration of built-in adapters
   - Platform discovery
   - Adapter information

### Python CLI Scripts (3 main commands)

1. **deploy.py** (271 lines)
   - Deploy framework to target platform
   - Platform listing
   - Validation and backup
   - User-friendly output

2. **docs.py** (100+ lines)
   - Generate documentation from config
   - Overwrite control
   - Custom output directories

3. **roadmap.py** (200+ lines)
   - Sprint/task summarization
   - Context loading
   - JSON output support

### Unified CLI Wrapper

**vibey** (bash script, 150+ lines)
- Colored banner
- Command routing
- Help system
- Python dependency checking
- Error handling

---

## 🏗️ Architecture Changes

### Before v1.3.0 (Monolithic)

```
.claude/                 # Everything in one place
├── agents/              # Claude-specific
├── workflows/           # Claude-specific
├── commands/            # Claude-specific
├── CLAUDE.md            # Claude-specific
└── project-config.yaml  # Mixed concerns
```

**Problems:**
- ❌ Locked to Claude Code
- ❌ Can't deploy to other platforms
- ❌ Source and deployment mixed
- ❌ Manual maintenance

### After v1.3.0 (Platform-Agnostic)

```
.vibey/                  # Platform-agnostic source
├── config/              # Pure metadata (YAML)
├── roadmap/             # State tracking
├── sprint_docs/         # Rich context
└── templates/           # User-customizable

.claude/                 # Generated deployment
├── CLAUDE.md            # Auto-generated
├── agents/              # Auto-generated
└── workflows/           # Auto-generated

.goose/                  # Future: Goose deployment
├── README.md            # Auto-generated
├── extensions/          # Auto-generated
└── recipes/             # Auto-generated
```

**Benefits:**
- ✅ Multi-platform support
- ✅ Clean separation of concerns
- ✅ Fast regeneration
- ✅ Version-controlled source

---

## 📝 Documentation Updates

### New Documentation

1. **PLATFORM_AGNOSTIC_ARCHITECTURE.md** (600+ lines)
   - Complete architecture design
   - Source vs deployment separation
   - File purposes and ownership
   - Context loading strategy

2. **PLATFORM_ADAPTER_PATTERN.md** (500+ lines)
   - Adapter development guide
   - Interface documentation
   - Implementation examples
   - Best practices

3. **YAML_MARKDOWN_SEPARATION.md** (400+ lines)
   - Design principle rationale
   - YAML for state, Markdown for context
   - Non-overlapping purposes
   - Integration patterns

4. **RELEASE_NOTES_V1.3.0.md** (this document)
   - Comprehensive release notes
   - Migration guide
   - Breaking changes
   - Upgrade path

### Updated Documentation

1. **README.md** - Completely rewritten
   - Platform-agnostic focus
   - New CLI documentation
   - Updated quick start
   - Architecture overview

2. **CHANGELOG.md** - Added v1.3.0 entry
   - All new features
   - All changes
   - All improvements
   - All fixes

---

## 🔧 Breaking Changes

### Configuration Location

**Before:** `.claude/project-config.yaml`
**After:** `.vibey/config/project.yaml`

**Migration:**
```bash
# Old location (delete after migration)
rm .claude/project-config.yaml

# New location
cp project-config.yaml .vibey/config/project.yaml
```

### Framework Deployment

**Before:** Clone to `.claude/` directly
**After:** Clone to `.vibey/`, deploy to `.claude/`

**Migration:**
```bash
# Old way (deprecated)
git clone https://github.com/fredabood/vibey.git .claude

# New way
git clone https://github.com/fredabood/vibey.git .vibey
cd .vibey
./vibey deploy --platform claude-code
```

### Agent/Workflow Definitions

**Before:** Markdown files with full instructions
**After:** YAML metadata + Jinja2 templates

**Migration:** No action needed for existing deployments. New agents use YAML configs.

---

## 🚀 Migration Guide

### For Existing v1.2 Users

#### Step 1: Backup Current Setup

```bash
# Backup .claude/ directory
cp -r .claude .claude.backup.$(date +%Y%m%d)

# Backup project config
cp .claude/project-config.yaml project-config.backup.yaml
```

#### Step 2: Clone New Framework

```bash
# Clone into .vibey/
git clone https://github.com/fredabood/vibey.git .vibey
```

#### Step 3: Migrate Configuration

```bash
# Create config directory
mkdir -p .vibey/config

# Copy project config
cp project-config.backup.yaml .vibey/config/project.yaml

# Framework will use sensible defaults for new configs
```

#### Step 4: Deploy

```bash
# Deploy to Claude Code
cd .vibey
./vibey deploy --platform claude-code
```

#### Step 5: Verify

```bash
# Check deployment
ls -la .claude/

# Verify CLAUDE.md generated correctly
cat .claude/CLAUDE.md
```

#### Step 6: Update .gitignore

```bash
# Add to .gitignore
echo ".claude/" >> .gitignore
echo ".goose/" >> .gitignore
echo ".cursor/" >> .gitignore
```

### For New Users

```bash
# Navigate to project
cd your-project

# Clone framework
git clone https://github.com/fredabood/vibey.git .vibey

# Deploy
.vibey/vibey deploy --platform claude-code

# Done!
```

---

## 📊 Statistics

### Code Additions

- **New Files:** 50+ files
- **New Lines:** ~5,000 lines
- **Python Code:** ~1,500 lines (adapters + CLI)
- **Documentation:** ~3,500 lines (architecture + guides)

### Component Breakdown

**Platform Adapters:**
- Base adapter: 456 lines
- Claude adapter: 338 lines
- Registry: 224 lines
- **Total:** 1,018 lines

**CLI Scripts:**
- deploy.py: 271 lines
- docs.py: 100+ lines
- roadmap.py: 200+ lines
- **Total:** 570+ lines

**Documentation:**
- Architecture docs: 2,000+ lines
- Release notes: 800+ lines (this file)
- Updated README: 657 lines
- **Total:** 3,500+ lines

---

## 🧪 Testing

### Integration Tests Performed

✅ **Deploy Command:**
- Deploy to Claude Code
- Platform listing
- Validation
- Backup creation
- Overwrite handling

✅ **Docs Command:**
- Documentation generation
- Overwrite mode
- Custom output directory
- Missing file handling

✅ **Roadmap Command:**
- Sprint summarization
- Task summarization
- Context loading
- JSON output

✅ **Platform Adapters:**
- Config loading
- Template rendering
- Fallback content
- Agent generation
- Workflow generation

### Test Results

- ✅ All commands working
- ✅ All adapters functional
- ✅ Deployment generation correct
- ✅ Documentation accurate
- ✅ No regressions found

---

## 🔮 Future Roadmap

### v1.4.0 - Default CLAUDE.md Auto-Generation (Sprint 1)

**Target:** Q1 2025 (2 weeks)

**Features:**
- Auto-generate default CLAUDE.md for new users
- Project type detection
- Tech stack-aware defaults
- Smooth onboarding experience

### v2.0.0 - Goose Platform Support

**Target:** Q2 2025 (2-3 months)

**Features:**
- Goose platform adapter
- Extension generation (TOML format)
- Recipe generation (YAML format)
- MCP ecosystem integration

### v2.1.0 - Cursor Platform Support

**Target:** Q3 2025 (Research + 2-3 months)

**Features:**
- Cursor platform adapter
- .cursorrules generation
- Parallel execution model
- Platform-specific optimizations

---

## 📚 References

### Documentation

- [Platform-Agnostic Architecture](development/PLATFORM_AGNOSTIC_ARCHITECTURE.md)
- [Platform Adapter Pattern](development/PLATFORM_ADAPTER_PATTERN.md)
- [YAML-Markdown Separation](development/YAML_MARKDOWN_SEPARATION.md)
- [README](../README.md)
- [CHANGELOG](../CHANGELOG.md)

### Sprint Documentation

- [Sprint 2 Plan](sprints/core-framework-2-plan.md)
- [Sprint State](.vibey/sprints/core-framework-2.yaml)

---

## 🙏 Acknowledgments

**Contributors:**
- Core architecture design
- Platform adapter implementation
- CLI development
- Documentation writing
- Testing and validation

**Special Thanks:**
- Claude Code team for the amazing platform
- Goose team for architectural inspiration
- Early adopters and feedback providers

---

## 📞 Support

**Issues:**
- GitHub Issues: https://github.com/fredabood/vibey/issues

**Questions:**
- Ask your AI assistant (framework is self-documenting)
- Check the documentation

**Updates:**
- Watch the repository for new releases
- Follow the CHANGELOG

---

**Vibey v1.3.0 - Building the future of platform-agnostic AI orchestration!** 🚀

```bash
# Upgrade today
cd your-project
git clone https://github.com/fredabood/vibey.git .vibey
.vibey/vibey deploy --platform claude-code
```
