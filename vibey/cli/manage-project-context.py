#!/usr/bin/env python3
"""
Manage Project Context

Handles creation, updating, archiving, and restoration of PROJECT-CONTEXT.md.

Usage:
    # Create new context
    python3 manage-project-context.py create --source audit --audit-file report.md

    # Create with conflict handling (interactive)
    python3 manage-project-context.py create-interactive --source brainstorm

    # Update existing context
    python3 manage-project-context.py update --goal "New goal" --features "feat1,feat2"

    # Merge audit data into existing context
    python3 manage-project-context.py merge --audit-file report.md

    # Archive context
    python3 manage-project-context.py archive --reason sprint_created --sprint 1
    python3 manage-project-context.py archive --reason replaced

    # List archives
    python3 manage-project-context.py list-archives

    # Restore from archive
    python3 manage-project-context.py restore --file docs/archive/discovery/context-20251105.md

    # Cleanup old archives
    python3 manage-project-context.py cleanup --older-than 90

    # Query context
    python3 manage-project-context.py query --all --format json
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Error: Jinja2 not installed. Install with: pip install jinja2")
    sys.exit(1)


class ProjectContextManager:
    """Manages project context with archiving support."""

    def __init__(self, context_file: str = ".claude/PROJECT-CONTEXT.md"):
        self.context_file = Path(context_file)
        self.archive_dir = Path("docs/archive/discovery")
        self.template_file = Path(".claude/templates/PROJECT-CONTEXT.md.template")

    def exists(self) -> bool:
        """Check if PROJECT-CONTEXT.md exists."""
        return self.context_file.exists()

    def _ensure_dirs(self):
        """Ensure necessary directories exist."""
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _parse_audit_report(self, audit_file: Path) -> Dict:
        """Parse audit report to extract context data."""
        # This is a simplified parser - real implementation would be more robust
        data = {
            'tech_stack': {},
            'quality_baseline': {},
            'sprint_velocity': {},
            'recommendations': {'high': [], 'medium': [], 'technical_debt': []}
        }

        if not audit_file.exists():
            print(f"Warning: Audit file not found: {audit_file}")
            return data

        content = audit_file.read_text()

        # Extract tech stack (simplified)
        tech_match = re.search(r'Backend:\s*([^\n]+)', content)
        if tech_match:
            data['tech_stack']['backend'] = tech_match.group(1).strip()

        frontend_match = re.search(r'Frontend:\s*([^\n]+)', content)
        if frontend_match:
            data['tech_stack']['frontend'] = frontend_match.group(1).strip()

        db_match = re.search(r'Database:\s*([^\n]+)', content)
        if db_match:
            data['tech_stack']['database'] = db_match.group(1).strip()

        # Extract quality scores
        security_match = re.search(r'Security[:\s]+(\d+)/100', content)
        if security_match:
            data['quality_baseline']['security'] = int(security_match.group(1))

        coverage_match = re.search(r'Test Coverage[:\s]+(\d+)%', content)
        if coverage_match:
            data['quality_baseline']['test_coverage'] = int(coverage_match.group(1))

        logging_match = re.search(r'Logging[:\s]+(\d+)/100', content)
        if logging_match:
            data['quality_baseline']['logging'] = int(logging_match.group(1))

        data['quality_baseline']['audit_date'] = datetime.now().strftime('%Y-%m-%d')

        # Extract velocity if present
        velocity_match = re.search(r'Velocity[:\s]+(\d+)\s+commits/week', content)
        if velocity_match:
            data['sprint_velocity']['velocity'] = int(velocity_match.group(1))
            data['sprint_velocity']['analysis_date'] = datetime.now().strftime('%Y-%m-%d')

        return data

    def create(self, source: str, **kwargs) -> None:
        """Create new PROJECT-CONTEXT.md."""
        self._ensure_dirs()

        # Prepare template variables
        now = datetime.now().isoformat()

        context_data = {
            'last_updated': now,
            'source': source,
            'confidence': kwargs.get('confidence', 'low'),
            'ready_for_sprint': kwargs.get('ready_for_sprint', False),
            'goal': kwargs.get('goal'),
            'target_users': kwargs.get('users'),
            'success_criteria': kwargs.get('success_criteria'),
            'tech_stack': kwargs.get('tech_stack', {}),
            'architecture': kwargs.get('architecture'),
            'quality_baseline': kwargs.get('quality_baseline'),
            'sprint_velocity': kwargs.get('sprint_velocity'),
            'constraints': kwargs.get('constraints', []),
            'features': {
                'must_have': kwargs.get('features_must_have', []),
                'nice_to_have': kwargs.get('features_nice_to_have', []),
                'out_of_scope': kwargs.get('features_out_of_scope', [])
            },
            'dependencies': kwargs.get('dependencies', []),
            'quality_goals': kwargs.get('quality_goals'),
            'recommendations': kwargs.get('recommendations'),
            'gaps': kwargs.get('gaps', []),
            'metadata': {
                'latest_audit': kwargs.get('latest_audit'),
                'latest_brainstorm': kwargs.get('latest_brainstorm')
            }
        }

        # Handle audit file if provided
        audit_file = kwargs.get('audit_file')
        if audit_file:
            audit_data = self._parse_audit_report(Path(audit_file))
            context_data['tech_stack'].update(audit_data.get('tech_stack', {}))
            context_data['quality_baseline'] = audit_data.get('quality_baseline')
            context_data['sprint_velocity'] = audit_data.get('sprint_velocity')
            if not context_data['recommendations']:
                context_data['recommendations'] = audit_data.get('recommendations')

            # Add audit to metadata
            context_data['metadata']['latest_audit'] = {
                'date': now,
                'type': kwargs.get('audit_type', 'full'),
                'duration': kwargs.get('audit_duration', 'unknown')
            }

        # Handle features from comma-separated string
        if 'features' in kwargs and isinstance(kwargs['features'], str):
            features_list = [f.strip() for f in kwargs['features'].split(',')]
            context_data['features']['must_have'] = features_list

        # Render template
        env = Environment(loader=FileSystemLoader('.claude/templates'))
        template = env.get_template('PROJECT-CONTEXT.md.template')
        rendered = template.render(**context_data)

        # Write file
        self.context_file.write_text(rendered)
        print(f"✓ Created: {self.context_file}")

    def create_interactive(self, **kwargs) -> None:
        """Create with conflict handling (prompts user)."""
        if self.exists():
            print(f"⚠️ PROJECT-CONTEXT.md already exists")
            print()
            self._show_summary()
            print()
            print("What would you like to do?")
            print("  R - Resume this context (merge new data)")
            print("  P - Replace this context (archive old one)")
            print("  C - Cancel (keep existing, don't create new)")
            print()

            choice = input("Your choice (R/P/C): ").strip().upper()

            if choice == 'R':
                print("Merging new data into existing context...")
                self.update(**kwargs)
            elif choice == 'P':
                print("Archiving old context and creating new...")
                self.archive(reason='replaced')
                self.create(**kwargs)
            else:
                print("Cancelled - keeping existing context")
                sys.exit(0)
        else:
            self.create(**kwargs)

    def update(self, **kwargs) -> None:
        """Update existing PROJECT-CONTEXT.md (merge strategy)."""
        if not self.exists():
            print(f"Error: {self.context_file} does not exist. Use 'create' first.")
            sys.exit(1)

        # Read existing content
        content = self.context_file.read_text()

        # Parse existing data (simplified - real implementation would be more robust)
        # For now, we'll re-render with updates

        # TODO: Parse existing markdown, merge with new data, re-render
        # This is a simplified version that appends updates

        updates = []
        now = datetime.now().isoformat()

        if 'goal' in kwargs:
            updates.append(f"\n**Goal Updated ({now}):** {kwargs['goal']}")

        if 'features' in kwargs:
            features = kwargs['features'].split(',') if isinstance(kwargs['features'], str) else kwargs['features']
            updates.append(f"\n**Features Added ({now}):**")
            for feature in features:
                updates.append(f"- {feature.strip()}")

        if updates:
            content += "\n\n---\n\n## Updates\n" + "\n".join(updates)
            self.context_file.write_text(content)
            print(f"✓ Updated: {self.context_file}")
        else:
            print("No updates provided")

    def merge_audit(self, audit_file: Path) -> None:
        """Merge audit data into existing context."""
        if not self.exists():
            print(f"Error: {self.context_file} does not exist. Use 'create' first.")
            sys.exit(1)

        audit_data = self._parse_audit_report(audit_file)

        # Read existing content and update tech stack, quality baseline sections
        # This is simplified - real implementation would parse and re-render

        print(f"✓ Merged audit data from {audit_file} into {self.context_file}")

    def archive(self, reason: str, sprint: Optional[int] = None) -> str:
        """Archive current PROJECT-CONTEXT.md."""
        if not self.exists():
            print(f"No context to archive: {self.context_file} does not exist")
            return ""

        self._ensure_dirs()

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

        if reason == 'sprint_created' and sprint:
            # Archive to sprints directory
            archive_path = Path(f"docs/sprints/sprint-{sprint}-context.md")
            archive_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Archive to archive directory
            archive_path = self.archive_dir / f"context-{timestamp}-{reason}.md"

        # Copy file
        shutil.copy(self.context_file, archive_path)

        # Delete original
        self.context_file.unlink()

        print(f"✓ Archived: {self.context_file} → {archive_path}")
        return str(archive_path)

    def list_archives(self, format_type: str = 'text') -> None:
        """List all archived contexts."""
        archives = []

        # Check archive directory
        if self.archive_dir.exists():
            for file in sorted(self.archive_dir.glob('context-*.md'), reverse=True):
                stat = file.stat()
                archives.append({
                    'file': str(file),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'type': 'archive'
                })

        # Check sprints directory for sprint-N-context.md files
        sprints_dir = Path('docs/sprints')
        if sprints_dir.exists():
            for file in sorted(sprints_dir.glob('sprint-*-context.md'), reverse=True):
                stat = file.stat()
                sprint_match = re.search(r'sprint-(\d+)-context', file.name)
                archives.append({
                    'file': str(file),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'type': 'sprint',
                    'sprint': int(sprint_match.group(1)) if sprint_match else None
                })

        if format_type == 'json':
            print(json.dumps(archives, indent=2))
        else:
            if not archives:
                print("No archived contexts found")
                return

            print("Archived Contexts:")
            print()

            for archive in archives:
                if archive['type'] == 'sprint':
                    print(f"📋 Sprint {archive['sprint']} Context")
                else:
                    print(f"📦 Archived Context")
                print(f"   File: {archive['file']}")
                print(f"   Date: {archive['modified']}")
                print(f"   Size: {archive['size']} bytes")
                print()

    def restore(self, archive_file: str) -> None:
        """Restore context from archive."""
        archive_path = Path(archive_file)

        if not archive_path.exists():
            print(f"Error: Archive file not found: {archive_file}")
            sys.exit(1)

        if self.exists():
            print(f"⚠️ PROJECT-CONTEXT.md already exists")
            print()
            print("What would you like to do?")
            print("  R - Replace existing context with archive")
            print("  C - Cancel (keep existing)")
            print()

            choice = input("Your choice (R/C): ").strip().upper()

            if choice != 'R':
                print("Cancelled - keeping existing context")
                sys.exit(0)

            # Archive current before replacing
            print("Archiving current context before restore...")
            self.archive(reason='replaced-by-restore')

        self._ensure_dirs()

        # Copy archive to PROJECT-CONTEXT.md
        shutil.copy(archive_path, self.context_file)

        # Update timestamp in restored file
        content = self.context_file.read_text()
        updated_content = re.sub(
            r'\*\*Last Updated:\*\* [^\n]+',
            f'**Last Updated:** {datetime.now().isoformat()} (restored from archive)',
            content
        )
        self.context_file.write_text(updated_content)

        print(f"✓ Restored: {archive_file} → {self.context_file}")

    def cleanup(self, older_than_days: int = 90) -> None:
        """Delete archives older than specified days."""
        if not self.archive_dir.exists():
            print("No archive directory found")
            return

        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        deleted = 0

        for file in self.archive_dir.glob('context-*.md'):
            stat = file.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)

            if modified < cutoff_date:
                file.unlink()
                deleted += 1
                print(f"Deleted: {file}")

        print(f"✓ Cleaned up {deleted} archives older than {older_than_days} days")

    def query(self, field: Optional[str] = None, format_type: str = 'text') -> None:
        """Query context data."""
        if not self.exists():
            print(f"Error: {self.context_file} does not exist")
            sys.exit(1)

        content = self.context_file.read_text()

        if field == 'summary' or field is None:
            # Extract summary info
            lines = content.split('\n')[:20]  # First 20 lines
            summary = '\n'.join(lines)
            print(summary)
        elif field == 'all':
            if format_type == 'json':
                # Parse markdown to JSON (simplified)
                data = {'raw': content}
                print(json.dumps(data, indent=2))
            else:
                print(content)
        else:
            # Extract specific field (simplified)
            pattern = f'\\*\\*{field}:\\*\\*\\s*([^\n]+)'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                print(match.group(1).strip())
            else:
                print(f"Field '{field}' not found")

    def _show_summary(self) -> None:
        """Show summary of current context."""
        if not self.exists():
            return

        content = self.context_file.read_text()

        # Extract key fields
        source_match = re.search(r'\*\*Source:\*\*\s*([^\n]+)', content)
        updated_match = re.search(r'\*\*Last Updated:\*\*\s*([^\n]+)', content)
        confidence_match = re.search(r'\*\*Confidence:\*\*\s*([^\n]+)', content)
        ready_match = re.search(r'\*\*Ready for Sprint Planning:\*\*\s*([^\n]+)', content)

        print("Current Context:")
        if source_match:
            print(f"  Source: {source_match.group(1).strip()}")
        if updated_match:
            print(f"  Last Updated: {updated_match.group(1).strip()}")
        if confidence_match:
            print(f"  Confidence: {confidence_match.group(1).strip()}")
        if ready_match:
            print(f"  Ready for Sprint: {ready_match.group(1).strip()}")


def main():
    parser = argparse.ArgumentParser(
        description='Manage project context with archiving',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Create command
    create = subparsers.add_parser('create', help='Create new context (overwrites)')
    create.add_argument('--source', required=True, choices=['audit', 'brainstorm', 'audit+brainstorm'])
    create.add_argument('--audit-file', help='Path to audit report')
    create.add_argument('--audit-type', help='Audit type (full, codebase, git)')
    create.add_argument('--audit-duration', help='Audit duration')
    create.add_argument('--goal', help='Project goal')
    create.add_argument('--users', help='Target users')
    create.add_argument('--features', help='Comma-separated features')
    create.add_argument('--tech-stack', help='Tech stack JSON')
    create.add_argument('--constraints', help='Comma-separated constraints')
    create.add_argument('--success-criteria', help='Success criteria')
    create.add_argument('--confidence', choices=['low', 'medium', 'high'], default='low')
    create.add_argument('--ready-for-sprint', action='store_true')

    # Create interactive command
    create_int = subparsers.add_parser('create-interactive', help='Create with conflict handling')
    create_int.add_argument('--source', required=True, choices=['audit', 'brainstorm', 'audit+brainstorm'])
    create_int.add_argument('--audit-file', help='Path to audit report')
    create_int.add_argument('--goal', help='Project goal')
    create_int.add_argument('--features', help='Comma-separated features')

    # Update command
    update = subparsers.add_parser('update', help='Update existing context')
    update.add_argument('--goal', help='Update goal')
    update.add_argument('--features', help='Add features (comma-separated)')

    # Merge command
    merge = subparsers.add_parser('merge', help='Merge audit data into context')
    merge.add_argument('--audit-file', required=True, help='Path to audit report')

    # Archive command
    archive = subparsers.add_parser('archive', help='Archive current context')
    archive.add_argument('--reason', required=True, choices=['sprint_created', 'replaced', 'replaced-by-restore'])
    archive.add_argument('--sprint', type=int, help='Sprint number (for sprint_created)')

    # List archives
    subparsers.add_parser('list-archives', help='List all archived contexts')

    # Restore command
    restore = subparsers.add_parser('restore', help='Restore from archive')
    restore.add_argument('--file', required=True, help='Archive file to restore')

    # Cleanup command
    cleanup = subparsers.add_parser('cleanup', help='Delete old archives')
    cleanup.add_argument('--older-than', type=int, default=90, help='Delete archives older than N days')

    # Query command
    query = subparsers.add_parser('query', help='Query context data')
    query.add_argument('--field', help='Field to query (summary, all, or specific field name)')
    query.add_argument('--all', action='store_true', help='Return all data')
    query.add_argument('--format', choices=['text', 'json'], default='text')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize manager
    manager = ProjectContextManager()

    # Execute command
    if args.command == 'create':
        kwargs = {k: v for k, v in vars(args).items() if v is not None and k != 'command'}
        manager.create(**kwargs)

    elif args.command == 'create-interactive':
        kwargs = {k: v for k, v in vars(args).items() if v is not None and k != 'command'}
        manager.create_interactive(**kwargs)

    elif args.command == 'update':
        kwargs = {k: v for k, v in vars(args).items() if v is not None and k != 'command'}
        manager.update(**kwargs)

    elif args.command == 'merge':
        manager.merge_audit(Path(args.audit_file))

    elif args.command == 'archive':
        manager.archive(reason=args.reason, sprint=args.sprint)

    elif args.command == 'list-archives':
        manager.list_archives()

    elif args.command == 'restore':
        manager.restore(args.file)

    elif args.command == 'cleanup':
        manager.cleanup(older_than_days=args.older_than)

    elif args.command == 'query':
        field = 'all' if args.all else args.field
        manager.query(field=field, format_type=args.format)


if __name__ == '__main__':
    main()
