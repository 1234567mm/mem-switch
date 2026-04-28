import json
from pathlib import Path
from datetime import datetime

from .base_adapter import BaseAdapter, Conversation


class GeminiCLIAdapter(BaseAdapter):
    """Gemini CLI 对话适配器

    Gemini CLI 会话格式: Google AI JSON
    """

    source_name = "gemini_cli"

    def detect(self, source_path: str = None) -> bool:
        path = Path(source_path) if source_path else Path.home() / ".gemini" / "history"
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        base_path = Path(source_path) if source_path else Path.home() / ".gemini" / "history"

        if not base_path.exists():
            return []

        conversations = []

        for session_file in base_path.rglob("*.json"):
            try:
                data = json.loads(session_file.read_text())

                # Google AI格式转换
                messages = []
                for turn in data.get("turns", []):
                    role = "user" if turn.get("role") == "user" else "assistant"
                    for part in turn.get("parts", []):
                        if "text" in part:
                            messages.append({"role": role, "content": part["text"]})

                conv = Conversation(
                    session_id=data.get("id", session_file.stem),
                    source=self.source_name,
                    timestamp=datetime.fromisoformat(data.get("create_time", datetime.now().isoformat())),
                    messages=messages,
                )

                if self.validate_conversation(conv):
                    conversations.append(conv)

            except Exception as e:
                print(f"Error parsing {session_file}: {e}")

        return conversations