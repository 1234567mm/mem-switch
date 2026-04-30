import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from .base_adapter import BaseAdapter, Conversation


TYPE_MAP = {
    "decision": "decision",
    "bugfix": "bugfix",
    "feature": "feature",
    "refactor": "refactor",
    "discovery": "discovery",
    "change": "change",
}
DEFAULT_TYPE = "fact"


class ClaudeMemAdapter(BaseAdapter):
    """claude-mem 数据库导入适配器"""

    source_name = "claude_mem"

    def detect(self, source_path: str = None) -> bool:
        if not source_path:
            return False
        db_path = Path(source_path) / "claude-mem.db"
        return db_path.exists()

    def parse(self, source_path: str = None) -> list[Conversation]:
        if not source_path:
            return []
        db_path = Path(source_path) / "claude-mem.db"
        if not db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取所有 sessions
            cursor.execute("SELECT * FROM sdk_sessions ORDER BY created_at DESC")
            sessions = cursor.fetchall()

            conversations = []
            for session in sessions:
                cursor.execute(
                    "SELECT * FROM observations WHERE sdk_session_id = ? ORDER BY created_at",
                    (session["sdk_session_id"],)
                )
                observations = cursor.fetchall()

                if not observations:
                    continue

                messages = []
                for obs in observations:
                    obs_type = obs.get("type", DEFAULT_TYPE)
                    mapped_type = TYPE_MAP.get(obs_type, DEFAULT_TYPE)

                    narrative = obs.get("narrative", "")
                    content = narrative if narrative else obs.get("title", "")

                    messages.append({
                        "role": "assistant",
                        "content": f"[{mapped_type}] {content}" if content else obs.get("title", ""),
                        "metadata": {
                            "type": mapped_type,
                            "facts": obs.get("facts", ""),
                            "concepts": obs.get("concepts", ""),
                            "files_read": obs.get("files_read", ""),
                            "files_modified": obs.get("files_modified", ""),
                        }
                    })

                cursor.execute(
                    "SELECT * FROM user_prompts WHERE sdk_session_id = ? ORDER BY created_at",
                    (session["sdk_session_id"],)
                )
                prompts = cursor.fetchall()

                for prompt in prompts:
                    messages.append({
                        "role": "user",
                        "content": prompt.get("prompt_text", ""),
                    })

                conversations.append(Conversation(
                    session_id=session["sdk_session_id"],
                    source=self.source_name,
                    timestamp=datetime.fromisoformat(session["created_at"]) if session["created_at"] else datetime.now(),
                    messages=sorted(messages, key=lambda m: m.get("timestamp", "")),
                ))

            conn.close()
            return [c for c in conversations if self.validate_conversation(c)]

        except Exception as e:
            print(f"Error parsing claude-mem db: {e}")
            return []

    def _observation_to_memory(self, obs: dict) -> dict:
        """将 claude-mem observation 转换为 memory 格式。"""
        obs_type = obs.get("type", DEFAULT_TYPE)
        mapped_type = TYPE_MAP.get(obs_type, DEFAULT_TYPE)

        narrative = obs.get("narrative", "")
        content = narrative if narrative else obs.get("title", "")

        return {
            "type": mapped_type,
            "content": content or obs.get("title", ""),
            "metadata": {
                "facts": obs.get("facts", ""),
                "concepts": obs.get("concepts", ""),
                "title": obs.get("title", ""),
            },
            "session_id": obs.get("session_id", obs.get("sdk_session_id", "")),
        }