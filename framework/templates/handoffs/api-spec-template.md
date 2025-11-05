# API Specification: {{ api_name }}

**Created by:** API Architect
**Date:** {{ date }}
**For:** API Engineer / Backend Developer

---

## Executive Summary

**Source:** {{ api_full_name }}
**Provider:** {{ api_provider }}
**Category:** {{ api_category }}
**Documentation:** {{ api_documentation_url }}

**Purpose:** {{ api_purpose }}

**Complexity:** {{ complexity_level }}
- Simple: Single endpoint, no auth, straightforward response
- Medium: Multiple endpoints, API key auth, structured responses
- Complex: OAuth2, many endpoints, complex data structures, rate limiting challenges

---

## API Overview

### Authentication

**Method:** {{ auth_method }}

{% if auth_method == 'api_key' %}
**API Key Details:**
- Header format: `{{ auth_header_name }}: {{ auth_header_format }}`
- Example: `X-API-Key: your_key_here` OR `Authorization: Bearer your_key_here`
- Environment variable: `{{ api_name|upper }}_API_KEY` (uppercase, underscores)
- How to obtain: {{ api_key_registration_url }}
- Cost: {{ api_cost }}

{% elif auth_method == 'oauth2' %}
**OAuth2 Details:**
- Grant type: {{ oauth_grant_type }}
- Token URL: {{ oauth_token_url }}
- Scopes required: {{ oauth_scopes }}
- Client ID/Secret format: {{ oauth_client_format }}
- Token expiry: {{ oauth_token_expiry }}
- Refresh strategy: {{ oauth_refresh_strategy }}

{% elif auth_method == 'basic_auth' %}
**Basic Auth Details:**
- Header format: `Authorization: Basic {{ base64_encoded_credentials }}`
- Username/Password: {{ basic_auth_details }}

{% elif auth_method == 'none' %}
**No Authentication:**
- Public API, no authentication required

{% endif %}

### Base URL

```
{{ api_base_url }}
```

**Examples:**
- Production: `{{ api_production_url }}`
{% if api_sandbox_url %}
- Sandbox: `{{ api_sandbox_url }}`
{% endif %}

### Data Format

**Request:** {{ request_format }}
**Response:** {{ response_format }}

**Content-Type:** {{ content_type }}

### API Version

**Current Version:** {{ api_version }}
{% if api_version_header %}
**Version Header:** `{{ api_version_header }}`
{% endif %}
**Versioning Strategy:** {{ api_versioning_strategy }}

---

## Endpoints to Implement

### Endpoint 1: {{ endpoint_1_name }}

**Priority:** {{ endpoint_1_priority }}

**URL Pattern:**
```
{{ endpoint_1_method }} {{ endpoint_1_url_pattern }}
```

**Example:**
```
{{ endpoint_1_example_request }}
```

**Purpose:** {{ endpoint_1_purpose }}

{% if config.project.type == 'data-platform' %}
**Data Scope:** {{ endpoint_1_data_scope }}
{% endif %}

**Parameters:**

| Parameter | Type | Required | Description | Example | Default |
|-----------|------|----------|-------------|---------|---------|
{% for param in endpoint_1_parameters %}
| {{ param.name }} | {{ param.type }} | {{ param.required }} | {{ param.description }} | {{ param.example }} | {{ param.default }} |
{% endfor %}

**Response Format:**

```json
{{ endpoint_1_response_example }}
```

**Response Fields:**

| Field | Type | Always Present? | Description |
|-------|------|----------------|-------------|
{% for field in endpoint_1_response_fields %}
| {{ field.path }} | {{ field.type }} | {{ field.required }} | {{ field.description }} |
{% endfor %}

**Error Responses:**

| Status Code | Condition | Response |
|-------------|-----------|----------|
| 400 | Invalid parameters | `{"error": "{{ error_400_message }}"}` |
| 401 | Missing/invalid auth | `{"error": "Unauthorized"}` |
| 404 | Resource not found | `{"error": "{{ error_404_message }}"}` |
| 429 | Rate limit exceeded | `{"error": "Rate limit exceeded", "retry_after": 60}` |
| 500 | Server error | `{"error": "Internal server error"}` |

{% if config.project.type == 'data-platform' %}
**Cache Strategy:**
- Should cache: {{ endpoint_1_should_cache }}
- Cache key format: `{{ cache_key_format }}`
- Cache TTL: {{ cache_ttl }}
- Invalidation: {{ cache_invalidation_strategy }}
{% endif %}

**Implementation Notes:**
- {{ endpoint_1_implementation_notes }}

---

### Endpoint 2: {{ endpoint_2_name }}

[Repeat structure from Endpoint 1 for each additional endpoint]

[If many endpoints, prioritize and document only MUST HAVE and key SHOULD HAVE endpoints]

---

## Rate Limiting

### Limits

**Official Limits:**
- Requests per period: {{ rate_limit_requests }} requests per {{ rate_limit_period }}
- Burst allowed: {{ rate_limit_burst_allowed }}
- Per API key: {{ rate_limit_per_key }}
- Global: {{ rate_limit_global }}

**Rate Limit Headers:**
```
{{ rate_limit_headers_example }}
```

**Recommended Client-Side Limits:**
{% if config.technology_stack.backend.language == 'python' %}
```python
RATE_LIMIT_CALLS = {{ recommended_rate_limit_calls }}
RATE_LIMIT_PERIOD = {{ recommended_rate_limit_period }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
const RATE_LIMIT_CALLS = {{ recommended_rate_limit_calls }};
const RATE_LIMIT_PERIOD = {{ recommended_rate_limit_period }};
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
public static final int RATE_LIMIT_CALLS = {{ recommended_rate_limit_calls }};
public static final int RATE_LIMIT_PERIOD = {{ recommended_rate_limit_period }};
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
const RateLimitCalls = {{ recommended_rate_limit_calls }}
const RateLimitPeriod = {{ recommended_rate_limit_period }}
```
{% endif %}

**Rationale:** {{ rate_limit_rationale }}

### Throttling Strategy

**Approach:** {{ throttling_approach }}

**Retry Strategy:**
- Max retries: {{ max_retries }}
- Backoff: {{ backoff_strategy }}
- Factor: {{ backoff_factor }}
- Retry on codes: {{ retry_on_codes }}
- Don't retry on: {{ no_retry_on_codes }}

---

{% if config.project.type == 'data-platform' %}
## Caching Strategy

### Data Scope

**Data Coverage:** {{ data_coverage }}

**Rationale:** {{ caching_rationale }}

### Caching Recommendation

**Should Cache:** {{ should_cache }}

{% if should_cache %}
**Cache Level:** {{ cache_level }}

**Cache Key Format:**
```
{{ cache_key_format }}
```

**Examples:**
{{ cache_key_examples }}

**Cache TTL (Time-To-Live):**
- Duration: {{ cache_ttl_duration }}
- Rationale: {{ cache_ttl_rationale }}

{% else %}
**Rationale:** {{ no_cache_rationale }}
{% endif %}

### Update Frequency

**How often does this data change?**
- {{ data_update_frequency }}

**Cache TTL Recommendation:**
{{ cache_ttl_recommendation }}

---
{% endif %}

## Data Structures

### Structure 1: {{ structure_1_name }}

**Used By:** {{ structure_1_used_by }}

**Schema:**
{% if response_format == 'json' %}
```json
{{ structure_1_json_schema }}
```
{% elif response_format == 'xml' %}
```xml
{{ structure_1_xml_schema }}
```
{% endif %}

**Field Definitions:**

| Field Path | Type | Required | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
{% for field in structure_1_fields %}
| {{ field.path }} | {{ field.type }} | {{ field.required }} | {{ field.description }} | {{ field.example }} | {{ field.notes }} |
{% endfor %}

**Validation Rules:**
{{ structure_1_validation_rules }}

### Structure 2: Error Response

{{ error_response_structure }}

---

{% if config.project.type == 'data-platform' %}
## Record Storage Specification

**When storing records, include:**

{% if config.technology_stack.backend.language == 'python' %}
```python
Record(
    source="{{ api_name }}",
    request_params={
        "endpoint": "{{ endpoint_called }}",
        {{ request_params_example }}
    },
    response_raw="{{ response_raw }}",
    response_status={{ http_status_code }},
    response_headers={
        {{ response_headers_example }}
    },
    metadata={
        {{ metadata_example }}
    }
)
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
{
    source: "{{ api_name }}",
    requestParams: {
        endpoint: "{{ endpoint_called }}",
        {{ request_params_example }}
    },
    responseRaw: "{{ response_raw }}",
    responseStatus: {{ http_status_code }},
    responseHeaders: {
        {{ response_headers_example }}
    },
    metadata: {
        {{ metadata_example }}
    }
}
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
Record.builder()
    .source("{{ api_name }}")
    .requestParams(Map.of(
        "endpoint", "{{ endpoint_called }}",
        {{ request_params_example }}
    ))
    .responseRaw("{{ response_raw }}")
    .responseStatus({{ http_status_code }})
    .responseHeaders(Map.of(
        {{ response_headers_example }}
    ))
    .metadata(Map.of(
        {{ metadata_example }}
    ))
    .build();
```
{% endif %}

---
{% endif %}

## Error Handling

### HTTP Error Codes

| Code | Meaning | Action | Retry? |
|------|---------|--------|--------|
| 400 | Bad Request | Log params, raise error | No |
| 401 | Unauthorized | Check credentials, raise error | No |
| 403 | Forbidden | Check permissions, raise error | No |
| 404 | Not Found | Resource doesn't exist, raise error | No |
| 429 | Rate Limited | Wait retry_after, then retry | Yes (after wait) |
| 500 | Server Error | Log, raise exception | Yes (with backoff) |
| 502 | Bad Gateway | Log, raise exception | Yes (with backoff) |
| 503 | Service Unavailable | Log, raise exception | Yes (with backoff) |
| 504 | Gateway Timeout | Log, raise exception | Yes (with backoff) |

### API-Specific Errors

{{ api_specific_errors }}

### Data Validation Errors

**Client-side validation before API call:**
{{ client_side_validation }}

**Server response validation:**
{{ server_response_validation }}

---

## Implementation Guidance

### Class/Module Structure

{% if config.technology_stack.backend.language == 'python' %}
```python
"""
{{ api_name }} API Client

This module provides a client for accessing {{ api_description }}.

API Documentation: {{ api_documentation_url }}
"""

from typing import Dict, Any, Optional
import requests
from datetime import datetime

{% if config.project.type == 'data-platform' %}
from {{ config.project.name }}.base_api_client import BaseAPIClient, Record
{% endif %}


class {{ api_class_name }}{% if config.project.type == 'data-platform' %}(BaseAPIClient){% endif %}:
    """
    Client for {{ api_name }} API.

    {{ api_detailed_description }}

    API Documentation: {{ api_documentation_url }}

    Example:
        >>> client = {{ api_class_name }}(api_key="your_key")
        >>> result = client.{{ primary_method }}(param="value")
        >>> print(result)
    """

    SOURCE_NAME = "{{ api_name }}"
    BASE_URL = "{{ api_base_url }}"
    RATE_LIMIT_CALLS = {{ recommended_rate_limit_calls }}
    RATE_LIMIT_PERIOD = {{ recommended_rate_limit_period }}

    def __init__(
        self,
        {% if auth_method != 'none' %}api_key: Optional[str] = None,{% endif %}
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize {{ api_name }} API client.

        Args:
            {% if auth_method != 'none' %}api_key: {{ api_key_description }}{% endif %}
            base_url: Override default API base URL (for testing)
            **kwargs: Additional arguments
        """
        {% if config.project.type == 'data-platform' %}
        super().__init__(
            source_name=self.SOURCE_NAME,
            rate_limit_calls=self.RATE_LIMIT_CALLS,
            rate_limit_period=self.RATE_LIMIT_PERIOD,
            **kwargs
        )
        {% endif %}
        {% if auth_method != 'none' %}self.api_key = api_key{% endif %}
        self.base_url = base_url or self.BASE_URL

    {% if auth_method != 'none' %}
    def _get_api_key(self) -> Optional[str]:
        """
        Return API key if authentication is required.

        Returns:
            API key string if required, None if public API

        Raises:
            ValueError: If API key is required but not provided
        """
        if not self.api_key:
            raise ValueError("API key required but not provided")
        return self.api_key
    {% endif %}

    def _prepare_headers(self, **kwargs) -> Dict[str, str]:
        """
        Prepare HTTP headers for API requests.

        Returns:
            Dict of headers to include in requests
        """
        headers = {"Content-Type": "{{ content_type }}"}
        {% if auth_method == 'api_key' %}
        api_key = self._get_api_key()
        headers["{{ auth_header_name }}"] = f"{{ auth_header_format.replace('your_key_here', '{api_key}') }}"
        {% elif auth_method == 'bearer' %}
        api_key = self._get_api_key()
        headers["Authorization"] = f"Bearer {api_key}"
        {% endif %}
        return headers

    def {{ primary_method_name }}(self, {{ primary_method_params }}) -> {{ primary_method_return_type }}:
        """
        {{ primary_method_description }}

        Args:
            {{ primary_method_args_docs }}

        Returns:
            {{ primary_method_return_description }}

        Raises:
            ValueError: {{ primary_method_raises }}

        Example:
            >>> client = {{ api_class_name }}()
            >>> result = client.{{ primary_method_name }}({{ primary_method_example_call }})
        """
        pass
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
/**
 * {{ api_name }} API Client
 *
 * This module provides a client for accessing {{ api_description }}.
 *
 * API Documentation: {{ api_documentation_url }}
 */

{% if config.project.type == 'data-platform' %}
import { BaseAPIClient, Record } from './base-api-client';
{% endif %}

interface {{ api_class_name }}Config {
    {% if auth_method != 'none' %}apiKey?: string;{% endif %}
    baseUrl?: string;
}

export class {{ api_class_name }} {% if config.project.type == 'data-platform' %}extends BaseAPIClient {% endif %}{
    private readonly sourceName = '{{ api_name }}';
    private readonly baseUrl: string;
    {% if auth_method != 'none' %}private readonly apiKey?: string;{% endif %}
    private readonly rateLimitCalls = {{ recommended_rate_limit_calls }};
    private readonly rateLimitPeriod = {{ recommended_rate_limit_period }};

    constructor(config: {{ api_class_name }}Config = {}) {
        {% if config.project.type == 'data-platform' %}
        super({
            sourceName: this.sourceName,
            rateLimitCalls: this.rateLimitCalls,
            rateLimitPeriod: this.rateLimitPeriod,
        });
        {% endif %}
        {% if auth_method != 'none' %}this.apiKey = config.apiKey;{% endif %}
        this.baseUrl = config.baseUrl || '{{ api_base_url }}';
    }

    {% if auth_method != 'none' %}
    private getApiKey(): string {
        if (!this.apiKey) {
            throw new Error('API key required but not provided');
        }
        return this.apiKey;
    }
    {% endif %}

    private prepareHeaders(): Record<string, string> {
        const headers: Record<string, string> = {
            'Content-Type': '{{ content_type }}'
        };
        {% if auth_method == 'api_key' %}
        const apiKey = this.getApiKey();
        headers['{{ auth_header_name }}'] = `{{ auth_header_format.replace('your_key_here', '${apiKey}') }}`;
        {% elif auth_method == 'bearer' %}
        const apiKey = this.getApiKey();
        headers['Authorization'] = `Bearer ${apiKey}`;
        {% endif %}
        return headers;
    }

    async {{ primary_method_name }}({{ primary_method_params }}): Promise<{{ primary_method_return_type }}> {
        // Implementation
    }
}
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
/**
 * {{ api_name }} API Client
 *
 * This class provides a client for accessing {{ api_description }}.
 *
 * API Documentation: {{ api_documentation_url }}
 */

package {{ config.project.package_name }}.api;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;
import java.util.Optional;

{% if config.project.type == 'data-platform' %}
import {{ config.project.package_name }}.base.BaseAPIClient;
import {{ config.project.package_name }}.models.Record;
{% endif %}

public class {{ api_class_name }} {% if config.project.type == 'data-platform' %}extends BaseAPIClient {% endif %}{

    private static final String SOURCE_NAME = "{{ api_name }}";
    private static final String BASE_URL = "{{ api_base_url }}";
    private static final int RATE_LIMIT_CALLS = {{ recommended_rate_limit_calls }};
    private static final int RATE_LIMIT_PERIOD = {{ recommended_rate_limit_period }};

    {% if auth_method != 'none' %}private final String apiKey;{% endif %}
    private final String baseUrl;
    private final HttpClient httpClient;

    public {{ api_class_name }}({% if auth_method != 'none' %}String apiKey{% endif %}) {
        this({% if auth_method != 'none' %}apiKey, {% endif %}BASE_URL);
    }

    public {{ api_class_name }}({% if auth_method != 'none' %}String apiKey, {% endif %}String baseUrl) {
        {% if config.project.type == 'data-platform' %}
        super(SOURCE_NAME, RATE_LIMIT_CALLS, RATE_LIMIT_PERIOD);
        {% endif %}
        {% if auth_method != 'none' %}
        if (apiKey == null || apiKey.isEmpty()) {
            throw new IllegalArgumentException("API key is required");
        }
        this.apiKey = apiKey;
        {% endif %}
        this.baseUrl = baseUrl;
        this.httpClient = HttpClient.newHttpClient();
    }

    private Map<String, String> prepareHeaders() {
        Map<String, String> headers = new HashMap<>();
        headers.put("Content-Type", "{{ content_type }}");
        {% if auth_method == 'api_key' %}
        headers.put("{{ auth_header_name }}", "{{ auth_header_format.replace('your_key_here', '" + apiKey + "') }}");
        {% elif auth_method == 'bearer' %}
        headers.put("Authorization", "Bearer " + apiKey);
        {% endif %}
        return headers;
    }

    public {{ primary_method_return_type }} {{ primary_method_name }}({{ primary_method_params }}) {
        // Implementation
    }
}
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
// {{ api_name }} API Client
//
// This package provides a client for accessing {{ api_description }}.
//
// API Documentation: {{ api_documentation_url }}

package api

import (
    "fmt"
    "net/http"
    "time"
)

const (
    SourceName      = "{{ api_name }}"
    BaseURL         = "{{ api_base_url }}"
    RateLimitCalls  = {{ recommended_rate_limit_calls }}
    RateLimitPeriod = {{ recommended_rate_limit_period }}
)

type {{ api_class_name }} struct {
    {% if auth_method != 'none' %}apiKey    string{% endif %}
    baseURL   string
    client    *http.Client
}

func New{{ api_class_name }}({% if auth_method != 'none' %}apiKey string{% endif %}) *{{ api_class_name }} {
    {% if auth_method != 'none' %}
    if apiKey == "" {
        panic("API key is required")
    }
    {% endif %}
    return &{{ api_class_name }}{
        {% if auth_method != 'none' %}apiKey:  apiKey,{% endif %}
        baseURL: BaseURL,
        client:  &http.Client{Timeout: 30 * time.Second},
    }
}

func (c *{{ api_class_name }}) prepareHeaders() map[string]string {
    headers := map[string]string{
        "Content-Type": "{{ content_type }}",
    }
    {% if auth_method == 'api_key' %}
    headers["{{ auth_header_name }}"] = fmt.Sprintf("{{ auth_header_format }}", c.apiKey)
    {% elif auth_method == 'bearer' %}
    headers["Authorization"] = fmt.Sprintf("Bearer %s", c.apiKey)
    {% endif %}
    return headers
}

func (c *{{ api_class_name }}) {{ primary_method_name }}({{ primary_method_params }}) ({{ primary_method_return_type }}, error) {
    // Implementation
}
```
{% endif %}

### Testing Requirements

**Test Coverage Target:** {{ test_coverage_target }}%

**Required Tests:**
1. Initialization (with/without API key, custom base URL)
{% if auth_method != 'none' %}
2. API key handling (required/optional, error when missing)
{% endif %}
3. Each public method (success case)
4. Each public method (error cases: 400, 401, 404, 429, 500)
5. Parameter validation (required params, type checking, range validation)
6. Rate limiting (verify it works correctly)
{% if auth_method == 'oauth2' %}
7. Authentication (header format, token refresh)
{% endif %}
8. Response parsing (valid response, invalid response)
{% if config.project.type == 'data-platform' %}
9. Record creation (all fields populated correctly)
{% endif %}

**Mock Strategy:**
- Mock all external API calls
- Create realistic mock responses based on actual API docs
- Test both success and failure scenarios

---

## Example Usage

### Basic Usage

{% if config.technology_stack.backend.language == 'python' %}
```python
from {{ config.project.name }}.{{ api_name }}_api import {{ api_class_name }}
import os

# Initialize client
client = {{ api_class_name }}(
    {% if auth_method != 'none' %}api_key=os.getenv("{{ api_name|upper }}_API_KEY"){% endif %}
)

# Fetch data
result = client.{{ primary_method_name }}(
    {{ example_method_call }}
)

# Parse response
{% if response_format == 'json' %}
import json
data = json.loads(result)
print(data)
{% else %}
print(result)
{% endif %}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
import { {{ api_class_name }} } from './{{ api_name }}-api';

// Initialize client
const client = new {{ api_class_name }}({
    {% if auth_method != 'none' %}apiKey: process.env.{{ api_name|upper }}_API_KEY{% endif %}
});

// Fetch data
const result = await client.{{ primary_method_name }}(
    {{ example_method_call }}
);

console.log(result);
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
import {{ config.project.package_name }}.api.{{ api_class_name }};

// Initialize client
{{ api_class_name }} client = new {{ api_class_name }}(
    {% if auth_method != 'none' %}System.getenv("{{ api_name|upper }}_API_KEY"){% endif %}
);

// Fetch data
{{ primary_method_return_type }} result = client.{{ primary_method_name }}(
    {{ example_method_call }}
);

System.out.println(result);
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
import (
    "{{ config.project.module }}/api"
    "os"
)

// Initialize client
client := api.New{{ api_class_name }}(
    {% if auth_method != 'none' %}os.Getenv("{{ api_name|upper }}_API_KEY"){% endif %}
)

// Fetch data
result, err := client.{{ primary_method_name }}(
    {{ example_method_call }}
)
if err != nil {
    panic(err)
}

fmt.Println(result)
```
{% endif %}

{% if config.project.type == 'data-platform' %}
### Data Pipeline Integration

{{ data_pipeline_integration_example }}
{% endif %}

---

## Implementation Checklist

**{{ config.roles.api_engineer or 'API Engineer' }} should verify:**

- [ ] Spec is complete and unambiguous
- [ ] All endpoints documented with examples
- [ ] Authentication method clearly specified
- [ ] Rate limits defined with rationale
{% if config.project.type == 'data-platform' %}
- [ ] Caching strategy makes sense for data type
{% endif %}
- [ ] Error handling covers all scenarios
- [ ] Data structures documented with types
- [ ] Class skeleton provides clear starting point
- [ ] Example usage shows realistic scenarios
- [ ] No questions remain - can implement without clarification

**If anything is unclear, ask {{ config.roles.api_architect or 'API Architect' }} for clarification before starting implementation.**

---

## Additional Notes

**Known Limitations:**
{{ known_limitations }}

**Performance Considerations:**
{{ performance_considerations }}

**Dependencies:**
{{ dependencies }}

**Testing Challenges:**
{{ testing_challenges }}

**Future Enhancements:**
{{ future_enhancements }}

---

**Handoff Status:** ✅ COMPLETE

**Next Step:** {{ config.roles.api_engineer or 'API Engineer' }} should read this spec and implement the client following all specifications.
