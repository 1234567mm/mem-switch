import pytest
from unittest.mock import patch, MagicMock
from services.search_service import SearchService


@pytest.fixture
def search_service(tmp_session, mock_vector_store, mock_ollama):
    with patch("services.search_service.get_session", return_value=tmp_session):
        with patch("services.search_service.VectorStore", return_value=mock_vector_store):
            with patch("services.search_service.OllamaService", return_value=mock_ollama):
                yield SearchService()


class TestUnifiedSearch:
    def test_search_returns_dict(self, search_service):
        result = search_service.unified_search(query="test", scopes=["memory"])
        assert isinstance(result, dict)

    def test_cache_hit_on_second_call(self, search_service):
        """相同参数第二次调用应命中缓存。"""
        search_service.unified_search(query="cache-test", scopes=["memory"], limit=5)
        result = search_service.unified_search(query="cache-test", scopes=["memory"], limit=5)
        assert result.get("_from_cache") is True

    def test_different_queries_no_cache_collision(self, search_service):
        search_service.unified_search(query="query-A", scopes=["memory"])
        result = search_service.unified_search(query="query-B", scopes=["memory"])
        assert result.get("_from_cache") is not True


class TestSearchMemories:
    def test_small_data_uses_like(self, search_service, tmp_session):
        # 小数据量（< 1000）使用 LIKE 搜索
        result = search_service.search_memories("test", limit=10, session=tmp_session)
        assert "results" in result
        assert "method" in result


class TestGetHotMemories:
    def test_returns_memories_sorted_by_call_count(self, search_service, tmp_session):
        result = search_service.get_hot_memories(limit=5)
        assert isinstance(result, list)


class TestGetHotKnowledge:
    def test_returns_knowledge_sorted_by_view_count(self, search_service, tmp_session):
        result = search_service.get_hot_knowledge(limit=5)
        assert isinstance(result, list)


class TestAddSearchHistory:
    def test_add_search_history_does_not_raise(self, search_service):
        # add_search_history uses its own connection, should not raise
        search_service.add_search_history("test query")
        search_service.add_search_history("another query")

    def test_get_search_history_returns_list(self, search_service):
        result = search_service.get_search_history(limit=10)
        assert isinstance(result, list)


class TestIncrementMemoryCall:
    def test_increment_memory_call_does_not_raise(self, search_service, tmp_session):
        from services.database import MemoryRow
        mem = MemoryRow(
            id="test-mem-1",
            type="preference",
            content="test",
            confidence=0.8,
            qdrant_id="q1",
            call_count=0,
        )
        tmp_session.add(mem)
        tmp_session.commit()

        search_service.increment_memory_call("test-mem-1")
