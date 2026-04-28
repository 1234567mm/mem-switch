import re
from pathlib import Path
from datetime import datetime

from .base_adapter import BaseAdapter, Conversation


class MarkdownAdapter(BaseAdapter):
    """Markdown对话文件适配器"""

    source_name = "markdown"

    def detect(self, source_path: str = None) -> bool:
        if not source_path:
            return False
        path = Path(source_path)
        return path.exists() and path.suffix.lower() in {".md", ".markdown"}

    def parse(self, source_path: str = None) -> list[Conversation]:
        if not source_path:
            return []

        path = Path(source_path)
        if not path.exists():
            return []

        content = path.read_text()
        messages = []
        current_role = None
        current_content = []

        for line in content.splitlines():
            # 检测对话标记
            user_match = re.match(r'^(?:```(?:user|human))?\s*(?:^|\n)(?:##?\s*)?(?:User|Human|提问):?\s*(.*)$', line, re.IGNORECASE)
            assistant_match = re.match(r'^(?:```(?:assistant|ai))?\s*(?:^|\n)(?:##?\s*)?(?:Assistant|AI|回答):?\s*(.*)$', line, re.IGNORECASE)

            if user_match:
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                current_role = "user"
                current_content = [user_match.group(1)] if user_match.group(1) else []
            elif assistant_match:
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                current_role = "assistant"
                current_content = [assistant_match.group(1)] if assistant_match.group(1) else []
            else:
                if current_role is not None:
                    current_content.append(line)

        if current_role and current_content:
            messages.append({"role": current_role, "content": "\n".join(current_content)})

        conv = Conversation(
            session_id=path.stem,
            source=self.source_name,
            timestamp=datetime.now(),
            messages=messages,
        )

        return [conv] if self.validate_conversation(conv) else []