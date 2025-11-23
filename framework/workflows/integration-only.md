---
id: integration-only
name: Integration Only
type: development
version: 1.0.0
duration: 30 minutes - 2 hours per component
complexity: low
steps:
- order: 1
  name: Gather Component Metadata
  agent: integration-engineer-(with-developer-input)
  duration: 5-10 minutes
- order: 2
  name: Register/Connect Component
  agent: integration-engineer
  duration: 15-30 minutes
- order: 3
  name: Create Integration Test
  agent: integration-engineer
  duration: 15-30 minutes
- order: 4
  name: Manual Verification
  agent: integration-engineer
  duration: 10-15 minutes
- order: 5
  name: Create Integration Handoff Document
  agent: integration-engineer
  duration: 10-15 minutes
inputs:
- name: feature_name
  type: string
  required: true
  description: Name of the feature or task
- name: requirements
  type: string
  required: true
  description: Requirements and acceptance criteria
- name: project_type
  type: string
  required: false
  default: web-app
  description: Project type (web-app, api, ml, data-platform)
description: Integrate completed and tested components into the main system
---

# Workflow: Integration Only

**Workflow ID:** Integration Only
**Purpose:** Integrate completed and tested components into the main system
**Duration:** 30 minutes - 2 hours per component
**Complexity:** Low

---

## Overview

This workflow integrates already-implemented and tested components into the main application. Use this when you have finished developing a component separately and now need to connect it to the rest of the system.

**Use Cases:**
{% if config.project.type == 'web-app' %}- Integrating completed UI components into the application
- Adding new routes to the router
- Connecting components to state management{% elif config.project.type == 'api' %}- Integrating new API endpoints into the main router
- Adding new services to dependency injection
- Connecting new middleware{% elif config.project.type == 'data-platform' %}- Integrating new data sources into main data interface
- Adding ETL pipelines to orchestration
- Registering new data transformations{% elif config.project.type == 'ml' %}- Integrating new models into model registry
- Adding new feature pipelines
- Connecting inference endpoints{% else %}- Integrating completed modules
- Connecting new services
- Adding new functionality to main application{% endif %}

**Prerequisites:**
{% if config.project.type == 'web-app' %}- ✅ Component implemented and tested
- ✅ Component tests passing{% elif config.project.type == 'api' %}- ✅ API endpoint/service implemented
- ✅ Unit tests passing{% elif config.project.type == 'data-platform' %}- ✅ Data source/pipeline implemented
- ✅ Tests passing{% elif config.project.type == 'ml' %}- ✅ Model/pipeline implemented
- ✅ Tests passing{% else %}- ✅ Component implemented
- ✅ Tests passing{% endif %}
- ✅ Test coverage ≥ {{ config.test_coverage_target or '85' }}%
- ✅ Security review passed (if required)

---

## Workflow Steps

### Step 1: Gather Component Metadata

**Duration:** 5-10 minutes
**Agent:** Integration Engineer (with developer input)

**Information Needed:**
{% if config.project.type == 'web-app' %}- Component name and location
- Route path (if applicable)
- Props/API requirements
- State management needs
- Dependencies{% elif config.project.type == 'api' %}- Endpoint path and HTTP methods
- Request/response schemas
- Authentication requirements
- Dependencies (database, external services)
- Rate limiting needs{% elif config.project.type == 'data-platform' %}- Data source/pipeline name
- Data schema
- Update frequency (real-time, batch, scheduled)
- Dependencies (other data sources)
- Storage location{% elif config.project.type == 'ml' %}- Model name and version
- Input/output schema
- Inference type (batch, real-time)
- Dependencies (features, preprocessing)
- Resource requirements (CPU, GPU, memory){% else %}- Component name
- Interface/API
- Dependencies
- Configuration requirements{% endif %}

**How to Find:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# Look for key information in the implementation
grep -r "class\|def\|CONFIG" src/{% if config.project.type == 'data-platform' %}data_sources{% elif config.project.type == 'ml' %}models{% else %}components{% endif %}/[component_name]*
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# Look for exports and configurations
grep -r "export\|interface\|const" src/{% if config.project.type == 'web-app' %}components{% elif config.project.type == 'api' %}routes{% else %}modules{% endif %}/[ComponentName]*
```{% else %}```bash
# Search for component definition
find src/ -name "*[component_name]*"
```{% endif %}

**Deliverables:**
- Component metadata document
- Integration requirements checklist

---

### Step 2: Register/Connect Component

**Duration:** 15-30 minutes
**Agent:** Integration Engineer

**Activities:**

{% if config.project.type == 'web-app' %}**Web Application Integration:**

{% if config.web_framework and config.web_framework.frontend == 'react' %}**React Integration:**
```typescript
// 1. Add route to router
// src/routes/index.tsx
import { NewComponent } from '@/components/NewComponent';

export const routes = [
  // ... existing routes
  {
    path: '/new-feature',
    element: <NewComponent />,
  },
];

// 2. Add to navigation (if applicable)
// src/components/Navigation.tsx
<NavLink to="/new-feature">New Feature</NavLink>

// 3. Connect to state management (if needed)
// src/store/index.ts
import { newFeatureSlice } from './newFeatureSlice';

export const store = configureStore({
  reducer: {
    // ... existing reducers
    newFeature: newFeatureSlice.reducer,
  },
});
```{% elif config.web_framework and config.web_framework.frontend == 'vue' %}**Vue Integration:**
```typescript
// 1. Add route to router
// src/router/index.ts
import NewComponent from '@/components/NewComponent.vue';

const routes = [
  // ... existing routes
  {
    path: '/new-feature',
    name: 'NewFeature',
    component: NewComponent,
  },
];

// 2. Add to navigation (if applicable)
// src/components/Navigation.vue
<router-link to="/new-feature">New Feature</router-link>

// 3. Connect to state management (if needed)
// src/store/index.ts
import { newFeatureModule } from './modules/newFeature';

export default createStore({
  modules: {
    // ... existing modules
    newFeature: newFeatureModule,
  },
});
```{% endif %}{% elif config.project.type == 'api' %}**API Integration:**

{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}**Python/FastAPI Integration:**
```python
# 1. Register router
# src/main.py
from src.routes.new_feature import router as new_feature_router

app.include_router(new_feature_router, prefix="/api/new-feature", tags=["new-feature"])

# 2. Add to dependency injection (if applicable)
# src/dependencies.py
def get_new_feature_service():
    return NewFeatureService()

# 3. Update OpenAPI documentation
# The router registration above automatically updates OpenAPI
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}**Node.js/Express Integration:**
```typescript
// 1. Register router
// src/app.ts
import { newFeatureRouter } from './routes/newFeature';

app.use('/api/new-feature', newFeatureRouter);

// 2. Add middleware (if needed)
// src/middleware/index.ts
import { newFeatureMiddleware } from './newFeatureMiddleware';

app.use(newFeatureMiddleware);

// 3. Update API documentation (if using Swagger)
// Add route documentation to swagger.yaml or JSDoc comments
```{% endif %}{% elif config.project.type == 'data-platform' %}**Data Platform Integration:**

```{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}python{% else %}text{% endif %}
# 1. Register data source
# src/core/data_registry.py
DATA_SOURCES = {
    # ... existing sources
    "new_source": {
        "name": "New Data Source",
        "implementation": "src.data_sources.new_source",
        "update_frequency": "DAILY",  # or STATIC, HOURLY, WEEKLY, etc.
        "schema": "path/to/schema.json",
    },
}

# 2. Add to main data interface
# src/core/data_fetcher.py
def fetch_new_source_data(self, **params):
    """Fetch data from new source."""
    source = self.sources.get("new_source")
    return source.fetch(params)

# 3. Add to orchestration (if batch pipeline)
{% if config.orchestration %}# {{ config.orchestration }} configuration
# Add task/DAG for new source{% endif %}
```{% elif config.project.type == 'ml' %}**ML Integration:**

```{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}python{% else %}text{% endif %}
# 1. Register model
{% if config.ml_platform and config.ml_platform.model_registry == 'mlflow' %}# MLflow model registration
import mlflow

mlflow.register_model(
    model_uri="runs:/{run_id}/model",
    name="new_model"
)

# Transition to production
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name="new_model",
    version=1,
    stage="Production"
){% elif config.ml_platform and config.ml_platform.model_registry %}# {{ config.ml_platform.model_registry }} registration
# Register model according to platform docs{% else %}# Register model in model registry{% endif %}

# 2. Add inference endpoint
# src/api/inference.py
@app.post("/predict/new-model")
async def predict_new_model(data: InputSchema):
    model = load_model("new_model")
    predictions = model.predict(data)
    return {"predictions": predictions}

# 3. Add to model serving configuration
# Update serving configuration to include new model
```{% else %}**Component Integration:**

```
# 1. Register component in main application
# 2. Add to dependency injection (if applicable)
# 3. Update configuration
# 4. Connect to other services
```{% endif %}

**Deliverables:**
{% if config.project.type == 'web-app' %}- Updated router configuration
- Updated navigation (if applicable)
- State management connection (if applicable){% elif config.project.type == 'api' %}- Updated API router
- Registered middleware (if applicable)
- Updated API documentation{% elif config.project.type == 'data-platform' %}- Updated data registry
- Updated data interface
- Orchestration configuration (if applicable){% elif config.project.type == 'ml' %}- Registered model
- Inference endpoint configured
- Serving configuration updated{% else %}- Component registered
- Configuration updated{% endif %}

---

### Step 3: Create Integration Test

**Duration:** 15-30 minutes
**Agent:** Integration Engineer

**Create End-to-End Integration Test:**

{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```python
# tests/integration/test_new_component_integration.py
import pytest
{% if config.project.type == 'web-app' %}from selenium import webdriver{% elif config.project.type == 'api' %}from fastapi.testclient import TestClient
from src.main import app{% elif config.project.type == 'data-platform' %}from src.core.data_fetcher import DataFetcher{% elif config.project.type == 'ml' %}from src.api.inference import app{% endif %}

def test_new_component_integration():
    """Test that new component integrates correctly with main system."""
    {% if config.project.type == 'web-app' %}# Test UI integration
    driver = webdriver.Chrome()
    driver.get("http://localhost:3000/new-feature")
    assert "Expected Content" in driver.page_source
    driver.quit(){% elif config.project.type == 'api' %}# Test API integration
    client = TestClient(app)
    response = client.post("/api/new-feature", json={"test": "data"})
    assert response.status_code == 200
    assert "expected_field" in response.json(){% elif config.project.type == 'data-platform' %}# Test data source integration
    fetcher = DataFetcher()
    result = fetcher.fetch_new_source_data(param="value")
    assert result["status"] == "success"
    assert "data" in result{% elif config.project.type == 'ml' %}# Test model inference integration
    client = TestClient(app)
    response = client.post("/predict/new-model", json={"features": [1, 2, 3]})
    assert response.status_code == 200
    assert "predictions" in response.json(){% else %}# Test component integration
    # Add appropriate integration test{% endif %}

def test_component_accessible():
    """Verify component is accessible through main application."""
    {% if config.project.type == 'web-app' %}# Test route exists
    # Test component renders{% elif config.project.type == 'api' %}# Test endpoint is registered
    # Test endpoint returns expected response{% elif config.project.type == 'data-platform' %}# Test data source is registered
    # Test data can be fetched{% elif config.project.type == 'ml' %}# Test model is loadable
    # Test inference works{% else %}# Test component is accessible{% endif %}
    pass
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```typescript
// tests/integration/newComponent.integration.test.ts
import { describe, it, expect } from {% if config.test_framework == 'jest' %}'@jest/globals'{% else %}'vitest'{% endif %};
{% if config.project.type == 'web-app' %}import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../src/App';{% elif config.project.type == 'api' %}import request from 'supertest';
import app from '../src/app';{% endif %}

describe('New Component Integration', () => {
  it('should integrate correctly with main system', async () => {
    {% if config.project.type == 'web-app' %}// Test UI integration
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    // Navigate to new feature
    // Assert component renders{% elif config.project.type == 'api' %}// Test API integration
    const response = await request(app)
      .post('/api/new-feature')
      .send({ test: 'data' });

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('expected_field');{% else %}// Test integration
    // Add appropriate assertions{% endif %}
  });
});
```{% else %}```
# Create integration test in your testing framework
# Test that component integrates correctly
# Verify component is accessible
# Test end-to-end workflow
```{% endif %}

**Run Integration Test:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
pytest tests/integration/test_new_component_integration.py -v
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
npm test tests/integration/newComponent.integration.test.ts
```{% else %}```bash
# Run integration tests
```{% endif %}

**Deliverables:**
- Integration test file
- Passing test results

---

### Step 4: Manual Verification

**Duration:** 10-15 minutes
**Agent:** Integration Engineer

**Verify Integration Manually:**

{% if config.project.type == 'web-app' %}```bash
# 1. Start development server
npm run dev  # or yarn dev

# 2. Navigate to http://localhost:3000/new-feature

# 3. Verify:
# - Page loads without errors
# - Component renders correctly
# - Functionality works as expected
# - Navigation links work
# - State updates correctly
```{% elif config.project.type == 'api' %}```bash
# 1. Start API server
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}uvicorn src.main:app --reload{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}npm run dev{% else %}# Start server{% endif %}

# 2. Test endpoint
curl -X POST http://localhost:8000/api/new-feature \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# 3. Verify:
# - Endpoint responds
# - Response format is correct
# - Authentication works (if required)
# - Error handling works
```{% elif config.project.type == 'data-platform' %}```{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}python{% else %}bash{% endif %}
# Test data fetching
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}from src.core.data_fetcher import DataFetcher

fetcher = DataFetcher()
result = fetcher.fetch_new_source_data(param="test_value")

print(f"Status: {result['status']}")
if result['status'] == 'success':
    print("✅ Integration working!")
    print(f"Data: {result['data']}")
else:
    print(f"❌ Error: {result.get('error')}"){% else %}# Run data fetching test
# Verify data returns successfully{% endif %}
```{% elif config.project.type == 'ml' %}```{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}python{% else %}bash{% endif %}
# Test model inference
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}import requests

response = requests.post(
    "http://localhost:8000/predict/new-model",
    json={"features": [1.0, 2.0, 3.0]}
)

print(f"Status: {response.status_code}")
print(f"Predictions: {response.json()}"){% else %}# Test inference endpoint
curl -X POST http://localhost:8000/predict/new-model \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0]}'{% endif %}
```{% else %}```bash
# Manual verification steps
# 1. Start application
# 2. Test component functionality
# 3. Verify integration works
```{% endif %}

**Verification Checklist:**
- [ ] Component/endpoint accessible
- [ ] Functionality works as expected
- [ ] No console errors {% if config.project.type == 'web-app' %}(browser DevTools){% endif %}
- [ ] {% if config.project.type == 'api' %}API returns correct responses{% elif config.project.type == 'web-app' %}UI renders correctly{% elif config.project.type == 'data-platform' %}Data fetching successful{% elif config.project.type == 'ml' %}Inference works correctly{% else %}Component works correctly{% endif %}
- [ ] Integration test passes

**Deliverables:**
- Manual test results
- Screenshots (if applicable)
- Verification confirmation

---

### Step 5: Create Integration Handoff Document

**Duration:** 10-15 minutes
**Agent:** Integration Engineer

**Create Handoff Document:**

```markdown
# Integration Complete: [Component Name]

**Date:** YYYY-MM-DD
**Integration Engineer:** [Name or "Claude"]

## Summary

Successfully integrated [Component Name] into {{ config.project.name or 'the application' }}.

## Changes Made

{% if config.project.type == 'web-app' %}### Routes
- Added route: `/new-feature`
- Updated navigation: Added link in main navigation

### State Management
- Connected to state: `newFeatureSlice`

### Components
- Integrated component: `NewComponent.tsx`{% elif config.project.type == 'api' %}### API Endpoints
- Added endpoint: `POST /api/new-feature`
- Updated router: Registered in main app

### Middleware
- Added middleware: [If applicable]

### Documentation
- Updated OpenAPI schema{% elif config.project.type == 'data-platform' %}### Data Sources
- Registered: `new_source` in data registry
- Added fetch method: `fetch_new_source_data()`

### Orchestration
- Added to pipeline: [If applicable]{% elif config.project.type == 'ml' %}### Models
- Registered model: `new_model` version 1
- Added inference endpoint: `/predict/new-model`

### Serving
- Configured serving: [Details]{% else %}### Integration
- [List changes made]{% endif %}

## Test Results

### Integration Tests
- ✅ All integration tests passing
- Test file: `tests/integration/test_new_component_integration.py`

### Manual Tests
- ✅ Manual verification completed
- No errors observed

## Configuration

{% if config.project.type == 'api' %}- Authentication: [Required/Not required]
- Rate limiting: [Details]{% elif config.project.type == 'data-platform' %}- Update frequency: [DAILY/HOURLY/etc.]
- Dependencies: [List any dependencies]{% elif config.project.type == 'ml' %}- Model version: 1
- Resource requirements: [CPU/GPU/Memory]{% endif %}

## Next Steps

- Update documentation (Documentation Engineer)
- Commit changes (Git Committer)
- Deploy to staging/production

## Files Modified

- [List all files modified]

**Integration Status:** ✅ COMPLETE
```

**Save Handoff Document:**
```bash
# Save to handoffs directory
# {{ config.custom.handoff_location or 'docs/handoffs' }}/integration-complete-[component-name].md
```

**Deliverables:**
- Integration handoff document

---

## Success Criteria

Integration is complete when:

- [x] Component {% if config.project.type == 'web-app' %}registered in router{% elif config.project.type == 'api' %}registered in API router{% elif config.project.type == 'data-platform' %}registered in data registry{% elif config.project.type == 'ml' %}registered in model registry{% else %}registered in main application{% endif %}
- [x] {% if config.project.type == 'web-app' %}Routes and navigation updated{% elif config.project.type == 'api' %}Endpoint accessible via API{% elif config.project.type == 'data-platform' %}Data fetching method added{% elif config.project.type == 'ml' %}Inference endpoint deployed{% else %}Component accessible{% endif %}
- [x] Integration test created and passing
- [x] Manual verification successful
- [x] Handoff document created

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
{% if config.project.type == 'web-app' %}| **Component not rendering** | Check route configuration, verify imports |
| **State not updating** | Verify state management connection |
| **404 errors** | Check route path matches exactly |{% elif config.project.type == 'api' %}| **Endpoint not found** | Verify router registration, check path |
| **Authentication fails** | Check middleware configuration |
| **Response format wrong** | Verify serialization/schema |{% elif config.project.type == 'data-platform' %}| **Data source not found** | Check registry registration |
| **Fetch fails** | Verify data source implementation, check credentials |
| **Schema mismatch** | Verify data schema matches expected format |{% elif config.project.type == 'ml' %}| **Model not loading** | Check model registry, verify version |
| **Inference fails** | Verify input schema, check preprocessing |
| **High latency** | Optimize model loading, implement caching |{% else %}| **Component not accessible** | Check registration and configuration |
| **Integration fails** | Verify dependencies are satisfied |{% endif %}

---

## Next Steps

After integration complete:
1. **Documentation Engineer** - Update documentation
2. **Git Committer** - Commit changes
3. {% if config.ci_cd %}**CI/CD** - Deploy to staging{% else %}**Deploy** - Deploy to staging/production{% endif %}

---

## Related Documentation

**Agent Instructions:**
- `agents/development/integration-engineer.md`
- `agents/documentation/documentation-engineer.md`
- `agents/documentation/git-committer.md`

**Other Workflows:**
- `workflows/single-feature-development.md` (full development workflow)
- `workflows/weekly-sprint.md` (multi-component integration)

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
