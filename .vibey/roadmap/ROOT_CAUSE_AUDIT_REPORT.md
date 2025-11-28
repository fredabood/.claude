# Root Cause Audit Report

**Total Discrepancies:** 122
**Needs Human Review:** 118

## Summary by Root Cause

| Root Cause | Count | Needs Review |
|------------|-------|--------------|
| yaml_counter_drift | 57 | 53 |
| status_not_updated | 39 | 39 |
| extra_task_files | 14 | 14 |
| extra_sprint_dirs | 12 | 12 |

## Roadmap Discrepancies (7)

### 🟠 vibey-framework-v2: progress.tracks_total 

**Computed:** `36`
**Declared:** `35`
**Root Cause:** yaml_counter_drift
**Confidence:** high

**Evidence:**
- Computed progress.tracks_total=36 from actual files
- Declared progress.tracks_total=35 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.tracks_total from 35 to 36

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

### 🟠 vibey-framework-v2: progress.sprints_total 

**Computed:** `172`
**Declared:** `100`
**Root Cause:** yaml_counter_drift
**Confidence:** high

**Evidence:**
- Computed progress.sprints_total=172 from actual files
- Declared progress.sprints_total=100 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.sprints_total from 100 to 172

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

### 🟠 vibey-framework-v2: progress.tasks_total 

**Computed:** `862`
**Declared:** `482`
**Root Cause:** yaml_counter_drift
**Confidence:** high

**Evidence:**
- Computed progress.tasks_total=862 from actual files
- Declared progress.tasks_total=482 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.tasks_total from 482 to 862

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

### 🟡 vibey-framework-v2: progress.tracks_completed ⚠️ NEEDS REVIEW

**Computed:** `18`
**Declared:** `20`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tracks_completed=18 from actual files
- Declared progress.tracks_completed=20 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.tracks_completed from 20 to 18

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

### 🟡 vibey-framework-v2: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `81`
**Declared:** `45`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=81 from actual files
- Declared progress.sprints_completed=45 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.sprints_completed from 45 to 81

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

### 🟡 vibey-framework-v2: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `574`
**Declared:** `338`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=574 from actual files
- Declared progress.tasks_completed=338 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.tasks_completed from 338 to 574

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

### 🟢 vibey-framework-v2: progress.completion_percent 

**Computed:** `66.6`
**Declared:** `70.0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.completion_percent=66.6 from actual files
- Declared progress.completion_percent=70.0 in roadmap.yaml

**Suggested Fix:** Update roadmap.yaml progress.completion_percent from 70.0 to 66.6

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap.yaml`

---

## Track Discrepancies (58)

### 🟠 aider-port: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** low

**Evidence:**
- Computed status 'completed' based on sprint statuses
- Sprint statuses: ['aider-port-1: completed']...
- Declared status in track.yaml: 'in_progress'

**Suggested Fix:** Review track 'aider-port' - is status 'in_progress' or 'completed' correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/aider-port/track.yaml`

---

### 🟠 cody-port: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** low

**Evidence:**
- Computed status 'not_started' based on sprint statuses
- Sprint statuses: ['cody-port-2: not_started', 'cody-port-1: not_started']...
- Declared status in track.yaml: 'in_progress'

**Suggested Fix:** Review track 'cody-port' - is status 'in_progress' or 'not_started' correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/cody-port/track.yaml`

---

### 🟠 cody-port: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `10`
**Declared:** `6`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 10 task.yaml files in cody-port/
- Declared tasks_total=6 in track.yaml
- Extra 4 task files found

**Suggested Fix:** Review: Are all 10 tasks in cody-port/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/cody-port/track.yaml`

---

### 🟠 directory-consolidation: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `5`
**Declared:** `0`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'directory-consolidation-3', 'directory-consolidation-5', 'directory-consolidation-4', 'directory-consolidation-2', 'directory-consolidation-1'}

**Suggested Fix:** Review if sprints {'directory-consolidation-3', 'directory-consolidation-5', 'directory-consolidation-4', 'directory-consolidation-2', 'directory-consolidation-1'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-3/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-5/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-4/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-2/sprint.yaml`
- ... and 1 more

---

### 🟠 directory-consolidation: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `23`
**Declared:** `0`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 23 task.yaml files in directory-consolidation/
- Declared tasks_total=0 in track.yaml
- Extra 23 task files found

**Suggested Fix:** Review: Are all 23 tasks in directory-consolidation/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/track.yaml`

---

### 🟠 documentation-system: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `1`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'documentation-system-3', 'documentation-system-2'}

**Suggested Fix:** Review if sprints {'documentation-system-3', 'documentation-system-2'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/documentation-system-3/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/documentation-system-2/sprint.yaml`

---

### 🟠 documentation-system: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `19`
**Declared:** `8`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 19 task.yaml files in documentation-system/
- Declared tasks_total=8 in track.yaml
- Extra 11 task files found

**Suggested Fix:** Review: Are all 19 tasks in documentation-system/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/track.yaml`

---

### 🟠 gemini-port: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** low

**Evidence:**
- Computed status 'not_started' based on sprint statuses
- Sprint statuses: ['gemini-port-5: not_started', 'gemini-port-2: not_started', 'gemini-port-3: not_started', 'gemini-port-4: not_started', 'gemini-port-1: not_started']...
- Declared status in track.yaml: 'completed'

**Suggested Fix:** Review track 'gemini-port' - is status 'completed' or 'not_started' correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/track.yaml`

---

### 🟠 gemini-port: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `1`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'gemini-port-3', 'gemini-port-5', 'gemini-port-6', 'gemini-port-2', 'gemini-port-1'}

**Suggested Fix:** Review if sprints {'gemini-port-3', 'gemini-port-5', 'gemini-port-6', 'gemini-port-2', 'gemini-port-1'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-3/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-5/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-6/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-2/sprint.yaml`
- ... and 1 more

---

### 🟠 gemini-port: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `32`
**Declared:** `5`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 32 task.yaml files in gemini-port/
- Declared tasks_total=5 in track.yaml
- Extra 27 task files found

**Suggested Fix:** Review: Are all 32 tasks in gemini-port/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/track.yaml`

---

### 🟠 git-integration: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `5`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'git-integration-5'}

**Suggested Fix:** Review if sprints {'git-integration-5'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/git-integration/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/git-integration/git-integration-5/sprint.yaml`

---

### 🟠 git-integration: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `63`
**Declared:** `41`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 63 task.yaml files in git-integration/
- Declared tasks_total=41 in track.yaml
- Extra 22 task files found

**Suggested Fix:** Review: Are all 63 tasks in git-integration/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/git-integration/track.yaml`

---

### 🟠 infrastructure-fixes: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `20`
**Declared:** `13`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 20 task.yaml files in infrastructure-fixes/
- Declared tasks_total=13 in track.yaml
- Extra 7 task files found

**Suggested Fix:** Review: Are all 20 tasks in infrastructure-fixes/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/infrastructure-fixes/track.yaml`

---

### 🟠 interface-unification: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `0`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'interface-unification-1', 'interface-unification-2', 'interface-unification-3'}

**Suggested Fix:** Review if sprints {'interface-unification-1', 'interface-unification-2', 'interface-unification-3'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/interface-unification/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/interface-unification/interface-unification-1/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/interface-unification/interface-unification-2/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/interface-unification/interface-unification-3/sprint.yaml`

---

### 🟠 missing-agents: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'missing-agents-1'}

**Suggested Fix:** Review if sprints {'missing-agents-1'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/missing-agents/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/missing-agents/missing-agents-1/sprint.yaml`

---

### 🟠 missing-agents: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `11`
**Declared:** `0`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 11 task.yaml files in missing-agents/
- Declared tasks_total=0 in track.yaml
- Extra 11 task files found

**Suggested Fix:** Review: Are all 11 tasks in missing-agents/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/missing-agents/track.yaml`

---

### 🟠 multi-platform: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `1`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'multi-platform-3', 'multi-platform-1'}

**Suggested Fix:** Review if sprints {'multi-platform-3', 'multi-platform-1'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/multi-platform/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/multi-platform/multi-platform-3/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/multi-platform/multi-platform-1/sprint.yaml`

---

### 🟠 multi-platform: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `12`
**Declared:** `6`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 12 task.yaml files in multi-platform/
- Declared tasks_total=6 in track.yaml
- Extra 6 task files found

**Suggested Fix:** Review: Are all 12 tasks in multi-platform/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/multi-platform/track.yaml`

---

### 🟠 platform-context-management: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `5`
**Declared:** `1`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'platform-context-management-2', 'platform-context-management-1', 'platform-context-management-4', 'platform-context-management-3'}

**Suggested Fix:** Review if sprints {'platform-context-management-2', 'platform-context-management-1', 'platform-context-management-4', 'platform-context-management-3'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/platform-context-management-2/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/platform-context-management-1/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/platform-context-management-4/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/platform-context-management-3/sprint.yaml`

---

### 🟠 platform-context-management: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `29`
**Declared:** `6`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 29 task.yaml files in platform-context-management/
- Declared tasks_total=6 in track.yaml
- Extra 23 task files found

**Suggested Fix:** Review: Are all 29 tasks in platform-context-management/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/track.yaml`

---

### 🟠 roadmap-integrity-fixes: status ⚠️ NEEDS REVIEW

**Computed:** `in_progress`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** low

**Evidence:**
- Computed status 'in_progress' based on sprint statuses
- Sprint statuses: ['roadmap-integrity-fixes-8: completed', 'roadmap-integrity-fixes-6: completed', 'roadmap-integrity-fixes-1: completed', 'roadmap-integrity-fixes-0: completed', 'roadmap-integrity-fixes-7: completed']...
- Declared status in track.yaml: 'completed'

**Suggested Fix:** Review track 'roadmap-integrity-fixes' - is status 'completed' or 'in_progress' correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/track.yaml`

---

### 🟠 roadmap-integrity-fixes: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `12`
**Declared:** `8`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'roadmap-integrity-fixes-9', 'roadmap-integrity-fixes-1', 'roadmap-integrity-fixes-0', 'roadmap-integrity-fixes-11'}

**Suggested Fix:** Review if sprints {'roadmap-integrity-fixes-9', 'roadmap-integrity-fixes-1', 'roadmap-integrity-fixes-0', 'roadmap-integrity-fixes-11'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/roadmap-integrity-fixes-9/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/roadmap-integrity-fixes-1/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/roadmap-integrity-fixes-0/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/roadmap-integrity-fixes-11/sprint.yaml`

---

### 🟠 roadmap-integrity-fixes: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `82`
**Declared:** `66`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 82 task.yaml files in roadmap-integrity-fixes/
- Declared tasks_total=66 in track.yaml
- Extra 16 task files found

**Suggested Fix:** Review: Are all 82 tasks in roadmap-integrity-fixes/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/track.yaml`

---

### 🟠 roadmap-integrity-fixes-2: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** low

**Evidence:**
- Computed status 'not_started' based on sprint statuses
- Sprint statuses: ['roadmap-integrity-fixes-2-3: not_started', 'roadmap-integrity-fixes-2-4: not_started', 'roadmap-integrity-fixes-2-5: not_started', 'roadmap-integrity-fixes-2-2: not_started', 'roadmap-integrity-fixes-2-1: not_started']...
- Declared status in track.yaml: 'completed'

**Suggested Fix:** Review track 'roadmap-integrity-fixes-2' - is status 'completed' or 'not_started' correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes-2/track.yaml`

---

### 🟠 roadmap-state-audit: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** low

**Evidence:**
- Computed status 'not_started' based on sprint statuses
- Sprint statuses: ['roadmap-state-audit-11: not_started', 'roadmap-state-audit-16: not_started', 'roadmap-state-audit-20: not_started', 'roadmap-state-audit-18: not_started', 'roadmap-state-audit-27: in_progress']...
- Declared status in track.yaml: 'in_progress'

**Suggested Fix:** Review track 'roadmap-state-audit' - is status 'in_progress' or 'not_started' correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/track.yaml`

---

### 🟠 roadmap-state-audit: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `28`
**Declared:** `0`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'roadmap-state-audit-17', 'roadmap-state-audit-15', 'roadmap-state-audit-22', 'roadmap-state-audit-8', 'roadmap-state-audit-11', 'roadmap-state-audit-21', 'roadmap-state-audit-24', 'roadmap-state-audit-3', 'roadmap-state-audit-10', 'roadmap-state-audit-7', 'roadmap-state-audit-9', 'roadmap-state-audit-2', 'roadmap-state-audit-20', 'roadmap-state-audit-28', 'roadmap-state-audit-4', 'roadmap-state-audit-23', 'roadmap-state-audit-16', 'roadmap-state-audit-12', 'roadmap-state-audit-6', 'roadmap-state-audit-26', 'roadmap-state-audit-13', 'roadmap-state-audit-25', 'roadmap-state-audit-27', 'roadmap-state-audit-18', 'roadmap-state-audit-19', 'roadmap-state-audit-5', 'roadmap-state-audit-14', 'roadmap-state-audit-1'}

**Suggested Fix:** Review if sprints {'roadmap-state-audit-17', 'roadmap-state-audit-15', 'roadmap-state-audit-22', 'roadmap-state-audit-8', 'roadmap-state-audit-11', 'roadmap-state-audit-21', 'roadmap-state-audit-24', 'roadmap-state-audit-3', 'roadmap-state-audit-10', 'roadmap-state-audit-7', 'roadmap-state-audit-9', 'roadmap-state-audit-2', 'roadmap-state-audit-20', 'roadmap-state-audit-28', 'roadmap-state-audit-4', 'roadmap-state-audit-23', 'roadmap-state-audit-16', 'roadmap-state-audit-12', 'roadmap-state-audit-6', 'roadmap-state-audit-26', 'roadmap-state-audit-13', 'roadmap-state-audit-25', 'roadmap-state-audit-27', 'roadmap-state-audit-18', 'roadmap-state-audit-19', 'roadmap-state-audit-5', 'roadmap-state-audit-14', 'roadmap-state-audit-1'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-17/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-15/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-22/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-8/sprint.yaml`
- ... and 24 more

---

### 🟠 roadmap-state-audit: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `83`
**Declared:** `0`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 83 task.yaml files in roadmap-state-audit/
- Declared tasks_total=0 in track.yaml
- Extra 83 task files found

**Suggested Fix:** Review: Are all 83 tasks in roadmap-state-audit/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/track.yaml`

---

### 🟠 roadmap-system: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `7`
**Declared:** `1`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'roadmap-system-5', 'roadmap-system-1', 'roadmap-system-6', 'roadmap-system-2', 'roadmap-system-4', 'roadmap-system-3'}

**Suggested Fix:** Review if sprints {'roadmap-system-5', 'roadmap-system-1', 'roadmap-system-6', 'roadmap-system-2', 'roadmap-system-4', 'roadmap-system-3'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/roadmap-system-5/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/roadmap-system-1/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/roadmap-system-6/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/roadmap-system-2/sprint.yaml`
- ... and 2 more

---

### 🟠 roadmap-system: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `58`
**Declared:** `5`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 58 task.yaml files in roadmap-system/
- Declared tasks_total=5 in track.yaml
- Extra 53 task files found

**Suggested Fix:** Review: Are all 58 tasks in roadmap-system/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/track.yaml`

---

### 🟠 sqlite-backend: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `37`
**Declared:** `36`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 37 task.yaml files in sqlite-backend/
- Declared tasks_total=36 in track.yaml
- Extra 1 task files found

**Suggested Fix:** Review: Are all 37 tasks in sqlite-backend/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/sqlite-backend/track.yaml`

---

### 🟠 standards-system: progress.sprints_total ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `0`
**Root Cause:** extra_sprint_dirs
**Confidence:** medium

**Evidence:**
- Sprint directories exist but not in track.yaml sprints list: {'standards-system-3', 'standards-system-1', 'standards-system-5', 'standards-system-2', 'standards-system-4', 'standards-system-6'}

**Suggested Fix:** Review if sprints {'standards-system-3', 'standards-system-1', 'standards-system-5', 'standards-system-2', 'standards-system-4', 'standards-system-6'} should be added to track.yaml or deleted

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/track.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/standards-system-3/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/standards-system-1/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/standards-system-5/sprint.yaml`
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/standards-system-2/sprint.yaml`
- ... and 2 more

---

### 🟠 standards-system: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `51`
**Declared:** `0`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 51 task.yaml files in standards-system/
- Declared tasks_total=0 in track.yaml
- Extra 51 task files found

**Suggested Fix:** Review: Are all 51 tasks in standards-system/ valid, or should some be deleted?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/track.yaml`

---

### 🟡 core-framework: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=2
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for core-framework

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/core-framework/track.yaml`

---

### 🟡 directory-consolidation: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `5`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=5
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for directory-consolidation

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/track.yaml`

---

### 🟡 directory-consolidation: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `23`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=23
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for directory-consolidation

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/track.yaml`

---

### 🟡 documentation-system: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=3
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for documentation-system

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/track.yaml`

---

### 🟡 documentation-system: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `19`
**Declared:** `8`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=19
- Declared progress.tasks_completed=8

**Suggested Fix:** Review progress.tasks_completed for documentation-system

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/track.yaml`

---

### 🟡 gemini-port: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `0`
**Declared:** `1`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=0
- Declared progress.sprints_completed=1

**Suggested Fix:** Review progress.sprints_completed for gemini-port

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/track.yaml`

---

### 🟡 infrastructure-fixes: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `1`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=2
- Declared progress.sprints_completed=1

**Suggested Fix:** Review progress.sprints_completed for infrastructure-fixes

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/infrastructure-fixes/track.yaml`

---

### 🟡 infrastructure-fixes: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `20`
**Declared:** `13`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=20
- Declared progress.tasks_completed=13

**Suggested Fix:** Review progress.tasks_completed for infrastructure-fixes

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/infrastructure-fixes/track.yaml`

---

### 🟡 interface-unification: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=3
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for interface-unification

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/interface-unification/track.yaml`

---

### 🟡 mcp-server: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=2
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for mcp-server

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/mcp-server/track.yaml`

---

### 🟡 missing-agents: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=1
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for missing-agents

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/missing-agents/track.yaml`

---

### 🟡 missing-agents: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `11`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=11
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for missing-agents

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/missing-agents/track.yaml`

---

### 🟡 multi-platform: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `1`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=3
- Declared progress.sprints_completed=1

**Suggested Fix:** Review progress.sprints_completed for multi-platform

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/multi-platform/track.yaml`

---

### 🟡 multi-platform: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `12`
**Declared:** `6`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=12
- Declared progress.tasks_completed=6

**Suggested Fix:** Review progress.tasks_completed for multi-platform

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/multi-platform/track.yaml`

---

### 🟡 platform-context-management: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `5`
**Declared:** `1`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=5
- Declared progress.sprints_completed=1

**Suggested Fix:** Review progress.sprints_completed for platform-context-management

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/track.yaml`

---

### 🟡 platform-context-management: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `29`
**Declared:** `6`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=29
- Declared progress.tasks_completed=6

**Suggested Fix:** Review progress.tasks_completed for platform-context-management

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/platform-context-management/track.yaml`

---

### 🟡 roadmap-integrity-fixes: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `11`
**Declared:** `8`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=11
- Declared progress.sprints_completed=8

**Suggested Fix:** Review progress.sprints_completed for roadmap-integrity-fixes

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/track.yaml`

---

### 🟡 roadmap-integrity-fixes: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `81`
**Declared:** `66`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=81
- Declared progress.tasks_completed=66

**Suggested Fix:** Review progress.tasks_completed for roadmap-integrity-fixes

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/track.yaml`

---

### 🟡 roadmap-integrity-fixes-2: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `0`
**Declared:** `4`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=0
- Declared progress.sprints_completed=4

**Suggested Fix:** Review progress.sprints_completed for roadmap-integrity-fixes-2

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes-2/track.yaml`

---

### 🟡 roadmap-state-audit: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `14`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=14
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for roadmap-state-audit

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/track.yaml`

---

### 🟡 roadmap-system: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `7`
**Declared:** `1`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=7
- Declared progress.sprints_completed=1

**Suggested Fix:** Review progress.sprints_completed for roadmap-system

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/track.yaml`

---

### 🟡 roadmap-system: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `58`
**Declared:** `5`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=58
- Declared progress.tasks_completed=5

**Suggested Fix:** Review progress.tasks_completed for roadmap-system

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-system/track.yaml`

---

### 🟡 sqlite-backend: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `3`
**Declared:** `4`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=3
- Declared progress.sprints_completed=4

**Suggested Fix:** Review progress.sprints_completed for sqlite-backend

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/sqlite-backend/track.yaml`

---

### 🟡 sqlite-backend: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `22`
**Declared:** `29`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=22
- Declared progress.tasks_completed=29

**Suggested Fix:** Review progress.tasks_completed for sqlite-backend

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/sqlite-backend/track.yaml`

---

### 🟡 standards-system: progress.sprints_completed ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.sprints_completed=6
- Declared progress.sprints_completed=0

**Suggested Fix:** Review progress.sprints_completed for standards-system

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/track.yaml`

---

### 🟡 standards-system: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `51`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=51
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for standards-system

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/standards-system/track.yaml`

---

## Sprint Discrepancies (57)

### 🟡 cody-port-1: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `4`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 6 task.yaml files in cody-port-1/
- Declared tasks_total=4

**Suggested Fix:** Review: 6 task files exist but 4 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/cody-port/cody-port-1/sprint.yaml`

---

### 🟡 cody-port-2: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `2`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 4 task.yaml files in cody-port-2/
- Declared tasks_total=2

**Suggested Fix:** Review: 4 task files exist but 2 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/cody-port/cody-port-2/sprint.yaml`

---

### 🟡 core-framework-2: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `production_ready`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 13/13 completed
- Computed status: 'completed' based on task completion
- Declared status: 'production_ready'

**Suggested Fix:** Review sprint 'core-framework-2' - with 13/13 tasks done, should status be 'completed'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/core-framework/core-framework-2/sprint.yaml`

---

### 🟡 core-framework-3: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `production_ready`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 7/7 completed
- Computed status: 'completed' based on task completion
- Declared status: 'production_ready'

**Suggested Fix:** Review sprint 'core-framework-3' - with 7/7 tasks done, should status be 'completed'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/core-framework/core-framework-3/sprint.yaml`

---

### 🟡 directory-consolidation-1: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `5`
**Declared:** `0`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 5 task.yaml files in directory-consolidation-1/
- Declared tasks_total=0

**Suggested Fix:** Review: 5 task files exist but 0 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-1/sprint.yaml`

---

### 🟡 directory-consolidation-2: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `0`
**Root Cause:** extra_task_files
**Confidence:** medium

**Evidence:**
- Found 6 task.yaml files in directory-consolidation-2/
- Declared tasks_total=0

**Suggested Fix:** Review: 6 task files exist but 0 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-2/sprint.yaml`

---

### 🟡 directory-consolidation-3: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 4 task.yaml files in directory-consolidation-3/
- Declared tasks_total=0

**Suggested Fix:** Review: 4 task files exist but 0 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-3/sprint.yaml`

---

### 🟡 directory-consolidation-4: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 4 task.yaml files in directory-consolidation-4/
- Declared tasks_total=0

**Suggested Fix:** Review: 4 task files exist but 0 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-4/sprint.yaml`

---

### 🟡 directory-consolidation-5: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 4 task.yaml files in directory-consolidation-5/
- Declared tasks_total=0

**Suggested Fix:** Review: 4 task files exist but 0 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-5/sprint.yaml`

---

### 🟡 documentation-system-1: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `production_ready`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 8/8 completed
- Computed status: 'completed' based on task completion
- Declared status: 'production_ready'

**Suggested Fix:** Review sprint 'documentation-system-1' - with 8/8 tasks done, should status be 'completed'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/documentation-system/documentation-system-1/sprint.yaml`

---

### 🟡 gemini-port-1: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/6 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'gemini-port-1' - with 0/6 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-1/sprint.yaml`

---

### 🟡 gemini-port-2: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/5 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'gemini-port-2' - with 0/5 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-2/sprint.yaml`

---

### 🟡 gemini-port-3: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/6 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'gemini-port-3' - with 0/6 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-3/sprint.yaml`

---

### 🟡 gemini-port-4: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/5 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'gemini-port-4' - with 0/5 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/gemini-port/gemini-port-4/sprint.yaml`

---

### 🟡 infrastructure-fixes-1: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `production_ready`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 13/13 completed
- Computed status: 'completed' based on task completion
- Declared status: 'production_ready'

**Suggested Fix:** Review sprint 'infrastructure-fixes-1' - with 13/13 tasks done, should status be 'completed'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/sprint.yaml`

---

### 🟡 infrastructure-fixes-2: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `7`
**Declared:** `6`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 7 task.yaml files in infrastructure-fixes-2/
- Declared tasks_total=6

**Suggested Fix:** Review: 7 task files exist but 6 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/infrastructure-fixes/infrastructure-fixes-2/sprint.yaml`

---

### 🟡 mcp-server-1: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `production_ready`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 8/8 completed
- Computed status: 'completed' based on task completion
- Declared status: 'production_ready'

**Suggested Fix:** Review sprint 'mcp-server-1' - with 8/8 tasks done, should status be 'completed'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/mcp-server/mcp-server-1/sprint.yaml`

---

### 🟡 mcp-server-2: status ⚠️ NEEDS REVIEW

**Computed:** `completed`
**Declared:** `production_ready`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 8/8 completed
- Computed status: 'completed' based on task completion
- Declared status: 'production_ready'

**Suggested Fix:** Review sprint 'mcp-server-2' - with 8/8 tasks done, should status be 'completed'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/mcp-server/mcp-server-2/sprint.yaml`

---

### 🟡 roadmap-integrity-fixes-11: progress.tasks_total ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Found 1 task.yaml files in roadmap-integrity-fixes-11/
- Declared tasks_total=0

**Suggested Fix:** Review: 1 task files exist but 0 declared. Which is correct?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes/roadmap-integrity-fixes-11/sprint.yaml`

---

### 🟡 roadmap-integrity-fixes-2-2: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/6 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'roadmap-integrity-fixes-2-2' - with 0/6 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes-2/roadmap-integrity-fixes-2-2/sprint.yaml`

---

### 🟡 roadmap-integrity-fixes-2-3: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/6 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'roadmap-integrity-fixes-2-3' - with 0/6 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes-2/roadmap-integrity-fixes-2-3/sprint.yaml`

---

### 🟡 roadmap-integrity-fixes-2-4: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/8 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'roadmap-integrity-fixes-2-4' - with 0/8 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes-2/roadmap-integrity-fixes-2-4/sprint.yaml`

---

### 🟡 roadmap-integrity-fixes-2-5: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `completed`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/4 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'completed'

**Suggested Fix:** Review sprint 'roadmap-integrity-fixes-2-5' - with 0/4 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-integrity-fixes-2/roadmap-integrity-fixes-2-5/sprint.yaml`

---

### 🟡 roadmap-state-audit-10: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/2 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-10' - with 0/2 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-10/sprint.yaml`

---

### 🟡 roadmap-state-audit-11: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-11' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-11/sprint.yaml`

---

### 🟡 roadmap-state-audit-12: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/4 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-12' - with 0/4 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-12/sprint.yaml`

---

### 🟡 roadmap-state-audit-13: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/2 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-13' - with 0/2 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-13/sprint.yaml`

---

### 🟡 roadmap-state-audit-14: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-14' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-14/sprint.yaml`

---

### 🟡 roadmap-state-audit-15: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/2 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-15' - with 0/2 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-15/sprint.yaml`

---

### 🟡 roadmap-state-audit-16: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-16' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-16/sprint.yaml`

---

### 🟡 roadmap-state-audit-18: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/2 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-18' - with 0/2 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-18/sprint.yaml`

---

### 🟡 roadmap-state-audit-20: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/4 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-20' - with 0/4 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-20/sprint.yaml`

---

### 🟡 roadmap-state-audit-21: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/4 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-21' - with 0/4 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-21/sprint.yaml`

---

### 🟡 roadmap-state-audit-22: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-22' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-22/sprint.yaml`

---

### 🟡 roadmap-state-audit-23: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/5 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-23' - with 0/5 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-23/sprint.yaml`

---

### 🟡 roadmap-state-audit-24: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-24' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-24/sprint.yaml`

---

### 🟡 roadmap-state-audit-25: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/1 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-25' - with 0/1 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-25/sprint.yaml`

---

### 🟡 roadmap-state-audit-3: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/1 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-3' - with 0/1 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-3/sprint.yaml`

---

### 🟡 roadmap-state-audit-5: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/4 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-5' - with 0/4 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-5/sprint.yaml`

---

### 🟡 roadmap-state-audit-7: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-7' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-7/sprint.yaml`

---

### 🟡 roadmap-state-audit-8: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/3 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-8' - with 0/3 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-8/sprint.yaml`

---

### 🟡 roadmap-state-audit-9: status ⚠️ NEEDS REVIEW

**Computed:** `not_started`
**Declared:** `in_progress`
**Root Cause:** status_not_updated
**Confidence:** medium

**Evidence:**
- Tasks: 0/1 completed
- Computed status: 'not_started' based on task completion
- Declared status: 'in_progress'

**Suggested Fix:** Review sprint 'roadmap-state-audit-9' - with 0/1 tasks done, should status be 'not_started'?

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-9/sprint.yaml`

---

### 🟢 directory-consolidation-1: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `5`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=5
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint directory-consolidation-1

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-1/sprint.yaml`

---

### 🟢 directory-consolidation-2: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `6`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=6
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint directory-consolidation-2

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-2/sprint.yaml`

---

### 🟢 directory-consolidation-3: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=4
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint directory-consolidation-3

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-3/sprint.yaml`

---

### 🟢 directory-consolidation-4: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=4
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint directory-consolidation-4

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-4/sprint.yaml`

---

### 🟢 directory-consolidation-5: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `4`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=4
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint directory-consolidation-5

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/directory-consolidation/directory-consolidation-5/sprint.yaml`

---

### 🟢 infrastructure-fixes-2: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `7`
**Declared:** `6`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=7
- Declared progress.tasks_completed=6

**Suggested Fix:** Review progress.tasks_completed for sprint infrastructure-fixes-2

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/infrastructure-fixes/infrastructure-fixes-2/sprint.yaml`

---

### 🟢 roadmap-state-audit-1: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=1
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-1

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-1/sprint.yaml`

---

### 🟢 roadmap-state-audit-17: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=1
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-17

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-17/sprint.yaml`

---

### 🟢 roadmap-state-audit-19: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=2
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-19

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-19/sprint.yaml`

---

### 🟢 roadmap-state-audit-2: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=2
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-2

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-2/sprint.yaml`

---

### 🟢 roadmap-state-audit-26: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=1
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-26

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-26/sprint.yaml`

---

### 🟢 roadmap-state-audit-27: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=2
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-27

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-27/sprint.yaml`

---

### 🟢 roadmap-state-audit-28: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=2
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-28

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-28/sprint.yaml`

---

### 🟢 roadmap-state-audit-4: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `1`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=1
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-4

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-4/sprint.yaml`

---

### 🟢 roadmap-state-audit-6: progress.tasks_completed ⚠️ NEEDS REVIEW

**Computed:** `2`
**Declared:** `0`
**Root Cause:** yaml_counter_drift
**Confidence:** medium

**Evidence:**
- Computed progress.tasks_completed=2
- Declared progress.tasks_completed=0

**Suggested Fix:** Review progress.tasks_completed for sprint roadmap-state-audit-6

**Affected Files:**
- `/Users/fredabood/Repositories/vibey/.vibey/roadmap/roadmap-state-audit/roadmap-state-audit-6/sprint.yaml`

---
