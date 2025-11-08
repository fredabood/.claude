# Example: Kubernetes Infrastructure Migration

This example demonstrates roadmap planning for migrating from EC2-based infrastructure to Kubernetes with strict sequential dependencies.

## Project Overview

**Goal:** Migrate production application from AWS EC2 to EKS (Elastic Kubernetes Service) with zero downtime.

**Duration:** 10 weeks
**Tracks:** 4 (must be sequential)
**Total Sprints:** 7
**Total Tasks:** 48

## Roadmap Structure

```
K8s Migration (roadmap)
  ├── Infrastructure Setup (track) - 2 sprints
  │   ├── Sprint 1: EKS Cluster Provisioning
  │   └── Sprint 2: Networking & Security
  ├── Application Migration (track) - 3 sprints
  │   ├── Sprint 1: Containerization
  │   ├── Sprint 2: K8s Manifests & Helm Charts
  │   └── Sprint 3: CI/CD Pipeline
  ├── Observability (track) - 1 sprint
  │   └── Sprint 1: Monitoring & Logging
  └── Cutover (track) - 1 sprint
      └── Sprint 1: Blue-Green Deployment & Switch
```

## Technology Stack

- **Infrastructure:** AWS EKS, Terraform
- **Containers:** Docker, Kubernetes
- **CI/CD:** GitHub Actions, ArgoCD
- **Monitoring:** Prometheus, Grafana, ELK Stack
- **Secrets:** AWS Secrets Manager, External Secrets Operator

## Critical Dependencies

```
Infrastructure Setup (Track 1)
    ↓
Application Migration (Track 2) [Need cluster before deploying apps]
    ↓
Observability (Track 3) [Need apps deployed before monitoring]
    ↓
Cutover (Track 4) [Need everything ready before production switch]
```

**Important:** These tracks MUST be completed sequentially. Each track blocks the next.

## Sprint Breakdown

### Track 1: Infrastructure Setup (3 weeks)

#### Sprint 1: EKS Cluster Provisioning (1.5 weeks)
- Task 1: Design EKS cluster architecture
- Task 2: Write Terraform for VPC
- Task 3: Write Terraform for EKS cluster
- Task 4: Provision EKS cluster (3 node groups: system, app, db)
- Task 5: Configure kubectl access
- Task 6: Set up RBAC roles and permissions
- Task 7: **Gate:** Infrastructure validation tests
- Task 8: **Gate:** Security audit of cluster config
- Task 9: **Gate:** Documentation for cluster setup

#### Sprint 2: Networking & Security (1.5 weeks)
- Task 1: Configure VPC peering with existing network
- Task 2: Set up ingress controller (nginx)
- Task 3: Configure load balancer
- Task 4: Set up cert-manager for SSL
- Task 5: Implement network policies
- Task 6: Configure AWS Secrets Manager integration
- Task 7: Set up External Secrets Operator
- Task 8: **Gate:** Network connectivity tests
- Task 9: **Gate:** Security audit of network config
- Task 10: **Gate:** SSL/TLS validation

### Track 2: Application Migration (4 weeks)

#### Sprint 1: Containerization (1.5 weeks)
- Task 1: Audit existing EC2 applications
- Task 2: Write Dockerfiles for all services (8 services)
- Task 3: Set up private ECR repositories
- Task 4: Build and push Docker images
- Task 5: Implement health check endpoints
- Task 6: Configure container resource limits
- Task 7: **Gate:** Container security scan (no critical vulnerabilities)
- Task 8: **Gate:** Image size optimization (<500MB per image)

#### Sprint 2: K8s Manifests & Helm Charts (1.5 weeks)
- Task 1: Write K8s Deployments for all services
- Task 2: Create Services and Ingress rules
- Task 3: Configure ConfigMaps
- Task 4: Set up PersistentVolumeClaims
- Task 5: Create Helm charts
- Task 6: Implement HPA (Horizontal Pod Autoscaler)
- Task 7: Deploy to dev environment
- Task 8: **Gate:** K8s manifest validation (kubeval)
- Task 9: **Gate:** Helm chart testing

#### Sprint 3: CI/CD Pipeline (1 week)
- Task 1: Set up GitHub Actions workflows
- Task 2: Implement ArgoCD for GitOps
- Task 3: Configure automatic image builds
- Task 4: Set up staging environment
- Task 5: Implement rollback procedures
- Task 6: **Gate:** CI/CD end-to-end test
- Task 7: **Gate:** Rollback testing

### Track 3: Observability (1.5 weeks)

#### Sprint 1: Monitoring & Logging (1.5 weeks)
- Task 1: Deploy Prometheus operator
- Task 2: Configure ServiceMonitors for all apps
- Task 3: Create Grafana dashboards (10 dashboards)
- Task 4: Deploy ELK stack (Elasticsearch, Logstash, Kibana)
- Task 5: Configure log aggregation from all pods
- Task 6: Set up alert rules
- Task 7: Integrate PagerDuty for alerting
- Task 8: **Gate:** All services emitting metrics
- Task 9: **Gate:** Log retention tests (30 days)
- Task 10: **Gate:** Alert validation tests

### Track 4: Cutover (1.5 weeks)

#### Sprint 1: Blue-Green Deployment & Switch (1.5 weeks)
- Task 1: Deploy all services to production EKS
- Task 2: Run smoke tests
- Task 3: Configure blue-green DNS switching
- Task 4: Run load tests (same traffic as production)
- Task 5: Perform gradual traffic shift (10% → 50% → 100%)
- Task 6: Monitor metrics during shift
- Task 7: Validate all functionality
- Task 8: Decommission EC2 instances
- Task 9: **Gate:** Zero production errors during cutover
- Task 10: **Gate:** Performance validation (<100ms latency increase)
- Task 11: **Gate:** Final security audit
- Task 12: **Gate:** Runbook documentation

## Agent Assignments

**Recommended agents:**
- **web-developer** - Containerization, health checks, manifests
- **test-engineer** - All testing gates, load testing
- **security-auditor** - All security audits
- **docs-writer** - Documentation gates, runbooks
- **performance-engineer** - Performance testing, optimization
- **coordinator** - Cutover coordination (complex multi-step process)

## Quality Gates by Track

### Infrastructure Gates
- Infrastructure validation
- Security audits (2 gates)
- Network connectivity tests
- SSL/TLS validation

### Application Migration Gates
- Container security scans (no critical)
- Image size optimization (<500MB)
- K8s manifest validation
- Helm chart testing
- CI/CD end-to-end tests
- Rollback testing

### Observability Gates
- All services emitting metrics
- Log retention (30 days)
- Alert validation

### Cutover Gates (Critical!)
- Zero production errors
- Performance validation (<100ms increase)
- Final security audit
- Complete runbook

## Risk Management

### High-Risk Tasks
1. **Production traffic shift** (cutover-1-task-005)
   - Mitigation: Gradual shift, instant rollback capability
   - Requires: Coordinator agent oversight

2. **Database migration** (app-migration-2-task-004)
   - Mitigation: PersistentVolumes, backup before migration
   - Gate: Data validation test

3. **Decommissioning EC2** (cutover-1-task-008)
   - Mitigation: Only after 100% traffic on K8s for 48 hours
   - Gate: Zero production errors

## Usage Example

```bash
# Week 1-3: Infrastructure setup
roadmap start infrastructure
roadmap start infrastructure-1

# Check what's blocked
roadmap list tracks --status not_started
roadmap deps app-migration --blockers
# Output: ⚠️ Blocked by infrastructure track

# Complete infrastructure
roadmap complete infrastructure-2
roadmap complete infrastructure

# Week 4-7: Application migration now unblocked
roadmap deps app-migration --blockers
# Output: No blockers!

roadmap start app-migration
roadmap start app-migration-1

# Week 8: Observability (waits for apps)
roadmap deps observability-1 --blockers
# Output: ⚠️ Blocked by app-migration track

# Complete app migration
roadmap complete app-migration

# Week 9: Observability now unblocked
roadmap start observability
roadmap start observability-1

# Week 10: Critical cutover (requires coordinator)
roadmap recommend --task cutover-1-task-005
# Output: coordinator (95% confidence) - Complex multi-step coordination

roadmap start cutover
roadmap assign cutover-1-task-005 coordinator

# Monitor cutover carefully
roadmap show cutover-1
# Real-time progress tracking
```

## Monitoring During Migration

```bash
# Check overall progress
roadmap status

# View track dependencies
roadmap deps

# Check blocker status daily
roadmap deps --blockers --json > blockers.json

# Agent workload for cutover
roadmap agents --workload
```

## Rollback Plan

If issues occur during cutover:

1. **Immediate:** Shift traffic back to EC2 (DNS change)
2. **Within 1 hour:** Investigate K8s issues
3. **Within 24 hours:** Fix and retry cutover
4. **Rollback criteria:**
   - Error rate >1%
   - Latency increase >100ms
   - Any 5xx errors
   - Customer complaints

```bash
# Rollback tracking
roadmap show cutover-1
# Check gate: Zero production errors (if failed, rollback triggered)
```

## Expected Timeline

| Weeks | Track | Focus | Status |
|-------|-------|-------|--------|
| 1-3   | Infrastructure | EKS cluster & network | ✅ completed |
| 4-7   | App Migration | Containers & CI/CD | 🔵 in_progress |
| 8     | Observability | Monitoring & logging | ⚪ not_started |
| 9-10  | Cutover | Production switch | ⚪ not_started |

## Success Criteria

✅ Zero downtime during migration
✅ All services running on K8s
✅ Performance maintained (<100ms latency increase)
✅ All monitoring and alerts operational
✅ EC2 infrastructure decommissioned
✅ Complete runbooks documented
✅ Team trained on K8s operations

## Post-Migration

After successful cutover:

1. **Monitor for 30 days** - Watch for issues
2. **Cost optimization** - Rightsize node groups
3. **Documentation sprint** - Update all runbooks
4. **Team training** - K8s best practices
5. **Retrospective** - Lessons learned

## Key Learnings

This example demonstrates:
- **Strict sequential dependencies** - Critical for infrastructure
- **Risk management** - High-risk tasks identified
- **Coordinator agent usage** - For complex cutover
- **Rollback planning** - Built into quality gates
- **Zero-downtime migration** - Blue-green deployment
- **Comprehensive monitoring** - Before production switch

## Files Structure

```
infrastructure-migration/
└── .vibey/
    ├── roadmap.yaml
    ├── tracks/
    │   ├── infrastructure.yaml
    │   ├── app-migration.yaml
    │   ├── observability.yaml
    │   └── cutover.yaml
    ├── sprints/
    │   └── [7 sprint files]
    └── tasks/
        └── [7 task files]
```

---

**Critical:** This migration requires careful coordination. Use the Coordinator agent for the cutover track!
