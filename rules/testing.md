---
description: Testing standards and behavioral instructions — tests are required for all implementation work, not optional
globs:
  - "**/*"
---

# Testing Rules

## Behavioral Instructions (always active)

These apply to all implementation work, not just test files:

- **Tests are required, not optional.** Before marking work complete, verify:
  - Unit tests cover the changed business logic (target 90%+ on new code)
  - Integration tests exist for any new external service interactions
  - Edge cases and error paths are tested

- **Test-first when possible:**
  - For bug fixes, write a failing test that reproduces the bug before fixing it
  - For new features, write test scenarios during the planning phase

- **Testing is part of acceptance criteria:** Every ticket's acceptance criteria must include at least one test-based criterion (`Tests pass: <command>`).

- **On `/complete-task`:** The test suite must pass as a hard gate. Test coverage on changed files must not decrease.

## Standards for Test Code

When writing or modifying tests:

1. **Follow AAA pattern** — Arrange, Act, Assert in every test
2. **One concern per test** — each test should verify a single behavior
3. **Use descriptive names** — `test_user_registration_fails_with_invalid_email` not `test_reg`
4. **Mock external dependencies** — APIs, databases, file systems should be mocked in unit tests
5. **Use fixtures for shared setup** — don't repeat test data construction
6. **Test edge cases** — empty inputs, boundary values, error paths, concurrent access
7. **Keep unit tests fast** — each should complete in <1 second
8. **No real credentials in tests** — use clearly fake test data
9. **Aim for 90%+ coverage on business logic** — focus on critical paths, not getters/setters
10. **Integration tests hit real services** — use test databases or containers, not mocks
