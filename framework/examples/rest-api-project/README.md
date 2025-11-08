# Example: Task Manager REST API

This example demonstrates a complete roadmap setup for building a REST API for a task management application.

## Project Overview

**Goal:** Build a production-ready REST API for task management with authentication, CRUD operations, and user management.

**Duration:** 6 weeks
**Sprints:** 3
**Total Tasks:** 24

## Roadmap Structure

```
Task Manager API (roadmap)
  └── REST API Development (track)
      ├── Sprint 1: Authentication & User Management (8 tasks)
      ├── Sprint 2: Task CRUD Operations (10 tasks)
      └── Sprint 3: Advanced Features & Polish (6 tasks)
```

## Quick Start

```bash
# Copy this example to your project
cp -r rest-api-project/.vibey /path/to/your-project/

# Initialize roadmap CLI
cd /path/to/your-project
export PATH="$PATH:/path/to/vibey/framework/scripts"

# View status
roadmap status

# Start first sprint
roadmap start api-1

# Get recommended task
roadmap recommend

# Start working
roadmap start api-1-task-001
```

## Files Included

```
rest-api-project/
└── .vibey/
    ├── roadmap.yaml                 # Roadmap root
    ├── tracks/
    │   └── api.yaml                 # REST API track
    ├── sprints/
    │   ├── api-1.yaml               # Sprint 1: Auth
    │   ├── api-2.yaml               # Sprint 2: CRUD
    │   └── api-3.yaml               # Sprint 3: Advanced
    └── tasks/
        ├── api-1-tasks.yaml         # Sprint 1 tasks
        ├── api-2-tasks.yaml         # Sprint 2 tasks
        └── api-3-tasks.yaml         # Sprint 3 tasks
```

## Technology Stack

- **Language:** Python 3.9+
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Auth:** JWT (bcrypt for passwords)
- **Testing:** pytest
- **Documentation:** OpenAPI/Swagger

## Key Features

✅ **User Authentication** - Registration, login, logout with JWT
✅ **Task Management** - Full CRUD operations for tasks
✅ **User Management** - Profile management
✅ **Filtering & Search** - Query tasks by status, priority, tags
✅ **Pagination** - Efficient data loading
✅ **Rate Limiting** - API protection
✅ **Comprehensive Testing** - 90%+ coverage
✅ **Full Documentation** - Auto-generated API docs

## Sprint Breakdown

### Sprint 1: Authentication & User Management (2 weeks)

**Tasks:**
1. Design database schema for users
2. Implement user registration endpoint
3. Implement login endpoint
4. Implement logout endpoint
5. Implement authentication middleware
6. **Gate:** Write unit tests for authentication
7. **Gate:** Security audit of authentication
8. **Gate:** Write API documentation for auth endpoints

**Deliverables:**
- User registration with email validation
- Login with JWT tokens
- Session management
- 90%+ test coverage
- Security reviewed
- API documentation

### Sprint 2: Task CRUD Operations (2 weeks)

**Tasks:**
1. Design task database schema
2. Implement create task endpoint
3. Implement get task endpoint
4. Implement list tasks endpoint
5. Implement update task endpoint
6. Implement delete task endpoint
7. Add filtering and search
8. **Gate:** Write unit tests for task endpoints
9. **Gate:** Write integration tests
10. **Gate:** Document all task API endpoints

**Deliverables:**
- Full CRUD operations for tasks
- Filtering by status, priority, tags
- Search functionality
- Pagination support
- 90%+ test coverage
- API documentation

### Sprint 3: Advanced Features & Polish (2 weeks)

**Tasks:**
1. Implement user profile endpoints
2. Add rate limiting middleware
3. Add request/response logging
4. Performance optimization
5. **Gate:** Performance testing
6. **Gate:** Final security review

**Deliverables:**
- User profile management
- Rate limiting (100 req/min)
- Comprehensive logging
- Performance optimized (<100ms avg response time)
- Production-ready

## Dependency Chain

```
Sprint 1 (Auth)
    └─> Sprint 2 (Tasks) [Need auth before task operations]
            └─> Sprint 3 (Advanced) [Need core functionality before polish]
```

## Quality Gates

### Sprint 1 Gates
- Unit Tests (≥90% coverage)
- Security Review (≥95% score)
- API Documentation (100% complete)

### Sprint 2 Gates
- Unit Tests (≥90% coverage)
- Integration Tests (≥85% coverage)
- API Documentation (100% complete)

### Sprint 3 Gates
- Performance Tests (<100ms avg)
- Final Security Review (≥95% score)

## Agent Assignments

**Recommended agents for this project:**
- **web-developer** - All development tasks (APIs, endpoints, middleware)
- **test-engineer** - All testing gates
- **security-auditor** - Security review gates
- **docs-writer** - Documentation gates
- **performance-engineer** - Performance optimization

## Usage Example

```bash
# Day 1: Start sprint 1
roadmap start api-1
roadmap recommend --agent web-developer
# Output: api-1-task-001 (Design database schema)

roadmap start api-1-task-001
roadmap assign api-1-task-001 web-developer

# Complete and move to next
roadmap complete api-1-task-001
roadmap recommend --agent web-developer
# Output: api-1-task-002 (Implement registration endpoint)

# Day 7: Check progress
roadmap show api-1
# Shows: 5/8 tasks complete (62%)

# Day 10: Sprint auto-progresses to completion_gate_check
roadmap show api-1
# Status: completion_gate_check

# Work on gates
roadmap recommend --agent test-engineer
roadmap start api-1-task-gate-001
roadmap assign api-1-task-gate-001 test-engineer

# Day 14: Complete sprint
roadmap complete api-1
roadmap version --show
# Version: 0.1.1 (auto-bumped)

# Start sprint 2
roadmap start api-2
```

## Expected Timeline

| Week | Sprint | Focus | Status |
|------|--------|-------|--------|
| 1-2  | Sprint 1 | Authentication | ✅ completed |
| 3-4  | Sprint 2 | Task CRUD | 🔵 in_progress |
| 5-6  | Sprint 3 | Polish | ⚪ not_started |

## Success Criteria

✅ All 24 tasks completed
✅ All quality gates passed
✅ 90%+ test coverage
✅ Security score ≥95%
✅ API documentation 100% complete
✅ Performance <100ms avg response time
✅ Ready for production deployment

## Next Steps After Completion

1. **Deploy to production** - Use infrastructure track for deployment
2. **Monitor performance** - Set up observability
3. **Iterate on features** - Create new tracks for v2 features
4. **Scale** - Plan horizontal scaling track

---

**This example demonstrates:**
- Complete roadmap structure
- Sprint planning with dependencies
- Quality gate enforcement
- Agent routing recommendations
- Progress tracking
- Version management
