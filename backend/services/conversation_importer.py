from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from services.memory_service import MemoryService
from services.memory_extractor import MemoryExtractor, EXTRACT_DIMENSIONS
from services.profile_manager import ProfileManager
from config import AppConfig, IMPORTS_DIR
from adapters import get_adapter, Conversation


class ImportOptions:
    """导入选项"""

    def __init__(
        self,
        extract_memories: bool = True,
        extract_dimensions: list[str] = None,
        delete_after_import: bool = False,
    ):
        self.extract_memories = extract_memories
        self.extract_dimensions = extract_dimensions or list(EXTRACT_DIMENSIONS.keys())
        self.delete_after_import = delete_after_import


class ConversationImporter:
    """对话导入服务"""

    def __init__(
        self,
        vector_store: VectorStore,
        ollama_service: OllamaService,
        config: AppConfig,
    ):
        self.vector_store = vector_store
        self.ollama = ollama_service
        self.config = config
        self.memory_service = MemoryService(vector_store, ollama_service, config)
        self.extractor = MemoryExtractor(ollama_service, config)
        self.profile_manager = ProfileManager()
        self.collection_name = "conversations"

    def import_conversations(
        self,
        source_type: str,
        source_path: str = None,
        options: ImportOptions = None,
    ) -> list[dict]:
        """导入对话"""
        options = options or ImportOptions()

        adapter = get_adapter(source_type)

        if not adapter.detect(source_path):
            return [{"status": "error", "message": f"Source not found: {source_type}"}]

        conversations = adapter.parse(source_path)

        results = []
        for conv in conversations:
            result = self._import_single(conv, options)
            results.append(result)

        return results

    def _import_single(self, conv: Conversation, options: ImportOptions) -> dict:
        """导入单个对话"""
        session_id = conv.session_id or str(uuid4())

        try:
            text_content = self.format_conversation_for_embedding(conv)
            emb = self.ollama.embed(text_content)

            self.vector_store.client.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": session_id,
                    "vector": emb,
                    "payload": {
                        "session_id": session_id,
                        "source": conv.source,
                        "timestamp": conv.timestamp.isoformat(),
                        "messages": conv.messages,
                        "message_count": len(conv.messages),
                    }
                }]
            )

            self._save_session_metadata(session_id, conv)

            memories_created = 0
            if options.extract_memories:
                memories_created = self._extract_and_store_memories(conv, session_id, options)

            return {
                "status": "success",
                "session_id": session_id,
                "source": conv.source,
                "messages_count": len(conv.messages),
                "memories_created": memories_created,
            }

        except Exception as e:
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
            }

    def _extract_and_store_memories(
        self,
        conv: Conversation,
        session_id: str,
        options: ImportOptions,
    ) -> int:
        """提取并存储记忆"""
        text_content = self.format_conversation_for_embedding(conv)

        extracted = self.extractor.extract_memories(
            text_content,
            dimensions=options.extract_dimensions,
        )

        memories_count = 0
        for dim, data in extracted.items():
            if 'error' not in data and 'data' in data:
                memory = self.memory_service.create_memory(
                    content=str(data['data']),
                    memory_type=dim,
                    dimensions={
                        "label": data.get('label', dim),
                        "confidence": data.get('confidence', 0.8),
                    },
                    source_session_id=session_id,
                )
                memories_count += 1

        return memories_count

    def _save_session_metadata(self, session_id: str, conv: Conversation):
        """保存会话元数据到SQLite"""
        from services.database import get_session, SessionRow

        session = get_session()
        try:
            row = SessionRow(
                id=session_id,
                source=conv.source,
                import_time=datetime.now(),
                deleted=False,
            )
            session.add(row)
            session.commit()
        finally:
            session.close()

    def format_conversation_for_embedding(self, conv: Conversation) -> str:
        """将对话格式化为embedding文本"""
        lines = []
        for msg in conv.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def preview_import(
        self,
        source_type: str,
        source_path: str = None,
    ) -> list[dict]:
        """预览导入内容（不执行导入）"""
        adapter = get_adapter(source_type)

        if not adapter.detect(source_path):
            return []

        conversations = adapter.parse(source_path)

        return [
            {
                "session_id": conv.session_id,
                "source": conv.source,
                "timestamp": conv.timestamp.isoformat(),
                "message_count": len(conv.messages),
                "preview": self.format_conversation_for_embedding(conv)[:200],
            }
            for conv in conversations[:10]
        ]

    def delete_session(self, session_id: str, delete_memories: bool = False) -> dict:
        """删除会话"""
        try:
            self.vector_store.client.delete(
                collection_name=self.collection_name,
                points=[session_id],
            )

            if delete_memories:
                memories = self.memory_service.search_memories(
                    query="",
                    limit=100,
                )
                for mem in memories:
                    if mem.source_session_id == session_id:
                        self.memory_service.delete_memory(mem.memory_id)

            from services.database import get_session, SessionRow
            session_db = get_session()
            try:
                row = session_db.query(SessionRow).filter_by(id=session_id).first()
                if row:
                    row.deleted = True
                    session_db.commit()
            finally:
                session_db.close()

            return {"status": "deleted", "session_id": session_id}

        except Exception as e:
            return {"status": "error", "error": str(e)}