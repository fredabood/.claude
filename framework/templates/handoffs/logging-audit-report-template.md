# Logging Audit Report: {{ component_name }}

**From:** {{ config.roles.observability_engineer or 'Observability Engineer' }}
**To:** Implementation Engineers, Team
**Date:** {{ audit_date }}
**Sprint/Version:** {{ sprint_version }}
**Status:** {{ audit_status }}

---

## 📊 Audit Summary

**Overall Score:** {{ overall_score }}/100
**Result:** {{ audit_result }}
**Critical Issues:** {{ critical_issues_count }}
**High Priority Issues:** {{ high_priority_issues_count }}
**Low Priority Issues:** {{ low_priority_issues_count }}

### Scores by Category

| Category | Score | Max | Status |
|----------|-------|-----|--------|
| Request Tracing | {{ request_tracing_score }}/25 | 25 | {{ request_tracing_status }} |
| Error Context | {{ error_context_score }}/30 | 30 | {{ error_context_status }} |
| Product Analytics | {{ product_analytics_score }}/20 | 20 | {{ product_analytics_status }} |
| Performance Metrics | {{ performance_metrics_score }}/15 | 15 | {{ performance_metrics_status }} |
| Log Accessibility | {{ log_accessibility_score }}/10 | 10 | {{ log_accessibility_status }} |

**Minimum Required:** {{ config.quality_gates.logging_score_minimum or 80 }}/100
**Gap to Close:** {{ score_gap }} points

---

## 🚨 Critical Issues (Must Fix Before {{ deployment_milestone }})

{% for issue in critical_issues %}
### Issue {{ loop.index }}: {{ issue.title }}

**Category:** {{ issue.category }}
**Score Impact:** -{{ issue.score_impact }} points
**Priority:** 🔴 Critical (Blocking)
**Estimated Effort:** {{ issue.estimated_effort }} hours
**Assigned To:** {{ issue.assigned_to }}
**Due:** {{ issue.due_date }}

**Problem:**
{{ issue.problem_description }}

**Current State:**
{% if config.technology_stack.backend.language == 'python' %}
```python
{{ issue.current_code_python }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
{{ issue.current_code_typescript }}
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
{{ issue.current_code_java }}
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
{{ issue.current_code_go }}
```
{% endif %}

**Required Fix:**
{% if config.technology_stack.backend.language == 'python' %}
```python
{{ issue.fixed_code_python }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
{{ issue.fixed_code_typescript }}
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
{{ issue.fixed_code_java }}
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
{{ issue.fixed_code_go }}
```
{% endif %}

**Verification Steps:**
```bash
{{ issue.verification_commands }}
```

**Files to Modify:**
{% for file in issue.files_to_modify %}
- `{{ file.path }}` ({{ file.modification }})
{% endfor %}

**Reference:**
- Logging Audit Checklist: {{ logging_audit_checklist_path }}
- Related Documentation: {{ issue.reference_docs }}

---

{% endfor %}

## ⚠️ High Priority Issues (Should Fix)

{% for issue in high_priority_issues %}
### Issue {{ loop.index }}: {{ issue.title }}

**Category:** {{ issue.category }}
**Score Impact:** -{{ issue.score_impact }} points
**Priority:** 🟠 High (Recommended)
**Estimated Effort:** {{ issue.estimated_effort }} hours
**Assigned To:** {{ issue.assigned_to }}
**Due:** {{ issue.due_date }}

**Problem:**
{{ issue.problem_description }}

**Recommended Fix:**
{{ issue.fix_description }}

---

{% endfor %}

## 📋 Low Priority Issues (Nice to Have)

{% for issue in low_priority_issues %}
### Issue {{ loop.index }}: {{ issue.title }}

**Category:** {{ issue.category }}
**Score Impact:** -{{ issue.score_impact }} points
**Priority:** 🟢 Low (Optional)
**Estimated Effort:** {{ issue.estimated_effort }} hours
**Assigned To:** {{ issue.assigned_to or 'Backlog' }}
**Due:** Future sprint

{{ issue.brief_description }}

---

{% endfor %}

## 🎯 Remediation Roadmap

### Phase 1: Critical Fixes (Must Do)
**Timeline:** {{ phase_1_timeline }} hours
**Blockers:** {{ deployment_milestone }} cannot complete without these

{% for issue in phase_1_issues %}
{{ loop.index }}. **{{ issue.title }}** ({{ issue.effort }}h) - {{ issue.assigned_to }}
{% endfor %}

**Subtotal:** {{ phase_1_total_hours }} hours

### Phase 2: High Priority Fixes (Should Do)
**Timeline:** {{ phase_2_timeline }} hours
**Impact:** Significantly improves observability

{% for issue in phase_2_issues %}
{{ loop.index }}. **{{ issue.title }}** ({{ issue.effort }}h) - {{ issue.assigned_to }}
{% endfor %}

**Subtotal:** {{ phase_2_total_hours }} hours

### Phase 3: Low Priority Fixes (Nice to Do)
**Timeline:** {{ phase_3_timeline }} hours
**Impact:** Minor improvements

{% for issue in phase_3_issues %}
{{ loop.index }}. **{{ issue.title }}** ({{ issue.effort }}h) - {{ issue.assigned_to }}
{% endfor %}

**Subtotal:** {{ phase_3_total_hours }} hours

---

**Total Estimated Effort:** {{ total_effort_hours }} hours
**Recommended Timeline:** {{ recommended_timeline_days }} days for critical + high priority
**Re-audit Schedule:** {{ re_audit_date }} after Phase 1 + 2 complete

---

## ✅ Verification Checklist

After implementing fixes, verify each issue is resolved:

{% for issue in critical_issues + high_priority_issues %}
### Issue {{ loop.index }}: {{ issue.title }}
- [ ] Code changes implemented
- [ ] Tests pass locally
- [ ] Verification steps executed successfully
- [ ] Logs show expected output
- [ ] Deployed to {{ staging_environment or 'staging' }} environment
- [ ] Re-tested in {{ staging_environment or 'staging' }}

{% endfor %}

---

## 🔄 Re-Audit Process

### When to Request Re-Audit
After completing:
- ✅ All critical issues fixed (Phase 1)
- ✅ All high priority issues fixed (Phase 2)
- ✅ All verification steps passed
- ✅ Changes deployed to {{ staging_environment or 'staging' }}

### What Will Be Re-Tested
- Only categories that failed (score < {{ passing_threshold or 80 }}% of max)
- Specific issues that were fixed
- End-to-end integration tests

### Expected Re-Audit Duration
- ~{{ re_audit_duration or '1-2' }} hours (only testing fixes, not full audit)

### Re-Audit Success Criteria
- ✅ All critical issues resolved
- ✅ Overall score ≥ {{ config.quality_gates.logging_score_minimum or 80 }}/100
- ✅ No new issues introduced

---

## 📚 Reference Materials

### Code Examples

**Correlation ID Propagation:**

{% if config.technology_stack.backend.language == 'python' %}
```python
# FastAPI/Flask Middleware
import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id_var.set(correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
// Express Middleware
import { v4 as uuidv4 } from 'uuid';

app.use((req, res, next) => {
  const correlationId = req.headers['x-correlation-id'] || uuidv4();
  req.correlationId = correlationId;
  res.setHeader('X-Correlation-ID', correlationId);
  next();
});
```

{% if config.web_framework and config.web_framework.frontend %}
```typescript
// {{ config.web_framework.frontend }} Client
export const getOrCreateCorrelationId = (): string => {
  let id = sessionStorage.getItem('correlationId');
  if (!id) {
    id = uuidv4();
    sessionStorage.getItem('correlationId', id);
  }
  return id;
};

// Add to all API requests
const headers = {
  'X-Correlation-ID': getOrCreateCorrelationId(),
  ...otherHeaders
};
```
{% endif %}

{% elif config.technology_stack.backend.language == 'java' %}
```java
// Spring Boot Filter
@Component
public class CorrelationIdFilter implements Filter {
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        String correlationId = httpRequest.getHeader("X-Correlation-ID");

        if (correlationId == null) {
            correlationId = UUID.randomUUID().toString();
        }

        MDC.put("correlationId", correlationId);

        try {
            chain.doFilter(request, response);
        } finally {
            MDC.clear();
        }
    }
}
```

{% elif config.technology_stack.backend.language == 'go' %}
```go
// Go Middleware
func CorrelationIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        correlationID := r.Header.Get("X-Correlation-ID")
        if correlationID == "" {
            correlationID = uuid.New().String()
        }

        ctx := context.WithValue(r.Context(), "correlationID", correlationID)
        w.Header().Set("X-Correlation-ID", correlationID)

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```
{% endif %}

**Error Context Logging:**

{% if config.technology_stack.backend.language == 'python' %}
```python
import logging

logger = logging.getLogger(__name__)

def log_error_with_context(error: Exception, operation: str, **context):
    """Log error with full context for debugging."""
    logger.error(
        f"Error in {operation}: {str(error)}",
        extra={
            "operation": operation,
            "error_type": type(error).__name__,
            "correlation_id": correlation_id_var.get(),
            **context
        },
        exc_info=True
    )

# Usage
try:
    result = process_data(user_id, data)
except Exception as e:
    log_error_with_context(
        error=e,
        operation="process_data",
        user_id=user_id,
        data_size=len(data)
    )
    raise
```

{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
import { logger } from './logger';

export function logErrorWithContext(
  error: Error,
  operation: string,
  context: Record<string, any>
): void {
  logger.error({
    message: `Error in ${operation}: ${error.message}`,
    operation,
    errorType: error.name,
    stack: error.stack,
    ...context
  });
}

// Usage
try {
  const result = await processData(userId, data);
} catch (error) {
  logErrorWithContext(error as Error, 'processData', {
    userId,
    dataSize: data.length
  });
  throw error;
}
```

{% elif config.technology_stack.backend.language == 'java' %}
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ErrorLogger {
    private static final Logger logger = LoggerFactory.getLogger(ErrorLogger.class);

    public static void logErrorWithContext(
        Exception error,
        String operation,
        Map<String, Object> context
    ) {
        logger.error("Error in {}: {}", operation, error.getMessage(), error);
        logger.error("Context: {}", context);
    }
}

// Usage
try {
    result = processData(userId, data);
} catch (Exception e) {
    ErrorLogger.logErrorWithContext(e, "processData", Map.of(
        "userId", userId,
        "dataSize", data.size()
    ));
    throw e;
}
```
{% endif %}

{% if config.project.type == 'web-app' %}
**Product Analytics / Event Tracking:**

{% if config.web_framework.frontend == 'react' %}
```typescript
// React Analytics Hook
import { useEffect } from 'react';
import { analytics } from './services/analytics';

export const usePageTracking = (pageName: string) => {
  useEffect(() => {
    analytics.trackPageView(pageName, {
      timestamp: new Date().toISOString(),
      correlationId: getOrCreateCorrelationId()
    });
  }, [pageName]);
};

// Track user actions
const handleSearch = (query: string, filters: any, results: any[]) => {
  analytics.trackEvent('search', {
    query,
    filters,
    resultCount: results.length,
    correlationId: getOrCreateCorrelationId()
  });
};
```
{% endif %}
{% endif %}

**Performance Metrics:**

{% if config.technology_stack.backend.language == 'python' %}
```python
import time
from functools import wraps

def track_performance(operation: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{operation} completed",
                    extra={
                        "operation": operation,
                        "duration_ms": duration * 1000,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation} failed",
                    extra={
                        "operation": operation,
                        "duration_ms": duration * 1000,
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise
        return wrapper
    return decorator
```
{% endif %}

### Documentation
- **Logging Audit Checklist:** `{{ logging_audit_checklist_path }}`
- **Observability Documentation:** `{{ observability_docs_path }}`
- **Logging Standards:** `{{ logging_standards_path }}`
- **Monitoring Dashboard:** `{{ monitoring_dashboard_url }}`

---

## 💬 Communication

### Team Updates
Post progress updates in {{ team_chat_channel }}:

```
🔍 Logging Audit Status Update

Component: {{ component_name }}
Score: {{ overall_score }}/100 ({{ audit_result }})

Critical Issues: {{ critical_issues_count }} (Priority 1)
High Priority: {{ high_priority_issues_count }} (Priority 2)

Currently Working On:
{% for issue in in_progress_issues %}
- [ ] Issue {{ loop.index }}: {{ issue.title }} - {{ issue.assigned_to }} - ETA: {{ issue.eta }}
{% endfor %}

Re-audit scheduled: {{ re_audit_date }}
```

### Daily Standup
During remediation period, include in standup:
- Which issues are being worked on
- Estimated completion time
- Any blockers or questions
- When ready for re-audit

### Questions?
- **Logging questions:** Ask {{ config.roles.observability_engineer or 'Observability Engineer' }}
- **Implementation questions:** Pair with senior engineer
- **Urgent blockers:** Escalate to tech lead

---

## 📝 Notes from Auditor

{{ auditor_notes }}

---

## ✅ Sign-off

### Implementation Team
- [ ] All critical issues addressed
- [ ] All high priority issues addressed (or deferred with justification)
- [ ] All verification steps passed
- [ ] Changes deployed to {{ staging_environment or 'staging' }}
- [ ] Ready for re-audit

**Completed By:** _______________ **Date:** _______________

### Re-Audit Approval
- [ ] Re-audit conducted
- [ ] Score ≥ {{ config.quality_gates.logging_score_minimum or 80 }}/100
- [ ] No new issues introduced
- [ ] {{ deployment_milestone }} approved for logging audit completion

**Auditor:** {{ config.roles.observability_engineer or 'Observability Engineer' }}
**Date:** _______________
**Final Score:** ___/100

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
