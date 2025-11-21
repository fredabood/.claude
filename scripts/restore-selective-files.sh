#!/bin/bash
# Restore Selective Files from Checkpoint
#
# Restores specific files from checkpoint using glob patterns.
#
# Usage: ./restore-selective-files.sh <checkpoint-name> <file-pattern>
#
# Examples:
#   ./restore-selective-files.sh checkpoint_20251120 ".vibey/roadmap/*/track.yaml"
#   ./restore-selective-files.sh checkpoint_20251120 ".vibey/roadmap/roadmap-system/*"
#
# Sprint: roadmap-integrity-fixes-1
# Task: roadmap-integrity-fixes-1-task-002

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CHECKPOINT_NAME="$1"
FILE_PATTERN="$2"
CHECKPOINT_BASE_DIR=".vibey-checkpoints"
CHECKPOINT_DIR="$CHECKPOINT_BASE_DIR/$CHECKPOINT_NAME"

if [ -z "$CHECKPOINT_NAME" ] || [ -z "$FILE_PATTERN" ]; then
    echo "Usage: $0 <checkpoint-name> <file-pattern>"
    echo ""
    echo "Examples:"
    echo "  $0 checkpoint_20251120 \".vibey/roadmap/*/track.yaml\""
    echo "  $0 checkpoint_20251120 \".vibey/roadmap/roadmap-system/*\""
    echo ""
    exit 1
fi

echo "================================================================================"
echo "Selective File Restoration from Checkpoint"
echo "================================================================================"
echo ""
echo "Checkpoint: $CHECKPOINT_NAME"
echo "Pattern: $FILE_PATTERN"
echo ""

# Validate checkpoint exists
if [ ! -d "$CHECKPOINT_DIR" ]; then
    echo -e "${RED}❌ Error: Checkpoint not found${NC}"
    echo "   Path: $CHECKPOINT_DIR"
    exit 1
fi

# Find matching files in checkpoint
echo "Finding matching files in checkpoint..."
cd "$CHECKPOINT_DIR"
MATCHED_FILES=($(eval "ls -1 $FILE_PATTERN 2>/dev/null" || true))
cd - > /dev/null

if [ ${#MATCHED_FILES[@]} -eq 0 ]; then
    echo -e "${RED}❌ No files match pattern${NC}"
    echo "   Pattern: $FILE_PATTERN"
    exit 1
fi

echo "Found ${#MATCHED_FILES[@]} matching files:"
for file in "${MATCHED_FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Confirm restoration
read -p "Restore these files? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Create backup of current versions
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$CHECKPOINT_BASE_DIR/selective-backup_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "Creating backup of current files..."
BACKUP_COUNT=0

for file in "${MATCHED_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Create directory structure in backup
        FILE_DIR=$(dirname "$file")
        mkdir -p "$BACKUP_DIR/$FILE_DIR"

        # Copy current version to backup
        cp "$file" "$BACKUP_DIR/$file"
        BACKUP_COUNT=$((BACKUP_COUNT + 1))
    fi
done

echo "  ✅ Backed up $BACKUP_COUNT files to: $BACKUP_DIR"

# Restore files
echo "Restoring files from checkpoint..."
RESTORE_COUNT=0
FAILED_COUNT=0

for file in "${MATCHED_FILES[@]}"; do
    SOURCE="$CHECKPOINT_DIR/$file"
    DEST="$file"

    if [ -f "$SOURCE" ]; then
        # Create directory if needed
        mkdir -p "$(dirname "$DEST")"

        # Copy file
        if cp "$SOURCE" "$DEST"; then
            RESTORE_COUNT=$((RESTORE_COUNT + 1))

            # Validate YAML if it's a .yaml file
            if [[ "$file" == *.yaml ]]; then
                python3 -c "
import yaml
try:
    with open('$DEST') as f:
        yaml.safe_load(f)
    print('  ✅ $file (YAML valid)')
except Exception as e:
    print('  ❌ $file (YAML invalid: ' + str(e) + ')')
    exit(1)
" || FAILED_COUNT=$((FAILED_COUNT + 1))
            else
                echo "  ✅ $file"
            fi
        else
            echo -e "  ${RED}❌ Failed to restore: $file${NC}"
            FAILED_COUNT=$((FAILED_COUNT + 1))
        fi
    else
        echo -e "  ${YELLOW}⚠️  Not in checkpoint: $file${NC}"
    fi
done

# Final report
echo ""
echo "================================================================================"
if [ $FAILED_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ Selective restoration completed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Selective restoration completed with $FAILED_COUNT failures${NC}"
fi
echo "================================================================================"
echo ""
echo "Restored: $RESTORE_COUNT files"
echo "Failed: $FAILED_COUNT files"
echo "Backup: $BACKUP_DIR"
echo ""

if [ $FAILED_COUNT -gt 0 ]; then
    echo "To rollback failed restorations:"
    echo "  ./scripts/restore-selective-files.sh selective-backup_$TIMESTAMP \"$FILE_PATTERN\""
    echo ""
    exit 1
fi

exit 0
