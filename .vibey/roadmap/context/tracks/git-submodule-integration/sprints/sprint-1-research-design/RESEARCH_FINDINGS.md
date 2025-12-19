# Git Submodule Integration - Research Findings

**Task:** 01KCMP1YQD3J2M0STQ9FNRKTPT
**Date:** 2025-12-19
**Status:** Complete

---

## 1. Common Patterns for Parent-Child Repo Relationships

### Pattern A: Git Submodules (Static Reference)

Git submodules track a specific commit hash in an external repository:

```
parent-repo/
├── .gitmodules          # Declares submodule locations
├── submodule-a/         # Points to commit abc123
└── submodule-b/         # Points to commit def456
```

**Characteristics:**
- Static tracking (specific commit, not branch)
- Explicit version pinning
- Requires `git submodule update` to sync
- `.gitmodules` file declares relationships

**Source:** [Git Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)

### Pattern B: Git Subtrees (Embedded History)

Git subtrees nest repositories as sub-directories with merged history:

```
parent-repo/
├── subtree-a/           # History merged into parent
└── subtree-b/           # No separate .git
```

**Characteristics:**
- No metadata files (.gitmodules)
- Sub-project code available immediately after clone
- Users don't need to learn submodule commands
- History is merged, not referenced

**Source:** [Atlassian Git Subtree](https://www.atlassian.com/git/tutorials/git-subtree)

### Pattern C: Monorepo (Single Repository)

All code in one repository with internal dependencies:

```
monorepo/
├── packages/
│   ├── core/
│   ├── ui/
│   └── api/
└── package.json         # Workspace definitions
```

**Characteristics:**
- Single source of truth
- Atomic cross-package changes
- Tools: Lerna, Nx, Turborepo, Bazel
- DAG-based dependency tracking

**Source:** [Earthly Blog](https://earthly.dev/blog/monorepo-vs-polyrepo/)

### Pattern D: Polyrepo with Coordination (Multiple Repositories)

Independent repositories with external coordination:

```
org/
├── repo-a/              # Independent releases
├── repo-b/              # References repo-a via version
└── meta-repo/           # Coordination scripts
```

**Characteristics:**
- Independent versioning
- Explicit version dependencies
- Tools: Lyft's refactorator, custom scripts
- Cross-repo PRs harder to coordinate

**Source:** [Endor Labs](https://www.endorlabs.com/learn/polyrepo-vs-monorepo-how-does-it-impact-dependency-management)

---

## 2. How Dependency Management Works Across Repos

### Version Pinning Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Commit SHA** | Pin to exact commit | Stability, reproducibility |
| **Tag/Release** | Pin to semantic version | Production dependencies |
| **Branch tracking** | Follow branch HEAD | Development/integration |
| **Range expressions** | e.g., `^1.2.0` | Flexible minor updates |

### Dependency Graph Models

**DAG (Directed Acyclic Graph):**
- Google's Bazel uses DAG for internal dependencies
- Each node is a build target
- Edges represent dependencies
- Enables incremental builds

**Flat Dependency List:**
- Simple list of (package, version) tuples
- No transitive resolution
- Used by Git submodules

### Cross-Repo Dependency Tools

| Tool | Approach | Strengths |
|------|----------|-----------|
| **Bazel** | DAG tracking, hermetic builds | Google-scale monorepos |
| **Lerna** | Package version management | JavaScript workspaces |
| **Nx** | Affected command, caching | React/Angular monorepos |
| **Pants** | Python-focused, fine-grained | Medium-scale polyrepos |

---

## 3. Sync Strategies: Push-Down vs Pull-Up

### Push-Down (Parent → Child)

**Definition:** Parent repository pushes requirements/changes to child repositories.

**Mechanisms:**
1. **Version bumps** - Parent updates pinned version in submodule
2. **Automated PRs** - Script creates PRs in child repos
3. **Configuration inheritance** - Shared config pushed to children
4. **Requirement specification** - Parent defines what children must implement

**Challenges:**
- Child may reject pushed changes
- Version conflicts between parent expectations and child state
- Ownership ambiguity (who controls child roadmap?)

### Pull-Up (Child → Parent)

**Definition:** Parent repository aggregates information from child repositories.

**Mechanisms:**
1. **Status polling** - Parent queries child for completion state
2. **Webhook notifications** - Child notifies parent on state changes
3. **Progress aggregation** - Parent computes combined metrics
4. **Blocker surfacing** - Child blockers bubble up to parent visibility

**Challenges:**
- Stale data if polling interval too long
- Notification reliability
- Aggregation semantics (how to combine progress?)

### Bidirectional Sync

**Best Practice:** Implement both push-down and pull-up with clear ownership:

```
┌─────────────────────────────────────────────────────┐
│                    PARENT REPO                       │
│  ┌─────────────────────────────────────────────┐    │
│  │ Requirements: "Implement feature X"          │    │
│  │ Aggregated Progress: 75% (3/4 children done) │    │
│  └─────────────────────────────────────────────┘    │
│              │ push-down          ▲ pull-up         │
└──────────────┼────────────────────┼─────────────────┘
               │                    │
    ┌──────────┼──────────┬─────────┼──────────┐
    ▼          ▼          ▼         │          │
┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐
│Child A│  │Child B│  │Child C│  │Child D│
│ Done  │  │ Done  │  │ Done  │  │ WIP   │
└───────┘  └───────┘  └───────┘  └───────┘
```

---

## 4. Relevance to Vibey's Unified Ticket Architecture

### Current State: Triangle Model

```
                     ┌─────────────┐
                     │   Ticket    │
                     └─────────────┘
                    /               \
                   /                 \
      TicketCommitLink          TicketArtifactAssociation
                 /                     \
                /                       \
    ┌─────────────┐               ┌─────────────┐
    │  GitCommit  │───────────────│  Artifact   │
    └─────────────┘               └─────────────┘
                CommitArtifactChange
```

### Extension for Submodules

Each submodule has its own Triangle Model. Cross-repo relationships need:

1. **SubmoduleReference** - Links parent roadmap to submodule roadmap
2. **CrossRepoRequirement** - Push-down from parent Ticket to submodule Ticket
3. **CrossRepoDependency** - Ticket in repo A depends on Ticket in repo B
4. **AggregatedProgress** - Roll-up of submodule metrics to parent

### Proposed Extension: Cross-Repo Triangle

```
PARENT REPO                          SUBMODULE REPO
┌─────────────┐                      ┌─────────────┐
│   Ticket    │─────────────────────▶│   Ticket    │
│   (parent)  │  CrossRepoRequirement│  (derived)  │
└─────────────┘                      └─────────────┘
      │                                    │
      │ TicketArtifactAssociation          │ TicketArtifactAssociation
      ▼                                    ▼
┌─────────────┐                      ┌─────────────┐
│  Artifact   │◀ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│  Artifact   │
│  (shared?)  │  CrossRepoArtifactRef│  (local)    │
└─────────────┘                      └─────────────┘
```

### Key Design Questions (for subsequent tasks)

1. **Discovery:** How to detect `.vibey/roadmap` in submodules?
2. **Identity:** How to reference tickets across repo boundaries?
3. **Sync timing:** Real-time vs polling vs on-demand?
4. **Conflict resolution:** What if parent and child disagree?
5. **Artifact sharing:** Can artifacts exist in multiple repos?

---

## 5. Recommendations

### R1: Use Git Submodules Pattern

Rationale: Static commit references align with reproducibility needs. Vibey can detect via `.gitmodules`.

### R2: Implement Bidirectional Sync

Rationale: Both push-down (requirements) and pull-up (progress) are needed for useful integration.

### R3: Extend Triangle Model

Rationale: Don't create parallel structures. Add cross-repo relationship entities that reference existing Tickets, Artifacts, GitCommits.

### R4: Explicit Ownership Model

Rationale: Define who owns what:
- Parent owns requirements
- Child owns implementation
- Artifacts may be shared with provenance tracking

### R5: Configurable Sync Modes

Rationale: Different teams need different levels of coupling:
- **Tight:** Real-time sync, blocking dependencies
- **Loose:** Polling, advisory dependencies
- **Manual:** On-demand sync only

---

## Sources

- [Git Documentation - Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Atlassian Git Subtree](https://www.atlassian.com/git/tutorials/git-subtree)
- [Earthly Blog - Monorepo vs Polyrepo](https://earthly.dev/blog/monorepo-vs-polyrepo/)
- [Endor Labs - Dependency Management](https://www.endorlabs.com/learn/polyrepo-vs-monorepo-how-does-it-impact-dependency-management)
- [Developer Nation - Git Submodules](https://www.developernation.net/blog/how-git-submodules-can-save-you-time-and-headaches-taming-the-dependency-beast/)
