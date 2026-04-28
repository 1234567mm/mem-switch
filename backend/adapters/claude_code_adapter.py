import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from .base_adapter import BaseAdapter, Conversation, ImportResult


class ClaudeCodeAdapter(BaseAdapter):
    """Claude Code 对话适配器

    Claude Code 会话格式: JSONL
    每个会话是一个JSON对象，包含messages数组
    """

    source_name = "claude_code"

    DEFAULT_PATHS = {
        "linux": "~/.claude/projects",
        "macos": "~/.claude/projects",
        "windows": "%USERPROFILE%/.claude/projects",
    }

    def detect(self, source_path: str = None) -> bool:
        """检测Claude Code会话目录是否存在"""
        import os
        path = Path(source_path) if source_path else Path.home() / ".claude" / "projects"
        return path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        """解析Claude Code会话文件"""
        base_path = Path(source_path) if source_path else Path.home() / ".claude" / "projects"

        if not base_path.exists():
            return []

        conversations = []

        # 遍历所有项目目录
        for project_dir in base_path.iterdir():
            if not project_dir.is_dir():
                continue

            conv_dir = project_dir / "conversations"
            if not conv_dir.exists():
                continue

            # 读取JSONL文件
            for conv_file in conv_dir.glob("*.jsonl"):
                try:
                    convs = self._parse_jsonl_file(conv_file)
                    conversations.extend(convs)
                except Exception as e:
                    print(f"Error parsing {conv_file}: {e}")

        return conversations

    def _parse_jsonl_file(self, file_path: Path) -> list[Conversation]:
        """解析JSONL文件"""
        conversations = []

        for line in file_path.read_text().splitlines():
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                messages = data.get("messages", [])

                if messages:
                    conv = Conversation(
                        session_id=data.get("id", file_path.stem),
                        source=self.source_name,
                        timestamp=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                        messages=[
                            {"role": msg.get("role"), "content": msg.get("content", "")}
                            for msg in messages
                        ],
                        metadata={"project": data.get("project", "")},
                    )
                    if self.validate_conversation(conv):
                        conversations.append(conv)

            except json.JSONDecodeError:
                continue

        return conversations