# Submodule Detection and Discovery Design

**Task:** 01KCMP26A493MCX37CVRG8YSM0
**Date:** 2025-12-19
**Status:** Complete

---

## Overview

This document defines how Vibey detects and discovers git submodules within a repository, and identifies which submodules have their own `.vibey/roadmap` directories.

---

## 1. Detection Mechanisms

### 1.1 Primary: .gitmodules Parsing

Git stores submodule configuration in `.gitmodules` at repository root.

**Format:**
```ini
[submodule "libs/auth"]
    path = libs/auth
    url = git@github.com:org/auth-lib.git

[submodule "libs/ui"]
    path = libs/ui
    url = git@github.com:org/ui-components.git
```

**Parsing Strategy:**
```python
def parse_gitmodules(repo_root: Path) -> List[SubmoduleEntry]:
    """Parse .gitmodules file to extract submodule definitions."""
    gitmodules_path = repo_root / ".gitmodules"
    if not gitmodules_path.exists():
        return []

    config = configparser.ConfigParser()
    config.read(gitmodules_path)

    submodules = []
    for section in config.sections():
        if section.startswith("submodule "):
            name = section.replace('submodule "', '').rstrip('"')
            submodules.append(SubmoduleEntry(
                name=name,
                path=config.get(section, "path"),
                url=config.get(section, "url"),
            ))
    return submodules
```

### 1.2 Secondary: Git Submodule Command

For validation and additional metadata:

```bash
git submodule status
```

**Output:**
```
 abc1234 libs/auth (v1.2.0)
-def5678 libs/ui (heads/main)
+ghi9012 libs/api (v2.0.0-dirty)
```

**Status prefixes:**
- ` ` (space): Submodule initialized and at recorded commit
- `-`: Submodule not initialized
- `+`: Submodule at different commit than recorded
- `U`: Submodule has merge conflicts

### 1.3 Fallback: Directory Scanning

If `.gitmodules` parsing fails, scan for nested `.git` directories:

```python
def scan_for_submodules(repo_root: Path) -> List[Path]:
    """Fallback: find directories with .git that aren't the root."""
    submodule_paths = []
    for git_dir in repo_root.rglob(".git"):
        if git_dir.parent != repo_root:
            submodule_paths.append(git_dir.parent)
    return submodule_paths
```

---

## 2. Discovery: Finding Vibey-Enabled Submodules

### 2.1 Roadmap Detection

After identifying submodules, check for Vibey roadmap:

```python
def has_vibey_roadmap(submodule_path: Path) -> bool:
    """Check if submodule has a Vibey roadmap."""
    roadmap_indicators = [
        submodule_path / ".vibey" / "roadmap",
        submodule_path / ".vibey" / "roadmap.yaml",
        submodule_path / ".vibey" / "roadmap" / "roadmap.yaml",
    ]
    return any(indicator.exists() for indicator in roadmap_indicators)
```

### 2.2 SubmoduleReference Entity

**Integration with Unified Ticket Architecture:**

```python
@dataclass
class SubmoduleReference:
    """Links parent roadmap to submodule roadmap."""
    id: str                          # ULID
    parent_roadmap_id: str           # Parent's roadmap ID
    submodule_path: str              # Relative path from parent root
    submodule_url: str               # Git URL
    submodule_commit: Optional[str]  # Pinned commit SHA
    submodule_roadmap_id: Optional[str]  # Submodule's roadmap ID (if detected)

    # Detection metadata
    detected_at: datetime
    detection_source: DetectionSource  # GITMODULES | GIT_COMMAND | DIRECTORY_SCAN
    has_vibey_roadmap: bool

    # Sync state
    last_synced_at: Optional[datetime]
    sync_status: SyncStatus  # SYNCED | STALE | NEVER_SYNCED | ERROR

class DetectionSource(Enum):
    GITMODULES = "gitmodules"
    GIT_COMMAND = "git_command"
    DIRECTORY_SCAN = "directory_scan"
    MANUAL = "manual"

class SyncStatus(Enum):
    SYNCED = "synced"
    STALE = "stale"
    NEVER_SYNCED = "never_synced"
    ERROR = "error"
```

---

## 3. Discovery Process Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SUBMODULE DISCOVERY FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 1: Parse .gitmodules                                           │
│    • Read [submodule "name"] sections                                │
│    • Extract path, url for each                                      │
│    • Create SubmoduleEntry records                                   │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 2: Validate with git submodule status                          │
│    • Get current commit SHA for each                                 │
│    • Detect initialization state                                     │
│    • Flag dirty/diverged submodules                                  │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 3: Check for Vibey roadmaps                                    │
│    For each submodule:                                               │
│      • Check .vibey/roadmap exists                                   │
│      • If exists, read roadmap.yaml for roadmap_id                   │
│      • Set has_vibey_roadmap flag                                    │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 4: Build SubmoduleRegistry                                     │
│    • Create SubmoduleReference for each                              │
│    • Store in parent's .vibey/roadmap/submodules/                    │
│    • Index by path and roadmap_id                                    │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 5: Persist to SQLite                                           │
│    • Add submodule_references table                                  │
│    • Enable cross-repo queries                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Storage Structure

### 4.1 YAML Storage

```
.vibey/roadmap/
├── submodules/
│   ├── .registry.yaml           # List of all submodule references
│   ├── libs-auth.yaml           # SubmoduleReference for libs/auth
│   └── libs-ui.yaml             # SubmoduleReference for libs/ui
```

**Example .registry.yaml:**
```yaml
submodule_registry:
  parent_roadmap_id: vibey-framework-v2
  discovered_at: '2025-12-19T19:00:00+00:00'
  submodules:
    - id: 01KCX_SUBMOD_AUTH
      path: libs/auth
      has_vibey_roadmap: true
    - id: 01KCX_SUBMOD_UI
      path: libs/ui
      has_vibey_roadmap: false
```

### 4.2 SQLite Schema

```sql
CREATE TABLE submodule_references (
    id TEXT PRIMARY KEY,
    parent_roadmap_id TEXT NOT NULL,
    submodule_path TEXT NOT NULL,
    submodule_url TEXT,
    submodule_commit TEXT,
    submodule_roadmap_id TEXT,
    detected_at TEXT NOT NULL,
    detection_source TEXT NOT NULL,
    has_vibey_roadmap INTEGER NOT NULL DEFAULT 0,
    last_synced_at TEXT,
    sync_status TEXT NOT NULL DEFAULT 'never_synced',

    UNIQUE(parent_roadmap_id, submodule_path)
);

CREATE INDEX idx_submodule_refs_parent ON submodule_references(parent_roadmap_id);
CREATE INDEX idx_submodule_refs_roadmap ON submodule_references(submodule_roadmap_id);
```

---

## 5. API Design

### 5.1 SubmoduleDiscovery Class

```python
class SubmoduleDiscovery:
    """Discovers and tracks git submodules with Vibey roadmaps."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.registry: Dict[str, SubmoduleReference] = {}

    def discover(self) -> List[SubmoduleReference]:
        """Run full discovery process."""
        entries = self._parse_gitmodules()
        entries = self._validate_with_git(entries)

        references = []
        for entry in entries:
            ref = self._create_reference(entry)
            ref.has_vibey_roadmap = self._check_vibey_roadmap(entry.path)
            if ref.has_vibey_roadmap:
                ref.submodule_roadmap_id = self._read_roadmap_id(entry.path)
            references.append(ref)
            self.registry[entry.path] = ref

        return references

    def get_vibey_submodules(self) -> List[SubmoduleReference]:
        """Return only submodules with Vibey roadmaps."""
        return [ref for ref in self.registry.values() if ref.has_vibey_roadmap]

    def refresh(self, path: str) -> SubmoduleReference:
        """Refresh discovery for a specific submodule."""
        # Re-run discovery for single submodule
        pass
```

### 5.2 CLI Commands

```bash
# List all detected submodules
vibey submodule list
# Output:
# PATH          URL                              VIBEY    STATUS
# libs/auth     git@github.com:org/auth.git      ✓        synced
# libs/ui       git@github.com:org/ui.git        ✗        n/a
# libs/api      git@github.com:org/api.git       ✓        stale

# Refresh discovery
vibey submodule discover
# Re-parses .gitmodules and checks for roadmaps

# Show details for specific submodule
vibey submodule show libs/auth
# Shows SubmoduleReference details + roadmap summary if available
```

### 5.3 MCP Tools

```python
@mcp_tool
def submodule_list() -> List[SubmoduleInfo]:
    """List all detected submodules and their Vibey status."""
    pass

@mcp_tool
def submodule_discover() -> DiscoveryResult:
    """Run submodule discovery and return findings."""
    pass

@mcp_tool
def submodule_roadmap(path: str) -> RoadmapSummary:
    """Get roadmap summary for a Vibey-enabled submodule."""
    pass
```

---

## 6. Configuration

### 6.1 Discovery Settings

```yaml
# .vibey/config/submodules.yaml
submodule_discovery:
  enabled: true

  # Auto-discover on these events
  auto_discover:
    on_init: true           # Run discovery when `vibey init` runs
    on_roadmap_status: true # Run discovery when checking roadmap status
    on_git_pull: false      # Run after git pull (via hook)

  # Detection methods (in priority order)
  detection_methods:
    - gitmodules
    - git_command
    # - directory_scan  # Disabled by default (slow)

  # Filter which submodules to include
  include_patterns:
    - "libs/*"
    - "packages/*"
  exclude_patterns:
    - "vendor/*"
    - "third_party/*"
```

---

## 7. Implementation Guidance

### 7.1 File Locations

| Component | Location |
|-----------|----------|
| SubmoduleReference model | `vibey/roadmap/models/submodule.py` |
| SubmoduleDiscovery class | `vibey/operations/submodule/discovery.py` |
| CLI commands | `vibey/cli/submodule.py` |
| MCP tools | `vibey/mcp/tools/submodule.py` |
| SQLite schema | `vibey/roadmap/serialization/sql_schema.py` |
| Config schema | `vibey/config/schemas/submodules.py` |

### 7.2 Dependencies

- `configparser` (stdlib) - Parse .gitmodules
- `subprocess` - Run `git submodule status`
- Existing `vibey.roadmap.serialization` - YAML/SQLite persistence

### 7.3 Error Handling

| Error | Handling |
|-------|----------|
| .gitmodules not found | Return empty list (not an error) |
| Submodule not initialized | Mark as `status=not_initialized` |
| .vibey/roadmap unreadable | Mark `has_vibey_roadmap=False`, log warning |
| Git command fails | Fall back to directory scan |

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
def test_parse_gitmodules_empty():
    """Empty .gitmodules returns empty list."""

def test_parse_gitmodules_single():
    """Single submodule parsed correctly."""

def test_parse_gitmodules_multiple():
    """Multiple submodules parsed correctly."""

def test_has_vibey_roadmap_true():
    """Detect existing .vibey/roadmap directory."""

def test_has_vibey_roadmap_false():
    """Return False when no .vibey/roadmap exists."""
```

### 8.2 Integration Tests

```python
def test_full_discovery_flow():
    """End-to-end discovery with mock submodule repos."""

def test_discovery_persists_to_sqlite():
    """SubmoduleReferences stored in database."""
```

---

## Next Steps

1. → Task 3: Design push-down mechanism (uses SubmoduleReference)
2. → Task 4: Design pull-up mechanism (queries submodule roadmaps)
3. → Task 5: Design cross-repo dependencies (extends Triangle Model)
