"""
Validation commands.

Commands for validating documentation organization, asset frontmatter,
and directory structure.
"""

from pathlib import Path


def validate_docs_cmd(verbose: bool = False) -> int:
    """Validate documentation organization in roadmap."""
    from vibey.operations.validate.doc_organization import DocOrganizationValidator

    roadmap_dir = Path.cwd() / '.vibey' / 'roadmap'
    validator = DocOrganizationValidator(roadmap_dir, verbose)
    report = validator.validate()

    # Print summary
    print("\n" + "=" * 70)
    print("DOCUMENTATION ORGANIZATION VALIDATION")
    print("=" * 70)
    print(f"Tracks checked: {report.tracks_checked}")
    print(f"Sprints checked: {report.sprints_checked}")

    if report.warnings:
        print(f"\nWarnings: {len(report.warnings)}")
        for path, warning in report.warnings[:10]:
            print(f"  {path}")
            print(f"    {warning}")
        if len(report.warnings) > 10:
            print(f"  ... and {len(report.warnings) - 10} more warnings")

    if report.issues:
        print(f"\nIssues: {len(report.issues)}")
        for path, issue in report.issues[:20]:
            print(f"  {path}")
            print(f"    {issue}")
        if len(report.issues) > 20:
            print(f"  ... and {len(report.issues) - 20} more issues")

    print("\n" + "=" * 70)
    if report.is_valid:
        print("All documentation properly organized!")
    else:
        print(f"{len(report.issues)} organization issues found")
    print("=" * 70)

    return 0 if report.is_valid else 1


def validate_assets_cmd(asset_type: str = 'all', verbose: bool = False) -> int:
    """Validate asset frontmatter (agents, workflows, handoffs)."""
    from vibey.operations.validate.frontmatter import FrontmatterValidator

    root_dir = Path.cwd()
    validator = FrontmatterValidator(root_dir, verbose)

    if asset_type == 'all':
        report = validator.validate_all()
    else:
        report = validator.validate_assets(asset_type)

    # Print results by type
    types_validated = set(r.asset_type for r in report.results)
    for atype in sorted(types_validated):
        type_results = [r for r in report.results if r.asset_type == atype]
        valid = sum(1 for r in type_results if r.is_valid)
        invalid = sum(1 for r in type_results if not r.is_valid)
        print(f"\n{atype.capitalize()}:")
        print(f"  {valid} valid")
        if invalid > 0:
            print(f"  {invalid} invalid")

    # Show errors
    invalid_results = [r for r in report.results if not r.is_valid]
    if invalid_results:
        print(f"\n{'=' * 60}")
        print("VALIDATION ERRORS:")
        print('=' * 60)
        for result in invalid_results:
            print(f"\n{result.filepath}:")
            for error in result.errors:
                print(f"  - {error}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {report.valid_count} valid, {report.invalid_count} invalid")
    print('=' * 60)

    return 0 if report.is_valid else 1


def validate_structure_cmd(fix: bool = False) -> int:
    """Validate directory structure."""
    from vibey.operations.roadmap.structure_validator import StructureValidator

    root_dir = Path.cwd()
    validator = StructureValidator(root_dir)

    print("Validating directory structure...")
    print()

    issues = validator.validate()

    if not issues:
        print("Directory structure is valid!")
        return 0

    print(f"Found {len(issues)} structure issues:")
    print()

    for issue in issues[:20]:
        print(f"  - {issue}")

    if len(issues) > 20:
        print(f"  ... and {len(issues) - 20} more issues")

    if fix:
        print()
        print("Attempting to fix issues...")
        fixed = validator.fix_issues(issues)
        print(f"Fixed {fixed} issues")

    return 1
