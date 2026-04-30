"""统一搜索服务 - SearchService"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache
import time

from services.vector_store import VectorStore
from services.ollama_service import OllamaService
from services.database import get_session, MemoryRow, DocumentRow


# 小数据量阈值
SMALL_DATA_THRESHOLD = 1000

# 搜索超时 (秒)
SEARCH_TIMEOUT = 30

# 缓存配置
CACHE_TTL_SECONDS = 300  # 5 分钟缓存


@dataclass
class SearchResult:
    """搜索结果"""
    memory_results: list
    knowledge_results: list
    total_memory: int
    total_knowledge: int


class SearchService:
    """统一搜索服务"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.ollama = OllamaService()
        # 简单缓存：{key: {"results": data, "timestamp": float}}
        self._cache = {}

    def _get_cache_key(self, query: str, scopes: list, limit: int) -> str:
        """生成缓存键"""
        return f"{query}:{','.join(sorted(scopes))}:{limit}"

    def _get_from_cache(self, key: str) -> Optional[dict]:
        """从缓存获取结果"""
        if key not in self._cache:
            return None
        cached = self._cache[key]
        if time.time() - cached["timestamp"] > CACHE_TTL_SECONDS:
            del self._cache[key]
            return None
        return cached["results"]

    def _set_cache(self, key: str, results: dict):
        """设置缓存"""
        self._cache[key] = {
            "results": results,
            "timestamp": time.time()
        }

    def unified_search(self, query: str, scopes: list, limit: int = 20) -> dict:
        """统一搜索入口

        Args:
            query: 搜索查询
            scopes: 搜索范围列表，如 ["memory", "knowledge"]
            limit: 返回结果数量限制

        Returns:
            {"memory": {...}, "knowledge": {...}}
        """
        # 尝试缓存
        cache_key = self._get_cache_key(query, scopes, limit)
        cached = self._get_from_cache(cache_key)
        if cached:
            cached["_from_cache"] = True
            return cached

        # 执行搜索（带超时控制）
        start_time = time.time()
        results = {}
        session = get_session()
        try:
            if "memory" in scopes:
                timeout = max(1, SEARCH_TIMEOUT - (time.time() - start_time))
                results["memory"] = self.search_memories(query, limit, session, timeout=timeout)
            if "knowledge" in scopes:
                timeout = max(1, SEARCH_TIMEOUT - (time.time() - start_time))
                results["knowledge"] = self.search_knowledge(query, limit, session, timeout=timeout)
        finally:
            session.close()

        # 缓存结果
        self._set_cache(cache_key, results)

        # 添加搜索历史（异步，不阻塞）
        self.add_search_history(query)

        return results

    def search_memories(self, query: str, limit: int, session, timeout: int = SEARCH_TIMEOUT) -> dict:
        """搜索记忆库

        - 小数据量 (< 1000): 直接 LIKE 搜索
        - 大数据量 (>= 1000): 向量搜索

        Args:
            query: 搜索查询
            limit: 结果数量限制
            session: 数据库会话
            timeout: 超时时间（秒）
        """
        start_time = time.time()

        # 检查数据量
        total_count = session.query(MemoryRow).count()

        if total_count < SMALL_DATA_THRESHOLD:
            # 小数据量：使用 LIKE 搜索
            memories = (
                session.query(MemoryRow)
                .filter(MemoryRow.content.like(f"%{query}%"))
                .limit(limit)
                .all()
            )
            results = [
                {
                    "id": m.id,
                    "type": m.type,
                    "content": m.content,
                    "confidence": m.confidence,
                    "call_count": m.call_count,
                    "source_session_id": m.source_session_id,
                }
                for m in memories
            ]
        else:
            # 大数据量：使用向量搜索
            query_emb = self.ollama.embed(query)

            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Search timeout after {timeout}s")

            vector_results = self.vector_store.search(
                collection_name="memories",
                query_vector=query_emb,
                limit=limit,
            )
            # 从向量结果中提取 id 列表，然后批量查询数据库获取 call_count
            memory_ids = [r["id"] for r in vector_results]
            memory_map = {}
            if memory_ids:
                db_memories = (
                    session.query(MemoryRow)
                    .filter(MemoryRow.id.in_(memory_ids))
                    .all()
                )
                memory_map = {m.id: m for m in db_memories}

            results = []
            for r in vector_results:
                memory_id = r["id"]
                db_mem = memory_map.get(memory_id)
                results.append({
                    "id": memory_id,
                    "type": r["payload"].get("type"),
                    "content": r["payload"].get("content"),
                    "confidence": r["payload"].get("confidence"),
                    "call_count": db_mem.call_count if db_mem else 0,
                    "source_session_id": r["payload"].get("source_session_id"),
                    "score": r["score"],
                })

        return {
            "results": results,
            "total": total_count,
            "method": "like" if total_count < SMALL_DATA_THRESHOLD else "vector",
            "elapsed_ms": int((time.time() - start_time) * 1000),
        }

    def search_knowledge(self, query: str, limit: int, session, timeout: int = SEARCH_TIMEOUT) -> dict:
        """搜索知识库

        Args:
            query: 搜索查询
            limit: 结果数量限制
            session: 数据库会话
            timeout: 超时时间（秒）
        """
        start_time = time.time()

        # 获取所有文档数量
        total_count = session.query(DocumentRow).count()

        if total_count < SMALL_DATA_THRESHOLD:
            # 小数据量：使用 LIKE 搜索文档内容
            # 需要从向量存储中搜索，因为 DocumentRow 只存储元数据
            doc_rows = session.query(DocumentRow).limit(SMALL_DATA_THRESHOLD).all()
            kb_ids = list(set(d.kb_id for d in doc_rows))

            # Compute embedding once outside loop
            query_emb = self.ollama.embed(query)

            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Search timeout after {timeout}s")

            results = []
            for kb_id in kb_ids:
                vector_results = self.vector_store.search(
                    collection_name="knowledge",
                    query_vector=query_emb,
                    limit=limit,
                    query_filter={"must": [{"key": "kb_id", "match": {"value": kb_id}}]},
                )
                for r in vector_results:
                    results.append({
                        "doc_id": r["payload"].get("doc_id"),
                        "kb_id": kb_id,
                        "content": r["payload"].get("content"),
                        "filename": r["payload"].get("filename"),
                        "chunk_index": r["payload"].get("chunk_index"),
                        "score": r["score"],
                    })
        else:
            # 大数据量：使用向量搜索
            query_emb = self.ollama.embed(query)

            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Search timeout after {timeout}s")

            vector_results = self.vector_store.search(
                collection_name="knowledge",
                query_vector=query_emb,
                limit=limit,
            )
            results = []
            for r in vector_results:
                results.append({
                    "doc_id": r["payload"].get("doc_id"),
                    "kb_id": r["payload"].get("kb_id"),
                    "content": r["payload"].get("content"),
                    "filename": r["payload"].get("filename"),
                    "chunk_index": r["payload"].get("chunk_index"),
                    "score": r["score"],
                })

        return {
            "results": results[:limit],
            "total": total_count,
            "method": "like" if total_count < SMALL_DATA_THRESHOLD else "vector",
            "elapsed_ms": int((time.time() - start_time) * 1000),
        }

    def add_search_history(self, query: str):
        """添加搜索历史到 search_history 表"""
        import sqlite3
        from config import SQLITE_DIR

        conn = sqlite3.connect(SQLITE_DIR / "metadata.db")
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO search_history (query, timestamp) VALUES (?, ?)",
                (query, datetime.now().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_search_history(self, limit: int = 10) -> list:
        """获取搜索历史"""
        import sqlite3
        from config import SQLITE_DIR

        conn = sqlite3.connect(SQLITE_DIR / "metadata.db")
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, query, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        return [
            {"id": r[0], "query": r[1], "timestamp": r[2]}
            for r in rows
        ]

    def get_hot_memories(self, limit: int = 5) -> list:
        """获取热门记忆（按 call_count 排序）"""
        session = get_session()
        try:
            memories = (
                session.query(MemoryRow)
                .order_by(MemoryRow.call_count.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": m.id,
                    "type": m.type,
                    "content": m.content,
                    "call_count": m.call_count,
                }
                for m in memories
            ]
        finally:
            session.close()

    def get_hot_knowledge(self, limit: int = 5) -> list:
        """获取热门知识（按 view_count 排序）"""
        session = get_session()
        try:
            docs = (
                session.query(DocumentRow)
                .order_by(DocumentRow.view_count.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "doc_id": d.doc_id,
                    "kb_id": d.kb_id,
                    "filename": d.filename,
                    "view_count": d.view_count,
                    "chunks_count": d.chunks_count,
                }
                for d in docs
            ]
        finally:
            session.close()

    def increment_memory_call(self, memory_id: int):
        """增加记忆调用计数"""
        session = get_session()
        try:
            memory = session.query(MemoryRow).filter_by(id=memory_id).first()
            if memory:
                memory.call_count = (memory.call_count or 0) + 1
                session.commit()
        finally:
            session.close()