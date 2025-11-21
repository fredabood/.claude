#!/bin/bash
# Restore Integrity Checkpoint
#
# Restores .vibey/ directory from a checkpoint with verification.
# Integrates with Sprint 0 rollback procedures.
#
# Usage: ./restore-integrity-checkpoint.sh <checkpoint-name> [--verify-only]
#
# Sprint: roadmap-integrity-fixes-1
# Task: roadmap-integrity-fixes-1-task-002

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CHECKPOINT_NAME="$1"
VERIFY_ONLY="${2:-}"
CHECKPOINT_BASE_DIR=".vibey-checkpoints"
CHECKPOINT_DIR="$CHECKPOINT_BASE_DIR/$CHECKPOINT_NAME"

if [ -z "$CHECKPOINT_NAME" ]; then
    echo "Usage: $0 <checkpoint-name> [--verify-only]"
    echo ""
    echo "Available checkpoints:"
    ls -1 "$CHECKPOINT_BASE_DIR" 2>/dev/null || echo "  (none)"
    exit 1
fi

echo "================================================================================"
echo "Vibey Integrity Checkpoint Restoration"
echo "================================================================================"
echo ""
echo "Checkpoint: $CHECKPOINT_NAME"
echo "Mode: ${VERIFY_ONLY:+VERIFY ONLY}"
echo ""

# Validate checkpoint exists
if [ ! -d "$CHECKPOINT_DIR" ]; then
    echo -e "${RED}❌ Error: Checkpoint not found${NC}"
    echo "   Path: $CHECKPOINT_DIR"
    echo ""
    echo "Available checkpoints:"
    ls -1 "$CHECKPOINT_BASE_DIR" 2>/dev/null || echo "  (none)"
    exit 1
fi

# Verify checkpoint integrity
echo "Verifying checkpoint integrity..."
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import verify_checkpoint_integrity

success, report = verify_checkpoint_integrity(Path('$CHECKPOINT_DIR'))

print(f'  Total files: {report[\"total_files\"]}')
print(f'  Verified: {report[\"verified_files\"]}')
print(f'  Failed: {report[\"failed_files\"]}')
print(f'  Missing: {report[\"missing_files\"]}')

if success:
    print('✅ Checkpoint integrity valid')
    sys.exit(0)
else:
    print('❌ Checkpoint integrity check failed')
    for failure in report.get('failures', [])[:5]:
        print(f'  - {failure[\"file\"]}: {failure[\"error\"]}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Checkpoint verification failed${NC}"
    echo "   Cannot restore from invalid checkpoint"
    exit 1
fi

# Check YAML syntax in checkpoint
echo "Verifying YAML syntax in checkpoint..."
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import verify_yaml_syntax

checkpoint_roadmap = Path('$CHECKPOINT_DIR') / '.vibey' / 'roadmap'
if checkpoint_roadmap.exists():
    success, report = verify_yaml_syntax(checkpoint_roadmap)
    print(f'  YAML files: {report[\"total_yaml_files\"]}')
    print(f'  Valid: {report[\"valid_files\"]}')
    print(f'  Invalid: {report[\"invalid_files\"]}')

    if success:
        print('✅ All YAML files valid')
        sys.exit(0)
    else:
        print('❌ YAML validation failed')
        for error in report.get('errors', [])[:5]:
            print(f'  - {error[\"file\"]}: {error[\"error\"]}')
        sys.exit(1)
else:
    print('⚠️  No roadmap directory in checkpoint')
    sys.exit(0)
"

YAML_VALID=$?

if [ "$VERIFY_ONLY" = "--verify-only" ]; then
    echo ""
    echo "================================================================================"
    echo -e "${GREEN}✅ Checkpoint verification complete${NC}"
    echo "================================================================================"
    echo ""
    echo "Checkpoint: $CHECKPOINT_NAME"
    echo "Status: Valid and ready for restoration"
    echo ""
    echo "To restore: ./scripts/restore-integrity-checkpoint.sh $CHECKPOINT_NAME"
    echo ""
    exit 0
fi

# Display checkpoint info
echo ""
echo "Checkpoint information:"
if [ -f "$CHECKPOINT_DIR/git-state.txt" ]; then
    echo "  Git commit: $(head -1 "$CHECKPOINT_DIR/git-state.txt")"
fi
if [ -f "$CHECKPOINT_DIR/README.md" ]; then
    grep "Created:" "$CHECKPOINT_DIR/README.md" | head -1
fi
echo "  Size: $(du -sh "$CHECKPOINT_DIR" | cut -f1)"
echo ""

# Confirm restoration
echo -e "${YELLOW}⚠️  WARNING: This will replace your current .vibey/ directory${NC}"
echo ""
read -p "Continue with restoration? (yes/NO) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Create pre-rollback backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PRE_ROLLBACK_BACKUP="$CHECKPOINT_BASE_DIR/pre-rollback-backup_$TIMESTAMP"

echo "Creating pre-rollback backup..."
mkdir -p "$PRE_ROLLBACK_BACKUP"

if [ -d ".vibey" ]; then
    cp -R .vibey "$PRE_ROLLBACK_BACKUP/"
    echo "  ✅ Current state backed up to: $PRE_ROLLBACK_BACKUP"
else
    echo "  ℹ️  No .vibey directory to backup"
fi

# Restore from checkpoint
echo "Restoring from checkpoint..."

# Remove current .vibey
if [ -d ".vibey" ]; then
    rm -rf .vibey
fi

# Copy from checkpoint
cp -R "$CHECKPOINT_DIR/.vibey" .vibey

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to restore .vibey/${NC}"
    echo "   Attempting to restore from pre-rollback backup..."

    if [ -d "$PRE_ROLLBACK_BACKUP/.vibey" ]; then
        cp -R "$PRE_ROLLBACK_BACKUP/.vibey" .vibey
        echo "  ✅ Restored from pre-rollback backup"
    fi
    exit 1
fi

# Restore framework files if they exist in checkpoint
if [ -d "$CHECKPOINT_DIR/vibey" ]; then
    echo "Restoring framework files..."
    if [ -d "$CHECKPOINT_DIR/vibey/operations/roadmap" ]; then
        mkdir -p vibey/operations
        cp -R "$CHECKPOINT_DIR/vibey/operations/roadmap" vibey/operations/ 2>/dev/null || true
    fi
fi

# Verify restoration
echo "Verifying restoration..."

# Check .vibey exists
if [ ! -d ".vibey" ]; then
    echo -e "${RED}❌ Error: .vibey directory not found after restoration${NC}"
    exit 1
fi

# Verify YAML syntax
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import verify_yaml_syntax

roadmap_dir = Path('.vibey/roadmap')
if roadmap_dir.exists():
    success, report = verify_yaml_syntax(roadmap_dir)

    if success:
        print(f'✅ YAML validation passed ({report[\"total_yaml_files\"]} files)')
        sys.exit(0)
    else:
        print(f'❌ YAML validation failed')
        print(f'  Invalid files: {report[\"invalid_files\"]}')
        sys.exit(1)
else:
    print('⚠️  No roadmap directory found')
    sys.exit(0)
"

YAML_OK=$?

# Test roadmap commands
echo "Testing roadmap commands..."
python3 vibey/cli/main.py roadmap status > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "  ✅ roadmap status command works"
else
    echo -e "  ${YELLOW}⚠️  roadmap status command failed${NC}"
fi

# Final report
echo ""
echo "================================================================================"
if [ $YAML_OK -eq 0 ]; then
    echo -e "${GREEN}✅ Restoration completed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Restoration completed with warnings${NC}"
fi
echo "================================================================================"
echo ""
echo "Checkpoint restored: $CHECKPOINT_NAME"
echo "Pre-rollback backup: $PRE_ROLLBACK_BACKUP"
echo ""
echo "Verification:"
echo "  - .vibey/ directory: ✅ Present"
echo "  - YAML syntax: $([ $YAML_OK -eq 0 ] && echo '✅ Valid' || echo '⚠️  Warnings')"
echo "  - Roadmap commands: $(python3 vibey/cli/main.py roadmap status > /dev/null 2>&1 && echo '✅ Working' || echo '⚠️  Check manually')"
echo ""
echo "If you need to rollback this restoration:"
echo "  ./scripts/restore-integrity-checkpoint.sh pre-rollback-backup_$TIMESTAMP"
echo ""

exit 0
