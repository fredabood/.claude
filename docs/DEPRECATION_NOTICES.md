# Deprecation Notices

**Version:** 2.5.0
**Last Updated:** 2025-11-10

This document tracks deprecated features in the Vibey framework.

---

## Active Deprecations

### Legacy Monolithic Config (`.claude/project-config.yaml`)

**Status:** Deprecated in v2.5.0
**Removal:** Planned for v3.0.0
**Replacement:** Modular config in `.vibey/config/`

**What's deprecated:**
- Single file `.claude/project-config.yaml`
- Monolithic YAML structure

**Migration path:**
```bash
# Automatic migration
vibey config migrate

# Verify migration
vibey config validate

# Remove legacy file (optional)
rm .claude/project-config.yaml
```

**Backward compatibility:**
- ✅ Legacy format still works (until v3.0.0)
- ✅ Automatic fallback in config loader
- ⚠️ Deprecation warnings shown when loading legacy config
- ✅ Migration tool available (`vibey config migrate`)

**Why deprecated:**
The monolithic config mixed concerns (project info, framework settings, agents, quality gates) in one file. The new modular format:
- Separates concerns (4 focused files)
- Easier to understand and edit
- Better validation
- Clearer organization

**Timeline:**
- **v2.5.0** (Nov 2025): Modular config introduced, legacy deprecated
- **v2.6.0-2.9.0**: Both formats supported, migration encouraged
- **v3.0.0** (Est. Q2 2026): Legacy format removed

---

## Future Deprecations

### Framework Scripts in `framework/scripts/`

**Status:** Under review
**Planned:** v2.6.0
**Replacement:** `vibey` CLI commands

Many scripts in `framework/scripts/` will be deprecated in favor of unified CLI:
- `generate-config.py` → `vibey config generate`
- `update-config.py` → `vibey config update`
- `roadmap-*.py` → `vibey roadmap *`

Migration guides will be provided when deprecation is formalized.

---

## Removed Features

None yet (v2.5.0 is first release with deprecations).

---

## Deprecation Policy

### Levels

**Level 1: Soft Deprecation**
- Feature works normally
- Documentation updated to show new way
- No warnings shown

**Level 2: Active Deprecation** (Current: Legacy config)
- Feature still works
- Deprecation warnings shown
- Documentation shows migration path
- Minimum 6 months before removal

**Level 3: Removal Planned**
- Strong warnings
- Migration tool available
- Timeline announced
- 3 months notice before removal

**Level 4: Removed**
- Feature no longer works
- Clear error message with migration guide
- Legacy support may remain in older versions

### Warning Format

Deprecation warnings follow this format:

```
DeprecationWarning: [Feature] is deprecated since v[X.Y.Z].

  What: [Brief description of deprecated feature]
  Why: [Reason for deprecation]
  Migration: [How to migrate]
  Removal: Planned for v[X.Y.Z]

  Learn more: [URL to migration guide]
```

### Backward Compatibility Promise

- **Deprecated features work** until explicitly removed
- **Minimum 6 months** between deprecation and removal
- **Migration tools provided** for complex changes
- **Clear documentation** for all migrations
- **Semantic versioning** (breaking changes = major version bump)

---

## How to Handle Deprecation Warnings

### In Development

```bash
# See all warnings
python3 -W default script.py

# Treat warnings as errors (strict mode)
python3 -W error script.py

# Suppress specific warnings (not recommended)
python3 -W ignore::DeprecationWarning script.py
```

### In Code

```python
import warnings

# See deprecation warnings
warnings.simplefilter('always', DeprecationWarning)

# Suppress specific warnings (not recommended)
warnings.filterwarnings('ignore', category=DeprecationWarning,
                       message='.*legacy config.*')
```

### Best Practice

**Don't suppress deprecation warnings!**

Instead:
1. Read the warning message
2. Follow the migration guide
3. Update your code/config
4. Verify warnings are gone

---

## Migration Support

### Resources

- **Migration guides:** `docs/development/CONFIG_MIGRATION_GUIDE.md`
- **CLI help:** `vibey config migrate --help`
- **Issue tracker:** Report migration issues on GitHub

### Getting Help

If you encounter issues migrating:

1. Check the migration guide
2. Run with `--dry-run` to preview changes
3. Check existing issues on GitHub
4. Create new issue with:
   - Vibey version
   - Error message
   - Config file content (if applicable)

---

## Staying Updated

### Check for Deprecations

```bash
# Check your config for deprecated features
vibey config validate

# See all framework deprecations
vibey --version --verbose
```

### Release Notes

Always review release notes when upgrading:
- **CHANGELOG.md** - Detailed changes
- **RELEASE_NOTES_*.md** - Version highlights
- **GitHub Releases** - Official announcements

---

**Questions?** See `docs/development/CONFIG_MIGRATION_GUIDE.md` or open a GitHub issue.
