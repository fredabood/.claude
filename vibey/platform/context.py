"""
Context window detection for AI coding platforms.

Provides context window sizes for known platforms and
supports user overrides via configuration.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from vibey.platform.detector import (
    PlatformInfo,
    PlatformName,
    KNOWN_PLATFORMS,
    detect_platform,
    get_platform_info,
)


# Context window sizes for known platforms (in tokens)
# These are conservative estimates that may vary by model/tier
PLATFORM_CONTEXT_WINDOWS: Dict[str, int] = {
    PlatformName.CLAUDE_CODE.value: 200_000,  # Claude 3.5 Sonnet
    PlatformName.GOOSE.value: 128_000,  # Model-dependent, default for Claude
    PlatformName.CURSOR.value: 128_000,  # Model-dependent
    PlatformName.AIDER.value: 128_000,  # Model-dependent
    PlatformName.CONTINUE.value: 128_000,  # Model-dependent
    PlatformName.COPILOT.value: 64_000,  # GPT-4 based
    PlatformName.JETBRAINS_AI.value: 128_000,  # Model-dependent
    PlatformName.WINDSURF.value: 128_000,  # Model-dependent
    PlatformName.VSCODE.value: 128_000,  # Extension-dependent
    PlatformName.GEMINI.value: 1_000_000,  # Gemini 1.5 Pro/Flash
    PlatformName.UNKNOWN.value: 128_000,  # Conservative default
}


def get_context_window(
    platform: Optional[str] = None,
    platform_info: Optional[PlatformInfo] = None,
    config_override: Optional[int] = None,
) -> int:
    """
    Get the context window size for a platform.

    Priority:
    1. User config override (if provided)
    2. Platform-specific size from database
    3. Default fallback (128K)

    Args:
        platform: Platform identifier (e.g., 'claude-code').
        platform_info: Pre-computed PlatformInfo object.
        config_override: User-specified context window size.

    Returns:
        Context window size in tokens.
    """
    # User override takes precedence
    if config_override is not None:
        return config_override

    # Use provided platform info or detect
    if platform_info is not None:
        return platform_info.context_window

    # Look up by platform ID
    if platform is not None:
        if platform in PLATFORM_CONTEXT_WINDOWS:
            return PLATFORM_CONTEXT_WINDOWS[platform]
        # Try to get from KNOWN_PLATFORMS
        if platform in KNOWN_PLATFORMS:
            return KNOWN_PLATFORMS[platform].get("context_window", 128_000)

    # Auto-detect and return
    detected = detect_platform()
    return detected.context_window


def estimate_token_count(text: str, method: str = "approximate") -> int:
    """
    Estimate the token count for a text string.

    Args:
        text: The text to count tokens for.
        method: Counting method ('approximate', 'tiktoken', 'words').

    Returns:
        Estimated token count.
    """
    if method == "words":
        # Very rough: ~1.3 tokens per word
        return int(len(text.split()) * 1.3)
    elif method == "tiktoken":
        # Try to use tiktoken for accurate count
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            # Fall back to approximate
            pass

    # Approximate: ~4 characters per token (common heuristic)
    return len(text) // 4


def check_fits_context(
    content: str,
    platform: Optional[str] = None,
    context_window: Optional[int] = None,
    buffer_percent: float = 0.1,
) -> Dict[str, Any]:
    """
    Check if content fits within a platform's context window.

    Args:
        content: The content to check.
        platform: Platform identifier (auto-detected if not provided).
        context_window: Override context window size.
        buffer_percent: Buffer to leave for response (default 10%).

    Returns:
        Dict with fit status, token counts, and details.
    """
    # Get context window
    if context_window is None:
        context_window = get_context_window(platform=platform)

    # Calculate usable context (leave buffer for response)
    usable_context = int(context_window * (1 - buffer_percent))

    # Estimate token count
    estimated_tokens = estimate_token_count(content)

    # Check fit
    fits = estimated_tokens <= usable_context
    overflow = max(0, estimated_tokens - usable_context)

    return {
        "fits": fits,
        "estimated_tokens": estimated_tokens,
        "context_window": context_window,
        "usable_context": usable_context,
        "buffer_percent": buffer_percent,
        "overflow_tokens": overflow,
        "utilization_percent": round(estimated_tokens / context_window * 100, 1),
    }


def format_token_count(tokens: int) -> str:
    """Format token count for display (e.g., '128K')."""
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    elif tokens >= 1_000:
        return f"{tokens / 1_000:.0f}K"
    else:
        return str(tokens)


def get_platform_context_summary(platform: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a summary of platform context capabilities.

    Args:
        platform: Platform identifier (auto-detected if not provided).

    Returns:
        Dict with platform name, context window, and recommendations.
    """
    if platform is None:
        platform_info = detect_platform()
    else:
        platform_info = get_platform_info(platform)

    context_window = platform_info.context_window
    usable_90 = int(context_window * 0.9)
    usable_80 = int(context_window * 0.8)

    return {
        "platform": platform_info.name,
        "display_name": platform_info.display_name,
        "context_window": context_window,
        "context_window_formatted": format_token_count(context_window),
        "recommended_task_size": usable_90,
        "recommended_task_size_formatted": format_token_count(usable_90),
        "safe_task_size": usable_80,
        "safe_task_size_formatted": format_token_count(usable_80),
        "recommendations": [
            f"Tasks should fit within {format_token_count(usable_90)} tokens (90% of context)",
            f"For complex tasks with outputs, target {format_token_count(usable_80)} tokens (80%)",
            "Leave at least 10% buffer for model responses",
        ],
    }
