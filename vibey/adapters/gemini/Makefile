# Vibey Gemini Extension Build Makefile
#
# Usage:
#   make build          - Build extension to ./dist/vibey-gemini-extension
#   make validate       - Validate existing export for drift
#   make clean          - Remove build artifacts
#   make install-local  - Install extension to ~/.gemini/
#   make test           - Run generator tests

.PHONY: build validate clean install-local test help

# Configuration
DIST_DIR ?= ./dist/vibey-gemini-extension
VIBEY_ROOT ?= $(shell pwd)
PYTHON ?= python3

# Default target
help:
	@echo "Vibey Gemini Extension Builder"
	@echo ""
	@echo "Usage:"
	@echo "  make build          - Build extension to $(DIST_DIR)"
	@echo "  make validate       - Validate existing export for drift"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make install-local  - Install extension to ~/.gemini/"
	@echo "  make test           - Run generator tests"
	@echo ""
	@echo "Configuration:"
	@echo "  DIST_DIR=$(DIST_DIR)"
	@echo "  VIBEY_ROOT=$(VIBEY_ROOT)"

# Build the Gemini extension
build:
	@echo "Building Vibey Gemini Extension..."
	@$(PYTHON) -c "\
from pathlib import Path; \
from vibey.adapters.gemini import GeminiAdapter; \
adapter = GeminiAdapter(Path('$(VIBEY_ROOT)')); \
result = adapter.export(Path('$(DIST_DIR)')); \
print(f'Success: {result.success}'); \
print(f'Files: {len(result.files_created)}'); \
print(f'Agents: {result.context.agents_count if result.context else 0}'); \
print(f'Workflows: {result.context.workflows_count if result.context else 0}'); \
print(f'Commands: {len(result.commands.commands) if result.commands else 0}'); \
exit(0 if result.success else 1)"
	@echo ""
	@echo "Extension built to: $(DIST_DIR)"
	@echo "Install with: gemini extensions install $(DIST_DIR)"

# Validate existing export for drift
validate:
	@echo "Validating Gemini export for drift..."
	@$(PYTHON) -c "\
from pathlib import Path; \
from vibey.adapters.gemini import GeminiAdapter; \
adapter = GeminiAdapter(Path('$(VIBEY_ROOT)')); \
is_valid, errors = adapter.validate_export(Path('$(DIST_DIR)')); \
if is_valid: \
    print('✓ No drift detected - export matches source'); \
else: \
    print('✗ Drift detected:'); \
    [print(f'  - {e}') for e in errors]; \
exit(0 if is_valid else 1)"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(DIST_DIR)
	@echo "Done."

# Install extension to local Gemini config
install-local: build
	@echo "Installing to ~/.gemini/..."
	@mkdir -p ~/.gemini/commands/vibey
	@mkdir -p ~/.gemini/extensions/vibey
	@cp -r $(DIST_DIR)/commands/vibey/* ~/.gemini/commands/vibey/
	@cp $(DIST_DIR)/GEMINI.md ~/.gemini/
	@cp $(DIST_DIR)/gemini-extension.json ~/.gemini/extensions/vibey/
	@cp $(DIST_DIR)/settings.json ~/.gemini/extensions/vibey/
	@echo ""
	@echo "Installed to ~/.gemini/"
	@echo "Commands available: /vibey:status, /vibey:sprint, etc."

# Run generator tests
test:
	@echo "Running generator tests..."
	@$(PYTHON) -m pytest vibey/adapters/gemini/tests/ -v

# Quick smoke test (no pytest required)
smoke-test:
	@echo "Running smoke test..."
	@$(PYTHON) -c "\
from pathlib import Path; \
from vibey.adapters.gemini import GeminiAdapter; \
from vibey.adapters.gemini.context_generator import GeminiContextGenerator; \
from vibey.adapters.gemini.command_generator import GeminiCommandGenerator; \
print('Testing GeminiContextGenerator...'); \
ctx = GeminiContextGenerator(Path('.')); \
result = ctx.generate(); \
assert result.agents_count > 0, 'No agents found'; \
print(f'  ✓ {result.agents_count} agents, {result.workflows_count} workflows'); \
print('Testing GeminiCommandGenerator...'); \
cmd = GeminiCommandGenerator(Path('.')); \
result = cmd.generate(); \
assert len(result.commands) > 0, 'No commands generated'; \
print(f'  ✓ {len(result.commands)} commands'); \
print('Testing GeminiAdapter.export (dry run)...'); \
adapter = GeminiAdapter(Path('.')); \
print('  ✓ Adapter initialized'); \
print(''); \
print('All smoke tests passed!')"
