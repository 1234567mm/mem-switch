import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .base_adapter import BaseAdapter, Conversation


class CodexAdapter(BaseAdapter):
    """Codex (OpenAI) 对话适配器

    Codex 会话格式: OpenAI兼容JSON
    """

    source_name = "codex"

    def detect(self, source_path: str = None) -> bool:
        path = Path(source_path) if source_path else Path.home() / ".codex" / "sessions"
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        base_path = Path(source_path) if source_path else Path.home() / ".codex" / "sessions"

        if not base_path.exists():
            return []

        conversations = []

        for session_file in base_path.rglob("*.json"):
            try:
                data = json.loads(session_file.read_text())

                conv = Conversation(
                    session_id=data.get("id", session_file.stem),
                    source=self.source_name,
                    timestamp=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                    messages=data.get("messages", []),
                )

                if self.validate_conversation(conv):
                    conversations.append(conv)

            except Exception as e:
                print(f"Error parsing {session_file}: {e}")

        return conversations