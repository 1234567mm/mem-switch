from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass

from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from services.memory_extractor import MemoryExtractor, EXTRACT_DIMENSIONS
from services.profile_manager import ProfileManager
from config import AppConfig


@dataclass
class Memory:
    memory_id: str
    type: str
    content: str
    dimensions: dict
    confidence: float
    source_session_id: Optional[str]
    created_at: datetime


class MemoryService:
    """记忆库服务"""

    def __init__(
        self,
        vector_store: VectorStore,
        ollama_service: OllamaService,
        config: AppConfig,
    ):
        self.vector_store = vector_store
        self.ollama = ollama_service
        self.config = config
        self.extractor = MemoryExtractor(ollama_service, config)
        self.profile_manager = ProfileManager()
        self.collection_name = "memories"

    def create_memory(
        self,
        content: str,
        memory_type: str,
        dimensions: dict = None,
        source_session_id: str = None,
    ) -> Memory:
        """创建记忆"""
        memory_id = str(uuid4())

        emb = self.ollama.embed(content)

        self.vector_store.client.upsert(
            collection_name=self.collection_name,
            points=[{
                "id": memory_id,
                "vector": emb,
                "payload": {
                    "memory_id": memory_id,
                    "type": memory_type,
                    "content": content,
                    "dimensions": dimensions or {},
                    "source_session_id": source_session_id,
                    "created_at": datetime.now().isoformat(),
                }
            }]
        )

        return Memory(
            memory_id=memory_id,
            type=memory_type,
            content=content,
            dimensions=dimensions or {},
            confidence=dimensions.get("confidence", 0.8) if dimensions else 0.8,
            source_session_id=source_session_id,
            created_at=datetime.now(),
        )

    def search_memories(
        self,
        query: str,
        memory_type: str = None,
        limit: int = 10,
    ) -> list[Memory]:
        """检索记忆"""
        query_emb = self.ollama.embed(query)

        filter_condition = None
        if memory_type:
            filter_condition = {"must": [{"key": "type", "match": {"value": memory_type}}]}

        results = self.vector_store.client.search(
            collection_name=self.collection_name,
            query_vector=query_emb,
            limit=limit,
            query_filter=filter_condition,
        )

        memories = []
        for r in results:
            payload = r.payload
            memories.append(Memory(
                memory_id=payload["memory_id"],
                type=payload["type"],
                content=payload["content"],
                dimensions=payload.get("dimensions", {}),
                confidence=payload.get("confidence", 0.8),
                source_session_id=payload.get("source_session_id"),
                created_at=datetime.fromisoformat(payload["created_at"]),
            ))

        return memories

    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            self.vector_store.client.delete(
                collection_name=self.collection_name,
                points=[memory_id],
            )
            return True
        except Exception:
            return False

    def list_memories(
        self,
        memory_type: str = None,
        limit: int = 100,
    ) -> list[Memory]:
        """列出记忆"""
        results = self.vector_store.scroll(
            collection_name=self.collection_name,
            limit=limit,
        )

        memories = []
        for r in results[0]:
            payload = r.payload
            if memory_type and payload.get("type") != memory_type:
                continue
            memories.append(Memory(
                memory_id=payload["memory_id"],
                type=payload["type"],
                content=payload["content"],
                dimensions=payload.get("dimensions", {}),
                confidence=payload.get("confidence", 0.8),
                source_session_id=payload.get("source_session_id"),
                created_at=datetime.fromisoformat(payload["created_at"]),
            ))

        return memories

    def get_profile(self) -> dict:
        """获取用户画像"""
        return self.profile_manager.get_profile_summary("default")

    def update_profile_from_memories(
        self,
        memory_ids: list[str],
    ) -> dict:
        """从记忆更新画像"""
        return {"status": "updated"}