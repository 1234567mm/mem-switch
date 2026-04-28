import json
from pathlib import Path
from datetime import datetime

from .base_adapter import BaseAdapter, Conversation


class GenericAdapter(BaseAdapter):
    """通用适配器 - 尝试自动检测格式"""

    source_name = "generic"

    def detect(self, source_path: str = None) -> bool:
        if not source_path:
            return False
        path = Path(source_path)
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        if not source_path:
            return []

        path = Path(source_path)
        if not path.exists():
            return []

        # 尝试JSON格式
        if path.suffix.lower() == ".json":
            return self._parse_json(path)

        # 尝试Markdown格式
        if path.suffix.lower() in {".md", ".markdown"}:
            from .markdown_adapter import MarkdownAdapter
            adapter = MarkdownAdapter()
            return adapter.parse(source_path)

        # 尝试纯文本
        return self._parse_text(path)

    def _parse_json(self, path: Path) -> list[Conversation]:
        try:
            data = json.loads(path.read_text())

            if isinstance(data, list):
                messages = data
            elif isinstance(data, dict):
                if "messages" in data:
                    messages = data["messages"]
                else:
                    messages = [data]
            else:
                return []

            conv = Conversation(
                session_id=path.stem,
                source=self.source_name,
                timestamp=datetime.now(),
                messages=messages if isinstance(messages, list) else [messages],
            )

            return [conv] if self.validate_conversation(conv) else []

        except Exception:
            return []

    def _parse_text(self, path: Path) -> list[Conversation]:
        content = path.read_text()
        lines = content.splitlines()

        messages = []
        for line in lines:
            if ": " in line:
                role, content = line.split(": ", 1)
                role = role.lower().strip()
                if role in ["user", "human", "assistant", "ai"]:
                    messages.append({
                        "role": "user" if role in ["user", "human"] else "assistant",
                        "content": content,
                    })

        conv = Conversation(
            session_id=path.stem,
            source=self.source_name,
            timestamp=datetime.now(),
            messages=messages,
        )

        return [conv] if self.validate_conversation(conv) else []