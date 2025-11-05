# Infrastructure Design Document: {{ project_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.devops_engineer or 'DevOps Engineer' }}
**To:** Implementation Team, Security Reviewer
**Purpose:** Document infrastructure-as-code design before implementation
**Related Workflow:** Infrastructure Setup Workflow - Step 3

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Project** | {{ project_name }} |
| **Created By** | {{ author_name }} |
| **Date:** | {{ creation_date }} |
| **Status** | {{ document_status }} |
| **Reviewers** | {{ reviewers_list }} |
| **Version** | {{ version_number }} |

---

## 1. Infrastructure Overview

### Purpose & Scope
{{ infrastructure_purpose }}

### Environments

| Environment | Purpose | Users | Cost Target |
|-------------|---------|-------|-------------|
{% for env in environments %}
| **{{ env.name }}** | {{ env.purpose }} | {{ env.users }} | {{ env.cost_target }} |
{% endfor %}

### High-Level Architecture
{{ high_level_architecture_description }}

**Architecture Diagram:**
```
{{ architecture_diagram }}
```

---

## 2. Cloud Provider & Platform

**Cloud Provider:** {{ config.cloud_provider or 'AWS/Azure/GCP' }}
**IaC Tool:** {{ config.infrastructure.iac_tool or 'Terraform' }}
**Primary Region:** {{ primary_region }}
**Secondary Region (DR):** {{ secondary_region }}

{% if config.cloud_provider == 'aws' %}
### AWS Services Used
{% for service in aws_services %}
- **{{ service.name }}:** {{ service.purpose }}
{% endfor %}

{% elif config.cloud_provider == 'azure' %}
### Azure Services Used
{% for service in azure_services %}
- **{{ service.name }}:** {{ service.purpose }}
{% endfor %}

{% elif config.cloud_provider == 'gcp' %}
### GCP Services Used
{% for service in gcp_services %}
- **{{ service.name }}:** {{ service.purpose }}
{% endfor %}
{% endif %}

---

## 3. Resource Hierarchy

### Compute Resources

{% if config.project.type == 'web-app' or config.project.type == 'api' %}
**Application Servers:**

| Resource | Environment | Type | Instance Size | Auto-scaling | High Availability |
|----------|-------------|------|---------------|--------------|-------------------|
{% for server in application_servers %}
| {{ server.name }} | {{ server.environment }} | {{ server.type }} | {{ server.size }} | {{ server.autoscaling }} | {{ server.ha }} |
{% endfor %}

{% if deployment_target == 'kubernetes' %}
**Kubernetes Configuration:**
- **Cluster Type:** {{ k8s_cluster_type }}
- **Node Pools:** {{ k8s_node_pools }}
- **Pod Autoscaling:** {{ k8s_pod_autoscaling }}
- **Cluster Autoscaling:** {{ k8s_cluster_autoscaling }}

{% elif deployment_target == 'serverless' %}
**Serverless Configuration:**
{% if config.cloud_provider == 'aws' %}
- **Lambda Functions:** {{ lambda_functions_count }}
- **Memory Allocation:** {{ lambda_memory }}
- **Timeout:** {{ lambda_timeout }}
- **Concurrency Limits:** {{ lambda_concurrency }}
{% elif config.cloud_provider == 'azure' %}
- **Azure Functions:** {{ azure_functions_count }}
- **App Service Plan:** {{ azure_app_service_plan }}
- **Runtime:** {{ azure_functions_runtime }}
{% elif config.cloud_provider == 'gcp' %}
- **Cloud Functions:** {{ gcp_functions_count }}
- **Runtime:** {{ gcp_functions_runtime }}
- **Max Instances:** {{ gcp_max_instances }}
{% endif %}
{% endif %}

{% elif config.project.type == 'data-platform' %}
**Data Processing Resources:**

| Resource | Environment | Purpose | Instance Type | Workers | Auto-scale |
|----------|-------------|---------|---------------|---------|------------|
{% for resource in data_processing_resources %}
| {{ resource.name }} | {{ resource.environment }} | {{ resource.purpose }} | {{ resource.instance_type }} | {{ resource.workers }} | {{ resource.autoscale }} |
{% endfor %}

{% elif config.project.type == 'ml' %}
**ML Training Resources:**

| Resource | Environment | Purpose | Instance Type | GPU | Spot/On-Demand |
|----------|-------------|---------|---------------|-----|----------------|
{% for resource in ml_training_resources %}
| {{ resource.name }} | {{ resource.environment }} | {{ resource.purpose }} | {{ resource.instance_type }} | {{ resource.gpu }} | {{ resource.pricing }} |
{% endfor %}

**ML Inference Resources:**
{{ ml_inference_resources_description }}
{% endif %}

### Storage Resources

{% if config.technology_stack.database %}
**Databases:**

| Database | Environment | Engine | Size | Backup | Multi-AZ |
|----------|-------------|--------|------|--------|----------|
{% for db in databases %}
| {{ db.name }} | {{ db.environment }} | {{ db.engine }} | {{ db.size }} | {{ db.backup }} | {{ db.multi_az }} |
{% endfor %}
{% endif %}

**Object Storage:**

| Bucket/Container | Purpose | Lifecycle Policy | Versioning | Encryption |
|------------------|---------|------------------|------------|------------|
{% for storage in object_storage %}
| {{ storage.name }} | {{ storage.purpose }} | {{ storage.lifecycle }} | {{ storage.versioning }} | {{ storage.encryption }} |
{% endfor %}

### Networking

**VPC/VNet Configuration:**
- **CIDR Blocks:** {{ vpc_cidr_blocks }}
- **Subnets:** {{ subnet_configuration }}
- **NAT Gateway:** {{ nat_gateway_configuration }}
- **VPN/Direct Connect:** {{ vpn_configuration }}

**Load Balancers:**

| Load Balancer | Type | Targets | SSL/TLS | Health Checks |
|---------------|------|---------|---------|---------------|
{% for lb in load_balancers %}
| {{ lb.name }} | {{ lb.type }} | {{ lb.targets }} | {{ lb.ssl }} | {{ lb.health_checks }} |
{% endfor %}

---

## 4. {{ config.infrastructure.iac_tool }} Structure

### Directory Layout

{% if config.infrastructure.iac_tool == 'terraform' %}
```
terraform/
├── providers.tf                 # Provider configurations
├── versions.tf                  # Version constraints
├── variables.tf                 # Global variables
├── outputs.tf                   # Global outputs
├── modules/
{% for module in terraform_modules %}
│   ├── {{ module.name }}/       # {{ module.description }}
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
{% endfor %}
└── environments/
    ├── dev/
    │   ├── main.tf
    │   ├── terraform.tfvars
    │   └── backend.hcl
    ├── staging/
    │   ├── main.tf
    │   ├── terraform.tfvars
    │   └── backend.hcl
    └── prod/
        ├── main.tf
        ├── terraform.tfvars
        └── backend.hcl
```

{% elif config.infrastructure.iac_tool == 'pulumi' %}
```
infrastructure/
├── Pulumi.yaml                  # Pulumi project file
├── __main__.py                  # Main program (or index.ts for TypeScript)
├── requirements.txt             # Python dependencies (or package.json for TS)
├── components/
{% for component in pulumi_components %}
│   ├── {{ component.name }}.py  # {{ component.description }}
{% endfor %}
└── stacks/
    ├── Pulumi.dev.yaml
    ├── Pulumi.staging.yaml
    └── Pulumi.prod.yaml
```

{% elif config.infrastructure.iac_tool == 'cloudformation' %}
```
cloudformation/
├── templates/
{% for template in cloudformation_templates %}
│   ├── {{ template.name }}.yaml # {{ template.description }}
{% endfor %}
└── parameters/
    ├── dev.json
    ├── staging.json
    └── prod.json
```
{% endif %}

### Module/Component Descriptions

{% for module in iac_modules %}
**{{ loop.index }}. {{ module.name }}:**
- Purpose: {{ module.purpose }}
- Resources Created: {{ module.resources }}
- Outputs: {{ module.outputs }}

{% endfor %}

### Module Dependencies

```
{{ module_dependency_graph }}
```

**Rationale:** {{ module_dependency_rationale }}

---

## 5. State Management

{% if config.infrastructure.iac_tool == 'terraform' %}
### Remote Backend Configuration

**Backend Type:** {{ terraform_backend_type }}

| Setting | Value |
|---------|-------|
{% for setting in terraform_backend_settings %}
| **{{ setting.name }}** | {{ setting.value }} |
{% endfor %}

**Backend Configuration Files:**

```hcl
# environments/dev/backend.hcl
{{ dev_backend_config }}
```

```hcl
# environments/prod/backend.hcl
{{ prod_backend_config }}
```

### State Locking

{{ state_locking_description }}

### State Backup

{{ state_backup_strategy }}

{% elif config.infrastructure.iac_tool == 'pulumi' %}
### State Backend

**Backend:** {{ pulumi_backend }}
**Encryption:** {{ pulumi_encryption }}
**Access Control:** {{ pulumi_access_control }}

{% elif config.infrastructure.iac_tool == 'cloudformation' %}
### Stack Management

**Stack Naming Convention:** {{ stack_naming_convention }}
**Change Sets:** {{ change_sets_policy }}
**Stack Policies:** {{ stack_policies }}
{% endif %}

---

## 6. Variable Structure

### Global Variables

{% if config.infrastructure.iac_tool == 'terraform' %}
```hcl
{{ global_variables_hcl }}
```

{% elif config.infrastructure.iac_tool == 'pulumi' %}
```{{ config.technology_stack.backend.language }}
{{ global_variables_pulumi }}
```
{% endif %}

### Environment-Specific Variables

{% for env in environments %}
**{{ env.name }} Environment:**
```
{{ env.variables }}
```

{% endfor %}

### Sensitive Variables (Not in Git)

**Storage Methods:**
{% for method in sensitive_var_storage %}
- {{ method.name }}: {{ method.description }}
{% endfor %}

**Sensitive Variables:**
{% for var in sensitive_variables %}
- `{{ var.name }}` - {{ var.description }}
{% endfor %}

---

## 7. CI/CD Pipeline Design

### Pipeline Stages

**Pull Request Workflow:**
{% for stage in pr_pipeline_stages %}
{{ loop.index }}. **{{ stage.name }}** - {{ stage.description }}
{% endfor %}

**Merge to Main Workflow:**
{% for stage in merge_pipeline_stages %}
{{ loop.index }}. **{{ stage.name }}** - {{ stage.description }}
{% endfor %}

### Deployment Gates

| Environment | Approval Required | Tests Required | Notifications |
|-------------|-------------------|----------------|---------------|
{% for env in deployment_gates %}
| **{{ env.name }}** | {{ env.approval_required }} | {{ env.tests_required }} | {{ env.notifications }} |
{% endfor %}

### Approval Process (Production)

**Approvers:**
{% for approver in prod_approvers %}
- {{ approver.role }} ({{ approver.required and 'required' or 'optional' }})
{% endfor %}

**Approval Checklist:**
{% for item in approval_checklist %}
- [ ] {{ item }}
{% endfor %}

---

## 8. Secrets Management

### Secrets Storage Strategy

| Secret Type | Storage Method | Access Method |
|-------------|----------------|---------------|
{% for secret_type in secret_types %}
| **{{ secret_type.type }}** | {{ secret_type.storage }} | {{ secret_type.access }} |
{% endfor %}

{% if config.cloud_provider == 'aws' %}
### AWS Secrets Manager Configuration

{{ aws_secrets_manager_config }}

{% elif config.cloud_provider == 'azure' %}
### Azure Key Vault Configuration

{{ azure_key_vault_config }}

{% elif config.cloud_provider == 'gcp' %}
### GCP Secret Manager Configuration

{{ gcp_secret_manager_config }}
{% endif %}

### Secret Rotation Policy

{% for policy in secret_rotation_policies %}
- **{{ policy.secret_type }}:** Rotate every {{ policy.frequency }}
{% endfor %}

---

## 9. IAM & Access Control

### User/Group Structure

| Group/Role | Members | Purpose | Permissions |
|------------|---------|---------|-------------|
{% for group in iam_groups %}
| {{ group.name }} | {{ group.members }} | {{ group.purpose }} | {{ group.permissions }} |
{% endfor %}

### Resource-Level Permissions

{{ resource_permissions_description }}

### Service Accounts / Service Principals

| Service Account | Purpose | Permissions |
|-----------------|---------|-------------|
{% for sa in service_accounts %}
| {{ sa.name }} | {{ sa.purpose }} | {{ sa.permissions }} |
{% endfor %}

{% if config.infrastructure.iac_tool == 'terraform' %}
### {{ config.infrastructure.iac_tool }} IAM Configuration

```hcl
{{ iam_configuration_example }}
```
{% endif %}

---

## 10. Monitoring & Alerting

### Monitoring Strategy

**Metrics to Monitor:**
{% for metric in monitoring_metrics %}
- {{ metric }}
{% endfor %}

**Monitoring Tools:**
{% for tool in monitoring_tools %}
- **{{ tool.name }}:** {{ tool.purpose }}
{% endfor %}

### Alerting Rules

| Alert | Condition | Severity | Notification |
|-------|-----------|----------|--------------|
{% for alert in alerting_rules %}
| **{{ alert.name }}** | {{ alert.condition }} | {{ alert.severity }} | {{ alert.notification }} |
{% endfor %}

### Cost Monitoring

**Cost Tracking:**
{{ cost_tracking_strategy }}

**Cost Alerts:**
{% for alert in cost_alerts %}
- {{ alert }}
{% endfor %}

---

## 11. Security Configuration

### Network Security

**Firewall Rules:**
{% for rule in firewall_rules %}
- {{ rule.description }}: {{ rule.configuration }}
{% endfor %}

**Security Groups/NSGs:**
{{ security_groups_configuration }}

### Encryption

**Data at Rest:**
- **Databases:** {{ database_encryption }}
- **Object Storage:** {{ storage_encryption }}
- **Volumes:** {{ volume_encryption }}

**Data in Transit:**
- **TLS/SSL:** {{ tls_configuration }}
- **VPN:** {{ vpn_encryption }}

### Compliance

**Compliance Requirements:**
{% for requirement in compliance_requirements %}
- {{ requirement }}
{% endfor %}

**Audit Logging:**
{{ audit_logging_configuration }}

---

## 12. Disaster Recovery & Backup

### Backup Strategy

**Backup Schedule:**
{% for backup in backup_schedules %}
- **{{ backup.resource }}:** {{ backup.frequency }} (Retention: {{ backup.retention }})
{% endfor %}

**Backup Storage:**
{{ backup_storage_configuration }}

### Disaster Recovery Plan

**RTO (Recovery Time Objective):** {{ rto }}
**RPO (Recovery Point Objective):** {{ rpo }}

**Recovery Steps:**
{% for step in dr_recovery_steps %}
{{ loop.index }}. **{{ step.scenario }}:** {{ step.steps }} ({{ step.duration }})
{% endfor %}

### Disaster Recovery Testing

- **{{ dr_testing_frequency }}:** {{ dr_testing_description }}

---

## 13. Cost Estimation

### Environment Cost Breakdown

{% for env in cost_breakdown %}
**{{ env.name }} Environment:**

| Resource | Quantity | Unit Cost | Usage | Total/Month |
|----------|----------|-----------|-------|-------------|
{% for resource in env.resources %}
| {{ resource.name }} | {{ resource.quantity }} | {{ resource.unit_cost }} | {{ resource.usage }} | {{ resource.total }} |
{% endfor %}
| **Total {{ env.name }}** | | | | **{{ env.total }}** |

{% endfor %}

**Grand Total:** {{ grand_total_cost }}/month

### Cost Optimization Strategies

{% for strategy in cost_optimization_strategies %}
{{ loop.index }}. **{{ strategy.name }}:** {{ strategy.description }}
{% endfor %}

---

## 14. Timeline & Milestones

| Milestone | Deliverable | Duration | Target Date | Status |
|-----------|------------|----------|-------------|---------|
{% for milestone in infrastructure_milestones %}
| {{ milestone.name }} | {{ milestone.deliverable }} | {{ milestone.duration }} | {{ milestone.target_date }} | {{ milestone.status }} |
{% endfor %}

**Total Timeline:** {{ total_timeline }}

---

## 15. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
{% for risk in infrastructure_risks %}
| **{{ risk.description }}** | {{ risk.probability }} | {{ risk.impact }} | {{ risk.mitigation }} |
{% endfor %}

---

## 16. Approval & Sign-Off

### Required Approvals

{% for approval in required_approvals %}
- [ ] **{{ approval.role }}:** {{ approval.approval_criteria }}
{% endfor %}

### Design Approved

**Approved By:** _________________________
**Date:** _________________________
**Comments:** _________________________

---

## Appendix: Resource Tagging Strategy

**Required Tags:**
{% for tag in required_tags %}
- `{{ tag.name }}`: {{ tag.description }}
{% endfor %}

**Tagging Example:**
```
{{ tagging_example }}
```

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
