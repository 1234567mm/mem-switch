# backend/platform_adapters/claude_code_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class ClaudeCodeAdapter(PlatformAdapter):
    """Claude Code 适配器 - MCP 协议"""

    platform_name = "claude_code"
    api_endpoint = "http://localhost:11434/api/generate"

    MCP_TO_OLLAMA_FORMAT = {
        "model": "model",
        "messages": "messages",
        "stream": "stream",
        "options": "options",
    }

    def identify(self, request_data: dict) -> bool:
        # 检查是否是 Claude Code 请求
        # Claude Code 使用 MCP 协议，有特殊的请求格式
        return (
            request_data.get("protocol") == "mcp" or
            "mcp_server" in request_data.get("path", "") or
            request_data.get("tool") == "claude_code"
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        # MCP 格式的消息提取
        messages = request_data.get("messages", [])
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                # 处理多模态内容
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                content = "\n".join(text_parts)
            converted.append({"role": role, "content": content})
        return converted

    def build_forward_request(
        self,
        messages: list[dict],
        model: str,
        stream: bool = False,
    ) -> dict:
        # 构建转发到 Ollama 的请求
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        home = os.path.expanduser("~")
        claude_dir = os.path.join(home, ".claude")
        config_path = os.path.join(claude_dir, "settings.json")

        # 检查 Claude Code 安装
        if os.path.exists(claude_dir):
            return config_path
        return None