---
id: dashboard-specification
name: Dashboard Specification
version: 1.0.0
from_agent: backend-engineer
to_agents:
- frontend-engineer
- documentation-engineer
purpose: Template for dashboard specification
variables:
- name: aggregation_strategy
  type: string
  required: true
  description: Aggregation Strategy value
- name: author_name
  type: string
  required: true
  description: Author Name value
- name: body_font
  type: string
  required: true
  description: Body Font value
- name: body_size
  type: string
  required: true
  description: Body Size value
- name: caching_strategy
  type: string
  required: true
  description: Caching Strategy value
- name: categorical_scale
  type: string
  required: true
  description: Categorical Scale value
- name: company_colors
  type: string
  required: true
  description: Company Colors value
- name: creation_date
  type: string
  required: true
  description: Creation Date value
- name: criterion
  type: string
  required: true
  description: Criterion value
- name: cross_filter_behavior
  type: string
  required: true
  description: Cross Filter Behavior value
- name: custom_css
  type: string
  required: true
  description: Custom Css value
- name: dashboard_name
  type: string
  required: true
  description: Dashboard Name value
- name: dashboard_platform
  type: string
  required: true
  description: Dashboard Platform value
- name: dashboard_purpose
  type: string
  required: true
  description: Dashboard Purpose value
- name: data_refresh_target
  type: string
  required: true
  description: Data Refresh Target value
description: Template for dashboard specification
---

# Dashboard Specification: {{ dashboard_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.product_owner or 'Product Owner / Data Analyst / Business User' }}
**To:** {{ config.roles.data_analyst or 'Data Analyst / BI Developer / Frontend Developer' }}
**Purpose:** Comprehensive dashboard requirements specification
**Related Workflow:** Dashboard Creation Workflow

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Dashboard Name** | {{ dashboard_name }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ creation_date }} |
| **Platform** | {{ dashboard_platform or 'Tableau/Power BI/Looker/Databricks Lakeview/Custom' }} |
| **Purpose** | {{ dashboard_purpose }} |
| **Audience** | {{ target_audience }} |
| **Status** | {{ document_status }} |

---

## 1. Dashboard Overview

### Business Purpose

**Primary Objective:** {{ primary_objective }}

**Business Questions to Answer:**
{% for question in business_questions %}
{{ loop.index }}. {{ question }}
{% endfor %}

### Target Audience

**Primary Users:** {{ primary_users }}
**Secondary Users:** {{ secondary_users }}

**User Personas:**
{% for persona in user_personas %}
- **{{ persona.role }}**: {{ persona.needs }}
  - **Use Cases:** {{ persona.use_cases }}
  - **Frequency:** {{ persona.frequency }}
{% endfor %}

### Success Criteria

**Dashboard is successful when:**
{% for criterion in success_criteria %}
- [ ] {{ criterion }}
{% endfor %}

---

## 2. Data Sources & Refresh Strategy

### Data Sources

{% for source in data_sources %}
**{{ loop.index }}. {{ source.name }}**
- **Type:** {{ source.type }}
- **Location:** {{ source.location }}
- **Owner:** {{ source.owner }}
- **Update Frequency:** {{ source.update_frequency }}
- **Data Volume:** {{ source.data_volume }}
- **Data Retention:** {{ source.data_retention }}

{% if config.project.type == 'data-platform' %}
**SQL Query:**
```sql
{{ source.sql_query }}
```
{% endif %}
{% endfor %}

### Data Refresh Strategy

| Data Source | Refresh Type | Frequency | Time Window | SLA |
|-------------|--------------|-----------|-------------|-----|
{% for refresh in refresh_strategy %}
| {{ refresh.source }} | {{ refresh.type }} | {{ refresh.frequency }} | {{ refresh.time_window }} | {{ refresh.sla }} |
{% endfor %}

### Data Quality Requirements

{% for requirement in data_quality_requirements %}
- **{{ requirement.name }}**: {{ requirement.description }}
  - **Validation:** {{ requirement.validation }}
{% endfor %}

---

## 3. Dashboard Layout & Structure

### Page Structure

{% if is_multi_page %}
**Dashboard Type:** Multi-page dashboard

**Pages:**
{% for page in dashboard_pages %}
{{ loop.index }}. **{{ page.name }}**: {{ page.description }}
   - **Purpose:** {{ page.purpose }}
   - **Visualizations:** {{ page.visualization_count }}
{% endfor %}

{% else %}
**Dashboard Type:** Single-page dashboard
{% endif %}

### Wireframe

```
{{ wireframe_ascii_art }}
```

{% if wireframe_image_url %}
**Detailed Wireframe:** {{ wireframe_image_url }}
{% endif %}

### Grid Layout

{% if dashboard_platform in ['tableau', 'power-bi', 'looker', 'lakeview'] %}
**Layout Type:** {{ layout_type }}
**Grid Dimensions:** {{ grid_rows }} rows × {{ grid_cols }} columns

{% for section in layout_sections %}
**Section {{ loop.index }}: {{ section.name }}**
- **Position:** Row {{ section.row_start }}-{{ section.row_end }}, Col {{ section.col_start }}-{{ section.col_end }}
- **Content:** {{ section.content }}
{% endfor %}

{% elif dashboard_platform == 'custom' %}
**Framework:** {{ config.web_framework.frontend or 'React/Vue/Angular' }}
**Charting Library:** {{ charting_library or 'Chart.js/D3.js/Recharts/ECharts' }}
**Responsive Breakpoints:** {{ responsive_breakpoints }}
{% endif %}

---

## 4. Visualizations Specification

{% for viz in visualizations %}
### Visualization {{ loop.index }}: {{ viz.name }}

**Type:** {{ viz.type }}
**Position:** {{ viz.position }}
**Size:** {{ viz.size }}

**Data Source:**
- **Query:** {{ viz.data_query }}
- **Aggregation:** {{ viz.aggregation }}
- **Granularity:** {{ viz.granularity }}

{% if viz.type == 'KPI Card' %}
**KPI Configuration:**
- **Metric:** {{ viz.metric_name }}
- **Value:** {{ viz.metric_value }}
- **Trend:** {{ viz.trend_indicator }}
- **Comparison:** {{ viz.comparison }}
- **Target:** {{ viz.target_value }}
- **Color Coding:** {{ viz.color_rules }}

{% elif viz.type in ['Bar Chart', 'Line Chart', 'Area Chart', 'Column Chart'] %}
**Chart Configuration:**
- **X-Axis:** {{ viz.x_axis }}
- **Y-Axis:** {{ viz.y_axis }}
- **Series:** {{ viz.series }}
- **Legend:** {{ viz.legend_position }}
- **Colors:** {{ viz.color_palette }}
- **Tooltips:** {{ viz.tooltip_format }}

{% elif viz.type == 'Table' %}
**Table Configuration:**
- **Columns:** {{ viz.columns }}
- **Sorting:** {{ viz.sorting }}
- **Filtering:** {{ viz.filtering }}
- **Pagination:** {{ viz.pagination }}
- **Row Count:** {{ viz.row_count }}
- **Conditional Formatting:** {{ viz.conditional_formatting }}

{% elif viz.type in ['Pie Chart', 'Donut Chart'] %}
**Pie/Donut Configuration:**
- **Dimension:** {{ viz.dimension }}
- **Measure:** {{ viz.measure }}
- **Labels:** {{ viz.labels }}
- **Legend:** {{ viz.legend_position }}
- **Colors:** {{ viz.color_palette }}

{% elif viz.type == 'Map' %}
**Map Configuration:**
- **Map Type:** {{ viz.map_type }}
- **Location Field:** {{ viz.location_field }}
- **Metric:** {{ viz.metric }}
- **Zoom Level:** {{ viz.zoom_level }}
- **Basemap:** {{ viz.basemap }}
- **Color Scale:** {{ viz.color_scale }}

{% elif viz.type == 'Heatmap' %}
**Heatmap Configuration:**
- **X-Axis:** {{ viz.x_axis }}
- **Y-Axis:** {{ viz.y_axis }}
- **Metric:** {{ viz.metric }}
- **Color Scale:** {{ viz.color_scale }}

{% elif viz.type == 'Gauge' %}
**Gauge Configuration:**
- **Metric:** {{ viz.metric }}
- **Min Value:** {{ viz.min_value }}
- **Max Value:** {{ viz.max_value }}
- **Thresholds:** {{ viz.thresholds }}
- **Color Zones:** {{ viz.color_zones }}
{% endif %}

**Interactivity:**
{% for interaction in viz.interactions %}
- **{{ interaction.trigger }}**: {{ interaction.action }}
{% endfor %}

**Filters Applied:**
{% for filter in viz.filters %}
- {{ filter }}
{% endfor %}

---

{% endfor %}

## 5. Filters & Parameters

### Global Filters

{% for filter in global_filters %}
**{{ loop.index }}. {{ filter.name }}**
- **Type:** {{ filter.type }}
- **Options:** {{ filter.options }}
- **Default Value:** {{ filter.default }}
- **Required:** {{ filter.required }}
- **Applies To:** {{ filter.applies_to }}

{% if filter.type == 'Date Range' %}
**Date Range Configuration:**
- **Default Range:** {{ filter.default_range }}
- **Min Date:** {{ filter.min_date }}
- **Max Date:** {{ filter.max_date }}
- **Presets:** {{ filter.presets }}

{% elif filter.type == 'Dropdown' %}
**Dropdown Configuration:**
- **Multi-Select:** {{ filter.multi_select }}
- **Search:** {{ filter.searchable }}
- **Data Source:** {{ filter.data_source }}

{% elif filter.type == 'Slider' %}
**Slider Configuration:**
- **Min:** {{ filter.min_value }}
- **Max:** {{ filter.max_value }}
- **Step:** {{ filter.step }}
{% endif %}
{% endfor %}

### Local Filters (Visualization-Specific)

{% for local_filter in local_filters %}
- **Visualization:** {{ local_filter.viz_name }}
  - **Filter:** {{ local_filter.filter_name }} ({{ local_filter.filter_type }})
{% endfor %}

### Parameters

{% for param in parameters %}
**{{ param.name }}**
- **Type:** {{ param.type }}
- **Default:** {{ param.default }}
- **Usage:** {{ param.usage }}
{% endfor %}

---

## 6. Metrics & Calculations

### Key Performance Indicators (KPIs)

{% for kpi in kpis %}
**{{ loop.index }}. {{ kpi.name }}**
- **Definition:** {{ kpi.definition }}
- **Formula:** `{{ kpi.formula }}`
- **Data Source:** {{ kpi.data_source }}
- **Update Frequency:** {{ kpi.update_frequency }}
- **Target/Threshold:** {{ kpi.target }}
- **Display Format:** {{ kpi.display_format }}

{% if config.project.type == 'data-platform' %}
**SQL Calculation:**
```sql
{{ kpi.sql_calculation }}
```
{% endif %}
{% endfor %}

### Calculated Fields

{% for calc_field in calculated_fields %}
**{{ calc_field.name }}**
- **Type:** {{ calc_field.type }}
- **Formula:** `{{ calc_field.formula }}`
- **Description:** {{ calc_field.description }}

{% if dashboard_platform == 'tableau' %}
**Tableau Calculation:**
```tableau
{{ calc_field.tableau_formula }}
```

{% elif dashboard_platform == 'power-bi' %}
**DAX Formula:**
```dax
{{ calc_field.dax_formula }}
```

{% elif dashboard_platform == 'custom' %}
**{{ config.technology_stack.backend.language }} Calculation:**
```{{ config.technology_stack.backend.language }}
{{ calc_field.code }}
```
{% endif %}
{% endfor %}

---

## 7. Interactivity & User Actions

### Click Actions

{% for click_action in click_actions %}
**{{ loop.index }}. {{ click_action.viz_name }}**
- **Trigger:** {{ click_action.trigger }}
- **Action:** {{ click_action.action }}
- **Target:** {{ click_action.target }}
- **Behavior:** {{ click_action.behavior }}
{% endfor %}

### Drill-Down Paths

{% for drill_path in drill_down_paths %}
**{{ loop.index }}. {{ drill_path.name }}**
- **Start:** {{ drill_path.start_level }}
- **Path:** {{ drill_path.path_levels }}
- **End:** {{ drill_path.end_level }}
- **Context:** {{ drill_path.context_maintained }}
{% endfor %}

### Cross-Filtering

**Cross-Filter Behavior:** {{ cross_filter_behavior }}

**Filter Relationships:**
{% for relationship in filter_relationships %}
- **{{ relationship.source_viz }}** → **{{ relationship.target_viz }}** ({{ relationship.filter_type }})
{% endfor %}

---

## 8. Styling & Branding

### Color Palette

**Primary Colors:**
{% for color in primary_colors %}
- **{{ color.name }}**: {{ color.hex }} ({{ color.usage }})
{% endfor %}

**Data Visualization Colors:**
- **Sequential Scale:** {{ sequential_scale }}
- **Diverging Scale:** {{ diverging_scale }}
- **Categorical Scale:** {{ categorical_scale }}

### Typography

- **Dashboard Title:** {{ title_font }} ({{ title_size }})
- **Section Headers:** {{ header_font }} ({{ header_size }})
- **Body Text:** {{ body_font }} ({{ body_size }})
- **Data Labels:** {{ label_font }} ({{ label_size }})

### Logo & Branding

- **Logo Position:** {{ logo_position }}
- **Logo Image:** {{ logo_image_url }}
- **Company Colors:** {{ company_colors }}

{% if dashboard_platform == 'custom' %}
### CSS/Styling

```css
{{ custom_css }}
```
{% endif %}

---

## 9. Performance Requirements

### Load Time Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Initial Load** | {{ initial_load_target }} | Time to first visualization |
| **Filter Application** | {{ filter_apply_target }} | Time to update after filter change |
| **Data Refresh** | {{ data_refresh_target }} | Time to refresh all data |
| **Export** | {{ export_target }} | Time to generate export |

### Data Volume Handling

- **Expected Row Count:** {{ expected_row_count }}
- **Max Row Count:** {{ max_row_count }}
- **Aggregation Strategy:** {{ aggregation_strategy }}
- **Caching:** {{ caching_strategy }}

### Optimization Strategies

{% for optimization in performance_optimizations %}
- **{{ optimization.name }}**: {{ optimization.description }}
{% endfor %}

---

## 10. Access Control & Permissions

### User Roles & Permissions

| Role | View | Edit | Share | Export | Admin |
|------|------|------|-------|--------|-------|
{% for role in user_roles %}
| **{{ role.name }}** | {{ role.view }} | {{ role.edit }} | {{ role.share }} | {{ role.export }} | {{ role.admin }} |
{% endfor %}

### Row-Level Security

{% if has_row_level_security %}
**RLS Rules:**
{% for rls_rule in rls_rules %}
{{ loop.index }}. **{{ rls_rule.name }}**: {{ rls_rule.description }}
   - **Logic:** {{ rls_rule.logic }}
   - **Applies To:** {{ rls_rule.applies_to }}
{% endfor %}

{% if config.project.type == 'data-platform' %}
**Implementation:**
```sql
{{ rls_implementation_sql }}
```
{% endif %}
{% endif %}

### Sharing & Distribution

- **Public Access:** {{ public_access }}
- **Share Link:** {{ share_link_enabled }}
- **Embedding:** {{ embedding_enabled }}
- **Email Distribution:** {{ email_distribution }}
  - **Recipients:** {{ email_recipients }}
  - **Schedule:** {{ email_schedule }}

---

## 11. Export & Download Options

### Export Formats

{% for export_format in export_formats %}
- **{{ export_format.name }}**: {{ export_format.description }}
  - **Available To:** {{ export_format.available_to }}
  - **Size Limit:** {{ export_format.size_limit }}
{% endfor %}

### Scheduled Reports

{% if has_scheduled_reports %}
{% for report in scheduled_reports %}
**{{ loop.index }}. {{ report.name }}**
- **Frequency:** {{ report.frequency }}
- **Recipients:** {{ report.recipients }}
- **Format:** {{ report.format }}
- **Delivery Method:** {{ report.delivery_method }}
{% endfor %}
{% endif %}

---

## 12. Alerts & Notifications

{% if has_alerts %}
### Alert Rules

{% for alert in alerts %}
**{{ loop.index }}. {{ alert.name }}**
- **Condition:** {{ alert.condition }}
- **Threshold:** {{ alert.threshold }}
- **Notification Channel:** {{ alert.channel }}
- **Recipients:** {{ alert.recipients }}
- **Frequency:** {{ alert.frequency }}
{% endfor %}
{% endif %}

---

## 13. Testing Requirements

### Test Scenarios

{% for test in test_scenarios %}
{{ loop.index }}. **{{ test.name }}**: {{ test.description }}
   - **Expected Result:** {{ test.expected_result }}
{% endfor %}

### User Acceptance Criteria

{% for criterion in user_acceptance_criteria %}
- [ ] {{ criterion }}
{% endfor %}

---

## 14. Documentation Requirements

### User Guide

**Content to Include:**
{% for guide_section in user_guide_sections %}
- {{ guide_section }}
{% endfor %}

### Technical Documentation

{% for tech_doc in technical_documentation %}
- **{{ tech_doc.name }}**: {{ tech_doc.description }}
{% endfor %}

---

## 15. Implementation Checklist

**Data Preparation:**
- [ ] Create/validate data sources
- [ ] Test data refresh process
- [ ] Implement data quality checks
- [ ] Set up caching (if applicable)

**Dashboard Development:**
- [ ] Create dashboard structure
- [ ] Implement all visualizations
- [ ] Configure filters and parameters
- [ ] Set up calculated fields
- [ ] Implement interactivity (drill-downs, cross-filtering)
- [ ] Apply styling and branding

**Testing:**
- [ ] Test all visualizations with real data
- [ ] Test filters and parameters
- [ ] Test interactivity and drill-downs
- [ ] Performance testing (load time)
- [ ] User acceptance testing
- [ ] Cross-browser testing (for custom dashboards)

**Deployment:**
- [ ] Configure access control
- [ ] Set up row-level security (if applicable)
- [ ] Configure data refresh schedule
- [ ] Set up alerts (if applicable)
- [ ] Create user documentation
- [ ] Train users
- [ ] Deploy to production

**Post-Deployment:**
- [ ] Monitor performance
- [ ] Collect user feedback
- [ ] Iterate and improve

---

## 16. Next Steps

**For {{ config.roles.data_analyst or 'BI Developer' }}:**

1. Review this specification with stakeholders
2. Validate data sources and SQL queries
3. Create dashboard in {{ dashboard_platform }}
4. Implement all visualizations and filters
5. Apply styling and branding
6. Test dashboard with sample data
7. Conduct user acceptance testing
8. Deploy to production
9. Create handoff: `.claude/handoffs/dashboard-implementation-{{ dashboard_name }}.md`

**Estimated Implementation Time:** {{ estimated_hours }} hours

**Handoff To:**
- Users/stakeholders (for UAT)
- Documentation Engineer (for user guide)
- DevOps (for deployment configuration)

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
