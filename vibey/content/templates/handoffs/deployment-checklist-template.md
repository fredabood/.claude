---
id: deployment-checklist
name: Deployment Checklist
version: 1.0.0
from_agent: infrastructure-engineer
to_agents:
- documentation-engineer
purpose: Template for deployment checklist
variables:
- name: app_label
  type: string
  required: true
  description: App Label value
- name: app_name
  type: string
  required: true
  description: App Name value
- name: artifact_bucket
  type: string
  required: true
  description: Artifact Bucket value
- name: artifact_name
  type: string
  required: true
  description: Artifact Name value
- name: backend_image_name
  type: string
  required: true
  description: Backend Image Name value
- name: backup_bucket
  type: string
  required: true
  description: Backup Bucket value
- name: bucket_name
  type: string
  required: true
  description: Bucket Name value
- name: build_command
  type: string
  required: true
  description: Build Command value
- name: cdn_distribution
  type: string
  required: true
  description: Cdn Distribution value
- name: cloud_region
  type: string
  required: true
  description: Cloud Region value
- name: custom_deploy_command
  type: string
  required: true
  description: Custom Deploy Command value
- name: custom_rollback_command
  type: string
  required: true
  description: Custom Rollback Command value
- name: custom_rollback_criteria
  type: string
  required: true
  description: Custom Rollback Criteria value
- name: dependency_install_command
  type: string
  required: true
  description: Dependency Install Command value
- name: deployer_name
  type: string
  required: true
  description: Deployer Name value
description: Template for deployment checklist
---

# Deployment Checklist: {{ environment_name }}

**Created by:** {{ config.roles.devops_engineer or 'DevOps Engineer' }}
**Date:** {{ deployment_date }}
**Environment:** {{ environment_type }}
**Deployment Target:** {{ deployment_target }}
**For:** Team/Stakeholders

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing ({{ test_coverage }}% coverage)
- [ ] Test coverage ≥ {{ config.coding_standards.test_coverage.minimum or 90 }}%
- [ ] No compiler/build warnings
- [ ] Linter passing
- [ ] Code reviewed and approved
- [ ] Security review completed

### Security
- [ ] Security review score ≥ {{ config.quality_gates.security_score_minimum or 90 }}/100
- [ ] No hardcoded secrets
- [ ] Environment variables documented
{% if deployment_target in ['kubernetes', 'docker', 'vm'] %}
- [ ] SSL/TLS certificate valid
- [ ] Certificate expiration monitored
{% endif %}
- [ ] Secrets stored in {{ config.infrastructure.secrets_manager or 'secrets manager' }}
- [ ] Network security groups configured

### Documentation
- [ ] README updated
{% if config.project.type == 'api' %}
- [ ] API documentation complete (OpenAPI/Swagger)
{% endif %}
- [ ] Runbook created
- [ ] Deployment procedures documented
- [ ] Rollback procedures documented
- [ ] Environment variables documented
- [ ] Monitoring dashboards configured

### Infrastructure
{% if deployment_target == 'kubernetes' %}
- [ ] Kubernetes cluster provisioned
- [ ] Namespaces created
- [ ] Resource quotas configured
- [ ] Ingress controller configured
- [ ] Load balancer configured
{% elif deployment_target == 'docker' %}
- [ ] Server provisioned
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Domain configured
- [ ] Reverse proxy configured (nginx/Traefik)
{% elif deployment_target == 'serverless' %}
- [ ] Cloud account configured
- [ ] IAM roles created
- [ ] API Gateway configured
- [ ] Function runtime validated
{% elif deployment_target == 'static' %}
- [ ] CDN configured ({{ config.infrastructure.cdn or 'CloudFront/Cloudflare' }})
- [ ] Storage bucket created
- [ ] DNS configured
- [ ] SSL certificate configured
{% elif deployment_target == 'vm' %}
- [ ] Server provisioned
- [ ] Firewall configured
- [ ] Load balancer configured (if applicable)
- [ ] Domain configured
{% endif %}
{% if config.technology_stack.database %}
- [ ] Database provisioned
- [ ] Database migrations tested
- [ ] Database backups configured
{% endif %}

---

## Build Checklist

{% if config.technology_stack.backend %}
### Backend Build ({{ config.technology_stack.backend.framework }})

{% if config.technology_stack.backend.language == 'java' %}
- [ ] Production profile configured (`application-prod.yml`)
- [ ] JAR/WAR built successfully
- [ ] Artifact size acceptable
- [ ] Dependencies optimized
- [ ] Logging configured
- [ ] Health checks implemented

**Build Command:**
```bash
cd {{ backend_directory or 'backend' }}
mvn clean package -P prod -DskipTests=false
```

**Output:** `target/{{ artifact_name }}.jar`

{% elif config.technology_stack.backend.language == 'python' %}
- [ ] Dependencies frozen (`requirements.txt`)
- [ ] Production settings configured
- [ ] WSGI/ASGI server configured ({{ wsgi_server or 'gunicorn/uvicorn' }})
- [ ] Logging configured
- [ ] Health checks implemented

**Build Command:**
```bash
cd {{ backend_directory or 'backend' }}
pip install -r requirements.txt
python -m pytest
```

{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
- [ ] Production build configured
- [ ] Dependencies installed (`package-lock.json`)
- [ ] Build successful (`npm run build`)
- [ ] Environment variables configured
- [ ] Logging configured
- [ ] Health checks implemented

**Build Command:**
```bash
cd {{ backend_directory or 'backend' }}
npm ci
npm run build
npm test
```

**Output:** `dist/` or `build/` directory

{% elif config.technology_stack.backend.language == 'go' %}
- [ ] Production binary built
- [ ] Dependencies vendored (if applicable)
- [ ] Binary optimized (`-ldflags "-s -w"`)
- [ ] Health checks implemented
- [ ] Logging configured

**Build Command:**
```bash
cd {{ backend_directory or 'backend' }}
go build -ldflags "-s -w" -o {{ app_name }} .
go test ./...
```

**Output:** `{{ app_name }}` binary
{% endif %}

{% endif %}

{% if config.web_framework and config.web_framework.frontend %}
### Frontend Build ({{ config.web_framework.frontend }})

- [ ] Production build configured
- [ ] Bundle built successfully
- [ ] Bundle size acceptable ({{ max_bundle_size or '<500KB' }} gzipped)
- [ ] Source maps disabled in production
- [ ] Console logs removed/disabled
- [ ] Environment variables configured
- [ ] Asset optimization complete

{% if config.web_framework.frontend in ['react', 'vue', 'angular', 'svelte'] %}
**Build Command:**
```bash
cd {{ frontend_directory or 'frontend' }}
npm ci
npm run build
```

**Output:** `dist/` or `build/` directory

**Bundle Analysis:**
```bash
ls -lh {{ frontend_directory or 'frontend' }}/dist/assets/
# Verify total size < {{ max_bundle_size or '500KB' }}
```
{% endif %}

{% endif %}

---

{% if deployment_target in ['docker', 'kubernetes'] %}
## Container Checklist

### Docker Images
- [ ] Dockerfiles created
- [ ] Multi-stage builds used
- [ ] Non-root users configured
- [ ] Health checks included
- [ ] Images built successfully
- [ ] Images tagged with version
- [ ] Images scanned for vulnerabilities

**Build Commands:**
{% if config.technology_stack.backend %}
```bash
# Build backend image
cd {{ backend_directory or 'backend' }}
docker build -t {{ image_registry }}/{{ backend_image_name }}:{{ version }} .
docker tag {{ image_registry }}/{{ backend_image_name }}:{{ version }} {{ image_registry }}/{{ backend_image_name }}:latest
```
{% endif %}

{% if config.web_framework and config.web_framework.frontend %}
```bash
# Build frontend image
cd {{ frontend_directory or 'frontend' }}
docker build -t {{ image_registry }}/{{ frontend_image_name }}:{{ version }} .
docker tag {{ image_registry }}/{{ frontend_image_name }}:{{ version }} {{ image_registry }}/{{ frontend_image_name }}:latest
```
{% endif %}

**Verify Images:**
```bash
docker images | grep {{ project_name }}
```

{% if deployment_target == 'docker' %}
### docker-compose.yml
- [ ] Services defined
- [ ] Environment variables configured
- [ ] Volumes mapped
- [ ] Ports exposed
- [ ] Health checks configured
- [ ] Restart policies set (unless-stopped)
- [ ] Logging configured
- [ ] Resource limits set
{% elif deployment_target == 'kubernetes' %}
### Kubernetes Manifests
- [ ] Deployment manifests created
- [ ] Service manifests created
- [ ] ConfigMaps created
- [ ] Secrets created
- [ ] Ingress configured
- [ ] Resource limits set
- [ ] Health probes configured (liveness, readiness)
- [ ] HorizontalPodAutoscaler configured (if needed)
{% endif %}

---
{% endif %}

## Deployment Checklist

### Pre-Deployment

**{{ environment_name }} Environment:**
{% if deployment_target in ['vm', 'docker'] %}
- Server: `{{ server_hostname }}`
- IP: `{{ server_ip }}`
- SSH User: `{{ ssh_user }}`
{% elif deployment_target == 'kubernetes' %}
- Cluster: `{{ k8s_cluster_name }}`
- Namespace: `{{ k8s_namespace }}`
- Context: `{{ k8s_context }}`
{% elif deployment_target == 'serverless' %}
- Cloud Provider: {{ config.cloud_provider or 'AWS/Azure/GCP' }}
- Region: `{{ cloud_region }}`
- Function/App Name: `{{ function_name }}`
{% elif deployment_target == 'static' %}
- CDN: {{ config.infrastructure.cdn }}
- Bucket/Container: `{{ storage_bucket }}`
- Distribution: `{{ cdn_distribution }}`
{% endif %}

**Backup:**
{% if config.technology_stack.database %}
- [ ] Database backed up
- [ ] Backup verified and restorable
{% endif %}
- [ ] Current version tagged in Git
- [ ] Rollback plan ready
- [ ] Previous deployment artifacts archived

**Team Notification:**
- [ ] Team notified of deployment
{% if has_downtime %}
- [ ] Maintenance window scheduled
- [ ] Maintenance page deployed
{% endif %}
- [ ] Stakeholders informed

### Deployment Steps

{% if deployment_target == 'docker' %}
**1. SSH to Server:**
```bash
ssh {{ ssh_user }}@{{ server_hostname }}
```

**2. Pull Latest Code:**
```bash
cd {{ deployment_directory }}
git pull origin {{ git_branch or 'main' }}
```

**3. Pull Docker Images:**
```bash
docker-compose pull
```

**4. Update Environment Variables:**
```bash
# Edit .env file
nano .env

# Verify variables
cat .env
```

**5. Deploy Containers:**
```bash
# Zero-downtime deployment
docker-compose up -d --no-deps --build

# Verify containers running
docker-compose ps
```

{% elif deployment_target == 'kubernetes' %}
**1. Set Kubernetes Context:**
```bash
kubectl config use-context {{ k8s_context }}
kubectl config set-context --current --namespace={{ k8s_namespace }}
```

**2. Update ConfigMaps/Secrets:**
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
```

**3. Deploy Application:**
```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Or use Helm
helm upgrade --install {{ release_name }} ./helm-chart \
  --namespace {{ k8s_namespace }} \
  --values values-{{ environment_type }}.yaml
```

**4. Verify Deployment:**
```bash
kubectl rollout status deployment/{{ deployment_name }}
kubectl get pods -l app={{ app_label }}
```

{% elif deployment_target == 'serverless' %}
**1. Configure Cloud CLI:**
```bash
# AWS
aws configure
aws sts get-caller-identity

# Azure
az login
az account show

# GCP
gcloud auth login
gcloud config set project {{ gcp_project_id }}
```

**2. Deploy Functions:**
```bash
{% if config.cloud_provider == 'aws' %}
# AWS SAM/Serverless Framework
sam deploy --config-env {{ environment_type }}
# or
serverless deploy --stage {{ environment_type }}

{% elif config.cloud_provider == 'azure' %}
# Azure Functions
func azure functionapp publish {{ function_app_name }}

{% elif config.cloud_provider == 'gcp' %}
# Google Cloud Functions
gcloud functions deploy {{ function_name }} \
  --runtime {{ runtime }} \
  --trigger-http \
  --region {{ cloud_region }}
{% endif %}
```

{% elif deployment_target == 'static' %}
**1. Build Assets:**
```bash
cd {{ frontend_directory }}
npm run build
```

**2. Deploy to CDN:**
```bash
{% if config.cloud_provider == 'aws' %}
# AWS S3 + CloudFront
aws s3 sync dist/ s3://{{ bucket_name }}/ --delete
aws cloudfront create-invalidation \
  --distribution-id {{ distribution_id }} \
  --paths "/*"

{% elif config.cloud_provider == 'azure' %}
# Azure Static Web Apps
az staticwebapp deploy \
  --name {{ app_name }} \
  --app-location ./dist

{% elif config.cloud_provider == 'gcp' %}
# GCP Cloud Storage + Cloud CDN
gsutil -m rsync -r -d dist/ gs://{{ bucket_name }}/
gcloud compute url-maps invalidate-cdn-cache {{ url_map }} --path "/*"

{% else %}
# Cloudflare Pages / Netlify / Vercel
{{ custom_deploy_command }}
{% endif %}
```

{% elif deployment_target == 'vm' %}
**1. SSH to Server:**
```bash
ssh {{ ssh_user }}@{{ server_hostname }}
```

**2. Pull Latest Code:**
```bash
cd {{ deployment_directory }}
git pull origin {{ git_branch or 'main' }}
```

**3. Install/Update Dependencies:**
```bash
{{ dependency_install_command }}
```

**4. Build Application:**
```bash
{{ build_command }}
```

**5. Restart Service:**
```bash
sudo systemctl restart {{ service_name }}
sudo systemctl status {{ service_name }}
```
{% endif %}

**6. Verify Health Checks:**
```bash
{% if config.project.type == 'api' or config.project.type == 'web-app' %}
# Check backend health
curl {{ health_check_url }}
# Expected: {{ health_check_expected_response }}

{% if config.web_framework and config.web_framework.frontend %}
# Check frontend
curl -I {{ frontend_url }}
# Expected: 200 OK
{% endif %}
{% endif %}
```

**7. Verify Application:**
```bash
{{ verification_commands }}
```

---

## Post-Deployment Checklist

### Smoke Tests
- [ ] Application accessible via URL
{% if config.project.type == 'web-app' %}
- [ ] Homepage loads
- [ ] Can authenticate
- [ ] Core features functional
- [ ] Forms submit correctly
- [ ] Navigation works
{% elif config.project.type == 'api' %}
- [ ] Health endpoint responds
- [ ] Authentication works
- [ ] Core endpoints respond
- [ ] Error handling works
- [ ] Rate limiting functional
{% endif %}

**Manual Test:**
{{ manual_test_steps }}

### Monitoring
- [ ] Health checks passing
- [ ] Logs flowing correctly
- [ ] Metrics collecting
- [ ] Alerts configured
- [ ] Dashboard showing data
- [ ] Error tracking active ({{ config.monitoring.error_tracking or 'Sentry' }})

**Check Logs:**
{% if deployment_target == 'docker' %}
```bash
docker-compose logs -f {{ service_name }}
docker-compose logs {{ service_name }} | grep ERROR
```
{% elif deployment_target == 'kubernetes' %}
```bash
kubectl logs -f deployment/{{ deployment_name }}
kubectl logs deployment/{{ deployment_name }} | grep ERROR
```
{% elif deployment_target == 'serverless' %}
```bash
{% if config.cloud_provider == 'aws' %}
aws logs tail /aws/lambda/{{ function_name }} --follow
{% elif config.cloud_provider == 'azure' %}
func azure functionapp logstream {{ function_app_name }}
{% elif config.cloud_provider == 'gcp' %}
gcloud functions logs read {{ function_name }} --limit 50
{% endif %}
```
{% elif deployment_target == 'vm' %}
```bash
sudo journalctl -u {{ service_name }} -f
sudo journalctl -u {{ service_name }} | grep ERROR
```
{% endif %}

**Monitor for {{ monitoring_duration or '30 minutes' }}:**
- [ ] No errors in logs
- [ ] Response times normal ({{ acceptable_response_time or '<500ms' }})
- [ ] Error rate {{ acceptable_error_rate or '<1%' }}
- [ ] CPU/memory usage normal
- [ ] No health check failures

### Performance
- [ ] Response time {{ performance_p95_threshold or '<500ms' }} (p95)
{% if config.web_framework and config.web_framework.frontend %}
- [ ] Page load time {{ page_load_threshold or '<2s' }}
{% endif %}
- [ ] No memory leaks
- [ ] CPU usage {{ cpu_usage_threshold or '<70%' }}
{% if config.technology_stack.database %}
- [ ] Database queries optimized
- [ ] Connection pool healthy
{% endif %}

---

## Rollback Checklist

**Decision Criteria:**
- Error rate >{{ rollback_error_threshold or '10%' }} for {{ rollback_duration or '5 minutes' }}
- Critical functionality broken
- Security vulnerability discovered
- Data integrity issues
- {{ custom_rollback_criteria }}

**Rollback Steps:**

{% if deployment_target == 'docker' %}
1. **Stop Current Containers:**
```bash
docker-compose down
```

2. **Rollback to Previous Version:**
```bash
git checkout {{ previous_version_tag }}
docker-compose pull
```

3. **Start Previous Version:**
```bash
docker-compose up -d
```

{% elif deployment_target == 'kubernetes' %}
1. **Rollback Deployment:**
```bash
kubectl rollout undo deployment/{{ deployment_name }}
# Or rollback to specific revision
kubectl rollout undo deployment/{{ deployment_name }} --to-revision={{ revision_number }}
```

2. **Verify Rollback:**
```bash
kubectl rollout status deployment/{{ deployment_name }}
kubectl get pods -l app={{ app_label }}
```

{% elif deployment_target == 'serverless' %}
1. **Rollback to Previous Version:**
```bash
{% if config.cloud_provider == 'aws' %}
aws lambda update-function-code \
  --function-name {{ function_name }} \
  --s3-bucket {{ artifact_bucket }} \
  --s3-key {{ previous_artifact }}

{% elif config.cloud_provider == 'azure' %}
# Swap slots back
az functionapp deployment slot swap \
  --name {{ function_app_name }} \
  --slot staging

{% elif config.cloud_provider == 'gcp' %}
gcloud functions deploy {{ function_name }} \
  --source {{ previous_source }}
{% endif %}
```

{% elif deployment_target == 'static' %}
1. **Restore Previous Build:**
```bash
{% if config.cloud_provider == 'aws' %}
aws s3 sync s3://{{ backup_bucket }}/{{ previous_version }}/ s3://{{ bucket_name }}/ --delete
aws cloudfront create-invalidation --distribution-id {{ distribution_id }} --paths "/*"
{% else %}
{{ custom_rollback_command }}
{% endif %}
```

{% elif deployment_target == 'vm' %}
1. **Checkout Previous Version:**
```bash
cd {{ deployment_directory }}
git checkout {{ previous_version_tag }}
```

2. **Rebuild and Restart:**
```bash
{{ build_command }}
sudo systemctl restart {{ service_name }}
```
{% endif %}

3. **Verify Rollback:**
```bash
{{ rollback_verification_commands }}
```

4. **Monitor for {{ rollback_monitoring_duration or '15 minutes' }}:**
- [ ] Application stable
- [ ] Error rate normal
- [ ] Users can access

5. **Notify Team:**
- [ ] Team notified of rollback
- [ ] Incident report created
- [ ] Post-mortem scheduled

---

## Environment Variables

**Required:**
```bash
{{ environment_variables_list }}
```

**Secrets (stored in {{ config.infrastructure.secrets_manager or 'secrets manager' }}):**
{{ secrets_list }}

---

## Success Criteria

**Deployment Successful If:**
- [ ] {{ has_zero_downtime and 'Zero downtime achieved' or 'Downtime within acceptable window' }}
- [ ] All health checks passing
- [ ] All smoke tests passed
- [ ] Error rate {{ acceptable_error_rate or '<1%' }}
- [ ] Response time {{ acceptable_response_time or '<500ms' }} (p95)
- [ ] No critical issues in logs
- [ ] Team confirmed successful
{% if config.technology_stack.database %}
- [ ] Database migrations successful
{% endif %}

**Sign-off:**
- Deployed by: `{{ deployer_name }}`
- Deployed at: `{{ deployment_timestamp }}`
- Version: `{{ version_tag }}`
- Git SHA: `{{ git_sha }}`
- Status: {{ deployment_status }}

---

## Post-Deployment Actions

- [ ] Tag release in Git
- [ ] Update deployment log
- [ ] Update CHANGELOG
- [ ] Notify stakeholders of success
- [ ] Schedule post-mortem (if issues)
- [ ] Update documentation with lessons learned
- [ ] Archive deployment artifacts
- [ ] Update monitoring dashboards
- [ ] Close deployment tickets

---

**Deployment Complete!** 🎉

**Next Steps:**
{{ post_deployment_next_steps }}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
