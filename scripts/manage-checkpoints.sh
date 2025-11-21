#!/bin/bash
# Manage Integrity Checkpoints
#
# Provides checkpoint lifecycle management: list, verify, clean, compare
#
# Usage: ./manage-checkpoints.sh [list|verify|clean|compare] [args...]
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
CHECKPOINT_BASE_DIR=".vibey-checkpoints"
COMMAND="${1:-list}"

# Ensure checkpoint directory exists
mkdir -p "$CHECKPOINT_BASE_DIR"

# Function: List all checkpoints
list_checkpoints() {
    echo "================================================================================"
    echo "Available Checkpoints"
    echo "================================================================================"
    echo ""

    if [ ! "$(ls -A $CHECKPOINT_BASE_DIR 2>/dev/null)" ]; then
        echo "No checkpoints found"
        echo ""
        echo "To create a checkpoint:"
        echo "  ./scripts/create-integrity-checkpoint.sh [name]"
        return 0
    fi

    # Table header
    printf "%-40s  %-12s  %-20s  %s\n" "NAME" "SIZE" "CREATED" "STATUS"
    echo "--------------------------------------------------------------------------------"

    # List each checkpoint
    for checkpoint_dir in "$CHECKPOINT_BASE_DIR"/*; do
        if [ -d "$checkpoint_dir" ]; then
            NAME=$(basename "$checkpoint_dir")
            SIZE=$(du -sh "$checkpoint_dir" 2>/dev/null | cut -f1)

            # Get creation date from README if available
            if [ -f "$checkpoint_dir/README.md" ]; then
                CREATED=$(grep "Created:" "$checkpoint_dir/README.md" | sed 's/\*\*Created:\*\* //' | cut -d' ' -f1)
            else
                CREATED=$(stat -f "%Sm" -t "%Y-%m-%d" "$checkpoint_dir" 2>/dev/null || echo "Unknown")
            fi

            # Check status
            if [ -f "$checkpoint_dir/manifest.json" ]; then
                STATUS="✅ Valid"
            else
                STATUS="⚠️  No manifest"
            fi

            printf "%-40s  %-12s  %-20s  %s\n" "$NAME" "$SIZE" "$CREATED" "$STATUS"
        fi
    done

    echo ""
    echo "Total checkpoints: $(ls -1d $CHECKPOINT_BASE_DIR/*/ 2>/dev/null | wc -l | tr -d ' ')"
    echo ""
}

# Function: Verify checkpoint integrity
verify_checkpoint() {
    CHECKPOINT_NAME="$1"

    if [ -z "$CHECKPOINT_NAME" ]; then
        echo "Usage: $0 verify <checkpoint-name>"
        echo ""
        echo "Available checkpoints:"
        ls -1 "$CHECKPOINT_BASE_DIR" 2>/dev/null || echo "  (none)"
        exit 1
    fi

    CHECKPOINT_DIR="$CHECKPOINT_BASE_DIR/$CHECKPOINT_NAME"

    if [ ! -d "$CHECKPOINT_DIR" ]; then
        echo -e "${RED}❌ Checkpoint not found: $CHECKPOINT_NAME${NC}"
        exit 1
    fi

    echo "================================================================================"
    echo "Checkpoint Verification: $CHECKPOINT_NAME"
    echo "================================================================================"
    echo ""

    # Generate full report
    python3 -c "
import sys
import json
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import generate_checkpoint_report

checkpoint_path = Path('$CHECKPOINT_DIR')
report = generate_checkpoint_report(checkpoint_path)

# Display report
print(f'Checkpoint: {report[\"checkpoint_path\"]}')
print(f'Exists: {report[\"exists\"]}')
if 'created' in report:
    print(f'Created: {report[\"created\"]}')
if 'total_files' in report:
    print(f'Files: {report[\"total_files\"]}')
if 'total_size_mb' in report:
    print(f'Size: {report[\"total_size_mb\"]} MB')
print()

# Integrity check
if 'integrity_check' in report:
    ic = report['integrity_check']
    status = '✅ PASSED' if ic['passed'] else '❌ FAILED'
    print(f'Integrity Check: {status}')
    print(f'  Verified: {ic[\"verified_files\"]} files')
    print(f'  Failed: {ic[\"failed_files\"]} files')
    print(f'  Missing: {ic[\"missing_files\"]} files')
    print()

# YAML check
if 'yaml_syntax_check' in report:
    yc = report['yaml_syntax_check']
    status = '✅ PASSED' if yc['passed'] else '❌ FAILED'
    print(f'YAML Syntax Check: {status}')
    print(f'  Valid: {yc[\"valid_files\"]} files')
    print(f'  Invalid: {yc[\"invalid_files\"]} files')
    print(f'  Total YAML files: {yc[\"total_files\"]}')
    print()

# Overall status
overall = report.get('status', 'unknown')
if overall == 'valid':
    print('Overall Status: ✅ VALID')
    sys.exit(0)
else:
    print('Overall Status: ❌ INVALID')
    sys.exit(1)
"
}

# Function: Clean old checkpoints
clean_checkpoints() {
    KEEP_COUNT="${1:-5}"

    echo "================================================================================"
    echo "Checkpoint Cleanup"
    echo "================================================================================"
    echo ""
    echo "Keeping: $KEEP_COUNT most recent checkpoints"
    echo ""

    # Count checkpoints
    TOTAL_COUNT=$(ls -1d $CHECKPOINT_BASE_DIR/*/ 2>/dev/null | wc -l | tr -d ' ')

    if [ "$TOTAL_COUNT" -le "$KEEP_COUNT" ]; then
        echo "Only $TOTAL_COUNT checkpoints exist. No cleanup needed."
        return 0
    fi

    # List checkpoints by date (oldest first)
    CHECKPOINTS=($(ls -1td $CHECKPOINT_BASE_DIR/*/ 2>/dev/null))

    # Calculate how many to delete
    DELETE_COUNT=$((TOTAL_COUNT - KEEP_COUNT))

    echo "Will delete $DELETE_COUNT old checkpoints:"
    echo ""

    # Show what will be deleted
    for ((i=${#CHECKPOINTS[@]}-1; i>=${KEEP_COUNT}; i--)); do
        checkpoint="${CHECKPOINTS[$i]}"
        NAME=$(basename "$checkpoint")
        SIZE=$(du -sh "$checkpoint" 2>/dev/null | cut -f1)
        echo "  - $NAME ($SIZE)"
    done
    echo ""

    # Confirm deletion
    read -p "Delete these checkpoints? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        return 0
    fi

    # Delete old checkpoints
    DELETED=0
    for ((i=${#CHECKPOINTS[@]}-1; i>=${KEEP_COUNT}; i--)); do
        checkpoint="${CHECKPOINTS[$i]}"
        NAME=$(basename "$checkpoint")

        if rm -rf "$checkpoint"; then
            echo "  ✅ Deleted: $NAME"
            DELETED=$((DELETED + 1))
        else
            echo -e "  ${RED}❌ Failed to delete: $NAME${NC}"
        fi
    done

    echo ""
    echo "Deleted $DELETED checkpoints"
    echo "Remaining: $(ls -1d $CHECKPOINT_BASE_DIR/*/ 2>/dev/null | wc -l | tr -d ' ')"
}

# Function: Compare two checkpoints
compare_checkpoints() {
    CHECKPOINT1="$1"
    CHECKPOINT2="$2"

    if [ -z "$CHECKPOINT1" ] || [ -z "$CHECKPOINT2" ]; then
        echo "Usage: $0 compare <checkpoint1> <checkpoint2>"
        echo ""
        echo "Available checkpoints:"
        ls -1 "$CHECKPOINT_BASE_DIR" 2>/dev/null || echo "  (none)"
        exit 1
    fi

    CHECKPOINT1_DIR="$CHECKPOINT_BASE_DIR/$CHECKPOINT1"
    CHECKPOINT2_DIR="$CHECKPOINT_BASE_DIR/$CHECKPOINT2"

    if [ ! -d "$CHECKPOINT1_DIR" ]; then
        echo -e "${RED}❌ Checkpoint not found: $CHECKPOINT1${NC}"
        exit 1
    fi

    if [ ! -d "$CHECKPOINT2_DIR" ]; then
        echo -e "${RED}❌ Checkpoint not found: $CHECKPOINT2${NC}"
        exit 1
    fi

    echo "================================================================================"
    echo "Checkpoint Comparison"
    echo "================================================================================"
    echo ""
    echo "Checkpoint 1: $CHECKPOINT1"
    echo "Checkpoint 2: $CHECKPOINT2"
    echo ""

    # Run comparison
    python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import compare_checkpoints

checkpoint1 = Path('$CHECKPOINT1_DIR')
checkpoint2 = Path('$CHECKPOINT2_DIR')

report = compare_checkpoints(checkpoint1, checkpoint2)

if 'error' in report:
    print(f'❌ Error: {report[\"error\"]}')
    sys.exit(1)

# Display comparison
print(f'Compared at: {report[\"compared_at\"]}')
print()

print(f'Files in both: {report[\"files_in_both\"]}')
print(f'Files only in checkpoint 1: {len(report[\"files_only_in_checkpoint1\"])}')
print(f'Files only in checkpoint 2: {len(report[\"files_only_in_checkpoint2\"])}')
print(f'Changed files: {len(report[\"changed_files\"])}')
print(f'Total changes: {report[\"total_changes\"]}')
print()

# Show changes
if report['files_only_in_checkpoint1']:
    print('Files only in checkpoint 1:')
    for f in report['files_only_in_checkpoint1'][:10]:
        print(f'  - {f}')
    if len(report['files_only_in_checkpoint1']) > 10:
        print(f'  ... and {len(report[\"files_only_in_checkpoint1\"]) - 10} more')
    print()

if report['files_only_in_checkpoint2']:
    print('Files only in checkpoint 2:')
    for f in report['files_only_in_checkpoint2'][:10]:
        print(f'  + {f}')
    if len(report['files_only_in_checkpoint2']) > 10:
        print(f'  ... and {len(report[\"files_only_in_checkpoint2\"]) - 10} more')
    print()

if report['changed_files']:
    print('Changed files:')
    for change in report['changed_files'][:10]:
        print(f'  ~ {change[\"file\"]}')
        print(f'    Size: {change[\"size1\"]} → {change[\"size2\"]} bytes')
    if len(report['changed_files']) > 10:
        print(f'  ... and {len(report[\"changed_files\"]) - 10} more')
    print()
"
}

# Main command dispatcher
case "$COMMAND" in
    list)
        list_checkpoints
        ;;
    verify)
        verify_checkpoint "$2"
        ;;
    clean)
        clean_checkpoints "$2"
        ;;
    compare)
        compare_checkpoints "$2" "$3"
        ;;
    *)
        echo "Usage: $0 {list|verify|clean|compare} [args...]"
        echo ""
        echo "Commands:"
        echo "  list              - List all checkpoints"
        echo "  verify <name>     - Verify checkpoint integrity"
        echo "  clean [keep]      - Remove old checkpoints (keep last N, default 5)"
        echo "  compare <c1> <c2> - Compare two checkpoints"
        echo ""
        exit 1
        ;;
esac
