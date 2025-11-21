#!/bin/bash
# Create Integrity Checkpoint
#
# Creates a timestamped checkpoint of .vibey/ directory with verification.
# Integrates with Sprint 0 rollback procedures.
#
# Usage: ./create-integrity-checkpoint.sh [checkpoint-name]
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CHECKPOINT_NAME="${1:-checkpoint_$TIMESTAMP}"
CHECKPOINT_BASE_DIR=".vibey-checkpoints"
CHECKPOINT_DIR="$CHECKPOINT_BASE_DIR/$CHECKPOINT_NAME"

echo "================================================================================"
echo "Vibey Integrity Checkpoint Creation"
echo "================================================================================"
echo ""
echo "Checkpoint name: $CHECKPOINT_NAME"
echo "Checkpoint path: $CHECKPOINT_DIR"
echo ""

# Check if running from repository root
if [ ! -d ".vibey" ]; then
    echo -e "${RED}❌ Error: .vibey directory not found${NC}"
    echo "   Run this script from the repository root"
    exit 1
fi

# Check disk space (need at least 100MB free)
AVAILABLE_SPACE=$(df -k . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=$((100 * 1024))  # 100MB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo -e "${RED}❌ Error: Insufficient disk space${NC}"
    echo "   Available: $(($AVAILABLE_SPACE / 1024)) MB"
    echo "   Required: $(($REQUIRED_SPACE / 1024)) MB"
    exit 1
fi

# Check if checkpoint already exists
if [ -d "$CHECKPOINT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Warning: Checkpoint already exists${NC}"
    echo "   Path: $CHECKPOINT_DIR"
    read -p "   Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
    rm -rf "$CHECKPOINT_DIR"
fi

# Create checkpoint directory
echo "Creating checkpoint directory..."
mkdir -p "$CHECKPOINT_DIR"

# Copy .vibey/ directory
echo "Copying .vibey/ directory..."
cp -R .vibey "$CHECKPOINT_DIR/"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to copy .vibey/ directory${NC}"
    rm -rf "$CHECKPOINT_DIR"
    exit 1
fi

# Copy key framework files
echo "Copying framework Python files..."
mkdir -p "$CHECKPOINT_DIR/vibey"
if [ -d "vibey/operations/roadmap" ]; then
    cp -R vibey/operations/roadmap "$CHECKPOINT_DIR/vibey/"
fi
if [ -d "vibey/roadmap" ]; then
    cp -R vibey/roadmap "$CHECKPOINT_DIR/vibey/"
fi

# Export git state
echo "Exporting git state..."
git log -1 --format="%H%n%an%n%ae%n%at%n%s" > "$CHECKPOINT_DIR/git-state.txt" 2>/dev/null || echo "No git repository" > "$CHECKPOINT_DIR/git-state.txt"
git status --short > "$CHECKPOINT_DIR/git-status.txt" 2>/dev/null || echo "No git repository" > "$CHECKPOINT_DIR/git-status.txt"

# Generate manifest with checksums
echo "Generating manifest and checksums..."
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import generate_manifest

checkpoint_path = Path('$CHECKPOINT_DIR')
manifest_path = checkpoint_path / 'manifest.json'
manifest = generate_manifest(checkpoint_path, manifest_path)

print(f'  Files: {manifest[\"total_files\"]}')
print(f'  Size: {manifest[\"total_size\"] / (1024*1024):.2f} MB')
"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Could not generate manifest${NC}"
fi

# Create README
cat > "$CHECKPOINT_DIR/README.md" <<EOF
# Integrity Checkpoint: $CHECKPOINT_NAME

**Created:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Git Commit:** $(git log -1 --format="%H" 2>/dev/null || echo "Unknown")
**Created By:** $(git config user.name 2>/dev/null || echo "Unknown")

## Contents

- \`.vibey/\` - Complete roadmap state
- \`vibey/\` - Framework Python files
- \`git-state.txt\` - Git commit information
- \`git-status.txt\` - Git working tree status
- \`manifest.json\` - File checksums and metadata

## Restoration

To restore this checkpoint:

\`\`\`bash
./scripts/restore-integrity-checkpoint.sh $CHECKPOINT_NAME
\`\`\`

Or verify without restoring:

\`\`\`bash
./scripts/restore-integrity-checkpoint.sh $CHECKPOINT_NAME --verify-only
\`\`\`

## Verification

To verify checkpoint integrity:

\`\`\`bash
python3 -c "
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import verify_checkpoint_integrity

success, report = verify_checkpoint_integrity(Path('$CHECKPOINT_DIR'))
print('✅ Valid' if success else '❌ Invalid')
print(f'Verified: {report[\"verified_files\"]} files')
print(f'Failed: {report[\"failed_files\"]} files')
"
\`\`\`

---
*Checkpoint created by Vibey Framework v1.3.0*
EOF

# Verify checkpoint integrity
echo "Verifying checkpoint integrity..."
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from vibey.operations.roadmap.checkpoint_verifier import verify_checkpoint_integrity

success, report = verify_checkpoint_integrity(Path('$CHECKPOINT_DIR'))

if success:
    print('✅ Checkpoint integrity verified')
    print(f'  Verified: {report[\"verified_files\"]} files')
    sys.exit(0)
else:
    print('❌ Checkpoint verification failed')
    print(f'  Failed: {report[\"failed_files\"]} files')
    print(f'  Missing: {report[\"missing_files\"]} files')
    sys.exit(1)
"

VERIFY_EXIT=$?

# Final report
echo ""
echo "================================================================================"
if [ $VERIFY_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Checkpoint created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Checkpoint created with warnings${NC}"
fi
echo "================================================================================"
echo ""
echo "Checkpoint: $CHECKPOINT_NAME"
echo "Location: $CHECKPOINT_DIR"
echo "Size: $(du -sh "$CHECKPOINT_DIR" | cut -f1)"
echo ""
echo "To restore: ./scripts/restore-integrity-checkpoint.sh $CHECKPOINT_NAME"
echo "To verify:  ./scripts/manage-checkpoints.sh verify $CHECKPOINT_NAME"
echo ""

exit $VERIFY_EXIT
