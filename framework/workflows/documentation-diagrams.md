# Documentation & Diagrams Workflow

**Purpose:** Create comprehensive technical documentation with professional Mermaid diagrams
**Duration:** 2-4 hours
**Agents:** {% if config.agents %}{{ config.agents.diagram_engineer or 'Diagram Engineer' }}, {{ config.agents.documentation_engineer or 'Documentation Engineer' }}, {{ config.agents.git_committer or 'Git Committer' }}{% else %}Diagram Engineer, Documentation Engineer, Git Committer{% endif %}

**When to Use:**
- After completing a major sprint or feature
- When architecture changes need to be documented
- For onboarding documentation
- When creating sprint implementation guides
- For technical specification documents
- When visual documentation improves understanding

---

## 📋 Workflow Overview

This workflow creates professional Mermaid diagrams and integrates them into your project documentation. Diagrams improve understanding of complex systems, accelerate onboarding, and serve as visual specifications for development.

**Key Benefits:**
- **Visual Communication:** Complex concepts explained with diagrams
- **Onboarding Acceleration:** New team members understand architecture faster
- **Documentation Quality:** Professional diagrams enhance documentation
- **Living Documentation:** Diagrams updated alongside code changes
- **Design Clarity:** Visual specs reduce implementation errors

---

## 🔄 Workflow Steps

### Phase 1: Documentation Research (Optional)
**Agent:** {% if config.agents %}{{ config.agents.researcher or 'Researcher' }}{% else %}Researcher{% endif %}
**Duration:** 30 min - 1 hour
**When:** Needed for external documentation, API specs, or architectural patterns

**Tasks:**
- Research external API documentation
- Summarize architectural patterns
- Extract code examples
- Create quick reference guides
- {% if config.project.type == 'data-platform' %}Research data architecture best practices{% elif config.project.type == 'ml' %}Research ML architecture patterns{% elif config.project.type == 'api' %}Research API design patterns{% else %}Research relevant technical patterns{% endif %}

**Handoff:** Research summary to Diagram Engineer and Documentation Engineer

**Skip This Phase If:**
- Architecture is already well understood
- Documentation is for internal systems only
- Time is constrained

---

### Phase 2: Diagram Creation
**Agent:** {% if config.agents %}{{ config.agents.diagram_engineer or 'Diagram Engineer' }}{% else %}Diagram Engineer{% endif %}
**Duration:** 1-2 hours

**Tasks:**

**1. Clarify Requirements**
   - What diagrams are needed? (architecture, flows, models, workflows)
   - What level of detail? (high-level overview vs implementation details)
   - Who is the audience? (developers, stakeholders, external users)
   - Which components to include?

**2. Create Diagrams**

{% if config.project.type == 'data-platform' %}**Data Platform Diagrams:**
- {% if config.architecture and config.architecture.pattern %}{{ config.architecture.pattern }}{% else %}Data architecture{% endif %} overview diagrams
- Data pipeline workflows ({% if config.data_pipeline %}{{ config.data_pipeline.stages or 'ingestion → processing → serving' }}{% else %}ingestion → transformation → serving{% endif %})
- System architecture (components, data flows)
- {% if config.database %}{{ config.database.type or 'Database' }}{% else %}Database{% endif %} data models (ERDs with relationships)
- Data ingestion workflows
- {% if config.data_pipeline and config.data_pipeline.caching %}Caching strategy diagrams{% endif %}

{% elif config.project.type == 'api' %}**API Service Diagrams:**
- System architecture (API gateway, services, databases)
- API endpoint workflows (request → validation → processing → response)
- Authentication/authorization flows ({% if config.security and config.security.authentication %}{{ config.security.authentication.method or 'JWT, OAuth' }}{% else %}authentication methods{% endif %})
- {% if config.database %}{{ config.database.type or 'Database' }}{% else %}Database{% endif %} schema (ERDs with relationships)
- Rate limiting and caching strategies
- Microservices communication (if applicable)

{% elif config.project.type == 'ml' %}**ML Project Diagrams:**
- ML system architecture (training, inference, monitoring)
- Model training pipelines (data → features → training → evaluation)
- Feature engineering workflows
- Model deployment architecture ({% if config.ml_platform and config.ml_platform.deployment %}{{ config.ml_platform.deployment.type or 'batch, real-time' }}{% else %}deployment patterns{% endif %})
- Inference flows (request → preprocessing → prediction → postprocessing)
- {% if config.ml_platform and config.ml_platform.monitoring %}Monitoring and drift detection{% endif %}

{% elif config.project.type == 'web-app' %}**Web Application Diagrams:**
- System architecture (frontend, backend, database{% if config.cloud_provider %}, {{ config.cloud_provider }} services{% endif %})
- User flows (authentication, key features, navigation)
- Component hierarchy ({% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend }}{% else %}frontend{% endif %} components)
- API integration workflows (frontend → backend → database)
- State management flows ({% if config.web_framework and config.web_framework.frontend == 'react' %}Redux, Context{% elif config.web_framework and config.web_framework.frontend == 'vue' %}Vuex, Pinia{% else %}state management{% endif %})
- Deployment architecture

{% else %}**General Application Diagrams:**
- System architecture (all major components)
- User workflows (key user interactions)
- Component relationships and dependencies
- Data flows through the system
- Integration points with external services
- Deployment architecture

{% endif %}**3. Save and Organize**
   - Create `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}/diagrams/{% else %}docs/diagrams/{% endif %}` directory if needed
   - Save each diagram with descriptive filename
   - Create `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}/diagrams/{% else %}docs/diagrams/{% endif %}README.md` index
   - Embed diagrams in relevant documentation

**4. Deliverables:**
   - ✅ Mermaid diagram files (.md) in diagrams directory
   - ✅ Diagrams embedded in README, sprint plans, guides
   - ✅ Diagram index with descriptions
   - {% if config.project.type == 'data-platform' and config.architecture and config.architecture.pattern and 'medallion' in config.architecture.pattern.lower() %}✅ Consistent layer color coding (if using medallion architecture){% endif %}
   - ✅ Accurate component names from codebase
   - ✅ Consistent styling across all diagrams

**Handoff:** Diagram files and embedded diagrams to Documentation Engineer

---

### Phase 3: Documentation Writing
**Agent:** {% if config.agents %}{{ config.agents.documentation_engineer or 'Documentation Engineer' }}{% else %}Documentation Engineer{% endif %}
**Duration:** 1-2 hours

**Tasks:**

**1. Update Core Documentation**
   - `CLAUDE.md` - Current state, recent changes
   - `README.md` - Project overview with embedded diagrams
   - {% if config.project.structure and config.project.structure.docs_directory %}`{{ config.project.structure.docs_directory }}/architecture/{% else %}`docs/architecture/{% endif %}` - Technical details
   - Sprint-specific docs (sprint completion documents)

**2. Integrate Diagrams**
   - Embed relevant diagrams in appropriate sections
   - Add context descriptions before each diagram
   - Link to detailed diagram files when needed
   - Ensure diagrams match text descriptions

**3. Create Guides** (if needed)

{% if config.project.type == 'api' %}- API usage guides with sequence diagrams
- Authentication flows with security diagrams
- Integration guides with workflow diagrams
- Developer onboarding with architecture diagrams

{% elif config.project.type == 'web-app' %}- User guides with workflow diagrams
- Component documentation with hierarchy diagrams
- State management guides with flow diagrams
- Developer onboarding with architecture diagrams

{% elif config.project.type == 'data-platform' %}- Data pipeline guides with flow diagrams
- Data model documentation with ERD diagrams
- Integration guides with workflow diagrams
- Developer onboarding with architecture diagrams

{% elif config.project.type == 'ml' %}- Model training guides with pipeline diagrams
- Inference guides with deployment diagrams
- Feature engineering guides with workflow diagrams
- ML ops guides with monitoring diagrams

{% else %}- User guides with workflow diagrams
- Developer guides with architecture diagrams
- Integration guides with system diagrams
- Onboarding guides with overview diagrams

{% endif %}**4. Deliverables:**
   - ✅ Updated documentation with embedded diagrams
   - ✅ Consistent references across all docs
   - ✅ Clear diagram captions and context
   - ✅ Links to related documentation
   - ✅ Code examples matching diagram flows

**Handoff:** Complete documentation package to Git Committer

---

### Phase 4: Git Commit
**Agent:** {% if config.agents %}{{ config.agents.git_committer or 'Git Committer' }}{% else %}Git Committer{% endif %}
**Duration:** 15 minutes

**Tasks:**
- Review all diagram files and documentation updates
- Stage diagram files (`{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}/diagrams/{% else %}docs/diagrams/{% endif %}*.md`)
- Stage documentation updates
- Create descriptive commit message
- Push to repository

**Deliverables:**
- ✅ All diagrams committed to diagrams directory
- ✅ Documentation updated and committed
- ✅ Diagrams render correctly on {% if config.vcs_platform %}{{ config.vcs_platform }}{% else %}GitHub{% endif %}
- ✅ Commit message references diagram additions

**Commit Message Template:**
```
docs: {% if config.project.type == 'data-platform' %}Add data pipeline diagrams{% elif config.project.type == 'api' %}Add API architecture diagrams{% elif config.project.type == 'ml' %}Add ML pipeline diagrams{% elif config.project.type == 'web-app' %}Add application architecture diagrams{% else %}Add system diagrams{% endif %} and comprehensive guide

Created professional Mermaid diagrams documenting:
- [Diagram 1 description]
- [Diagram 2 description]
- [Diagram 3 description]

Updated [README/Architecture Guide] with embedded diagrams.
All diagrams use consistent styling and accurate component names.
```

---

## 📊 Example Use Cases

### Use Case 1: Sprint Completion Documentation

**Trigger:** Sprint v1.2.0 complete, need comprehensive documentation

**Workflow:**
1. **Diagram Engineer** creates:
   {% if config.project.type == 'data-platform' %}- `docs/diagrams/architecture-data-pipeline.md` - Data pipeline architecture
   - `docs/diagrams/workflow-ingestion-process.md` - Data ingestion flow
   - `docs/diagrams/system-caching-strategy.md` - Caching system
   - `docs/diagrams/model-data-schema.md` - Database ERD
   {% elif config.project.type == 'api' %}- `docs/diagrams/architecture-api-gateway.md` - API architecture
   - `docs/diagrams/workflow-authentication.md` - Auth flow sequence
   - `docs/diagrams/flow-rate-limiting.md` - Rate limiting strategy
   - `docs/diagrams/model-database-schema.md` - Database ERD
   {% elif config.project.type == 'ml' %}- `docs/diagrams/architecture-ml-system.md` - ML system architecture
   - `docs/diagrams/workflow-training-pipeline.md` - Training pipeline
   - `docs/diagrams/flow-inference.md` - Inference flow
   - `docs/diagrams/system-monitoring.md` - Monitoring architecture
   {% else %}- `docs/diagrams/architecture-system-overview.md` - System architecture
   - `docs/diagrams/workflow-user-flow.md` - User workflow
   - `docs/diagrams/flow-data-processing.md` - Data processing
   - `docs/diagrams/model-database-schema.md` - Database ERD
   {% endif %}

2. **Documentation Engineer** writes:
   - Sprint completion document (`SPRINT_V1.2.0_COMPLETE.md`)
   - Embeds diagrams in relevant sections
   - Updates CLAUDE.md with new capabilities
   - Links to diagram files for detailed views

3. **Git Committer** commits:
   - Diagram files in `docs/diagrams/`
   - Sprint completion document
   - Updated CLAUDE.md
   - Commit: "docs: Add Sprint v1.2.0 completion docs with architecture diagrams"

**Result:** Complete sprint documentation with professional diagrams

---

### Use Case 2: Architecture Documentation

**Trigger:** Need to document {% if config.architecture and config.architecture.pattern %}{{ config.architecture.pattern }}{% else %}system architecture{% endif %} for onboarding

**Workflow:**
1. **Diagram Engineer** creates:
   {% if config.project.type == 'data-platform' %}- `docs/diagrams/architecture-data-flow-overview.md` - Full data flow
   - `docs/diagrams/model-database-schema.md` - Database ERD
   - `docs/diagrams/flow-ingestion.md` - Data ingestion
   - `docs/diagrams/flow-transformation.md` - Data transformations
   - `docs/diagrams/flow-serving.md` - Data serving patterns
   {% elif config.project.type == 'ml' %}- `docs/diagrams/architecture-ml-pipeline.md` - ML pipeline overview
   - `docs/diagrams/workflow-feature-engineering.md` - Feature engineering
   - `docs/diagrams/flow-model-training.md` - Training process
   - `docs/diagrams/system-deployment.md` - Deployment architecture
   - `docs/diagrams/flow-monitoring.md` - Monitoring and alerts
   {% else %}- `docs/diagrams/architecture-system-components.md` - Component overview
   - `docs/diagrams/model-data-model.md` - Data model
   - `docs/diagrams/flow-request-processing.md` - Request processing
   - `docs/diagrams/system-deployment.md` - Deployment architecture
   - `docs/diagrams/workflow-integration.md` - External integrations
   {% endif %}

2. **Documentation Engineer** creates:
   - `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}{% else %}docs{% endif %}/architecture/ARCHITECTURE.md` - Comprehensive guide
   - Embeds all diagrams with explanations
   - Includes code examples matching diagram flows
   - Links to specific {% if config.database %}{{ config.database.type }}{% else %}database{% endif %} schemas

3. **Git Committer** commits all files

**Result:** Complete architecture guide with visual documentation

---

### Use Case 3: {% if config.project.type == 'api' %}API{% elif config.project.type == 'data-platform' %}Data Source{% elif config.project.type == 'ml' %}Model{% else %}Feature{% endif %} Integration Guide

**Trigger:** Need developer guide for {% if config.project.type == 'api' %}adding new endpoints{% elif config.project.type == 'data-platform' %}integrating new data sources{% elif config.project.type == 'ml' %}deploying new models{% else %}adding new features{% endif %}

**Workflow:**
1. **Diagram Engineer** creates:
   {% if config.project.type == 'api' %}- `docs/diagrams/workflow-endpoint-pattern.md` - Standard endpoint workflow
   - `docs/diagrams/flow-validation.md` - Request validation
   - `docs/diagrams/architecture-service-layer.md` - Service layer structure
   {% elif config.project.type == 'data-platform' %}- `docs/diagrams/workflow-data-source-pattern.md` - Standard integration workflow
   - `docs/diagrams/flow-caching.md` - Caching strategy flowchart
   - `docs/diagrams/architecture-ingestion.md` - Ingestion architecture
   {% elif config.project.type == 'ml' %}- `docs/diagrams/workflow-model-deployment.md` - Deployment workflow
   - `docs/diagrams/flow-inference-pipeline.md` - Inference flow
   - `docs/diagrams/system-model-serving.md` - Model serving architecture
   {% else %}- `docs/diagrams/workflow-feature-integration.md` - Integration workflow
   - `docs/diagrams/flow-component-lifecycle.md` - Component lifecycle
   - `docs/diagrams/architecture-module-structure.md` - Module structure
   {% endif %}

2. **Documentation Engineer** writes:
   - `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}{% else %}docs{% endif %}/guides/{% if config.project.type == 'api' %}ADDING_ENDPOINTS.md{% elif config.project.type == 'data-platform' %}ADDING_DATA_SOURCES.md{% elif config.project.type == 'ml' %}DEPLOYING_MODELS.md{% else %}ADDING_FEATURES.md{% endif %}` - Step-by-step guide
   - Embeds workflow diagram showing full integration pattern
   - References diagram files for detailed views
   - Includes code templates matching diagrams

3. **Git Committer** commits documentation package

**Result:** Developer guide with clear visual workflow

---

### Use Case 4: {% if config.project.type == 'web-app' %}Dashboard{% else %}User{% endif %} Guide

**Trigger:** {% if config.project.type == 'web-app' %}Dashboard{% else %}Application{% endif %} complete, need user documentation

**Workflow:**
1. **Diagram Engineer** creates:
   {% if config.project.type == 'web-app' %}- `docs/diagrams/workflow-user-navigation.md` - User flow through {% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend }}{% else %}frontend{% endif %} app
   - `docs/diagrams/workflow-page-navigation.md` - Page navigation structure
   - `docs/diagrams/system-frontend-architecture.md` - Frontend architecture
   {% else %}- `docs/diagrams/workflow-user-interaction.md` - User interaction flow
   - `docs/diagrams/workflow-feature-usage.md` - Feature usage patterns
   - `docs/diagrams/system-ui-architecture.md` - UI architecture
   {% endif %}

2. **Documentation Engineer** writes:
   - `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}{% else %}docs{% endif %}/USER_GUIDE.md` - Complete user documentation
   - Embeds user flow diagrams
   - Screenshots with diagram references
   - Feature descriptions matching diagram components

3. **Git Committer** commits user guide

**Result:** User-friendly guide with visual workflows

---

## ✅ Success Criteria

Documentation and diagrams are successful when:

1. ✅ **Diagrams Render:** All Mermaid diagrams render correctly on {% if config.vcs_platform %}{{ config.vcs_platform }}{% else %}GitHub{% endif %}
2. ✅ **Accuracy:** Component names match actual codebase exactly
3. ✅ **Consistency:** {% if config.project.type == 'data-platform' and config.architecture and config.architecture.pattern and 'medallion' in config.architecture.pattern.lower() %}Layer{% else %}Component{% endif %} styling used consistently throughout
4. ✅ **Clarity:** Non-technical readers can understand main flows
5. ✅ **Completeness:** All key components and relationships shown
6. ✅ **Integration:** Diagrams embedded in relevant documentation
7. ✅ **Maintenance:** Diagrams updated when architecture changes
8. ✅ **Accessibility:** Diagram index makes finding diagrams easy

---

## 📐 Diagram Types by Documentation Need

### For Sprint Completion Docs
{% if config.project.type == 'data-platform' %}- Data pipeline architecture (new pipelines added)
- Feature workflows (new data transformations)
- Data models (new tables or schema changes)
- Integration flows (how new sources integrate)

{% elif config.project.type == 'api' %}- API architecture (new services added)
- Endpoint workflows (new API endpoints)
- Data models (new database tables)
- Integration flows (external service integrations)

{% elif config.project.type == 'ml' %}- ML system architecture (new models added)
- Training pipelines (new model training workflows)
- Feature engineering (new features)
- Deployment architecture (new model deployments)

{% else %}- System architecture (new components added)
- Feature workflows (user flows through new features)
- Data models (new tables or schema changes)
- Integration flows (new integrations)

{% endif %}### For Technical Specifications
- Detailed flowcharts (implementation logic)
- Sequence diagrams ({% if config.project.type == 'api' %}API interactions, auth flows{% elif config.project.type == 'data-platform' %}data pipeline steps{% elif config.project.type == 'ml' %}training/inference steps{% else %}system interactions{% endif %})
- Class diagrams (OOP structure)
- ERDs (database relationships)

### For User Documentation
- User journey flowcharts (simplified, high-level)
- {% if config.project.type == 'web-app' %}Dashboard navigation (page structure){% else %}Interface navigation{% endif %}
- Process workflows (what happens when user performs action)

### For Developer Onboarding
- Overall system architecture (all components)
- {% if config.project.type == 'data-platform' %}Data pipeline architecture{% elif config.project.type == 'ml' %}ML pipeline architecture{% else %}Application architecture{% endif %}
- {% if config.project.type == 'api' %}API endpoint pattern{% elif config.project.type == 'data-platform' %}Data source integration pattern{% elif config.project.type == 'ml' %}Model deployment pattern{% else %}Component integration pattern{% endif %}
- Development workflow (code → test → deploy)

---

## 💡 Best Practices

### For Diagram Engineer

1. **Ask Before Creating:**
   - Clarify diagram purpose and audience
   - Confirm level of detail needed
   - Identify which components to include

2. **Use Project Standards:**
   {% if config.project.type == 'data-platform' and config.architecture and config.architecture.pattern and 'medallion' in config.architecture.pattern.lower() %}- Layer color coding (e.g., Bronze/Silver/Gold: #CD7F32, #C0C0C0, #FFD700){% endif %}
   - Actual component names from codebase
   - {% if config.database %}{{ config.database.type }}{% else %}Database{% endif %} table names from schema
   - Consistent styling across all diagrams

3. **Provide Context:**
   - Add description before diagram code
   - Include legend for complex diagrams
   - Suggest related diagrams that might be useful

### For Documentation Engineer

1. **Embed Strategically:**
   - Put diagrams near relevant text
   - Add caption/context before each diagram
   - Link to detailed diagram files for complex flows

2. **Keep Synchronized:**
   - Update diagrams when architecture changes
   - Reference diagrams in code comments
   - Maintain diagram index

3. **Cross-Reference:**
   - Link between related documentation
   - Reference diagrams in sprint plans
   - Include diagrams in {% if config.project.type == 'api' %}API{% else %}technical{% endif %} documentation

### For Git Committer

1. **Verify Rendering:**
   - Check diagrams render on {% if config.vcs_platform %}{{ config.vcs_platform }}{% else %}GitHub{% endif %} preview
   - Test complex diagrams at mermaid.live
   - Ensure no syntax errors

2. **Organize Well:**
   - Keep `{% if config.project.structure and config.project.structure.docs_directory %}{{ config.project.structure.docs_directory }}/diagrams/{% else %}docs/diagrams/{% endif %}` directory clean
   - Use descriptive filenames
   - Update diagram index

3. **Commit Message:**
   - List diagram files created
   - Mention documentation updated
   - Reference sprint/feature if applicable

---

## 🔗 Related Workflows

**Upstream (Triggers This Workflow):**
- **Sprint Completion** - Often triggers diagram creation
- **Architecture Review** - May require updated diagrams
- **Single Feature Development** - Complex features benefit from diagrams

**Downstream (This Workflow Triggers):**
- **Git Commit Workflow** - Commits diagrams and documentation

**Parallel Workflows:**
- Can run in parallel with development work
- Diagrams can be iteratively refined during sprint

---

## 📝 Common Patterns

### Pattern 1: Feature Documentation
```
Diagram Engineer:
  - workflow-[feature-name].md (user flow)
  - system-[feature-name].md (architecture)

Documentation Engineer:
  - FEATURE_GUIDE.md (embed both diagrams)
  - Update README with links

Git Committer:
  - Commit 2 diagrams + guide
```

### Pattern 2: Architecture Documentation
```
Diagram Engineer:
  - architecture-[system].md (components)
  - model-[schema].md (database ERD)
  - flow-[process].md (data flow)

Documentation Engineer:
  - ARCHITECTURE.md (comprehensive guide)
  - Embed all 3 diagrams

Git Committer:
  - Commit 3 diagrams + architecture doc
```

### Pattern 3: {% if config.project.type == 'api' %}API{% else %}Integration{% endif %} Documentation
```
Diagram Engineer:
  - workflow-[endpoint].md (sequence diagram)
  - flow-[process].md (flowchart)

Documentation Engineer:
  - {% if config.project.type == 'api' %}API_GUIDE.md{% else %}INTEGRATION_GUIDE.md{% endif %} (documentation)
  - Embed workflow diagrams

Git Committer:
  - Commit diagrams + guide
```

---

**Workflow Version:** 1.0
**Created:** {{ "now"|date("%Y-%m-%d") }}
**Maintained By:** {% if config.team %}{{ config.team.name }}{% else %}Project Team{% endif %}
**Framework:** Vibey Agent Framework
