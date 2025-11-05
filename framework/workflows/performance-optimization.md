# Workflow: Performance Optimization

**Workflow ID:** Performance Optimization
**Purpose:** Systematic performance optimization cycle for applications, services, and data pipelines
**Duration:** 5-8 days (1-1.5 weeks)
**Complexity:** Medium-High

---

## Overview

This workflow orchestrates systematic performance optimization: analysis → recommendations → implementation → validation → benchmarking. It ensures Performance Engineer, {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}, developers, Test Engineer, Documentation Engineer, and Git Committer work together to optimize performance, reduce costs, and meet SLA requirements.

**Use Cases:**
{% if config.project.type == 'web-app' %}- Slow page loads (>3 second load times)
- High server response times
- Frontend rendering performance issues
- Database query optimization
- Bundle size optimization{% elif config.project.type == 'api' %}- Slow API endpoints (>500ms response time)
- High database query latency
- Memory leaks or high CPU usage
- Inefficient algorithms
- API rate limit issues{% elif config.project.type == 'data-platform' %}- Slow data processing jobs (>1 hour runtime)
- Expensive queries (high resource consumption)
- Data pipeline latency issues
- ETL performance bottlenecks{% elif config.project.type == 'ml' %}- Slow model training (>24 hours)
- High inference latency (>1 second)
- Feature engineering bottlenecks
- Model serving performance issues{% else %}- Application performance issues
- Resource consumption problems
- Latency and throughput optimization{% endif %}
- Performance regression after code changes
- Pre-production performance validation
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost optimization{% endif %}

**Prerequisites:**
- Existing code with performance issues identified
- SLA requirements defined (runtime, latency, cost)
{% if config.project.type == 'web-app' %}- Access to browser DevTools, Lighthouse reports{% elif config.project.type == 'api' %}- Access to API metrics and database query logs{% elif config.project.type == 'data-platform' %}- Access to query execution logs and job metrics{% elif config.project.type == 'ml' %}- Access to training logs and inference metrics{% endif %}
{% if config.monitoring %}- Access to {{ config.monitoring.platform }} metrics{% endif %}

---

## Workflow Steps

### Step 1: Identify Performance Issues & SLA Requirements (Day 1)

**Agent:** Sprint Planning Agent
**Duration:** 0.5 days
**Input:** Performance complaints, monitoring alerts, cost reports
**Output:** Performance optimization requirements

**Activities:**
- Identify underperforming {% if config.project.type == 'web-app' %}pages/components{% elif config.project.type == 'api' %}endpoints{% elif config.project.type == 'data-platform' %}jobs/queries{% elif config.project.type == 'ml' %}training/inference pipelines{% else %}components{% endif %}
- Define SLA requirements
  {% if config.project.type == 'web-app' %}- Page load time: <3 seconds
  - Time to Interactive (TTI): <5 seconds
  - Lighthouse score: >90{% elif config.project.type == 'api' %}- API response time: <500ms (p95)
  - Throughput: >1000 req/sec
  - Database query time: <100ms{% elif config.project.type == 'data-platform' %}- Job runtime: <1 hour
  - Query latency: <30 seconds
  - Resource cost: <$X/run{% elif config.project.type == 'ml' %}- Training time: <24 hours
  - Inference latency: <100ms
  - GPU utilization: >80%{% endif %}
- Prioritize optimization opportunities (by impact × frequency)
- Set success criteria (% improvement needed)
- Create sprint plan for optimization work

**Deliverables:**
- Performance issue list (ranked by impact)
- SLA requirements
- Success criteria
- Optimization sprint plan

**Handoff:** Pass requirements to Performance Engineer

---

### Step 2: Analyze Current Performance (Days 1-2)

**Agent:** Performance Engineer
**Duration:** 1.5 days
**Input:** Performance requirements, target {% if config.project.type == 'web-app' %}pages/components{% elif config.project.type == 'api' %}endpoints{% elif config.project.type == 'data-platform' %}jobs/queries{% elif config.project.type == 'ml' %}models/pipelines{% else %}components{% endif %}
**Output:** Performance Analysis Report

**Activities:**

{% if config.project.type == 'web-app' %}**Web Performance Analysis:**
- Run Lighthouse audits (Performance, Best Practices, SEO)
- Analyze Chrome DevTools Performance tab
  - Identify long tasks (>50ms)
  - Analyze main thread blocking
  - Review network waterfall
- Measure Core Web Vitals
  - LCP (Largest Contentful Paint)
  - FID (First Input Delay)
  - CLS (Cumulative Layout Shift)
- Profile frontend rendering (React DevTools Profiler)
- Analyze bundle size (webpack-bundle-analyzer)
- Review database queries (if backend)
- Check image optimization and lazy loading
- Measure API call latency{% elif config.project.type == 'api' %}**API Performance Analysis:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Profile Python code (cProfile, line_profiler, memory_profiler){% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- Profile Node.js code (clinic.js, 0x){% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}- Profile Java code (JProfiler, YourKit){% else %}- Profile application code{% endif %}
- Analyze database query execution plans
  {% if config.database and config.database.type == 'postgresql' %}- Use EXPLAIN ANALYZE in PostgreSQL{% elif config.database and config.database.type == 'mysql' %}- Use EXPLAIN in MySQL{% elif config.database and config.database.type == 'mongodb' %}- Use explain() in MongoDB{% endif %}
- Identify N+1 query problems
- Review API endpoint response times (p50, p95, p99)
- Analyze connection pooling and concurrency
- Check caching effectiveness (Redis hit rate if applicable)
- Measure memory usage and garbage collection{% elif config.project.type == 'data-platform' %}**Data Pipeline Performance Analysis:**
{% if config.big_data_framework == 'Spark' %}- Review Spark UI (stages, tasks, shuffle)
- Analyze query execution plans (physical plans, join strategies)
- Identify data skew and large shuffles
- Check partition distribution{% elif config.big_data_framework %}- Analyze {{ config.big_data_framework }} execution metrics{% else %}- Review ETL job execution metrics{% endif %}
{% if config.database %}- Review {{ config.database.type }} query performance{% endif %}
- Profile data characteristics (table sizes, row counts)
- Identify bottlenecks (I/O, CPU, memory)
- Calculate current metrics (runtime, cost, throughput){% elif config.project.type == 'ml' %}**ML Performance Analysis:**
- Profile model training
  {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Use PyTorch Profiler or TensorFlow Profiler{% endif %}
  - GPU utilization
  - Data loading bottlenecks
  - Training step time
- Analyze inference latency
  - Model forward pass time
  - Pre/post-processing time
  - Batch inference efficiency
- Review feature engineering performance
- Check data pipeline throughput
- Measure model size and memory footprint{% else %}**Application Performance Analysis:**
- Profile application code
- Analyze resource usage (CPU, memory, I/O)
- Identify bottlenecks
- Review metrics and logs{% endif %}
- Calculate baseline metrics

**Deliverables:**
- **Performance Analysis Report** ({% if config.custom.handoff_location %}{{ config.custom.handoff_location %}{% else %}docs/handoffs{% endif %}/performance-analysis.md)
{% if config.project.type == 'web-app' %}- Lighthouse audit results
- Chrome DevTools screenshots
- Core Web Vitals metrics{% elif config.project.type == 'api' %}- Profiling results (flame graphs)
- Database query execution plans
- API latency distribution{% elif config.project.type == 'data-platform' %}- Query execution plans
- Job execution metrics{% elif config.project.type == 'ml' %}- Training/inference profiles
- GPU utilization reports{% endif %}
- Bottleneck identification
- Current performance metrics

**Handoff:** Pass Performance Analysis Report to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}

---

### Step 3: Review Architectural Optimization Opportunities (Day 3)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 1 day
**Input:** Performance Analysis Report
**Output:** Architecture recommendations

**Activities:**
{% if config.project.type == 'web-app' %}- Review application architecture (SSR vs CSR, code splitting)
- Validate caching strategy (CDN, browser cache, service worker)
- Recommend bundle optimization (tree shaking, lazy loading)
- Suggest infrastructure improvements (CDN, edge functions)
- Identify database optimization opportunities (indexing, query optimization)
- Review state management efficiency{% elif config.project.type == 'api' %}- Review API architecture (REST, GraphQL, gRPC)
- Validate caching strategy (Redis, CDN, HTTP caching)
- Recommend database optimization (indexing, denormalization, read replicas)
- Suggest infrastructure improvements (load balancing, auto-scaling)
- Identify connection pooling opportunities
- Review async/await patterns and concurrency{% elif config.project.type == 'data-platform' %}- Review data architecture (table design, partitioning)
{% if config.big_data_framework %}- Recommend {{ config.big_data_framework }} optimizations{% endif %}
- Suggest infrastructure improvements (cluster sizing, auto-scaling)
- Identify caching opportunities
- Review job orchestration and dependencies{% elif config.project.type == 'ml' %}- Review ML pipeline architecture (training, inference)
- Validate model serving strategy (batch vs real-time)
- Recommend infrastructure improvements (GPU selection, distributed training)
- Suggest feature store optimizations
- Identify model optimization opportunities (quantization, pruning){% else %}- Review system architecture
- Validate design patterns
- Recommend infrastructure improvements
- Identify optimization opportunities{% endif %}

**Deliverables:**
- Architecture review document
- Optimization recommendations (ranked by impact)
- Infrastructure recommendations
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost optimization opportunities{% endif %}

**Handoff:** Pass architecture recommendations to Performance Engineer

---

### Step 4: Implement Optimizations (Days 4-5)

**Agent:** Performance Engineer → Developers
**Duration:** 2 days
**Input:** Performance Analysis Report, Architecture recommendations
**Output:** Optimized code and configurations

**Activities:**

{% if config.project.type == 'web-app' %}**Frontend Optimizations:**
- Implement code splitting (lazy loading routes/components)
{% if config.web_framework and config.web_framework.frontend == 'react' %}- Use React.lazy() and Suspense
- Implement React.memo() for expensive components
- Optimize re-renders (useMemo, useCallback){% elif config.web_framework and config.web_framework.frontend == 'vue' %}- Use Vue async components
- Implement computed properties caching{% endif %}
- Optimize images (WebP, lazy loading, responsive images)
- Implement service worker caching
- Minify and compress bundles (Gzip, Brotli)
- Reduce bundle size (tree shaking, remove unused dependencies)
- Optimize fonts (font-display: swap, subset fonts)

**Backend Optimizations:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Optimize Python code (list comprehensions, generators)
- Implement database query optimization (select_related, prefetch_related in Django/SQLAlchemy){% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- Optimize Node.js event loop usage
- Implement database query optimization (Prisma/TypeORM includes){% endif %}
- Add database indexes
- Implement caching (Redis, in-memory cache)
- Optimize API payloads (GraphQL field selection, pagination){% elif config.project.type == 'api' %}**API Optimizations:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Optimize Python code (use async/await with FastAPI)
- Implement connection pooling (asyncpg, SQLAlchemy){% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- Optimize async patterns (Promise.all for parallel ops)
- Implement connection pooling{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}- Optimize thread pools and executors
- Implement JPA query optimization (fetch strategies){% endif %}
- Add database indexes on query columns
- Implement N+1 query fixes (batch loading, joins)
- Add caching layer (Redis for hot data)
- Implement response compression (Gzip)
- Optimize serialization (use efficient formats: Protocol Buffers, MessagePack)
- Implement request batching/debouncing

**Database Optimizations:**
{% if config.database and config.database.type == 'postgresql' %}- Add PostgreSQL indexes (B-tree, GiST, GIN)
- Implement materialized views
- Tune PostgreSQL configuration (work_mem, shared_buffers){% elif config.database and config.database.type == 'mysql' %}- Add MySQL indexes
- Optimize query cache
- Tune InnoDB buffer pool{% elif config.database and config.database.type == 'mongodb' %}- Add MongoDB indexes
- Implement aggregation pipeline optimization{% endif %}
- Denormalize where appropriate
- Implement read replicas for read-heavy workloads{% elif config.project.type == 'data-platform' %}**Data Pipeline Optimizations:**
{% if config.big_data_framework == 'Spark' %}- Optimize Spark jobs (broadcast joins, bucketing)
- Reduce shuffles (repartition strategically)
- Fix data skew (salting, AQE)
- Enable Adaptive Query Execution{% endif %}
{% if config.database %}- Optimize {{ config.database.type }} queries{% endif %}
- Implement partitioning and indexing
- Add caching for frequently accessed data
- Optimize file formats (Parquet, ORC)
- Tune parallelism and resource allocation{% elif config.project.type == 'ml' %}**ML Optimizations:**
- Optimize data loading
  {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Use PyTorch DataLoader with multiple workers
  - Implement prefetching{% endif %}
- Optimize model architecture (reduce parameters, pruning)
- Implement mixed-precision training (FP16)
- Use gradient checkpointing for memory efficiency
- Optimize batch sizes
- Implement model quantization for inference (INT8)
- Use model distillation (smaller student model)
- Implement batched inference
- Optimize feature engineering (vectorization, caching){% else %}**Code Optimizations:**
- Optimize algorithms (better time complexity)
- Reduce unnecessary computations
- Implement caching
- Optimize data structures
- Parallelize where possible{% endif %}

{% if config.cloud_provider %}**Infrastructure Optimizations:**
- Right-size {% if config.cloud_provider == 'AWS' %}EC2 instances{% elif config.cloud_provider == 'Azure' %}VMs{% elif config.cloud_provider == 'GCP' %}Compute Engine instances{% else %}compute resources{% endif %}
- Implement auto-scaling
{% if config.project.type == 'web-app' %}- Configure CDN caching{% endif %}
- Optimize network configuration
{% endif %}

**Deliverables:**
- Optimized code
{% if config.cloud_provider %}- Updated {{ config.cloud_provider }} configurations{% endif %}
- Configuration changes
- Optimization scripts

**Handoff:** Pass optimized code to Test Engineer

---

### Step 5: Create Performance Regression Tests (Day 6)

**Agent:** Test Engineer
**Duration:** 1 day
**Input:** Optimized code, performance requirements
**Output:** Performance regression test suite

**Activities:**
- Create benchmarking tests
{% if config.project.type == 'web-app' %}- Lighthouse CI for Core Web Vitals
- Bundle size tests (fail if >10% increase)
- Page load time tests (WebPageTest, Playwright){% elif config.project.type == 'api' %}- API load tests (k6, Artillery, Locust)
- Database query performance tests
- Memory leak tests{% elif config.project.type == 'data-platform' %}- Job runtime benchmarks
- Query performance tests
- Resource usage tests{% elif config.project.type == 'ml' %}- Training time benchmarks
- Inference latency tests
- Model accuracy vs performance trade-off tests{% endif %}
- Implement performance assertions (fail if >10% regression)
- Set up performance CI checks
- Document test datasets and expected metrics

**Deliverables:**
- Performance test suite
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- `tests/performance/test_*.py`{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- `tests/performance/*.test.ts`{% else %}- Performance tests{% endif %}
- Benchmarking scripts
- CI/CD integration (performance gates)
- Test documentation

**Handoff:** Pass tests to Performance Engineer for validation

---

### Step 6: Validate Improvements & Benchmark (Day 7)

**Agent:** Performance Engineer
**Duration:** 1 day
**Input:** Optimized code, performance tests
**Output:** Performance validation report with benchmarks

**Activities:**
- Run benchmarks (before vs after)
- Validate SLA requirements met
- Measure improvement metrics
{% if config.project.type == 'web-app' %}- Page load time improvement: X% faster
  - Bundle size reduction: X% smaller
  - Lighthouse score improvement: +X points{% elif config.project.type == 'api' %}- API latency improvement: X% faster (p95)
  - Throughput improvement: +X%
  - Cost reduction: X% lower{% elif config.project.type == 'data-platform' %}- Job runtime improvement: X% faster
  - Resource cost reduction: X% lower
  - Query latency improvement: X% faster{% elif config.project.type == 'ml' %}- Training time improvement: X% faster
  - Inference latency improvement: X% faster
  - GPU utilization improvement: +X%{% endif %}
- Confirm no correctness regressions (functionality unchanged)
- Calculate ROI {% if config.cloud_provider %}({{ config.cloud_provider }} cost savings){% else %}(cost savings){% endif %}

**Deliverables:**
- Before/after benchmark comparison
- Performance metrics
- Improvement summary (% faster, $ saved/month)
{% if config.project.type == 'web-app' %}- Lighthouse comparison reports{% elif config.project.type == 'api' %}- Flame graph comparisons{% elif config.project.type == 'data-platform' %}- Query plan comparisons{% elif config.project.type == 'ml' %}- Training profile comparisons{% endif %}
- Validation report

**Handoff:** Pass validation report and code to Documentation Engineer

---

### Step 7: Document Optimization Patterns (Day 8)

**Agent:** Documentation Engineer
**Duration:** 1 day
**Input:** All optimization artifacts, validation report
**Output:** Complete optimization documentation

**Activities:**
- Document optimization patterns applied
- Create before/after performance comparison
- Update performance best practices guide
- Document configuration changes
- Update {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %} with performance improvements
- Create runbook for future optimizations

**Deliverables:**
- Performance optimization documentation
- Best practices guide updates
- Runbook for common optimizations
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}

**Handoff:** Pass all code and documentation to Git Committer

---

### Step 8: Commit Optimized Code (Day 8)

**Agent:** Git Committer
**Duration:** 0.5 days
**Input:** All optimized code, tests, documentation
**Output:** Committed and pushed changes

**Activities:**
- Stage optimized code
- Stage performance tests
- Stage documentation updates
- Create descriptive commit message with metrics
- Push to remote repository

**Commit Message Example:**
```
perf: Optimize {% if config.project.type == 'web-app' %}page load performance{% elif config.project.type == 'api' %}API endpoint performance{% elif config.project.type == 'data-platform' %}data pipeline performance{% elif config.project.type == 'ml' %}model training performance{% else %}application performance{% endif %}

{% if config.project.type == 'web-app' %}Improvements:
- Page load time: 5.2s → 1.8s (65% faster)
- Bundle size: 2.1MB → 850KB (60% smaller)
- Lighthouse score: 67 → 94 (+27 points){% elif config.project.type == 'api' %}Improvements:
- API p95 latency: 850ms → 320ms (62% faster)
- Throughput: 500 req/s → 1,200 req/s (+140%)
- Database query time: 450ms → 85ms (81% faster){% elif config.project.type == 'data-platform' %}Improvements:
- Job runtime: 2.5h → 45min (70% faster)
- Resource cost: $45/run → $12/run (73% lower)
- Query latency: 38s → 8s (79% faster){% elif config.project.type == 'ml' %}Improvements:
- Training time: 18h → 6h (67% faster)
- Inference latency: 450ms → 95ms (79% faster)
- GPU utilization: 45% → 85% (+40%){% endif %}

{% if config.cloud_provider %}Cost savings: ~$X,XXX/month in {{ config.cloud_provider }} costs{% endif %}
```

**Deliverables:**
- Git commit with performance improvements
- Performance metrics in commit message
- Updated remote repository

**Completion:** Performance optimization workflow complete

---

## Workflow Diagram

```mermaid
graph LR
    A[Sprint Planning<br/>Identify Issues] --> B[Performance Engineer<br/>Analyze]
    B --> C[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Review Arch]
    C --> D[Performance + Devs<br/>Implement]
    D --> E[Test Engineer<br/>Regression Tests]
    E --> F[Performance Engineer<br/>Validate & Benchmark]
    F --> G[Documentation<br/>Document]
    G --> H[Git Committer<br/>Commit]
```

---

## Duration Estimates

| Phase | Agent | Duration | Cumulative |
|-------|-------|----------|------------|
| Identify Issues | Sprint Planning | 0.5 days | Day 0.5 |
| Analyze Performance | Performance Engineer | 1.5 days | Day 2 |
| Architecture Review | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 1 day | Day 3 |
| Implement Optimizations | Performance + Devs | 2 days | Day 5 |
| Regression Tests | Test Engineer | 1 day | Day 6 |
| Validate & Benchmark | Performance Engineer | 1 day | Day 7 |
| Document | Documentation Engineer | 1 day | Day 8 |
| Commit | Git Committer | 0.5 days | Day 8 |
| **Total** | | **8 days** | **~1.5 weeks** |

---

## Success Criteria

### Must Have
- [ ] Performance issues identified and prioritized
- [ ] Performance analysis completed with bottlenecks identified
- [ ] Architecture review completed
- [ ] Optimizations implemented
- [ ] Performance regression tests created
- [ ] SLA requirements met (benchmarks show improvement)
- [ ] Documentation updated

### Should Have
- [ ] % improvement meets or exceeds targets
{% if config.cloud_provider %}- [ ] {{ config.cloud_provider }} cost reduced{% endif %}
- [ ] No correctness regressions
- [ ] Performance CI gates in place

### Nice to Have
- [ ] Automated performance monitoring
- [ ] Performance dashboard created
- [ ] Optimization patterns documented for future reference

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Optimizations don't meet SLA** | Revisit architecture review, consider infrastructure changes |
| **Correctness regression** | Roll back optimization, add more tests, fix and re-validate |
{% if config.project.type == 'web-app' %}| **Bundle size increased** | Review dependencies, implement code splitting, tree shaking |{% endif %}
{% if config.project.type == 'api' %}| **N+1 queries persist** | Implement batch loading, use ORM includes/joins |{% endif %}
{% if config.project.type == 'data-platform' %}| **Data skew** | Implement salting, use adaptive query execution |{% endif %}
{% if config.project.type == 'ml' %}| **GPU underutilization** | Increase batch size, optimize data loading, use mixed precision |{% endif %}
{% if config.cloud_provider %}| **{{ config.cloud_provider }} costs increase** | Review resource sizing, implement auto-scaling, use spot instances |{% endif %}

---

## Integration with Other Workflows

**Triggers other workflows:**
- Testing & QA - Comprehensive testing after optimizations
- Documentation - Update performance best practices

**Invoked by:**
- Sprint Planning - Regular performance optimization cycles
- Production monitoring - When performance degrades
- Pre-release validation - Before major releases

---

## Related Documentation

**Agent Instructions:**
- `agents/quality/performance-engineer.md`
- `agents/planning/sprint-planning.md`
{% if config.architecture %}- `agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md`{% endif %}
- `agents/quality/test-engineer.md`
- `agents/documentation/documentation-engineer.md`

**Handoff Templates:**
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/performance-analysis-template.md`
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/performance-validation-template.md`

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
