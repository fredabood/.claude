---
id: research-summary
name: Research Summary
version: 1.0.0
from_agent: researcher
to_agents:
- sprint-planning
- web-developer
purpose: Template for research summary
variables:
- name: api_key_env_var
  type: string
  required: true
  description: Api Key Env Var value
- name: architecture_diagram
  type: string
  required: true
  description: Architecture Diagram value
- name: artifact_id
  type: string
  required: true
  description: Artifact Id value
- name: auth_header_format
  type: string
  required: true
  description: Auth Header Format value
- name: auth_header_name
  type: string
  required: true
  description: Auth Header Name value
- name: auth_method
  type: string
  required: true
  description: Auth Method value
- name: base_url
  type: string
  required: true
  description: Base Url value
- name: basic_configuration_code
  type: string
  required: true
  description: Basic Configuration Code value
- name: compression_ratio
  type: string
  required: true
  description: Compression Ratio value
- name: con
  type: string
  required: true
  description: Con value
- name: difference
  type: string
  required: true
  description: Difference value
- name: endpoint
  type: string
  required: true
  description: Endpoint value
- name: error_handling_example_python
  type: string
  required: true
  description: Error Handling Example Python value
- name: error_handling_example_typescript
  type: string
  required: true
  description: Error Handling Example Typescript value
- name: fact
  type: string
  required: true
  description: Fact value
description: Template for research summary
---

# Research Summary: {{ research_topic }}

**Document Type:** Handoff Template
**From:** {{ config.roles.researcher or 'Researcher' }}
**To:** {{ requesting_agent }}
**Purpose:** Concise documentation summary with actionable insights
**Related Workflow:** Documentation Research Workflow - Step 3

---

## Summary Metadata

| Field | Value |
|-------|-------|
| **Research Topic** | {{ research_topic }} |
| **Original Source** | {{ original_source_url }} |
| **Original Size** | {{ original_size }} |
| **Summary Size** | {{ summary_size }} |
| **Compression Ratio** | {{ compression_ratio }}% |
| **Research Type** | {{ research_type }} |
| **Created By** | {{ researcher_name }} |
| **Date** | {{ research_date }} |
| **Status** | {{ research_status }} |

---

## 1. Executive Summary

### What Is It?
{{ what_is_it_summary }}

### Why Use It?
{{ why_use_it_summary }}

### Key Use Cases
{% for use_case in key_use_cases %}
- {{ use_case }}
{% endfor %}

### When NOT to Use
{{ when_not_to_use }}

---

## 2. Quick Reference

### Key Facts
{% for fact in key_facts %}
- {{ fact }}
{% endfor %}

### Important Gotchas
{% for gotcha in gotchas %}
- ⚠️ **{{ gotcha.title }}:** {{ gotcha.description }}
{% endfor %}

### Prerequisites
{% for prerequisite in prerequisites %}
- {{ prerequisite }}
{% endfor %}

---

{% if research_type in ['api', 'rest_api', 'graphql'] %}
## 3. Authentication

**Method:** {{ auth_method }}

{% if auth_method == 'api_key' %}
**Setup:**
{% if config.technology_stack.backend.language == 'python' %}
```python
import os
import requests

API_KEY = os.getenv("{{ api_key_env_var }}")
headers = {
    "{{ auth_header_name }}": f"{{ auth_header_format }}"
}

response = requests.get("{{ base_url }}/{{ endpoint }}", headers=headers)
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
const apiKey = process.env.{{ api_key_env_var }};
const headers = {
    "{{ auth_header_name }}": `{{ auth_header_format }}`
};

const response = await fetch("{{ base_url }}/{{ endpoint }}", { headers });
```
{% endif %}

{% elif auth_method == 'oauth2' %}
**OAuth2 Flow:**
{% if config.technology_stack.backend.language == 'python' %}
```python
from requests_oauthlib import OAuth2Session

client_id = os.getenv("{{ oauth_client_id_var }}")
client_secret = os.getenv("{{ oauth_client_secret_var }}")

oauth = OAuth2Session(client_id)
token = oauth.fetch_token(
    "{{ token_url }}",
    client_secret=client_secret
)

response = oauth.get("{{ base_url }}/{{ endpoint }}")
```
{% endif %}

{% elif auth_method == 'jwt' %}
**JWT Authentication:**
{% if config.technology_stack.backend.language == 'python' %}
```python
import jwt
import datetime

secret = os.getenv("{{ jwt_secret_var }}")
payload = {
    "sub": "user_id",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token = jwt.encode(payload, secret, algorithm="{{ jwt_algorithm }}")

headers = {"Authorization": f"Bearer {token}"}
response = requests.get("{{ base_url }}/{{ endpoint }}", headers=headers)
```
{% endif %}
{% endif %}

**Rate Limits:** {{ rate_limits }}

---

## 4. Key Endpoints / Concepts

| Endpoint/Concept | Purpose | Method | Example |
|------------------|---------|--------|---------|
{% for item in key_items %}
| `{{ item.path }}` | {{ item.purpose }} | {{ item.method }} | `{{ item.example }}` |
{% endfor %}

---

{% elif research_type in ['library', 'framework', 'package'] %}
## 3. Installation & Setup

**Installation:**
{% if config.technology_stack.backend.language == 'python' %}
```bash
pip install {{ package_name }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```bash
npm install {{ package_name }}
# or
yarn add {{ package_name }}
```
{% elif config.technology_stack.backend.language == 'java' %}
```xml
<dependency>
    <groupId>{{ group_id }}</groupId>
    <artifactId>{{ artifact_id }}</artifactId>
    <version>{{ version }}</version>
</dependency>
```
{% elif config.technology_stack.backend.language == 'go' %}
```bash
go get {{ package_import_path }}
```
{% endif %}

**Basic Configuration:**
```{{ config.technology_stack.backend.language }}
{{ basic_configuration_code }}
```

---

## 4. Core Concepts

{% for concept in core_concepts %}
### {{ concept.name }}

**What It Is:** {{ concept.description }}

**When to Use:** {{ concept.when_to_use }}

**Example:**
```{{ config.technology_stack.backend.language }}
{{ concept.example_code }}
```

{% endfor %}

---

{% elif research_type in ['architecture', 'design_pattern'] %}
## 3. Architecture Overview

**Pattern Type:** {{ pattern_type }}

**Problem Solved:** {{ problem_solved }}

**Key Components:**
{% for component in architecture_components %}
- **{{ component.name }}:** {{ component.description }}
{% endfor %}

**Architecture Diagram:**
```
{{ architecture_diagram }}
```

---

## 4. Implementation Patterns

{% for pattern in implementation_patterns %}
### {{ pattern.name }}

**Use Case:** {{ pattern.use_case }}

**Structure:**
{{ pattern.structure_description }}

**Example:**
```{{ config.technology_stack.backend.language }}
{{ pattern.example_code }}
```

**Pros:**
{% for pro in pattern.pros %}
- {{ pro }}
{% endfor %}

**Cons:**
{% for con in pattern.cons %}
- {{ con }}
{% endfor %}

{% endfor %}

---
{% endif %}

## 5. Code Templates

{% for template in code_templates %}
### Template {{ loop.index }}: {{ template.use_case }}

**Purpose:** {{ template.purpose }}

**Code:**
{% if config.technology_stack.backend.language == 'python' %}
```python
{{ template.python_code }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
{{ template.typescript_code }}
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
{{ template.java_code }}
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
{{ template.go_code }}
```
{% endif %}

**Explanation:**
{{ template.explanation }}

{% endfor %}

---

## 6. Common Patterns & Best Practices

### Recommended Patterns
{% for pattern in recommended_patterns %}
- **{{ pattern.name }}:** {{ pattern.description }}
{% endfor %}

### Anti-Patterns (Avoid)
{% for antipattern in antipatterns %}
- **{{ antipattern.name }}:** {{ antipattern.description }} - Use {{ antipattern.alternative }} instead
{% endfor %}

### Performance Optimization
{% for optimization in performance_optimizations %}
- {{ optimization }}
{% endfor %}

---

## 7. Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
{% for error in common_errors %}
| `{{ error.code }}` | {{ error.cause }} | {{ error.solution }} |
{% endfor %}

### Error Handling Pattern

{% if config.technology_stack.backend.language == 'python' %}
```python
{{ error_handling_example_python }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
{{ error_handling_example_typescript }}
```
{% endif %}

---

## 8. Testing

### Testing Strategy
{{ testing_strategy }}

### Test Examples

{% if config.testing.framework %}
{% if config.testing.framework == 'pytest' %}
```python
import pytest

{{ test_example_pytest }}
```
{% elif config.testing.framework in ['jest', 'vitest'] %}
```typescript
import { describe, it, expect } from '{{ config.testing.framework }}';

{{ test_example_jest }}
```
{% elif config.testing.framework == 'junit' %}
```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

{{ test_example_junit }}
```
{% endif %}
{% endif %}

---

## 9. Production Considerations

### Security
{% for security_item in security_considerations %}
- {{ security_item }}
{% endfor %}

### Performance
{% for performance_item in performance_considerations %}
- {{ performance_item }}
{% endfor %}

### Scalability
{% for scalability_item in scalability_considerations %}
- {{ scalability_item }}
{% endfor %}

### Monitoring
{{ monitoring_recommendations }}

---

## 10. Integration Examples

{% for integration in integration_examples %}
### Integration with {{ integration.system }}

**Use Case:** {{ integration.use_case }}

**Implementation:**
```{{ config.technology_stack.backend.language }}
{{ integration.code_example }}
```

{% endfor %}

---

## 11. Migration Guide

{% if migration_guide %}
### Migrating from {{ migration_from }}

**Key Differences:**
{% for difference in migration_differences %}
- {{ difference }}
{% endfor %}

**Migration Steps:**
{% for step in migration_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

**Code Comparison:**

**Before ({{ migration_from }}):**
```{{ config.technology_stack.backend.language }}
{{ migration_before_code }}
```

**After ({{ research_topic }}):**
```{{ config.technology_stack.backend.language }}
{{ migration_after_code }}
```
{% endif %}

---

## 12. Troubleshooting

### Common Issues

{% for issue in common_issues %}
**Issue:** {{ issue.description }}
- **Symptoms:** {{ issue.symptoms }}
- **Diagnosis:** {{ issue.diagnosis }}
- **Fix:** {{ issue.fix }}

{% endfor %}

---

## 13. Further Reading & Deep Dives

### Essential Resources
{% for resource in essential_resources %}
- **{{ resource.title }}:** {{ resource.url }} - {{ resource.description }}
{% endfor %}

### Advanced Topics
{% for topic in advanced_topics %}
- **{{ topic.name }}:** {{ topic.description }} (See: {{ topic.reference }})
{% endfor %}

### Related Technologies
{% for tech in related_technologies %}
- **{{ tech.name }}:** {{ tech.relationship_description }}
{% endfor %}

---

## 14. Quick Start Checklist

**To get started with {{ research_topic }}:**

{% for step in quick_start_steps %}
- [ ] {{ step }}
{% endfor %}

---

## 15. Indexed Sections (for Deep Dives)

{% for section in indexed_sections %}
- **{{ section.title }}:** {{ section.description }} ([Original Docs]({{ section.url }}))
{% endfor %}

---

## Appendix: Version Compatibility

| {{ research_topic }} Version | Compatible With | Notes |
|---|---|---|
{% for compatibility in version_compatibility %}
| {{ compatibility.version }} | {{ compatibility.compatible_with }} | {{ compatibility.notes }} |
{% endfor %}

---

**Research Complete:** {{ research_completion_status }}
**Compression Achieved:** {{ compression_ratio }}% ({{ original_size }} → {{ summary_size }})
**Actionable:** {{ is_actionable }}

**Next Steps:**
{{ next_steps }}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
