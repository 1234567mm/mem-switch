# backend/platform_adapters/codex_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class CodexAdapter(PlatformAdapter):
    """Codex 适配器 - OpenAI 兼容 API"""

    platform_name = "codex"
    api_endpoint = "http://localhost:8765/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        # Codex 请求通常有 openai 格式
        has_messages = "messages" in request_data
        has_model = "model" in request_data
        # 检查是否指向 Codex 特定端点
        return has_messages and has_model and (
            "codex" in request_data.get("model", "").lower() or
            request_data.get("provider") == "codex"
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        return request_data.get("messages", [])

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
        # Codex 使用环境变量 OPENAI_API_BASE
        return None