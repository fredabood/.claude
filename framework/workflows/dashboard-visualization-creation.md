# Dashboard & Visualization Creation Workflow

**Purpose:** Create and deploy dashboards/visualizations with version control and automation
**Duration:** 2-5 days
**Complexity:** Medium
**Agents:** {% if config.agents %}{{ config.agents.data_analyst or 'Data Analyst' }}, {{ config.agents.developer or 'Developer' }}, {{ config.agents.documentation_engineer or 'Documentation Engineer' }}, {{ config.agents.git_committer or 'Git Committer' }}{% else %}Data Analyst, Developer, Documentation Engineer, Git Committer{% endif %}

**When to Use:**
- Creating monitoring dashboards for production systems
- Building analytics dashboards for {% if config.project.type == 'data-platform' %}data insights{% elif config.project.type == 'ml' %}model performance{% elif config.project.type == 'api' %}API metrics{% else %}application metrics{% endif %}
- Implementing dashboard-as-code with version control
- Setting up multi-environment dashboard deployment
- Automating dashboard generation from templates

---

## 📋 Workflow Overview

This workflow provides systematic guidance for creating dashboards/visualizations with version control, automated deployment, and quality assurance. It covers the complete dashboard lifecycle from design through CI/CD integration.

**Key Benefits:**
- **Version Control:** Dashboards managed as code in Git
- **Automation:** Programmatic dashboard generation and deployment
- **Multi-Environment:** Consistent promotion from dev → staging → prod
- **Quality Assurance:** Validation and testing before deployment
- **Maintenance:** Easy updates and rollback capabilities

**Applicable To:**
{% if config.monitoring and config.monitoring.visualization %}{{ config.monitoring.visualization or 'Visualization platform' }}{% else %}- Grafana
- Tableau
- PowerBI
- {% if config.cloud_provider == 'aws' %}CloudWatch Dashboards{% elif config.cloud_provider == 'azure' %}Azure Monitor Dashboards{% elif config.cloud_provider == 'gcp' %}Google Cloud Monitoring{% else %}Cloud monitoring dashboards{% endif %}
- {% if config.project.type == 'data-platform' %}Databricks/Lakeview{% else %}Custom dashboards{% endif %}
- {% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend }} visualization libraries{% endif %}{% endif %}

---

## 🔄 Workflow Steps

### Step 1: Define Dashboard Requirements (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.data_analyst or 'Data Analyst' }}{% else %}Data Analyst{% endif %} or Product Owner
**Duration:** 4 hours

**Activities:**

**1.1: Identify Dashboard Purpose**
- **Audience:** Who will use this dashboard? (developers, executives, operations, customers)
- **Use Case:** {% if config.project.type == 'data-platform' %}Data insights{% elif config.project.type == 'ml' %}Model monitoring{% elif config.project.type == 'api' %}API performance{% elif config.project.type == 'web-app' %}Application analytics{% else %}System monitoring{% endif %}
- **Refresh Frequency:** Real-time, hourly, daily, weekly?
- **Key Decisions:** What actions will users take based on dashboard data?

**1.2: Define Key Metrics**

{% if config.project.type == 'api' %}**API Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Endpoint performance
- Rate limiting hits
{% elif config.project.type == 'data-platform' %}**Data Pipeline Metrics:**
- Pipeline execution time
- Data volume processed
- Success/failure rates
- Data quality scores
- Cost per pipeline run
{% elif config.project.type == 'ml' %}**ML Model Metrics:**
- Model accuracy/precision/recall
- Inference latency
- Prediction volume
- Feature drift detection
- Model retraining frequency
{% elif config.project.type == 'web-app' %}**Application Metrics:**
- Page load time
- User sessions
- Feature usage
- Error rates
- Conversion funnel
{% else %}**System Metrics:**
- Performance metrics
- Error rates
- Usage statistics
- Resource utilization
- Business KPIs
{% endif %}

**1.3: Identify Data Sources**
- {% if config.database %}{{ config.database.type or 'Database' }}{% else %}Database{% endif %} tables/views
- {% if config.monitoring and config.monitoring.platform %}{{ config.monitoring.platform }}{% else %}Monitoring system{% endif %} metrics
- {% if config.logging and config.logging.platform %}{{ config.logging.platform }}{% else %}Logging platform{% endif %} logs
- {% if config.project.type == 'api' %}API gateways{% elif config.project.type == 'ml' %}ML platforms{% else %}Application{% endif %} events
- External data sources (if needed)

**1.4: Design Dashboard Layout**
- Number of panels/widgets needed
- Widget types (time series, counters, tables, heatmaps, etc.)
- Layout structure (grid, rows, columns)
- Filtering and drill-down requirements
- Mobile/responsive considerations

**Output:**
- Dashboard requirements document
- Data source inventory
- Mockup or wireframe (optional)
- Success metrics for dashboard

---

### Step 2: Develop Dashboard (1-3 days)

**Agent:** {% if config.agents %}{{ config.agents.developer or 'Developer' }}{% else %}Developer{% endif %} or {% if config.agents %}{{ config.agents.data_analyst or 'Data Analyst' }}{% else %}Data Analyst{% endif %}
**Duration:** 1-3 days (varies by complexity)

**Activities:**

**2.1: Set Up Dashboard-as-Code Structure**

Create version-controlled dashboard configuration:

{% if config.monitoring and config.monitoring.visualization == 'grafana' %}```
dashboards/
├── {{ config.project.name or 'project' }}-overview.json    # Grafana dashboard JSON
├── {{ config.project.name or 'project' }}-details.json
├── provisioning/
│   └── dashboards.yml                 # Grafana provisioning config
└── queries/
    └── *.{% if config.technology_stack.backend.language == 'python' %}py{% elif config.technology_stack.backend.language == 'java' %}java{% else %}sql{% endif %}                            # Query definitions
```
{% elif config.cloud_provider == 'aws' %}```
dashboards/
├── cloudwatch-dashboard.json          # CloudWatch dashboard definition
├── cloudformation/
│   └── dashboard-stack.yml            # IaC for dashboard deployment
└── queries/
    └── *.{% if config.technology_stack.backend.language == 'python' %}py{% elif config.technology_stack.backend.language == 'java' %}java{% else %}sql{% endif %}                            # Metric queries
```
{% else %}```
dashboards/
├── dashboard-config.{% if config.technology_stack.backend.language == 'python' %}json{% elif config.technology_stack.backend.language == 'java' %}json{% else %}yaml{% endif %}        # Dashboard specification
├── {% if config.iac_tool %}{{ config.iac_tool.lower() }}/{% else %}infrastructure/{% endif %}
│   └── dashboard-resources.{% if config.iac_tool == 'Terraform' %}tf{% elif config.iac_tool == 'Pulumi' %}{% if config.technology_stack.backend.language == 'python' %}py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}ts{% else %}yaml{% endif %}{% else %}yaml{% endif %}     # Infrastructure-as-Code
└── queries/
    └── *.{% if config.technology_stack.backend.language == 'python' %}py{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}ts{% elif config.technology_stack.backend.language == 'java' %}java{% else %}sql{% endif %}                            # Data queries
```
{% endif %}

**2.2: Create Dashboard Configuration**

{% if config.monitoring and config.monitoring.visualization == 'grafana' %}**Grafana JSON Example:**
```json
{
  "dashboard": {
    "title": "{% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %} Overview",
    "panels": [
      {
        "id": 1,
        "title": "{% if config.project.type == 'api' %}Request Rate{% elif config.project.type == 'ml' %}Predictions/sec{% else %}Requests/sec{% endif %}",
        "type": "graph",
        "targets": [
          {
            "expr": "rate({% if config.project.name %}{{ config.project.name }}_{% endif %}requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```
{% elif config.cloud_provider == 'aws' %}**CloudWatch Dashboard Example:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["{% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %}", "{% if config.project.type == 'api' %}RequestCount{% elif config.project.type == 'ml' %}PredictionCount{% else %}EventCount{% endif %}"]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "{{ config.cloud_region or 'us-east-1' }}"
      }
    }
  ]
}
```
{% else %}**Dashboard Configuration Example:**
{% if config.technology_stack.backend.language == 'python' %}```python
dashboard_config = {
    "title": "{% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %} Dashboard",
    "refresh": "{% if config.monitoring and config.monitoring.refresh_rate %}{{ config.monitoring.refresh_rate }}{% else %}30s{% endif %}",
    "panels": [
        {
            "title": "{% if config.project.type == 'api' %}API Performance{% elif config.project.type == 'ml' %}Model Performance{% else %}System Performance{% endif %}",
            "type": "timeseries",
            "query": "SELECT timestamp, value FROM metrics WHERE metric_name = 'performance'"
        }
    ]
}
```{% else %}```yaml
dashboard:
  title: "{% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %} Dashboard"
  refresh: "{% if config.monitoring and config.monitoring.refresh_rate %}{{ config.monitoring.refresh_rate }}{% else %}30s{% endif %}"
  panels:
    - title: "{% if config.project.type == 'api' %}API Performance{% elif config.project.type == 'ml' %}Model Performance{% else %}System Performance{% endif %}"
      type: timeseries
      query: "SELECT timestamp, value FROM metrics WHERE metric_name = 'performance'"
```{% endif %}
{% endif %}

**2.3: Define Data Queries**

Create reusable query definitions:

{% if config.database and config.database.type == 'postgresql' %}```sql
-- queries/{% if config.project.type == 'api' %}api_metrics{% elif config.project.type == 'ml' %}model_metrics{% else %}app_metrics{% endif %}.sql
SELECT
    time_bucket('5 minutes', timestamp) AS time,
    {% if config.project.type == 'api' %}COUNT(*) as request_count,
    AVG(response_time) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time) as p95_response_time
{% elif config.project.type == 'ml' %}COUNT(*) as prediction_count,
    AVG(inference_time) as avg_inference_time,
    AVG(confidence_score) as avg_confidence
{% else %}COUNT(*) as event_count,
    AVG(processing_time) as avg_processing_time
{% endif %}FROM {% if config.monitoring and config.monitoring.metrics_table %}{{ config.monitoring.metrics_table }}{% else %}metrics{% endif %}
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY time
ORDER BY time DESC;
```
{% elif config.technology_stack.backend.language == 'python' %}```python
# queries/{% if config.project.type == 'api' %}api_metrics{% elif config.project.type == 'ml' %}model_metrics{% else %}app_metrics{% endif %}.py
from datetime import datetime, timedelta

def get_{% if config.project.type == 'api' %}api{% elif config.project.type == 'ml' %}model{% else %}app{% endif %}_metrics(time_range_hours=24):
    """Query {% if config.project.type == 'api' %}API{% elif config.project.type == 'ml' %}model{% else %}application{% endif %} metrics."""
    query = f"""
        SELECT
            timestamp,
            {% if config.project.type == 'api' %}request_count,
            avg_response_time,
            error_rate
{% elif config.project.type == 'ml' %}prediction_count,
            avg_inference_time,
            model_accuracy
{% else %}event_count,
            avg_processing_time,
            error_rate
{% endif %}        FROM {{ config.monitoring.metrics_table or 'metrics' }}
        WHERE timestamp > NOW() - INTERVAL '{time_range_hours} hours'
        ORDER BY timestamp DESC
    """
    return query
```
{% else %}```
# Define queries in your preferred query language
SELECT * FROM metrics
WHERE timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)
```
{% endif %}

**2.4: Implement Dashboard Generation** (Optional - for programmatic dashboards)

{% if config.technology_stack.backend.language == 'python' %}```python
# scripts/generate_dashboard.py
import json
from typing import List, Dict

class DashboardGenerator:
    def __init__(self, title: str):
        self.dashboard = {
            "title": title,
            "panels": [],
            "refresh": "30s"
        }

    def add_metric_panel(self, title: str, query: str, panel_type: str = "timeseries"):
        """Add a metric visualization panel."""
        panel = {
            "title": title,
            "type": panel_type,
            "query": query,
            "position": len(self.dashboard["panels"])
        }
        self.dashboard["panels"].append(panel)
        return self

    def add_table_panel(self, title: str, query: str, columns: List[str]):
        """Add a table panel."""
        panel = {
            "title": title,
            "type": "table",
            "query": query,
            "columns": columns,
            "position": len(self.dashboard["panels"])
        }
        self.dashboard["panels"].append(panel)
        return self

    def to_json(self) -> str:
        """Export dashboard as JSON."""
        return json.dumps(self.dashboard, indent=2)

    def save(self, filename: str):
        """Save dashboard to file."""
        with open(filename, 'w') as f:
            f.write(self.to_json())

# Usage
dashboard = DashboardGenerator("{% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %} Monitoring")
dashboard.add_metric_panel(
    title="{% if config.project.type == 'api' %}Request Rate{% elif config.project.type == 'ml' %}Prediction Rate{% else %}Event Rate{% endif %}",
    query="SELECT * FROM {% if config.monitoring and config.monitoring.metrics_table %}{{ config.monitoring.metrics_table }}{% else %}metrics{% endif %}"
)
dashboard.save("dashboards/generated-dashboard.json")
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// scripts/generate-dashboard.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}
{% if config.technology_stack.backend.language == 'typescript' %}interface Panel {
    title: string;
    type: string;
    query: string;
    position: number;
}

interface Dashboard {
    title: string;
    panels: Panel[];
    refresh: string;
}
{% endif %}
class DashboardGenerator {
    private dashboard{% if config.technology_stack.backend.language == 'typescript' %}: Dashboard{% endif %};

    constructor(title{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}) {
        this.dashboard = {
            title,
            panels: [],
            refresh: '30s'
        };
    }

    addMetricPanel(title{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}, query{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}, panelType{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %} = 'timeseries'){% if config.technology_stack.backend.language == 'typescript' %}: this{% endif %} {
        const panel{% if config.technology_stack.backend.language == 'typescript' %}: Panel{% endif %} = {
            title,
            type: panelType,
            query,
            position: this.dashboard.panels.length
        };
        this.dashboard.panels.push(panel);
        return this;
    }

    toJSON(){% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %} {
        return JSON.stringify(this.dashboard, null, 2);
    }
}

// Usage
const dashboard = new DashboardGenerator('{% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %} Monitoring');
dashboard.addMetricPanel(
    '{% if config.project.type == 'api' %}Request Rate{% elif config.project.type == 'ml' %}Prediction Rate{% else %}Event Rate{% endif %}',
    'SELECT * FROM {% if config.monitoring and config.monitoring.metrics_table %}{{ config.monitoring.metrics_table }}{% else %}metrics{% endif %}'
);
```
{% else %}# Use dashboard generator tool or template approach for your language/platform
{% endif %}

**Output:**
- Dashboard configuration files
- Query definitions
- Generation scripts (if programmatic)
- README with setup instructions

---

### Step 3: Validate Dashboard (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.developer or 'Developer' }}{% else %}Developer{% endif %}
**Duration:** 4 hours

**Activities:**

**3.1: Configuration Validation**
- Validate dashboard configuration syntax (JSON/YAML schema)
- Check query syntax {% if config.database %}against {{ config.database.type }}{% endif %}
- Verify data source connections
- Test metric calculations

**3.2: Visual Validation**
- Deploy to {% if config.environments %}{{ config.environments.dev or 'development' }}{% else %}development{% endif %} environment
- Verify all panels render correctly
- Check data accuracy against source
- Test filtering and drill-down
- Validate time range selections

**3.3: Performance Validation**
- Measure dashboard load time
- Check query execution times
- Verify refresh rates are appropriate
- Test with expected data volumes

**Validation Script Example:**
{% if config.technology_stack.backend.language == 'python' %}```python
# scripts/validate_dashboard.py
import json{% if config.database and config.database.type %}
import {{ 'psycopg2' if config.database.type == 'postgresql' else 'pymongo' if config.database.type == 'mongodb' else 'sqlalchemy' }}{% endif %}

def validate_dashboard(dashboard_file):
    """Validate dashboard configuration."""
    errors = []

    # Load dashboard
    with open(dashboard_file) as f:
        dashboard = json.load(f)

    # Check required fields
    if 'title' not in dashboard:
        errors.append("Missing required field: title")

    if 'panels' not in dashboard:
        errors.append("Missing required field: panels")

    # Validate panels
    for i, panel in enumerate(dashboard.get('panels', [])):
        if 'query' not in panel:
            errors.append(f"Panel {i}: Missing query")
        # Validate query syntax here

    return errors

errors = validate_dashboard('dashboards/dashboard.json')
if errors:
    print("Validation errors:", errors)
    exit(1)
else:
    print("Dashboard validation passed")
```
{% else %}# Create validation script in your preferred language
# Check configuration syntax, query validity, data source connectivity
{% endif %}

**Output:**
- Validation report
- Performance benchmarks
- List of issues to address

---

### Step 4: Deploy Dashboard (0.5-1 days)

**Agent:** {% if config.agents %}{{ config.agents.developer or 'Developer' }}{% else %}Developer{% endif %} or DevOps Engineer
**Duration:** 4-8 hours

**Activities:**

**4.1: Set Up Multi-Environment Deployment**

Create environment-specific configurations:

```
{% if config.iac_tool %}{{ config.iac_tool.lower() }}/{% else %}infrastructure/{% endif %}
├── environments/
│   ├── {% if config.environments %}{{ config.environments.dev or 'dev' }}{% else %}dev{% endif %}/
│   │   └── dashboard-config.{% if config.iac_tool == 'Terraform' %}tfvars{% else %}yaml{% endif %}
│   ├── {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}/
│   │   └── dashboard-config.{% if config.iac_tool == 'Terraform' %}tfvars{% else %}yaml{% endif %}
│   └── {% if config.environments %}{{ config.environments.prod or 'prod' }}{% else %}prod{% endif %}/
│       └── dashboard-config.{% if config.iac_tool == 'Terraform' %}tfvars{% else %}yaml{% endif %}
```

**4.2: Create Deployment Scripts**

{% if config.iac_tool == 'Terraform' %}```hcl
# {% if config.iac_tool %}{{ config.iac_tool.lower() }}/{% endif %}dashboard.tf
{% if config.monitoring and config.monitoring.visualization == 'grafana' %}resource "grafana_dashboard" "main" {
  config_json = file("${path.module}/../dashboards/dashboard.json")
  folder      = var.folder_id
}
{% elif config.cloud_provider == 'aws' %}resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.dashboard_name
  dashboard_body = file("${path.module}/../dashboards/cloudwatch-dashboard.json")
}
{% else %}# Configure dashboard deployment for your platform
{% endif %}
```
{% elif config.iac_tool == 'Pulumi' %}{% if config.technology_stack.backend.language == 'python' %}```python
# {{ config.iac_tool.lower() }}/dashboard.py
import pulumi
{% if config.cloud_provider == 'aws' %}import pulumi_aws as aws{% endif %}

dashboard = aws.cloudwatch.Dashboard("dashboard",
    dashboard_name="{{ config.project.name or 'app' }}-dashboard",
    dashboard_body=open("../dashboards/dashboard.json").read()
)
```{% endif %}
{% else %}```bash
# scripts/deploy-dashboard.sh
{% if config.monitoring and config.monitoring.visualization == 'grafana' %}#!/bin/bash
# Deploy Grafana dashboard
DASHBOARD_FILE="dashboards/dashboard.json"
GRAFANA_URL="{{ config.monitoring.url or '$GRAFANA_URL' }}"
GRAFANA_TOKEN="{{ config.monitoring.api_token or '$GRAFANA_API_TOKEN' }}"

curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
    -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${DASHBOARD_FILE}"
{% else %}#!/bin/bash
# Deploy dashboard to your platform
# Add platform-specific deployment commands
{% endif %}```
{% endif %}

**4.3: Set Up CI/CD Pipeline**

{% if config.vcs_platform == 'GitHub' %}```yaml
# .github/workflows/deploy-dashboard.yml
name: Deploy Dashboard

on:
  push:
    branches: [{% if config.environments %}{{ config.environments.prod or 'main' }}{% else %}main{% endif %}]
    paths:
      - 'dashboards/**'
      - '{% if config.iac_tool %}{{ config.iac_tool.lower() }}/{% else %}infrastructure/{% endif %}**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Dashboard
        run: {% if config.technology_stack.backend.language == 'python' %}python scripts/validate_dashboard.py{% else %}./scripts/validate-dashboard.sh{% endif %}

  deploy-staging:
    needs: validate
    runs-on: ubuntu-latest
    environment: {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Staging
        run: {% if config.iac_tool %}{{ config.iac_tool.lower() }} apply -auto-approve{% else %}./scripts/deploy-dashboard.sh staging{% endif %}
        env:
          {% if config.monitoring %}MONITORING_API_KEY: {% raw %}${{ secrets.STAGING_MONITORING_API_KEY }}{% endraw %}{% endif %}

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: {% if config.environments %}{{ config.environments.prod or 'production' }}{% else %}production{% endif %}
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Production
        run: {% if config.iac_tool %}{{ config.iac_tool.lower() }} apply -auto-approve{% else %}./scripts/deploy-dashboard.sh prod{% endif %}
        env:
          {% if config.monitoring %}MONITORING_API_KEY: {% raw %}${{ secrets.PROD_MONITORING_API_KEY }}{% endraw %}{% endif %}
```
{% else %}# Create CI/CD pipeline configuration for your platform (GitLab, Jenkins, etc.)
{% endif %}

**Output:**
- Deployed dashboard in {% if config.environments %}{{ config.environments.dev or 'dev' }}{% else %}dev{% endif %}/{% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}/{% if config.environments %}{{ config.environments.prod or 'prod' }}{% else %}prod{% endif %} environments
- CI/CD pipeline configured
- Deployment documentation

---

### Step 5: Document Dashboard (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.documentation_engineer or 'Documentation Engineer' }}{% else %}Documentation Engineer{% endif %}
**Duration:** 4 hours

**Activities:**

**5.1: Create Dashboard Documentation**

```markdown
# {% if config.project.name %}{{ config.project.name }}{% else %}Application{% endif %} Dashboard Documentation

## Overview
{% if config.project.type == 'api' %}Monitoring dashboard for API performance and health.
{% elif config.project.type == 'ml' %}ML model performance and monitoring dashboard.
{% elif config.project.type == 'data-platform' %}Data pipeline monitoring and analytics dashboard.
{% else %}Application monitoring dashboard.
{% endif %}

## Access
- **{% if config.environments %}{{ config.environments.dev | title or 'Dev' }}{% else %}Dev{% endif %}:** [URL]
- **{% if config.environments %}{{ config.environments.staging | title or 'Staging' }}{% else %}Staging{% endif %}:** [URL]
- **{% if config.environments %}{{ config.environments.prod | title or 'Prod' }}{% else %}Prod{% endif %}:** [URL]

## Metrics

### {% if config.project.type == 'api' %}API Performance{% elif config.project.type == 'ml' %}Model Performance{% elif config.project.type == 'data-platform' %}Pipeline Performance{% else %}System Performance{% endif %}
- **Description:** [Metric description]
- **Data Source:** {% if config.monitoring and config.monitoring.metrics_table %}{{ config.monitoring.metrics_table }}{% else %}[table name]{% endif %}
- **Query:** [SQL/query]
- **Thresholds:** [Alert thresholds]

## Alerts
[Document any configured alerts]

## Maintenance
- **Refresh Rate:** {% if config.monitoring and config.monitoring.refresh_rate %}{{ config.monitoring.refresh_rate }}{% else %}30 seconds{% endif %}
- **Data Retention:** {% if config.monitoring and config.monitoring.retention_days %}{{ config.monitoring.retention_days }} days{% else %}[retention period]{% endif %}
- **Owner:** {% if config.team %}{{ config.team.name }}{% else %}[team name]{% endif %}
```

**5.2: Update Project Documentation**
- Add dashboard links to .claude/CLAUDE.md
- Update README with monitoring section
- Document query definitions
- Create troubleshooting guide

**Output:**
- Dashboard documentation
- Updated project docs
- User guide (if needed)

---

### Step 6: Commit & Review (0.2 days)

**Agent:** {% if config.agents %}{{ config.agents.git_committer or 'Git Committer' }}{% else %}Git Committer{% endif %}
**Duration:** 1.5 hours

**Activities:**
1. Review all dashboard files
2. Stage dashboard configurations, queries, scripts
3. Create descriptive commit message
4. Push to repository
5. Create pull request for review

**Commit Message Template:**
```
feat: Add {% if config.project.type == 'api' %}API monitoring{% elif config.project.type == 'ml' %}model performance{% elif config.project.type == 'data-platform' %}pipeline monitoring{% else %}system monitoring{% endif %} dashboard

Created {% if config.monitoring and config.monitoring.visualization %}{{ config.monitoring.visualization }}{% else %}monitoring{% endif %} dashboard with:
- {% if config.project.type == 'api' %}Request rate, response time, error rate metrics{% elif config.project.type == 'ml' %}Prediction rate, inference latency, model accuracy{% elif config.project.type == 'data-platform' %}Pipeline execution, data volume, quality scores{% else %}Key performance and health metrics{% endif %}
- Multi-environment deployment (dev/staging/prod)
- Automated CI/CD pipeline
- Query definitions and validation scripts

Dashboard accessible at: [URL]
```

**Output:**
- Dashboard files committed
- Pull request created
- CI/CD pipeline validated

---

## ✅ Success Criteria

Dashboard workflow is successful when:

1. ✅ **Functional:** Dashboard displays all required metrics accurately
2. ✅ **Performant:** Dashboard loads in <3 seconds, queries execute efficiently
3. ✅ **Version Controlled:** All dashboard config in Git
4. ✅ **Automated:** CI/CD pipeline deploys to all environments
5. ✅ **Documented:** Dashboard purpose, metrics, and maintenance documented
6. ✅ **Validated:** Validation scripts ensure quality
7. ✅ **Multi-Environment:** Deployed to dev/staging/prod successfully

---

## 🔗 Related Workflows

**Upstream (Triggers This Workflow):**
- **{% if config.project.type == 'api' %}API Development{% elif config.project.type == 'ml' %}ML Model Development{% elif config.project.type == 'data-platform' %}Data Pipeline Development{% else %}Feature Development{% endif %}** - Metrics collected during development
- **Sprint Planning** - Dashboard requirements identified

**Downstream (This Workflow Enables):**
- **Monitoring & Alerting** - Dashboards enable observability
- **Performance Optimization** - Metrics guide optimizations

---

## 💡 Best Practices

1. **Start Simple:** Begin with key metrics, expand iteratively
2. **Automate Everything:** Dashboard-as-code, CI/CD, validation
3. **Multi-Environment:** Test in dev/staging before production
4. **Performance:** Optimize queries, use appropriate refresh rates
5. **Documentation:** Document all metrics and data sources
6. **Version Control:** Track all changes in Git
7. **Validation:** Automated validation prevents deployment errors
8. **Maintainability:** Use reusable queries, consistent naming

---

**Workflow Version:** 1.0
**Created:** {{ "now"|date("%Y-%m-%d") }}
**Maintained By:** {% if config.team %}{{ config.team.name }}{% else %}Project Team{% endif %}
**Framework:** Vibey Agent Framework
