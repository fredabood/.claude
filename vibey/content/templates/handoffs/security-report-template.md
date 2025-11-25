---
id: security-report
name: Security Review
version: 1.0.0
from_agent: security-reviewer
to_agents:
- web-developer
- documentation-engineer
purpose: Template for security review
variables:
- name: api_mocking_status
  type: string
  required: true
  description: Api Mocking Status value
- name: approval_decision
  type: string
  required: true
  description: Approval Decision value
- name: approval_summary
  type: string
  required: true
  description: Approval Summary value
- name: areas_for_improvement
  type: string
  required: true
  description: Areas For Improvement value
- name: auth_findings
  type: string
  required: true
  description: Auth Findings value
- name: auth_recommendations
  type: string
  required: true
  description: Auth Recommendations value
- name: auth_status
  type: string
  required: true
  description: Auth Status value
- name: component_name
  type: string
  required: true
  description: Component Name value
- name: conditional_approval_summary
  type: string
  required: true
  description: Conditional Approval Summary value
- name: critical_count
  type: string
  required: true
  description: Critical Count value
- name: critical_issues_list
  type: string
  required: true
  description: Critical Issues List value
- name: critical_issues_section
  type: string
  required: true
  description: Critical Issues Section value
- name: cve_check_output
  type: string
  required: true
  description: Cve Check Output value
- name: database_security_findings
  type: string
  required: true
  description: Database Security Findings value
- name: database_security_recommendations
  type: string
  required: true
  description: Database Security Recommendations value
description: Template for security review
---

# Security Review: {{ component_name }}

**Reviewer:** {{ config.roles.security_reviewer or 'Security Reviewer' }}
**Date:** {{ review_date }}
**Files Reviewed:**
{{ files_reviewed_list }}

---

## Executive Summary

**Overall Risk Level:** {{ overall_risk_level }}

**Issues Found:**
- Critical: {{ critical_count }}
- High: {{ high_count }}
- Medium: {{ medium_count }}
- Low: {{ low_count }}
- Info: {{ info_count }}

**Total Issues:** {{ total_issues }}

**Recommendation:** {{ recommendation_status }}

**Summary:** {{ executive_summary }}

---

## Detailed Findings

### 1. Secrets Management

**Status:** {{ secrets_management_status }}

**Checks Performed:**
- [x] No hardcoded credentials in source code
- [x] No hardcoded credentials in tests
- [x] Environment variables or secret managers used correctly
- [x] Variable names documented
- [x] Test credentials are clearly fake

**Findings:**

{{ secrets_management_findings }}

**Recommendations:**
{{ secrets_management_recommendations }}

---

### 2. Input Validation

**Status:** {{ input_validation_status }}

**Checks Performed:**
- [x] All user inputs validated
- [x] Type checking on parameters
- [x] Range validation where applicable
{% if config.technology_stack.database %}
- [x] No SQL injection vulnerabilities
{% endif %}
- [x] No URL injection vulnerabilities
- [x] No command injection vulnerabilities
- [x] Special characters handled safely
{% if config.project.type == 'web-app' %}
- [x] XSS prevention (input sanitization)
- [x] CSRF protection enabled
{% endif %}

**Findings:**

{{ input_validation_findings }}

**Parameter Validation Table:**

| Parameter | Type Check | Range Check | Sanitization | Status |
|-----------|------------|-------------|--------------|--------|
{{ parameter_validation_table_rows }}

**Recommendations:**
{{ input_validation_recommendations }}

---

### 3. Logging

**Status:** {{ logging_status }}

**Checks Performed:**
- [x] No credentials in log statements
- [x] No PII in logs (without explicit user consent)
- [x] No full API responses logged (unless sanitized)
- [x] Error messages don't leak secrets
- [x] Debug mode doesn't expose sensitive data
{% if config.project.type == 'web-app' %}
- [x] Client-side logs don't expose sensitive data
{% endif %}

**Findings:**

{{ logging_findings }}

**Recommendations:**
{{ logging_recommendations }}

---

{% if config.project.type == 'api' or 'web-app' %}
### 4. Rate Limiting

**Status:** {{ rate_limiting_status }}

**Checks Performed:**
- [x] Rate limiting implemented for API endpoints
- [x] Rate limits configured appropriately
- [x] Rate limit bypass prevention
- [x] Rate limits match API documentation (if applicable)
{% if config.project.type == 'web-app' %}
- [x] Login endpoint has rate limiting (brute force prevention)
- [x] Resource-intensive endpoints protected
{% endif %}

**Findings:**

{{ rate_limiting_findings }}

**Recommendations:**
{{ rate_limiting_recommendations }}

---
{% endif %}

### {{ next_section_number }}. TLS/HTTPS

**Status:** {{ tls_https_status }}

**Checks Performed:**
- [x] All production URLs use HTTPS
- [x] No SSL/TLS verification disabled
- [x] No plaintext communication in production
- [x] Certificate validation enabled
{% if config.project.type == 'web-app' %}
- [x] Secure cookie flags set (Secure, HttpOnly, SameSite)
- [x] HSTS header configured
{% endif %}

**Findings:**

{{ tls_https_findings }}

**Recommendations:**
{{ tls_https_recommendations }}

---

### {{ next_section_number }}. Error Handling

**Status:** {{ error_handling_status }}

**Checks Performed:**
- [x] Error messages don't reveal system internals
- [x] Error messages don't include credentials
- [x] Stack traces don't leak sensitive paths
- [x] Error messages are helpful but not too specific
{% if config.project.type == 'web-app' %}
- [x] Custom error pages configured (no framework defaults)
- [x] Debug mode disabled in production
{% endif %}

**Findings:**

{{ error_handling_findings }}

**Error Message Review:**

| Error Type | Information Leaked | Severity | Status |
|------------|-------------------|----------|--------|
{{ error_message_table_rows }}

**Recommendations:**
{{ error_handling_recommendations }}

---

### {{ next_section_number }}. Authentication & Authorization

**Status:** {{ auth_status }}

{% if config.project.type == 'web-app' or config.project.type == 'api' %}
**Checks Performed:**
- [x] Authentication mechanism secure ({{ config.authentication.method or 'JWT/OAuth2/Session' }})
- [x] Passwords hashed with strong algorithm (bcrypt/argon2)
- [x] Password complexity requirements enforced
- [x] Session management secure (timeout, invalidation)
- [x] Authorization checks on all protected endpoints
- [x] Role-based access control (RBAC) implemented correctly
{% if config.authentication.method == 'jwt' %}
- [x] JWT tokens signed with strong secret
- [x] JWT tokens have expiration
- [x] Token refresh mechanism secure
{% elif config.authentication.method == 'oauth2' %}
- [x] OAuth2 flows implemented correctly
- [x] State parameter used (CSRF prevention)
- [x] Token storage secure
{% endif %}

**Findings:**

{{ auth_findings }}

**Recommendations:**
{{ auth_recommendations }}

---
{% else %}
**Not Applicable:** {{ component_name }} does not implement authentication.

---
{% endif %}

### {{ next_section_number }}. Dependencies

**Status:** {{ dependencies_status }}

**Checks Performed:**
- [x] All dependencies up to date
- [x] No known CVEs in dependencies
- [x] No deprecated packages
- [x] Minimal dependencies used
- [x] Dependency versions pinned

**Findings:**

{{ dependencies_findings }}

**Dependencies Review:**

{% if config.technology_stack.backend.language == 'python' %}
| Package | Current Version | Latest Version | CVEs | Status |
|---------|----------------|----------------|------|--------|
{{ dependencies_table_rows }}

**CVE Check:**
```bash
# Run: pip-audit
{{ cve_check_output }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
| Package | Current Version | Latest Version | CVEs | Status |
|---------|----------------|----------------|------|--------|
{{ dependencies_table_rows }}

**CVE Check:**
```bash
# Run: npm audit
{{ cve_check_output }}
```
{% elif config.technology_stack.backend.language == 'java' %}
| Package | Current Version | Latest Version | CVEs | Status |
|---------|----------------|----------------|------|--------|
{{ dependencies_table_rows }}

**CVE Check:**
```bash
# Run: mvn dependency:tree and OWASP Dependency Check
{{ cve_check_output }}
```
{% elif config.technology_stack.backend.language == 'go' %}
| Package | Current Version | Latest Version | CVEs | Status |
|---------|----------------|----------------|------|--------|
{{ dependencies_table_rows }}

**CVE Check:**
```bash
# Run: go list -m all and govulncheck
{{ cve_check_output }}
```
{% endif %}

**Recommendations:**
{{ dependencies_recommendations }}

---

### {{ next_section_number }}. Test Security

**Status:** {{ test_security_status }}

**Checks Performed:**
- [x] No real credentials in test code
- [x] All external API calls mocked
- [x] Test data is fake/sanitized
- [x] No tests hitting production APIs
- [x] Test fixtures don't contain sensitive data
- [x] Test environment isolated from production

**Findings:**

{{ test_security_findings }}

**Test Credential Review:**
- Test credentials: {{ test_credentials_type }}
- API mocking: {{ api_mocking_status }}
- Test data: {{ test_data_status }}

**Recommendations:**
{{ test_security_recommendations }}

---

{% if config.project.type == 'web-app' %}
### {{ next_section_number }}. Frontend Security

**Status:** {{ frontend_security_status }}

**Checks Performed:**
- [x] XSS prevention (DOMPurify or equivalent)
- [x] CSRF protection enabled
- [x] Content Security Policy (CSP) configured
- [x] Input sanitization on client side
- [x] Sensitive data not stored in localStorage
- [x] API keys not exposed in client code
- [x] Source maps disabled in production

**Findings:**

{{ frontend_security_findings }}

**Recommendations:**
{{ frontend_security_recommendations }}

---
{% endif %}

{% if config.technology_stack.database %}
### {{ next_section_number }}. Database Security

**Status:** {{ database_security_status }}

**Checks Performed:**
- [x] No SQL injection vulnerabilities
- [x] Parameterized queries used (no string concatenation)
- [x] Database credentials not hardcoded
- [x] Principle of least privilege for DB user
- [x] Database connection encrypted
- [x] Sensitive data encrypted at rest (if applicable)

**Findings:**

{{ database_security_findings }}

**Recommendations:**
{{ database_security_recommendations }}

---
{% endif %}

## Risk Assessment

### Critical Issues (Must Fix Before {{ deployment_stage or 'Integration' }})

{{ critical_issues_section }}

---

### High Issues (Should Fix Before {{ deployment_stage or 'Integration' }})

{{ high_issues_section }}

---

### Medium Issues (Consider Fixing)

{{ medium_issues_section }}

---

### Low / Info Issues

{{ low_info_issues_section }}

---

## Code Quality Observations

**Positive Observations:**
{{ positive_observations }}

**Areas for Improvement:**
{{ areas_for_improvement }}

---

## Recommendations for {{ config.roles.integration_engineer or 'Integration Engineer' }}

**Integration Notes:**
{{ integration_notes }}

**Testing Notes:**
{{ testing_notes }}

---

## Recommendations for {{ config.roles.documentation_engineer or 'Documentation Engineer' }}

**Documentation Required:**
{{ documentation_required }}

**Security Notes for Users:**
{{ security_notes_for_users }}

---

## Approval Decision

### Status: {{ approval_decision }}

{% if approval_decision == 'APPROVED' %}
✅ **APPROVED**

**Summary:**
{{ approval_summary }}

**Conditions:**
None - proceed to {{ next_handoff or 'next step' }}.

---

{% elif approval_decision == 'CONDITIONALLY APPROVED' %}
✅ **CONDITIONALLY APPROVED**

**Summary:**
{{ conditional_approval_summary }}

**Required Fixes:**
{{ required_fixes_list }}

**Optional Fixes:**
{{ optional_fixes_list }}

**Re-review Required:**
{{ re_review_required }}
- If Yes: Re-run security review after fixes
- If No: Fixes are straightforward, proceed after implementing

**Proceed to {{ next_handoff or 'next step' }} after fixing required issues.**

---

{% elif approval_decision == 'REJECTED' %}
❌ **REJECTED**

**Summary:**
{{ rejection_summary }}

**Critical Issues:**
{{ critical_issues_list }}

**Next Steps:**
1. Fix all critical issues
2. Re-submit for security review
3. Do NOT proceed until APPROVED

**Estimated Time to Fix:** {{ estimated_fix_time }}

---
{% endif %}

## Appendix: Security Checklist

**Full Checklist (for reference):**

**Secrets Management:**
- [ ] No hardcoded credentials in source
- [ ] No hardcoded credentials in tests
- [ ] Environment variables or secret managers used
- [ ] Variable names documented
- [ ] Test credentials clearly fake

**Input Validation:**
- [ ] All inputs validated
- [ ] Type checking
- [ ] Range checking
- [ ] No injection vulnerabilities
- [ ] Special characters handled

**Logging:**
- [ ] No credentials logged
- [ ] No PII logged (without consent)
- [ ] No full responses logged
- [ ] Error messages appropriate

{% if config.project.type == 'api' or config.project.type == 'web-app' %}
**Rate Limiting:**
- [ ] Rate limiting implemented
- [ ] Rate limits configured
- [ ] No bypass mechanisms
{% endif %}

**TLS/HTTPS:**
- [ ] All URLs HTTPS
- [ ] SSL verification enabled
- [ ] No plaintext communication

**Error Handling:**
- [ ] No information leakage
- [ ] Helpful messages
- [ ] No credential exposure

{% if config.project.type == 'web-app' or config.project.type == 'api' %}
**Authentication & Authorization:**
- [ ] Secure authentication mechanism
- [ ] Passwords hashed (bcrypt/argon2)
- [ ] Session management secure
- [ ] Authorization checks on protected endpoints
- [ ] RBAC implemented correctly
{% endif %}

**Dependencies:**
- [ ] No known CVEs
- [ ] Packages up to date
- [ ] Minimal dependencies
- [ ] Versions pinned

**Test Security:**
- [ ] No real credentials in tests
- [ ] All external calls mocked
- [ ] Test data fake

{% if config.project.type == 'web-app' %}
**Frontend Security:**
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] CSP configured
- [ ] No API keys in client code
{% endif %}

{% if config.technology_stack.database %}
**Database Security:**
- [ ] No SQL injection
- [ ] Parameterized queries
- [ ] Credentials not hardcoded
- [ ] Least privilege DB user
{% endif %}

---

## Sign-off

**Reviewed by:** {{ reviewer_name }}
**Date:** {{ review_date }}
**Status:** {{ approval_decision }}

**Next Steps:**
{% if approval_decision == 'APPROVED' %}
Proceed to {{ next_handoff or 'Integration Engineer' }}
{% elif approval_decision == 'CONDITIONALLY APPROVED' %}
Fix issues listed above, then proceed
{% elif approval_decision == 'REJECTED' %}
Fix critical issues and re-submit for review
{% endif %}

---

**Handoff File:** `{{ handoff_file_path }}`
