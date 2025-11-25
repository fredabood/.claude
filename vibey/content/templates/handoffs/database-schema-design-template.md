---
id: database-schema-design
name: Database Schema Design
version: 1.0.0
from_agent: architecture-agent
to_agents:
- web-developer
- backend-engineer
purpose: Template for database schema design
variables:
- name: access_control_model
  type: string
  required: true
  description: Access Control Model value
- name: architecture_pattern
  type: string
  required: true
  description: Architecture Pattern value
- name: ascii_erd
  type: string
  required: true
  description: Ascii Erd value
- name: author_name
  type: string
  required: true
  description: Author Name value
- name: backup_frequency
  type: string
  required: true
  description: Backup Frequency value
- name: backup_location
  type: string
  required: true
  description: Backup Location value
- name: backup_retention
  type: string
  required: true
  description: Backup Retention value
- name: backup_tool
  type: string
  required: true
  description: Backup Tool value
- name: business_context
  type: string
  required: true
  description: Business Context value
- name: cache_layer
  type: string
  required: true
  description: Cache Layer value
- name: cache_ttl
  type: string
  required: true
  description: Cache Ttl value
- name: check
  type: string
  required: true
  description: Check value
- name: compression_algorithm
  type: string
  required: true
  description: Compression Algorithm value
- name: connection_pool_config
  type: string
  required: true
  description: Connection Pool Config value
- name: creation_date
  type: string
  required: true
  description: Creation Date value
description: Template for database schema design
---

# Database Schema Design: {{ database_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.database_architect or 'Database Architect / Data Engineer' }}
**To:** {{ config.roles.backend_engineer or 'Backend Engineer / Database Administrator' }}
**Purpose:** Comprehensive database schema design specification
**Related Workflow:** Database Design Workflow

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Database Name** | {{ database_name }} |
| **Database Type** | {{ database_type }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ creation_date }} |
| **Database Technology** | {{ config.technology_stack.database or 'PostgreSQL/MySQL/MongoDB/etc.' }} |
| **Status** | {{ document_status }} |
| **Version** | {{ schema_version }} |

---

## 1. Schema Overview

### Purpose

**Business Context:** {{ business_context }}

**Data Domain:** {{ data_domain }}

**Primary Use Cases:**
{% for use_case in primary_use_cases %}
- {{ use_case }}
{% endfor %}

### Database Technology

**Database System:** {{ config.technology_stack.database }}
**Database Type:** {{ database_type }}

{% if database_type == 'relational' %}
**RDBMS:** {{ config.technology_stack.database }}
**SQL Dialect:** {{ sql_dialect }}
**Version:** {{ database_version }}

{% elif database_type == 'document' %}
**Document Store:** {{ config.technology_stack.database }}
**Schema Flexibility:** {{ schema_flexibility }}

{% elif database_type == 'graph' %}
**Graph Database:** {{ config.technology_stack.database }}
**Query Language:** {{ graph_query_language }}

{% elif database_type == 'timeseries' %}
**Time-Series Database:** {{ config.technology_stack.database }}
**Retention Policy:** {{ retention_policy }}

{% elif database_type == 'key_value' %}
**Key-Value Store:** {{ config.technology_stack.database }}
**Persistence:** {{ persistence_mode }}

{% elif database_type == 'columnar' %}
**Columnar Store:** {{ config.technology_stack.database }}
**Compression:** {{ compression_algorithm }}
{% endif %}

### Architecture Pattern

**Pattern:** {{ architecture_pattern }}
**Sharding Strategy:** {{ sharding_strategy }}
**Replication:** {{ replication_strategy }}
**Partitioning:** {{ partitioning_strategy }}

---

## 2. Entity/Table Definitions

{% if database_type == 'relational' %}
### Tables

{% for table in tables %}
### {{ loop.index }}. {{ table.name }}

**Purpose:** {{ table.purpose }}
**Estimated Rows:** {{ table.estimated_rows }}
**Growth Rate:** {{ table.growth_rate }}

```sql
CREATE TABLE {{ table.name }} (
{% for column in table.columns %}
  {{ column.name }} {{ column.data_type }}{% if not column.nullable %} NOT NULL{% endif %}{% if column.default %} DEFAULT {{ column.default }}{% endif %}{% if column.comment %} COMMENT '{{ column.comment }}'{% endif %},
{% endfor %}
{% if table.primary_key %}
  PRIMARY KEY ({{ table.primary_key }}),
{% endif %}
{% for unique_key in table.unique_keys %}
  UNIQUE ({{ unique_key }}),
{% endfor %}
{% for foreign_key in table.foreign_keys %}
  FOREIGN KEY ({{ foreign_key.column }}) REFERENCES {{ foreign_key.ref_table }}({{ foreign_key.ref_column }}){% if foreign_key.on_delete %} ON DELETE {{ foreign_key.on_delete }}{% endif %},
{% endfor %}
{% if table.check_constraints %}
{% for check in table.check_constraints %}
  CHECK ({{ check }}),
{% endfor %}
{% endif %}
{% for index in table.indexes %}
  INDEX {{ index.name }} ({{ index.columns }}){% if index.type %} USING {{ index.type }}{% endif %},
{% endfor %}
){% if table.engine %} ENGINE={{ table.engine }}{% endif %}{% if table.partition_by %} PARTITION BY {{ table.partition_by }}{% endif %};
```

**Column Details:**

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
{% for column in table.columns %}
| `{{ column.name }}` | {{ column.data_type }} | {{ column.nullable and 'Yes' or 'No' }} | {{ column.default or 'NULL' }} | {{ column.description }} |
{% endfor %}

**Indexes:**
{% for index in table.indexes %}
- **{{ index.name }}**: {{ index.type or 'BTREE' }} on `{{ index.columns }}`
  - **Purpose:** {{ index.purpose }}
  - **Cardinality:** {{ index.cardinality }}
{% endfor %}

---

{% endfor %}

{% elif database_type == 'document' %}
### Collections

{% for collection in collections %}
### {{ loop.index }}. {{ collection.name }}

**Purpose:** {{ collection.purpose }}
**Estimated Documents:** {{ collection.estimated_docs }}
**Average Document Size:** {{ collection.avg_doc_size }}

**Schema (JSON):**
```json
{
{% for field in collection.schema_fields %}
  "{{ field.name }}": {{ field.example_value }},  // {{ field.type }} - {{ field.description }}
{% endfor %}
}
```

**Validation Rules:**
```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": {{ collection.required_fields }},
    "properties": {
{% for field in collection.schema_fields %}
      "{{ field.name }}": {
        "bsonType": "{{ field.bson_type }}",
        "description": "{{ field.description }}"
      }{% if not loop.last %},{% endif %}
{% endfor %}
    }
  }
}
```

**Indexes:**
{% for index in collection.indexes %}
- **{{ index.name }}**: {{ index.type }} on `{{ index.fields }}`
  - **Unique:** {{ index.unique }}
  - **Sparse:** {{ index.sparse }}
{% endfor %}

---

{% endfor %}

{% elif database_type == 'graph' %}
### Node Types

{% for node_type in node_types %}
**{{ loop.index }}. {{ node_type.name }}**

**Label:** `{{ node_type.label }}`
**Purpose:** {{ node_type.purpose }}
**Estimated Count:** {{ node_type.estimated_count }}

**Properties:**
| Property | Type | Required | Description |
|----------|------|----------|-------------|
{% for property in node_type.properties %}
| `{{ property.name }}` | {{ property.type }} | {{ property.required and 'Yes' or 'No' }} | {{ property.description }} |
{% endfor %}

**Indexes:**
{% for index in node_type.indexes %}
- **{{ index.type }}** on `{{ index.property }}`
{% endfor %}

---

{% endfor %}

### Relationship Types

{% for relationship in relationship_types %}
**{{ loop.index }}. {{ relationship.name }}**

**Type:** `{{ relationship.type }}`
**Direction:** {{ relationship.from_node }} → {{ relationship.to_node }}
**Cardinality:** {{ relationship.cardinality }}
**Purpose:** {{ relationship.purpose }}

**Properties:**
| Property | Type | Required | Description |
|----------|------|----------|-------------|
{% for property in relationship.properties %}
| `{{ property.name }}` | {{ property.type }} | {{ property.required and 'Yes' or 'No' }} | {{ property.description }} |
{% endfor %}

**Example:**
```cypher
({{ relationship.from_node }})-[{{ relationship.variable }}:{{ relationship.type }}]->({{ relationship.to_node }})
```

---

{% endfor %}
{% endif %}

---

## 3. Relationships & Constraints

{% if database_type == 'relational' %}
### Foreign Key Relationships

```
{{ erd_diagram_ascii }}
```

**Relationship Details:**

{% for fk in foreign_key_relationships %}
**{{ loop.index }}. {{ fk.from_table }}.{{ fk.from_column }} → {{ fk.to_table }}.{{ fk.to_column }}**
- **Cardinality:** {{ fk.cardinality }}
- **On Delete:** {{ fk.on_delete }}
- **On Update:** {{ fk.on_update }}
- **Business Rule:** {{ fk.business_rule }}
{% endfor %}

### Constraints

**Unique Constraints:**
{% for unique in unique_constraints %}
- **{{ unique.table }}.{{ unique.columns }}**: {{ unique.purpose }}
{% endfor %}

**Check Constraints:**
{% for check in check_constraints %}
- **{{ check.table }}**: {{ check.constraint }}
  - **Purpose:** {{ check.purpose }}
{% endfor %}

**NOT NULL Constraints:**
{% for not_null in not_null_constraints %}
- **{{ not_null.table }}.{{ not_null.column }}**: {{ not_null.rationale }}
{% endfor %}

{% elif database_type == 'document' %}
### Document References

{% for reference in document_references %}
**{{ reference.from_collection }} → {{ reference.to_collection }}**
- **Reference Field:** `{{ reference.field }}`
- **Reference Type:** {{ reference.type }}
- **Cascade:** {{ reference.cascade }}
{% endfor %}

### Embedded Documents

{% for embedded in embedded_documents %}
**{{ embedded.parent_collection }}.{{ embedded.field }}**
- **Type:** {{ embedded.type }}
- **Rationale:** {{ embedded.rationale }}
{% endfor %}

{% elif database_type == 'graph' %}
### Graph Patterns

{% for pattern in graph_patterns %}
**Pattern {{ loop.index }}: {{ pattern.name }}**
```cypher
{{ pattern.cypher_pattern }}
```
- **Purpose:** {{ pattern.purpose }}
- **Example:** {{ pattern.example }}
{% endfor %}
{% endif %}

---

## 4. Indexes & Query Optimization

### Primary Indexes

{% for index in primary_indexes %}
**{{ loop.index }}. {{ index.name }}**
- **Table/Collection:** {{ index.table }}
- **Columns/Fields:** {{ index.columns }}
- **Type:** {{ index.type }}
- **Purpose:** {{ index.purpose }}
- **Cardinality:** {{ index.cardinality }}
- **Selectivity:** {{ index.selectivity }}
- **Size Estimate:** {{ index.size_estimate }}
{% endfor %}

### Secondary Indexes

{% for index in secondary_indexes %}
**{{ loop.index }}. {{ index.name }}**
- **Table/Collection:** {{ index.table }}
- **Columns/Fields:** {{ index.columns }}
- **Type:** {{ index.type }}
- **Query Pattern:** {{ index.query_pattern }}
{% endfor %}

### Composite Indexes

{% for index in composite_indexes %}
**{{ loop.index }}. {{ index.name }}**
- **Table/Collection:** {{ index.table }}
- **Columns/Fields:** {{ index.columns }}
- **Column Order Rationale:** {{ index.order_rationale }}
- **Covering Index:** {{ index.is_covering }}
{% endfor %}

### Query Patterns

{% for query_pattern in query_patterns %}
**Pattern {{ loop.index }}: {{ query_pattern.name }}**

**Query:**
```{{ database_type == 'graph' and 'cypher' or 'sql' }}
{{ query_pattern.query }}
```

**Indexes Used:** {{ query_pattern.indexes_used }}
**Expected Performance:** {{ query_pattern.expected_performance }}
**Execution Plan:** {{ query_pattern.execution_plan }}

---

{% endfor %}

---

## 5. Data Integrity & Validation

### Business Rules

{% for rule in business_rules %}
**{{ loop.index }}. {{ rule.name }}**
- **Description:** {{ rule.description }}
- **Enforcement:** {{ rule.enforcement }}
- **Implementation:** {{ rule.implementation }}
{% endfor %}

### Data Quality Checks

| Check | Rule | Enforcement Level | Action on Failure |
|-------|------|-------------------|-------------------|
{% for check in data_quality_checks %}
| **{{ check.name }}** | {{ check.rule }} | {{ check.enforcement_level }} | {{ check.action_on_failure }} |
{% endfor %}

{% if database_type == 'relational' %}
### Validation SQL

```sql
-- Check for constraint violations
{% for validation in validation_queries %}
-- {{ validation.name }}
{{ validation.sql }}

{% endfor %}
```
{% endif %}

---

## 6. Denormalization & Optimization

### Denormalized Fields

{% for denorm in denormalized_fields %}
**{{ loop.index }}. {{ denorm.table }}.{{ denorm.field }}**
- **Source:** {{ denorm.source_table }}.{{ denorm.source_field }}
- **Rationale:** {{ denorm.rationale }}
- **Sync Strategy:** {{ denorm.sync_strategy }}
- **Trade-off:** {{ denorm.tradeoff }}
{% endfor %}

### Materialized Views

{% for mv in materialized_views %}
**{{ loop.index }}. {{ mv.name }}**

**Purpose:** {{ mv.purpose }}
**Refresh Strategy:** {{ mv.refresh_strategy }}
**Refresh Frequency:** {{ mv.refresh_frequency }}

```sql
{{ mv.definition }}
```

**Estimated Speedup:** {{ mv.estimated_speedup }}

---

{% endfor %}

### Caching Strategy

**Cache Layer:** {{ cache_layer }}
**TTL:** {{ cache_ttl }}

**Cached Queries:**
{% for cached_query in cached_queries %}
- **{{ cached_query.name }}**: {{ cached_query.cache_duration }}
  - **Invalidation:** {{ cached_query.invalidation_strategy }}
{% endfor %}

---

## 7. Partitioning & Sharding

{% if has_partitioning %}
### Partitioning Strategy

**Partitioning Type:** {{ partitioning_type }}
**Partitioning Key:** {{ partitioning_key }}
**Partition Count:** {{ partition_count }}

**Partitioned Tables:**
{% for partitioned_table in partitioned_tables %}
**{{ partitioned_table.name }}**
```sql
{{ partitioned_table.partition_ddl }}
```
- **Partition Size:** {{ partitioned_table.partition_size }}
- **Retention Policy:** {{ partitioned_table.retention_policy }}
{% endfor %}
{% endif %}

{% if has_sharding %}
### Sharding Strategy

**Sharding Type:** {{ sharding_type }}
**Shard Key:** {{ shard_key }}
**Number of Shards:** {{ num_shards }}

**Shard Distribution:**
{% for shard in shard_distribution %}
- **Shard {{ loop.index }}**: {{ shard.range }} ({{ shard.estimated_size }})
{% endfor %}

**Rebalancing:** {{ rebalancing_strategy }}
{% endif %}

---

## 8. Data Migration & Seeding

### Migration Strategy

**Migration Tool:** {{ migration_tool }}
**Migration Order:** {{ migration_order }}

**Migration Scripts:**
{% for migration in migrations %}
**{{ migration.version }}: {{ migration.name }}**
```{{ database_type == 'graph' and 'cypher' or 'sql' }}
{{ migration.up_script }}
```

**Rollback:**
```{{ database_type == 'graph' and 'cypher' or 'sql' }}
{{ migration.down_script }}
```

---

{% endfor %}

### Seed Data

**Seed Data Purpose:** {{ seed_data_purpose }}

**Seed Scripts:**
{% for seed in seed_scripts %}
**{{ seed.name }}**
```{{ database_type == 'graph' and 'cypher' or 'sql' }}
{{ seed.script }}
```
{% endfor %}

---

## 9. Performance Considerations

### Capacity Planning

**Current Scale:**
- **Total Rows/Documents:** {{ total_rows }}
- **Total Size:** {{ total_size }}
- **Daily Growth:** {{ daily_growth }}

**1-Year Projection:**
- **Projected Rows/Documents:** {{ projected_rows_1year }}
- **Projected Size:** {{ projected_size_1year }}
- **Storage Requirements:** {{ storage_requirements_1year }}

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
{% for target in performance_targets %}
| **{{ target.metric }}** | {{ target.target }} | {{ target.measurement }} |
{% endfor %}

### Query Performance

**Top Queries by Frequency:**
{% for query in top_queries %}
{{ loop.index }}. **{{ query.name }}** ({{ query.frequency }})
   - **Current Performance:** {{ query.current_performance }}
   - **Target Performance:** {{ query.target_performance }}
   - **Optimization Status:** {{ query.optimization_status }}
{% endfor %}

---

## 10. Backup & Recovery

### Backup Strategy

**Backup Tool:** {{ backup_tool }}
**Backup Frequency:** {{ backup_frequency }}
**Backup Retention:** {{ backup_retention }}
**Backup Location:** {{ backup_location }}

**Backup Schedule:**
{% for backup_schedule_item in backup_schedule %}
- **{{ backup_schedule_item.type }}**: {{ backup_schedule_item.schedule }}
{% endfor %}

### Recovery Procedures

**RTO (Recovery Time Objective):** {{ rto }}
**RPO (Recovery Point Objective):** {{ rpo }}

**Recovery Steps:**
{% for recovery_step in recovery_steps %}
{{ loop.index }}. {{ recovery_step }}
{% endfor %}

---

## 11. Security & Access Control

### Authentication

**Authentication Method:** {{ db_authentication_method }}

{% if db_authentication_method == 'database_users' %}
**Database Users:**
{% for user in database_users %}
- **{{ user.username }}**: {{ user.role }}
  - **Password Policy:** {{ user.password_policy }}
{% endfor %}

{% elif db_authentication_method == 'application_level' %}
**Application Connection:**
- **Service Account:** {{ service_account }}
- **Connection Pool:** {{ connection_pool_config }}
{% endif %}

### Authorization

**Access Control Model:** {{ access_control_model }}

**Permissions:**
| User/Role | Permissions | Scope |
|-----------|-------------|-------|
{% for permission in permissions %}
| **{{ permission.user_or_role }}** | {{ permission.permissions }} | {{ permission.scope }} |
{% endfor %}

{% if database_type == 'relational' %}
**Row-Level Security:**
{% for rls in row_level_security %}
- **Table:** {{ rls.table }}
  - **Policy:** {{ rls.policy }}
  - **Applies To:** {{ rls.applies_to }}
{% endfor %}
{% endif %}

### Encryption

**Encryption at Rest:** {{ encryption_at_rest }}
**Encryption in Transit:** {{ encryption_in_transit }}
**Key Management:** {{ key_management }}

---

## 12. Monitoring & Observability

### Key Metrics

{% for metric in monitoring_metrics %}
- **{{ metric.name }}**: {{ metric.description }}
  - **Alert Threshold:** {{ metric.alert_threshold }}
  - **Action:** {{ metric.action }}
{% endfor %}

### Slow Query Monitoring

**Slow Query Threshold:** {{ slow_query_threshold }}
**Logging:** {{ slow_query_logging }}
**Analysis Tool:** {{ slow_query_analysis_tool }}

### Database Health Checks

{% for health_check in health_checks %}
- **{{ health_check.name }}**: {{ health_check.frequency }}
  - **Check:** {{ health_check.check }}
  - **Alert On:** {{ health_check.alert_condition }}
{% endfor %}

---

## 13. Implementation Checklist

**Schema Creation:**
{% for schema_task in schema_tasks %}
- [ ] {{ schema_task }}
{% endfor %}

**Data Migration:**
{% for migration_task in migration_tasks %}
- [ ] {{ migration_task }}
{% endfor %}

**Testing:**
{% for test_task in test_tasks %}
- [ ] {{ test_task }}
{% endfor %}

**Deployment:**
{% for deployment_task in deployment_tasks %}
- [ ] {{ deployment_task }}
{% endfor %}

---

## 14. Next Steps

**For {{ config.roles.backend_engineer or 'Implementation Team' }}:**

1. Review schema design with stakeholders
2. Create database migration scripts
3. Implement schema in {{ config.technology_stack.database }}
4. Create indexes and constraints
5. Seed initial data
6. Performance test with realistic data volumes
7. Set up monitoring and alerting
8. Deploy to {{ first_environment }} environment
9. Create handoff: `.claude/handoffs/database-implementation-{{ database_name }}.md`

**Estimated Implementation Time:** {{ estimated_hours }} hours

---

## Appendix: ERD / Schema Diagram

**Diagram Location:** {{ diagram_location }}

{% if has_ascii_erd %}
```
{{ ascii_erd }}
```
{% endif %}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
