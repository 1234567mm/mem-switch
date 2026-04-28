import json
from pathlib import Path
from datetime import datetime
import re

from .base_adapter import BaseAdapter, Conversation


class OpenCodeAdapter(BaseAdapter):
    """OpenCode 对话适配器

    OpenCode 会话格式: Markdown/JSON混合
    """

    source_name = "opencode"

    def detect(self, source_path: str = None) -> bool:
        path = Path(source_path) if source_path else Path.home() / ".opencode" / "history"
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        base_path = Path(source_path) if source_path else Path.home() / ".opencode" / "history"

        if not base_path.exists():
            return []

        conversations = []

        for session_file in base_path.rglob("*.md"):
            try:
                content = session_file.read_text()
                conv = self._parse_markdown_session(content, session_file.stem)
                if conv and self.validate_conversation(conv):
                    conversations.append(conv)
            except Exception as e:
                print(f"Error parsing {session_file}: {e}")

        return conversations

    def _parse_markdown_session(self, content: str, session_id: str) -> Conversation:
        """解析Markdown格式的会话"""
        messages = []
        current_role = None
        current_content = []

        for line in content.splitlines():
            # 检测角色标记
            if line.startswith("## User") or line.startswith("**User**"):
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                current_role = "user"
                current_content = []
            elif line.startswith("## Assistant") or line.startswith("**Assistant**"):
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                current_role = "assistant"
                current_content = []
            else:
                current_content.append(line)

        if current_role and current_content:
            messages.append({"role": current_role, "content": "\n".join(current_content)})

        return Conversation(
            session_id=session_id,
            source=self.source_name,
            timestamp=datetime.now(),
            messages=messages,
        )