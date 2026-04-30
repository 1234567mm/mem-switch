import pytest
from unittest.mock import Mock, patch, MagicMock
from services.vector_store import VectorStore, COLLECTIONS


@pytest.fixture
def mock_chromadb():
    with patch("services.vector_store.chromadb") as mock:
        mock_client = MagicMock()
        mock.PersistentClient.return_value = mock_client
        yield mock, mock_client


@pytest.fixture
def mock_qdrant_dir(tmp_path):
    with patch("services.vector_store.QDRANT_DIR", tmp_path):
        yield tmp_path


@pytest.fixture
def vector_store(mock_chromadb, mock_qdrant_dir):
    VectorStore._instance = None
    VectorStore._initialized = False
    store = VectorStore()
    return store

class TestVectorStoreInit:
    def test_singleton_pattern(self, mock_chromadb, mock_qdrant_dir):
        VectorStore._instance = None
        VectorStore._initialized = False
        store1 = VectorStore()
        store2 = VectorStore()
        assert store1 is store2

    def test_init_collections_called(self, mock_chromadb, mock_qdrant_dir):
        _, mock_client = mock_chromadb
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        VectorStore._instance = None
        VectorStore._initialized = False
        store = VectorStore()
        assert mock_client.get_or_create_collection.call_count == len(COLLECTIONS)


class TestUpsert:
    def test_upsert_single_point(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        points = [{"id": "doc-1", "vector": [0.1, 0.2, 0.3], "payload": {"content": "Hello world", "type": "test"}}]
        vector_store.upsert("conversations", points)
        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args
        assert call_args.kwargs["ids"] == ["doc-1"]
        assert call_args.kwargs["documents"] == ["Hello world"]
        assert call_args.kwargs["metadatas"] == [{"type": "test"}]

    def test_upsert_multiple_points(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        points = [
            {"id": "doc-1", "vector": [0.1, 0.2, 0.3], "payload": {"content": "First", "type": "a"}},
            {"id": "doc-2", "vector": [0.4, 0.5, 0.6], "payload": {"content": "Second", "type": "b"}}
        ]
        vector_store.upsert("memories", points)
        call_args = mock_collection.upsert.call_args
        assert call_args.kwargs["ids"] == ["doc-1", "doc-2"]
        assert call_args.kwargs["documents"] == ["First", "Second"]
        assert call_args.kwargs["metadatas"] == [{"type": "a"}, {"type": "b"}]

    def test_upsert_point_without_content(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        points = [{"id": "doc-1", "vector": [0.1, 0.2, 0.3], "payload": {"type": "test"}}]
        vector_store.upsert("conversations", points)
        call_args = mock_collection.upsert.call_args
        assert call_args.kwargs["documents"] == [""]

class TestSearch:
    def test_search_without_filter(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        mock_collection.query.return_value = {
            "documents": [["doc content"]], "ids": [["doc-1"]], "distances": [[0.5]], "metadatas": [[{"type": "test"}]]
        }
        results = vector_store.search("conversations", [0.1, 0.2, 0.3], limit=10)
        assert len(results) == 1
        assert results[0]["id"] == "doc-1"
        assert results[0]["score"] == pytest.approx(1.0 / (1.0 + 0.5))

    def test_search_with_query_filter(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        mock_collection.query.return_value = {
            "documents": [["filtered"]], "ids": [["doc-2"]], "distances": [[0.2]], "metadatas": [[{"type": "preference"}]]
        }
        query_filter = {"must": [{"key": "type", "match": {"value": "preference"}}]}
        results = vector_store.search("knowledge", [0.5, 0.6, 0.7], limit=5, query_filter=query_filter)
        assert len(results) == 1
        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] == {"type": "preference"}

    def test_search_with_empty_results(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        mock_collection.query.return_value = {"documents": [[]], "ids": [[]], "distances": [[]], "metadatas": [[]]}
        results = vector_store.search("conversations", [0.1, 0.2, 0.3])
        assert results == []

    def test_search_with_no_distances(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        mock_collection.query.return_value = {
            "documents": [["content"]], "ids": [["doc-1"]], "distances": [], "metadatas": [[{"type": "test"}]]
        }
        results = vector_store.search("conversations", [0.1, 0.2, 0.3])
        assert len(results) == 1
        assert results[0]["score"] == 1.0

    def test_search_with_no_metadata(self, vector_store):
        mock_collection = MagicMock()
        vector_store.client.get_collection.return_value = mock_collection
        mock_collection.query.return_value = {
            "documents": [["content"]], "ids": [["doc-1"]], "distances": [[0.3]], "metadatas": [[None]]
        }
        results = vector_store.search("conversations", [0.1, 0.2, 0.3])
        assert len(results) == 1
        assert results[0]["payload"]["content"] == "content"