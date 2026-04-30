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
    # New fields
    invalidated: bool = False
    expires_at: Optional[datetime] = None
    call_count: int = 0
    last_called_at: Optional[datetime] = None


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
                    "invalidated": False,
                    "expires_at": None,
                    "call_count": 0,
                    "last_called_at": None,
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
        """检索记忆（过滤失效记忆）"""
        query_emb = self.ollama.embed(query)

        must_conditions = []
        if memory_type:
            must_conditions.append({"key": "type", "match": {"value": memory_type}})

        filter_condition = None
        if must_conditions:
            filter_condition = {"must": must_conditions}

        results = self.vector_store.client.search(
            collection_name=self.collection_name,
            query_vector=query_emb,
            limit=limit * 2,  # Fetch extra to account for filtering
            query_filter=filter_condition,
        )

        memories = []
        for r in results:
            payload = r.payload
            # Filter out invalidated memories
            if payload.get("invalidated", False):
                continue
            memories.append(Memory(
                memory_id=payload["memory_id"],
                type=payload["type"],
                content=payload["content"],
                dimensions=payload.get("dimensions", {}),
                confidence=payload.get("confidence", 0.8),
                source_session_id=payload.get("source_session_id"),
                created_at=datetime.fromisoformat(payload["created_at"]),
                invalidated=payload.get("invalidated", False),
                expires_at=datetime.fromisoformat(payload["expires_at"]) if payload.get("expires_at") else None,
                call_count=payload.get("call_count", 0),
                last_called_at=datetime.fromisoformat(payload["last_called_at"]) if payload.get("last_called_at") else None,
            ))
            if len(memories) >= limit:
                break

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
                invalidated=payload.get("invalidated", False),
                expires_at=datetime.fromisoformat(payload["expires_at"]) if payload.get("expires_at") else None,
                call_count=payload.get("call_count", 0),
                last_called_at=datetime.fromisoformat(payload["last_called_at"]) if payload.get("last_called_at") else None,
            ))

        return memories

    def update_memory(
        self,
        memory_id: str,
        content: str = None,
        memory_type: str = None,
    ) -> bool:
        """更新记忆内容、类型"""
        try:
            # Get current memory
            results = self.vector_store.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
            )
            if not results or len(results) == 0:
                return False

            payload = results[0].payload
            update_payload = {
                "memory_id": memory_id,
                "type": memory_type if memory_type is not None else payload.get("type"),
                "content": content if content is not None else payload.get("content"),
                "dimensions": payload.get("dimensions", {}),
                "source_session_id": payload.get("source_session_id"),
                "created_at": payload.get("created_at"),
                "invalidated": payload.get("invalidated", False),
                "expires_at": payload.get("expires_at"),
                "call_count": payload.get("call_count", 0),
                "last_called_at": payload.get("last_called_at"),
            }

            self.vector_store.client.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": memory_id,
                    "vector": self.ollama.embed(update_payload["content"]),
                    "payload": update_payload,
                }]
            )
            return True
        except Exception:
            return False

    def invalidate_memory(self, memory_id: str, invalidated: bool = True) -> bool:
        """标记记忆失效/恢复"""
        try:
            results = self.vector_store.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
            )
            if not results or len(results) == 0:
                return False

            payload = results[0].payload
            payload["invalidated"] = invalidated

            self.vector_store.client.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": memory_id,
                    "vector": results[0].vector,
                    "payload": payload,
                }]
            )
            return True
        except Exception:
            return False

    def increment_call_count(self, memory_id: str) -> bool:
        """增加调用计数"""
        try:
            results = self.vector_store.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
            )
            if not results or len(results) == 0:
                return False

            payload = results[0].payload
            payload["call_count"] = payload.get("call_count", 0) + 1
            payload["last_called_at"] = datetime.now().isoformat()

            self.vector_store.client.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": memory_id,
                    "vector": results[0].vector,
                    "payload": payload,
                }]
            )
            return True
        except Exception:
            return False

    def get_memory_stats(self, memory_id: str) -> Optional[dict]:
        """获取统计信息"""
        try:
            results = self.vector_store.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
            )
            if not results or len(results) == 0:
                return None

            payload = results[0].payload
            return {
                "memory_id": memory_id,
                "call_count": payload.get("call_count", 0),
                "last_called_at": payload.get("last_called_at"),
                "invalidated": payload.get("invalidated", False),
                "expires_at": payload.get("expires_at"),
                "created_at": payload.get("created_at"),
            }
        except Exception:
            return None

    def get_profile(self) -> dict:
        """获取用户画像"""
        return self.profile_manager.get_profile_summary("default")

    def update_profile_from_memories(
        self,
        memory_ids: list[str],
    ) -> dict:
        """从记忆更新画像"""
        return {"status": "updated"}