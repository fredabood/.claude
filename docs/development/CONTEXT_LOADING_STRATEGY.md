# Context Loading Strategy

**Version:** 1.0
**Date:** 2025-11-07
**Status:** Design Specification
**Related:** PLATFORM_AGNOSTIC_ARCHITECTURE.md, YAML_MARKDOWN_SEPARATION.md

---

## Overview

This document specifies the context loading strategy for the Vibey roadmap system, addressing the **context explosion problem** that occurs when tasks have deep dependency chains.

**Problem:** Without mitigation, a task with 10 dependencies could require loading 40+ markdown files (exponential growth).

**Solution:** Hybrid approach with dependency summaries, context modes, and hierarchical loading.

---

## Table of Contents

1. [Problem Analysis](#problem-analysis)
2. [Solution Architecture](#solution-architecture)
3. [Context Loading Modes](#context-loading-modes)
4. [Hierarchical Loading](#hierarchical-loading)
5. [Auto-Generation](#auto-generation)
6. [Implementation Guide](#implementation-guide)
7. [Performance Optimization](#performance-optimization)
8. [Testing Strategy](#testing-strategy)

---

## Problem Analysis

### Exponential Context Growth

#### Simple Example
```
Task: backend-3-task-005
  └── Depends on: backend-2-task-003
      └── Depends on: backend-1-task-001

Without mitigation:
- Load backend-3 docs (4 files × ~1,250 tokens = 5,000 tokens)
- Load backend-2 docs (4 files × ~1,250 tokens = 5,000 tokens)
- Load backend-1 docs (4 files × ~1,250 tokens = 5,000 tokens)

Total: 15,000 tokens for 3 sprints
```

#### Complex Example
```
Task: payment-processing-1-task-012
  ├── Depends on: auth-2-task-008 (authentication)
  │   ├── Depends on: users-1-task-003 (user model)
  │   │   └── Depends on: infra-1-task-001 (database)
  │   └── Depends on: crypto-1-task-002 (password hashing)
  │
  ├── Depends on: billing-1-task-005 (billing model)
  │   └── Depends on: users-1-task-003 (user model)
  │       └── Depends on: infra-1-task-001 (database)
  │
  └── Depends on: notifications-1-task-004 (email)
      └── Depends on: templates-1-task-002 (email templates)

Dependency count:
- Direct: 3 tasks
- Transitive: 6 tasks
- Total unique: 8 sprints

Without mitigation:
8 sprints × 4 files × ~1,250 tokens = 40,000 tokens

With model context limit of 200K tokens:
- 5 such tasks = entire context window!
- No room for code, current work, or responses
```

### Why This Matters

**1. Context Window Limits**
- Claude Sonnet: 200K tokens
- Complex task + dependencies = 40K+ tokens
- Only 5 tasks before hitting limits

**2. Performance Degradation**
- Reading 40 markdown files takes time
- Parsing and tokenizing overhead
- Slower responses for users

**3. Relevance Dilution**
- Not all dependency context is equally important
- Deep dependencies rarely need full detail
- Important info gets lost in noise

**4. Cognitive Overload**
- Too much context confuses the model
- Harder to focus on current task
- More likely to make mistakes

---

## Solution Architecture

### Hybrid Multi-Strategy Approach

```
┌─────────────────────────────────────────────────────┐
│ Context Loading Strategy                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Dependency Summaries (Sprint-Level)             │
│     ├─ Auto-generated on sprint completion          │
│     ├─ 500 words per sprint                         │
│     └─ Stored in sprint YAML                        │
│                                                     │
│  2. Task Summaries (Task-Level)                     │
│     ├─ Auto-generated on task completion            │
│     ├─ Key outputs, interfaces, gotchas             │
│     └─ Stored in sprint YAML                        │
│                                                     │
│  3. Context Modes (Configurable)                    │
│     ├─ Minimal: Outputs only (~100 tokens)          │
│     ├─ Summary: Summaries (~700 tokens)             │
│     └─ Full: All docs (~5,700 tokens)               │
│                                                     │
│  4. Hierarchical Loading (Distance-Based)           │
│     ├─ Direct deps (distance=1): Summary mode       │
│     ├─ Transitive deps (distance=2): Minimal mode   │
│     └─ Deep deps (distance>2): Skip                 │
│                                                     │
│  5. Lazy Loading (Performance)                      │
│     ├─ Load on demand, not upfront                  │
│     ├─ Cache loaded summaries                       │
│     └─ Parallel loading where possible              │
│                                                     │
│  6. Preparation Mode (Deep Analysis)                │
│     ├─ User-triggered for complex tasks             │
│     ├─ Uses full context window for analysis        │
│     ├─ Generates task-specific prep document        │
│     └─ Stored in sprint_docs/<sprint>/prep/         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Context Loading Modes

### Mode Comparison

| Mode | Tokens | Use Case | What's Loaded |
|------|--------|----------|---------------|
| **Minimal** | ~100 | Weak dependencies, known interfaces | Sprint ID, name, status, task outputs only |
| **Summary** | ~700 | Most dependencies (default) | dependency_summary + task_summary |
| **Full** | ~5,700 | Complex deps, architecture review | All sprint docs + summaries |

### Mode Selection Algorithm

```python
def select_context_mode(task: Task, dependency: Dependency) -> str:
    """Select context mode for a dependency."""

    # 1. User override takes precedence
    if dependency.context_mode:
        return dependency.context_mode

    # 2. Calculate dependency distance
    distance = calculate_distance(task, dependency.target_id)

    # 3. Distance-based default
    if distance == 1:
        return "summary"  # Direct dependencies
    elif distance == 2:
        return "minimal"  # One step removed
    else:
        return "none"     # Skip deep dependencies

def calculate_distance(task: Task, target_id: str) -> int:
    """Calculate dependency distance using BFS."""

    queue = [(task, 0)]
    visited = set()

    while queue:
        current, dist = queue.pop(0)

        if current.id == target_id:
            return dist

        if current.id in visited:
            continue

        visited.add(current.id)

        for dep in current.dependencies:
            dep_task = load_task(dep.target_id)
            queue.append((dep_task, dist + 1))

    return float('inf')  # Not found
```

---

## Hierarchical Loading

### Distance-Based Loading Strategy

```
Current Task: payment-1-task-012
  ↓
┌─────────────────────────────────────────────────┐
│ Distance 1: Direct Dependencies                 │
│ Mode: SUMMARY (~700 tokens each)                │
├─────────────────────────────────────────────────┤
│ - auth-2-task-008 (authentication)              │
│ - billing-1-task-005 (billing model)            │
│ - notifications-1-task-004 (email)              │
│                                                 │
│ Total: 3 × 700 = 2,100 tokens                   │
└─────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────┐
│ Distance 2: Transitive Dependencies             │
│ Mode: MINIMAL (~50 tokens each)                 │
├─────────────────────────────────────────────────┤
│ - users-1-task-003 (user model)                 │
│ - crypto-1-task-002 (password hashing)          │
│ - templates-1-task-002 (email templates)        │
│                                                 │
│ Total: 3 × 50 = 150 tokens                      │
└─────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────┐
│ Distance 3+: Deep Dependencies                  │
│ Mode: NONE (skipped)                            │
├─────────────────────────────────────────────────┤
│ - infra-1-task-001 (database)                   │
│   ↑ Skipped (information available via users-1) │
└─────────────────────────────────────────────────┘

Total Context: 2,100 + 150 = 2,250 tokens
vs. Full Loading: 8 sprints × 5,000 = 40,000 tokens
Reduction: 94%
```

### Dependency Graph Analysis

```python
class DependencyGraph:
    """Analyzes dependency structure for optimal loading."""

    def get_loading_plan(self, task: Task) -> LoadingPlan:
        """Generate optimal context loading plan."""

        # Build dependency graph
        graph = self.build_graph(task)

        # Group by distance
        distance_groups = self.group_by_distance(graph)

        # Apply modes
        loading_plan = LoadingPlan()

        for distance, deps in distance_groups.items():
            mode = self.get_mode_for_distance(distance)

            for dep in deps:
                loading_plan.add(
                    dependency=dep,
                    mode=mode,
                    priority=self.calculate_priority(dep, distance)
                )

        # Deduplicate (handle diamond dependencies)
        loading_plan.deduplicate()

        return loading_plan

    def deduplicate(self, plan: LoadingPlan) -> LoadingPlan:
        """Handle diamond dependencies (same dep at multiple distances)."""

        # If same dependency appears at distance 1 and 2,
        # keep the distance 1 entry (closer = more detail)

        seen = {}
        deduped = LoadingPlan()

        for entry in sorted(plan, key=lambda e: e.distance):
            if entry.dependency_id not in seen:
                seen[entry.dependency_id] = entry
                deduped.add(entry)

        return deduped
```

---

## Preparation Mode: Deep Dependency Analysis

### Overview

**Preparation Mode** is a user-triggered deep analysis phase for complex tasks with large dependency graphs.

**Purpose:** Allow the model to use a full context window to thoroughly analyze all dependencies and generate a task-specific preparation document.

**When to use:**
- Complex tasks with 5+ dependencies
- Critical integration points
- Tasks requiring deep understanding of multiple systems
- When you want to "think before you code"

### How It Works

```
User runs: roadmap prepare backend-5-task-007

1. Load ALL dependency docs (no context limits)
   - Full sprint docs for all dependencies
   - Transitive dependencies included
   - Architecture decisions, learnings, gotchas

2. AI analyzes implications for THIS specific task
   - How dependencies interact
   - What outputs are needed from each
   - Integration patterns
   - Potential conflicts or issues
   - Critical gotchas to avoid

3. Generate task-specific preparation document
   - Saved to: .vibey/sprint_docs/backend-5/prep/task-007.md
   - Tailored to the upcoming task
   - Comprehensive but focused

4. Reference during task execution
   - Read prep doc instead of all dependency docs
   - Focused, actionable context
   - Persistent artifact (committed to git)
```

### Preparation Document Structure

```markdown
# Task Preparation: Implement Payment Processing
# Task ID: backend-5-task-007
# Generated: 2025-11-07T20:30:00Z

## Task Overview
Implement Stripe payment processing with user authentication,
billing model integration, and transaction notifications.

## Dependency Analysis

### 1. Authentication (backend-4-task-012)

**What it provides:**
- JWT token validation via `validateToken(token)` middleware
- User object with `{ id, email, role }`
- Authentication errors throw `AuthError` (401)

**Implications for payment processing:**
- MUST use `validateToken` middleware on ALL payment endpoints
- Payment records should link to `user.id` (authenticated user)
- Handle `AuthError` gracefully (return 401 to client)

**Integration pattern:**
```python
from auth import validateToken

@app.post("/api/payments")
async def create_payment(
    request: Request,
    user: User = Depends(validateToken)  # ← Use this pattern
):
    payment = Payment(
        user_id=user.id,  # ← Link to authenticated user
        amount=request.amount
    )
```

**Gotchas:**
- validateToken is async (use await)
- Don't import from auth.py in auth-related files (circular import)
- Tokens expire after 15 minutes (ensure fresh tokens)

---

### 2. Billing Model (backend-3-task-008)

**What it provides:**
- `BillingAccount` model with `user_id`, `stripe_customer_id`
- `get_or_create_billing_account(user_id)` helper
- Payment method storage (credit cards)

**Implications for payment processing:**
- Check if user has billing account BEFORE processing payment
- Create billing account if missing (seamless UX)
- Link payment to `billing_account.id`

**Integration pattern:**
```python
from billing import get_or_create_billing_account

async def create_payment(user: User, amount: Decimal):
    # Get or create billing account
    billing_account = await get_or_create_billing_account(user.id)

    # Use Stripe customer ID
    stripe_charge = stripe.Charge.create(
        amount=int(amount * 100),  # Stripe uses cents
        customer=billing_account.stripe_customer_id
    )
```

**Gotchas:**
- Stripe amounts in CENTS (multiply by 100)
- Handle case where user has no payment method on file
- Billing account creation can fail (Stripe API errors)

---

### 3. Notifications (backend-4-task-009)

**What it provides:**
- `send_email(user_id, template, context)` function
- Email templates: `payment_success`, `payment_failed`
- Async email sending (doesn't block)

**Implications for payment processing:**
- Send email AFTER payment succeeds/fails
- Don't await email sending (fire and forget)
- Include receipt info in email context

**Integration pattern:**
```python
from notifications import send_email

# After successful payment
send_email(
    user_id=user.id,
    template="payment_success",
    context={
        "amount": payment.amount,
        "receipt_url": payment.receipt_url,
        "transaction_id": payment.id
    }
)
# Don't await - email sends in background
```

**Gotchas:**
- Email failures shouldn't fail payment (already charged!)
- Log email failures for debugging
- Email templates expect specific context fields

---

## Critical Integration Points

### 1. Payment Flow
```
Request → Validate Auth → Get Billing Account → Process Stripe Charge
  → Save Payment Record → Send Email → Return Receipt
```

### 2. Error Handling
- **AuthError (401):** User not authenticated → return 401
- **BillingError:** No payment method → return 400 "Add payment method"
- **StripeError:** Payment declined → return 400 with decline reason
- **DatabaseError:** Save failed → REFUND charge, return 500

### 3. Race Conditions
- User could make multiple payment requests simultaneously
- Use database transaction + unique constraint on `idempotency_key`
- Stripe has idempotency built-in (use same key)

---

## Key Learnings from Dependencies

### From backend-4 (Authentication sprint):
- "Always validate server-side even if frontend validates"
- "Circular imports: separate auth.py from other modules"
- "Use refresh token rotation for security"

### From backend-3 (Billing sprint):
- "Stripe amounts are in CENTS, not dollars (common mistake!)"
- "Test with Stripe test mode cards (4242 4242 4242 4242)"
- "Handle 3D Secure (SCA) for European customers"

### From backend-2 (Infrastructure sprint):
- "Use database transactions for financial operations"
- "Add comprehensive logging (correlation IDs)"
- "Set up error monitoring (Sentry) for payment failures"

---

## Potential Issues to Avoid

### 1. Double Charging
**Problem:** User clicks "Pay" twice, gets charged twice
**Solution:** Use idempotency keys (Stripe + database)

### 2. Charge Success but Save Fails
**Problem:** Stripe charge succeeds but database save fails → user charged, no record
**Solution:**
- Try to save FIRST (pre-flight check)
- If save fails after charge, log error + queue refund
- Use Stripe webhooks as backup

### 3. Amount Mismatch
**Problem:** Frontend sends $10, backend charges $100
**Solution:**
- Validate amount server-side
- Use fixed prices from database (don't trust client)
- Log amount discrepancies

### 4. Currency Issues
**Problem:** User in EUR, charged in USD
**Solution:**
- Detect user currency from billing account
- Convert or use multi-currency Stripe setup
- Display currency clearly in UI

---

## Implementation Checklist

Before starting, ensure:
- [ ] Stripe API keys configured (test mode)
- [ ] Database migration for `payments` table
- [ ] Idempotency key strategy defined
- [ ] Error monitoring set up (Sentry)
- [ ] Email templates exist (`payment_success`, `payment_failed`)

During implementation:
- [ ] Use `validateToken` middleware on ALL endpoints
- [ ] Use database transactions for financial ops
- [ ] Add comprehensive logging (correlation IDs)
- [ ] Test with Stripe test cards
- [ ] Handle ALL error cases gracefully
- [ ] Don't await email sending (fire and forget)

After implementation:
- [ ] Test double-charge prevention
- [ ] Test charge-success-but-save-fails scenario
- [ ] Verify email notifications work
- [ ] Check error monitoring captures issues
- [ ] Security review (PCI compliance basics)

---

## Recommended Implementation Order

1. **Database setup** (30 min)
   - Create `payments` table
   - Add indexes, constraints
   - Test migration

2. **Core payment endpoint** (2 hours)
   - POST /api/payments
   - Auth validation
   - Billing account check
   - Basic Stripe integration

3. **Error handling** (1 hour)
   - Handle all error types
   - Logging
   - Error responses

4. **Idempotency** (1 hour)
   - Add idempotency_key
   - Test double-charge prevention

5. **Notifications** (30 min)
   - Email on success/failure
   - Test templates

6. **Testing** (1 hour)
   - Unit tests
   - Integration tests
   - Error scenario tests

**Total estimate:** 6 hours

---

## Questions to Resolve

Before starting, clarify:
1. What currencies do we support? (USD only? Multi-currency?)
2. Payment methods? (Credit card only? ACH? PayPal?)
3. Refund policy? (Automatic? Manual approval?)
4. 3D Secure / SCA handling? (Required for EU?)
5. Webhook handling? (Should we implement webhooks now?)

---

## References

**Full dependency docs:**
- `.vibey/sprint_docs/backend-4/` - Authentication implementation
- `.vibey/sprint_docs/backend-3/` - Billing model and Stripe setup
- `.vibey/sprint_docs/backend-2/` - Infrastructure and database

**External resources:**
- Stripe API docs: https://stripe.com/docs/api
- Stripe test cards: https://stripe.com/docs/testing
- PCI compliance: https://stripe.com/docs/security

---

**This preparation document was generated by analyzing all dependency documentation.
Use this as your primary reference during task implementation.**
```

### Command Syntax

```bash
# Generate preparation document
roadmap prepare <task-id>

# Options
roadmap prepare <task-id> --regenerate     # Regenerate if exists
roadmap prepare <task-id> --depth <N>      # Max dependency depth (default: all)
roadmap prepare <task-id> --focus <aspect> # Focus analysis (integration, errors, etc.)

# View preparation document
roadmap prepare <task-id> --show

# List tasks with preparation docs
roadmap prepare --list
```

### YAML Schema Addition

```yaml
# .vibey/tasks/backend-5-tasks.yaml
- id: "backend-5-task-007"
  name: "Implement payment processing"

  # ... existing fields ...

  # NEW: Preparation document metadata
  preparation:
    document: "sprint_docs/backend-5/prep/task-007.md"
    generated: "2025-11-07T20:30:00Z"
    dependencies_analyzed: 8
    context_tokens: 45000  # Context used during analysis
    model_used: "claude-sonnet-4-5"
```

### Implementation

```python
# framework/scripts/roadmap_prepare.py

def prepare_task(task_id: str, regenerate: bool = False):
    """Generate preparation document for complex task."""

    task = load_task(task_id)

    # Check if already exists
    prep_path = get_prep_path(task)
    if prep_path.exists() and not regenerate:
        print(f"Preparation document already exists: {prep_path}")
        print(f"Use --regenerate to recreate")
        return

    # Load ALL dependency docs (full context)
    print(f"Loading dependencies for {task_id}...")
    deps = load_all_dependencies(task, max_depth=None)  # No limit

    print(f"Analyzing {len(deps)} dependencies...")
    print(f"Context size: ~{estimate_context_size(deps):,} tokens")

    # Generate preparation prompt
    prompt = generate_prep_prompt(task, deps)

    # Call Claude API to generate prep document
    print(f"Generating preparation document (this may take 30-60 seconds)...")
    prep_doc = call_claude_api(prompt)

    # Save preparation document
    save_prep_document(task, prep_doc)

    # Update task YAML with prep metadata
    update_task_preparation_metadata(task, prep_doc)

    print(f"✅ Preparation document created: {prep_path}")
    print(f"   Read before starting: cat {prep_path}")

def generate_prep_prompt(task: Task, deps: List[Dependency]) -> str:
    """Generate prompt for Claude to create prep document."""

    prompt = f"""
    You are preparing for a complex task that has multiple dependencies.

    # Task Details
    ID: {task.id}
    Name: {task.name}
    Description: {task.description}

    # All Dependency Documentation

    """

    for dep in deps:
        prompt += f"""
        ## Dependency: {dep.sprint_id}

        ### Plan
        {dep.docs['plan']}

        ### Architecture
        {dep.docs['architecture']}

        ### Progress & Learnings
        {dep.docs['progress']}

        ### Lessons Learned
        {dep.docs.get('lessons', 'N/A')}

        ---

        """

    prompt += f"""
    # Your Task

    Analyze ALL the dependency documentation above and create a comprehensive
    task preparation document that:

    1. **Dependency Analysis** - For each dependency, explain:
       - What it provides (outputs, interfaces, functions)
       - How to integrate it with this task
       - Code examples showing integration patterns
       - Critical gotchas and common mistakes

    2. **Critical Integration Points** - Identify:
       - How dependencies interact with each other
       - Potential conflicts or issues
       - Correct integration flow/sequence

    3. **Key Learnings** - Extract relevant learnings from dependency progress:
       - Mistakes to avoid
       - Best practices discovered
       - Performance considerations

    4. **Potential Issues** - Anticipate problems:
       - Race conditions
       - Error handling gaps
       - Edge cases
       - Security concerns

    5. **Implementation Checklist** - Create actionable checklist:
       - Prerequisites
       - Step-by-step implementation order
       - Testing requirements
       - Questions to resolve

    Output a comprehensive markdown document following the structure shown
    in the example preparation document template.

    Focus on ACTIONABLE, SPECIFIC guidance tailored to this exact task.
    Include code examples with concrete function/variable names from dependencies.
    """

    return prompt
```

### Usage Example

```bash
# User knows upcoming task is complex
$ roadmap show backend-5-task-007

Task: Implement payment processing
Dependencies: 8 tasks across 4 sprints
Estimated: 6 hours

# Trigger preparation mode
$ roadmap prepare backend-5-task-007

Loading dependencies for backend-5-task-007...
Analyzing 8 dependencies...
Context size: ~45,000 tokens

Generating preparation document (this may take 30-60 seconds)...

✅ Preparation document created: .vibey/sprint_docs/backend-5/prep/task-007.md
   Read before starting: cat .vibey/sprint_docs/backend-5/prep/task-007.md

# Read the prep document
$ cat .vibey/sprint_docs/backend-5/prep/task-007.md
# [Comprehensive analysis shown above]

# Start the task (prep doc is now available as reference)
$ roadmap start backend-5-task-007

# During implementation, reference prep doc as needed
# It contains all the integration patterns, gotchas, etc.
```

### Benefits

**1. Deep Understanding**
- Model can use full context window for analysis
- No context limits during preparation
- Thorough examination of all dependencies

**2. Focused Artifact**
- Task-specific (not generic dependency summaries)
- Actionable guidance
- Integration patterns with code examples

**3. Persistent Knowledge**
- Saved to `.vibey/sprint_docs/` (committed to git)
- Reusable across sessions
- Can be manually edited/refined

**4. Reduced Cognitive Load**
- One comprehensive document vs. 20+ dependency docs
- Clear implementation path
- Checklist format

**5. Proactive Issue Detection**
- Identifies potential problems BEFORE coding
- Suggests solutions upfront
- Reduces debugging time

### Trade-offs

**Costs:**
- Takes 30-60 seconds to generate
- Uses significant API tokens (45K+ context)
- Requires user to trigger explicitly

**Benefits:**
- Saves hours during implementation
- Prevents integration bugs
- Higher quality implementation
- Faster task completion

**When to use:**
- Complex tasks (5+ dependencies)
- Critical integrations
- Unfamiliar domains
- High-risk tasks (payments, security, etc.)

**When to skip:**
- Simple tasks (1-2 dependencies)
- Well-understood patterns
- Small changes
- Time-sensitive fixes

### Preparation Document Quality

**Auto-generation tips:**
```yaml
# In task definition, add hints for preparation
- id: "backend-5-task-007"
  preparation_hints:
    focus_areas:
      - "Integration patterns"
      - "Error handling"
      - "Race conditions"
    key_dependencies:
      - "backend-4-task-012"  # Most critical
      - "backend-3-task-008"
```

**Manual refinement:**
```bash
# Generate initial prep doc
roadmap prepare backend-5-task-007

# Manually refine if needed
vim .vibey/sprint_docs/backend-5/prep/task-007.md

# Add custom notes, diagrams, code examples
# The prep doc is yours to customize!
```

---

## Auto-Generation

### Sprint Dependency Summary

**Triggered by:** `roadmap complete <sprint-id>`

**Process:**
1. Read all sprint docs from `.vibey/sprint_docs/<sprint-id>/`
2. Extract key sections (goals, features, learnings)
3. Generate structured summary (500 words max)
4. Save to `sprint.dependency_summary` field in YAML

**Template:**
```markdown
This sprint implemented [high-level description].

Key Outputs:
- [Endpoint/function/model 1]
- [Endpoint/function/model 2]
- [Endpoint/function/model 3]

Key Interfaces:
- [Interface 1]: [description]
- [Interface 2]: [description]

Critical Learnings:
- [Learning 1]
- [Learning 2]

For dependencies: [How to use outputs]
See full context: .vibey/sprint_docs/<sprint-id>/
```

**Implementation:**
```python
def generate_dependency_summary(sprint_id: str) -> str:
    """Generate dependency summary for completed sprint."""

    # Load sprint docs
    docs = load_sprint_docs(sprint_id)
    plan = docs['plan']
    architecture = docs['architecture']
    progress = docs['progress']
    lessons = docs.get('lessons', '')

    # Extract key information
    outputs = extract_outputs(plan, progress)
    interfaces = extract_interfaces(architecture)
    learnings = extract_learnings(progress, lessons)
    goals = extract_goals(plan)

    # Build summary
    summary = f"This sprint {summarize_goals(goals)}.\n\n"

    summary += "Key Outputs:\n"
    for output in outputs[:5]:  # Top 5 outputs
        summary += f"- {output}\n"
    summary += "\n"

    summary += "Key Interfaces:\n"
    for interface in interfaces[:3]:
        summary += f"- {interface['name']}: {interface['description']}\n"
    summary += "\n"

    summary += "Critical Learnings:\n"
    for learning in learnings[:3]:
        summary += f"- {learning}\n"
    summary += "\n"

    summary += f"For dependencies: {generate_usage_guidance(outputs)}\n"
    summary += f"See full context: .vibey/sprint_docs/{sprint_id}/\n"

    return summary
```

### Task-Level Summaries

**Triggered by:** `roadmap complete <task-id>`

**Process:**
1. Extract task details from sprint docs
2. Identify outputs (functions, endpoints, models)
3. Capture gotchas from progress.md
4. Generate structured task summary
5. Save to `sprint.task_summaries[task_id]`

**Structure:**
```yaml
task_summaries:
  backend-4-task-012:
    summary: "Brief description"
    outputs:
      - "Output 1"
      - "Output 2"
    interfaces:
      - function: "functionName"
        signature: "functionName(args) -> ReturnType"
        raises: "ExceptionType"
    gotchas:
      - "Important caveat 1"
      - "Important caveat 2"
    full_context: "sprint_docs/backend-4/progress.md#day-8"
```

**Implementation:**
```python
def generate_task_summary(task: Task) -> dict:
    """Generate task summary for completed task."""

    # Load sprint docs
    sprint_docs = load_sprint_docs(task.sprint_id)

    # Find task mentions in progress.md
    task_sections = extract_task_sections(
        sprint_docs['progress'],
        task.id
    )

    # Extract outputs
    outputs = extract_outputs_for_task(task_sections)

    # Extract interfaces
    interfaces = extract_interfaces_for_task(
        sprint_docs['architecture'],
        task.name
    )

    # Extract gotchas
    gotchas = extract_gotchas(task_sections)

    # Generate summary
    summary = {
        'summary': generate_brief_summary(task, task_sections),
        'outputs': outputs,
        'interfaces': interfaces,
        'gotchas': gotchas,
        'full_context': find_full_context_link(task_sections)
    }

    return summary
```

---

## Implementation Guide

### Phase 1: Schema Extension (Week 1)

**1. Update Sprint YAML Schema**

Add to `.vibey/roadmap/sprints/<sprint-id>.yaml`:
```yaml
sprint:
  # ... existing fields ...

  # NEW: Context loading fields
  dependency_summary: null  # Auto-generated on completion
  task_summaries: {}        # Auto-generated per task

  # NEW: Summary generation config
  summary_config:
    auto_generate: true
    include_sections:
      - "goals"
      - "key_features"
      - "learnings"
      - "interfaces"
    max_length: 500  # words
```

**2. Update Task YAML Schema**

Add to `.vibey/roadmap/tasks/<sprint-id>-tasks.yaml`:
```yaml
- id: "backend-5-task-007"
  # ... existing fields ...

  dependencies:
    - type: "task"
      target_id: "backend-4-task-012"
      at_status: "completed"

      # NEW: Context mode control
      context_mode: "summary"  # minimal, summary, full

      reason: "Need authentication to protect payment endpoints"
```

### Phase 2: Auto-Generation (Week 2)

**1. Implement Summary Generators**

```python
# framework/scripts/roadmap_utils.py

def auto_generate_summaries(sprint_id: str):
    """Auto-generate all summaries for sprint."""

    sprint = load_sprint(sprint_id)

    # Generate sprint-level summary
    sprint.dependency_summary = generate_dependency_summary(sprint_id)

    # Generate task-level summaries
    for task in sprint.tasks:
        if task.status == "completed":
            sprint.task_summaries[task.id] = generate_task_summary(task)

    save_sprint(sprint)
```

**2. Integrate with CLI Commands**

```python
# framework/scripts/roadmap_commands/complete.py

def complete_sprint(sprint_id: str):
    """Complete sprint and generate summaries."""

    # Update status
    sprint = load_sprint(sprint_id)
    sprint.status = "completed"
    sprint.completed = datetime.now()

    # Generate summaries
    if sprint.summary_config.auto_generate:
        auto_generate_summaries(sprint_id)

    save_sprint(sprint)
```

### Phase 3: Context Loading (Week 3)

**1. Implement Context Loader**

```python
# framework/scripts/context_loader.py

class ContextLoader:
    """Loads dependency context based on mode and distance."""

    def __init__(self, max_distance: int = 2, cache: bool = True):
        self.max_distance = max_distance
        self.cache = cache
        self.summary_cache = {} if cache else None

    def load_context_for_task(self, task: Task) -> ContextBundle:
        """Load all context needed for a task."""

        bundle = ContextBundle()

        # Load current sprint docs (always full)
        bundle.add_current_sprint(load_sprint_docs(task.sprint_id))

        # Build dependency graph
        graph = DependencyGraph(task)
        plan = graph.get_loading_plan()

        # Load dependencies by mode
        for entry in plan:
            context = self.load_dependency_context(entry)
            bundle.add_dependency(entry.dependency_id, context)

        return bundle

    def load_dependency_context(self, entry: PlanEntry) -> dict:
        """Load context for a single dependency."""

        if entry.mode == "minimal":
            return self.load_minimal(entry.dependency_id)

        elif entry.mode == "summary":
            return self.load_summary(entry.dependency_id)

        elif entry.mode == "full":
            return self.load_full(entry.dependency_id)

        else:
            return {}

    def load_minimal(self, task_id: str) -> dict:
        """Load minimal context (outputs only)."""

        sprint = load_sprint_from_task(task_id)
        task_summary = sprint.task_summaries.get(task_id, {})

        return {
            'sprint_id': sprint.id,
            'sprint_name': sprint.name,
            'sprint_status': sprint.status,
            'outputs': task_summary.get('outputs', [])
        }

    def load_summary(self, task_id: str) -> dict:
        """Load summary context."""

        # Use cache if enabled
        if self.cache and task_id in self.summary_cache:
            return self.summary_cache[task_id]

        sprint = load_sprint_from_task(task_id)

        context = {
            'sprint_summary': sprint.dependency_summary,
            'task_summary': sprint.task_summaries.get(task_id, {})
        }

        if self.cache:
            self.summary_cache[task_id] = context

        return context

    def load_full(self, task_id: str) -> dict:
        """Load full context."""

        sprint = load_sprint_from_task(task_id)
        docs = load_sprint_docs(sprint.id)

        return {
            'sprint_summary': sprint.dependency_summary,
            'task_summary': sprint.task_summaries.get(task_id, {}),
            'sprint_docs': docs
        }
```

**2. Add CLI Commands**

```bash
# Generate summaries
roadmap summarize <sprint-id>
roadmap summarize <sprint-id> --task <task-id>

# View context
roadmap context <task-id>
roadmap context <task-id> --mode summary
roadmap context <task-id> --show-full

# Preparation mode (see roadmap_prepare.py implementation in Preparation Mode section)
roadmap prepare <task-id>
roadmap prepare <task-id> --regenerate
roadmap prepare <task-id> --show
```

### Phase 4: Testing & Optimization (Week 4)

**1. Performance Testing**
```python
def test_context_loading_performance():
    """Test context loading speed."""

    # Create test sprint with 10 dependencies
    task = create_test_task_with_dependencies(10)

    loader = ContextLoader()

    start = time.time()
    bundle = loader.load_context_for_task(task)
    duration = time.time() - start

    assert duration < 0.5  # Under 500ms
    assert bundle.total_tokens < 10000  # Under 10K tokens
```

**2. Quality Testing**
```python
def test_summary_quality():
    """Test auto-generated summary quality."""

    sprint = create_completed_test_sprint()
    summary = generate_dependency_summary(sprint.id)

    # Check structure
    assert "Key Outputs:" in summary
    assert "Key Interfaces:" in summary
    assert "Critical Learnings:" in summary

    # Check length
    word_count = len(summary.split())
    assert 200 <= word_count <= 600
```

---

## Performance Optimization

### Caching Strategy

**1. Summary Cache**
```python
# In-memory cache for loaded summaries
summary_cache = {}

def get_summary(sprint_id: str) -> str:
    if sprint_id not in summary_cache:
        summary_cache[sprint_id] = load_summary(sprint_id)
    return summary_cache[sprint_id]
```

**2. Graph Cache**
```python
# Cache dependency graphs
graph_cache = {}

def get_dependency_graph(task_id: str) -> DependencyGraph:
    if task_id not in graph_cache:
        graph_cache[task_id] = build_dependency_graph(task_id)
    return graph_cache[task_id]
```

### Lazy Loading

**Load on demand, not upfront:**
```python
class LazyContextBundle:
    """Lazy-load context as needed."""

    def __init__(self, task: Task):
        self.task = task
        self.loaded_deps = {}

    def get_dependency_context(self, dep_id: str) -> dict:
        """Load dependency context only when accessed."""

        if dep_id not in self.loaded_deps:
            self.loaded_deps[dep_id] = load_context(dep_id)

        return self.loaded_deps[dep_id]
```

### Parallel Loading

**Load multiple dependencies concurrently:**
```python
import concurrent.futures

def load_all_dependencies(task: Task) -> dict:
    """Load dependencies in parallel."""

    contexts = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}

        for dep in task.dependencies:
            future = executor.submit(load_context, dep.target_id)
            futures[future] = dep.target_id

        for future in concurrent.futures.as_completed(futures):
            dep_id = futures[future]
            contexts[dep_id] = future.result()

    return contexts
```

---

## Testing Strategy

### Unit Tests

```python
def test_dependency_distance_calculation():
    """Test distance calculation for dependencies."""

    # Linear chain: A → B → C
    task_c = create_task('C', depends_on=['B'])
    task_b = create_task('B', depends_on=['A'])
    task_a = create_task('A')

    assert calculate_distance(task_c, 'B') == 1
    assert calculate_distance(task_c, 'A') == 2

def test_diamond_dependency_deduplication():
    """Test handling of diamond dependencies."""

    # Diamond: D depends on B and C, both depend on A
    task_d = create_task('D', depends_on=['B', 'C'])
    task_b = create_task('B', depends_on=['A'])
    task_c = create_task('C', depends_on=['A'])

    graph = DependencyGraph(task_d)
    plan = graph.get_loading_plan()

    # A should appear once at distance 2 (not twice)
    a_entries = [e for e in plan if e.dependency_id == 'A']
    assert len(a_entries) == 1
    assert a_entries[0].distance == 2

def test_context_mode_selection():
    """Test automatic context mode selection."""

    task = create_task('main', depends_on=['dep1'])
    dep = task.dependencies[0]

    # Distance 1 → summary
    assert select_context_mode(task, dep) == "summary"

    # User override
    dep.context_mode = "full"
    assert select_context_mode(task, dep) == "full"
```

### Integration Tests

```python
def test_end_to_end_context_loading():
    """Test complete context loading workflow."""

    # Create complex dependency structure
    sprint_1 = create_sprint_with_tasks('sprint-1', 5)
    sprint_2 = create_sprint_with_tasks('sprint-2', 5, depends_on=['sprint-1'])
    sprint_3 = create_sprint_with_tasks('sprint-3', 5, depends_on=['sprint-2'])

    # Complete sprints (triggers summary generation)
    complete_sprint('sprint-1')
    complete_sprint('sprint-2')

    # Load context for sprint-3 task
    task = get_task('sprint-3-task-003')
    loader = ContextLoader()
    bundle = loader.load_context_for_task(task)

    # Verify correct loading
    assert bundle.has_current_sprint_docs()
    assert len(bundle.dependencies) > 0
    assert bundle.total_tokens < 10000  # Reasonable size
```

### Performance Tests

```python
def test_context_loading_performance():
    """Test that context loading is fast."""

    # Create task with 20 dependencies
    task = create_task_with_many_dependencies(20)

    loader = ContextLoader(cache=True)

    # First load (cold cache)
    start = time.time()
    bundle1 = loader.load_context_for_task(task)
    cold_duration = time.time() - start

    # Second load (warm cache)
    start = time.time()
    bundle2 = loader.load_context_for_task(task)
    warm_duration = time.time() - start

    assert cold_duration < 1.0  # Under 1 second
    assert warm_duration < 0.1  # Under 100ms
```

---

## Migration Path

### For Existing Sprints

```bash
# Generate summaries for all completed sprints
roadmap summarize --all --completed

# Or per sprint
for sprint in backend-1 backend-2 backend-3; do
  roadmap summarize $sprint
done
```

### Backwards Compatibility

**If summary doesn't exist:**
```python
def get_context(task_id: str, mode: str) -> dict:
    """Get context with fallback for legacy sprints."""

    sprint = load_sprint_from_task(task_id)

    if mode == "summary":
        # Try to load summary
        if sprint.dependency_summary:
            return load_summary(task_id)
        else:
            # Fallback: generate on-the-fly
            return generate_summary_on_fly(sprint.id)

    elif mode == "full":
        # Always works (reads markdown files)
        return load_full_docs(sprint.id)
```

---

## Success Criteria

### Performance Targets
- ✅ Context loading < 500ms per task
- ✅ Summary generation < 2 seconds per sprint
- ✅ Preparation mode < 60 seconds per task
- ✅ 80-90% reduction in context tokens for tasks with 5+ dependencies

### Quality Targets
- ✅ 90% of users don't edit auto-generated summaries
- ✅ 85% of preparation docs rated "helpful" by users
- ✅ Summaries capture key outputs and learnings
- ✅ No critical information lost in summarization
- ✅ Preparation docs identify 90% of integration issues

### Usability Targets
- ✅ Users understand context modes
- ✅ 30% of complex tasks (5+ deps) use preparation mode
- ✅ Clear documentation and examples
- ✅ Sensible defaults (summary mode)
- ✅ Easy override mechanism

---

## Future Enhancements

### AI-Powered Summarization
Use Claude API to generate higher-quality summaries:
```python
def generate_ai_summary(sprint_docs: dict) -> str:
    """Use Claude to generate summary."""

    prompt = f"""
    Generate a concise dependency summary for this sprint.

    Sprint docs:
    {sprint_docs}

    Format:
    - Key Outputs: [list]
    - Key Interfaces: [list]
    - Critical Learnings: [list]
    """

    return claude_api.complete(prompt)
```

### Dynamic Context Adjustment
Adjust context mode based on task complexity:
```python
def smart_context_mode(task: Task, dep: Dependency) -> str:
    """Dynamically adjust context mode."""

    # High complexity task → more context
    if task.complexity == "high":
        return "full"

    # Architectural dependency → more context
    if dep.type == "architectural":
        return "full"

    # Otherwise use distance-based
    return get_default_mode(calculate_distance(task, dep.target_id))
```

### Context Compression
Compress summaries further for deep dependencies:
```python
def compress_summary(summary: str, compression_level: int) -> str:
    """Compress summary based on level."""

    if compression_level == 0:
        return summary  # Full summary

    elif compression_level == 1:
        # Keep outputs and interfaces only
        return extract_outputs_and_interfaces(summary)

    elif compression_level == 2:
        # Keep outputs only
        return extract_outputs(summary)
```

---

## Conclusion

The context loading strategy provides a scalable solution to the dependency context explosion problem through:

1. **Hybrid approach** - Multiple strategies work together
2. **Auto-generation** - No manual summary writing required
3. **Hierarchical loading** - More detail for closer dependencies
4. **Configurability** - Users can override defaults when needed
5. **Preparation mode** - Deep analysis for complex tasks
6. **Performance** - Caching and lazy loading keep it fast

**Expected Impact:**
- 80-90% reduction in context tokens for normal tasks
- Sub-second context loading
- Scalable to projects with 100+ sprints
- No loss of critical information
- Proactive issue detection via preparation mode
- Higher quality implementations with fewer integration bugs

---

**Next Steps:**
1. Implement Phase 1 (schema extension)
2. Build auto-generation (Phase 2)
3. Implement context loader (Phase 3)
4. Test and optimize (Phase 4)
5. Document usage patterns
6. Migrate existing Vibey sprints

**Questions? Feedback?**
This is a critical feature for roadmap system scalability. Review carefully before implementation.
