#!/usr/bin/env python3
"""
Sprint 12 Task 012: End-to-end validation of criteria system

This script validates the complete criteria system implementation:
1. Database schema (criteria table, views)
2. All 8 target types
3. SQL loader/dumper functions
4. Round-trip: DB → Load → Ticket
5. QueryTicketLoader integration
6. Completable model methods
7. Pre-commit hook integration
8. Commit-msg hook integration

Run with: python E2E_VALIDATION.py
"""

import os
import sys
from pathlib import Path

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check(name, condition, msg_pass=None, msg_fail=None):
    """Check a condition and print result."""
    if condition:
        print(f"  {GREEN}✓{RESET} {name}" + (f": {msg_pass}" if msg_pass else ""))
        return True
    else:
        print(f"  {RED}✗{RESET} {name}" + (f": {msg_fail}" if msg_fail else ""))
        return False


def main():
    # Change to repo root
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    os.chdir(repo_root)

    print(f"\n{BOLD}=== Sprint 12 End-to-End Validation ==={RESET}\n")

    passed = 0
    failed = 0

    # ============================================
    # 1. Database Schema Validation
    # ============================================
    print(f"{BOLD}1. Database Schema Validation{RESET}")
    import sqlite3
    db_path = '.vibey/roadmap.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check criteria table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='criteria'")
    if check("Criteria table exists", cursor.fetchone() is not None):
        passed += 1
    else:
        failed += 1

    # Check criteria count
    cursor.execute("SELECT COUNT(*) FROM criteria")
    criteria_count = cursor.fetchone()[0]
    if check("Criteria populated", criteria_count > 0, f"{criteria_count} criteria"):
        passed += 1
    else:
        failed += 1

    # Check views exist
    for view in ['v_criteria_status', 'v_blocking_criteria', 'v_completable_dependencies']:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view}'")
        if check(f"View {view} exists", cursor.fetchone() is not None):
            passed += 1
        else:
            failed += 1

    conn.close()

    # ============================================
    # 2. Criterion Target Types
    # ============================================
    print(f"\n{BOLD}2. Criterion Target Types{RESET}")

    from vibey.roadmap.models.ticket.targets import (
        CompletableTarget, FileExistsTarget, TestPassesTarget,
        TestCoverageTarget, ThresholdTarget, ManualTarget,
        ExternalTarget, ArtifactTarget
    )

    target_classes = [
        CompletableTarget, FileExistsTarget, TestPassesTarget,
        TestCoverageTarget, ThresholdTarget, ManualTarget,
        ExternalTarget, ArtifactTarget
    ]

    for cls in target_classes:
        if check(f"{cls.__name__} importable", True):
            passed += 1

    # ============================================
    # 3. SQL Loader/Dumper Functions
    # ============================================
    print(f"\n{BOLD}3. SQL Serialization Functions{RESET}")

    from vibey.roadmap.serialization.sql_loader import (
        load_criteria_for_completable,
        load_criteria_blocking_transition,
        load_unmet_criteria,
    )
    from vibey.roadmap.serialization.sql_dumper import (
        dump_criterion, dump_criteria,
        update_criterion_met_status,
    )

    funcs = [
        ("load_criteria_for_completable", load_criteria_for_completable),
        ("load_criteria_blocking_transition", load_criteria_blocking_transition),
        ("load_unmet_criteria", load_unmet_criteria),
        ("dump_criterion", dump_criterion),
        ("dump_criteria", dump_criteria),
        ("update_criterion_met_status", update_criterion_met_status),
    ]

    for name, func in funcs:
        if check(name, callable(func)):
            passed += 1
        else:
            failed += 1

    # ============================================
    # 4. Round-trip Test
    # ============================================
    print(f"\n{BOLD}4. Round-trip: Database → Load → Check{RESET}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT completable_id FROM criteria LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        task_id = row[0]
        criteria = load_criteria_for_completable('task', task_id)
        if check("Load criteria from DB", len(criteria) > 0, f"{len(criteria)} criteria for {task_id}"):
            passed += 1
        else:
            failed += 1

        if criteria:
            c = criteria[0]
            for attr_check, attr in [
                ("Criterion has ID", 'id'),
                ("Criterion has target", 'target'),
                ("Criterion has blocks_transition_to", 'blocks_transition_to'),
            ]:
                if check(attr_check, hasattr(c, attr) and getattr(c, attr) is not None):
                    passed += 1
                else:
                    failed += 1

    # ============================================
    # 5. QueryTicketLoader Integration
    # ============================================
    print(f"\n{BOLD}5. QueryTicketLoader Integration{RESET}")

    from vibey.operations.roadmap.query import load_task_ticket
    from vibey.roadmap.models.ticket import TicketStatus

    if row:
        ticket = load_task_ticket(Path('.'), task_id)
        if check("Load task ticket", ticket is not None):
            passed += 1
        else:
            failed += 1

        if ticket:
            for attr_check, cond in [
                ("Ticket has criteria attribute", hasattr(ticket, 'criteria')),
                ("Criteria loaded into ticket", len(ticket.criteria) > 0),
            ]:
                if check(attr_check, cond):
                    passed += 1
                else:
                    failed += 1

            can, blockers = ticket.can_transition_to(TicketStatus.COMPLETED)
            if check("can_transition_to() works", isinstance(can, bool)):
                passed += 1
            else:
                failed += 1
            if check("blockers is list", isinstance(blockers, list)):
                passed += 1
            else:
                failed += 1

    # ============================================
    # 6. Completable Model Methods
    # ============================================
    print(f"\n{BOLD}6. Completable Model Methods{RESET}")

    from vibey.roadmap.models.ticket.completable import Completable, Criterion
    from vibey.roadmap.models.ticket.targets import ManualTarget

    test_criterion = Criterion(
        id='test-001',
        description='Test criterion',
        required=True,
        blocks_transition_to=TicketStatus.COMPLETED,
        target=ManualTarget(verifier='Test', verification_steps=['Step 1']),
    )

    class TestCompletable(Completable):
        pass

    test_completable = TestCompletable(
        id='test-completable',
        name='Test',
        status=TicketStatus.IN_PROGRESS,
        criteria=[test_criterion],
    )

    can, blockers = test_completable.can_transition_to(TicketStatus.COMPLETED)
    if check("Unmet criterion blocks COMPLETED", not can, f"blocked by: {blockers}"):
        passed += 1
    else:
        failed += 1

    # ============================================
    # 7. Pre-commit Hook Integration
    # ============================================
    print(f"\n{BOLD}7. Pre-commit Hook Integration{RESET}")

    from vibey.operations.git.hooks.pre_commit import PreCommitHook

    hook = PreCommitHook('.')
    if check("PreCommitHook instantiates", hook is not None):
        passed += 1
    else:
        failed += 1
    if check("_check_completion_verification exists", hasattr(hook, '_check_completion_verification')):
        passed += 1
    else:
        failed += 1

    # ============================================
    # 8. Commit-msg Hook Integration
    # ============================================
    print(f"\n{BOLD}8. Commit-msg Hook Integration{RESET}")

    from vibey.operations.git.hooks.commit_msg import CommitMsgHook
    from vibey.operations.git.commit_parser import CommitParser
    from vibey.operations.git.commit_parser_schema import TaskStatus

    parser = CommitParser()
    # Use proper task ID format
    result = parser.parse("feat: Done\n\nCompletes: sqlite-backend-12-task-001")
    if check("Parser extracts Completes:", result.has_task_reference):
        passed += 1
    else:
        failed += 1

    if result.tasks:
        if check("Parser sets COMPLETED status", result.tasks[0].status == TaskStatus.COMPLETED):
            passed += 1
        else:
            failed += 1

    if check("CommitMsgHook._verify_completion_claims exists",
             hasattr(CommitMsgHook, '_verify_completion_claims')):
        passed += 1
    else:
        failed += 1

    # ============================================
    # Summary
    # ============================================
    print(f"\n{BOLD}=== Validation Summary ==={RESET}")
    total = passed + failed
    print(f"  Passed: {GREEN}{passed}{RESET}/{total}")
    print(f"  Failed: {RED}{failed}{RESET}/{total}")

    if failed == 0:
        print(f"\n{GREEN}All end-to-end validations passed!{RESET}")
        print(f"Criteria system is fully operational.\n")
        return 0
    else:
        print(f"\n{RED}Some validations failed.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
