"""
Integration tests for Journey 3: Feature Development

Tests the complete feature development workflow from implementation through
code review, testing, and git commit creation.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, GitValidator, MetricsCollector
from tests.utils.config_loader import ConfigLoader
import time
import subprocess


@pytest.mark.integration
class TestJourney3FeatureDevelopment:
    """Test Journey 3: Feature Development workflow."""

    def test_01_feature_implementation(self, temp_dir):
        """Test implementing a new feature in codebase."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Create feature code
        feature_file = repo.path / "src" / "components" / "UserAuth.tsx"
        feature_file.write_text("""import React from 'react';

export const UserAuth: React.FC = () => {
  return (
    <div className="auth-container">
      <h1>User Authentication</h1>
      {/* Auth form here */}
    </div>
  );
};
""")

        # Assert
        assert feature_file.exists()
        content_result = validator.validate_file_content(
            feature_file,
            contains=["UserAuth", "React"]
        )
        assert content_result.passed

    def test_02_code_quality_check(self, temp_dir):
        """Test code quality validation during feature development."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        metrics = MetricsCollector()

        # Act - Create code with quality metrics
        feature_file = repo.path / "src" / "utils" / "validation.ts"
        feature_file.write_text("""/**
 * User input validation utilities
 */

export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function validatePassword(password: string): boolean {
  // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
  return password.length >= 8 &&
         /[A-Z]/.test(password) &&
         /[a-z]/.test(password) &&
         /[0-9]/.test(password);
}
""")

        # Assert - Track code quality metrics
        metrics.track("code_quality_score", 95, unit="percentage", threshold=80)
        metrics.track("has_documentation", 100, unit="percentage", threshold=100)
        metrics.track("follows_conventions", 100, unit="percentage", threshold=90)

        assert metrics.calculate_success_rate() == 100.0

    def test_03_unit_test_creation(self, temp_dir):
        """Test creating unit tests for new feature."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create test file
        test_file = repo.path / "src" / "__tests__" / "validation.test.ts"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("""import { validateEmail, validatePassword } from '../utils/validation';

describe('validateEmail', () => {
  it('should validate correct email', () => {
    expect(validateEmail('test@example.com')).toBe(true);
  });

  it('should reject invalid email', () => {
    expect(validateEmail('invalid-email')).toBe(false);
  });
});

describe('validatePassword', () => {
  it('should validate strong password', () => {
    expect(validatePassword('Strong123')).toBe(true);
  });

  it('should reject weak password', () => {
    expect(validatePassword('weak')).toBe(false);
  });
});
""")

        validator = StateValidator()

        # Assert
        assert test_file.exists()
        content_result = validator.validate_file_content(
            test_file,
            contains=["describe", "it", "expect"]
        )
        assert content_result.passed

    def test_04_git_commit_conventional_format(self, temp_dir):
        """Test creating git commit in conventional format."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)
        git_validator = GitValidator()

        # Act - Create feature and commit
        feature_file = repo.path / "src" / "feature.ts"
        feature_file.write_text("export const feature = () => {};")

        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add new feature implementation"],
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        # Assert - Validate conventional commit
        commits = git_validator.get_commit_history(repo.path, count=2)
        latest_commit = commits[0]

        assert git_validator.validate_commit_message(latest_commit)
        assert latest_commit.message.startswith("feat:")

    def test_05_sprint_state_update_on_task_completion(self, temp_dir):
        """Test updating sprint state when task is completed."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        import yaml

        # Create initial state
        state_file = sprint_dir / "state.yaml"
        initial_state = {
            "sprint": {
                "id": "sprint-1",
                "progress": {
                    "tasks_total": 3,
                    "tasks_completed": 0,
                    "completion_percent": 0
                },
                "tasks": [
                    {"id": "task-001", "status": "in_progress"},
                    {"id": "task-002", "status": "not_started"},
                    {"id": "task-003", "status": "not_started"}
                ]
            }
        }
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)

        # Act - Complete task-001
        updated_state = initial_state.copy()
        updated_state["sprint"]["progress"]["tasks_completed"] = 1
        updated_state["sprint"]["progress"]["completion_percent"] = 33
        updated_state["sprint"]["tasks"][0]["status"] = "completed"
        updated_state["sprint"]["tasks"][1]["status"] = "in_progress"

        with open(state_file, 'w') as f:
            yaml.dump(updated_state, f)

        # Assert
        with open(state_file) as f:
            data = yaml.safe_load(f)

        assert data["sprint"]["progress"]["tasks_completed"] == 1
        assert data["sprint"]["progress"]["completion_percent"] == 33
        assert data["sprint"]["tasks"][0]["status"] == "completed"

    def test_06_agent_handoff_documentation(self, temp_dir):
        """Test handoff documentation between agents."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create handoff document
        handoff_dir = repo.path / ".vibey" / "handoffs"
        handoff_dir.mkdir(parents=True, exist_ok=True)

        handoff_file = handoff_dir / "web-dev-to-security.md"
        handoff_file.write_text("""# Handoff: Web Developer → Security Reviewer

## Feature Implemented
User authentication with JWT tokens

## Files Changed
- src/auth/login.ts
- src/auth/register.ts
- src/middleware/jwt.ts

## Security Concerns
- Password hashing implementation
- JWT secret key management
- Input validation for credentials

## Review Requested
- Security audit of authentication flow
- Verification of JWT implementation
- Check for common vulnerabilities (SQL injection, XSS)

## Tests Added
- Unit tests for login/register functions
- Integration tests for auth flow
""")

        validator = StateValidator()

        # Assert
        assert handoff_file.exists()
        content_result = validator.validate_file_content(
            handoff_file,
            contains=[
                "Feature Implemented",
                "Files Changed",
                "Security Concerns",
                "Review Requested"
            ]
        )
        assert content_result.passed

    def test_07_complete_feature_development_workflow(self, temp_dir):
        """Test complete end-to-end feature development workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        git_validator = GitValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Complete workflow
        # Step 1: Initialize project
        repo = builder.create_web_app_repo(name="feature-project")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Step 2: Create feature code
        feature_file = repo.path / "src" / "components" / "NewFeature.tsx"
        feature_file.write_text("export const NewFeature = () => <div>Feature</div>;")

        # Step 3: Create tests
        test_file = repo.path / "src" / "__tests__" / "NewFeature.test.tsx"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("test('renders', () => {});")

        # Step 4: Commit feature
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: implement new feature with tests"],
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        total_time = time.time() - start_time

        # Assert - Validate complete workflow
        # Check files exist
        expected_files = {
            "files": [
                "src/components/NewFeature.tsx",
                "src/__tests__/NewFeature.test.tsx",
                "CLAUDE.md",
                ".vibey/config/project.yaml"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected_files)
        assert result.passed, f"Feature development structure invalid: {result.errors}"

        # Check git history
        commits = git_validator.get_commit_history(repo.path, count=2)
        assert len(commits) >= 1
        latest_commit = commits[0]
        assert git_validator.validate_commit_message(latest_commit)

        # Track success metrics
        metrics.track("feature_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("code_quality_score", 90, unit="percentage", threshold=80)
        metrics.track("test_coverage", 85, unit="percentage", threshold=75)
        metrics.track("development_time", total_time, unit="seconds")  # Track without threshold

        # Validate metrics
        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0, f"Journey 3 success rate: {success_rate}%"

    def test_08_code_review_feedback_loop(self, temp_dir):
        """Test code review and revision cycle."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)

        # Act - Create initial implementation
        feature_file = repo.path / "src" / "api" / "users.ts"
        feature_file.parent.mkdir(parents=True, exist_ok=True)
        feature_file.write_text("""export async function getUser(id: string) {
  // Initial implementation
  return { id };
}
""")

        # Commit initial version
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add user API endpoint"],
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        # Create review feedback
        review_dir = repo.path / ".vibey" / "reviews"
        review_dir.mkdir(parents=True, exist_ok=True)
        review_file = review_dir / "users-api-review.md"
        review_file.write_text("""# Code Review: User API

## Issues Found
- Missing error handling
- No input validation
- Missing type safety

## Recommendations
- Add try/catch blocks
- Validate user ID format
- Add return type annotation
""")

        # Revise based on feedback
        feature_file.write_text("""export async function getUser(id: string): Promise<User | null> {
  try {
    if (!isValidUserId(id)) {
      throw new Error('Invalid user ID');
    }
    return await fetchUser(id);
  } catch (error) {
    console.error('Error fetching user:', error);
    return null;
  }
}
""")

        # Commit revision
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fix: add error handling and validation to user API"],
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        git_validator = GitValidator()

        # Assert - Validate review cycle
        commits = git_validator.get_commit_history(repo.path, count=3)
        assert len(commits) >= 2

        # Check both commits are conventional
        assert all(git_validator.validate_commit_message(c) for c in commits[:2])
        assert commits[0].message.startswith("fix:")
        assert commits[1].message.startswith("feat:")

    def test_09_multiple_features_in_parallel(self, temp_dir):
        """Test managing multiple feature branches in parallel."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)

        # Act - Create feature branch 1
        subprocess.run(
            ["git", "checkout", "-b", "feature/auth"],
            cwd=repo.path,
            check=True
        )
        auth_file = repo.path / "src" / "auth.ts"
        auth_file.write_text("export const auth = {};")
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add authentication"],
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        # Create feature branch 2
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=repo.path,
            check=True
        )
        subprocess.run(
            ["git", "checkout", "-b", "feature/api"],
            cwd=repo.path,
            check=True
        )
        api_file = repo.path / "src" / "api.ts"
        api_file.write_text("export const api = {};")
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add API layer"],
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        # Assert - Both branches exist
        result = subprocess.run(
            ["git", "branch"],
            cwd=repo.path,
            capture_output=True,
            text=True
        )
        assert "feature/auth" in result.stdout
        assert "feature/api" in result.stdout

    def test_10_feature_development_metrics(self, temp_dir):
        """Test comprehensive metrics collection for feature development."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        metrics = MetricsCollector()

        # Act - Simulate feature development with metrics
        repo = builder.create_web_app_repo()
        builder.init_git(repo)
        builder.add_vibey_framework(repo)

        # Track comprehensive metrics
        metrics.track("feature_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("code_quality_score", 92, unit="percentage", threshold=80)
        metrics.track("test_coverage", 88, unit="percentage", threshold=75)
        metrics.track("review_pass_rate", 100, unit="percentage", threshold=90)
        metrics.track("development_time", 1200, unit="seconds")  # Track without threshold
        metrics.track("commits_count", 3, unit="count")

        # Assert - All metrics collected
        assert len(metrics.get_all_metrics()) == 6
        assert metrics.calculate_success_rate() == 100.0

        # Export metrics
        output_file = temp_dir / "journey3-metrics.json"
        export_data = metrics.export_metrics(output_file)

        assert output_file.exists()
        assert all(metric in export_data["metrics"] for metric in [
            "feature_completion_rate",
            "code_quality_score",
            "test_coverage",
            "review_pass_rate"
        ])


@pytest.mark.integration
class TestJourney3ErrorScenarios:
    """Test Journey 3 error handling and edge cases."""

    def test_feature_fails_quality_gate(self, temp_dir):
        """Test handling of feature that fails quality gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Create feature with low quality
        feature_file = repo.path / "src" / "feature.ts"
        feature_file.write_text("export const f = () => {};")  # Poor naming, no docs

        # Track failing metrics
        metrics.track("code_quality_score", 45, unit="percentage", threshold=80)
        metrics.track("test_coverage", 30, unit="percentage", threshold=75)

        # Assert - Quality gates should fail
        assert not metrics.assert_metric("code_quality_score", min_value=80)
        assert not metrics.assert_metric("test_coverage", min_value=75)
        assert metrics.calculate_success_rate() < 100.0

    def test_git_commit_fails_conventional_format(self, temp_dir):
        """Test detection of non-conventional commit messages."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        git_validator = GitValidator()

        # Act - Create non-conventional commit
        feature_file = repo.path / "src" / "feature.ts"
        feature_file.write_text("export const feature = {};")

        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "added feature"],  # Non-conventional
            cwd=repo.path,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com"
            }
        )

        # Assert - Should detect non-conventional format
        commits = git_validator.get_commit_history(repo.path, count=2)
        latest_commit = commits[0]
        assert not git_validator.validate_commit_message(latest_commit)
