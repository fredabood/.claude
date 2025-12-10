# CI Verification Setup Guide

Configure continuous integration to enforce roadmap integrity on your repository.

**Tasks:** git-integration-5-task-010, git-integration-5-task-012

## Table of Contents

- [Overview](#overview)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Other CI Systems](#other-ci-systems)
- [Troubleshooting](#troubleshooting)

---

## Overview

CI verification ensures that roadmap changes pushed to your repository have corresponding activity log entries, proving they were made through the Vibey CLI.

### How It Works

1. CI detects roadmap file changes (`.vibey/roadmap/**/*.yaml`)
2. Runs `vibey roadmap verify-commits` on the commit range
3. Checks each commit's roadmap files against the activity log
4. Blocks merge if unverified changes are found

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All commits verified |
| 1 | Some commits have unverified changes |
| 2 | Error occurred |

---

## GitHub Actions

### Quick Setup

Copy this workflow to `.github/workflows/roadmap-integrity.yml`:

```yaml
name: Roadmap Integrity

on:
  push:
    branches: [main, develop]
    paths:
      - '.vibey/roadmap/**/*.yaml'
  pull_request:
    branches: [main, develop]
    paths:
      - '.vibey/roadmap/**/*.yaml'

jobs:
  verify-activity-log:
    name: Verify Activity Log Entries
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Vibey
        run: |
          pip install -e .

      - name: Determine commit range
        id: commit-range
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            echo "range=${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }}" >> $GITHUB_OUTPUT
          else
            if [ "${{ github.event.before }}" = "0000000000000000000000000000000000000000" ]; then
              echo "range=HEAD~1..HEAD" >> $GITHUB_OUTPUT
            else
              echo "range=${{ github.event.before }}..${{ github.sha }}" >> $GITHUB_OUTPUT
            fi
          fi

      - name: Verify roadmap integrity
        run: |
          vibey roadmap verify-commits "${{ steps.commit-range.outputs.range }}"
```

### Advanced Configuration

Add PR comments on failure:

```yaml
      - name: Verify (with JSON output)
        id: verify
        run: |
          vibey roadmap verify-commits "${{ steps.commit-range.outputs.range }}" --json > result.json
        continue-on-error: true

      - name: Comment on PR
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const result = JSON.parse(fs.readFileSync('result.json', 'utf8'));
            let body = '## Roadmap Integrity Failed\n\n';
            body += `${result.failed_commits} commits have unverified changes.\n\n`;
            body += 'Please use `vibey roadmap` commands to modify roadmap files.';

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: body
            });

      - name: Fail job
        if: steps.verify.outcome != 'success'
        run: exit 1
```

---

## GitLab CI

### Quick Setup

Add this to your `.gitlab-ci.yml`:

```yaml
# Roadmap Integrity Verification
# Task: git-integration-5-task-010

stages:
  - verify

roadmap-integrity:
  stage: verify
  image: python:3.12-slim

  # Only run when roadmap files change
  rules:
    - changes:
        - .vibey/roadmap/**/*.yaml
      when: always
    - when: never

  before_script:
    - pip install -e .

  script:
    - echo "Verifying commits ${CI_COMMIT_BEFORE_SHA}..${CI_COMMIT_SHA}"
    - |
      if [ "$CI_COMMIT_BEFORE_SHA" = "0000000000000000000000000000000000000000" ]; then
        vibey roadmap verify-commits "HEAD~1..HEAD"
      else
        vibey roadmap verify-commits "${CI_COMMIT_BEFORE_SHA}..${CI_COMMIT_SHA}"
      fi

  # Fail the pipeline on verification failure
  allow_failure: false
```

### Merge Request Configuration

For merge request pipelines:

```yaml
roadmap-integrity:
  stage: verify
  image: python:3.12-slim

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - .vibey/roadmap/**/*.yaml
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      changes:
        - .vibey/roadmap/**/*.yaml
    - when: never

  before_script:
    - pip install -e .

  script:
    - |
      if [ "$CI_PIPELINE_SOURCE" = "merge_request_event" ]; then
        # For MRs, compare against target branch
        git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
        vibey roadmap verify-commits "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}..HEAD"
      else
        # For pushes, use before/after
        vibey roadmap verify-commits "${CI_COMMIT_BEFORE_SHA}..${CI_COMMIT_SHA}"
      fi
```

### With Artifacts

Save verification results:

```yaml
roadmap-integrity:
  stage: verify
  image: python:3.12-slim

  rules:
    - changes:
        - .vibey/roadmap/**/*.yaml

  before_script:
    - pip install -e .

  script:
    - vibey roadmap verify-commits "${CI_COMMIT_BEFORE_SHA}..${CI_COMMIT_SHA}" --json > verification-result.json

  artifacts:
    when: always
    paths:
      - verification-result.json
    expire_in: 30 days
```

---

## Other CI Systems

### Generic Configuration

For any CI system, the basic pattern is:

```bash
# 1. Install Vibey
pip install vibey  # or: pip install -e .

# 2. Get commit range
# For pushes: $BEFORE_SHA..$AFTER_SHA
# For PRs: $BASE_SHA..$HEAD_SHA

# 3. Run verification
vibey roadmap verify-commits "$BEFORE_SHA..$AFTER_SHA"

# Exit code will be:
# 0 = success (all verified)
# 1 = failure (unverified changes)
# 2 = error
```

### CircleCI Example

```yaml
version: 2.1

jobs:
  roadmap-verify:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run:
          name: Install Vibey
          command: pip install -e .
      - run:
          name: Verify roadmap integrity
          command: |
            vibey roadmap verify-commits origin/main..HEAD

workflows:
  verify:
    jobs:
      - roadmap-verify:
          filters:
            branches:
              ignore: main
```

### Jenkins Example

```groovy
pipeline {
    agent { docker { image 'python:3.12-slim' } }

    stages {
        stage('Verify Roadmap') {
            when {
                changeset ".vibey/roadmap/**/*.yaml"
            }
            steps {
                sh 'pip install -e .'
                sh 'vibey roadmap verify-commits origin/main..HEAD'
            }
        }
    }
}
```

---

## Troubleshooting

### Common Issues

#### "No commits found in range"

**Cause:** Invalid commit range or shallow clone

**Fix:**
```bash
# Ensure full history is available
git fetch --unshallow  # or fetch-depth: 0 in CI

# Verify range is valid
git log --oneline $BEFORE..$AFTER
```

#### "Command not found: vibey"

**Cause:** Vibey not installed or not in PATH

**Fix:**
```bash
# Ensure Vibey is installed
pip install -e .

# Or use Python module directly
python -m vibey.cli.main roadmap verify-commits ...
```

#### "Activity log not found"

**Cause:** Activity log directory doesn't exist

**Fix:**
```bash
# Ensure activity log exists
ls -la .vibey/roadmap/activity_log/

# If missing, create it
mkdir -p .vibey/roadmap/activity_log
```

#### Verification always fails

**Cause:** Manual YAML edits instead of CLI commands

**Fix:**
1. Revert the manual changes
2. Use CLI commands to make changes:
   ```bash
   vibey roadmap start <task-id>
   vibey roadmap complete <task-id>
   vibey roadmap update task <id> --status <status>
   ```
3. Commit and push again

### Debug Mode

Run with verbose output:

```bash
# Human-readable output
vibey roadmap verify-commits main..HEAD

# JSON output for parsing
vibey roadmap verify-commits main..HEAD --json | jq .
```

### Bypass CI Verification

For emergencies only:

1. **GitHub Actions:** Add `[skip ci]` to commit message
2. **GitLab CI:** Add `[ci skip]` to commit message
3. **All platforms:** Temporarily remove the workflow file

**Warning:** Bypassing verification defeats the purpose of integrity protection. Only use in genuine emergencies.

---

## Best Practices

1. **Always use CLI commands** - Never edit `.vibey/roadmap/*.yaml` files directly
2. **Full history in CI** - Use `fetch-depth: 0` for accurate verification
3. **Block merges** - Configure branch protection to require passing CI
4. **Monitor bypass log** - Check `.vibey/audit/bypass.log` regularly

---

**Last Updated:** 2025-12-10
**Version:** 1.0 (Git Integration Sprint 5)
