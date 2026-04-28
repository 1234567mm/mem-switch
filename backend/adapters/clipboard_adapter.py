from .base_adapter import BaseAdapter, Conversation
from datetime import datetime


class ClipboardAdapter(BaseAdapter):
    """剪贴板适配器 - 处理粘贴的对话内容"""

    source_name = "clipboard"

    def __init__(self):
        self._clipboard_content = ""

    def set_content(self, content: str):
        """设置剪贴板内容"""
        self._clipboard_content = content

    def detect(self, source_path: str = None) -> bool:
        return bool(self._clipboard_content.strip())

    def parse(self, source_path: str = None) -> list[Conversation]:
        if not self._clipboard_content.strip():
            return []

        # 简单按行分割，假设格式为 "role: content"
        messages = []
        for line in self._clipboard_content.splitlines():
            line = line.strip()
            if not line:
                continue

            if ": " in line:
                role, content = line.split(": ", 1)
                role = role.lower().strip()
                if role in ["user", "human", "assistant", "ai"]:
                    messages.append({
                        "role": "user" if role in ["user", "human"] else "assistant",
                        "content": content,
                    })

        conv = Conversation(
            session_id="clipboard",
            source=self.source_name,
            timestamp=datetime.now(),
            messages=messages,
        )

        return [conv] if self.validate_conversation(conv) else []