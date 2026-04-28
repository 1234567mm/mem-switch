import json
from pathlib import Path
from datetime import datetime

from .base_adapter import BaseAdapter, Conversation


class HermesAdapter(BaseAdapter):
    """Hermes 对话适配器

    Hermes 会话格式: NousResearch Hermes Agent格式
    参考: https://github.com/NousResearch/hermes-agent
    """

    source_name = "hermes"

    def detect(self, source_path: str = None) -> bool:
        path = Path(source_path) if source_path else Path.home() / ".hermes" / "sessions"
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        base_path = Path(source_path) if source_path else Path.home() / ".hermes" / "sessions"

        if not base_path.exists():
            return []

        conversations = []

        for session_file in base_path.rglob("*.json"):
            try:
                data = json.loads(session_file.read_text())

                # Hermes格式转换
                messages = []
                for msg in data.get("messages", []):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    messages.append({"role": role, "content": content})

                conv = Conversation(
                    session_id=data.get("session_id", session_file.stem),
                    source=self.source_name,
                    timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                    messages=messages,
                )

                if self.validate_conversation(conv):
                    conversations.append(conv)

            except Exception as e:
                print(f"Error parsing {session_file}: {e}")

        return conversations