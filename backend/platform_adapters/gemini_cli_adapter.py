# backend/platform_adapters/gemini_cli_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class GeminiCLIAdapter(PlatformAdapter):
    """Gemini CLI 适配器 - Google AI 格式"""

    platform_name = "gemini_cli"
    api_endpoint = "http://localhost:8765/gemini/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "gemini" or
            "gemini" in request_data.get("model", "").lower() or
            request_data.get("source") == "gemini_cli"
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        # Gemini 格式转换
        messages = request_data.get("messages", [])
        converted = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")
            if isinstance(content, list):
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
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

    def get_config_path(self) -> Optional[str]:
        # Gemini CLI 使用环境变量
        return None