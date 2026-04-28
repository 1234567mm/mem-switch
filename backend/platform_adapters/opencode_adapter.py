# backend/platform_adapters/opencode_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class OpenCodeAdapter(PlatformAdapter):
    """OpenCode 适配器"""

    platform_name = "opencode"
    api_endpoint = "http://localhost:8765/opencode/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "opencode" or
            "opencode_session" in request_data
        )

    def extract_messages(self, request_data: dict) -> list[dict]:
        messages = request_data.get("messages", [])
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        ]

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
        home = os.path.expanduser("~")
        config_path = os.path.join(home, ".opencode", "config.json")
        if os.path.exists(os.path.dirname(config_path)):
            return config_path
        return None