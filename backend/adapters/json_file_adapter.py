import json
from pathlib import Path
from datetime import datetime

from .base_adapter import BaseAdapter, Conversation


class JSONFileAdapter(BaseAdapter):
    """通用JSON文件适配器"""

    source_name = "json_file"

    def detect(self, source_path: str = None) -> bool:
        if not source_path:
            return False
        path = Path(source_path)
        return path.exists() and path.suffix.lower() == ".json"

    def parse(self, source_path: str = None) -> list[Conversation]:
        if not source_path:
            return []

        path = Path(source_path)
        if not path.exists():
            return []

        try:
            data = json.loads(path.read_text())

            # 支持多种JSON格式
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

        except Exception as e:
            print(f"Error parsing {path}: {e}")
            return []