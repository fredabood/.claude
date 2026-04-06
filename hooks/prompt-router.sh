#!/usr/bin/env bash
# prompt-router.sh — Auto-suggest skills from prompt keywords
# UserPromptSubmit hook — advisory only (exit 0 always)

# Read the user prompt from stdin
PROMPT=$(cat)

# Extract the actual prompt text (it comes as JSON)
# The prompt text is in the input
TEXT=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# Skill suggestion based on keyword matching
SUGGESTION=""

# Deploy patterns
if echo "$TEXT" | grep -qE 'deploy|service|stack|container|caddy'; then
  SUGGESTION="/deploy-service or /deploy-stack"
fi

# Ticket creation patterns
if echo "$TEXT" | grep -qE 'create.*(ticket|issue|task)|new ticket|new issue'; then
  SUGGESTION="/create-ticket"
fi

# Status patterns
if echo "$TEXT" | grep -qE 'status|sprint|board|backlog'; then
  SUGGESTION="/status"
fi

# Blocker patterns
if echo "$TEXT" | grep -qE 'block|stuck|waiting|depend'; then
  SUGGESTION="/check-blockers"
fi

# Planning patterns
if echo "$TEXT" | grep -qE 'plan.*(sprint|next|work)|prioritize|roadmap'; then
  SUGGESTION="/plan-sprint"
fi

# Start task patterns
if echo "$TEXT" | grep -qE 'start.*(work|task|ticket)|pick up|begin'; then
  SUGGESTION="/start-task"
fi

# Health check patterns
if echo "$TEXT" | grep -qE 'health|check.*service|stack.*status|docker.*status'; then
  SUGGESTION="/health-check or /stack-status"
fi

# Discovery patterns
if echo "$TEXT" | grep -qE 'discover|analyze.*code|tech.*stack|codebase'; then
  SUGGESTION="/discovery"
fi

# Scraper patterns
if echo "$TEXT" | grep -qE 'scrape|crawl|fetch|ingest|connector'; then
  SUGGESTION="/implement-feature (scraper template available)"
fi

# Handoff patterns
if echo "$TEXT" | grep -qE 'handoff|hand off|session.*end|wrap up'; then
  SUGGESTION="/handoff"
fi

# Only output if we have a suggestion (advisory, never blocks)
if [ -n "$SUGGESTION" ]; then
  echo "[INFO] Suggested skill: $SUGGESTION"
fi

exit 0
