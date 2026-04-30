import pytest
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
        mock_vector_store.client.get_collection.assert_called_with("memories")

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
        mock_vector_store.client.get_collection.side_effect = Exception("fail")
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
