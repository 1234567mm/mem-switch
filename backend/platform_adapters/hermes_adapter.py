# backend/platform_adapters/hermes_adapter.py

import os
from typing import Optional
from .base_adapter import PlatformAdapter


class HermesAdapter(PlatformAdapter):
    """Hermes 适配器 - NousResearch Hermes Agent"""

    platform_name = "hermes"
    api_endpoint = "http://localhost:8765/hermes/v1/chat/completions"

    def identify(self, request_data: dict) -> bool:
        return (
            request_data.get("provider") == "hermes" or
            "hermes_agent" in request_data.get("source", "") or
            "NousResearch" in str(request_data.get("model", ""))
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
        config_path = os.path.join(home, ".hermes", "config.json")
        if os.path.exists(os.path.dirname(config_path)):
            return config_path
        return None