from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Conversation:
    session_id: str
    source: str
    timestamp: datetime
    messages: list[dict]  # [{"role": "user"/"assistant", "content": str}]
    metadata: dict = None


@dataclass
class ImportResult:
    session_id: str
    source: str
    messages_count: int
    status: str  # "success" / "partial" / "failed"
    error: Optional[str] = None


class BaseAdapter(ABC):
    """对话导入适配器基类"""

    source_name: str = "base"

    @abstractmethod
    def detect(self, source_path: str = None) -> bool:
        """检测数据源是否存在"""
        pass

    @abstractmethod
    def parse(self, source_path: str = None) -> list[Conversation]:
        """解析数据源，返回对话列表"""
        pass

    def validate_conversation(self, conv: Conversation) -> bool:
        """验证对话格式"""
        return (
            conv.session_id and
            conv.messages and
            len(conv.messages) > 0
        )

    def format_for_extraction(self, conv: Conversation) -> str:
        """将对话格式化为可提取的文本"""
        lines = []
        for msg in conv.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)