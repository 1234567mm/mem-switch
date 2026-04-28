import json
from pathlib import Path
from datetime import datetime

from .base_adapter import BaseAdapter, Conversation


class OpenClawAdapter(BaseAdapter):
    """OpenClaw 对话适配器

    OpenClaw 会话格式: 自定义JSON
    """

    source_name = "openclaw"

    def detect(self, source_path: str = None) -> bool:
        path = Path(source_path) if source_path else Path.home() / ".openclaw" / "sessions"
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        base_path = Path(source_path) if source_path else Path.home() / ".openclaw" / "sessions"

        if not base_path.exists():
            return []

        conversations = []

        for session_file in base_path.rglob("*.json"):
            try:
                data = json.loads(session_file.read_text())

                conv = Conversation(
                    session_id=data.get("session_id", session_file.stem),
                    source=self.source_name,
                    timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                    messages=data.get("conversation", []),
                )

                if self.validate_conversation(conv):
                    conversations.append(conv)

            except Exception as e:
                print(f"Error parsing {session_file}: {e}")

        return conversations