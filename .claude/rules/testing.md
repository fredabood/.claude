---
description: Testing standards for test files and test directories
globs:
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/tests/**"
  - "**/test_*"
  - "**/__tests__/**"
---

# Testing Rules

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
