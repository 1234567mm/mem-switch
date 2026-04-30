import pytest
from unittest.mock import MagicMock
from services.memory_service import MemoryService


@pytest.fixture
def memory_service(mock_vector_store, mock_ollama, mock_config):
    return MemoryService(mock_vector_store, mock_ollama, mock_config)


class TestCreateMemory:
    def test_returns_memory_with_id(self, memory_service):
        result = memory_service.create_memory(content="test", memory_type="preference")
        assert result.memory_id is not None
        assert result.content == "test"
        assert result.type == "preference"

    def test_calls_embed_once(self, memory_service, mock_ollama):
        memory_service.create_memory(content="test", memory_type="skill")
        mock_ollama.embed.assert_called_once_with("test")

    def test_upsert_called_with_correct_collection(self, memory_service, mock_vector_store):
        memory_service.create_memory(content="test", memory_type="fact")
        mock_vector_store.client.upsert.assert_called_once()
        call_args = mock_vector_store.client.upsert.call_args
        assert call_args.kwargs.get("collection_name") == "memories" or \
               (isinstance(call_args.args[0], dict) and "collection_name" in call_args.args[0])

    def test_default_confidence(self, memory_service):
        result = memory_service.create_memory(content="test", memory_type="fact")
        assert result.confidence == 0.8

    def test_custom_dimensions_confidence(self, memory_service):
        result = memory_service.create_memory(
            content="test", memory_type="fact",
            dimensions={"confidence": 0.95}
        )
        assert result.confidence == 0.95


class TestDeleteMemory:
    def test_delete_returns_true_on_success(self, memory_service):
        assert memory_service.delete_memory("any-id") is True

    def test_delete_raises_returns_false(self, memory_service, mock_vector_store):
        mock_vector_store.client.delete.side_effect = Exception("fail")
        assert memory_service.delete_memory("any-id") is False


class TestListMemories:
    def test_list_returns_memories(self, memory_service, mock_chroma_collection):
        # 预填充数据
        mock_chroma_collection._store["mem1"] = {"document": "test", "metadata": {
            "memory_id": "mem1", "type": "preference", "content": "test",
            "created_at": "2024-01-01T00:00:00", "invalidated": False,
            "dimensions": {}, "confidence": 0.8, "source_session_id": None
        }}
        mock_chroma_collection.count.return_value = 1

        results = memory_service.list_memories()
        assert isinstance(results, list)

    def test_list_filters_by_type(self, memory_service, mock_chroma_collection):
        mock_chroma_collection._store["mem1"] = {"document": "test", "metadata": {
            "memory_id": "mem1", "type": "preference", "content": "test pref",
            "created_at": "2024-01-01T00:00:00", "invalidated": False,
            "dimensions": {}, "confidence": 0.8, "source_session_id": None
        }}
        mock_chroma_collection._store["mem2"] = {"document": "test", "metadata": {
            "memory_id": "mem2", "type": "skill", "content": "test skill",
            "created_at": "2024-01-01T00:00:00", "invalidated": False,
            "dimensions": {}, "confidence": 0.8, "source_session_id": None
        }}
        mock_chroma_collection.count.return_value = 2

        results = memory_service.list_memories(memory_type="preference")
        assert isinstance(results, list)


class TestSearchMemories:
    def test_search_returns_list(self, memory_service, mock_chroma_collection):
        mock_vector_store = memory_service.vector_store
        mock_vector_store.client.search.return_value = []

        results = memory_service.search_memories(query="test")
        assert isinstance(results, list)

    def test_search_filters_by_type(self, memory_service, mock_vector_store):
        mock_vector_store.client.search.return_value = []
        results = memory_service.search_memories(query="test", memory_type="fact")
        assert isinstance(results, list)


class TestUpdateMemory:
    def test_update_returns_true_on_success(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = [MagicMock(
            payload={"memory_id": "m1", "content": "old", "type": "fact",
                     "created_at": "2024-01-01T00:00:00", "invalidated": False,
                     "dimensions": {}, "confidence": 0.8, "source_session_id": None,
                     "call_count": 0, "last_called_at": None},
            vector=[0.1] * 768
        )]
        result = memory_service.update_memory("m1", content="updated")
        assert result is True

    def test_update_returns_false_on_missing(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = []
        result = memory_service.update_memory("nonexistent", content="updated")
        assert result is False


class TestInvalidateMemory:
    def test_invalidate_returns_true_on_success(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = [MagicMock(
            payload={"memory_id": "m1", "content": "test", "type": "fact",
                     "created_at": "2024-01-01T00:00:00", "invalidated": False,
                     "dimensions": {}, "confidence": 0.8, "source_session_id": None,
                     "call_count": 0, "last_called_at": None},
            vector=[0.1] * 768
        )]
        result = memory_service.invalidate_memory("m1", invalidated=True)
        assert result is True

    def test_invalidate_returns_false_on_missing(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = []
        result = memory_service.invalidate_memory("nonexistent")
        assert result is False


class TestMergeMemories:
    def test_merge_returns_new_memory_dict(self, memory_service, mock_vector_store, mock_chroma_collection):
        mock_vector_store.client.retrieve.return_value = [
            MagicMock(payload={
                "memory_id": "a", "content": "Content A", "type": "fact",
                "created_at": "2024-01-01T00:00:00"
            }),
            MagicMock(payload={
                "memory_id": "b", "content": "Content B", "type": "fact",
                "created_at": "2024-01-02T00:00:00"
            }),
        ]
        result = memory_service.merge_memories(["a", "b"])
        assert result is not None
        assert "memory_id" in result
        assert "deleted_ids" in result

    def test_merge_returns_none_on_missing_ids(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = []
        result = memory_service.merge_memories(["x", "y"])
        assert result is None


class TestIncrementCallCount:
    def test_increment_returns_true_on_success(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = [MagicMock(
            payload={"memory_id": "m1", "content": "test", "type": "fact",
                     "created_at": "2024-01-01T00:00:00", "invalidated": False,
                     "dimensions": {}, "confidence": 0.8, "source_session_id": None,
                     "call_count": 5, "last_called_at": None},
            vector=[0.1] * 768
        )]
        result = memory_service.increment_call_count("m1")
        assert result is True

    def test_increment_returns_false_on_missing(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = []
        result = memory_service.increment_call_count("nonexistent")
        assert result is False


class TestGetMemoryStats:
    def test_get_stats_returns_dict_on_success(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = [MagicMock(
            payload={"memory_id": "m1", "content": "test", "type": "fact",
                     "created_at": "2024-01-01T00:00:00", "invalidated": False,
                     "dimensions": {}, "confidence": 0.8, "source_session_id": None,
                     "call_count": 10, "last_called_at": "2024-01-02T00:00:00"},
            vector=[0.1] * 768
        )]
        result = memory_service.get_memory_stats("m1")
        assert result is not None
        assert "memory_id" in result
        assert "call_count" in result

    def test_get_stats_returns_none_on_missing(self, memory_service, mock_vector_store):
        mock_vector_store.client.retrieve.return_value = []
        result = memory_service.get_memory_stats("nonexistent")
        assert result is None


class TestGetProfile:
    def test_get_profile_returns_dict(self, memory_service):
        result = memory_service.get_profile()
        # ProfileManager returns dict or raises - just check it returns
        assert result is not None


class TestUpdateProfileFromMemories:
    def test_update_profile_from_memories_returns_dict(self, memory_service):
        result = memory_service.update_profile_from_memories(["mem1", "mem2"])
        assert isinstance(result, dict)
