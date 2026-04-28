# backend/platform_adapters/openclaw_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class OpenClawAdapter(PlatformAdapter):
    """OpenClaw 适配器"""

    platform_name = "openclaw"
    api_endpoint = "http://localhost:8765/openclaw/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "openclaw" or
            "openclaw_session" in request_data
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
        config_path = os.path.join(home, ".openclaw", "config.json")
        if os.path.exists(os.path.dirname(config_path)):
            return config_path
        return None