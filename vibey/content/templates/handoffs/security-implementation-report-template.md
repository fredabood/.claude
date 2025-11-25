---
id: security-implementation-report
name: Security Implementation Report
version: 1.0.0
from_agent: security-reviewer
to_agents:
- web-developer
- documentation-engineer
purpose: Template for security implementation report
variables:
- name: achievement
  type: string
  required: true
  description: Achievement value
- name: approval_status
  type: string
  required: true
  description: Approval Status value
- name: auth_checklist_status
  type: string
  required: true
  description: Auth Checklist Status value
- name: auth_context_path
  type: string
  required: true
  description: Auth Context Path value
- name: auth_test_coverage
  type: string
  required: true
  description: Auth Test Coverage value
- name: authentication_test_evidence
  type: string
  required: true
  description: Authentication Test Evidence value
- name: authorization_test_evidence
  type: string
  required: true
  description: Authorization Test Evidence value
- name: authz_test_coverage
  type: string
  required: true
  description: Authz Test Coverage value
- name: cookie_settings
  type: string
  required: true
  description: Cookie Settings value
- name: cors_allow_credentials
  type: string
  required: true
  description: Cors Allow Credentials value
- name: cors_allowed_headers
  type: string
  required: true
  description: Cors Allowed Headers value
- name: cors_allowed_methods
  type: string
  required: true
  description: Cors Allowed Methods value
- name: cors_configuration_code
  type: string
  required: true
  description: Cors Configuration Code value
- name: critical_issues_fixed
  type: string
  required: true
  description: Critical Issues Fixed value
- name: critical_issues_found
  type: string
  required: true
  description: Critical Issues Found value
description: Template for security implementation report
---

# Security Implementation Report: {{ feature_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.security_engineer or 'Security Engineer' }}
**To:** {{ config.roles.documentation_engineer or 'Documentation Engineer / Next Agent in Workflow' }}
**Date:** {{ report_date }}
**Purpose:** Document security features implemented and issues fixed
**Related Workflow:** Frontend/Backend Security Hardening Workflow

---

## Handoff Metadata

| Field | Value |
|-------|-------|
| **Feature/Component** | {{ feature_name }} |
| **Security Score** | {{ security_score }}/100 |
| **Status** | {{ approval_status }} |
| **Issues Found** | {{ total_issues }} |
| **Issues Fixed** | {{ fixed_issues }} |
| **Implementation Duration** | {{ implementation_duration }} |
| **Project Type** | {{ config.project.type }} |

---

## Executive Summary

**Feature/Component:** {{ feature_name }}
**Security Score:** {{ security_score }}/100
**Status:** {{ approval_status }}

**Issues Found:**
- Critical: {{ critical_issues_found }}
- High: {{ high_issues_found }}
- Medium: {{ medium_issues_found }}
- Low: {{ low_issues_found }}

**Issues Fixed:**
- Critical: {{ critical_issues_fixed }}/{{ critical_issues_found }}
- High: {{ high_issues_fixed }}/{{ high_issues_found }}
- Medium: {{ medium_issues_fixed }}/{{ medium_issues_found }}

**Key Achievements:**
{% for achievement in security_achievements %}
- {{ achievement }}
{% endfor %}

---

## 1. Security Features Implemented

{% if config.project.type in ['web-app', 'api'] %}
### Authentication & Authorization

{% if config.web_framework.backend in ['spring-boot', 'express', 'fastapi', 'django'] %}
**{% if config.web_framework.backend == 'spring-boot' %}Spring Security{% elif config.web_framework.backend == 'express' %}Passport.js{% elif config.web_framework.backend == 'fastapi' %}FastAPI Security{% elif config.web_framework.backend == 'django' %}Django Auth{% endif %}:**
{% for auth_feature in authentication_features %}
- [{{ 'x' if auth_feature.completed else ' ' }}] {{ auth_feature.description }}
{% endfor %}

**Implementation:**
{% if auth_method == 'jwt' %}
- JWT token provider implemented
- Token signing algorithm: {{ jwt_algorithm }}
- Token expiration: {{ jwt_expiration }}
- Refresh token strategy: {{ refresh_token_strategy }}
{% elif auth_method == 'oauth2' %}
- OAuth2 provider integration: {{ oauth2_providers }}
- Authorization code flow implemented
- PKCE enabled: {{ pkce_enabled }}
{% elif auth_method == 'session' %}
- Session management configured
- Session timeout: {{ session_timeout }}
- Secure cookie settings: {{ cookie_settings }}
{% endif %}
{% endif %}

{% if config.web_framework.frontend in ['react', 'vue', 'angular', 'svelte'] %}
**Frontend Authentication:**
{% for frontend_auth_feature in frontend_auth_features %}
- [{{ 'x' if frontend_auth_feature.completed else ' ' }}] {{ frontend_auth_feature.description }}
{% endfor %}

**Implementation:**
- Auth context/store: `{{ auth_context_path }}`
- Login component: `{{ login_component_path }}`
- Protected routes: {{ protected_routes_count }} routes
- Token storage: {{ token_storage_method }}
{% endif %}

**Files Created/Modified:**
{% for file in authentication_files %}
- `{{ file }}`
{% endfor %}

---

### Input Validation

{% if config.technology_stack.backend.language == 'java' %}
**Backend (Bean Validation):**
- [x] `spring-boot-starter-validation` dependency added
- [x] All DTOs have validation annotations (`@NotBlank`, `@Size`, `@Email`, etc.)
- [x] `@Validated` added to controllers
- [x] `@Valid` added to `@RequestBody` parameters
- [x] Global exception handler handles validation errors

**Example Validation:**
```java
public class {{ example_dto_name }} {
    @NotBlank(message = "{{ field_name }} is required")
    @Size(max = {{ max_length }}, message = "{{ field_name }} must not exceed {{ max_length }} characters")
    private String {{ field_name }};
}
```

{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
**Backend (Joi/Yup/Zod):**
- [x] Validation library installed ({{ validation_library }})
- [x] Validation schemas created for all endpoints
- [x] Middleware validates requests before processing
- [x] Validation errors return 400 with field details

**Example Validation:**
```typescript
import {{ validation_library }} from '{{ validation_library }}';

const {{ schema_name }}Schema = {{ validation_library }}.object({
  {{ field_name }}: {{ validation_library }}.string()
    .required()
    .max({{ max_length }})
});
```

{% elif config.technology_stack.backend.language == 'python' %}
**Backend (Pydantic):**
- [x] Pydantic models created for all endpoints
- [x] Type validation enforced
- [x] Custom validators for complex rules
- [x] Validation errors return 422 with field details

**Example Validation:**
```python
from pydantic import BaseModel, Field, validator

class {{ model_name }}(BaseModel):
    {{ field_name }}: str = Field(..., max_length={{ max_length }})

    @validator('{{ field_name }}')
    def validate_{{ field_name }}(cls, v):
        # Custom validation logic
        return v
```
{% endif %}

{% if config.web_framework.frontend in ['react', 'vue', 'angular'] %}
**Frontend ({{ frontend_validation_library }}):**
- [x] `{{ frontend_validation_library }}` installed
- [x] Validation schemas created for all forms
- [x] Forms use validation resolver
- [x] Validation errors display correctly
- [x] Client-side validation matches backend rules

**Files Created/Modified:**
{% for file in validation_files %}
- `{{ file }}`
{% endfor %}
{% endif %}

---

### XSS Prevention

**Implementation:**
{% for xss_feature in xss_prevention_features %}
- [{{ 'x' if xss_feature.completed else ' ' }}] {{ xss_feature.description }}
{% endfor %}

{% if config.web_framework.frontend in ['react', 'vue', 'angular'] %}
**Sanitization Library:** {{ sanitization_library }}
**Files Created:**
- `{{ sanitization_utility_path }}`

**Usage Example:**
```{{ config.technology_stack.frontend.language }}
import { sanitizeInput } from '{{ sanitization_utility_path }}';

{{ sanitization_example }}
```
{% endif %}

**Safe Practices Enforced:**
- No `dangerouslySetInnerHTML` (React)
- No `v-html` (Vue)
- All user content sanitized before display
- Content Security Policy configured

---

### Security Headers

{% if config.technology_stack.backend.language == 'java' %}
**Spring Boot Configuration:**
```java
http.headers(headers -> headers
    .contentSecurityPolicy(csp -> csp
        .policyDirectives("{{ csp_directives }}"))
    .frameOptions(frame -> frame.{{ frame_options }})
    .xssProtection(xss -> xss.headerValue({{ xss_protection }}))
    .contentTypeOptions(contentType -> contentType.disable(false))
);
```

{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
**Helmet.js Configuration:**
```typescript
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {{ csp_directives }}
  },
  frameguard: { action: '{{ frame_options }}' },
  xssFilter: true
}));
```

{% elif config.technology_stack.backend.language == 'python' %}
**Flask-Talisman / FastAPI Middleware:**
```python
from {{ middleware_library }} import {{ middleware_class }}

app.add_middleware(
    {{ middleware_class }},
    content_security_policy="{{ csp_directives }}",
    frame_options="{{ frame_options }}",
    force_https=True
)
```
{% endif %}

**Headers Configured:**
{% for header in security_headers %}
- [{{ 'x' if header.configured else ' ' }}] {{ header.name }}: {{ header.value }}
{% endfor %}

---

### Rate Limiting

**Implementation:**
{% for rate_limit_feature in rate_limiting_features %}
- [{{ 'x' if rate_limit_feature.completed else ' ' }}] {{ rate_limit_feature.description }}
{% endfor %}

**Rate Limit Configuration:**
- **Strategy:** {{ rate_limit_strategy }}
- **Limits:** {{ rate_limit_value }}
- **Scope:** {{ rate_limit_scope }}
- **Response:** {{ rate_limit_response_code }} ({{ rate_limit_response_message }})

{% if config.technology_stack.backend.language == 'java' %}
**Files Created:**
- `{{ rate_limit_service_path }}`

{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
**Library:** {{ rate_limit_library }}

```typescript
import {{ rate_limit_library }} from '{{ rate_limit_library }}';

const limiter = {{ rate_limit_library }}({
  windowMs: {{ window_ms }},
  max: {{ max_requests }},
  message: '{{ rate_limit_message }}'
});

app.use('/api/', limiter);
```

{% elif config.technology_stack.backend.language == 'python' %}
**Library:** {{ rate_limit_library }}

```python
from {{ rate_limit_library }} import {{ rate_limit_class }}

limiter = {{ rate_limit_class }}(
    app,
    default_limits=["{{ rate_limit_value }}"]
)
```
{% endif %}

---

### Secrets Management

**Verification:**
{% for secret_check in secrets_management_checks %}
- [{{ 'x' if secret_check.passed else ' ' }}] {{ secret_check.description }}
{% endfor %}

**Environment Variables:**
```bash
{% for env_var in environment_variables %}
{{ env_var.name }}={{ env_var.example_value }}
{% endfor %}
```

**Secrets Storage:**
- Development: {{ dev_secrets_storage }}
- Production: {{ prod_secrets_storage }}

---

{% if config.project.type == 'web-app' %}
### CSRF Protection

**Implementation:**
{% for csrf_feature in csrf_protection_features %}
- [{{ 'x' if csrf_feature.completed else ' ' }}] {{ csrf_feature.description }}
{% endfor %}

**CSRF Token Strategy:** {{ csrf_strategy }}

---

### CORS Configuration

**Allowed Origins:**
{% for origin in cors_allowed_origins %}
- `{{ origin }}`
{% endfor %}

**Allowed Methods:** {{ cors_allowed_methods }}
**Allowed Headers:** {{ cors_allowed_headers }}
**Credentials:** {{ cors_allow_credentials }}

**Configuration:**
```{{ config.technology_stack.backend.language }}
{{ cors_configuration_code }}
```

---
{% endif %}
{% endif %}

## 2. Security Checklist Results

{% if security_checklist_path %}
Using `{{ security_checklist_path }}`:
{% endif %}

### Authentication & Authorization
{% for check in auth_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ auth_checklist_status }}

### Input Validation
{% for check in input_validation_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ input_validation_status }}

### Output Encoding
{% for check in output_encoding_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ output_encoding_status }}

### Session Management
{% for check in session_management_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ session_management_status }}

### Cryptography
{% for check in cryptography_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ cryptography_status }}

### Error Handling
{% for check in error_handling_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ error_handling_status }}

### Logging & Monitoring
{% for check in logging_monitoring_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ logging_monitoring_status }}

### Security Headers
{% for check in security_headers_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ security_headers_status }}

### Dependency Security
{% for check in dependency_security_checklist %}
- [{{ 'x' if check.passed else ' ' }}] {{ check.description }}
{% endfor %}
**Status:** {{ dependency_security_status }}

**TOTAL SCORE:** {{ total_security_score }}/100

---

## 3. Issues Found and Fixed

{% for issue in critical_issues %}
### CRITICAL Issue #{{ loop.index }}: {{ issue.title }}

**Severity:** CRITICAL
**Description:** {{ issue.description }}
**Impact:** {{ issue.impact }}
**CVE (if applicable):** {{ issue.cve or 'N/A' }}

**Fix Applied:**
```{{ issue.code_language }}
{{ issue.fix_code }}
```

**Verification:**
```{{ issue.verification_language }}
{{ issue.verification_code }}
```

**Status:** {{ issue.status }}

---

{% endfor %}

{% for issue in high_issues %}
### HIGH Issue #{{ loop.index }}: {{ issue.title }}

**Severity:** HIGH
**Description:** {{ issue.description }}
**Impact:** {{ issue.impact }}

**Fix Applied:**
```{{ issue.code_language }}
{{ issue.fix_code }}
```

**Status:** {{ issue.status }}

---

{% endfor %}

{% for issue in medium_issues %}
### MEDIUM Issue #{{ loop.index }}: {{ issue.title }}

**Severity:** MEDIUM
**Description:** {{ issue.description }}
**Impact:** {{ issue.impact }}

**Fix Applied:** {{ issue.fix_description }}

**Status:** {{ issue.status }}

---

{% endfor %}

---

## 4. OWASP Top 10 Assessment

{% for owasp_item in owasp_assessment %}
**{{ loop.index }}. {{ owasp_item.name }}:** {{ owasp_item.status }}
{% for detail in owasp_item.details %}
   - {{ detail }}
{% endfor %}

{% endfor %}

---

## 5. Testing Evidence

### Authentication Tests
```bash
{{ authentication_test_evidence }}
```

### Authorization Tests
```bash
{{ authorization_test_evidence }}
```

### Input Validation Tests
```bash
{{ input_validation_test_evidence }}
```

### XSS Prevention Tests
```bash
{{ xss_prevention_test_evidence }}
```

### Rate Limiting Tests
```bash
{{ rate_limiting_test_evidence }}
```

---

## 6. Penetration Testing Results

{% if penetration_testing_performed %}
**Testing Date:** {{ pentest_date }}
**Testing Tool:** {{ pentest_tool }}
**Tester:** {{ pentest_tester }}

**Results:**
{% for pentest_result in pentest_results %}
- **{{ pentest_result.test_name }}**: {{ pentest_result.result }}
{% endfor %}

**Vulnerabilities Found:** {{ pentest_vulnerabilities_found }}
**Vulnerabilities Fixed:** {{ pentest_vulnerabilities_fixed }}
{% else %}
**Status:** Not yet performed
**Recommendation:** Schedule penetration testing before production deployment
{% endif %}

---

## 7. Security Scanning Results

{% if config.technology_stack.backend.language in ['javascript', 'typescript'] %}
**npm audit:**
```bash
{{ npm_audit_output }}
```
{% elif config.technology_stack.backend.language == 'python' %}
**pip-audit / safety check:**
```bash
{{ pip_audit_output }}
```
{% elif config.technology_stack.backend.language == 'java' %}
**OWASP Dependency-Check:**
```bash
{{ dependency_check_output }}
```
{% elif config.technology_stack.backend.language == 'go' %}
**gosec / nancy:**
```bash
{{ gosec_output }}
```
{% endif %}

**Known CVEs:** {{ known_cves_count }}
**Action Taken:** {{ cve_action_taken }}

---

## 8. Compliance Assessment

{% if compliance_requirements %}
**Compliance Standards:**
{% for standard in compliance_standards %}
- **{{ standard.name }}**: {{ standard.status }}
{% endfor %}

**Compliance Checklist:**
{% for compliance_item in compliance_checklist %}
- [{{ 'x' if compliance_item.compliant else ' ' }}] {{ compliance_item.requirement }}
{% endfor %}
{% endif %}

---

## 9. Recommendations

### For Production
{% for production_rec in production_recommendations %}
{{ loop.index }}. **{{ production_rec.title }}** (Priority: {{ production_rec.priority }})
   - {{ production_rec.description }}
   - Effort: {{ production_rec.effort }}
{% endfor %}

### For Future Sprints
{% for future_rec in future_recommendations %}
{{ loop.index }}. **{{ future_rec.title }}**
   - {{ future_rec.description }}
{% endfor %}

---

## 10. Security Documentation

**Documentation Created:**
{% for security_doc in security_documentation %}
- `{{ security_doc.path }}` - {{ security_doc.description }}
{% endfor %}

**Security Runbook:** `{{ security_runbook_path }}`

**Incident Response Plan:** `{{ incident_response_plan_path or 'Not yet created' }}`

---

## 11. Monitoring & Alerting

**Security Events Monitored:**
{% for security_event in monitored_security_events %}
- {{ security_event.name }}: {{ security_event.monitoring_method }}
{% endfor %}

**Alert Configuration:**
{% for alert in security_alerts %}
- **{{ alert.name }}**: {{ alert.threshold }} → {{ alert.notification_channel }}
{% endfor %}

---

## 12. Security Training & Awareness

**Team Training:**
{% for training in security_training %}
- {{ training.topic }}: {{ training.status }}
{% endfor %}

**Security Guidelines:** `{{ security_guidelines_path }}`

---

## 13. Ready for Next Step

{% for ready_criterion in ready_criteria %}
- [{{ 'x' if ready_criterion.met else ' ' }}] {{ ready_criterion.description }}
{% endfor %}

**Next Agent:** {{ next_agent or 'Documentation Engineer' }}

**Handoff Location:** {{ handoff_location }}

---

## Appendix A: Security Configuration Files

{% for config_file in security_config_files %}
**{{ config_file.name }}:** `{{ config_file.path }}`

```{{ config_file.language }}
{{ config_file.content_preview }}
```

---

{% endfor %}

---

## Appendix B: Security Test Suite

**Test Files:**
{% for test_file in security_test_files %}
- `{{ test_file.path }}` - {{ test_file.description }} ({{ test_file.test_count }} tests)
{% endfor %}

**Test Coverage:**
- Security-related code: {{ security_test_coverage }}%
- Authentication: {{ auth_test_coverage }}%
- Authorization: {{ authz_test_coverage }}%

---

## Appendix C: Security Tools Used

{% for tool in security_tools %}
**{{ tool.name }}**
- **Purpose:** {{ tool.purpose }}
- **Version:** {{ tool.version }}
- **Configuration:** `{{ tool.config_path or 'Default' }}`
{% endfor %}

---

**Handoff Complete:** {{ handoff_date }}
**Security Engineer:** {{ config.roles.security_engineer or 'Security Engineer' }}
**Next Agent:** {{ next_agent or 'Documentation Engineer' }}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
