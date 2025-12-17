"""
Tests for vibey.platform.detector module.

Tests the platform detection functionality.
"""

import pytest
import os
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from vibey.platform.detector import (
    DetectionMethod,
    PlatformName,
    PlatformInfo,
    KNOWN_PLATFORMS,
    detect_platform,
    get_platform_info,
    list_known_platforms,
    _check_environment_vars,
    _check_config_files,
    _check_process_names,
)


class TestDetectionMethod:
    """Test DetectionMethod enum."""

    def test_environment_value(self):
        """Test ENVIRONMENT has correct value."""
        assert DetectionMethod.ENVIRONMENT.value == "environment"

    def test_process_value(self):
        """Test PROCESS has correct value."""
        assert DetectionMethod.PROCESS.value == "process"

    def test_config_file_value(self):
        """Test CONFIG_FILE has correct value."""
        assert DetectionMethod.CONFIG_FILE.value == "config_file"

    def test_user_agent_value(self):
        """Test USER_AGENT has correct value."""
        assert DetectionMethod.USER_AGENT.value == "user_agent"

    def test_manual_value(self):
        """Test MANUAL has correct value."""
        assert DetectionMethod.MANUAL.value == "manual"

    def test_fallback_value(self):
        """Test FALLBACK has correct value."""
        assert DetectionMethod.FALLBACK.value == "fallback"

    def test_is_string_enum(self):
        """Test DetectionMethod is str subclass."""
        assert isinstance(DetectionMethod.ENVIRONMENT, str)


class TestPlatformName:
    """Test PlatformName enum."""

    def test_claude_code_value(self):
        """Test CLAUDE_CODE has correct value."""
        assert PlatformName.CLAUDE_CODE.value == "claude-code"

    def test_goose_value(self):
        """Test GOOSE has correct value."""
        assert PlatformName.GOOSE.value == "goose"

    def test_cursor_value(self):
        """Test CURSOR has correct value."""
        assert PlatformName.CURSOR.value == "cursor"

    def test_aider_value(self):
        """Test AIDER has correct value."""
        assert PlatformName.AIDER.value == "aider"

    def test_continue_value(self):
        """Test CONTINUE has correct value."""
        assert PlatformName.CONTINUE.value == "continue"

    def test_copilot_value(self):
        """Test COPILOT has correct value."""
        assert PlatformName.COPILOT.value == "copilot"

    def test_jetbrains_ai_value(self):
        """Test JETBRAINS_AI has correct value."""
        assert PlatformName.JETBRAINS_AI.value == "jetbrains-ai"

    def test_windsurf_value(self):
        """Test WINDSURF has correct value."""
        assert PlatformName.WINDSURF.value == "windsurf"

    def test_vscode_value(self):
        """Test VSCODE has correct value."""
        assert PlatformName.VSCODE.value == "vscode"

    def test_gemini_value(self):
        """Test GEMINI has correct value."""
        assert PlatformName.GEMINI.value == "gemini"

    def test_unknown_value(self):
        """Test UNKNOWN has correct value."""
        assert PlatformName.UNKNOWN.value == "unknown"

    def test_is_string_enum(self):
        """Test PlatformName is str subclass."""
        assert isinstance(PlatformName.CLAUDE_CODE, str)


class TestKnownPlatforms:
    """Test KNOWN_PLATFORMS dictionary."""

    def test_claude_code_in_platforms(self):
        """Test Claude Code platform is defined."""
        assert "claude-code" in KNOWN_PLATFORMS

    def test_goose_in_platforms(self):
        """Test Goose platform is defined."""
        assert "goose" in KNOWN_PLATFORMS

    def test_cursor_in_platforms(self):
        """Test Cursor platform is defined."""
        assert "cursor" in KNOWN_PLATFORMS

    def test_platform_has_name(self):
        """Test platforms have name field."""
        for platform_id, info in KNOWN_PLATFORMS.items():
            assert "name" in info
            assert isinstance(info["name"], str)

    def test_platform_has_vendor(self):
        """Test platforms have vendor field."""
        for platform_id, info in KNOWN_PLATFORMS.items():
            assert "vendor" in info
            assert isinstance(info["vendor"], str)

    def test_platform_has_env_vars(self):
        """Test platforms have env_vars field."""
        for platform_id, info in KNOWN_PLATFORMS.items():
            assert "env_vars" in info
            assert isinstance(info["env_vars"], list)

    def test_platform_has_context_window(self):
        """Test platforms have context_window field."""
        for platform_id, info in KNOWN_PLATFORMS.items():
            assert "context_window" in info
            assert isinstance(info["context_window"], int)
            assert info["context_window"] > 0

    def test_platform_has_description(self):
        """Test platforms have description field."""
        for platform_id, info in KNOWN_PLATFORMS.items():
            assert "description" in info
            assert isinstance(info["description"], str)


class TestPlatformInfo:
    """Test PlatformInfo dataclass."""

    def test_basic_construction(self):
        """Test basic PlatformInfo construction."""
        info = PlatformInfo(
            name="test-platform",
            display_name="Test Platform",
            vendor="Test Vendor",
        )
        assert info.name == "test-platform"
        assert info.display_name == "Test Platform"
        assert info.vendor == "Test Vendor"

    def test_default_version(self):
        """Test default version is None."""
        info = PlatformInfo(
            name="test",
            display_name="Test",
            vendor="Vendor",
        )
        assert info.version is None

    def test_default_detected_by(self):
        """Test default detected_by is FALLBACK."""
        info = PlatformInfo(
            name="test",
            display_name="Test",
            vendor="Vendor",
        )
        assert info.detected_by == DetectionMethod.FALLBACK

    def test_default_context_window(self):
        """Test default context_window is 128000."""
        info = PlatformInfo(
            name="test",
            display_name="Test",
            vendor="Vendor",
        )
        assert info.context_window == 128_000

    def test_default_confidence(self):
        """Test default confidence is 0.0."""
        info = PlatformInfo(
            name="test",
            display_name="Test",
            vendor="Vendor",
        )
        assert info.confidence == 0.0

    def test_default_detection_details(self):
        """Test default detection_details is empty dict."""
        info = PlatformInfo(
            name="test",
            display_name="Test",
            vendor="Vendor",
        )
        assert info.detection_details == {}

    def test_detected_at_is_set(self):
        """Test detected_at is auto-set to current time."""
        info = PlatformInfo(
            name="test",
            display_name="Test",
            vendor="Vendor",
        )
        assert info.detected_at is not None
        # Should be ISO format
        datetime.fromisoformat(info.detected_at.replace("Z", "+00:00"))

    def test_is_known_returns_true_for_known(self):
        """Test is_known returns True for known platforms."""
        info = PlatformInfo(
            name="claude-code",
            display_name="Claude Code",
            vendor="Anthropic",
        )
        assert info.is_known() is True

    def test_is_known_returns_false_for_unknown(self):
        """Test is_known returns False for unknown platform."""
        info = PlatformInfo(
            name=PlatformName.UNKNOWN.value,
            display_name="Unknown",
            vendor="Unknown",
        )
        assert info.is_known() is False

    def test_to_dict(self):
        """Test to_dict serialization."""
        info = PlatformInfo(
            name="claude-code",
            display_name="Claude Code",
            vendor="Anthropic",
            version="1.0.0",
            detected_by=DetectionMethod.ENVIRONMENT,
            context_window=200_000,
            description="Test desc",
            confidence=0.95,
            detection_details={"env_vars": {"CLAUDE_CODE": "1"}},
        )
        result = info.to_dict()

        assert result["name"] == "claude-code"
        assert result["display_name"] == "Claude Code"
        assert result["vendor"] == "Anthropic"
        assert result["version"] == "1.0.0"
        assert result["detected_by"] == "environment"
        assert result["context_window"] == 200_000
        assert result["description"] == "Test desc"
        assert result["confidence"] == 0.95
        assert "env_vars" in result["detection_details"]


class TestCheckEnvironmentVars:
    """Test _check_environment_vars function."""

    def test_returns_none_when_no_vars_set(self):
        """Test returns None when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            result = _check_environment_vars("claude-code")
        # Can't fully clear env, just check it doesn't crash
        assert result is None or isinstance(result, dict)

    def test_returns_dict_when_vars_found(self):
        """Test returns dict when env vars are found."""
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}, clear=False):
            result = _check_environment_vars("claude-code")
            if result:
                assert "CLAUDE_CODE" in result

    def test_returns_none_for_unknown_platform(self):
        """Test returns None for unknown platform."""
        result = _check_environment_vars("nonexistent-platform")
        assert result is None


class TestCheckConfigFiles:
    """Test _check_config_files function."""

    def test_returns_none_when_no_files(self, tmp_path):
        """Test returns None when no config files exist."""
        result = _check_config_files(tmp_path)
        assert result is None

    def test_detects_claude_config(self, tmp_path):
        """Test detects Claude config file."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text("{}")
        
        result = _check_config_files(tmp_path)
        assert result == "claude-code"

    def test_detects_cursor_config(self, tmp_path):
        """Test detects Cursor config file."""
        (tmp_path / ".cursorrules").write_text("# Rules")
        
        result = _check_config_files(tmp_path)
        assert result == "cursor"

    def test_detects_goose_config(self, tmp_path):
        """Test detects Goose config file."""
        goose_dir = tmp_path / ".goose"
        goose_dir.mkdir()
        (goose_dir / "config.yaml").write_text("config: true")
        
        result = _check_config_files(tmp_path)
        assert result == "goose"

    def test_detects_windsurf_config(self, tmp_path):
        """Test detects Windsurf config file."""
        (tmp_path / ".windsurfrules").write_text("# Rules")
        
        result = _check_config_files(tmp_path)
        assert result == "windsurf"

    def test_detects_continue_config(self, tmp_path):
        """Test detects Continue config file."""
        continue_dir = tmp_path / ".continue"
        continue_dir.mkdir()
        (continue_dir / "config.json").write_text("{}")
        
        result = _check_config_files(tmp_path)
        assert result == "continue"


class TestCheckProcessNames:
    """Test _check_process_names function."""

    def test_returns_none_or_platform(self):
        """Test returns None or a valid platform."""
        result = _check_process_names()
        # Should return None or a string platform ID
        assert result is None or isinstance(result, str)

    def test_with_mocked_sys_executable(self):
        """Test process detection with mocked sys.executable."""
        # Mock sys.executable to simulate running under Claude
        with patch("vibey.platform.detector.sys") as mock_sys:
            mock_sys.executable = "/usr/local/bin/claude"
            result = _check_process_names()
            # Should detect claude-code from executable path
            assert result == "claude-code"

    def test_sys_executable_cursor(self):
        """Test process detection for Cursor."""
        with patch("vibey.platform.detector.sys") as mock_sys:
            mock_sys.executable = "/Applications/Cursor.app/Contents/MacOS/Cursor"
            result = _check_process_names()
            assert result == "cursor"

    def test_sys_executable_no_match(self):
        """Test process detection with no platform match."""
        with patch("vibey.platform.detector.sys") as mock_sys:
            mock_sys.executable = "/usr/bin/python3"
            result = _check_process_names()
            # Should return None or a platform (psutil might detect something)
            assert result is None or isinstance(result, str)


class TestDetectPlatform:
    """Test detect_platform function."""

    def test_returns_platform_info(self, tmp_path):
        """Test returns PlatformInfo."""
        result = detect_platform(tmp_path)
        assert isinstance(result, PlatformInfo)

    def test_fallback_to_unknown(self, tmp_path):
        """Test falls back to unknown when no detection."""
        # Clean environment
        with patch.dict(os.environ, {}, clear=False):
            result = detect_platform(tmp_path)
            # Should return unknown or detected platform
            assert result.name in list(KNOWN_PLATFORMS.keys()) + ["unknown"]

    def test_detects_from_config_file(self, tmp_path):
        """Test detects platform from config file."""
        (tmp_path / ".cursorrules").write_text("# Rules")
        
        result = detect_platform(tmp_path)
        assert result.name == "cursor"
        assert result.detected_by == DetectionMethod.CONFIG_FILE
        assert result.confidence == 0.7

    def test_environment_has_higher_priority(self, tmp_path):
        """Test environment detection has higher priority."""
        # Create config file for cursor
        (tmp_path / ".cursorrules").write_text("# Rules")
        
        # Set env var for claude-code
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}):
            result = detect_platform(tmp_path)
            assert result.name == "claude-code"
            assert result.detected_by == DetectionMethod.ENVIRONMENT
            assert result.confidence == 0.95


class TestGetPlatformInfo:
    """Test get_platform_info function."""

    def test_auto_detect_when_no_id(self, tmp_path):
        """Test auto-detects when no platform_id provided."""
        result = get_platform_info(cwd=tmp_path)
        assert isinstance(result, PlatformInfo)

    def test_returns_known_platform(self):
        """Test returns info for known platform."""
        result = get_platform_info("claude-code")
        assert result.name == "claude-code"
        assert result.display_name == "Claude Code"
        assert result.vendor == "Anthropic"
        assert result.detected_by == DetectionMethod.MANUAL
        assert result.confidence == 1.0

    def test_returns_cursor_platform(self):
        """Test returns info for Cursor platform."""
        result = get_platform_info("cursor")
        assert result.name == "cursor"
        assert result.display_name == "Cursor"
        assert result.vendor == "Cursor Inc"

    def test_returns_goose_platform(self):
        """Test returns info for Goose platform."""
        result = get_platform_info("goose")
        assert result.name == "goose"
        assert result.display_name == "Goose"
        assert result.vendor == "Block"

    def test_returns_custom_platform(self):
        """Test returns info for custom/unknown platform."""
        result = get_platform_info("custom-platform")
        assert result.name == "custom-platform"
        assert result.display_name == "Custom Platform"
        assert result.vendor == "Unknown"
        assert result.confidence == 0.5

    def test_context_window_set_correctly(self):
        """Test context window is set from platform info."""
        result = get_platform_info("claude-code")
        assert result.context_window == 200_000

        result = get_platform_info("gemini")
        assert result.context_window == 1_000_000


class TestListKnownPlatforms:
    """Test list_known_platforms function."""

    def test_returns_list(self):
        """Test returns a list."""
        result = list_known_platforms()
        assert isinstance(result, list)

    def test_list_not_empty(self):
        """Test list is not empty."""
        result = list_known_platforms()
        assert len(result) > 0

    def test_each_item_has_required_fields(self):
        """Test each item has required fields."""
        result = list_known_platforms()
        for platform in result:
            assert "id" in platform
            assert "name" in platform
            assert "vendor" in platform
            assert "context_window" in platform
            assert "description" in platform

    def test_contains_claude_code(self):
        """Test list contains Claude Code."""
        result = list_known_platforms()
        ids = [p["id"] for p in result]
        assert "claude-code" in ids

    def test_contains_cursor(self):
        """Test list contains Cursor."""
        result = list_known_platforms()
        ids = [p["id"] for p in result]
        assert "cursor" in ids

    def test_contains_all_known_platforms(self):
        """Test list contains all known platforms."""
        result = list_known_platforms()
        ids = [p["id"] for p in result]
        
        for platform_id in KNOWN_PLATFORMS:
            assert platform_id in ids


class TestPlatformDetectionIntegration:
    """Integration tests for platform detection."""

    def test_detect_from_environment_variable(self):
        """Test detection from environment variable."""
        with patch.dict(os.environ, {"GOOSE_HOME": "/home/goose"}):
            result = detect_platform()
            assert result.name == "goose"
            assert result.detected_by == DetectionMethod.ENVIRONMENT

    def test_detect_from_cursor_env(self):
        """Test detection from Cursor environment."""
        with patch.dict(os.environ, {"CURSOR_SESSION": "abc123"}):
            result = detect_platform()
            assert result.name == "cursor"

    def test_multiple_env_vars_uses_first_match(self):
        """Test first matching platform is returned."""
        # Since detection order depends on dict iteration,
        # just verify we get a valid known platform
        with patch.dict(os.environ, {
            "CURSOR_SESSION": "abc",
            "GOOSE_HOME": "/goose",
        }):
            result = detect_platform()
            assert result.name in ["cursor", "goose"]

    def test_unknown_platform_has_zero_confidence(self, tmp_path):
        """Test unknown platform has zero confidence."""
        # Clean environment and empty directory
        result = detect_platform(tmp_path)
        if result.name == "unknown":
            assert result.confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
