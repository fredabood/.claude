# Documentation Research & Preprocessing Workflow

**Purpose:** Research and summarize verbose documentation to prevent context window waste
**Duration:** 1-2 days
**Complexity:** Low-Medium
**Agent:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }}{% else %}Researcher{% endif %}

---

## 📋 Workflow Overview

This workflow pre-processes verbose documentation (>100KB) into concise summaries (<20KB), code templates, and indexed references. It prevents agents from wasting context on redundant documentation and creates reusable research artifacts for future work.

**Key Benefits:**
- **Context Efficiency:** 80-95% size reduction (100KB → 5-20KB)
- **Faster Development:** Agents get actionable summaries instantly
- **Reusability:** Research artifacts cached for future sprints
- **Consistency:** Standardized patterns across team
- **Quality:** Focus on key information, remove redundancy

**Use Cases:**
- {% if config.project.type == 'api' %}New API integration (research vendor documentation){% elif config.project.type == 'data-platform' %}New data source integration (research API docs){% elif config.project.type == 'ml' %}New ML library/framework (research model APIs){% else %}New library/service integration{% endif %}
- {% if config.cloud_provider %}New {{ config.cloud_provider }} service{% else %}New cloud service{% endif %} adoption
- {% if config.iac_tool %}{{ config.iac_tool }}{% else %}Infrastructure-as-code{% endif %} research
- {% if config.project.type == 'ml' and config.ml_platform %}{{ config.ml_platform.experiment_tracking or 'ML platform' }}{% endif %} feature research
- Multi-agent needs same documentation
- New {% if config.technology_stack %}{{ config.technology_stack.backend.language }}{% else %}programming language{% endif %} framework

---

## 🔄 Workflow Steps

### Step 1: Identify Documentation Need (0.1 days)

**Agent:** Any Agent (requesting research)
**Duration:** 15-30 minutes

**Trigger Conditions:**
- Documentation >100KB needs to be consulted
- Multiple agents will need the same external documentation
- {% if config.project.type == 'api' %}New API integration planned{% elif config.project.type == 'data-platform' %}New data source integration{% elif config.project.type == 'ml' %}New ML library/framework{% else %}New technology adoption{% endif %}
- Recurring documentation needs (worth caching)

**Activities:**
1. Identify verbose documentation source (URL, PDF, multi-page docs)
2. Estimate documentation size (check page count, file size)
3. Determine what information is needed (authentication, endpoints, examples, etc.)
4. Create research request

**Output:**
- Research request specifying documentation source and information needed

**Example Request:**
```markdown
## Research Request

**Documentation:** {% if config.project.type == 'api' %}[API Name] REST API Documentation{% elif config.project.type == 'data-platform' %}[Data Source] API Documentation{% elif config.project.type == 'ml' %}[ML Library] Model API Documentation{% else %}[Technology] Documentation{% endif %}
**Source:** https://docs.example.com/api/v1/
**Size:** ~150KB (200+ pages)

**Needed Information:**
{% if config.project.type == 'api' %}- Authentication methods (API key, OAuth, JWT)
- Core endpoints (CRUD operations)
- Rate limiting rules
- Request/response examples
- Error codes
{% elif config.project.type == 'data-platform' %}- API authentication
- Data endpoints
- Pagination patterns
- Rate limiting
- Response formats
{% elif config.project.type == 'ml' %}- Model initialization
- Training API
- Inference API
- Parameter tuning
- Example code
{% else %}- Authentication/setup
- Key APIs/functions
- Configuration options
- Code examples
- Best practices
{% endif %}
**Target Output:** <20KB summary with code templates
```

---

### Step 2: Fetch & Analyze Documentation (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }}{% else %}Researcher{% endif %}
**Duration:** 4 hours

**Activities:**

**2.1: Fetch Documentation**
- Use WebFetch tool for online documentation
- Read PDF/markdown files for local documentation
- Navigate multi-page documentation systematically
- Download code examples and schemas

**2.2: Analyze Structure**
- Identify documentation organization (sections, chapters, topics)
- Locate key information sections
- Find code examples and templates
- Identify redundancy (repeated content, verbose explanations)
- Note {% if config.project.type == 'api' %}API versioning{% elif config.project.type == 'ml' %}model versions{% else %}version-specific{% endif %} information

**2.3: Extract Key Patterns**
{% if config.project.type == 'api' %}- Authentication patterns ({% if config.security and config.security.authentication %}{{ config.security.authentication.method or 'API key, OAuth, JWT' }}{% else %}API key, OAuth, JWT{% endif %})
- Endpoint patterns (REST, GraphQL, RPC)
- Request/response formats (JSON, XML, Protocol Buffers)
- Error handling patterns
- Rate limiting strategies
{% elif config.project.type == 'data-platform' %}- Data API patterns
- Authentication methods
- Pagination strategies
- Data formats (JSON, CSV, Parquet)
- Caching recommendations
{% elif config.project.type == 'ml' %}- Model API patterns
- Training parameters
- Inference methods
- Optimization techniques
- Framework-specific patterns
{% else %}- API/library patterns
- Configuration patterns
- Usage examples
- Best practices
- Common pitfalls
{% endif %}

**2.4: Identify Compression Opportunities**
- Remove marketing fluff and repetition
- Consolidate similar examples
- Extract reusable code templates
- Focus on actionable information

**Output:**
- Annotated documentation outline
- Key patterns identified
- Compression strategy notes

---

### Step 3: Create Summary & Templates (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }}{% else %}Researcher{% endif %}
**Duration:** 4 hours

**Activities:**

**3.1: Create Research Summary Document**

Use standardized template structure:

```markdown
# {% if config.project.type == 'api' %}[API Name]{% elif config.project.type == 'data-platform' %}[Data Source]{% elif config.project.type == 'ml' %}[ML Library]{% else %}[Technology]{% endif %} Research Summary

**Source:** [URL or document path]
**Original Size:** [NNN]KB
**Summary Size:** [NN]KB (XX% reduction)
**Researched:** {{ "now"|date("%Y-%m-%d") }}
**Researcher:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }}{% else %}Researcher{% endif %}

---

## Quick Reference

{% if config.project.type == 'api' %}**Base URL:** https://api.example.com/v1
**Authentication:** API Key in header (X-API-Key)
**Rate Limit:** 1000 requests/hour
**Response Format:** JSON{% elif config.project.type == 'data-platform' %}**API Endpoint:** https://data.example.com/api/v1
**Authentication:** OAuth 2.0
**Data Format:** JSON
**Pagination:** Cursor-based{% elif config.project.type == 'ml' %}**Library:** {{ config.technology_stack.backend.language or 'python' }} package
**Installation:** pip install example-ml
**Model Types:** Classification, Regression
**Framework:** {% if config.ml_platform %}{{ config.ml_platform.framework or 'PyTorch/TensorFlow' }}{% else %}PyTorch/TensorFlow{% endif %}{% else %}**Setup:** [installation command]
**Configuration:** [config file location]
**Key Concepts:** [main concepts]{% endif %}

---

## {% if config.project.type == 'api' %}Authentication{% elif config.project.type == 'ml' %}Installation & Setup{% else %}Getting Started{% endif %}

[Concise authentication/setup instructions with code example]

---

## {% if config.project.type == 'api' %}Core Endpoints{% elif config.project.type == 'data-platform' %}Data Endpoints{% elif config.project.type == 'ml' %}Key APIs{% else %}Main Features{% endif %}

### {% if config.project.type == 'api' %}GET /resource{% elif config.project.type == 'data-platform' %}GET /data{% elif config.project.type == 'ml' %}model.fit(){% else %}Feature 1{% endif %}
**Purpose:** [Brief description]
**Parameters:** [Key parameters only]
**Response:** [Response format]
**Example:** [Minimal working code]

[Repeat for other key endpoints/APIs]

---

## Code Templates

### {% if config.project.type == 'api' %}Basic Request Template{% elif config.project.type == 'data-platform' %}Data Fetching Template{% elif config.project.type == 'ml' %}Training Template{% else %}Usage Template{% endif %}

{% if config.technology_stack.backend.language == 'python' %}```python
{% if config.project.type == 'api' %}import requests

headers = {'X-API-Key': 'your-api-key'}
response = requests.get('https://api.example.com/v1/resource', headers=headers)
data = response.json()
{% elif config.project.type == 'ml' %}from example_ml import Model

model = Model()
model.fit(X_train, y_train)
predictions = model.predict(X_test)
{% else %}# Usage template
import library

client = library.Client(api_key='...')
result = client.method()
{% endif %}```{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
{% if config.project.type == 'api' %}import axios from 'axios';

const response = await axios.get('https://api.example.com/v1/resource', {
    headers: { 'X-API-Key': 'your-api-key' }
});
const data = response.data;
{% else %}// Usage template
import { Client } from 'library';

const client = new Client({ apiKey: '...' });
const result = await client.method();
{% endif %}```{% elif config.technology_stack.backend.language == 'java' %}```java
{% if config.project.type == 'api' %}HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/v1/resource"))
    .header("X-API-Key", "your-api-key")
    .build();

HttpResponse<String> response = client.send(request,
    HttpResponse.BodyHandlers.ofString());
{% else %}// Usage template
Client client = new Client("api-key");
Result result = client.method();
{% endif %}```{% else %}```
# Usage template
[code example]
```{% endif %}

---

## {% if config.project.type == 'api' %}Rate Limiting & Best Practices{% elif config.project.type == 'ml' %}Best Practices{% else %}Important Notes{% endif %}

- [Key consideration 1]
- [Key consideration 2]
- [Common pitfall to avoid]

---

## {% if config.project.type == 'api' %}Error Codes{% else %}Error Handling{% endif %}

[Concise error reference with handling recommendations]

---

## Additional Resources

- **Full Documentation:** [URL]
- **Code Examples:** [GitHub repo or docs section]
- **{% if config.project.type == 'api' %}API Reference{% elif config.project.type == 'ml' %}Model API{% else %}API Reference{% endif %}:** [URL]
```

**3.2: Create Code Templates**

Extract reusable code templates in `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}{% else %}docs{% endif %}/research/templates/`:

{% if config.project.type == 'api' %}- `authentication-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Authentication boilerplate
- `request-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - API request pattern
- `error-handling-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Error handling
- `pagination-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Pagination logic
{% elif config.project.type == 'data-platform' %}- `data-fetcher-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Data fetching pattern
- `authentication-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - API authentication
- `caching-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Caching strategy
- `transformation-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Data transformation
{% elif config.project.type == 'ml' %}- `training-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Model training pattern
- `inference-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Inference pattern
- `preprocessing-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript' %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Data preprocessing
- `evaluation-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Model evaluation
{% else %}- `setup-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Setup and configuration
- `usage-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Basic usage pattern
- `error-handling-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}` - Error handling
{% endif %}

**3.3: Compression Targets**

| Documentation Type | Target Reduction | What to Keep |
|--------------------|------------------|--------------|
| {% if config.project.type == 'api' %}API Documentation{% elif config.project.type == 'data-platform' %}Data API Docs{% elif config.project.type == 'ml' %}ML Library Docs{% else %}Library Docs{% endif %} | 85-90% | Auth, endpoints/APIs, examples, errors |
| {% if config.cloud_provider %}{{ config.cloud_provider }}{% else %}Cloud Platform{% endif %} Docs | 80-85% | Setup, patterns, gotchas, code |
| {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC Tool{% endif %} Docs | 90-95% | Resource types, key arguments, examples |
| {% if config.project.type == 'ml' %}ML Framework{% else %}Framework{% endif %} Docs | 85-95% | Key {% if config.project.type == 'ml' %}model APIs{% else %}functions{% endif %}, config, examples |

**Output:**
- Research summary document (<20KB)
- Code templates (reusable {% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% else %}code{% endif %} files)
- Quick reference guide

---

### Step 4: Update Master Index (0.2 days)

**Agent:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }}{% else %}Researcher{% endif %}
**Duration:** 1.5 hours

**Activities:**
1. Open `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}{% else %}docs{% endif %}/research/RESEARCH_INDEX.md` (create if doesn't exist)
2. Add entry for new research summary
3. Organize by category ({% if config.project.type == 'api' %}APIs, Authentication, Services{% elif config.project.type == 'data-platform' %}Data Sources, APIs, Pipelines{% elif config.project.type == 'ml' %}ML Libraries, Frameworks, Models{% else %}Libraries, Frameworks, Services{% endif %})
4. Include keywords for searchability

**Index Entry Template:**
```markdown
### {% if config.project.type == 'api' %}[API Name]{% elif config.project.type == 'data-platform' %}[Data Source]{% elif config.project.type == 'ml' %}[ML Library]{% else %}[Technology]{% endif %} ({{ "now"|date("%Y-%m-%d") }})
- **Summary:** `docs/research/[name]-summary.md`
- **Templates:** `docs/research/templates/[name]-*{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}`
- **Original Docs:** [URL]
- **Compression:** XX% (XXXKB → XXKB)
- **Keywords:** {% if config.project.type == 'api' %}[authentication, REST, rate-limiting]{% elif config.project.type == 'data-platform' %}[data-api, pagination, caching]{% elif config.project.type == 'ml' %}[training, inference, model-api]{% else %}[keywords]{% endif %}
- **Use Case:** {% if config.project.type == 'api' %}API integration for [feature]{% elif config.project.type == 'data-platform' %}Data source integration{% elif config.project.type == 'ml' %}ML model development{% else %}[use case]{% endif %}
```

**Output:**
- Updated RESEARCH_INDEX.md
- Searchable research catalog

---

### Step 5: Deliver to Requesting Agent (0.1 days)

**Agent:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }} → Requesting Agent{% else %}Researcher → Requesting Agent{% endif %}
**Duration:** 30 minutes

**Handoff Package:**
1. Research summary document
2. Code templates
3. Link to RESEARCH_INDEX.md entry
4. Quick start instructions

**Handoff Template:**
```markdown
# Research Handoff: {% if config.project.type == 'api' %}[API Name]{% elif config.project.type == 'data-platform' %}[Data Source]{% elif config.project.type == 'ml' %}[ML Library]{% else %}[Technology]{% endif %}

## Research Summary
- **Location:** `docs/research/[name]-summary.md`
- **Size:** [NN]KB (XX% compression from [NNN]KB original)
- **Researched:** {{ "now"|date("%Y-%m-%d") }}

## Quick Start
[2-3 sentence summary of how to get started]

## Code Templates
- `docs/research/templates/[name]-auth-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}`
- `docs/research/templates/[name]-request-template{% if config.technology_stack.backend.language == 'python' %}.py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}{% elif config.technology_stack.backend.language == 'java' %}.java{% endif %}`

## Key Patterns
{% if config.project.type == 'api' %}- Authentication: [method]
- Base URL: [URL]
- Rate Limit: [limit]
- Response Format: [format]
{% elif config.project.type == 'ml' %}- Model API: [primary API]
- Training: [key method]
- Inference: [key method]
- Framework: [framework]
{% else %}- Setup: [key steps]
- Usage: [primary API]
- Configuration: [config file]
{% endif %}

## Next Steps for [Requesting Agent]
1. Read research summary
2. Copy relevant code templates
3. Adapt templates to {% if config.project.name %}{{ config.project.name }}{% else %}project{% endif %} patterns
4. Refer to original docs only for edge cases
```

**Output:**
- Concise handoff package delivered to requesting agent
- Agent can proceed without reading 100KB+ docs

---

### Step 6: Commit Research Artifacts (0.2 days)

**Agent:** {% if config.agents %}{{ config.agents.git_committer or 'Git Committer' }}{% else %}Git Committer{% endif %}
**Duration:** 1.5 hours

**Activities:**
1. Review research summary and templates
2. Stage research files
3. Update RESEARCH_INDEX.md
4. Create commit message
5. Push to repository

**Commit Message Template:**
```
docs: Add research summary for {% if config.project.type == 'api' %}[API Name] API{% elif config.project.type == 'data-platform' %}[Data Source]{% elif config.project.type == 'ml' %}[ML Library]{% else %}[Technology]{% endif %}

Researched and summarized {% if config.project.type == 'api' %}[API Name] API documentation{% elif config.project.type == 'data-platform' %}[Data Source] API documentation{% elif config.project.type == 'ml' %}[ML Library] documentation{% else %}[Technology] documentation{% endif %} for {% if config.project.type == 'api' %}API integration{% elif config.project.type == 'data-platform' %}data source integration{% elif config.project.type == 'ml' %}ML model development{% else %}feature implementation{% endif %}.

**Compression:** XX% reduction (XXXKB → XXKB)

**Deliverables:**
- Research summary with {% if config.project.type == 'api' %}authentication, endpoints, examples{% elif config.project.type == 'data-platform' %}API patterns, data formats{% elif config.project.type == 'ml' %}model APIs, training patterns{% else %}key patterns and examples{% endif %}
- Code templates for {% if config.project.type == 'api' %}authentication, requests, error handling{% elif config.project.type == 'ml' %}training, inference{% else %}common operations{% endif %}
- Updated research index

**Use Case:** {% if config.project.type == 'api' %}API client implementation for [feature]{% elif config.project.type == 'data-platform' %}Data source integration for [pipeline]{% elif config.project.type == 'ml' %}Model development for [use case]{% else %}[Feature] implementation{% endif %}
```

**Output:**
- Research artifacts committed to repository
- Reusable for future work

---

## ✅ Success Criteria

Research is successful when:

1. ✅ **Size Reduction:** 80-95% compression achieved
2. ✅ **Completeness:** All key information preserved
3. ✅ **Actionable:** Code templates work out-of-box
4. ✅ **Searchable:** Indexed in RESEARCH_INDEX.md
5. ✅ **Reusable:** Can be used by multiple agents/sprints
6. ✅ **Accurate:** No missing critical information
7. ✅ **Timely:** Delivered within 1-2 days

---

## 🔗 Related Workflows

**Upstream (Triggers This Workflow):**
- **{% if config.project.type == 'api' %}Single API Client{% elif config.project.type == 'data-platform' %}Single Feature Development{% elif config.project.type == 'ml' %}ML Model Development{% else %}Single Feature Development{% endif %}** - May need research before implementation
- **Sprint Planning** - May identify research needs

**Downstream (This Workflow Enables):**
- **{% if config.project.type == 'api' %}API Implementation{% elif config.project.type == 'data-platform' %}Data Source Integration{% elif config.project.type == 'ml' %}Model Development{% else %}Feature Implementation{% endif %}** - Uses research artifacts
- **Documentation** - Research summaries become project docs

**Parallel Workflows:**
- Can run in parallel with other non-dependent work
- Results delivered when needed by implementation agents

---

## 💡 Typical Compression Examples

### {% if config.project.type == 'api' %}REST API Documentation{% elif config.project.type == 'data-platform' %}Data API Documentation{% elif config.project.type == 'ml' %}ML Library Documentation{% else %}Library Documentation{% endif %}
- **Original:** 150KB (200+ pages)
- **Summary:** 15KB (10-12 pages)
- **Compression:** 90%
- **Kept:** Auth, {% if config.project.type == 'api' %}core endpoints{% elif config.project.type == 'data-platform' %}data endpoints{% elif config.project.type == 'ml' %}key APIs{% else %}main functions{% endif %}, examples, errors
- **Removed:** Marketing, verbose explanations, redundant examples

### {% if config.cloud_provider %}{{ config.cloud_provider }}{% else %}Cloud Platform{% endif %} Service Documentation
- **Original:** 200KB (300+ pages)
- **Summary:** 30KB (15-20 pages)
- **Compression:** 85%
- **Kept:** Setup, resource types, configuration, gotchas
- **Removed:** Tutorials, case studies, verbose intros

### {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC Tool{% endif %} Provider Documentation
- **Original:** 100KB (150+ pages)
- **Summary:** 8KB (5-7 pages)
- **Compression:** 92%
- **Kept:** Resource types, required args, examples
- **Removed:** Full argument lists (link to docs), marketing

---

## 📝 Best Practices

1. **Focus on Actionable Info:** Code over concepts
2. **Preserve Examples:** Working code is most valuable
3. **Extract Patterns:** Identify reusable templates
4. **Index Everything:** Make research searchable
5. **Update Index:** Keep RESEARCH_INDEX.md current
6. **Version Awareness:** Note {% if config.project.type == 'api' %}API{% elif config.project.type == 'ml' %}library{% else %}documentation{% endif %} version researched
7. **Link to Original:** Always include link to full docs

---

**Workflow Version:** 1.0
**Created:** {{ "now"|date("%Y-%m-%d") }}
**Maintained By:** {% if config.team %}{{ config.team.name }}{% else %}Project Team{% endif %}
**Framework:** Vibey Agent Framework
