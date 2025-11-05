# Workflow: Infrastructure Setup & Deployment

**Workflow ID:** Infrastructure Setup
**Purpose:** End-to-end infrastructure provisioning using Infrastructure-as-Code across multiple environments
**Duration:** 12-18 days (2.5-3.5 weeks)
**Complexity:** High

---

## Overview

This workflow orchestrates infrastructure-as-code (IaC) deployment across multiple environments (dev, staging, production). It ensures systematic, repeatable, and secure infrastructure provisioning with proper testing and documentation.

**Use Cases:**
- Initial cloud infrastructure setup
- Multi-environment infrastructure (dev/staging/prod)
{% if config.iac_tool %}- {{ config.iac_tool }} module deployment{% else %}- IaC module deployment{% endif %}
- CI/CD pipeline creation
- Infrastructure updates and migrations
{% if config.cloud_provider %}- {{ config.cloud_provider }} resource provisioning{% endif %}

**Prerequisites:**
{% if config.cloud_provider %}- {{ config.cloud_provider }} account access{% else %}- Cloud provider account access{% endif %}
{% if config.iac_tool %}- {{ config.iac_tool }} installed and configured{% else %}- Infrastructure-as-Code tool configured (Terraform, Pulumi, CloudFormation, etc.){% endif %}
{% if config.iac_tool == 'Terraform' %}- Terraform state backend configured (S3 + DynamoDB, Azure Storage, or GCS){% endif %}
- Version control repository access (GitHub, GitLab, Bitbucket)
{% if config.ci_cd %}- {{ config.ci_cd.platform }} access configured{% endif %}

---

## Workflow Steps

### Step 1: Define Infrastructure Requirements (Day 1)

**Agent:** Sprint Planning Agent
**Duration:** 1 day
**Input:** Business requirements, compliance needs, cost constraints
**Output:** Infrastructure requirements document

**Activities:**
- Identify infrastructure scope {% if config.cloud_provider %}({{ config.cloud_provider }} resources){% endif %}
- Define environment structure (dev, staging, prod)
- Specify compliance requirements (data governance, access control)
- Define cost constraints and budget
- List required cloud resources
{% if config.project.type == 'web-app' %}- Web application hosting requirements (compute, load balancing, CDN)
- Database requirements (managed database service){% elif config.project.type == 'api' %}- API hosting requirements (serverless, containers, VMs)
- Database and caching requirements{% elif config.project.type == 'data-platform' %}- Data processing requirements (big data, ETL)
- Data storage requirements (data lakes, warehouses){% elif config.project.type == 'ml' %}- ML infrastructure (training clusters, inference endpoints)
- Model storage and versioning{% endif %}
- Create sprint plan for infrastructure deployment

**Deliverables:**
- Infrastructure requirements document
- Environment specifications
- Resource inventory
- Budget and timeline
- Compliance checklist

**Handoff:** Pass requirements to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}

---

### Step 2: Review Infrastructure Design (Days 2-3)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 2 days
**Input:** Infrastructure requirements
**Output:** Architecture review with recommendations

**Activities:**
{% if config.cloud_provider %}- Review {{ config.cloud_provider }} service selection and architecture{% else %}- Review cloud service selection and architecture{% endif %}
{% if config.project.type == 'web-app' %}- Validate web application architecture (compute, storage, CDN, load balancing)
- Review database design (managed service vs self-hosted){% elif config.project.type == 'api' %}- Validate API architecture (serverless, containers, orchestration)
- Review data layer design (database, caching){% elif config.project.type == 'data-platform' %}- Validate data platform architecture (ingestion, processing, storage)
- Review data catalog and governance structure{% elif config.project.type == 'ml' %}- Validate ML infrastructure (training, inference, feature store)
- Review model management and versioning{% endif %}
- Validate security best practices (network isolation, encryption)
- Recommend cost optimization opportunities
- Review disaster recovery and backup strategy
- Approve multi-environment strategy

**Deliverables:**
- Architecture review document
- Best practices checklist
- Cost optimization recommendations
- Security validation
- Disaster recovery plan

**Handoff:** Pass architecture review to DevOps Engineer

---

### Step 3: Design IaC Modules (Days 4-5)

**Agent:** DevOps Engineer
**Duration:** 2 days
**Input:** Infrastructure requirements, architecture review
**Output:** Infrastructure Design Document

**Activities:**
{% if config.iac_tool %}- Design {{ config.iac_tool }} module structure{% else %}- Design IaC module structure{% endif %}
- Define resource hierarchy and dependencies
{% if config.iac_tool == 'Terraform' %}- Plan Terraform state management (remote backend, state locking)
- Design Terraform module structure and composition
- Define variable structure for multi-environment
- Plan Terraform workspace strategy{% elif config.iac_tool == 'Pulumi' %}- Design Pulumi stack structure
- Plan state backend (Pulumi Cloud or self-hosted)
- Define configuration for multi-environment
- Design component architecture{% elif config.iac_tool == 'CloudFormation' %}- Design CloudFormation stack structure
- Plan nested stack strategy
- Define parameter structure for multi-environment
- Design StackSets for multi-region{% else %}- Plan state/configuration management
- Design module/component structure
- Define configuration for multi-environment{% endif %}
- Plan CI/CD pipeline integration
- Document secrets management approach
{% if config.cloud_provider %}- Map {{ config.cloud_provider }} resource naming conventions{% endif %}

**Deliverables:**
- **Infrastructure Design Document** ({% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/infrastructure-design.md)
{% if config.iac_tool %}- {{ config.iac_tool }} module structure diagram{% else %}- IaC module structure diagram{% endif %}
- State management design
- Variable/parameter configuration plan
- CI/CD pipeline design
- Naming convention guide

**Handoff:** Pass Infrastructure Design to DevOps Engineer (implementation phase)

---

### Step 4: Implement IaC (Days 6-9)

**Agent:** DevOps Engineer
**Duration:** 4 days
**Input:** Infrastructure Design Document
**Output:** {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} modules and configuration

**Activities:**
{% if config.iac_tool == 'Terraform' %}- Create Terraform module structure
{% if config.cloud_provider == 'AWS' %}- Implement AWS resources (VPC, EC2, RDS, S3, IAM, etc.){% elif config.cloud_provider == 'Azure' %}- Implement Azure resources (VNet, VMs, SQL Database, Storage, RBAC, etc.){% elif config.cloud_provider == 'GCP' %}- Implement GCP resources (VPC, Compute Engine, Cloud SQL, Cloud Storage, IAM, etc.){% else %}- Implement cloud resources{% endif %}
- Configure Terraform remote backend
- Implement variable files for each environment
- Create environment-specific configurations (dev/staging/prod)
- Write Terraform documentation{% elif config.iac_tool == 'Pulumi' %}- Create Pulumi component structure
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Implement resources in Python{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- Implement resources in TypeScript{% else %}- Implement resources{% endif %}
- Configure Pulumi stack for each environment
- Implement configuration for dev/staging/prod
- Write Pulumi documentation{% elif config.iac_tool == 'CloudFormation' %}- Create CloudFormation template structure
- Implement AWS resources
- Create parameter files for each environment
- Implement nested stacks
- Write CloudFormation documentation{% else %}- Create IaC modules
- Implement cloud resources
- Create configurations for each environment{% endif %}
{% if config.project.type == 'web-app' %}- Implement compute resources (EC2/App Service/Compute Engine)
- Implement load balancing and auto-scaling
- Implement CDN and static asset hosting
- Implement managed database{% elif config.project.type == 'api' %}- Implement API hosting (Lambda/Functions/Cloud Run)
- Implement API Gateway
- Implement database and caching layer{% elif config.project.type == 'data-platform' %}- Implement data storage (S3/Blob Storage/GCS)
- Implement data processing (EMR/Databricks/Dataflow)
- Implement data cataloging{% elif config.project.type == 'ml' %}- Implement training infrastructure
- Implement model serving endpoints
- Implement feature store (if applicable){% endif %}
- Implement IAM and access control
- Implement monitoring and logging infrastructure

**Deliverables:**
{% if config.iac_tool == 'Terraform' %}- Terraform modules (`terraform/modules/`)
- Environment configurations (`terraform/environments/dev|staging|prod/`)
- Variable files (`terraform.tfvars` per environment)
- Backend configuration (`backend.hcl`)
- Terraform documentation{% elif config.iac_tool == 'Pulumi' %}- Pulumi components (`pulumi/components/`)
- Stack configurations (`Pulumi.dev.yaml`, `Pulumi.staging.yaml`, `Pulumi.prod.yaml`)
- Pulumi program code
- Pulumi documentation{% elif config.iac_tool == 'CloudFormation' %}- CloudFormation templates (`cloudformation/templates/`)
- Parameter files per environment
- Stack configuration
- CloudFormation documentation{% else %}- IaC modules
- Configuration files per environment
- IaC documentation{% endif %}

**Handoff:** Pass IaC code to Security Reviewer

---

### Step 5: Review Secrets Management & Access Control (Days 10-11)

**Agent:** Security Reviewer
**Duration:** 2 days
**Input:** {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} code, Infrastructure Design
**Output:** Security review report

**Activities:**
{% if config.cloud_provider == 'AWS' %}- Review secrets management (AWS Secrets Manager, Parameter Store)
- Validate IAM policies and least privilege access
- Review Security Groups and NACLs{% elif config.cloud_provider == 'Azure' %}- Review secrets management (Azure Key Vault)
- Validate Azure RBAC and least privilege
- Review Network Security Groups{% elif config.cloud_provider == 'GCP' %}- Review secrets management (Secret Manager)
- Validate Cloud IAM and least privilege
- Review VPC firewall rules{% else %}- Review secrets management
- Validate access control and least privilege
- Review network security{% endif %}
- Check for hardcoded credentials (none should exist)
- Review network security (VPC/VNet, private endpoints, bastion hosts)
- Validate encryption (at-rest, in-transit)
- Review audit logging configuration
- Ensure compliance requirements met (GDPR, SOC2, HIPAA, etc.)
- Validate backup and disaster recovery configuration

**Deliverables:**
- Security review report
- Secrets management validation
- Access control checklist (IAM/RBAC)
- Compliance validation
- Security findings and recommendations
- Remediation action items

**Handoff:** Pass security findings to DevOps Engineer for remediation

---

### Step 6: Create CI/CD Pipelines (Days 12-13)

**Agent:** DevOps Engineer
**Duration:** 2 days
**Input:** {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} code (security-reviewed), Infrastructure Design
**Output:** CI/CD pipelines for infrastructure deployment

**Activities:**
{% if config.ci_cd and config.ci_cd.platform == 'GitHub Actions' %}- Create GitHub Actions workflows (`.github/workflows/`){% elif config.ci_cd and config.ci_cd.platform == 'GitLab CI' %}- Create GitLab CI configuration (`.gitlab-ci.yml`){% elif config.ci_cd and config.ci_cd.platform == 'Azure DevOps' %}- Create Azure Pipelines configuration (`azure-pipelines.yml`){% elif config.ci_cd and config.ci_cd.platform == 'Jenkins' %}- Create Jenkinsfile{% else %}- Create CI/CD pipeline configuration{% endif %}
{% if config.iac_tool == 'Terraform' %}- Implement Terraform plan/apply workflow
- Implement `terraform validate` and `terraform fmt` checks
- Integrate tflint for linting
- Configure Infracost for cost estimation{% elif config.iac_tool == 'Pulumi' %}- Implement Pulumi preview/up workflow
- Implement Pulumi stack validation
- Configure cost estimation{% elif config.iac_tool == 'CloudFormation' %}- Implement CloudFormation validate/deploy workflow
- Integrate cfn-lint for linting{% else %}- Implement IaC validation and deployment workflow{% endif %}
- Set up environment-specific deployment gates
- Configure approval workflows (manual approval for prod)
- Implement automated testing
- Set up deployment notifications {% if config.alerting_platform %}({{ config.alerting_platform }}){% else %}(Slack, email){% endif %}
- Configure drift detection {% if config.iac_tool == 'Terraform' %}(terraform plan on schedule){% endif %}

**Deliverables:**
{% if config.ci_cd and config.ci_cd.platform %}- {{ config.ci_cd.platform }} pipeline configurations{% else %}- CI/CD pipeline configurations{% endif %}
- Deployment workflow documentation
- Approval process documentation
- Testing and validation scripts
- Notification configuration
- Drift detection automation

**Handoff:** Pass CI/CD pipelines to Performance Engineer

---

### Step 7: Review Resource Sizing & Configurations (Day 14)

**Agent:** Performance Engineer
**Duration:** 1 day
**Input:** {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} resource configurations, workload requirements
**Output:** Performance optimization recommendations

**Activities:**
{% if config.project.type == 'web-app' %}- Review compute instance sizing (EC2/VMs)
- Validate auto-scaling configurations
- Review database sizing and performance tier
- Validate CDN configuration
- Review caching strategy{% elif config.project.type == 'api' %}- Review serverless/container resource limits
- Validate API Gateway throttling
- Review database connection pooling
- Validate caching layer sizing{% elif config.project.type == 'data-platform' %}- Review data processing cluster sizing
- Validate auto-scaling for big data workloads
- Review data warehouse sizing
- Validate partitioning and indexing strategy{% elif config.project.type == 'ml' %}- Review training cluster sizing (GPU vs CPU)
- Validate inference endpoint auto-scaling
- Review model storage performance
- Validate feature store performance{% else %}- Review resource sizing
- Validate auto-scaling configurations
- Review performance configurations{% endif %}
- Check for cost optimization opportunities
- Recommend instance/SKU type selection
- Validate monitoring and alerting thresholds

**Deliverables:**
- Performance optimization report
- Resource sizing recommendations
- Cost optimization opportunities
- Auto-scaling policy recommendations
- Monitoring threshold recommendations

**Handoff:** Update {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} configs based on recommendations

---

### Step 8: Deploy to Dev Environment (Day 15)

**Agent:** DevOps Engineer
**Duration:** 1 day
**Input:** {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} code, CI/CD pipelines
**Output:** Dev environment deployed

**Activities:**
{% if config.iac_tool == 'Terraform' %}- Initialize Terraform backend for dev environment
- Run `terraform plan` for dev environment
- Review plan output carefully
- Execute `terraform apply` for dev resources{% elif config.iac_tool == 'Pulumi' %}- Initialize Pulumi stack for dev environment
- Run `pulumi preview` for dev stack
- Review preview output carefully
- Execute `pulumi up` for dev resources{% elif config.iac_tool == 'CloudFormation' %}- Validate CloudFormation template
- Create CloudFormation changeset for dev
- Review changeset output
- Execute changeset for dev stack{% else %}- Initialize IaC state for dev
- Preview changes
- Deploy dev resources{% endif %}
- Validate resource creation {% if config.cloud_provider %}in {{ config.cloud_provider }} console{% endif %}
- Test access control and permissions
- Validate secrets management
- Run smoke tests
{% if config.project.type == 'web-app' %}- Test web application deployment
- Verify load balancer health checks{% elif config.project.type == 'api' %}- Test API endpoints
- Verify API Gateway integration{% elif config.project.type == 'data-platform' %}- Test data ingestion
- Verify data processing jobs{% elif config.project.type == 'ml' %}- Test model training job
- Verify model serving endpoint{% endif %}

**Deliverables:**
- Dev environment fully deployed
- Resource validation report
- Smoke test results
- Deployment logs
{% if config.iac_tool %}- {{ config.iac_tool }} state file{% endif %}

**Handoff:** Confirm dev deployment success, proceed to staging

---

### Step 9: Deploy to Staging Environment (Day 16)

**Agent:** DevOps Engineer
**Duration:** 1 day
**Input:** Validated dev deployment, staging {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} configs
**Output:** Staging environment deployed

**Activities:**
{% if config.iac_tool == 'Terraform' %}- Initialize Terraform backend for staging
- Run `terraform plan` for staging
- Execute `terraform apply` for staging{% elif config.iac_tool == 'Pulumi' %}- Initialize Pulumi stack for staging
- Run `pulumi preview` for staging
- Execute `pulumi up` for staging{% elif config.iac_tool == 'CloudFormation' %}- Create CloudFormation changeset for staging
- Execute changeset for staging{% else %}- Deploy staging environment{% endif %}
- Validate resource parity with production requirements
{% if config.project.type == 'web-app' %}- Test application in staging
- Load test web application{% elif config.project.type == 'api' %}- Test API integration in staging
- Load test API endpoints{% elif config.project.type == 'data-platform' %}- Test data pipelines with production-like data
- Performance test data processing{% elif config.project.type == 'ml' %}- Test ML pipelines with production-like data
- Performance test model inference{% else %}- Test application in staging
- Performance testing{% endif %}
- Validate monitoring and alerting
- Run integration tests
- Perform disaster recovery drill

**Deliverables:**
- Staging environment fully deployed
- Integration test results
- Performance benchmarks
- Disaster recovery test results
- Deployment logs

**Handoff:** Confirm staging validation, request production approval

---

### Step 10: Deploy to Production (with Approval) (Day 17)

**Agent:** DevOps Engineer
**Duration:** 1 day
**Input:** Validated staging deployment, production {% if config.iac_tool %}{{ config.iac_tool }}{% else %}IaC{% endif %} configs, stakeholder approval
**Output:** Production environment deployed

**Activities:**
- Obtain production deployment approval from stakeholders
{% if config.iac_tool == 'Terraform' %}- Initialize Terraform backend for production
- Run `terraform plan` for production (review meticulously)
- Execute `terraform apply` for production resources{% elif config.iac_tool == 'Pulumi' %}- Initialize Pulumi stack for production
- Run `pulumi preview` for production (review meticulously)
- Execute `pulumi up` for production resources{% elif config.iac_tool == 'CloudFormation' %}- Create CloudFormation changeset for production (review meticulously)
- Execute changeset for production stack{% else %}- Deploy production environment (with extreme caution){% endif %}
- Validate all resources created successfully
- Enable production monitoring and alerting
{% if config.alerting_platform %}- Configure {{ config.alerting_platform }} alerts{% endif %}
- Test failover and backup procedures
- Create production runbook
- Perform production smoke tests
- Monitor closely for first 24 hours

**Deliverables:**
- Production environment fully deployed
- Production validation report
- Monitoring dashboard active
- Runbook documentation
- Rollback procedure documented
- Production deployment announcement

**Handoff:** Pass deployed infrastructure to Documentation Engineer

---

### Step 11: Update Infrastructure Documentation (Day 18)

**Agent:** Documentation Engineer
**Duration:** 1 day
**Input:** All infrastructure artifacts, deployment reports
**Output:** Complete infrastructure documentation

**Activities:**
{% if config.iac_tool %}- Document {{ config.iac_tool }} module structure and usage{% else %}- Document IaC module structure and usage{% endif %}
- Create infrastructure architecture diagrams
{% if config.diagramming_tool %}- Use {{ config.diagramming_tool }} for diagrams{% endif %}
- Document environment-specific configurations
- Create runbooks for common operations
  - Deployment procedures
  - Rollback procedures
  - Scaling procedures
  - Disaster recovery procedures
- Update {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %} with infrastructure status
- Document monitoring and alerting setup
- Create troubleshooting guide
- Document cost monitoring and optimization

**Deliverables:**
- Infrastructure architecture diagrams
{% if config.iac_tool %}- {{ config.iac_tool }} module documentation{% endif %}
- Runbook documentation
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}
- Troubleshooting guide
- Cost monitoring documentation

**Handoff:** Pass all artifacts to Git Committer

---

### Step 12: Commit Infrastructure Code (Day 18)

**Agent:** Git Committer
**Duration:** 0.5 days
**Input:** All infrastructure code, configurations, documentation
**Output:** Committed and pushed changes

**Activities:**
{% if config.iac_tool %}- Stage all {{ config.iac_tool }} code{% else %}- Stage all IaC code{% endif %}
- Stage CI/CD pipeline configurations
- Stage documentation updates
- Create descriptive commit message
- Tag release (e.g., `infra-v1.0.0`)
- Push to remote repository

**Deliverables:**
- Git commit with all infrastructure artifacts
- Tagged release
- Updated remote repository

**Completion:** Infrastructure setup workflow complete

---

## Workflow Diagram

```mermaid
graph TD
    A[Sprint Planning<br/>Requirements] --> B[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Review Design]
    B --> C[DevOps<br/>Design IaC]
    C --> D[DevOps<br/>Implement IaC]
    D --> E[Security<br/>Review Security]
    E --> F[DevOps<br/>Create CI/CD]
    F --> G[Performance<br/>Review Sizing]
    G --> H[DevOps<br/>Deploy Dev]
    H --> I[DevOps<br/>Deploy Staging]
    I --> J{Staging<br/>Validated?}
    J -->|Yes| K[DevOps<br/>Deploy Prod]
    J -->|No| H
    K --> L[Documentation<br/>Document]
    L --> M[Git Committer<br/>Commit]
```

---

## Duration Estimates

| Phase | Agent | Duration | Cumulative |
|-------|-------|----------|------------|
| Requirements | Sprint Planning | 1 day | Day 1 |
| Architecture Review | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 2 days | Day 3 |
| IaC Design | DevOps Engineer | 2 days | Day 5 |
| IaC Implementation | DevOps Engineer | 4 days | Day 9 |
| Security Review | Security Reviewer | 2 days | Day 11 |
| CI/CD Pipelines | DevOps Engineer | 2 days | Day 13 |
| Performance Review | Performance Engineer | 1 day | Day 14 |
| Deploy Dev | DevOps Engineer | 1 day | Day 15 |
| Deploy Staging | DevOps Engineer | 1 day | Day 16 |
| Deploy Production | DevOps Engineer | 1 day | Day 17 |
| Documentation | Documentation Engineer | 1 day | Day 18 |
| Git Commit | Git Committer | 0.5 days | Day 18 |
| **Total** | | **18 days** | **~3.5 weeks** |

**Buffer:** Add 2-4 days for troubleshooting and stakeholder coordination

---

## Success Criteria

### Must Have
- [ ] Infrastructure requirements documented
- [ ] Architecture review completed and approved
{% if config.iac_tool %}- [ ] {{ config.iac_tool }} modules created and tested{% else %}- [ ] IaC modules created and tested{% endif %}
- [ ] Security review passed (all critical/high issues resolved)
- [ ] CI/CD pipelines functional for all environments
- [ ] Dev environment deployed and validated
- [ ] Staging environment deployed and validated
- [ ] Production environment deployed with approval
- [ ] Complete documentation available

### Should Have
- [ ] Performance optimizations applied
- [ ] Cost monitoring enabled
- [ ] Drift detection automated
- [ ] Disaster recovery tested
- [ ] Runbooks created for all operations

### Nice to Have
{% if config.iac_tool == 'Terraform' %}- [ ] Terraform modules published to registry{% endif %}
- [ ] Multi-region deployment capability
- [ ] Blue-green deployment capability
- [ ] Automated compliance scanning
- [ ] Infrastructure cost optimization dashboard

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
{% if config.iac_tool == 'Terraform' %}| **Terraform state locked** | Check for stuck processes, manually unlock if safe, use state locking properly |
| **Terraform plan shows drift** | Review changes, update IaC to match reality or apply to fix drift |{% endif %}
| **Deployment fails in staging** | Don't proceed to production, fix issues in dev/staging first |
| **Cost higher than expected** | Review Performance Engineer recommendations, right-size resources |
| **Security review fails** | Fix all critical/high findings before proceeding |
{% if config.cloud_provider %}| **{{ config.cloud_provider }} quota exceeded** | Request quota increase, or reduce resource requests |{% endif %}
| **CI/CD pipeline failures** | Check credentials, validate IaC syntax, review logs |

---

## Integration with Other Workflows

**Depends on:**
- Sprint Planning - Creates infrastructure requirements

**Triggers other workflows:**
- Application deployment workflows - Once infrastructure ready
{% if config.project.type == 'ml' %}- ML Model Development - ML infrastructure enables model training{% endif %}

**Can run in parallel with:**
- Application development - If deploying to existing infrastructure
- Documentation workflows - Can document while building

---

## Related Documentation

**Agent Instructions:**
- `agents/planning/sprint-planning.md`
- `agents/development/devops-engineer.md`
{% if config.architecture %}- `agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md`{% endif %}
- `agents/quality/security-reviewer.md`
- `agents/quality/performance-engineer.md`
- `agents/documentation/documentation-engineer.md`

**Handoff Templates:**
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/infrastructure-design-template.md`
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/security-review-template.md`

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
