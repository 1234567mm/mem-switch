# backend/platform_adapters/__init__.py

from .base_adapter import PlatformAdapter, AdapterRegistry

# 导出所有适配器
from .claude_code_adapter import ClaudeCodeAdapter
from .codex_adapter import CodexAdapter
from .openclaw_adapter import OpenClawAdapter
from .opencode_adapter import OpenCodeAdapter
from .gemini_cli_adapter import GeminiCLIAdapter
from .hermes_adapter import HermesAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "openclaw": OpenClawAdapter,
    "opencode": OpenCodeAdapter,
    "gemini_cli": GeminiCLIAdapter,
    "hermes": HermesAdapter,
}


def get_adapter(platform: str) -> PlatformAdapter:
    adapter_class = ADAPTERS.get(platform)
    if not adapter_class:
        raise ValueError(f"Unknown platform: {platform}")
    return adapter_class()


def identify_platform(request_data: dict) -> str | None:
    """从请求中识别来源平台"""
    # 检查请求中的 platform 字段
    if "platform" in request_data:
        return request_data["platform"]

    # 检查 messages 中的特殊标记
    messages = request_data.get("messages", [])
    if messages and isinstance(messages[0], dict):
        first_msg = messages[0].get("content", "")
        if "[claude_code]" in str(first_msg):
            return "claude_code"
        if "[gemini]" in str(first_msg):
            return "gemini_cli"

    return None