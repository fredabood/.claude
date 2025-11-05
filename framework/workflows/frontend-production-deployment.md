# Frontend Production Deployment Workflow

**Purpose:** Package, test, and deploy frontend application to production
**Duration:** 1-2 days
**Complexity:** Medium-High
**Agents:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}, {{ config.agents.test_engineer or 'Test Engineer' }}, {{ config.agents.documentation_engineer or 'Documentation Engineer' }}, {{ config.agents.git_committer or 'Git Committer' }}{% else %}Deployment Engineer, Test Engineer, Documentation Engineer, Git Committer{% endif %}

**When to Use:**
- After all development, testing, and security review complete
- Ready for production deployment
- Multi-environment deployment (dev → staging → production)

---

## 📋 Workflow Overview

This workflow orchestrates production deployment for {% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend }}{% else %}frontend{% endif %} applications with systematic testing and quality gates.

**Workflow Steps:**
1. Create optimized production builds
2. {% if config.deployment and config.deployment.type == 'docker' %}Create Docker containers{% elif config.deployment and config.deployment.type == 'kubernetes' %}Create Kubernetes manifests{% elif config.deployment and config.deployment.type == 'serverless' %}Configure serverless deployment{% else %}Package application{% endif %}
3. Configure CI/CD pipeline
4. Deploy to {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}
5. Run E2E tests on {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}
6. Deploy to {% if config.environments %}{{ config.environments.prod or 'production' }}{% else %}production{% endif %}
7. Configure monitoring and alerts
8. Create operational runbook
9. Commit deployment configurations

**Total Effort:** 1-2 days

---

## 🚀 Prerequisites

Before starting, verify:

**1. Complete Application:**
- ✅ All features implemented
- ✅ All tests passing ({% if config.coding_standards and config.coding_standards.test_coverage %}{{ config.coding_standards.test_coverage.minimum or '90' }}{% else %}90{% endif %}%+ coverage)
- ✅ Security review passed
- ✅ Documentation complete

**2. Verify Local Build:**
{% if config.web_framework and config.web_framework.frontend == 'react' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
npm run build
# Verify build succeeds and outputs to dist/
```{% elif config.web_framework and config.web_framework.frontend == 'vue' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
npm run build
# Verify build succeeds and outputs to dist/
```{% elif config.web_framework and config.web_framework.frontend == 'angular' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
ng build --configuration production
# Verify build succeeds and outputs to dist/
```{% elif config.web_framework and config.web_framework.frontend == 'svelte' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
npm run build
# Verify build succeeds
```{% else %}```bash
# Build your frontend application
npm run build
# or
yarn build
```{% endif %}

**3. Infrastructure Ready:**
- {% if config.cloud_provider %}{{ config.cloud_provider }}{% else %}Cloud provider{% endif %} account and credentials
- {% if config.environments %}{{ config.environments.staging or 'Staging' }}{% else %}Staging{% endif %} environment configured
- {% if config.environments %}{{ config.environments.prod or 'Production' }}{% else %}Production{% endif %} environment ready
- {% if config.deployment and config.deployment.ssl %}SSL certificate configured{% else %}Domain name and SSL certificate (if needed){% endif %}
- {% if config.deployment and config.deployment.type == 'docker' %}Docker{% elif config.deployment and config.deployment.type == 'kubernetes' %}Kubernetes cluster{% endif %} configured

---

## 📝 Workflow Steps

### Step 1: Create Production Builds (4 hours)

**Agent:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}{% else %}Deployment Engineer{% endif %}

**Activities:**

**1.1: Configure Production Environment Variables**

Create production environment file:

{% if config.web_framework and config.web_framework.frontend == 'react' %}```bash
# {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/.env.production
VITE_API_URL=https://api.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
{% if config.security and config.security.authentication %}VITE_AUTH_DOMAIN={{ config.security.authentication.domain or 'auth.example.com' }}{% endif %}
VITE_ENVIRONMENT=production
```{% elif config.web_framework and config.web_framework.frontend == 'vue' %}```bash
# {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/.env.production
VUE_APP_API_URL=https://api.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
{% if config.security and config.security.authentication %}VUE_APP_AUTH_DOMAIN={{ config.security.authentication.domain or 'auth.example.com' }}{% endif %}
VUE_APP_ENVIRONMENT=production
```{% elif config.web_framework and config.web_framework.frontend == 'angular' %}```typescript
// {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}',
  {% if config.security and config.security.authentication %}authDomain: '{{ config.security.authentication.domain or 'auth.example.com' }}',{% endif %}
};
```{% else %}```bash
# Configure production environment variables
API_URL=https://api.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
ENVIRONMENT=production
```{% endif %}

**1.2: Build Optimized Production Bundle**

{% if config.web_framework and config.web_framework.frontend == 'react' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}

# Build with production optimizations
npm run build

# Verify bundle size
du -sh dist/
# Target: < 500KB gzipped

# Check for issues
npm run preview
```{% elif config.web_framework and config.web_framework.frontend == 'vue' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}

# Build with production optimizations
npm run build

# Analyze bundle size
npm run build -- --report

# Check build output
du -sh dist/
```{% elif config.web_framework and config.web_framework.frontend == 'angular' %}```bash
cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}

# Build with production configuration
ng build --configuration production

# Analyze bundle
ng build --configuration production --stats-json
npx webpack-bundle-analyzer dist/stats.json
```{% else %}```bash
# Build production bundle
npm run build

# Verify build output
ls -lh dist/
```{% endif %}

**1.3: Verify Build Quality**

Quality checks:
- ✅ Build completes without errors
- ✅ Bundle size < {% if config.performance and config.performance.bundle_size_limit %}{{ config.performance.bundle_size_limit }}{% else %}500KB{% endif %} gzipped
- ✅ Source maps disabled in production (or separate)
- ✅ Console.log statements removed
- ✅ Environment variables correctly injected
- ✅ All assets properly optimized

**Output:**
- Optimized production bundle
- Build verification report

---

### Step 2: {% if config.deployment and config.deployment.type == 'docker' %}Create Docker Containers{% elif config.deployment and config.deployment.type == 'kubernetes' %}Create Kubernetes Manifests{% elif config.deployment and config.deployment.type == 'serverless' %}Configure Serverless Deployment{% else %}Package Application{% endif %} (4 hours)

**Agent:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}{% else %}Deployment Engineer{% endif %}

{% if config.deployment and config.deployment.type == 'docker' %}**Activities: Create Docker Configuration**

**2.1: Create Dockerfile**

```dockerfile
# {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/Dockerfile

# Multi-stage build
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Build application
RUN npm run build

# Production image with nginx
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1

# Run as non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**2.2: Create nginx Configuration**

```nginx
# {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/nginx.conf

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy
        location /api {
            proxy_pass https://api.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

**2.3: Test Docker Build Locally**

```bash
# Build image
docker build -t {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:latest {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/

# Run container
docker run -d -p 8080:80 --name frontend-test {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:latest

# Test
curl http://localhost:8080/health
curl http://localhost:8080

# Cleanup
docker stop frontend-test
docker rm frontend-test
```

{% elif config.deployment and config.deployment.type == 'kubernetes' %}**Activities: Create Kubernetes Manifests**

**2.1: Create Deployment Manifest**

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
  namespace: {% if config.environments %}{{ config.environments.prod or 'production' }}{% else %}production{% endif %}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
  template:
    metadata:
      labels:
        app: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
    spec:
      containers:
      - name: frontend
        image: {% if config.docker_registry %}{{ config.docker_registry }}{% else %}your-registry{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: API_URL
          value: "https://api.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

**2.2: Create Service and Ingress**

```yaml
# k8s/frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
spec:
  selector:
    app: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - {% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
    secretName: frontend-tls
  rules:
  - host: {% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend
            port:
              number: 80
```

{% elif config.deployment and config.deployment.type == 'static' %}**Activities: Configure Static Hosting**

{% if config.cloud_provider == 'aws' %}**2.1: Create S3 Bucket Configuration**

```bash
# Create S3 bucket for static hosting
aws s3 mb s3://{% if config.project.domain %}{{ config.project.domain }}{% else %}your-app.com{% endif %}

# Enable static website hosting
aws s3 website s3://{% if config.project.domain %}{{ config.project.domain }}{% else %}your-app.com{% endif %} \
  --index-document index.html \
  --error-document index.html

# Set bucket policy
cat > bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::{% if config.project.domain %}{{ config.project.domain }}{% else %}your-app.com{% endif %}/*"
  }]
}
EOF

aws s3api put-bucket-policy --bucket {% if config.project.domain %}{{ config.project.domain }}{% else %}your-app.com{% endif %} --policy file://bucket-policy.json
```

**2.2: Configure CloudFront Distribution**

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name {% if config.project.domain %}{{ config.project.domain }}{% else %}your-app.com{% endif %}.s3-website-us-east-1.amazonaws.com \
  --default-root-object index.html
```

{% elif config.cloud_provider == 'azure' %}**2.1: Configure Azure Static Web Apps**

```bash
# Create static web app
az staticwebapp create \
  --name {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend \
  --resource-group {% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-rg \
  --location "Central US" \
  --sku Free
```

{% else %}**2.1: Deploy to Netlify/Vercel**

```bash
# netlify.toml or vercel.json configuration
# Add build and deployment settings
```
{% endif %}

{% else %}**Activities: Package Application**

Create deployment package appropriate for your hosting platform.
{% endif %}

**Output:**
- {% if config.deployment and config.deployment.type == 'docker' %}Docker image and configuration{% elif config.deployment and config.deployment.type == 'kubernetes' %}Kubernetes manifests{% elif config.deployment and config.deployment.type == 'static' %}Static hosting configuration{% else %}Deployment package{% endif %}
- Local testing complete
- Deployment scripts

---

### Step 3: Configure CI/CD Pipeline (6 hours)

**Agent:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}{% else %}Deployment Engineer{% endif %}

**Activities:**

**3.1: Create CI/CD Configuration**

{% if config.ci_cd and config.ci_cd.platform == 'github-actions' or not config.ci_cd %}```yaml
# .github/workflows/frontend-deploy.yml
name: Frontend Deployment

on:
  push:
    branches: [{% if config.environments %}{{ config.environments.prod or 'main' }}{% else %}main{% endif %}]
    paths:
      - '{% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/package-lock.json

      - name: Install dependencies
        run: |
          cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
          npm ci

      - name: Run tests
        run: |
          cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
          npm test -- --coverage

      - name: Check coverage
        run: |
          cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
          {% if config.coding_standards and config.coding_standards.test_coverage %}# Ensure {{ config.coding_standards.test_coverage.minimum or '90' }}% coverage{% else %}# Check coverage thresholds{% endif %}

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build
        run: |
          cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
          npm ci
          npm run build

      {% if config.deployment and config.deployment.type == 'docker' %}- name: Build Docker image
        run: |
          docker build -t {% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:${{ github.sha }} {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/
          docker tag {% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:${{ github.sha }} \
                     {% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:latest

      - name: Push Docker image
        run: |
          echo "{% raw %}${{ secrets.DOCKER_PASSWORD }}{% endraw %}" | docker login {% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %} -u {% raw %}${{ secrets.DOCKER_USERNAME }}{% endraw %} --password-stdin
          docker push {% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:${{ github.sha }}
          docker push {% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:latest
      {% endif %}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}
    steps:
      - name: Deploy to Staging
        run: |
          # Add deployment commands for staging
          {% if config.deployment and config.deployment.type == 'kubernetes' %}kubectl set image deployment/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend \
            frontend={% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:${{ github.sha }} \
            -n staging{% elif config.deployment and config.deployment.type == 'static' and config.cloud_provider == 'aws' %}aws s3 sync {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/dist/ s3://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}/ \
            --delete{% endif %}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: {% if config.environments %}{{ config.environments.prod or 'production' }}{% else %}production{% endif %}
    steps:
      - name: Deploy to Production
        run: |
          # Add deployment commands for production
          {% if config.deployment and config.deployment.type == 'kubernetes' %}kubectl set image deployment/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend \
            frontend={% if config.docker_registry %}{{ config.docker_registry }}{% else %}${{ secrets.DOCKER_REGISTRY }}{% endif %}/{% if config.project.name %}{{ config.project.name }}{% else %}app{% endif %}-frontend:${{ github.sha }} \
            -n production{% elif config.deployment and config.deployment.type == 'static' and config.cloud_provider == 'aws' %}aws s3 sync {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/dist/ s3://{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}/ \
            --delete
          # Invalidate CloudFront cache
          aws cloudfront create-invalidation --distribution-id {% raw %}${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}{% endraw %} --paths "/*"{% endif %}
```
{% elif config.ci_cd and config.ci_cd.platform == 'gitlab-ci' %}```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy-staging
  - deploy-production

test:
  stage: test
  image: node:18
  script:
    - cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
    - npm ci
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'

build:
  stage: build
  image: node:18
  script:
    - cd {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}
    - npm ci
    - npm run build
  artifacts:
    paths:
      - {% if config.project.structure and config.project.structure.frontend_directory %}{{ config.project.structure.frontend_directory }}{% else %}frontend{% endif %}/dist/

deploy-staging:
  stage: deploy-staging
  environment:
    name: staging
    url: https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
  script:
    - # Add staging deployment commands

deploy-production:
  stage: deploy-production
  environment:
    name: production
    url: https://{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
  when: manual
  script:
    - # Add production deployment commands
```
{% else %}# Create CI/CD pipeline for your platform
{% endif %}

**Output:**
- CI/CD pipeline configured
- Automated testing in pipeline
- Multi-environment deployment
- Manual approval for production

---

### Step 4: Deploy to {% if config.environments %}{{ config.environments.staging | title or 'Staging' }}{% else %}Staging{% endif %} (2 hours)

**Agent:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}{% else %}Deployment Engineer{% endif %}

**Activities:**
1. Trigger deployment to {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %} via CI/CD
2. Verify deployment health
3. Check application accessibility
4. Validate configuration

**Verification:**
```bash
# Check {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %} deployment
curl https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}/health

# Test application
open https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
```

**Quality Checks:**
- ✅ Application deployed successfully
- ✅ Health checks passing
- ✅ UI accessible and functional
- ✅ API integration working
- ✅ No console errors

---

### Step 5: Run E2E Tests on {% if config.environments %}{{ config.environments.staging | title or 'Staging' }}{% else %}Staging{% endif %} (4 hours)

**Agent:** {% if config.agents %}{{ config.agents.test_engineer or 'Test Engineer' }}{% else %}Test Engineer{% endif %}

**Activities:**

**5.1: Configure E2E Tests for Staging**

{% if config.testing and config.testing.e2e_framework == 'playwright' or config.web_framework and config.web_framework.frontend == 'react' %}```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}',
  },
  // ... other configuration
});
```

**5.2: Run E2E Tests**

```bash
PLAYWRIGHT_BASE_URL=https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %} npx playwright test
```
{% elif config.testing and config.testing.e2e_framework == 'cypress' %}```typescript
// cypress.config.ts
export default defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || 'https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}',
  },
});
```

**5.2: Run E2E Tests**

```bash
CYPRESS_BASE_URL=https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %} npx cypress run
```
{% else %}```bash
# Run E2E tests against staging
npm run test:e2e -- --url=https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
```
{% endif %}

**Critical Test Flows:**
- {% if config.security and config.security.authentication %}Authentication (login/logout){% endif %}
- {% if config.project.type == 'web-app' %}Core user workflows{% elif config.project.type == 'api' %}API integration{% else %}Key features{% endif %}
- CRUD operations
- Error handling
- Performance benchmarks

**Quality Checks:**
- ✅ All E2E tests passing
- ✅ No broken links
- ✅ Forms working correctly
- ✅ Error states handled
- ✅ Performance acceptable

---

### Step 6: Deploy to {% if config.environments %}{{ config.environments.prod | title or 'Production' }}{% else %}Production{% endif %} (2 hours)

**Agent:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}{% else %}Deployment Engineer{% endif %}

**Activities:**

**6.1: Pre-Production Checklist**
- ✅ All {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %} tests passed
- ✅ Stakeholder approval obtained
- ✅ Rollback plan documented
- ✅ Monitoring configured
- ✅ Team notified of deployment

**6.2: Execute Production Deployment**
- Trigger manual approval in CI/CD
- Deploy via pipeline
- Monitor deployment progress

**6.3: Post-Deployment Verification**
```bash
# Verify production deployment
curl https://{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}/health

# Smoke test
open https://{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
```

---

### Step 7: Configure Monitoring (2 hours)

**Agent:** {% if config.agents %}{{ config.agents.deployment_engineer or 'Deployment Engineer' }}{% else %}Deployment Engineer{% endif %}

**Activities:**

**7.1: Configure Application Monitoring**

{% if config.monitoring and config.monitoring.platform %}Set up monitoring in {{ config.monitoring.platform }}:
{% else %}Configure monitoring:
{% endif %}

- Frontend error tracking ({% if config.monitoring and config.monitoring.error_tracking %}{{ config.monitoring.error_tracking }}{% else %}Sentry, LogRocket, etc.{% endif %})
- Performance monitoring ({% if config.monitoring and config.monitoring.performance %}{{ config.monitoring.performance }}{% else %}Web Vitals, etc.{% endif %})
- Uptime monitoring
- User analytics

**7.2: Configure Alerts**

Set up alerts for:
- Application errors (>1% error rate)
- Performance degradation (p95 > {% if config.performance and config.performance.p95_threshold %}{{ config.performance.p95_threshold }}{% else %}3s{% endif %})
- Downtime (uptime < {% if config.monitoring and config.monitoring.uptime_threshold %}{{ config.monitoring.uptime_threshold }}{% else %}99.9%{% endif %})

---

### Step 8: Create Operational Runbook (2 hours)

**Agent:** {% if config.agents %}{{ config.agents.documentation_engineer or 'Documentation Engineer' }}{% else %}Documentation Engineer{% endif %}

**Activities:**

Create runbook document:

```markdown
# {% if config.project.name %}{{ config.project.name | title }}{% else %}Application{% endif %} Operations Runbook

## Deployment

### Production URL
https://{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}

### Deployment Process
[Document deployment steps]

## Monitoring

### Dashboards
- {% if config.monitoring and config.monitoring.platform %}{{ config.monitoring.platform }}{% endif %} Dashboard: [URL]
- Error Tracking: [URL]

### Key Metrics
- Uptime: Target {% if config.monitoring and config.monitoring.uptime_threshold %}{{ config.monitoring.uptime_threshold }}{% else %}99.9%{% endif %}
- Error Rate: Target < 1%
- P95 Latency: Target < {% if config.performance and config.performance.p95_threshold %}{{ config.performance.p95_threshold }}{% else %}3s{% endif %}

## Troubleshooting

### Common Issues
[Document common issues and solutions]

### Rollback Procedure
[Document rollback steps]

## Contacts
- On-call: [contact info]
- Escalation: [contact info]
```

---

### Step 9: Commit Deployment Configurations (1 hour)

**Agent:** {% if config.agents %}{{ config.agents.git_committer or 'Git Committer' }}{% else %}Git Committer{% endif %}

**Activities:**
1. Review all deployment files
2. Stage deployment configurations
3. Create commit
4. Push to repository

**Commit Message:**
```
feat: Configure production deployment for {% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend }}{% else %}frontend{% endif %}

{% if config.deployment and config.deployment.type == 'docker' %}- Docker configuration with multi-stage builds
- nginx configuration with security headers{% elif config.deployment and config.deployment.type == 'kubernetes' %}- Kubernetes deployment manifests
- Service and Ingress configuration{% elif config.deployment and config.deployment.type == 'static' %}- Static hosting configuration
- CDN setup{% endif %}
- CI/CD pipeline ({% if config.ci_cd and config.ci_cd.platform %}{{ config.ci_cd.platform }}{% else %}GitHub Actions{% endif %})
- Multi-environment deployment (staging/production)
- Monitoring and alerting
- Operational runbook

Deployed to:
- {% if config.environments %}{{ config.environments.staging | title or 'Staging' }}{% else %}Staging{% endif %}: https://staging.{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
- {% if config.environments %}{{ config.environments.prod | title or 'Production' }}{% else %}Production{% endif %}: https://{% if config.project.domain %}{{ config.project.domain }}{% else %}example.com{% endif %}
```

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ **Production Deployed:** Application running in production
2. ✅ **Tests Passing:** All E2E tests pass on {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %}
3. ✅ **Performance:** Meets performance targets (bundle size, load time)
4. ✅ **Monitoring:** Monitoring and alerts configured
5. ✅ **CI/CD:** Automated deployment pipeline working
6. ✅ **Documentation:** Operational runbook complete
7. ✅ **Rollback Ready:** Rollback procedure documented and tested

---

## 🔗 Related Workflows

**Upstream (Triggers This Workflow):**
- **Frontend Security Hardening** - Security review before deployment
- **{% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend | title }}{% else %}Frontend{% endif %} Development** - Application development complete

**Downstream (This Workflow Enables):**
- **Production Monitoring** - Ongoing monitoring and maintenance

---

## 💡 Best Practices

1. **Test Staging First:** Always deploy to {% if config.environments %}{{ config.environments.staging or 'staging' }}{% else %}staging{% endif %} before production
2. **Automate Everything:** CI/CD for consistency and speed
3. **Monitor Actively:** Set up monitoring before deployment
4. **Document Operations:** Create runbook for team
5. **Plan Rollbacks:** Always have rollback procedure ready
6. **Gradual Rollout:** Consider canary or blue-green deployments
7. **Security Headers:** Configure security headers in web server
8. **Performance:** Optimize bundle size and assets

---

**Workflow Version:** 1.0
**Created:** {{ "now"|date("%Y-%m-%d") }}
**Maintained By:** {% if config.team %}{{ config.team.name }}{% else %}Project Team{% endif %}
**Framework:** Vibey Agent Framework
