# backend/services/memory_injector.py

from typing import Optional
from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from config import AppConfig


class MemoryInjector:
    """记忆注入引擎 - 负责检索相关记忆并组装到上下文"""

    def __init__(self, vector_store: VectorStore, ollama_service: OllamaService, config: AppConfig):
        self.vector_store = vector_store
        self.ollama = ollama_service
        self.config = config
        self.collection_name = "memories"

    def inject(
        self,
        query: str,
        platform: str,
        recall_count: int = 5,
        similarity_threshold: float = 0.7,
        injection_position: str = "system",
    ) -> Optional[dict]:
        """
        检索相关记忆并组装注入上下文

        Returns:
            dict: {
                "injected_messages": [...],  # 注入记忆后的消息
                "context": str,  # 组装后的上下文字符串
                "memories_found": int,  # 找到的记忆数量
            }
        """
        # 1. 从 Qdrant 检索相关记忆
        memories = self._search_memories(query, recall_count, similarity_threshold)

        if not memories:
            return None

        # 2. 组装上下文字符串
        context = self._build_context_string(memories)

        # 3. 构建注入后的消息列表
        injected_messages = self._build_injected_messages(query, context, injection_position)

        return {
            "injected_messages": injected_messages,
            "context": context,
            "memories_found": len(memories),
        }

    def _search_memories(
        self,
        query: str,
        recall_count: int,
        similarity_threshold: float,
    ) -> list[dict]:
        """搜索相关记忆"""
        try:
            # 生成查询向量
            query_emb = self.ollama.embed(query)

            # 搜索 Qdrant
            results = self.vector_store.client.search(
                collection_name=self.collection_name,
                query_vector=query_emb,
                limit=recall_count,
            )

            # 过滤低于阈值的
            memories = []
            for r in results:
                if r.score >= similarity_threshold:
                    memories.append({
                        "content": r.payload.get("content", ""),
                        "type": r.payload.get("type", ""),
                        "dimensions": r.payload.get("dimensions", {}),
                        "score": r.score,
                    })

            return memories
        except Exception as e:
            print(f"Memory search error: {e}")
            return []

    def _build_context_string(self, memories: list[dict]) -> str:
        """构建记忆上下文字符串"""
        if not memories:
            return ""

        parts = ["[记忆上下文]\n"]

        # 按 type 分组
        by_type = {}
        for mem in memories:
            mem_type = mem.get("type", "unknown")
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(mem)

        # 按类型输出
        type_labels = {
            "preference": "偏好习惯",
            "expertise": "专业知识",
            "project_context": "项目上下文",
        }

        for mem_type, mems in by_type.items():
            label = type_labels.get(mem_type, mem_type)
            parts.append(f"\n{label}:\n")
            for mem in mems:
                parts.append(f"- {mem['content']}\n")

        return "".join(parts).strip()

    def _build_injected_messages(
        self,
        query: str,
        context: str,
        position: str,
    ) -> list[dict]:
        """构建注入后的消息列表"""
        if position == "system":
            return [
                {"role": "system", "content": context},
                {"role": "user", "content": query},
            ]
        else:
            return [
                {"role": "system", "content": context},
                {"role": "user", "content": query},
            ]